"""
应用场景：
    将自然语言提示解析为结构化的任务定义。
    由任务创建 API 使用。

核心功能：
    - LLM 交互（OpenAI/兼容接口）
    - JSON 提取与 Schema 校验
    - 自动重试逻辑
    - 默认值标准化

输入：
    prompt: str - 用户的自然语言请求
    db: AsyncSession - 用于配置查询的数据库会话

输出：
    Dict[str, Any] - 结构化的任务定义（指令、计划时间、目标节点）

__author__ = "xucao"
Created: 2024-05
Last Modified: 2025-03
"""

import json
import re
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from jsonschema import validate, ValidationError

from app.core.config import settings
import traceback
from app.core.logger import logger
from app.models.llm_model import LLMModel
from app.services.openclaw.utils.parser.exception import TaskParsingError
from app.services.openclaw.task.parser.prompt import SYSTEM_PROMPT

# Agent Memory Import
from app.services.openclaw.task.memory.storage import RedisMemoryStorage
from app.services.openclaw.task.memory.models import MemoryUnit, MemoryType

# Memory Storage Singleton (Initialize in app startup or here lazily)
# Assuming settings.REDIS_URL exists
_memory_storage = None

def get_memory_storage() -> RedisMemoryStorage:
    global _memory_storage
    if not _memory_storage:
        # Default fallback or use config
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        _memory_storage = RedisMemoryStorage(redis_url)
    return _memory_storage

async def _retrieve_context(session_id: str, prompt: str) -> str:
    """
    Retrieve relevant context from Agent Memory.
    Returns formatted context string.
    """
    if not session_id:
        return ""
        
    storage = get_memory_storage()
    # Lazy init index if needed
    if not storage._index_created:
        await storage.initialize()
        
    # 1. Get recent conversation history (Context Coherence)
    history = await storage.get_session_context(session_id, limit=5)
    
    # 2. Semantic Search for related tasks/rules (Recall)
    # Exclude recent history to avoid duplication? 
    # Search is broad, history is strict time-ordered.
    related = await storage.search_memory(prompt, session_id=session_id, limit=3)
    
    # Deduplicate based on memory_id
    seen_ids = {m.memory_id for m in history}
    unique_related = [m for m in related if m.memory_id not in seen_ids]
    
    context_parts = []
    
    if history:
        context_parts.append("Recent History:")
        # Reverse to chronological order for LLM
        for m in reversed(history):
            context_parts.append(f"- [{m.type}] {m.content}")
            
    if unique_related:
        context_parts.append("\nRelated Context:")
        for m in unique_related:
            context_parts.append(f"- {m.content}")
            
    return "\n".join(context_parts)

async def parse_task_intent(prompt: str, db: AsyncSession, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse user prompt into a structured task definition using an active LLM.
    Includes retry logic, schema validation, and Context Recall.
    """
    api_key, base_url, model_id = await _get_active_llm(db)
    
    if not api_key:
         raise HTTPException(status_code=500, detail="No active LLM model found for parsing task")

    # 1. Retrieve Context
    context_str = await _retrieve_context(session_id, prompt)
    
    # 2. Construct Augmented Prompt
    system_prompt_augmented = SYSTEM_PROMPT
    if context_str:
        system_prompt_augmented += f"\n\nContext Information:\n{context_str}\n\nUse the above context to resolve references (e.g., 'it', 'previous task')."

    messages = [
        {"role": "system", "content": system_prompt_augmented},
        {"role": "user", "content": prompt}
    ]
    
    max_retries = 1
# JSON Schema definition for task intent
TASK_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {"type": "string", "minLength": 1},
        "schedule": {"type": "string"},
        "node_requirements": {"type": "string"},
        "intent_type": {"type": "string", "enum": ["task", "chat"]}
    },
    "required": ["command"],
    "additionalProperties": False
}

async def _get_active_llm(db: AsyncSession) -> tuple[str, str, str]:
    """Helper to get active LLM configuration"""
    res = await db.execute(
        select(LLMModel)
        .filter(LLMModel.is_active == True)
        .filter(LLMModel.model_type == "text")  # Ensure we only pick text generation models
        .order_by(LLMModel.updated_at.desc())
    )
    active_model = res.scalars().first()
    
    # Default fallback
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
                 
    return api_key, base_url, model_id

async def _call_llm(client: httpx.AsyncClient, base_url: str, api_key: str, model_id: str, 
                   messages: list) -> str:
    """Helper to call LLM API"""
    try:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_id,
                "messages": messages,
                "temperature": 0.1
            }
        )
        
        if response.status_code != 200:
            logger.error(f"LLM parsing failed: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to parse task intent")
            
        content = response.json()["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        logger.error(f"LLM call error: {e}")
        raise

def _extract_and_validate_json(content: str) -> Dict[str, Any]:
    """Helper to extract JSON and validate schema"""
    try:
        # Extract JSON if wrapped in markdown or text
        match = re.search(r"(\{.*\})", content, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = content
            
        data = json.loads(json_str)
        validate(instance=data, schema=TASK_INTENT_SCHEMA)
        return data
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Invalid JSON or Schema: {str(e)}")

async def parse_task_intent(prompt: str, db: AsyncSession, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse user prompt into a structured task definition using an active LLM.
    Includes retry logic and schema validation.
    """
    api_key, base_url, model_id = await _get_active_llm(db)
    
    if not api_key:
         error_msg = "No active LLM model found for parsing task"
         logger.error(error_msg)
         raise HTTPException(status_code=500, detail=error_msg)

    # 1. Retrieve Context
    try:
        context_str = await _retrieve_context(session_id, prompt)
    except Exception as e:
        logger.warning(f"Context retrieval failed: {e}")
        context_str = ""
    
    # 2. Construct Augmented Prompt
    system_prompt_augmented = SYSTEM_PROMPT
    if context_str:
        system_prompt_augmented += f"\n\nContext Information:\n{context_str}\n\nUse the above context to resolve references (e.g., 'it', 'previous task')."

    messages = [
        {"role": "system", "content": system_prompt_augmented},
        {"role": "user", "content": prompt}
    ]
    
    max_retries = 1
    last_error = None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"LLM parsing attempt {attempt+1}/{max_retries+1}: model={model_id}")
                content = await _call_llm(client, base_url, api_key, model_id, messages)
                logger.debug(f"LLM response content: {content[:200]}...")
                
                try:
                    task_data = _extract_and_validate_json(content)
                    logger.info(f"Task intent parsed successfully: {task_data}")
                    
                    # Normalize fields
                    if "schedule" not in task_data:
                        task_data["schedule"] = "0 9 * * *"
                        
                    node_req = task_data.get("node_requirements")
                    if not node_req or node_req.lower() == "default":
                        task_data["target_node"] = "default"
                    else:
                        task_data["target_node"] = node_req
                    
                    # Store User Query & Result to Memory (if session_id provided)
                    if session_id:
                        try:
                            storage = get_memory_storage()
                            # 1. User Query
                            await storage.add_memory(
                                session_id,
                                MemoryUnit(
                                    session_id=session_id,
                                    type=MemoryType.CONVERSATION,
                                    content=f"User: {prompt}"
                                ),
                                ttl=7*24*3600 # 7 days
                            )
                            # 2. Assistant Response (Parsed Task)
                            await storage.add_memory(
                                session_id,
                                MemoryUnit(
                                    session_id=session_id,
                                    type=MemoryType.TASK_RESULT,
                                    content=f"Task: {task_data['command']} (Node: {task_data['target_node']})",
                                    metadata=task_data
                                ),
                                ttl=7*24*3600
                            )
                        except Exception as me:
                            logger.error(f"Failed to save memory: {me}")

                    return task_data
                    
                except ValueError as ve:
                    logger.warning(f"Validation failed (attempt {attempt}): {ve}")
                    last_error = ve
                    
                    # Prepare retry message
                    if attempt < max_retries:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user", 
                            "content": f"Previous response was invalid JSON or schema violation: {str(ve)}. Please strictly follow the JSON format requirements."
                        })
                        continue
                    else:
                        raise TaskParsingError(content, str(ve), attempt)
                        
            except TaskParsingError:
                raise
            except Exception as e:
                # Catch unexpected errors during LLM call or processing
                if attempt == max_retries:
                    error_details = traceback.format_exc()
                    logger.error(f"Task parsing error (final attempt): {str(e)}\n{error_details}")
                    raise HTTPException(status_code=500, detail=f"Task parsing error: {str(e)}")
                logger.warning(f"Attempt {attempt} failed: {e}")
                
    # Should not reach here if exceptions are raised correctly
    raise HTTPException(status_code=500, detail="Task parsing failed unexpectedly")
