import logging
import asyncio
import uuid
import json
from typing import Optional, List, Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

# 内部引用
from app.models.llm_model import LLMModel
from app.services.platform.llm.factory import ModelFactory
from app.services.platform.llm.resolver import resolve_chat_llm_model
from app.services.agent.schemas.plan import (
    TaskPlan, 
    ExecutionPlan, 
    ExecutionTaskStep, 
    PlanValidationError,
    parse_task_plan
)

logger = logging.getLogger("eah.core.engines.planning")

class GraphCycleError(Exception):
    """图论验证异常：检测到环路或幽灵依赖"""
    pass

class PlanningEngine:
    """
    无状态规划引擎 (Stateless Planning Engine)
    核心特性：
    1. 彻底无状态化：消灭并发竞态条件，支持高并发安全调用。
    2. 确定性拓扑校验：引入 Kahn 算法进行 DAG 图论级防呆校验。
    3. 工业级容错解析：集成 TaskPlanParser 进行多路降级提取与自愈。
    4. 动态上下文降维：内置基础 Tool RAG 机制，防止 LLM 注意力坍塌。
    """
    def __init__(
        self, 
        db: AsyncSession, 
        llm_model: Optional[LLMModel] = None,
        tools: List[Any] = None,
        skills: List[Any] = None,
        mcp_servers: List[Any] = None
    ):
        self.db = db
        self.llm_model = llm_model
        # 资源注册表（不可变配置）
        self.tools = tools or []
        self.skills = skills or []
        self.mcp_servers = mcp_servers or []

    async def _filter_capabilities(self, user_goal: str, top_k: int = 15) -> str:
        """
        [降维打击] 动态能力检索引擎 (Tool RAG)
        第一性原理：当工具库膨胀时，全量注入会导致 Prompt 爆炸和 LLM 注意力坍塌。
        我们使用高维度的语义匹配 (Text Embedding) 来召回最相关的工具。
        """
        candidates = []
        for t in (self.tools + self.skills):
            name = getattr(t, "__name__", str(t))
            doc = (getattr(t, "__doc__") or "Executes specific logic.").strip().split('\n')[0]
            candidates.append({"name": name, "desc": doc, "type": "tool"})
            
        for server in self.mcp_servers:
            if hasattr(server, "tools"):
                for m in server.tools:
                    candidates.append({"name": m.name, "desc": m.description, "type": "mcp"})
        
        if len(candidates) <= top_k:
            selected = candidates
        else:
            # 引入深度语义向量检索 (Vector Embedding Similarity)
            try:
                # 尝试调用系统全局配置的 Embedding 服务
                from app.services.intelligence.knowledge.rag.service import QAService
                from app.services.intelligence.knowledge.rag.retrieval.providers import OpenAIEmbedder
                import numpy as np
                import math

                embed_model = await QAService._get_active_embedding_model(self.db)
                if embed_model and embed_model.api_key:
                    embedder = OpenAIEmbedder(
                        api_key=embed_model.api_key, 
                        base_url=embed_model.base_url, 
                        model=embed_model.model_id
                    )
                    
                    # 1. 批量向量化所有工具描述和名称
                    texts_to_embed = [f"{c['name']}: {c['desc']}" for c in candidates]
                    # 2. 向量化用户目标
                    texts_to_embed.append(user_goal)
                    
                    # 为了性能，实际生产中应将工具向量缓存到 Redis/内存中。
                    # 这里在 Planning 初始化阶段执行单次全量 Embedding。
                    embeddings = embedder.embed(texts_to_embed)
                    
                    query_vec = np.array(embeddings[-1])
                    doc_vecs = np.array(embeddings[:-1])
                    
                    # 计算余弦相似度
                    norm_docs = np.linalg.norm(doc_vecs, axis=1)
                    norm_query = np.linalg.norm(query_vec)
                    
                    sims = np.dot(doc_vecs, query_vec) / (norm_docs * norm_query + 1e-10)
                    
                    # 按相似度得分排序
                    scored_candidates = [(float(sims[i]), candidates[i]) for i in range(len(candidates))]
                    
                    # 对于通用工具给予加权，防止被截断
                    for i, (score, c) in enumerate(scored_candidates):
                        name_lower = c["name"].lower()
                        if "general" in name_lower or "search" in name_lower or "web" in name_lower:
                            scored_candidates[i] = (score + 0.15, c)
                            
                    scored_candidates.sort(key=lambda x: x[0], reverse=True)
                    selected = [item[1] for item in scored_candidates[:top_k]]
                else:
                    raise ValueError("No active embedding model available")
            except Exception as e:
                logger.warning(f"Vector-based Tool RAG failed, falling back to lexical TF-IDF heuristic: {e}")
                # 降级：轻量级 TF-IDF/词频 启发式评分
                goal_lower = user_goal.lower()
                import re
                goal_words = set(re.findall(r'[a-zA-Z0-9_]+|[\u4e00-\u9fa5]', goal_lower))
                
                scored_candidates = []
                for c in candidates:
                    score = 0.0
                    name_lower = c["name"].lower()
                    desc_lower = c["desc"].lower()
                    
                    if name_lower in goal_lower:
                        score += 10.0
                    
                    desc_words = set(re.findall(r'[a-zA-Z0-9_]+|[\u4e00-\u9fa5]', desc_lower))
                    overlap = len(goal_words & desc_words)
                    score += overlap * 2.0
                    
                    if "general" in name_lower or "search" in name_lower or "web" in name_lower:
                        score += 1.0
                        
                    scored_candidates.append((score, c))
                
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                selected = [item[1] for item in scored_candidates[:top_k]]
        
        catalog = [f"- {c['name']} ({c['type']}): {c['desc']}" for c in selected]
        return "\n".join(catalog) if catalog else "GeneralAgent: Use for generic reasoning/coding."

    def _validate_dag_topology(self, plan: TaskPlan) -> None:
        """
        [架构确定性] 第一性原理拓扑验证 (Kahn's Algorithm)
        杜绝大模型输出循环依赖（Deadlock）和幽灵依赖（Ghost Nodes）。
        """
        if not plan.steps:
            return

        step_ids = {step.id for step in plan.steps}
        in_degree = {step.id: 0 for step in plan.steps}
        adj_list = {step.id: [] for step in plan.steps}

        # 1. 幽灵依赖检测
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise GraphCycleError(f"Logic Error: Step {step.id} depends on non-existent ghost step '{dep}'.")
                # 构建邻接表: dep -> step
                adj_list[dep].append(step.id)
                in_degree[step.id] += 1

        # 2. 环路检测 (Kahn)
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(plan.steps):
            cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
            raise GraphCycleError(f"Circular Dependency (Deadlock) detected involving steps: {cycle_nodes}. DAG must be acyclic.")

    @staticmethod
    def _format_error_feedback(error: Exception, raw_output: str) -> str:
        """精准的纠错反馈逻辑：向 LLM 暴露确切的断点"""
        lines = ["\n[FAILED VALIDATION]"]
        
        if isinstance(error, PlanValidationError):
            lines.append("Schema Validation Errors:")
            if hasattr(error, 'validation_details') and error.validation_details:
                for detail in error.validation_details:
                    lines.append(f"- Field '{detail.get('path')}': {detail.get('issue')}")
            else:
                lines.append(f"- {str(error)}")
        elif isinstance(error, GraphCycleError):
            lines.append(f"DAG Topology Error: {str(error)}")
        else:
            lines.append(f"Parse/Logic Error: {str(error)}")

        # 只返回必要的摘要上下文，防止下一次请求 Token 撑爆
        snippet = raw_output[:500] + ("..." if len(raw_output) > 500 else "")
        lines.append(f"\nYour previous output snippet:\n{snippet}")
        lines.append("\nPlease fix the above logic/structure errors, and output a strict JSON matching the schema.")
        return "\n".join(lines)

    async def generate_plan(self, session_id: str, user_goal: str, context: str = "", history_msgs: List[Dict[str, Any]] = None) -> Optional[ExecutionPlan]:
        # 1. 无状态初始化：每个 Request 独享独立的 Agent 实例
        if not self.llm_model:
            self.llm_model = await resolve_chat_llm_model(self.db)
            
        model_instance = ModelFactory.create_model(self.llm_model)
        
        agent = Agent(
            name="Master-Architect",
            model=model_instance,
            instructions=[
                "你是一位资深架构师，负责基于第一性原理将复杂目标拆解为执行任务流 (TaskPlan)。",
                "【强制要求】：必须输出符合 JSON Schema 的纯 JSON 结构，拒绝任何 Markdown 代码块标签。",
                "【工具原则】：从 Catalog 中精确挑选工具 (tool_name)。",
                "【依赖原则】：任务依赖必须严格构成有向无环图 (DAG)，依赖的前置任务必须真实存在且不能成环。",
                f"### 可用工具库 (Catalog)：\n{await self._filter_capabilities(user_goal)}"
            ],
            # 采用 Agent 的强结构化输出能力
            output_schema=TaskPlan,
            retries=1 # 将重试逻辑提升至外层进行带上下文的深度重试
        )

        history_str = ""
        if history_msgs:
            history_str = "Conversation History:\n" + "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history_msgs])

        base_prompt = (
            f"User Goal: {user_goal}\n"
            f"Context (Files/Docs): {context}\n"
            f"{history_str}\n"
            "Analyze the User Goal deeply considering the Conversation History and Context. If it is a complex task (like writing a comprehensive report, comparing products, or requiring data gathering), you MUST break it down into multiple logical steps (e.g., Step 1: Research, Step 2: Analyze, Step 3: Generate Document). ONLY use EXACTLY ONE step if the goal is truly trivial (like a simple greeting or a direct 1-step calculation). Use the same language as the User Goal."
        )

        MAX_ATTEMPTS = 3
        last_error = None
        last_raw = ""

        for attempt in range(1, MAX_ATTEMPTS + 1):
            prompt = base_prompt if attempt == 1 else f"{base_prompt}\n{self._format_error_feedback(last_error, last_raw)}"
            
            try:
                # 2. 调度执行
                response = await agent.arun(prompt)
                raw_data = response.content if hasattr(response, "content") else response

                if isinstance(raw_data, TaskPlan):
                    plan_data = raw_data
                    last_raw = str(raw_data.model_dump_json() if hasattr(raw_data, 'model_dump_json') else raw_data)
                else:
                    last_raw = str(raw_data)
                    # 3. 工业级解析与自愈 (使用 schemas/plan.py 中的核心解析器)
                    plan_data = parse_task_plan(last_raw)
                
                # 4. 架构确定性校验 (DAG 算法)
                self._validate_dag_topology(plan_data)
                
                # 5. 映射至执行引擎态
                manifest = ExecutionPlan(
                    plan_id=f"p-{uuid.uuid4().hex[:6]}",
                    session_id=session_id,
                    user_goal=user_goal,
                    reasoning=plan_data.estimated_reasoning,
                    tasks=[
                        ExecutionTaskStep(
                            task_id=str(s.id),
                            title=s.task[:60],
                            description=s.task,
                            dependencies=[str(d) for d in s.dependencies],
                            executor_role=s.tool_name
                        ) for s in plan_data.steps
                    ]
                )
                
                logger.info(f"Plan generated successfully for session {session_id} on attempt {attempt}")
                return manifest

            except (PlanValidationError, GraphCycleError) as e:
                # 业务级错误：触发自纠错回路
                last_error = e
                logger.warning(f"Planning semantic validation failed (attempt {attempt}): {str(e)}")
            except Exception as e:
                # 系统级异常（如网络中断）：记录并传递
                last_error = e
                logger.error(f"Planning unexpected error (attempt {attempt}): {str(e)}")
                
            if attempt == MAX_ATTEMPTS:
                logger.error(f"Failed to generate valid DAG plan after {MAX_ATTEMPTS} attempts. Last error: {str(last_error)}")
                return None

        return None
