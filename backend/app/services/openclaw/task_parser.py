import json
import re
import httpx
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.config import settings
from app.core.logger import logger
from app.models.llm_model import LLMModel

async def parse_task_intent(prompt: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Parse user prompt into a structured task definition using an active LLM.
    """
    # 1. Get active LLM for parsing
    res = await db.execute(
        select(LLMModel)
        .filter(LLMModel.is_active == True)
        .order_by(LLMModel.updated_at.desc())
    )
    active_model = res.scalars().first()
    
    # Fallback config
    api_key = settings.OPENAI_API_KEY
    base_url = "https://api.openai.com/v1"
    model_id = "gpt-3.5-turbo"
    
    if active_model:
        api_key = active_model.api_key
        model_id = active_model.model_id
        if active_model.base_url:
            base_url = active_model.base_url
        
        provider = (active_model.provider or "").lower()
        if not active_model.base_url:
            if "aliyun" in provider or "dashscope" in provider:
                 base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif "deepseek" in provider:
                 base_url = "https://api.deepseek.com"
    
    if not api_key:
         raise HTTPException(status_code=500, detail="No active LLM model found for parsing task")

    # 2. Parse prompt
    prompt_system = """
    You are an automation task assistant. Extract task details from the user's prompt.
    
    Your goal is to generate a JSON object with the following fields:
    - name: A short, descriptive name for the task (string).
    - schedule: A valid cron expression (string). 
        - If the user says "every hour", use "0 * * * *".
        - If "every day at 9am", use "0 9 * * *".
        - If unspecified, default to "0 9 * * *".
    - command: The command string to execute (string).
        - If the user wants to crawl/scrape a URL, format as: "crawl <url>"
        - If the user wants to screenshot a URL, format as: "screenshot <url>"
        - If the user wants to monitor a URL, format as: "monitor <url>"
    
    Respond with ONLY the JSON string.
    """
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            chat_res = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": prompt_system},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1
                }
            )
            
            if chat_res.status_code != 200:
                logger.error(f"LLM parsing failed: {chat_res.text}")
                raise HTTPException(status_code=500, detail="Failed to parse task intent")
            
            content = chat_res.json()["choices"][0]["message"]["content"]
            
            # Extract JSON
            match = re.search(r"(\{.*\})", content, re.DOTALL)
            if match:
                content = match.group(1)
            
            return json.loads(content)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"Task parsing error: {str(e)}")
