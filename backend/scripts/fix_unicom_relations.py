
import networkx as nx
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 图谱文件路径 - 使用绝对路径或相对于项目根目录的路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAPH_PATH = os.path.join(BASE_DIR, "backend/data/lightrag_store/graph_chunk_entity_relation.graphml")

def connect_branches(G, main_node, keyword):
    """
    通用函数：将包含指定关键字的节点连接到主节点
    """
    if main_node not in G:
        logger.warning(f"主节点 '{main_node}' 不在图谱中。")
        return 0

    # 查找所有包含关键字的节点
    target_nodes = []
    for n in G.nodes():
        if keyword in n and n != main_node:
            target_nodes.append(n)
    
    logger.info(f"[{main_node}] 找到 {len(target_nodes)} 个相关的'{keyword}'节点。")

    edges_added = 0
    for node in target_nodes:
        # 检查是否已经有连接
        if G.has_edge(node, main_node) or G.has_edge(main_node, node):
            logger.debug(f"节点 '{node}' 已经连接到 '{main_node}'，跳过。")
            continue
            
        # 添加连接边
        G.add_edge(main_node, node, 
                   weight=1.0, 
                   description=f"{node} 是 {main_node} 的分支机构或相关实体。", 
                   keywords="分支机构,隶属,包含",
                   source_id="manual_fix_script",
                   created_at="2025-02-10")
        edges_added += 1
        logger.info(f"已添加连接: {main_node} <--> {node}")
    
    return edges_added

def fix_relations():
    if not os.path.exists(GRAPH_PATH):
        # 尝试相对路径
        local_path = "backend/data/lightrag_store/graph_chunk_entity_relation.graphml"
        if os.path.exists(local_path):
            graph_file = local_path
        else:
            logger.error(f"图谱文件未找到: {GRAPH_PATH} 或 {local_path}")
            return
    else:
        graph_file = GRAPH_PATH

    logger.info(f"正在加载图谱: {graph_file}")
    try:
        G = nx.read_graphml(graph_file)
    except Exception as e:
        logger.error(f"加载图谱失败: {e}")
        return

    total_added = 0
    
    # 修复中国联通关系
    total_added += connect_branches(G, "中国联通", "联通")
    
    # 修复中国电信关系
    total_added += connect_branches(G, "中国电信", "电信")
    
    # 顺便修复中国移动关系（预防性）
    total_added += connect_branches(G, "中国移动", "移动")

    if total_added > 0:
        logger.info(f"共添加了 {total_added} 条新边。正在保存图谱...")
        try:
            nx.write_graphml(G, graph_file)
            logger.info("图谱保存成功！")
        except Exception as e:
            logger.error(f"保存图谱失败: {e}")
    else:
        logger.info("没有发现需要添加的新连接。")

if __name__ == "__main__":
    fix_relations()
