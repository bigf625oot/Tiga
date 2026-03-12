import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SemanticLayer:
    _instance = None
    
    def __init__(self):
        # In a real system, this would load from a database or KG
        # For PoC, we use a hardcoded dictionary simulating "Business Concepts"
        self.concepts = {
            "营收": {
                "sql_ref": "orders.total_amount", 
                "desc": "订单表中的总金额字段 (total_amount)"
            },
            "销售额": {
                "sql_ref": "orders.total_amount", 
                "desc": "同营收，指订单总金额"
            },
            "大客户": {
                "sql_ref": "users.vip_level >= 3", 
                "desc": "VIP等级大于等于3的用户"
            },
            "活跃用户": {
                "sql_ref": "users.last_login > DATE('now', '-30 days')", 
                "desc": "最近30天内有登录记录的用户"
            },
            "转化率": {
                "sql_ref": "COUNT(orders.id) / COUNT(users.id)", 
                "desc": "订单数除以用户总数"
            },
            "客单价": {
                "sql_ref": "AVG(orders.total_amount)", 
                "desc": "平均每单金额"
            }
        }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SemanticLayer()
        return cls._instance

    def get_context_hints(self, question: str) -> str:
        """
        Analyzes the question and returns relevant semantic hints for SQL generation.
        """
        hints = []
        # Simple keyword matching for PoC
        # In production, use vector similarity or KG traversal
        for term, concept in self.concepts.items():
            if term in question:
                hint = f"- '{term}' 对应业务逻辑: {concept['desc']} (参考 SQL片段: {concept['sql_ref']})"
                hints.append(hint)
        
        if hints:
            return "\n[业务语义提示 (Business Context)]:\n" + "\n".join(hints) + "\n"
        return ""

    def add_concept(self, term: str, sql_ref: str, desc: str):
        """
        Allows dynamic addition of concepts (e.g. from KG sync)
        """
        self.concepts[term] = {"sql_ref": sql_ref, "desc": desc}
