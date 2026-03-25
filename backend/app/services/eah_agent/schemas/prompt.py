import logging
from enum import IntEnum
from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass, field
from app.core.i18n import _

logger = logging.getLogger(__name__)

# --- 1. 领域模型定义 ---

class InstructionCategory(IntEnum):
    """
    定义指令的优先级分类。
    数值越小，在最终生成的 System Prompt 中位置越靠前。
    LLM 对开头（身份）和结尾（行动策略/约束）最敏感。
    """
    IDENTITY = 0      # 角色身份定义
    CAPABILITY = 10   # 基础平台能力 (OpenClaw, Sandbox)
    KNOWLEDGE = 20    # 知识库检索协议
    SKILL = 30        # 具体业务技能/工具提示词
    STRATEGY = 40     # 推理策略 (CoT, ReAct)
    CONSTRAINT = 50   # 强制性约束/负向提示词

@dataclass(frozen=True)
class InstructionSegment:
    """原子指令段：确保指令的唯一性与有序性"""
    key: str          # 唯一标识，用于幂等去重
    content: str      # 指令内容
    category: InstructionCategory = InstructionCategory.CAPABILITY
    priority: int = 100 # 同类别内的微调排序

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, InstructionSegment):
            return False
        return self.key == other.key

# --- 2. 指令内容库 (与逻辑分离) ---

class InstructionLibrary:
    """集中管理静态提示词模板，支持 i18n"""

    @staticmethod
    def get_default_identity() -> str:
        return _("""You are a highly capable and intelligent AI assistant.
Your primary goal is to help the user efficiently and accurately.

Key principles:
1. **Accuracy**: Provide factual information.
2. **Clarity**: Be concise and use markdown.
3. **Proactiveness**: Anticipate needs and execute logically.
4. **Tool Usage**: Utilize available tools instead of guessing.""")

    @staticmethod
    def get_openclaw_prompt() -> str:
        return _("""## OpenClaw Capabilities
You have FULL access to OpenClaw tools for automation. Use them directly:
1. `oc_web_search`/`oc_web_fetch`: Web interaction.
2. `oc_browser`: Browser UI control and screenshots.
3. `oc_cron`: Schedule and manage crawl tasks.
4. `oc_nodes`: Node management.
When asked to "crawl" or "automate", you MUST use these tools.""")

    @staticmethod
    def get_sandbox_prompt() -> str:
        return _("""## Sandbox Capabilities
You have access to a secure E2B sandbox (Python/Shell).
1. Use `run_code` for calculations or data processing.
2. Use `run_shell` to install packages or run system commands.
3. Manage files via `read_file`/`write_file`.
Always verify the environment with `list_files` if needed.""")

    @staticmethod
    def get_knowledge_prompt() -> str:
        return _("""## Knowledge Base
Access advanced Knowledge Graph retrieval via:
1. `search_knowledge_base`: Vector-based semantic search.
2. `query_knowledge_graph`: Multi-hop reasoning. 
   - `mode='local'`: Specific entities.
   - `mode='global'`: High-level summaries.""")

    @staticmethod
    def get_cot_prompt() -> str:
        return _("""## Reasoning Strategy
Let's think step by step. Break down complex problems into smaller parts. 
Analyze, plan, then execute.""")

    @staticmethod
    def get_react_prompt() -> str:
        return _("""## Task Execution (ReAct)
1. **Analyze**: Decompose requests.
2. **Act**: Execute via tools.
3. **Observe**: Evaluate tool outputs.
4. **Adapt**: Adjust plan based on observations.
Proceed autonomously unless critical confirmation is needed.""")

# --- 3. 核心编排引擎 ---

class InstructionComposer:
    """
    P10 级指令编排器。
    职责：收集不同维度的指令，按分类排序去重，生成最终 System Prompt。
    """

    def __init__(self, base_instructions: Optional[str] = None):
        self._segments: Set[InstructionSegment] = set()
        self._setup_identity(base_instructions)

    def _setup_identity(self, base: Optional[str]):
        """初始化基础身份"""
        placeholders = {"", "You are a helpful assistant.", "你是一个有用的助手。"}
        content = base if base and base.strip() not in placeholders \
                  else InstructionLibrary.get_default_identity()
        
        self.add_segment(InstructionSegment(
            key="core_identity",
            content=content,
            category=InstructionCategory.IDENTITY
        ))

    def add_segment(self, segment: InstructionSegment) -> "InstructionComposer":
        """原子化添加指令段（幂等）"""
        if segment.content and segment.content.strip():
            # 这里的 set.add 会根据 __hash__ 和 __eq__ (即 key) 自动去重
            self._segments.add(segment)
        return self

    # --- 链式能力注入接口 ---

    def with_openclaw(self) -> "InstructionComposer":
        return self.add_segment(InstructionSegment(
            key="cap_openclaw",
            content=InstructionLibrary.get_openclaw_prompt(),
            category=InstructionCategory.CAPABILITY
        ))

    def with_sandbox(self) -> "InstructionComposer":
        return self.add_segment(InstructionSegment(
            key="cap_sandbox",
            content=InstructionLibrary.get_sandbox_prompt(),
            category=InstructionCategory.CAPABILITY
        ))

    def with_knowledge(self) -> "InstructionComposer":
        return self.add_segment(InstructionSegment(
            key="cap_knowledge",
            content=InstructionLibrary.get_knowledge_prompt(),
            category=InstructionCategory.KNOWLEDGE
        ))

    def with_market_skills(self, tools_config: List[Dict[str, Any]]) -> "InstructionComposer":
        if not tools_config:
            return self
            
        for tool in tools_config:
            if isinstance(tool, dict) and tool.get('type') == 'skill' and tool.get('content'):
                name = tool.get('name', 'unnamed_skill')
                self.add_segment(InstructionSegment(
                    key=f"skill_market_{name}",
                    content=f"### Skill: {name}\n{tool.get('content')}",
                    category=InstructionCategory.SKILL
                ))
        return self

    def with_file_skill(self, snippet: Optional[str]) -> "InstructionComposer":
        """注入文件/工具自带的提示词片段"""
        if snippet:
            self.add_segment(InstructionSegment(
                key=f"skill_file_{hash(snippet)}",
                content=snippet,
                category=InstructionCategory.SKILL
            ))
        return self

    def with_strategies(self, cot: bool = False, react: bool = False) -> "InstructionComposer":
        """注入推理与执行策略"""
        if cot:
            self.add_segment(InstructionSegment(
                key="strat_cot",
                content=InstructionLibrary.get_cot_prompt(),
                category=InstructionCategory.STRATEGY
            ))
        if react:
            self.add_segment(InstructionSegment(
                key="strat_react",
                content=InstructionLibrary.get_react_prompt(),
                category=InstructionCategory.STRATEGY
            ))
        return self

    # --- 最终构建 ---

    def build(self) -> str:
        """
        按照 Category (优先级) 和 Priority (同级排序) 构建最终字符串。
        """
        if not self._segments:
            return ""

        # 1. 转换并排序
        ordered_segments = sorted(
            list(self._segments),
            key=lambda x: (x.category.value, x.priority)
        )

        # 2. 聚合内容
        # P10 细节：在不同分类之间使用清晰的 Markdown 分隔符
        final_parts = []
        last_category = None

        for seg in ordered_segments:
            # 如果类别切换，可以根据需要增加额外的逻辑（如添加分割线，目前直接换行）
            final_parts.append(seg.content.strip())
            last_category = seg.category

        return "\n\n".join(final_parts)

# --- 使用示例 ---
# prompt = (
#     InstructionComposer(agent_model.system_prompt)
#     .with_openclaw()
#     .with_sandbox()
#     .with_knowledge()
#     .with_market_skills(agent_model.tools_config)
#     .with_strategies(cot=True, react=True)
#     .build()
# )