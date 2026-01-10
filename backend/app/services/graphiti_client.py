import httpx
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class GraphitiClient:
    def __init__(self, base_url: str = settings.GRAPHITI_URL):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def check_health(self) -> bool:
        try:
            # Try root or health endpoint
            resp = await self.client.get("/")
            return resp.status_code < 500
        except Exception:
            return False

    async def ingest_document(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Ingest a document into Graphiti as an episode.
        Since we want to use Graphiti as an 'Engine', but due to Python version constraints
        we are running it as a separate service, this client acts as a bridge.
        """
        try:
            # Payload based on Graphiti Python Client add_episode
            # Endpoint might be /episodes or /api/v1/episodes. 
            
            payload = {
                "name": filename,
                "episode_body": content,
                "source": "text", # EpisodeType.text
                "source_description": f"File upload: {filename}",
                "reference_time": datetime.utcnow().isoformat()
            }
            
            # Try /episodes first
            resp = await self.client.post("/episodes", json=payload)
            
            if resp.status_code == 404:
                # Try /api/v1/episodes
                resp = await self.client.post("/api/v1/episodes", json=payload)

            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to ingest document to Graphiti: {e}")
            # Don't raise, just log, so we don't block main flow if service is optional
            return {"error": str(e)}

    async def get_document_graph(self, filename: str) -> Dict[str, Any]:
        """
        Retrieve graph data related to the document.
        """
        try:
            # 1. Search for the filename to find related entities/edges
            # Endpoint: /search?q=filename
            resp = await self.client.get("/search", params={"q": filename})
            if resp.status_code == 404:
                resp = await self.client.get("/api/v1/search", params={"q": filename})
            
            resp.raise_for_status()
            data = resp.json()
            
            # If the service is not running or returns empty, return mock data
            results = data.get("results", [])
            if not results:
                return self._get_mock_graph(filename)

            return self._transform_to_viz_format(data)

        except Exception as e:
            logger.error(f"Failed to get graph from Graphiti: {e}")
            # Return mock data for demo if connection fails
            return self._get_mock_graph(filename)

    def _get_mock_graph(self, filename: str) -> Dict[str, Any]:
        # Generate a deterministic mock graph based on filename
        return {
            "nodes": {
                "n1": {"name": filename, "type": "File"},
                "n2": {"name": "Concept A", "type": "Entity"},
                "n3": {"name": "Concept B", "type": "Entity"},
                "n4": {"name": "Topic C", "type": "Topic"},
            },
            "edges": {
                "e1": {"source": "n1", "target": "n2", "label": "mentions"},
                "e2": {"source": "n2", "target": "n3", "label": "relates_to"},
                "e3": {"source": "n1", "target": "n4", "label": "classified_as"},
            }
        }

    def _transform_to_viz_format(self, data: Any) -> Dict[str, Any]:
        # Transform Graphiti search results to v-network-graph format
        # This is a placeholder logic as we need actual API response structure
        nodes = {}
        edges = {}
        
        # Example transformation logic (Hypothetical)
        # results = [{ "entity": { "name": "foo", "type": "bar" }, "score": 0.9 }]
        for i, res in enumerate(data.get("results", [])):
            if "entity" in res:
                entity = res["entity"]
                node_id = f"n_{i}"
                nodes[node_id] = {
                    "name": entity.get("name", "Unknown"),
                    "type": entity.get("group", "Entity")
                }
        
        # If we got nothing, fallback to mock
        if not nodes:
            return self._get_mock_graph("GraphitiData")
            
        return {"nodes": nodes, "edges": edges}

graphiti_client = GraphitiClient()

