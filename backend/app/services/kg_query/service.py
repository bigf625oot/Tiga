import json
import logging
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.services.rag.engines.lightrag import lightrag_engine
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChartConfig(BaseModel):
    title: str
    chart_type: str  # bar, line, pie, radar, scatter, graph
    data: Dict[str, Any]

class KGQueryService:
    """
    Service to handle Natural Language -> Graph Query -> Chart Generation
    """
    _instance = None
    
    def __init__(self):
        self.enable_mock = getattr(settings, "ENABLE_MOCK_KG_FALLBACK", False)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_chart(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point: NL -> Chart JSON
        """
        logger.info(f"Generating chart for: {question}")
        
        # 1. Real Implementation: Query LightRAG Subgraph
        try:
            # Increase top_k to improve recall
            subgraph = lightrag_engine.query_subgraph(question, top_k=10)
            if subgraph and subgraph.get("nodes"):
                node_count = len(subgraph.get('nodes'))
                edge_count = len(subgraph.get('edges', {}))
                logger.info(f"LightRAG found {node_count} nodes and {edge_count} edges for query.")
                
                # If we have nodes but no edges, it might be a loose collection of entities.
                # We still try to visualize it.
                return self._format_subgraph_to_echarts(subgraph, question)
            else:
                logger.warning(f"No subgraph found in LightRAG for query: {question}. Check if knowledge graph is built and entities match.")
        except Exception as e:
            logger.error(f"LightRAG subgraph query failed: {e}", exc_info=True)

        # 2. Try Mock/Hardcoded Logic (Fallback for demos)
        # Only if explicitly enabled
        if self.enable_mock:
            logger.info("Attempting mock fallback for KG query...")
            cypher_query = self._nl_to_cypher(question)
            if cypher_query:
                graph_result = self._execute_cypher(cypher_query)
                if graph_result:
                    return self._format_to_echarts(graph_result, question)

        return None

    def _nl_to_cypher(self, question: str) -> str:
        """
        Mock LLM translation.
        """
        # Match keywords for test case "展示近30天各品类销售额趋势"
        if ("销售" in question and "品类" in question) or ("趋势" in question and "销售" in question):
            return "MATCH (o:Order)-[:BELONGS_TO]->(c:Category) WHERE o.date >= date() - duration('P30D') RETURN c.name, sum(o.amount)"
        
        # Match keywords for "Order" query to test data loading
        if "订单" in question and "用户" in question:
            return "MATCH (o:E_Order)-[:R_PlacedBy]->(u:E_User) RETURN o.label, u.label"
            
        return ""

    def _execute_cypher(self, query: str) -> List[Dict[str, Any]]:
        """
        Mock Graph Execution.
        """
        logger.info(f"Executing Cypher: {query}")
        normalized_query = " ".join(query.split())
        
        # Case 1: Hardcoded Aggregation (for Chart)
        if "sum(o.amount)" in normalized_query:
            return [
                {"category": "Electronics", "amount": 15000},
                {"category": "Clothing", "amount": 8000},
                {"category": "Home", "amount": 5000}
            ]
            
        # Case 2: Read from Mock DB File (for Data Verification)
        if "MATCH (o:E_Order)" in normalized_query:
            if os.path.exists(self.MOCK_DB_PATH):
                try:
                    with open(self.MOCK_DB_PATH, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        nodes = data.get("nodes", [])
                        edges = data.get("edges", [])
                        
                        # Simulate JOIN: Find Orders placed by Users
                        results = []
                        for edge in edges:
                            if edge["relation"] == "R_PlacedBy":
                                # Find User Node (Target)
                                user_node = next((n for n in nodes if n["id"] == edge["target"]), None)
                                # Find Order Node (Source)
                                order_node = next((n for n in nodes if n["id"] == edge["source"]), None)
                                
                                if user_node and order_node:
                                    results.append({
                                        "order": order_node.get("label", "Unknown Order"),
                                        "user": user_node.get("label", "Unknown User")
                                    })
                        return results
                except Exception as e:
                    logger.error(f"Failed to read mock graph: {e}")
                    return []
                    
        return []

    def _format_to_echarts(self, data: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """
        Adapter to convert tabular graph data to ECharts.
        """
        if not data:
            return {}
            
        # Heuristic 1: Category + Value -> Bar Chart
        if "category" in data[0] and "amount" in data[0]:
            categories = [item["category"] for item in data]
            values = [item["amount"] for item in data]
            
            return {
                "title": {"text": title},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": categories},
                "yAxis": {"type": "value"},
                "series": [{
                    "data": values,
                    "type": "bar",
                    "itemStyle": {"borderRadius": [4, 4, 0, 0]}
                }]
            }
            
        # Heuristic 2: Order + User -> Graph View (Force Directed)
        if "order" in data[0] and "user" in data[0]:
             # Convert tabular pairs to Graph Nodes/Links
            nodes = []
            links = []
            seen_nodes = set()
            
            for item in data:
                u, o = item["user"], item["order"]
                if u not in seen_nodes:
                    nodes.append({"name": u, "category": "User", "symbolSize": 30})
                    seen_nodes.add(u)
                if o not in seen_nodes:
                    nodes.append({"name": o, "category": "Order", "symbolSize": 20})
                    seen_nodes.add(o)
                links.append({"source": o, "target": u})
                
            return {
                "title": {"text": "Order-User Relationships"},
                "tooltip": {},
                "series": [{
                    "type": "graph",
                    "layout": "force",
                    "symbolSize": 30,
                    "roam": True,
                    "label": {"show": True},
                    "edgeSymbol": ['circle', 'arrow'],
                    "edgeSymbolSize": [4, 10],
                    "data": nodes,
                    "links": links,
                    "categories": [{"name": "User"}, {"name": "Order"}],
                    "force": {
                        "repulsion": 100
                    }
                }]
            }

        return {}

    def _format_subgraph_to_echarts(self, graph_data: Dict[str, Any], title: str) -> Dict[str, Any]:
        """
        Convert LightRAG subgraph (nodes/edges dict) to ECharts Graph.
        """
        nodes = []
        links = []
        categories = set()
        
        raw_nodes = graph_data.get("nodes", {})
        raw_edges = graph_data.get("edges", {})
        
        for nid, data in raw_nodes.items():
            ntype = data.get("type", "Entity")
            categories.add(ntype)
            nodes.append({
                "id": str(nid),
                "name": str(nid), 
                "category": ntype,
                "symbolSize": data.get("symbolSize", 15),
                "itemStyle": data.get("itemStyle", None),
                "draggable": True,
                "value": data.get("attributes", {}).get("description", "")[:50]
            })
            
        for eid, data in raw_edges.items():
            links.append({
                "source": str(data["source"]),
                "target": str(data["target"]),
                "value": data.get("label", "")
            })
            
        cats = [{"name": c} for c in sorted(categories)]
        
        return {
            "title": {"text": f"知识图谱: {title}", "subtext": f"实体: {len(nodes)}, 关系: {len(links)}"},
            "tooltip": {},
            "legend": [{"data": [c["name"] for c in cats]}],
            "series": [{
                "type": "graph",
                "layout": "force",
                "data": nodes,
                "links": links,
                "categories": cats,
                "roam": True,
                "label": {"show": True, "position": "right", "formatter": "{b}"},
                "force": {
                    "repulsion": 200, 
                    "edgeLength": 100,
                    "gravity": 0.1
                },
                "edgeSymbol": ['none', 'arrow'],
                "edgeLabel": {"show": True, "formatter": "{c}", "fontSize": 10}
            }]
        }
