import jieba
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.knowledge_base import kb_service, UPLOAD_DIR
from app.services.lightrag_service import lightrag_service
from app.services.model_factory import ModelFactory
from app.models.knowledge import KnowledgeDocument
from app.models.llm_model import LLMModel
from app.services.oss_service import oss_service
from pathlib import Path
import io
import PyPDF2
import asyncio

logger = logging.getLogger(__name__)

class QAService:
    """
    问答服务类，提供基于文档的混合检索问答功能。
    整合了 BM25 关键词检索、向量语义检索和知识图谱检索。
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _read_document_content(self, doc: KnowledgeDocument) -> str:
        """
        读取文档内容，支持从本地或 OSS 获取。
        逻辑复用了 kb_service 中的部分代码，进行了简化。
        """
        filename = doc.filename or ""
        file_path = UPLOAD_DIR / filename
        raw_data = None

        # 1. 尝试从本地读取
        if not file_path.exists() and doc.oss_key:
             file_path = UPLOAD_DIR / Path(doc.oss_key).name
        
        if file_path.exists():
            try:
                raw_data = file_path.read_bytes()
            except Exception:
                pass

        # 2. 如果本地不存在，尝试从 OSS 读取
        if not raw_data and doc.oss_key:
            try:
                raw_data = oss_service.bucket.get_object(doc.oss_key).read()
            except Exception:
                pass
        
        if not raw_data:
            return ""

        text = ""
        file_ext = Path(filename).suffix.lower()
        
        try:
            # 3. 根据文件类型解析文本
            if file_ext == ".pdf":
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(raw_data))
                text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            else:
                # 尝试多种编码格式解析文本
                for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
                    try:
                        text = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if not text:
                    text = raw_data.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"读取文档内容出错: {e}")
            return ""
            
        return text

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        简单的文本分块，用于 BM25 检索。
        相比图谱提取，这里使用更小的分块大小以便更精准定位关键词上下文。
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text[start:end])
            start = end - overlap
            if start >= end:
                start = end
        return chunks

    async def bm25_search(self, doc: KnowledgeDocument, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        对文档内容执行 BM25 关键词检索。
        """
        try:
            # 在线程中运行以避免阻塞异步事件循环
            return await asyncio.to_thread(self._bm25_search_sync, doc, query, top_k)
        except Exception as e:
            logger.error(f"BM25 检索失败: {e}")
            return []

    def _bm25_search_sync(self, doc: KnowledgeDocument, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        同步执行 BM25 检索的具体实现。
        """
        text = self._read_document_content(doc)
        if not text:
            return []
        
        chunks = self._chunk_text(text)
        if not chunks:
            return []
            
        # 对文档块进行分词
        tokenized_corpus = [list(jieba.cut(chunk)) for chunk in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        
        # 对查询进行分词
        tokenized_query = list(jieba.cut(query))
        scores = bm25.get_scores(tokenized_query)
        
        # 获取得分最高的 top_k 个结果
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for i in top_indices:
            if scores[i] > 0:
                results.append({
                    "content": chunks[i],
                    "score": float(scores[i]),
                    "source": "bm25"
                })
        return results

    async def vector_search(self, doc: KnowledgeDocument, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        使用 kb_service 在向量数据库中进行语义检索。
        """
        try:
            # 我们通过文件名过滤（kb_service.search 中已实现）
            # 虽然如果是海量数据这可能较慢，但当前架构下是可行的
            refs, filtered = kb_service.search(query, allowed_names=[doc.filename], top_k=top_k*2) # 获取更多候选项以便过滤
            
            results = []
            for r in refs:
                results.append({
                    "content": r.get("preview", ""),
                    "score": r.get("score", 0.0),
                    "source": "vector"
                })
            return results[:top_k]
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def graph_search(self, doc_id: int, query: str, db: AsyncSession, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        在本地知识图谱中搜索与查询匹配的节点。
        """
        try:
            graph_data = await kb_service.get_document_graph_local(db, doc_id)
            if not graph_data or "nodes" not in graph_data:
                return []
            
            nodes = graph_data["nodes"]
            results = []
            
            # 简单的关键词匹配
            # TODO: 后续可以考虑对节点名称进行向量嵌入，以支持语义匹配
            query_tokens = set(jieba.cut(query))
            
            for node_id, node in nodes.items():
                name = node.get("name", "")
                attrs = node.get("attributes", {})
                
                score = 0
                if name in query:
                    score += 10
                
                # 检查 token 重叠度
                node_tokens = set(jieba.cut(name))
                overlap = len(query_tokens.intersection(node_tokens))
                score += overlap * 2
                
                if score > 0:
                    # 格式化节点信息作为上下文
                    related_info = f"实体: {name} (类型: {node.get('type')})\n属性: {attrs}\n"
                    
                    results.append({
                        "content": related_info,
                        "score": score,
                        "source": "graph"
                    })
            
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []

    async def qa(self, doc_id: int, query: str, db: AsyncSession) -> Dict[str, Any]:
        """
        主问答函数 (Refined with LightRAG).
        使用 LightRAG 进行高效的全局混合检索。
        """
        try:
            # 确保 LightRAG 已初始化 (使用 DB 配置)
            await lightrag_service.ensure_initialized(db)
            
            # 使用 LightRAG 进行查询
            # mode="mix" 结合了图谱和向量检索
            import asyncio
            answer = await asyncio.to_thread(lightrag_service.query, query, mode="mix")
            
            return {
                "answer": answer,
                "sources": [{"source": "lightrag", "content": "Answer generated based on Global Knowledge Graph"}]
            }
        except Exception as e:
            logger.error(f"LightRAG QA 失败: {e}")
            return {"answer": "抱歉，生成回答时遇到错误。", "sources": []}

qa_service = QAService.get_instance()
