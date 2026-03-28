import logging
import base64
from uuid import uuid4
from typing import Optional, Union
from agno.tools import Toolkit
from agno.tools.function import ToolResult
from agno.media import Image
from app.services.platform.sandbox.e2b_sandbox import sandbox_service

logger = logging.getLogger(__name__)

class SandboxTools(Toolkit):
    _name = "sandbox"
    _label = "代码沙箱 (E2B)"
    _description = "安全执行 Python 代码和 Shell 命令"
    """
    与 E2B 沙箱环境交互的工具，支持代码执行、Shell 命令和文件管理。
    """

    def __init__(self, session_id: Optional[str] = None):
        super().__init__(name="sandbox_tools")
        self.session_id = session_id
        self.register(self.run_code)
        self.register(self.run_shell)
        self.register(self.read_file)
        self.register(self.write_file)
        self.register(self.list_files)

    async def run_code(self, code: str, language: str = "python") -> Union[str, ToolResult]:
        """
        Executes code in the sandbox environment.
        
        Args:
            code: The code to execute.
            language: The programming language (default: python).
            
        Returns:
            The output of the code execution (stdout + stderr) or error message.
            If images are generated, returns a ToolResult with image artifacts.
        """
        try:
            # Currently only Python is fully supported by the execute method wrapper
            # For other languages, we might need to use shell commands or extend execute
            if language.lower() != "python":
                # Fallback to shell execution for non-python if possible, or implement specific runners
                pass

            result = await sandbox_service.execute(code, session_id=self.session_id)
            
            output_text = []
            images = []
            
            if result.status == "success":
                output_text.append(result.content)
                
                # Handle files (images)
                if result.files:
                    files_desc = []
                    for file_info in result.files:
                        file_name = file_info.get("name", "unknown_file")
                        files_desc.append(f"File generated: {file_name}")
                        
                        # Check if it's an image
                        if file_info.get("type", "").startswith("image/"):
                            try:
                                content_b64 = file_info.get("content")
                                if content_b64:
                                    # Decode base64
                                    image_data = base64.b64decode(content_b64)
                                    
                                    # Save to UPLOADS_DIR for frontend access
                                    from pathlib import Path
                                    # parents[0]=libs, parents[1]=tools, parents[2]=agent, parents[3]=services, parents[4]=app, parents[5]=backend
                                    backend_dir = Path(__file__).resolve().parents[5]
                                    uploads_dir = backend_dir / "data" / "storage"
                                    uploads_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    file_path = uploads_dir / file_name
                                    with open(file_path, "wb") as f:
                                        f.write(image_data)
                                        
                                    public_url = f"/uploads/{file_name}"
                                    
                                    # Create Image object
                                    image_id = str(uuid4())
                                    
                                    images.append(Image(
                                        id=image_id,
                                        url=public_url,
                                        original_prompt=f"Generated from code execution: {file_name}"
                                    ))
                                    logger.info(f"Created image artifact: {file_path}")
                                    
                                    # Explicitly tell the LLM the markdown URL to use
                                    files_desc.append(f"Image is accessible at: {public_url} (You can display it using markdown: ![chart]({public_url}))")
                                    # We don't append the original "File generated" message to avoid confusion
                                    files_desc.pop() # remove the generic message added earlier
                            except Exception as img_err:
                                logger.error(f"Failed to process image {file_name}: {img_err}")
                                files_desc.append(f"(Failed to process image: {img_err})")

                    output_text.append("\n".join(files_desc))
            else:
                output_text.append(f"Error: {result.content}")
            
            final_output = "\n".join(output_text)
            
            if images:
                return ToolResult(
                    content=final_output,
                    images=images
                )
            else:
                return final_output

        except Exception as e:
            return f"Execution failed: {str(e)}"

    async def run_shell(self, command: str) -> str:
        """
        Executes a shell command in the sandbox.
        
        Args:
            command: The shell command to run (e.g., 'ls -la', 'pip install numpy').
            
        Returns:
            The standard output and standard error of the command.
        """
        try:
            res = await sandbox_service.run_shell(self.session_id, command)
            return res.get("content", "")
        except Exception as e:
            return f"Shell command failed: {str(e)}"

    async def read_file(self, path: str) -> str:
        """
        Reads the content of a file from the sandbox.
        
        Args:
            path: The absolute path to the file.
            
        Returns:
            The content of the file.
        """
        try:
            content_bytes = await sandbox_service.download_file(self.session_id, path)
            return content_bytes.decode('utf-8')
        except Exception as e:
            return f"Failed to read file: {str(e)}"

    async def write_file(self, path: str, content: str) -> str:
        """
        Writes content to a file in the sandbox.
        
        Args:
            path: The absolute path to the file.
            content: The content to write.
            
        Returns:
            Success message or error.
        """
        try:
            await sandbox_service.upload_file(self.session_id, path, content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Failed to write file: {str(e)}"

    async def list_files(self, path: str = ".") -> str:
        """
        Lists files in a directory.
        
        Args:
            path: The directory path (default: current directory).
            
        Returns:
            List of files.
        """
        return await self.run_shell(f"ls -la {path}")
