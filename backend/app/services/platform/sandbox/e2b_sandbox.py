import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Union, Callable, Protocol
from pydantic import BaseModel, Field

# 核心依赖：确保安装 e2b-code-interpreter >= 0.0.34
from e2b_code_interpreter import AsyncSandbox
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- 模型定义 ---

class SandboxResult(BaseModel):
    status: str = "success"  # success | error | timeout
    content: str = ""
    files: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: str
    execution_time: float = 0.0

# --- 存储抽象 ---

class SessionStore(Protocol):
    """定义 Session 存储协议，便于切换 Redis 或本地内存"""
    async def get(self, session_id: str) -> Optional[str]: ...
    async def set(self, session_id: str, sandbox_id: str): ...
    async def delete(self, session_id: str): ...

class LocalSessionStore:
    def __init__(self):
        self._data: Dict[str, str] = {}
    async def get(self, session_id: str) -> Optional[str]: return self._data.get(session_id)
    async def set(self, session_id: str, sandbox_id: str): self._data[session_id] = sandbox_id
    async def delete(self, session_id: str): self._data.pop(session_id, None)

# --- 主服务 ---

class E2BSandboxService:
    def __init__(self, storage: Optional[SessionStore] = None):
        self.api_key = settings.E2B_API_KEY
        # 生产环境建议通过依赖注入传入 RedisSessionStore
        self.storage = storage or LocalSessionStore()
        self.default_timeout = 300 # 5分钟默认超时

    async def _get_sandbox(self, session_id: Optional[str] = None) -> AsyncSandbox:
        """获取或创建异步沙箱，包含重连自愈逻辑"""
        if not self.api_key:
            raise RuntimeError("E2B_API_KEY is missing")

        sandbox = None
        
        # 1. 尝试从存储中恢复 Session
        if session_id:
            e2b_id = await self.storage.get(session_id)
            if e2b_id:
                try:
                    logger.debug(f"Attempting to reconnect: {e2b_id}")
                    # AsyncSandbox.connect 是轻量级的
                    sandbox = await AsyncSandbox.connect(e2b_id, api_key=self.api_key)
                    return sandbox
                except Exception as e:
                    logger.warning(f"Session {session_id} expired or invalid ({e}). Cleaning up.")
                    await self.storage.delete(session_id)

        # 2. 创建新沙箱
        logger.info(f"Creating new AsyncSandbox for session: {session_id or 'ephemeral'}")
        create_kwargs = {
            "api_key": self.api_key,
            "timeout": self.default_timeout,
            "metadata": {"created_at": str(time.time()), "session_id": session_id or "anon"}
        }
        if settings.E2B_TEMPLATE_ID:
            create_kwargs["template"] = settings.E2B_TEMPLATE_ID

        sandbox = await AsyncSandbox.create(**create_kwargs)

        # 3. 如果有 session_id，持久化映射关系
        if session_id:
            await self.storage.set(session_id, sandbox.id)
            
        return sandbox

    async def execute(self, 
                      code: str, 
                      session_id: Optional[str] = None,
                      on_stdout: Optional[Callable[[str], None]] = None,
                      on_stderr: Optional[Callable[[str], None]] = None
                      ) -> SandboxResult:
        """
        执行代码的核心入口。
        采用 AsyncSandbox 确保非阻塞，支持全格式结果解析。
        """
        start_time = time.perf_counter()
        sandbox = await self._get_sandbox(session_id)
        
        try:
            # 执行代码
            execution = await sandbox.run_code(
                code,
                on_stdout=lambda msg: on_stdout(msg.line) if on_stdout else None,
                on_stderr=lambda msg: on_stderr(msg.line) if on_stderr else None
            )

            text_outputs = []
            files = []
            
            # 1. 处理标准输出和错误
            if execution.logs.stdout:
                text_outputs.append("".join(execution.logs.stdout))
            if execution.logs.stderr:
                text_outputs.append(f"\nSTDERR:\n{''.join(execution.logs.stderr)}")

            # 2. 处理多模态结果 (Rich Outputs)
            for res in execution.results:
                # 文本/Json 结果
                if res.text:
                    text_outputs.append(f"\n[Result]: {res.text}")
                
                # 转换二进制文件格式
                formats = {
                    'png': 'image/png',
                    'jpeg': 'image/jpeg',
                    'svg': 'image/svg+xml',
                    'pdf': 'application/pdf',
                    'html': 'text/html',
                    'latex': 'text/latex',
                    'json': 'application/json'
                }
                
                for attr, mime in formats.items():
                    val = getattr(res, attr, None)
                    if val:
                        files.append({
                            "name": f"output_{int(time.time())}_{len(files)}.{attr}",
                            "content": val,
                            "type": mime
                        })

            # 3. 处理运行期错误
            status = "success"
            if execution.error:
                status = "error"
                error_trace = f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"
                text_outputs.append(f"\n[Runtime Error]:\n{error_trace}")

            return SandboxResult(
                status=status,
                content="".join(text_outputs),
                files=files,
                session_id=session_id or "ephemeral",
                execution_time=round(time.perf_counter() - start_time, 3)
            )

        except Exception as e:
            logger.exception(f"Critical sandbox execution error: {e}")
            return SandboxResult(status="error", content=str(e), session_id=session_id or "error")
        
        finally:
            # 只有 ephemeral (无 session_id) 的沙箱才立即关闭
            if not session_id:
                await sandbox.close()

    async def upload_file(self, session_id: Optional[str], remote_path: str, content: Union[str, bytes]):
        """异步上传文件"""
        sandbox = await self._get_sandbox(session_id)
        try:
            # E2B 的 files.write 也是支持异步调用的
            await sandbox.files.write(remote_path, content)
        finally:
            if not session_id:
                await sandbox.close()

    async def download_file(self, session_id: Optional[str], remote_path: str) -> bytes:
        """异步下载文件"""
        sandbox = await self._get_sandbox(session_id)
        try:
            return await sandbox.files.read(remote_path, format="bytes")
        finally:
            if not session_id:
                await sandbox.close()

    async def close_session(self, session_id: str):
        """主动销毁 Session，释放云端资源"""
        e2b_id = await self.storage.get(session_id)
        if e2b_id:
            try:
                sandbox = await AsyncSandbox.connect(e2b_id, api_key=self.api_key)
                await sandbox.close()
                logger.info(f"Sandbox {e2b_id} closed successfully.")
            except Exception:
                pass
            finally:
                await self.storage.delete(session_id)

    async def run_shell(self, session_id: Optional[str], command: str) -> Dict[str, Any]:
        """异步执行 Shell 命令"""
        sandbox = await self._get_sandbox(session_id)
        try:
            # 使用 commands.run 执行系统级任务，强制注入超时时间防止线程挂死
            result = await sandbox.commands.run(command, timeout=self.default_timeout)
            
            # 兼容 sandbox_tools.py 的契约
            output_text = []
            if result.stdout:
                output_text.append(result.stdout)
            if result.stderr:
                output_text.append(f"STDERR:\n{result.stderr}")
                
            content = "\n".join(output_text)
            if not content:
                content = "Command executed successfully (no output)."

            return {
                "status": "success" if result.exit_code == 0 else "error",
                "content": content,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        finally:
            if not session_id:
                await sandbox.close()

# 全局沙箱服务实例
sandbox_service = E2BSandboxService()