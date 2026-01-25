import aiohttp
import json
import asyncio
from app.core.config import settings

async def _call_llm(final_input: str, model: str, api_key: str):
    preset_models = ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long"]
    
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    headers = {
        "Content-Type": "application/json"
    }
    real_model_id = model
    
    try:
        # If not preset, try to find in DB
        if model not in preset_models:
            from app.db.session import AsyncSessionLocal
            from app.models.llm import LLMModel
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(LLMModel).filter(LLMModel.model_id == model))
                db_model = result.scalars().first()
                
                if db_model:
                    real_model_id = db_model.model_id
                    if db_model.base_url:
                        base_url = db_model.base_url.rstrip('/')
                        # Simple heuristic: if url doesn't end with /v1 and doesn't look like full path, append /v1
                        # But be careful not to break working urls.
                        # DeepSeek often works with https://api.deepseek.com (which implies /v1/chat/completions or /chat/completions)
                        # Let's trust the user's base_url mostly, but handle DeepSeek specifically if needed.
                    elif db_model.provider == "deepseek":
                         base_url = "https://api.deepseek.com"
                    
                    if db_model.api_key:
                        api_key = db_model.api_key

        headers["Authorization"] = f"Bearer {api_key}"
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant specialized in information extraction. Extract data precisely."},
            {"role": "user", "content": final_input}
        ]
        
        payload = {
            "model": real_model_id,
            "messages": messages,
            "temperature": 0.1
        }
        
        # DeepSeek R1 handling
        # R1 (DeepSeek Reasoner) might return 'reasoning_content'.
        
        # Construct Endpoint
        # If base_url already has /chat/completions, use it.
        if "/chat/completions" in base_url:
            endpoint = base_url
        else:
            # If base_url ends with /v1, append /chat/completions
            if base_url.endswith("/v1"):
                endpoint = f"{base_url}/chat/completions"
            else:
                # If just host, try appending /chat/completions (standard OAI)
                endpoint = f"{base_url}/chat/completions"
                
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload, timeout=120) as response:
                if response.status == 200:
                    result = await response.json()
                    choice = result['choices'][0]['message']
                    content = choice.get('content', '')
                    
                    # If content is empty but reasoning_content exists (DeepSeek R1 case)
                    reasoning = choice.get('reasoning_content', '')
                    if not content and reasoning:
                        return f"[Thinking Process]\n{reasoning}\n\n[Answer]\n(Model returned reasoning but no content)"
                    elif content and reasoning:
                        # Optionally show reasoning? For extraction, we usually just want the JSON.
                        # But for debugging, maybe we prepend it if it's not JSON?
                        # Let's just return content for now as extraction expects JSON.
                        return content
                    
                    return content
                else:
                    text = await response.text()
                    return f"Error: LLM Request failed with status {response.status}. URL: {endpoint}. Details: {text}"
                    
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"Error: {str(e)}"

def _chunk_text(text, chunk_size=20000, overlap=1000):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks

def _merge_results(results):
    merged_list = []
    
    for res in results:
        if not res: continue
        try:
            # Clean markdown
            clean_res = res.strip()
            if clean_res.startsWith('```'):
                clean_res = clean_res.replace('```json', '').replace('```', '').strip()
            
            # Try parsing
            data = json.loads(clean_res)
            if isinstance(data, list):
                merged_list.extend(data)
            elif isinstance(data, dict):
                merged_list.append(data)
        except:
            # If not valid JSON, maybe just append text or ignore
            pass
            
    return json.dumps(merged_list, ensure_ascii=False, indent=2)

async def run_extraction(prompt: str, text_content: str, model: str = "qwen-plus"):
    """
    运行提取任务：调用 LLM API 执行提取任务。
    对于超长文本，自动进行分块并行处理。
    """
    real_api_key = settings.ALIBABA_CLOUD_BEARER_TOKEN or "sk-placeholder"
    
    # Threshold for chunking (approx 15k-20k tokens)
    # If using qwen-long, we can skip chunking for very large contexts up to a point, 
    # but even qwen-long has limits (e.g. 10M tokens is huge, but let's stick to simple logic).
    # Actually qwen-long handles 10M, so we don't need chunking for qwen-long unless it's insanely huge.
    CHUNK_THRESHOLD = 30000
    
    if len(text_content) > CHUNK_THRESHOLD and model != "qwen-long":
        print(f"[Extraction] Text length {len(text_content)} exceeds threshold. Using Map-Reduce with {model}.")
        chunks = _chunk_text(text_content)
        tasks = []
        
        for chunk in chunks:
            if "{text_content}" in prompt:
                chunk_input = prompt.replace("{text_content}", chunk)
            else:
                chunk_input = prompt.replace("{{text_content}}", chunk)
            
            tasks.append(_call_llm(chunk_input, model, real_api_key))
            
        results = await asyncio.gather(*tasks)
        merged_content = _merge_results(results)
        
        # If merge resulted in empty list but we had raw text results (maybe parse failed), 
        # fallback to returning concatenated raw text or the first non-empty result
        if merged_content == "[]":
            valid_results = [r for r in results if r and not r.startswith("Error:")]
            if valid_results:
                # If parsing failed, just join them with newlines
                return {"status": "success", "content": "\n\n".join(valid_results)}
            
            # If all were errors
            error_results = [r for r in results if r and r.startswith("Error:")]
            if error_results:
                 return {"status": "error", "content": error_results[0]}
        
        return {"status": "success", "content": merged_content}
        
    else:
        # Single call
        if "{text_content}" in prompt:
            final_input = prompt.replace("{text_content}", text_content)
        else:
            final_input = prompt.replace("{{text_content}}", text_content)
            
        content = await _call_llm(final_input, model, real_api_key)
        
        # Check if content is an error message
        if content and content.startswith("Error:"):
             return {"status": "error", "content": content}
        
        if content:
            return {"status": "success", "content": content}
        else:
            return {"status": "error", "content": "LLM returned empty response"}
