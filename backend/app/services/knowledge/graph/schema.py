"""
Architecture: Graph Schema Definition & Ontology Contracts

First Principles (第一性原理): 
数据确定性 (Data Determinism)。一个没有严格 Schema 约束的图数据库，在多轮迭代后会迅速退化为数据沼泽 (Data Swamp)。
所有的节点和边在注入 (Ingestion) 之前，必须符合严格的图谱本体契约 (Ontology Contract)。

Trade-offs (权衡): 
在应用层进行强类型校验（如基于 Pydantic 的验证）会消耗 CPU 算力（增加延迟），
但换来的是图谱遍历 (Graph Traversal) 时的 100% 可预测性，避免了下游查询服务因数据污染而崩溃。
"""

from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Set, Tuple
from enum import Enum

class EntityType(str, Enum):
    """
    实体类型枚举。
    所有节点必须属于以下定义的有限域 (Finite Domain) 之一。
    """
    DOCUMENT = "DOCUMENT"
    CHUNK = "CHUNK"
    CONCEPT = "CONCEPT"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    EVENT = "EVENT"

class RelationType(str, Enum):
    """
    关系类型枚举。
    边必须使用这些明确定义的谓词 (Predicates)。
    """
    CONTAINS = "CONTAINS"
    RELATES_TO = "RELATES_TO"
    BELONGS_TO = "BELONGS_TO"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    MENTIONS = "MENTIONS"
    
# 本体三元组拓扑约束 (Source Type, Relation, Target Type)
# 只有在这个集合中声明的边结构，才允许被写入图谱数据库
VALID_TRIPLETS: Set[Tuple[EntityType, RelationType, EntityType]] = {
    (EntityType.DOCUMENT, RelationType.CONTAINS, EntityType.CHUNK),
    (EntityType.CHUNK, RelationType.MENTIONS, EntityType.CONCEPT),
    (EntityType.CHUNK, RelationType.MENTIONS, EntityType.PERSON),
    (EntityType.PERSON, RelationType.BELONGS_TO, EntityType.ORGANIZATION),
    (EntityType.PERSON, RelationType.PARTICIPATES_IN, EntityType.EVENT),
    (EntityType.CONCEPT, RelationType.RELATES_TO, EntityType.CONCEPT),
}

class NodeSchema(BaseModel):
    """节点本体模型"""
    id: str = Field(..., description="全局唯一标识符 (例如 UUIDv7 或内容的哈希值)")
    type: EntityType = Field(..., description="节点的实体类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="灵活的属性载体")
    
    @model_validator(mode='after')
    def validate_properties(self) -> 'NodeSchema':
        # 预留护城河：未来可以基于不同的 EntityType，对 properties 内部的必填字段进行更深层次的校验
        # 比如：如果是 PERSON，则 properties 必须包含 name
        return self

class EdgeSchema(BaseModel):
    """边本体模型"""
    source_id: str = Field(..., description="源节点ID")
    source_type: EntityType = Field(..., description="源节点类型")
    target_id: str = Field(..., description="目标节点ID")
    target_type: EntityType = Field(..., description="目标节点类型")
    relation: RelationType = Field(..., description="边关系")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="关系权重，用于 GraphRAG 中的路径衰减计算")
    properties: Dict[str, Any] = Field(default_factory=dict, description="边的额外属性 (如溯源出处 source_chunk_id)")
    
    @model_validator(mode='after')
    def validate_ontology(self) -> 'EdgeSchema':
        """
        核心防线：强制进行本体契约校验
        """
        triplet = (self.source_type, self.relation, self.target_type)
        if triplet not in VALID_TRIPLETS:
            raise ValueError(
                f"Ontology Violation: 三元组拓扑不合法 {triplet}。该关系未在系统图谱本体契约中注册。"
            )
        return self

class GraphSchemaRegistry:
    """
    动态本体注册表 (Singleton)
    用于在多租户/多图谱场景下，允许业务层在运行时动态注册或覆写本体规则。
    """
    _version: str = "1.0.0"
    _strict_mode: bool = True
    
    @classmethod
    def enforce_strict_mode(cls, enable: bool) -> None:
        """动态切换校验等级 (降级策略)"""
        cls._strict_mode = enable
