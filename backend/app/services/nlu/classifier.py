import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

class QueryIntent(str, Enum):
    SQL_QUERY = "SQL_QUERY"       # Precision lookup, aggregation
    KG_QUERY = "KG_QUERY"         # Trends, relationships, distribution
    RAG_QUERY = "RAG_QUERY"       # Text retrieval, summarization
    STRUCTURED_QUERY = "STRUCTURED_QUERY" # Structured data query with high confidence
    UNKNOWN = "UNKNOWN"

class IntentClassifier:
    _instance = None
    
    def __init__(self):
        # In real implementation, inject LLM client here
        pass

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def classify(self, question: str) -> QueryIntent:
        """
        Classifies the user question into an intent using semantic understanding.
        """
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
        sql_keywords = ["多少", "统计", "总数", "排名", "top", "count", "sum", "average", "avg", "max", "min", "列表", "list"]
        
        if any(w in question.lower() for w in sql_keywords):
            # Check for structured query confidence
            confidence = self._calculate_confidence(question)
            if confidence >= 0.85:
                return QueryIntent.STRUCTURED_QUERY
            return QueryIntent.SQL_QUERY

        # 4. Semantic Classification (LLM path fallback)
        logger.info(f"Classifying intent for: {question}")
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
