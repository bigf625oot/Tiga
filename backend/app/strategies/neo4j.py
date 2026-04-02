from typing import List, AsyncGenerator, Any, Dict
import asyncio
from neo4j import AsyncGraphDatabase

from app.strategies.base import BaseSource
from app.models.domain import MetadataModel, DataChunk
from app.utils.crypto_utils import decrypt_field


class Neo4jSource(BaseSource):
    """
    Neo4j 图数据库数据源策略实现。
    支持连接测试、标签/关系类型元数据获取以及 Cypher 查询数据提取。
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.driver = None

    async def _get_driver(self):
        """初始化并返回 Neo4j 异步驱动程序"""
        if self.driver:
            return self.driver
        
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 7687)
        uri = self.config.get('url') or f"bolt://{host}:{port}"
        
        user = self.config.get('username') or self.config.get('user', 'neo4j')
        
        # 处理密码解密
        password = self.config.get('password')
        if self.config.get('password_encrypted'):
            password = decrypt_field(self.config['password_encrypted'])
            
        encrypted = self.config.get('ssl', False)
        
        # 创建异步驱动
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password), encrypted=encrypted)
        return self.driver

    async def test_connection(self) -> Dict[str, Any]:
        """测试 Neo4j 连接是否可用"""
        try:
            driver = await self._get_driver()
            async with driver.session() as session:
                # 执行查询以验证连接并获取统计数据
                # 获取总节点数
                node_res = await session.run("MATCH (n) RETURN count(n) AS c")
                node_record = await node_res.single()
                node_count = node_record["c"] if node_record else 0
                
                # 获取总关系数
                rel_res = await session.run("MATCH ()-[r]->() RETURN count(r) AS c")
                rel_record = await rel_res.single()
                rel_count = rel_record["c"] if rel_record else 0
                
                # 获取节点标签数 (实体类型数)
                labels_res = await session.run("CALL db.labels() YIELD label RETURN count(label) AS c")
                labels_record = await labels_res.single()
                entity_types = labels_record["c"] if labels_record else 0

            return {
                "success": True, 
                "message": "成功连接到 Neo4j 数据库。",
                "details": {
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "entity_types": entity_types
                }
            }
        except Exception as e:
            return {"success": False, "error_type": "CONNECTION_FAILED", "message": str(e)}

    async def fetch_metadata(self) -> List[MetadataModel]:
        """获取 Neo4j 的元数据（节点标签和关系类型）"""
        driver = await self._get_driver()
        metadata_list = []
        
        try:
            async with driver.session() as session:
                # 0. 尝试获取所有 Databases (图空间)
                try:
                    result = await session.run("SHOW DATABASES YIELD name")
                    async for record in result:
                        db_name = record["name"]
                        metadata_list.append(MetadataModel(
                            name=db_name,
                            type="database",
                            description=f"图数据库/空间: {db_name}",
                            schema_info={}
                        ))
                except Exception:
                    # 社区版或权限不足时可能会报错，忽略该错误
                    pass

                # 1. 获取所有节点标签及其大致数量
                result = await session.run("CALL db.labels()")
                async for record in result:
                    label = record[0]
                    count_res = await session.run(f"MATCH (n:`{label}`) RETURN count(n) AS c")
                    count_data = await count_res.single()
                    count = count_data["c"] if count_data else 0
                    
                    metadata_list.append(MetadataModel(
                        name=label,
                        type="node_label",
                        description=f"节点标签: {label}",
                        schema_info={"count": count}
                    ))
                
                # 2. 获取所有关系类型及其大致数量
                result = await session.run("CALL db.relationshipTypes()")
                async for record in result:
                    rel_type = record[0]
                    count_res = await session.run(f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) AS c")
                    count_data = await count_res.single()
                    count = count_data["c"] if count_data else 0
                    
                    metadata_list.append(MetadataModel(
                        name=rel_type,
                        type="relationship_type",
                        description=f"关系类型: {rel_type}",
                        schema_info={"count": count}
                    ))
                    
            return metadata_list
        except Exception as e:
            raise Exception(f"Failed to fetch Neo4j metadata: {str(e)}")

    async def fetch_data(self, **kwargs) -> AsyncGenerator[DataChunk, None]:
        """
        根据标签、关系类型或自定义 Cypher 语句流式提取数据。
        """
        driver = await self._get_driver()
        
        label = kwargs.get('label')
        rel_type = kwargs.get('rel_type')
        query = kwargs.get('query') or kwargs.get('table_name')
        
        limit = kwargs.get('limit', 100)
        offset = kwargs.get('offset', 0)
        
        # 构造最终的 Cypher 语句
        if query and any(x in query.upper() for x in ["MATCH", "RETURN", "CALL"]):
            final_query = query
            if "LIMIT" not in query.upper():
                final_query += f" SKIP {offset} LIMIT {limit}"
        elif label or (query and not any(x in query.upper() for x in ["MATCH", "RETURN", "CALL"])):
            target_label = label or query
            final_query = f"MATCH (n:`{target_label}`) RETURN n SKIP {offset} LIMIT {limit}"
        elif rel_type:
            final_query = f"MATCH ()-[r:`{rel_type}`]->() RETURN r SKIP {offset} LIMIT {limit}"
        else:
            final_query = f"MATCH (n) RETURN n SKIP {offset} LIMIT {limit}"
            
        try:
            async with driver.session() as session:
                result = await session.run(final_query)
                
                chunk_data = []
                async for record in result:
                    row = {}
                    for key, value in record.items():
                        # 格式化节点和关系为可序列化的字典
                        if hasattr(value, "labels"): # 节点对象
                            row[key] = {
                                "id": getattr(value, "element_id", getattr(value, "id", None)),
                                "labels": list(value.labels),
                                "properties": dict(value.items())
                            }
                        elif hasattr(value, "type"): # 关系对象
                            row[key] = {
                                "id": getattr(value, "element_id", getattr(value, "id", None)),
                                "type": value.type,
                                "start_node": getattr(value.start_node, "element_id", getattr(value.start_node, "id", None)),
                                "end_node": getattr(value.end_node, "element_id", getattr(value.end_node, "id", None)),
                                "properties": dict(value.items())
                            }
                        else:
                            row[key] = value
                    
                    chunk_data.append(row)
                    
                    if len(chunk_data) >= 100:
                        yield DataChunk(data=chunk_data, count=len(chunk_data), has_more=True)
                        chunk_data = []
                
                if chunk_data:
                    yield DataChunk(data=chunk_data, count=len(chunk_data), has_more=False)
                elif offset == 0:
                    yield DataChunk(data=[], count=0, has_more=False)
        except Exception as e:
            raise Exception(f"Neo4j query execution failed: {str(e)}")

    async def close(self):
        """关闭驱动连接"""
        if self.driver:
            await self.driver.close()
            self.driver = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
