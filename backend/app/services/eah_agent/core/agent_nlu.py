import json
import re
import logging
import asyncio
from typing import Dict, Any, Optional, List, Set, Union
from enum import Enum
from pydantic import BaseModel, Field, ValidationError, validator, root_validator

from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory
from app.core.config import settings

logger = logging.getLogger("agno.nlu")

# --- 1. 严格的领域定义 (Domain Schemas) ---

class IntentType(str, Enum):
    CHAT = "chat"           # 闲聊、通用知识、网页实时搜索
    TASK = "task"           # 自规划任务（爬虫、监控）
    DATA_QUERY = "data_query" # 内部结构化数据库 SQL 查询
    KG_QA = "kg_qa"         # 知识图谱/非结构化 RAG
    TEAM = "team"           # 团队协作/多 Agent 编排
    WORKFLOW = "workflow"   # 标准 SOP 流程
    UNKNOWN = "unknown"

class IntentResult(BaseModel):
    """NLU 解析结果协议：强制执行结构化输出"""
    intent: IntentType = Field(..., description="The classified intent of the user.")
    confidence: float = Field(..., ge=0, le=1.0)
    reasoning: str = Field(..., description="CoT: Brief explanation of why this intent was chosen.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities and params.")

    @root_validator(pre=True)
    def normalize_parameters(cls, values):
        if isinstance(values, dict):
            if "parameters" not in values and "task_params" in values:
                values["parameters"] = values.get("task_params") or {}
        return values

    @validator("confidence")
    def cap_confidence(cls, v):
        return round(v, 2)

    @property
    def task_params(self) -> Dict[str, Any]:
        return self.parameters

# --- 2. 高性能前置检查 (Fast-Path Logic) ---

class NluFastPath:
    _GREETINGS: Set[str] = {
        "你好", "hello", "hi", "在吗", "嗨", "您好", "早上好", "下午好", 
        "晚上好", "哈喽", "hey", "hola", "help", "帮助"
    }

    @classmethod
    def match(cls, text: str) -> Optional[IntentResult]:
        """对于空输入或极简问候，直接返回，不消耗 Token 且延迟为 0"""
        clean_text = re.sub(r'[^\w\s]', '', text.strip().lower())
        if not clean_text or clean_text in cls._GREETINGS:
            return IntentResult(
                intent=IntentType.CHAT,
                confidence=1.0,
                reasoning="Matched fast-path greeting pattern.",
                parameters={}
            )
        return None

# --- 3. 核心 NLU 引擎 (The Orchestrator) ---

class NluService:
    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_record = llm_model
        self._model = None
        if llm_model:
            try:
                self._model = ModelFactory.create_model(llm_model)
            except Exception as e:
                logger.error(f"NLU Model initialization failed: {e}")

    async def analyze(self, user_input: str, timeout: float = 8.0) -> IntentResult:
        """
        异步分析意图：包含并行超时控制、JSON 修复和弹性降级。
        """
        # 1. 走快路径
        fast_result = NluFastPath.match(user_input)
        if fast_result:
            return fast_result

        # 2. 检查模型可用性
        if not self._model:
            return self._fallback("Model unavailable")

        # 3. 构造 Prompts (分离策略与逻辑)
        system_prompt = self._get_system_prompt()
        
        from agno.models.message import Message
        try:
            # 增加任务级超时，防止 NLU 阻塞整个 Pipeline
            response = await asyncio.wait_for(
                self._model.aresponse(
                    messages=[
                        Message(role="system", content=system_prompt),
                        Message(role="user", content=user_input)
                    ],
                    # 如果 Provider 支持，开启 JSON Mode
                    response_format={"type": "json_object"} if self._supports_json_mode() else None
                ),
                timeout=timeout
            )
            
            return self._robust_parse(response.content)

        except asyncio.TimeoutError:
            logger.warning(f"NLU timed out for input: {user_input[:50]}")
            return self._fallback("Analysis timed out")
        except Exception as e:
            logger.error(f"NLU analysis failed: {e}", exc_info=True)
            return self._fallback(str(e))

    def _get_system_prompt(self) -> str:
        """
        P10 级别 Prompt 技巧：
        1. 使用 XML/Markdown 结构增强 LLM 理解。
        2. 强调分类边界（尤其是 Chat 与 DataQuery 的区别）。
        3. 强制要求推理过程（CoT），大幅提升逻辑准确率。
        """
        return f"""You are the NLU Controller for an advanced Agent System.
Your mission is to classify user input into one of these categories:

<Categories>
- chat: General chit-chat, greetings, or PUBLIC web info (stocks, weather, news).
- task: Specific actions on the Openclaw platform (crawlers, monitors, automation).
- data_query: INTERNAL SQL database queries. Keywords: "our database", "sales report", "user count".
- kg_qa: Knowledge graph or unstructured RAG queries about entities/relationships.
- team: Requesting a group of agents or collaboration.
- workflow: Requesting a multi-step SOP or predefined pipeline.
</Categories>

<Instructions>
1. Evaluate the context deeply. If it sounds like an internal metric, use 'data_query'.
2. If the user asks for real-time web info, use 'chat' (which triggers search).
3. ALWAYS return valid JSON.
4. Provide a 'reasoning' field explaining your logic.
</Instructions>

<ResponseFormat>
{{
  "intent": "chat|task|data_query|kg_qa|team|workflow",
  "confidence": 0.0-1.0,
  "reasoning": "string",
  "parameters": {{ "key": "value" }}
}}
</ResponseFormat>
"""

    def _robust_parse(self, raw_content: str) -> IntentResult:
        """
        工业级 JSON 解析：
        1. 清理 Markdown 标签。
        2. 处理非标准空白。
        3. Pydantic 严格校验。
        """
        try:
            # 去除可能存在的 Markdown 代码块
            clean_content = re.sub(r"```json\s*|\s*```", "", raw_content).strip()
            
            # 容错：定位第一个 { 和最后一个 }
            start = clean_content.find('{')
            end = clean_content.rfind('}')
            if start != -1 and end != -1:
                clean_content = clean_content[start:end+1]

            data = json.loads(clean_content)
            return IntentResult(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"NLU Parse Error. Raw: {raw_content}. Error: {e}")
            return self._fallback("Parse failure")

    def _fallback(self, reason: str) -> IntentResult:
        """优雅降级策略：默认走 Chat，确保系统不中断"""
        return IntentResult(
            intent=IntentType.CHAT,
            confidence=0.0,
            reasoning=f"System fallback: {reason}",
            parameters={}
        )

    def _supports_json_mode(self) -> bool:
        """适配层：判断模型是否原生支持 JSON Object"""
        if not self.llm_record: return False
        provider = (self.llm_record.provider or "").lower()
        # OpenAI, DeepSeek, Azure, Groq 等通常支持
        return provider in ["openai", "deepseek", "azure", "groq"]
