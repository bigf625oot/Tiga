import logging
import json
import base64
import tempfile
import os
from uuid import uuid4
from typing import Optional, List, Dict, Any, Union
from agno.tools import Toolkit
from agno.tools.function import ToolResult
from agno.media import Image
from app.services.sandbox.codebox import codebox_service

logger = logging.getLogger(__name__)

class SandboxTools(Toolkit):
    """
    Tools for interacting with the E2B Sandbox environment.
    These tools allow the agent to execute code, run shell commands, and manage files.
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
                # For now, let's warn or try to run as python if it looks like python
                pass

            result = await codebox_service.execute(code, session_id=self.session_id)
            
            output_text = []
            images = []
            
            if result.get("status") == "success":
                output_text.append(result.get("content", ""))
                
                # Handle files (images)
                files = result.get("files", [])
                if files:
                    files_desc = []
                    for file_info in files:
                        file_name = file_info.get("name", "unknown_file")
                        files_desc.append(f"File generated: {file_name}")
                        
                        # Check if it's an image
                        if file_info.get("type", "").startswith("image/"):
                            try:
                                content_b64 = file_info.get("content")
                                if content_b64:
                                    # Decode base64
                                    image_data = base64.b64decode(content_b64)
                                    
                                    # Save to temporary file for Agno Image artifact
                                    # Note: Agno Image expects a URL or local path.
                                    # Since we are in a backend environment, we save it locally.
                                    # In a real production setup, this should be uploaded to S3/Storage and return a public URL.
                                    # For now, we use a temp file which works for local agents.
                                    suffix = ".png" if "png" in file_info.get("type") else ".jpg"
                                    fd, temp_path = tempfile.mkstemp(suffix=suffix)
                                    with os.fdopen(fd, "wb") as tmp:
                                        tmp.write(image_data)
                                    
                                    # Create Image object
                                    image_id = str(uuid4())
                                    file_url = f"file://{temp_path}"
                                    
                                    images.append(Image(
                                        id=image_id,
                                        url=file_url,
                                        original_prompt=f"Generated from code execution: {file_name}"
                                    ))
                                    logger.info(f"Created image artifact: {temp_path}")
                            except Exception as img_err:
                                logger.error(f"Failed to process image {file_name}: {img_err}")
                                files_desc.append(f"(Failed to process image: {img_err})")

                    output_text.append("\n".join(files_desc))
            else:
                output_text.append(f"Error: {result.get('content', 'Unknown error')}")
            
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
            # Efficient way: Use python's subprocess in the sandbox
            # We wrap it to ensure we get stdout/stderr
            wrapper_code = f"""
import subprocess
try:
    result = subprocess.run('{command}', shell=True, capture_output=True, text=True, timeout=60)
    print(result.stdout)
    if result.stderr:
        print('STDERR:', result.stderr)
except Exception as e:
    print(f"Shell execution error: {{e}}")
"""
            # Note: run_shell returns string, so we just take the content if run_code returns ToolResult
            res = await self.run_code(wrapper_code)
            if isinstance(res, ToolResult):
                return res.content
            return res
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
            wrapper_code = f"""
try:
    with open('{path}', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading file: {{e}}")
"""
            res = await self.run_code(wrapper_code)
            if isinstance(res, ToolResult):
                return res.content
            return res
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
            await codebox_service.upload_file(self.session_id, path, content)
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
