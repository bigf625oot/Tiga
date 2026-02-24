import asyncio
from typing import List, Optional
# [Fix] Import mcp directly to avoid pywintypes error on Windows
# 'FastMCP' uses 'mcp' under the hood which might trigger windows specific imports
# But if 'mcp' package is installed and 'pywin32' is installed, it should work.
# The error "No module named 'pywintypes'" suggests pywin32 is not installed or environment issue.
# However, user says it is installed.
# Let's try to wrap the import to be safe or debug.

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    # Fallback or re-raise with clear message
    raise ImportError(f"Failed to import FastMCP. Please ensure 'mcp' and 'pywin32' (on Windows) are installed. Error: {e}")

from app.services.rag.engines.lightrag import lightrag_engine

# Initialize MCP Server
try:
    mcp = FastMCP("LightRAG Knowledge Service")
except Exception as e:
    # If FastMCP fails to initialize (e.g. pywin32 missing on Windows), log and provide a dummy decorator
    import logging
    logging.warning(f"Failed to initialize FastMCP: {e}. Knowledge tools will be unavailable.")
    
    class MockMCP:
        def tool(self):
            def decorator(func):
                return func
            return decorator
    mcp = MockMCP()

@mcp.tool()
async def search_knowledge_base(query: str, num_documents: int = 5, doc_ids: Optional[List[int]] = None) -> str:
    """
    Search the knowledge base for relevant document chunks using vector similarity.
    
    Args:
        query: The search query to find relevant information.
        num_documents: The number of document chunks to return (default: 5).
        doc_ids: Optional list of document IDs to filter the search scope.
    """
    try:
        # Check if LightRAG is initialized
        if not lightrag_engine.rag:
            return "Knowledge base service is not initialized yet. Please contact administrator."
            
        # Directly call the singleton engine
        results = lightrag_engine.search_chunks(query, top_k=num_documents, doc_ids=doc_ids)
        
        if not results:
            return "No relevant documents found."
            
        # Format output as a readable string for the LLM
        response = []
        for i, r in enumerate(results, 1):
            title = r.get('title', 'Unknown Source')
            content = r.get('content', '').strip()
            score = r.get('score', 0.0)
            doc_id = r.get('doc_id', 'N/A')
            
            response.append(f"[{i}] Source: {title} (DocID: {doc_id}, Score: {score:.4f})\n{content}\n")
            
        return "\n".join(response)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"

@mcp.tool()
async def query_knowledge_graph(query: str, mode: str = "mix") -> str:
    """
    Perform an advanced graph-based search on the knowledge base.
    This provides capabilities similar to the "Knowledge Center" hybrid retrieval.
    
    Args:
        query: The question to ask.
        mode: Search mode.
              - 'mix' (default): Hybrid search combining vector search (chunks) and graph search (entities/relations). Best for most questions.
              - 'local': Focus on specific entities mentioned in the query and their immediate neighbors in the graph.
              - 'global': High-level summary across the entire knowledge base, useful for "What is the main theme?" type questions.
              - 'naive': Simple vector search only (faster but less context).
    """
    try:
        # Check if LightRAG is initialized
        if not lightrag_engine.rag:
            return "Knowledge base service is not initialized yet. Please contact administrator."

        # Use LightRAG's query_async method which supports mix, local, global modes
        # This matches the capabilities of the Knowledge Center frontend
        return await lightrag_engine.query_async(query, mode=mode)
    except Exception as e:
        return f"Error querying knowledge graph: {str(e)}"

@mcp.tool()
async def get_graph_structure(doc_id: Optional[int] = None) -> str:
    """
    Get the knowledge graph structure (nodes and edges).
    Use this to visualize or understand the relationships between entities.
    
    Args:
        doc_id: Optional Document ID to filter the graph. If provided, only returns the subgraph related to this document.
    """
    try:
        from app.models.knowledge import KnowledgeDocument
        doc = None
        if doc_id:
             # Create a dummy document object with just ID to satisfy the interface
             # or fetch real doc if needed. LightRAG get_graph_data uses doc.id for filtering.
             doc = KnowledgeDocument(id=doc_id, filename="", oss_key="")
        
        data = lightrag_engine.get_graph_data(doc=doc)
        
        # Summarize for LLM consumption (full JSON might be too large)
        nodes_count = len(data.get("nodes", {}))
        edges_count = len(data.get("edges", {}))
        
        summary = f"Graph Structure Summary:\nNodes: {nodes_count}\nEdges: {edges_count}\n"
        
        # List top 10 important nodes
        nodes = list(data.get("nodes", {}).values())
        if nodes:
             summary += "\nTop Entities:\n"
             # Sort by some metric if available, or just take first few
             for n in nodes[:10]:
                 name = n.get("name", "Unknown")
                 etype = n.get("type", "Entity")
                 summary += f"- {name} ({etype})\n"
                 
        return summary
    except Exception as e:
        return f"Error retrieving graph structure: {str(e)}"
