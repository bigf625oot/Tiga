import json
import pathway as pw
from typing import Dict, Any
from app.services.pathway.operators.registry import OperatorRegistry

# 模拟 LLM 调用函数
def mock_llm_call(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate LLM call with latency and structured output.
    In production, this would use OpenAI/Anthropic API.
    """
    import time
    import random
    
    # Simulate network latency (stream processing might block, so in real world use async/thread)
    # But pathway UDFs are executed in parallel workers usually.
    # For simulation, we keep it simple.
    
    model = config.get("model", "gpt-3.5-turbo")
    
    # Simple rule-based simulation for demo purposes
    intent = "unknown"
    confidence = 0.5
    slots = {}
    
    if not isinstance(text, str):
        text = str(text)
        
    text_lower = text.lower()
    
    if "refund" in text_lower or "退款" in text_lower:
        intent = "refund_request"
        confidence = 0.95
        if "order" in text_lower:
            slots["order_id"] = "12345" # Mock extraction
    elif "status" in text_lower or "状态" in text_lower:
        intent = "check_status"
        confidence = 0.88
    elif "human" in text_lower or "人工" in text_lower:
        intent = "transfer_to_agent"
        confidence = 0.99
        
    return {
        "intent": intent,
        "confidence": confidence,
        "slots": slots,
        "model": model,
        "processing_time_ms": random.randint(100, 500)
    }

@OperatorRegistry.register("llm_intent")
def apply_llm_intent(table: pw.Table, config: Dict[str, Any]) -> pw.Table:
    """
    Applies LLM Intent Recognition to a text column.
    
    Config:
    - input_col: str (default: "content")
    - output_col: str (default: "intent_result")
    - model: str
    - prompt_template: str
    - ... other LLM params
    """
    input_col = config.get("input_col", "content")
    output_col = config.get("output_col", "intent_result")
    
    # Define the UDF
    def intent_recognizer(text: Any) -> str:
        if text is None:
            return json.dumps({"error": "Empty input"})
        try:
            result = mock_llm_call(str(text), config)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e), "intent": "fallback"})

    # Apply UDF
    # We assume the input table has the 'input_col'. 
    # If not, we might need to check schema or just let it fail at runtime.
    
    # Pathway's apply returns a new table with the new column
    # Note: We use **kwargs unpacking to add the new column dynamically
    return table.select(
        *table.columns,
        **{output_col: pw.apply(intent_recognizer, table[input_col])}
    )

def mock_knowledge_retrieval(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate RAG retrieval.
    """
    import random
    
    top_k = config.get("top_k", 3)
    score_threshold = config.get("score_threshold", 0.7)
    
    # Mock knowledge base
    mock_docs = [
        {"content": "Tiga is a powerful data integration platform.", "score": 0.95, "source": "intro.md"},
        {"content": "It supports ETL, CDC, and Reverse ETL.", "score": 0.88, "source": "features.md"},
        {"content": "Users can define pipelines using a visual editor.", "score": 0.82, "source": "guide.md"},
        {"content": "The backend is built with Python and FastAPI.", "score": 0.75, "source": "architecture.md"},
        {"content": "This is an irrelevant document about cooking.", "score": 0.12, "source": "random.txt"},
    ]
    
    # Simulate filtering and ranking
    results = []
    for doc in mock_docs:
        # Simulate some semantic matching (randomly drop some based on threshold if we were real)
        # Here we just return the static list filtered by threshold
        if doc["score"] >= score_threshold:
            results.append(doc)
            
    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": query,
        "retrieved_docs": results[:top_k],
        "total_hits": len(results)
    }

@OperatorRegistry.register("knowledge_retrieval")
def apply_knowledge_retrieval(table: pw.Table, config: Dict[str, Any]) -> pw.Table:
    """
    Applies Knowledge Retrieval (RAG) to a query column.
    
    Config:
    - query_column: str (default: "content")
    - top_k: int (default: 3)
    - score_threshold: float (default: 0.7)
    """
    query_col = config.get("query_column", "content")
    # Output is fixed structure, maybe just "retrieval_result"
    output_col = "retrieval_result"
    
    def retriever(query: Any) -> str:
        if query is None:
            return json.dumps({"error": "Empty query"})
        try:
            result = mock_knowledge_retrieval(str(query), config)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    return table.select(
        *table.columns,
        **{output_col: pw.apply(retriever, table[query_col])}
    )
