import networkx as nx
import os
import shutil
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from pypinyin import lazy_pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class RelationFixService:
    def __init__(self):
        # Calculate base dir: backend/app/services/relation_fix_service.py -> ... -> Tiga
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.graph_path = os.path.join(self.base_dir, "backend/data/lightrag_store/graph_chunk_entity_relation.graphml")
        self.backup_dir = os.path.join(self.base_dir, "backend/data/backups")
        self.log_file = os.path.join(self.base_dir, "backend/data/relation_fix.log")
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _get_graph(self) -> nx.Graph:
        if not os.path.exists(self.graph_path):
            # Create an empty graph if it doesn't exist for testing purposes
            G = nx.Graph()
            return G
        try:
            return nx.read_graphml(self.graph_path)
        except Exception as e:
            logger.error(f"Error reading graph file: {e}")
            raise

    def _save_graph(self, G: nx.Graph):
        try:
            nx.write_graphml(G, self.graph_path)
        except Exception as e:
            logger.error(f"Error saving graph file: {e}")
            raise

    def _log_action(self, action: str, details: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {action} - {details}\n"
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write log: {e}")

    def backup_graph(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"graph_backup_{timestamp}.graphml")
        if os.path.exists(self.graph_path):
            shutil.copy2(self.graph_path, backup_path)
            self._log_action("BACKUP", f"Created backup at {backup_path}")
            return backup_path
        return ""

    def restore_backup(self, backup_filename: Optional[str] = None) -> bool:
        if not backup_filename:
            # Find latest backup
            if not os.path.exists(self.backup_dir):
                return False
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.endswith(".graphml")])
            if not backups:
                return False
            backup_filename = backups[-1]
        
        src = os.path.join(self.backup_dir, backup_filename)
        if not os.path.exists(src):
            return False
            
        shutil.copy2(src, self.graph_path)
        self._log_action("RESTORE", f"Restored from {src}")
        return True

    def detect_relations(self, main_node: str, keyword: str) -> List[Dict[str, Any]]:
        G = self._get_graph()
        
        # Check if main_node exists (exact match)
        main_node_exists = False
        for node in G.nodes():
            if node == main_node:
                main_node_exists = True
                break
        
        if not main_node_exists:
            # Try partial match or just return empty
            pass
            
        suggestions = []
        for n in G.nodes():
            if keyword in n and n != main_node:
                if not G.has_edge(main_node, n) and not G.has_edge(n, main_node):
                    suggestions.append({
                        "source": main_node,
                        "target": n,
                        "type": "related", 
                        "reason": f"Node name contains '{keyword}'"
                    })
        return suggestions

    def apply_fix(self, fixes: List[Dict[str, Any]]) -> int:
        if not fixes:
            return 0
            
        self.backup_graph()
        G = self._get_graph()
        count = 0
        
        for fix in fixes:
            src = fix.get("source")
            tgt = fix.get("target")
            if not src or not tgt:
                continue
                
            # Add edge
            # Ensure nodes exist (NetworkX adds them automatically, but good to be aware)
            attrs = {
                "weight": 1.0,
                "description": fix.get("description", f"{tgt} is related to {src}"),
                "keywords": fix.get("keywords", ""),
                "source_id": "manual_fix_tool",
                "created_at": datetime.now().isoformat()
            }
            # Add custom attributes
            for k, v in fix.get("attributes", {}).items():
                attrs[k] = v
                
            G.add_edge(src, tgt, **attrs)
            count += 1
            
        if count > 0:
            self._save_graph(G)
            self._log_action("FIX", f"Applied {count} relation fixes")
            
        return count

    def create_relation(self, source: str, target: str, rel_type: str, attributes: Dict[str, Any]) -> bool:
        self.backup_graph()
        G = self._get_graph()
        
        attrs = attributes.copy()
        attrs["label"] = rel_type
        attrs["source_id"] = "manual_create_tool"
        attrs["created_at"] = datetime.now().isoformat()
        
        G.add_edge(source, target, **attrs)
                   
        self._save_graph(G)
        self._log_action("CREATE", f"Created relation {source} -> {target} ({rel_type})")
        return True
        
    def get_logs(self, limit: int = 100) -> List[str]:
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
            return lines[-limit:]
        except Exception:
            return []

    def _is_fuzzy_match(self, query: str, text: str) -> bool:
        """
        Check if query characters appear in text in order (non-continuous subsequence).
        """
        q_idx = 0
        t_idx = 0
        while q_idx < len(query) and t_idx < len(text):
            if query[q_idx] == text[t_idx]:
                q_idx += 1
            t_idx += 1
        return q_idx == len(query)

    def search_nodes(self, query: str, limit: int = 20) -> List[str]:
        G = self._get_graph()
        results = []
        seen = set()
        
        query = query.strip().lower()
        if not query:
            return []
            
        keywords = query.split()
        # Enable pinyin if pypinyin is available and query contains only ascii chars
        enable_pinyin = PYPINYIN_AVAILABLE and all(ord(c) < 128 for c in query)
        
        for n in G.nodes():
            if len(results) >= limit:
                break
                
            node_name = str(n)
            if node_name in seen:
                continue
                
            node_name_lower = node_name.lower()
            
            # 1. Exact/Substring match (High priority)
            is_substring = True
            for kw in keywords:
                if kw not in node_name_lower:
                    is_substring = False
                    break
            
            if is_substring:
                results.append(node_name)
                seen.add(node_name)
                continue
                
            # 2. Pinyin match (Medium priority)
            if enable_pinyin:
                try:
                    # Calculate pinyin only if substring match fails
                    py_list = lazy_pinyin(node_name)
                    py_full = "".join(py_list)
                    py_first = "".join([p[0] for p in py_list if p])
                    
                    is_pinyin = True
                    for kw in keywords:
                        if kw not in py_full and kw not in py_first:
                            is_pinyin = False
                            break
                    
                    if is_pinyin:
                        results.append(node_name)
                        seen.add(node_name)
                        continue
                except Exception:
                    pass
            
            # 3. Fuzzy subsequence match (Low priority)
            # Only apply if single keyword to avoid noise
            if len(keywords) == 1:
                if self._is_fuzzy_match(keywords[0], node_name_lower):
                    results.append(node_name)
                    seen.add(node_name)
                    continue

        return results

    def get_node_relations(self, node_id: str) -> Dict[str, Any]:
        G = self._get_graph()
        if node_id not in G:
            return {"nodes": [], "edges": []}
            
        # Get ego graph (radius 1)
        # Using a subgraph logic manually to ensure we format it correctly
        nodes = {node_id: {"id": node_id, "label": node_id}}
        edges = []
        
        for neighbor in G.neighbors(node_id):
            nodes[neighbor] = {"id": neighbor, "label": neighbor}
            edge_data = G.get_edge_data(node_id, neighbor)
            edges.append({
                "source": node_id,
                "target": neighbor,
                "data": edge_data
            })
            
        return {"nodes": list(nodes.values()), "edges": edges}

relation_fix_service = RelationFixService()
