import logging
import os
import re
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func

from app.services.eah_agent.workflows.base import EAHWorkflow, EAHWorkflowState
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager
from app.services.eah_agent.core.agent_planner import PlannerAgent
from app.models.agent_plan import AgentPlan, AgentTask, TaskStatus
from app.core.context_compressor import ContextCompressor
from app.core.shared_state import StateManager, SharedState
from app.core.i18n import _

# Agno imports
from agno.agent import Agent
from agno.models.openai import OpenAIChat
try:
    from agno.tools.e2b import E2BTools
except ImportError:
    E2BTools = None

logger = logging.getLogger(__name__)

# Sandbox uploads directory (files saved by sandbox_tools.py)
_UPLOADS_DIR = Path(__file__).resolve().parents[5] / "data" / "storage"

# Regex to extract ARTIFACTS JSON block from agent response
_ARTIFACTS_RE = re.compile(r"ARTIFACTS\s*:\s*(\[[\s\S]*?\])", re.IGNORECASE)


def _snapshot_uploads_dir() -> Dict[str, int]:
    """返回当前 uploads 目录的文件快照 {相对文件名: 文件大小(bytes)}"""
    if not _UPLOADS_DIR.exists():
        return {}
    return {
        f.name: f.stat().st_size
        for f in _UPLOADS_DIR.iterdir()
        if f.is_file()
    }


def _diff_uploads(before: Dict[str, int], after: Dict[str, int]) -> List[Dict[str, Any]]:
    """对比快照，返回新增文件列表（含 url、name、type、size）"""
    new_files = []
    for name, size in after.items():
        if name not in before:
            new_files.append({
                "name": name,
                "url": f"/uploads/{name}",
                "type": _infer_type_from_url(name),
                "size": size,
            })
    return new_files


def _extract_artifacts_from_text(text: str) -> List[Dict[str, Any]]:
    """Parse ARTIFACTS: [...] block from agent response text."""
    match = _ARTIFACTS_RE.search(text)
    if not match:
        return []
    try:
        items = json.loads(match.group(1))
        result = []
        for item in items:
            if isinstance(item, dict) and item.get("url"):
                url = item["url"]
                name = item.get("name", os.path.basename(url))
                # Try to get file size from disk if available
                disk_path = _UPLOADS_DIR / name
                size = disk_path.stat().st_size if disk_path.exists() else item.get("size", 0)
                result.append({
                    "name": name,
                    "url": url,
                    "type": item.get("type", _infer_type_from_url(url)),
                    "size": size,
                })
        return result
    except Exception:
        return []


def _extract_artifacts_from_tool_result(result_str: str) -> List[Dict[str, Any]]:
    """Extract /uploads/ file URLs mentioned in tool results."""
    artifacts = []
    for url in re.findall(r"/uploads/[\w\-./]+", result_str):
        name = os.path.basename(url)
        disk_path = _UPLOADS_DIR / name
        size = disk_path.stat().st_size if disk_path.exists() else 0
        artifacts.append({
            "name": name,
            "url": url,
            "type": _infer_type_from_url(url),
            "size": size,
        })
    return artifacts

def _infer_type_from_url(url: str) -> str:
    ext = os.path.splitext(url)[-1].lower()
    mapping = {
        ".py": "python", ".ipynb": "notebook",
        ".md": "markdown", ".txt": "text",
        ".csv": "csv", ".json": "json",
        ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image",
        ".pdf": "pdf", ".html": "html", ".xlsx": "excel", ".zip": "archive"
    }
    return mapping.get(ext, "file")


class UnifiedWorkflowState(EAHWorkflowState):
    plan_id: Optional[str] = None
    images: List[str] = []

class UnifiedAgentWorkflow(EAHWorkflow):
    """
    Unified Agent Workflow that integrates Planning, Execution, RAG, Multimodal, and Sandbox capabilities.
    Inherits from EAHWorkflow (Agno Workflow).
    """
    def __init__(self, session_id: str, db: AsyncSession, user_goal: str, images: Optional[List[str]] = None, **kwargs):
        super().__init__(session_id=session_id, **kwargs)
        self.db = db
        self.user_goal = user_goal
        self.input_images = images or []

        # Initialize Helpers
        self.kb_manager = SessionKnowledgeManager(session_id)
        self.compressor = ContextCompressor()
        self.state_manager = StateManager.get_instance()

        # Initialize State
        if not hasattr(self, "state") or self.state is None:
             self.state = UnifiedWorkflowState(session_id=session_id, images=self.input_images, context={"history": []})
        elif isinstance(self.state, EAHWorkflowState) and not isinstance(self.state, UnifiedWorkflowState):
             # Upgrade state if needed
             self.state = UnifiedWorkflowState(**self.state.dict(), images=self.input_images)
             if "history" not in self.state.context:
                 self.state.context["history"] = []

    async def _process_files(self, images: List[str]) -> List[Dict[str, Any]]:
        """
        Process images for the workflow.
        Returns a list of image content blocks for the LLM.
        """
        processed_images = []
        if not images:
            return processed_images

        logger.info(f"Processing {len(images)} images for workflow {self.session_id}")
        for img_path in images:
            # Assuming local paths are valid for the Agent or handled by Agno
            processed_images.append({"type": "image_url", "image_url": {"url": img_path}})

        return processed_images

    async def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError("Use run_stream() for this workflow.")

    async def run_stream(self, *args, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the unified workflow with streaming feedback.
        Emits structured per-task events for the frontend task workspace.
        """
        all_artifacts: List[Dict[str, Any]] = []

        try:
            # 1. Initialize RAG
            yield {"type": "status", "content": _("Initializing Knowledge Base...")}
            kb = self.kb_manager.get_knowledge_base()

            # 2. Process Multimodal Inputs
            processed_images = await self._process_files(self.input_images)

            # 3. State Management: Set Mode
            await self.state_manager.update_mode(self.session_id, "workflow")

            # 4. Planning Phase
            fallback_model_id = kwargs.get("planner_model_id")
            planner = PlannerAgent(self.db, model_id=fallback_model_id)

            yield {"type": "status", "content": _("Planning tasks...")}

            plan_id = await planner.create_plan(self.session_id, self.user_goal)
            self.state.plan_id = plan_id
            self.state.current_step = "planning"

            # 5. Fetch plan + tasks, emit plan event
            plan = await self._get_plan(plan_id)
            if not plan:
                yield {"type": "error", "content": _("Failed to create execution plan.")}
                return

            stmt = select(AgentTask).filter(AgentTask.plan_id == plan_id).order_by(AgentTask.sequence.asc())
            result = await self.db.execute(stmt)
            tasks = result.scalars().all()

            plan_dict = {
                "id": str(plan.id),
                "reasoning": getattr(plan, "reasoning", ""),
                "status": plan.status.value if hasattr(plan.status, 'value') else str(plan.status),
                "tasks": [
                    {
                        "id": str(t.id),
                        "name": t.name,
                        "description": t.description,
                        "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                        "assigned_agent_role": t.assigned_agent_role
                    } for t in tasks
                ]
            }

            yield {"type": "plan", "content": plan_id, "plan": plan_dict}

            # 6. Execution Loop
            while True:
                task = await self._get_next_task(plan_id)
                if not task:
                    break

                task_id_str = str(task.id)
                self.state.current_step = task.name

                # Emit task_started event
                yield {
                    "type": "task_started",
                    "task_id": task_id_str,
                    "task_name": task.name,
                    "task_description": task.description or ""
                }

                # Context Compression
                history = self.state.context.get("history", [])
                if history:
                    compressed_history = await self.compressor.compress_context(history)
                    self.state.context["history"] = compressed_history

                # Execute Task
                try:
                    executor = await self._create_executor_agent(task, kb)

                    # Update task status
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = func.now()
                    await self.db.commit()

                    response_content = ""

                    # Snapshot uploads dir BEFORE execution to detect new files
                    pre_snapshot = _snapshot_uploads_dir()

                    task_prompt = (
                        f"Original User Goal: {self.user_goal}\n\n"
                        f"Your Current Task: {task.name}\n"
                        f"Task Details: {task.description}\n\n"
                        f"Please execute this task and respond in the same language as the Original User Goal."
                    )

                    stream_gen = executor.arun(
                        task_prompt,
                        images=processed_images if self.input_images else None,
                        stream=True
                    )

                    async for chunk in stream_gen:
                        chunk_text = None
                        if hasattr(chunk, "content") and chunk.content is not None:
                            chunk_text = str(chunk.content)
                            response_content += chunk_text
                        elif isinstance(chunk, str):
                            chunk_text = chunk
                            response_content += chunk_text

                        if chunk_text:
                            yield {"type": "task_content", "task_id": task_id_str, "content": chunk_text}

                        # Handle tool call events
                        if hasattr(chunk, "event"):
                            event_name = chunk.event
                            if event_name in ("ToolCallStarted", "ToolCallCompleted") and hasattr(chunk, "tool") and chunk.tool:
                                tool = chunk.tool
                                tool_info = {
                                    "tool_name": tool.tool_name,
                                    "tool_args": tool.tool_args,
                                    "status": "started" if event_name == "ToolCallStarted" else "completed"
                                }
                                if event_name == "ToolCallCompleted" and hasattr(tool, "result"):
                                    result_str = str(tool.result)
                                    tool_info["result"] = result_str
                                    # Extract file artifacts from tool results
                                    file_artifacts = _extract_artifacts_from_tool_result(result_str)
                                    for a in file_artifacts:
                                        if not any(x["url"] == a["url"] for x in all_artifacts):
                                            all_artifacts.append(a)

                                yield {
                                    "type": "task_tool_call",
                                    "task_id": task_id_str,
                                    "tool": tool_info
                                }

                    # Extract ARTIFACTS block from response
                    text_artifacts = _extract_artifacts_from_text(response_content)
                    for a in text_artifacts:
                        if not any(x["url"] == a["url"] for x in all_artifacts):
                            all_artifacts.append(a)

                    # Directory diff: detect new files created in uploads dir during this task
                    post_snapshot = _snapshot_uploads_dir()
                    dir_artifacts = _diff_uploads(pre_snapshot, post_snapshot)
                    for a in dir_artifacts:
                        if not any(x["url"] == a["url"] for x in all_artifacts):
                            all_artifacts.append(a)
                            logger.info(f"[Artifacts] New file detected: {a['name']} ({a['size']} bytes)")

                    # Mark Task Complete
                    task.status = TaskStatus.COMPLETED
                    task.result = response_content
                    task.completed_at = func.now()
                    await self.db.commit()

                    yield {
                        "type": "task_completed",
                        "task_id": task_id_str,
                        "result_summary": response_content # 移除 [:600] 截断，保留完整输出供前端展示
                    }

                    # Update History
                    if "history" not in self.state.context:
                        self.state.context["history"] = []
                    self.state.context["history"].append({"role": "user", "content": f"Task: {task.name}\n{task.description}"})
                    self.state.context["history"].append({"role": "assistant", "content": task.result})

                    self.state.steps_completed.append(task.name)
                    await self.state_manager.save_state(
                        self.session_id,
                        SharedState(
                            session_id=self.session_id,
                            mode="workflow",
                            ui_state={"current_task": task.id, "progress": len(self.state.steps_completed)}
                        )
                    )

                except Exception as e:
                    logger.error(f"Task {task.name} failed: {e}")
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    await self.db.commit()

                    yield {
                        "type": "task_failed",
                        "task_id": task_id_str,
                        "error": str(e)
                    }

                    if self._is_critical_task(task):
                        yield {"type": "error", "content": f"Critical task failed: {e}"}
                        self.state.error = str(e)
                        break
                    # non-critical: continue to next task

            # Finalize
            if not self.state.error:
                yield {"type": "status", "content": _("Workflow execution completed.")}

            # Emit artifact list
            if all_artifacts:
                yield {"type": "artifacts", "files": all_artifacts}

        except Exception as e:
            from app.services.eah_agent.core.schema import PlanValidationError
            if isinstance(e, PlanValidationError):
                raise e
            logger.exception(f"Workflow execution failed: {e}")
            yield {"type": "error", "content": f"Workflow execution failed: {e}"}
        finally:
            self.kb_manager.cleanup()

    async def _get_plan(self, plan_id: str) -> Optional[AgentPlan]:
        result = await self.db.execute(select(AgentPlan).filter(AgentPlan.id == plan_id))
        return result.scalars().first()

    async def _get_next_task(self, plan_id: str) -> Optional[AgentTask]:
        stmt = select(AgentTask).filter(
            AgentTask.plan_id == plan_id,
            AgentTask.status == TaskStatus.PENDING
        ).order_by(AgentTask.sequence.asc())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _create_executor_agent(self, task: AgentTask, kb: Any) -> Agent:
        """
        Creates an Agno Agent configured for the specific task.
        Enforces Sandbox (E2B) if code execution is likely needed.
        """
        from app.services.llm.resolver import resolve_chat_llm_model
        from app.services.llm.factory import ModelFactory

        tools = []
        is_code_task = any(kw in task.description.lower() for kw in ["code", "script", "python", "calculate", "plot", "analyze"])

        if is_code_task or "coder" in (task.assigned_agent_role or "").lower():
            if E2BTools:
                api_key = os.getenv("E2B_API_KEY")
                if api_key:
                    tools.append(E2BTools(api_key=api_key))
                else:
                    logger.warning("E2B_API_KEY not found. Skipping E2BTools.")

        llm_model = await resolve_chat_llm_model(self.db)
        model_instance = ModelFactory.create_model(llm_model)

        return Agent(
            model=model_instance,
            tools=tools,
            knowledge=kb,
            description=f"You are an expert executor for the task: {task.name}",
            instructions=[
                task.description,
                "IMPORTANT: You must always reply in the same language as the user's original request. If the task or context is in Chinese, you MUST reply in Chinese.",
                "If you generate any files during execution, at the very end of your response output exactly this format: ARTIFACTS: [{\"name\":\"filename.ext\",\"url\":\"/uploads/filename.ext\",\"type\":\"python\"}]"
            ],
            markdown=True
        )

    def _is_critical_task(self, task: AgentTask) -> bool:
        return True
