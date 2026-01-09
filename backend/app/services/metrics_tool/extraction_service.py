import aiohttp
import json
from app.core.config import settings

async def run_extraction(prompt: str, text_content: str, model: str = "qwen-plus"):
    """
    运行提取任务：调用 LLM API 执行提取任务
    """
    
    # 替换 Prompt 中的占位符
    if "{text_content}" in prompt:
        final_input = prompt.replace("{text_content}", text_content)
    else:
        final_input = prompt.replace("{{text_content}}", text_content)
    
    # Use Aliyun/Dashscope configuration if available, otherwise fallback or error
    # Note: The original repo used a generic OpenAI-compatible endpoint. 
    # We will use Dashscope (Aliyun) as configured in settings.
    
    api_key = settings.ALIYUN_APP_KEY # This might be confusing, usually it's API KEY.
    # Let's assume we use the same ALIBABA_CLOUD_BEARER_TOKEN or ALIYUN_ACCESS_KEY_SECRET 
    # But for LLM (Dashscope), usually we need a DASHSCOPE_API_KEY.
    # For now, let's use ALIBABA_CLOUD_BEARER_TOKEN as a placeholder or try to find a proper key in config.
    
    # Actually, in `recordings.py`, we saw `aliyun_asr_service`. Let's check `config.py` again.
    # Config has ALIYUN_ACCESS_KEY_SECRET and ALIYUN_APP_KEY (for ASR?).
    
    # Let's try to use OpenAI client if available or just http request to Dashscope compatible endpoint.
    # For simplicity, I will implement a generic OpenAI-compatible request here, 
    # assuming the user will configure an OPENAI_API_KEY or similar.
    
    # Since we don't have a dedicated LLM config yet, I'll add a placeholder using one of the keys.
    # Or better, I will assume the environment provides an OpenAI-compatible endpoint.
    
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" # Dashscope OpenAI compatible endpoint
    real_api_key = settings.ALIBABA_CLOUD_BEARER_TOKEN or "sk-placeholder" # You need to set this!

    headers = {
        "Authorization": f"Bearer {real_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant specialized in information extraction. You should extract data precisely according to the definition."},
            {"role": "user", "content": final_input}
        ],
        "temperature": 0.1 # Lower temperature for extraction
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    return {"status": "success", "content": content}
                else:
                    text = await response.text()
                    return {"status": "error", "content": f"Request failed: {response.status} {text}"}
            
    except Exception as e:
        return {"status": "error", "content": f"Error: {str(e)}"}
