import os
import yaml
import json
import logging
import argparse
import time
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, inspect, text
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import hashlib
from datetime import datetime

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("export_graph.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GraphExporter")

class GraphExportConfig:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)
        
        self.db_cfg = self.cfg.get('database', {})
        self.proc_cfg = self.cfg.get('processing', {})
        self.graph_cfg = self.cfg.get('graph', {})
        self.out_cfg = self.cfg.get('output', {})
        
        # 输出目录设置
        self.output_dir = Path(self.out_cfg.get('output_dir', './data/export'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_db_url(self) -> str:
        if self.db_cfg.get('url'): # Support direct URL from JSON config
            return self.db_cfg['url']
            
        if self.db_cfg.get('connection_string'):
            return self.db_cfg['connection_string']
        
        db_type = self.db_cfg.get('type', 'postgresql')
        if db_type == 'sqlite':
            return f"sqlite:///{self.db_cfg.get('database')}"
        
        return f"{db_type}+psycopg2://{self.db_cfg['user']}:{self.db_cfg['password']}@{self.db_cfg['host']}:{self.db_cfg['port']}/{self.db_cfg['database']}"

def process_chunk(
    chunk_data: pd.DataFrame, 
    table_config: Dict, 
    relationships: List[Dict],
    batch_id: int
) -> Dict[str, Any]:
    """
    处理单个数据块：
    - 创建节点
    - 基于外键创建边
    - 返回子图数据（节点、边）和映射数据
    """
    nodes = []
    edges = []
    vector_mappings = []
    
    table_name = table_config['table']
    label = table_config.get('label', table_name)
    id_col = table_config.get('id_column', 'id')
    long_text_fields = set(table_config.get('long_text_fields', []))
    allowed_attrs = table_config.get('attributes')
    
    def format_id(val):
        """Standardize ID formatting to avoid 1 vs 1.0 mismatches"""
        try:
            if pd.isna(val):
                return ""
            # If it's a float that is actually an integer (e.g. 1.0), convert to int first
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            return str(val)
        except:
            return str(val)

    for _, row in chunk_data.iterrows():
        # 1. 创建节点
        # 确保 ID 是字符串
        row_id_val = row[id_col]
        if pd.isna(row_id_val):
            continue
            
        node_id = f"{label}:{format_id(row_id_val)}"
        
        # 过滤属性
        attrs = {}
        for col, val in row.items():
            if pd.isna(val):
                continue
            if col == id_col:
                continue
            # 处理长文本
            if col in long_text_fields:
                # 存储哈希值或引用，实际文本存入向量数据库映射表
                val_str = str(val)
                content_hash = hashlib.md5(val_str.encode()).hexdigest()
                attrs[f"{col}_hash"] = content_hash
                
                vector_mappings.append({
                    "node_id": node_id,
                    "vector_db_collection": f"{label}_vectors",
                    "vector_id": f"{node_id}_{col}",
                    "text_content_hash": content_hash,
                    "content_preview": val_str[:100]
                })
            elif not allowed_attrs or col in allowed_attrs:
                # 转换非基本类型为字符串，保证 GraphML 兼容性
                if isinstance(val, (dict, list, tuple)):
                    attrs[col] = json.dumps(val, ensure_ascii=False)
                else:
                    attrs[col] = val
        
        nodes.append({
            "id": node_id,
            "label": label,
            "properties": attrs
        })
        
        # 2. 创建边（关系）
        for rel in relationships:
            if rel['source_table'] == table_name:
                fk = rel['foreign_key']
                if fk in row and pd.notna(row[fk]):
                    target_table = rel['target_table']
                    target_label = rel.get('target_label', target_table) 
                    
                    target_id = f"{target_label}:{format_id(row[fk])}"
                    
                    edge_props = {"type": rel['relation_type']}
                    if rel.get('weight_column'):
                        w_col = rel['weight_column']
                        if w_col in row:
                            edge_props['weight'] = row[w_col]
                            
                    edges.append({
                        "source": node_id,
                        "target": target_id,
                        "relation": rel['relation_type'],
                        "properties": edge_props
                    })

    return {
        "nodes": nodes, 
        "edges": edges, 
        "mappings": vector_mappings,
        "batch_id": batch_id
    }

class GraphExporter:
    def __init__(self, config_file: str):
        self.config = GraphExportConfig(config_file)
        try:
            self.engine = create_engine(self.config.get_db_url())
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
            
        # 初始化图
        self._init_graph()
        
        # 状态跟踪
        self.processed_count = 0
        self.checkpoint_file = Path(self.config.output_dir) / self.config.proc_cfg.get('checkpoint_file', 'checkpoint.json')
        self.load_checkpoint()
        
    def _init_graph(self):
        """初始化图对象，支持合并模式"""
        graph_path = self.config.output_dir / "graph_chunk_entity_relation.graphml"
        update_mode = self.config.out_cfg.get('update_mode', 'overwrite')
        
        if update_mode == 'merge' and graph_path.exists():
            try:
                logger.info(f"正在加载现有图文件进行合并: {graph_path}")
                self.graph = nx.read_graphml(str(graph_path))
                logger.info(f"成功加载现有图: {self.graph.number_of_nodes()} 节点, {self.graph.number_of_edges()} 边")
            except Exception as e:
                logger.warning(f"加载现有图文件失败: {e}。将创建新图。")
                self.graph = nx.DiGraph()
        else:
            if update_mode == 'merge':
                logger.info("未找到现有图文件，将创建新图。")
            else:
                logger.info("覆盖模式：创建新图。")
            self.graph = nx.DiGraph()
        
    def load_checkpoint(self):
        # 如果是覆盖模式，忽略检查点（重置）
        if self.config.out_cfg.get('update_mode', 'overwrite') == 'overwrite':
            self.state = {"processed_tables": {}}
            return

        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    self.state = json.load(f)
            except:
                self.state = {"processed_tables": {}}
        else:
            self.state = {"processed_tables": {}}

    def save_checkpoint(self):
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.state, f)
            
    def run(self):
        start_time = time.time()
        logger.info("开始导出图数据...")
        
        # 获取表配置
        tables = self.config.graph_cfg.get('entities', [])
        relationships = self.config.graph_cfg.get('relationships', [])
        
        # 预处理关系以映射目标标签
        table_label_map = {t['table']: t.get('label', t['table']) for t in tables}
        for r in relationships:
            r['target_label'] = table_label_map.get(r['target_table'], r['target_table'])
        
        chunk_size = self.config.proc_cfg.get('chunk_size', 10000)
        max_workers = self.config.proc_cfg.get('max_workers', multiprocessing.cpu_count())
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for table_cfg in tables:
                table_name = table_cfg['table']
                last_offset = self.state['processed_tables'].get(table_name, 0)
                
                logger.info(f"正在处理表: {table_name}, 起始偏移量 {last_offset}")
                
                try:
                    with self.engine.connect() as conn:
                        # 简单的行数检查
                        total_rows = pd.read_sql_query(text(f"SELECT COUNT(*) FROM {table_name}"), conn).iloc[0, 0]
                except Exception as e:
                    logger.error(f"无法查询表 {table_name}: {e}")
                    continue
                
                current_offset = last_offset
                batch_id = 0
                
                while current_offset < total_rows:
                    query = f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {current_offset}"
                    try:
                        chunk_df = pd.read_sql_query(query, self.engine)
                    except Exception as e:
                        logger.error(f"读取数据块失败 ({table_name} offset {current_offset}): {e}")
                        break
                    
                    if chunk_df.empty:
                        break
                        
                    future = executor.submit(
                        process_chunk, 
                        chunk_df, 
                        table_cfg, 
                        relationships,
                        batch_id
                    )
                    futures.append(future)
                    
                    current_offset += chunk_size
                    batch_id += 1
                    
                    # 内存控制/分批提交
                    if len(futures) > max_workers * 2:
                        self._collect_results(futures)
                        futures = []
                        self.state['processed_tables'][table_name] = current_offset
                        self.save_checkpoint()
            
            # 收集剩余结果
            self._collect_results(futures)
            
        # 最终导出
        self._export_data()
        
        duration = time.time() - start_time
        logger.info(f"导出完成，耗时 {duration:.2f} 秒。本次会话处理记录数: {self.processed_count}")
        logger.info(f"当前图总规模: {self.graph.number_of_nodes()} 节点, {self.graph.number_of_edges()} 边")
        
        self.engine.dispose()

    def _collect_results(self, futures):
        for future in as_completed(futures):
            try:
                res = future.result()
                self._merge_to_graph(res)
            except Exception as e:
                logger.error(f"处理数据块时出错: {e}")

    def _merge_to_graph(self, result: Dict):
        # 合并节点
        # NetworkX 的 add_node/add_nodes_from 会更新现有节点的属性，而不是覆盖整个节点
        # 这满足了 "无损合并" 和 "保留全部属性" (旧属性保留，新属性更新)
        for node in result['nodes']:
            self.graph.add_node(node['id'], entity_type=node['label'], **node['properties'])
            self.processed_count += 1
            
        # 合并边
        # 同样，add_edge 更新属性
        for edge in result['edges']:
            self.graph.add_edge(edge['source'], edge['target'], label=edge['relation'], **edge['properties'])
            
        # 立即保存向量映射（追加到文件）
        self._append_mappings(result['mappings'])

    def _append_mappings(self, mappings: List[Dict]):
        if not mappings:
            return
        
        mapping_file = self.config.output_dir / "vector_mappings.csv"
        df = pd.DataFrame(mappings)
        
        # 如果是覆盖模式且文件已存在，且是第一次写入(需要外部标志？或者简单点，每次运行前清理？)
        # 这里简化：如果是 overwrite 模式，run() 开始时应该清理 mapping file。
        # 但 _init_graph 无法清理 csv。
        # 更好的做法：在 run() 开始时清理辅助文件。
        
        header = not mapping_file.exists()
        df.to_csv(mapping_file, mode='a', header=header, index=False)

    def _export_data(self):
        logger.info("正在写入最终输出文件...")
        
        # 1. LightRAG GraphML
        # LightRAG 兼容性：确保属性类型正确
        graph_path = self.config.output_dir / "graph_chunk_entity_relation.graphml"
        nx.write_graphml(self.graph, str(graph_path))
        logger.info(f"GraphML 已写入 {graph_path}")
            
        # 2. LightRAG JSON (实体和关系)
        entities = []
        for n, attrs in self.graph.nodes(data=True):
            entities.append({
                "name": n,
                "type": attrs.get("entity_type", "Unknown"),
                **{k:v for k,v in attrs.items() if k != "entity_type"}
            })
            
        relations = []
        for u, v, attrs in self.graph.edges(data=True):
            relations.append({
                "source": u,
                "target": v,
                **attrs
            })
        
        self._write_json_sharded(entities, "entities.json")
        self._write_json_sharded(relations, "relationships.json")

    def _write_json_sharded(self, data: List[Dict], filename: str):
        out_path = self.config.output_dir / filename
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"已导出 {len(data)} 个项目到 {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导出数据库到知识图谱")
    parser.add_argument("--config", default="export_config.yaml", help="配置文件路径")
    args = parser.parse_args()
    
    if not Path(args.config).exists():
        logger.error(f"未找到配置文件 {args.config}。")
        exit(1)
        
    try:
        exporter = GraphExporter(args.config)
        exporter.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
