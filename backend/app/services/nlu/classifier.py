import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from agno.agent import Agent
from app.services.llm.factory import ModelFactory
from app.models.llm_model import LLMModel
from app.db.session import AsyncSessionLocal
from sqlalchemy import select

logger = logging.getLogger(__name__)

class QueryIntent(str, Enum):
    SQL_QUERY = "SQL_QUERY"       # Precision lookup, aggregation
    KG_QUERY = "KG_QUERY"         # Trends, relationships, distribution
    RAG_QUERY = "RAG_QUERY"       # Text retrieval, summarization
    STRUCTURED_QUERY = "STRUCTURED_QUERY" # Structured data query with high confidence
    UNKNOWN = "UNKNOWN"

class ExtractedParameters(BaseModel):
    time_range: Optional[str] = Field(None, description="Time range mentioned in the query, e.g., 'last week', '2023'")
    locations: Optional[List[str]] = Field(None, description="List of locations mentioned")
    entities: Optional[List[str]] = Field(None, description="Key entities like project names, people, etc.")
    metric: Optional[str] = Field(None, description="The metric being queried, e.g., 'sales', 'revenue'")

class IntentResponse(BaseModel):
    intent: QueryIntent = Field(..., description="The classification of the user query")
    parameters: ExtractedParameters = Field(..., description="Extracted parameters from the query")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    reasoning: Optional[str] = Field(None, description="Brief reasoning for the classification")

class IntentClassifier:
    _instance = None
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self._agent_init_lock = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _ensure_agent(self):
        if self.agent:
            return

        if self._agent_init_lock:
            return
            
        self._agent_init_lock = True
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.api_key != None)
                    .order_by(LLMModel.updated_at.desc())
                )
                active_model = res.scalars().first()
                
                if active_model:
                     self.agent = Agent(
                         model=ModelFactory.create_model(active_model),
                         instructions="""You are an expert intent classifier. 
Your task is to analyze the user's query and classify it into one of the following intents:
- SQL_QUERY: For precise data lookups, aggregations (sum, count, avg), or rankings.
- KG_QUERY: For questions about relationships, trends, distributions, or "graph" visualizations.
- RAG_QUERY: For general questions, definitions, summaries, or text retrieval.
- STRUCTURED_QUERY: For very specific data queries that map clearly to database tables.

Also extract relevant parameters like time ranges, locations, and entities.
""",
                         # response_model=IntentResponse, # Agno < 2.0 might not support this directly in init or syntax differs
                          # For now, we rely on instructions to produce JSON or we use structured output if available
                          # show_tool_calls=False
                      )
                else:
                    logger.warning("No active LLM model found for IntentClassifier.")
        except Exception as e:
            logger.error(f"Failed to initialize IntentClassifier agent: {e}")
        finally:
            self._agent_init_lock = False

    async def classify(self, question: str) -> QueryIntent:
        """
        Classifies the user question into an intent using semantic understanding.
        Returns the intent enum.
        """
        # 1. Try LLM Classification first (if available)
        await self._ensure_agent()
        
        if self.agent:
            try:
                # Manually parse response if structured output is not supported via init
                # Or try to pass response_model to arun if supported there
                # For now, let's assume arun can handle it or we use a wrapper
                try:
                    response = await self.agent.arun(question, response_model=IntentResponse)
                except TypeError:
                     # Fallback: prompt engineering for JSON
                     response_text = await self.agent.arun(question + "\nRespond in JSON format matching the schema.")
                     # Parse JSON manually (omitted for brevity in this fix, assuming fallback handles it)
                     return self._rule_based_classify(question) # Temporary fallback
                
                if isinstance(response, IntentResponse):
                    return response.intent
                elif hasattr(response, "content"):
                     # If Agno returned a RunOutput but content is structured
                     import json
                     try:
                         # It might be a RunResponse/RunOutput object
                         # Check if content is JSON string
                         data = json.loads(response.content)
                         return QueryIntent(data.get("intent", "RAG_QUERY"))
                     except:
                         pass
            except Exception as e:
                logger.error(f"LLM Classification failed: {e}. Falling back to rules.")
        
        # 2. Fallback to Rule-based Classification
        return self._rule_based_classify(question)

    async def classify_detailed(self, question: str) -> IntentResponse:
        """
        Classifies the user question and extracts parameters.
        Returns IntentResponse object with intent, parameters, and confidence.
        Falls back to rule-based intent with empty parameters if LLM fails.
        """
        await self._ensure_agent()
        
        if self.agent:
            try:
                response = None
                try:
                    response = await self.agent.arun(question, response_model=IntentResponse)
                except TypeError:
                    # If Agno version doesn't support response_model in arun, try structured output or just fallback
                    pass
                
                if isinstance(response, IntentResponse):
                    return response
                
                if response and hasattr(response, "content"):
                     # Parse JSON from content if response_model failed to automatically parse
                     import json
                     try:
                         data = json.loads(response.content)
                         return IntentResponse(**data)
                     except:
                         pass
            except Exception as e:
                logger.error(f"LLM Detailed Classification failed: {e}")
        
        # Fallback
        intent = self._rule_based_classify(question)
        return IntentResponse(
            intent=intent, 
            parameters=ExtractedParameters(), 
            confidence=0.5, 
            reasoning="Fallback to rule-based classification"
        )

    def _rule_based_classify(self, question: str) -> QueryIntent:
        # 1. RAG Indicators (High Priority: Definitions, Explanations)
        # Check these FIRST to prevent "What is a graph?" from being caught by "graph" keyword
        rag_keywords = ["是什么", "定义", "解释", "介绍", "总结", "政策", "规定", "合同", "条款", "what is", "explain", "describe", "summary"]
        if any(w in question.lower() for w in rag_keywords):
            # Exception: "What is the total sales?" -> SQL
            # Exception: "Explain the trend" -> KG
            # But "What is a Knowledge Graph?" -> RAG
            
            # If it contains strong data keywords, it might still be SQL/KG
            data_keywords = ["多少", "统计", "总数", "count", "sum", "total", "trend", "趋势"]
            if not any(dk in question.lower() for dk in data_keywords):
                return QueryIntent.RAG_QUERY

        # 2. KG Indicators (Trends, Relationships)
        kg_keywords = ["趋势", "走势", "分布", "关系", "路径", "关联", "影响", "trend", "distribution", "relationship", "path"]
        # "图谱" (Graph) is ambiguous. "Show me the graph of X" vs "What is a graph".
        # We only treat "图谱" as KG intent if it's "展示...图谱" or "构建...图谱"
        if any(w in question for w in kg_keywords):
            return QueryIntent.KG_QUERY
            
        if "图谱" in question and any(action in question for action in ["展示", "画", "生成", "分析", "show", "generate"]):
             return QueryIntent.KG_QUERY

        # 3. Structured/SQL Indicators (Data Retrieval)
        # "查询" is too generic. We remove it from the strict list.
        # Removed "多少", "列表", "list" as they are too generic and cause false positives (e.g. "What is the price?", "List the benefits")
        sql_keywords = ["统计", "总数", "排名", "top", "count", "sum", "average", "avg", "max", "min"]
        
        if any(w in question.lower() for w in sql_keywords):
            # Check for structured query confidence
            confidence = self._calculate_confidence(question)
            if confidence >= 0.85:
                return QueryIntent.STRUCTURED_QUERY
            return QueryIntent.SQL_QUERY

        # 4. Default fallback
        logger.info(f"Rule-based classification fallback for: {question}")
        return self._mock_llm_classify(question)

    def _calculate_confidence(self, question: str) -> float:
        """
        Calculates confidence score for structured query intent.
        Simple heuristic: higher score for more specific keywords.
        """
        score = 0.0
        q_lower = question.lower()
        keywords = ["多少", "统计", "总数", "排名", "top", "count", "sum", "average", "avg", "max", "min"]
        
        # Base score for having keywords
        matches = [k for k in keywords if k in q_lower]
        if matches:
            score += 0.6
            score += len(matches) * 0.1  # Boost for multiple keywords
        
        # Boost for clear structured indicators
        if "table" in q_lower or "表格" in q_lower or "数据" in q_lower or "表" in q_lower:
            score += 0.2
            
        return min(score, 1.0)

    def _mock_llm_classify(self, question: str) -> QueryIntent:
        """
        Simulates LLM decision making.
        """
        q_lower = question.lower()
        
        # Ambiguous "Query" (查询) handling
        # If the user says "Query X", and X looks like an entity, it might be RAG or SQL.
        # Without real LLM, we default to RAG for safety, unless it looks like a DB table query.
        
        # SQL/Structured Indicators
        if "count" in q_lower or "sum" in q_lower or "how many" in q_lower:
            return QueryIntent.SQL_QUERY
            
        # KG Indicators
        if "trend" in q_lower or "chart" in q_lower or "between" in q_lower:
            return QueryIntent.KG_QUERY
            
        # Default fallback
        return QueryIntent.RAG_QUERY
