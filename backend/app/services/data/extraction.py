import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory

logger = logging.getLogger(__name__)


# --- Templates ---

# 极简版中文模板 (Token Optimized)
COT_TEMPLATE_CN_LITE = """
# Task
根据 # Definition 提供的定义，从 # Text 部分的文本中提取或计算指标：“{indicator_name}”。
{aliases_section}
# Definition
{definition}

# Rules
1. 提取符合定义的数值。{extraction_rule_text}。若无匹配数据，JSON格式请返回空列表 []，其他格式返回 "N/A"。
2. 严格检查单位和时间周期 (Period)。
3. 按此格式输出：{format_instruction}

# Text
{{text_content}}
"""

# 标准版中文 CoT 模板 (High Accuracy)
COT_TEMPLATE_CN = """
# Role
你是一位数据提取专家。任务是根据 # Definition 提供的定义，从 # Text 中提取或计算指标：“{indicator_name}”。
{aliases_section}
# Definition
{definition}

# Steps
1. **定位**: 寻找与指标相关的关键词及数值。
2. **验证**: 确认数值的单位和口径符合定义（{extraction_rule_text}）。
3. **输出**: 输出包含所有提取结果的列表（若无数据，JSON格式返回 []，其他格式返回 "N/A"）。

# Format
{format_instruction}

# Text
{{text_content}}
"""

# 英文版同理优化
COT_TEMPLATE_EN = """
# Task
Extract the indicator "{indicator_name}" from the text below.
{aliases_section}
# Definition
{definition}

# Rules
1. Extract values matching the definition. {extraction_rule_text}. If none found, return empty list [] for JSON, or "N/A" for others.
2. Verify units and time period.
3. Output format: {format_instruction}

# Text
{{text_content}}
"""


class DataExtractionService:
    def __init__(self):
        pass

    async def _get_model_client(self, model_id: str):
        """
        Get or create an Agno model client.
        """
        async with AsyncSessionLocal() as db:
            # Try to find specific model
            stmt = select(LLMModel).filter(LLMModel.model_id == model_id)
            result = await db.execute(stmt)
            db_model = result.scalars().first()

            if not db_model:
                # Fallback: try to find any active model if specific one not found, or just return None
                # But typically we want the specific model requested.
                # If not found, maybe we check if it's a known preset like 'qwen-plus' and see if we have an aliyun key?
                # For now, let's assume the user has configured it or we try to find a default.
                stmt = select(LLMModel).filter(LLMModel.is_active == True).order_by(LLMModel.updated_at.desc())
                result = await db.execute(stmt)
                db_model = result.scalars().first()

            if not db_model:
                raise ValueError(f"Model {model_id} not found and no active models available.")

            return ModelFactory.create_model(db_model)

    def _chunk_text(self, text: str, chunk_size: int = 20000, overlap: int = 1000) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += chunk_size - overlap
        return chunks

    def _merge_results(self, results: List[str]) -> str:
        merged_list = []

        for res in results:
            if not res:
                continue
            try:
                # Clean markdown
                clean_res = res.strip()
                if clean_res.startswith("```"):
                    # Remove first line (```json) and last line (```)
                    lines = clean_res.split("\n")
                    if len(lines) >= 2:
                        # minimal check
                        clean_res = "\n".join(lines[1:-1]).strip()

                # Try parsing
                data = json.loads(clean_res)
                if isinstance(data, list):
                    merged_list.extend(data)
                elif isinstance(data, dict):
                    merged_list.append(data)
            except Exception:
                # If not valid JSON, ignore
                pass

        return json.dumps(merged_list, ensure_ascii=False, indent=2)

    async def _call_llm(self, prompt: str, model_id: str) -> str:
        try:
            model = await self._get_model_client(model_id)
            
            # Agno model usage: model.response(messages)
            # We need to construct messages. 
            # The prompt in this service seems to be a full prompt string.
            # We can pass it as a user message.
            
            # However, Agno's `response` method might return an object. 
            # Usually `response.content` is the string.
            
            # Wait, `OpenAIChat` in Agno usually has a `run` or `response` method.
            # Let's assume `response` returns a `ModelResponse` object which has `content`.
            
            # Since I can't check Agno docs, I'll rely on common patterns or check `llm/factory.py` usage elsewhere.
            # `llm/factory.py` just returns the object.
            # I'll assume standard Agno usage: `response = model.response(messages=[{"role": "user", "content": prompt}])`
            
            response = model.response(messages=[{"role": "user", "content": prompt}])
            return response.content
        except Exception as e:
            logger.error(f"LLM Call Error: {e}")
            return f"Error: {str(e)}"

    async def run_extraction(self, prompt: str, text_content: str, model: str = "qwen-plus") -> Dict[str, Any]:
        """
        Run extraction task. Calls LLM API.
        Handles chunking for large texts.
        """
        CHUNK_THRESHOLD = 30000

        if len(text_content) > CHUNK_THRESHOLD and model != "qwen-long":
            logger.info(f"[Extraction] Text length {len(text_content)} exceeds threshold. Using Map-Reduce with {model}.")
            chunks = self._chunk_text(text_content)
            tasks = []

            for chunk in chunks:
                if "{text_content}" in prompt:
                    chunk_input = prompt.replace("{text_content}", chunk)
                else:
                    chunk_input = prompt.replace("{{text_content}}", chunk)

                tasks.append(self._call_llm(chunk_input, model))

            results = await asyncio.gather(*tasks)
            merged_content = self._merge_results(results)

            if merged_content == "[]":
                # Fallback: check if we have any valid text results that failed to parse
                valid_results = [r for r in results if r and not r.startswith("Error:")]
                if valid_results:
                    return {"status": "success", "content": "\n\n".join(valid_results)}
                
                # Check for errors
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

            content = await self._call_llm(final_input, model)

            if content and content.startswith("Error:"):
                return {"status": "error", "content": content}

            if content:
                return {"status": "success", "content": content}
            else:
                return {"status": "error", "content": "LLM returned empty response"}


extraction_service = DataExtractionService()


async def run_extraction(prompt: str, text_content: str, model: str = "qwen-plus") -> Dict[str, Any]:
    return await extraction_service.run_extraction(prompt, text_content, model)


def generate_prompt(
    name: str,
    definition: str,
    output_format: str = "JSON",
    language: str = "CN",
    lite_mode: bool = False,
    aliases: str = "",
    extraction_mode: str = "Multi",
    advanced_options: Optional[Dict[str, Any]] = None,
) -> str:
    # Select Template
    if language == "EN":
        template = COT_TEMPLATE_EN
    elif lite_mode:
        template = COT_TEMPLATE_CN_LITE
    else:
        template = COT_TEMPLATE_CN

    # Aliases
    aliases_section = ""
    if aliases:
        aliases_section = f"Aliases: {aliases}\n" if language == "EN" else f"别名: {aliases}\n"

    # Extraction Rules
    extraction_rule_text = ""
    if extraction_mode == "Single":
        extraction_rule_text = "Only extract the single most relevant value" if language == "EN" else "仅提取最相关的一个数值"
    else:
        extraction_rule_text = "Extract all matching values" if language == "EN" else "提取所有符合定义的数据"

    # Format Instruction
    format_instruction = "Return a JSON list of objects" if output_format == "JSON" else "Return text"

    # Advanced Options (inject into definition or rules)
    if advanced_options:
        # Just append key-values to definition for context
        extra_info = []
        for k, v in advanced_options.items():
            if v:
                extra_info.append(f"{k}: {v}")
        if extra_info:
            definition += "\nAdditional Context:\n" + "\n".join(extra_info)

    # Fill Template
    # Note: COT_TEMPLATE_CN has {indicator_name}, {aliases_section}, {definition}, {extraction_rule_text}, {format_instruction}
    # And {{text_content}} which should be preserved (it is preserved by double braces in template definition)
    
    prompt = template.format(
        indicator_name=name,
        aliases_section=aliases_section,
        definition=definition,
        extraction_rule_text=extraction_rule_text,
        format_instruction=format_instruction,
    )
    
    return prompt
