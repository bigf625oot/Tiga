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
            # For JavaScript, we save to a file and run via node
            if language.lower() in ("javascript", "js", "node"):
                file_name = f"script_{uuid4().hex[:8]}.js"
                await self.write_file(file_name, code)
                
                # Check if docx is needed
                if "require('docx')" in code or "require(\"docx\")" in code:
                    # Install docx if not present (this might take a few seconds, but it's cached in the session)
                    await sandbox_service.run_shell(self.session_id, "npm list docx || npm install docx")
                    
                res = await sandbox_service.run_shell(self.session_id, f"node {file_name}")
                
                output_text = []
                if res.get("status") == "success":
                    output_text.append(res.get("content", ""))
                else:
                    output_text.append(f"Error executing JavaScript:\n{res.get('content')}")
            else:
                # Default to python via execute
                result = await sandbox_service.execute(code, session_id=self.session_id)
                
                output_text = []
                images = []
                
                if result.status == "success":
                    output_text.append(result.content)
                    
                    # Handle files (images from execution.results)
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
            
            # Common file scanner for ANY language execution
            # Scan for new .docx, .pdf, .html, .csv, .xlsx files generated in workspace
            list_res = await sandbox_service.run_shell(self.session_id, "ls -1 *.docx *.pdf *.html *.csv *.xlsx 2>/dev/null || true")
            if list_res.get("status") == "success":
                new_files = [f.strip() for f in list_res.get("content", "").split("\n") if f.strip()]
                for f in new_files:
                    if f.startswith("script_"): continue
                    try:
                        file_bytes = await sandbox_service.download_file(self.session_id, f)
                        from pathlib import Path
                        backend_dir = Path(__file__).resolve().parents[5]
                        uploads_dir = backend_dir / "data" / "storage"
                        uploads_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Use unique name to avoid conflicts
                        unique_name = f"{uuid4().hex[:8]}_{f}"
                        file_path = uploads_dir / unique_name
                        with open(file_path, "wb") as local_f:
                            local_f.write(file_bytes)
                        
                        public_url = f"/uploads/{unique_name}"
                        # Check if we already logged this file via execution.results
                        already_logged = any(f in str(out) for out in output_text)
                        if not already_logged:
                            output_text.append(f"\n<tiga-artifact type=\"file\" url=\"{public_url}\" name=\"{f}\"></tiga-artifact>")
                    except Exception as e:
                        logger.error(f"Failed to download generated file {f}: {e}")

            final_output = "\n".join(output_text)
            
            if 'images' in locals() and images:
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
