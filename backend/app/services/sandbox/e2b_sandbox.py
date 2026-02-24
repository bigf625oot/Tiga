import logging
import base64
import time
from typing import Dict, Any, Optional, List, Union, Callable
from e2b_code_interpreter import Sandbox
from app.core.config import settings

logger = logging.getLogger(__name__)

class E2BSandboxService:
    def __init__(self):
        self.api_key = settings.E2B_API_KEY
        # Map internal session_id to E2B sandbox_id
        # In a production multi-instance env, this should be in Redis
        self._active_sandboxes: Dict[str, str] = {}

    def _get_sandbox(self, session_id: Optional[str] = None) -> Sandbox:
        """
        Get an existing sandbox or create a new one.
        Returns the Sandbox instance.
        Caller is responsible for closing if needed, but for persistent sessions we keep it alive.
        """
        if not self.api_key:
            raise Exception("E2B_API_KEY is not set in configuration.")

        sandbox = None
        
        # Try to reconnect if session_id provided and known
        if session_id and session_id in self._active_sandboxes:
            e2b_id = self._active_sandboxes[session_id]
            try:
                logger.info(f"Reconnecting to E2B sandbox {e2b_id} for session {session_id}")
                sandbox = Sandbox.connect(e2b_id, api_key=self.api_key)
                return sandbox
            except Exception as e:
                logger.warning(f"Failed to reconnect to sandbox {e2b_id}: {e}. Creating new one.")
                # Fall through to create new
        
        # Create new sandbox
        logger.info("Creating new E2B Sandbox...")
        sandbox_kwargs = {"api_key": self.api_key}
        if settings.E2B_TEMPLATE_ID:
            sandbox_kwargs["template"] = settings.E2B_TEMPLATE_ID
            
        sandbox = Sandbox(**sandbox_kwargs)
        
        # Register if session_id provided
        if session_id:
            self._active_sandboxes[session_id] = sandbox.id
            logger.info(f"Registered session {session_id} -> sandbox {sandbox.id}")
            
        return sandbox

    async def execute(self, 
                      code: str, 
                      session_id: Optional[str] = None,
                      on_stdout: Optional[Callable[[str], None]] = None,
                      on_stderr: Optional[Callable[[str], None]] = None
                      ) -> Dict[str, Any]:
        """
        Execute python code in E2B cloud sandbox.
        """
        if not self.api_key:
             return {
                "status": "error",
                "content": "E2B_API_KEY is not set in configuration.",
                "type": "config_error"
            }

        logger.info(f"Executing code in E2B Sandbox (Session {session_id}): {code[:50]}...")
        
        sandbox = None
        try:
            sandbox = self._get_sandbox(session_id)
            
            # Wrap callbacks to handle E2B ProcessMessage
            def handle_stdout(process_message):
                if on_stdout:
                    on_stdout(process_message.line)
            
            def handle_stderr(process_message):
                if on_stderr:
                    on_stderr(process_message.line)

            # Execute code with streaming callbacks
            # Note: run_code in e2b-code-interpreter >= 0.0.10 supports on_stdout/on_stderr
            # But they usually take a ProcessMessage object (line, timestamp, etc) or just the output depending on SDK version.
            # We assume it passes an object with .line or .out based on common E2B patterns.
            # Let's try simple lambda first, assuming it passes the output object.
            
            execution = sandbox.run_code(
                code,
                on_stdout=handle_stdout if on_stdout else None,
                on_stderr=handle_stderr if on_stderr else None
            )
            
            text_content = []
            files = []
            status = "success"

            # Handle Stdout (still available in execution object even if streamed)
            if execution.logs.stdout:
                text_content.append("".join(execution.logs.stdout))
            
            # Handle Stderr
            if execution.logs.stderr:
                err_text = "".join(execution.logs.stderr)
                text_content.append(f"\nSTDERR:\n{err_text}")
            
            # Handle Results
            if execution.results:
                for result in execution.results:
                    if hasattr(result, "text") and result.text:
                        text_content.append(f"\nRESULT:\n{result.text}")
                    
                    # Handle Charts/Images
                    if hasattr(result, "png") and result.png:
                        files.append({
                            "name": f"chart_{int(time.time())}_{len(files)}.png",
                            "content": result.png,
                            "type": "image/png"
                        })
                    elif hasattr(result, "jpeg") and result.jpeg:
                            files.append({
                            "name": f"image_{int(time.time())}_{len(files)}.jpg",
                            "content": result.jpeg,
                            "type": "image/jpeg"
                        })
                    # Handle other formats if needed (pdf, svg, etc.)

            # Handle Errors
            if execution.error:
                error_msg = f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"
                text_content.append(f"\nEXECUTION ERROR:\n{error_msg}")
                status = "error"

            full_content = "".join(text_content)
            
            return {
                "status": status,
                "type": "text" if not files else "multimodal",
                "content": full_content,
                "files": files,
                "session_id": session_id or "ephemeral" # Echo back session_id
            }

        except Exception as e:
            logger.error(f"E2B execution error: {e}")
            return {
                "status": "error",
                "content": str(e),
                "type": "execution_error"
            }
        finally:
            # If ephemeral (no session_id), close immediately
            if not session_id and sandbox:
                try:
                    sandbox.close()
                except:
                    pass

    async def upload_file(self, session_id: str, path: str, content: Union[str, bytes]):
        """Upload file to the sandbox"""
        sandbox = self._get_sandbox(session_id)
        # e2b write_file accepts str or bytes
        sandbox.files.write(path, content)
        # We don't close here as we assume session usage

    async def download_file(self, session_id: str, path: str) -> bytes:
        """Download file from the sandbox"""
        sandbox = self._get_sandbox(session_id)
        return sandbox.files.read(path, format="bytes")

    async def install_packages(self, session_id: str, packages: List[str]):
        """Install Python packages"""
        sandbox = self._get_sandbox(session_id)
        cmd = f"pip install {' '.join(packages)}"
        logger.info(f"Installing packages in session {session_id}: {cmd}")
        result = sandbox.commands.run(cmd)
        if result.exit_code != 0:
            raise Exception(f"Failed to install packages: {result.stderr}")
        return result.stdout
