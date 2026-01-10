import aiohttp
import json
import asyncio
from app.core.config import settings

async def _call_llm(final_input: str, model: str, api_key: str):
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant specialized in information extraction. Extract data precisely."},
            {"role": "user", "content": final_input}
        ],
        "temperature": 0.1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    text = await response.text()
                    print(f"LLM Request failed: {response.status} {text}")
                    return None
    except Exception as e:
        print(f"LLM Error: {e}")
        return None

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
            valid_results = [r for r in results if r]
            if valid_results:
                # If parsing failed, just join them with newlines
                return {"status": "success", "content": "\n\n".join(valid_results)}
        
        return {"status": "success", "content": merged_content}
        
    else:
        # Single call
        if "{text_content}" in prompt:
            final_input = prompt.replace("{text_content}", text_content)
        else:
            final_input = prompt.replace("{{text_content}}", text_content)
            
        content = await _call_llm(final_input, model, real_api_key)
        
        if content:
            return {"status": "success", "content": content}
        else:
            return {"status": "error", "content": "LLM request failed"}
