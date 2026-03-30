import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import SkillValidationError
from .loaders.base import SkillLoader
from .skill import Skill
from .utils import is_safe_path, read_file_safe, run_script
from agno.tools.function import Function
from agno.utils.log import log_debug, log_warning


class Skills:
    """Orchestrates skill loading and provides tools for agents to access skills.

    The Skills class is responsible for:
    1. Loading skills from various sources (loaders)
    2. Providing methods to access loaded skills
    3. Generating tools for agents to use skills
    4. Creating system prompt snippets with available skills metadata

    Args:
        loaders: List of SkillLoader instances to load skills from.
    """

    def __init__(self, loaders: List[SkillLoader], allowed_skills: Optional[set[str]] = None):
        self.loaders = loaders
        self.allowed_skills = allowed_skills
        self._skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """Load skills from all loaders.

        Raises:
            SkillValidationError: If any skill fails validation.
        """
        for loader in self.loaders:
            try:
                skills = loader.load()
                for skill in skills:
                    if self.allowed_skills is not None and skill.name not in self.allowed_skills:
                        continue
                    if skill.name in self._skills:
                        log_warning(f"Duplicate skill name '{skill.name}', overwriting with newer version")
                    self._skills[skill.name] = skill
            except SkillValidationError:
                raise  # Re-raise validation errors as hard failures
            except Exception as e:
                log_warning(f"Error loading skills from {loader}: {e}")

        log_debug(f"Loaded {len(self._skills)} total skills")

    def reload(self) -> None:
        """Reload skills from all loaders, clearing existing skills.

        Raises:
            SkillValidationError: If any skill fails validation.
        """
        self._skills.clear()
        self._load_skills()

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name.

        Args:
            name: The name of the skill to retrieve.

        Returns:
            The Skill object if found, None otherwise.
        """
        return self._skills.get(name)

    def get_all_skills(self) -> List[Skill]:
        """Get all loaded skills.

        Returns:
            A list of all loaded Skill objects.
        """
        return list(self._skills.values())

    def get_skill_names(self) -> List[str]:
        """Get the names of all loaded skills.

        Returns:
            A list of skill names.
        """
        return list(self._skills.keys())

    def get_system_prompt_snippet(self) -> str:
        """Generate a system prompt snippet with available skills metadata.

        This creates an XML-formatted snippet that provides the agent with
        information about available skills without including the full instructions.

        Returns:
            An XML-formatted string with skills metadata.
        """
        if not self._skills:
            return ""

        lines = [
            "<skills_system>",
            "",
            "## What are Skills?",
            "Skills are packages of domain expertise that extend your capabilities. Each skill contains:",
            "- **Instructions**: Detailed guidance on when and how to apply the skill",
            "- **Scripts**: Executable code templates you can use or adapt",
            "- **References**: Supporting documentation (guides, cheatsheets, examples)",
            "",
            "## IMPORTANT: How to Use Skills",
            "**Skill names are NOT callable functions.** You cannot call a skill directly by its name.",
            "Instead, you MUST use the provided skill access tools:",
            "",
            "1. `get_skill_instructions(skill_name)` - Load the full instructions for a skill",
            "2. `get_skill_reference(skill_name, reference_path)` - Access specific documentation",
            "3. `get_skill_script(skill_name, script_path, execute=False)` - Read or run scripts",
            "",
            "## Progressive Discovery Workflow",
            "1. **Browse**: Review the skill summaries below to understand what's available",
            "2. **Load**: When a task matches a skill, call `get_skill_instructions(skill_name)` first",
            "3. **Reference**: Use `get_skill_reference` to access specific documentation as needed",
            "4. **Scripts**: Use `get_skill_script` to read or execute scripts from a skill",
            "",
            "**IMPORTANT**: References are documentation files (NOT executable). Only use `get_skill_script` when `<scripts>` lists actual script files. If `<scripts>none</scripts>`, do NOT call `get_skill_script`.",
            "",
            "This approach ensures you only load detailed instructions when actually needed.",
            "",
            "## Available Skills",
        ]
        for skill in self._skills.values():
            lines.append("<skill>")
            lines.append(f"  <name>{skill.name}</name>")
            lines.append(f"  <description>{skill.description}</description>")
            if skill.scripts:
                script_names = [s["name"] if isinstance(s, dict) else s for s in skill.scripts]
                lines.append(f"  <scripts>{', '.join(script_names)}</scripts>")
            else:
                # Explicitly indicate no scripts to prevent model confusion
                lines.append("  <scripts>none</scripts>")
            if skill.references:
                ref_names = [r["name"] if isinstance(r, dict) else r for r in skill.references]
                lines.append(f"  <references>{', '.join(ref_names)}</references>")
            lines.append("</skill>")
        lines.append("")
        lines.append("</skills_system>")

        return "\n".join(lines)

    def get_tools(self) -> List[Function]:
        """Get the tools for accessing skills.

        Returns:
            A list of Function objects that agents can use to access skills.
        """
        tools: List[Function] = []

        # Tool: get_skill_instructions
        tools.append(
            Function(
                name="get_skill_instructions",
                description="Load the full instructions for a skill. Use this when you need to follow a skill's guidance.",
                entrypoint=self._get_skill_instructions,
            )
        )

        # Tool: get_skill_reference
        tools.append(
            Function(
                name="get_skill_reference",
                description="Load a reference document from a skill's references. Use this to access detailed documentation.",
                entrypoint=self._get_skill_reference,
            )
        )

        # Tool: get_skill_script
        tools.append(
            Function(
                name="get_skill_script",
                description="Read or execute a script from a skill. Set execute=True to run the script and get output, or execute=False (default) to read the script content.",
                entrypoint=self._get_skill_script,
            )
        )

        # Tool: execute_skill (P10 动态路由执行器入口)
        tools.append(
            Function(
                name="execute_skill",
                description="""Directly execute a skill by its name and pass the required parameters. The system will automatically route it to the sandbox or local engine. 
CRITICAL: If the user explicitly asks you to use a specific skill (e.g., 'docx'), you MUST use this tool to execute it instead of answering the user directly.""",
                entrypoint=self._execute_skill,
            )
        )

        return tools

    def _get_skill_instructions(self, skill_name: str) -> str:
        """Load the full instructions for a skill.

        Args:
            skill_name: The name of the skill to get instructions for.

        Returns:
            A JSON string with the skill's instructions and metadata.
        """
        skill = self.get_skill(skill_name)
        if skill is None:
            available = ", ".join(self.get_skill_names())
            return json.dumps(
                {
                    "error": f"Skill '{skill_name}' not found",
                    "available_skills": available,
                }
            )

        return json.dumps(
            {
                "skill_name": skill.name,
                "description": skill.description,
                "instructions": skill.instructions,
                "available_scripts": skill.scripts,
                "available_references": skill.references,
            }
        )

    def _get_skill_reference(self, skill_name: str, reference_path: str) -> str:
        """Load a reference document from a skill.

        Args:
            skill_name: The name of the skill.
            reference_path: The filename of the reference document.

        Returns:
            A JSON string with the reference content.
        """
        skill = self.get_skill(skill_name)
        if skill is None:
            available = ", ".join(self.get_skill_names())
            return json.dumps(
                {
                    "error": f"Skill '{skill_name}' not found",
                    "available_skills": available,
                }
            )

        if reference_path not in skill.references:
            return json.dumps(
                {
                    "error": f"Reference '{reference_path}' not found in skill '{skill_name}'",
                    "available_references": skill.references,
                }
            )

        # Validate path to prevent path traversal attacks
        refs_dir = Path(skill.source_path) / "references"
        if not is_safe_path(refs_dir, reference_path):
            return json.dumps(
                {
                    "error": f"Invalid reference path: '{reference_path}'",
                    "skill_name": skill_name,
                }
            )

        # Load the reference file
        ref_file = refs_dir / reference_path
        try:
            content = read_file_safe(ref_file)
            return json.dumps(
                {
                    "skill_name": skill_name,
                    "reference_path": reference_path,
                    "content": content,
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "error": f"Error reading reference file: {e}",
                    "skill_name": skill_name,
                    "reference_path": reference_path,
                }
            )

    def _get_skill_script(
        self,
        skill_name: str,
        script_path: str,
        execute: bool = False,
        args: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> str:
        """Read or execute a script from a skill.

        Args:
            skill_name: The name of the skill.
            script_path: The filename of the script.
            execute: If True, execute the script. If False (default), return content.
            args: Optional list of arguments to pass to the script (only used if execute=True).
            timeout: Maximum execution time in seconds (default: 30, only used if execute=True).

        Returns:
            A JSON string with either the script content or execution results.
        """
        skill = self.get_skill(skill_name)
        if skill is None:
            available = ", ".join(self.get_skill_names())
            return json.dumps(
                {
                    "error": f"Skill '{skill_name}' not found",
                    "available_skills": available,
                }
            )

        if script_path not in skill.scripts:
            return json.dumps(
                {
                    "error": f"Script '{script_path}' not found in skill '{skill_name}'",
                    "available_scripts": skill.scripts,
                }
            )

        # Validate path to prevent path traversal attacks
        scripts_dir = Path(skill.source_path) / "scripts"
        if not is_safe_path(scripts_dir, script_path):
            return json.dumps(
                {
                    "error": f"Invalid script path: '{script_path}'",
                    "skill_name": skill_name,
                }
            )

        script_file = scripts_dir / script_path

        if not execute:
            # Read mode: return script content
            try:
                content = read_file_safe(script_file)
                return json.dumps(
                    {
                        "skill_name": skill_name,
                        "script_path": script_path,
                        "content": content,
                    }
                )
            except Exception as e:
                return json.dumps(
                    {
                        "error": f"Error reading script file: {e}",
                        "skill_name": skill_name,
                        "script_path": script_path,
                    }
                )

        # Execute mode: run the script
        try:
            result = run_script(
                script_path=script_file,
                args=args,
                timeout=timeout,
                cwd=Path(skill.source_path),
            )
            return json.dumps(
                {
                    "skill_name": skill_name,
                    "script_path": script_path,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            )
        except subprocess.TimeoutExpired:
            return json.dumps(
                {
                    "error": f"Script execution timed out after {timeout} seconds",
                    "skill_name": skill_name,
                    "script_path": script_path,
                }
            )
        except FileNotFoundError as e:
            return json.dumps(
                {
                    "error": f"Interpreter or script not found: {e}",
                    "skill_name": skill_name,
                    "script_path": script_path,
                }
            )
    def _execute_skill(self, skill_name: str, **kwargs: Any) -> str:
        """
        [P10 Architecture] Dynamic Skill Router.
        This is the unified entrypoint for LLM to execute a specific skill.
        The framework will dynamically route the execution to Sandbox or LocalEngine based on the Skill's metadata.
        
        Args:
            skill_name: The name of the skill to execute (e.g. 'docx').
            **kwargs: Dynamic parameters required by the skill (e.g., markdown_content="...").
            
        Returns:
            Execution result as a JSON string.
        """
        skill = self.get_skill(skill_name)
        if skill is None:
            # Fallback if LLM passed 'name' instead of 'skill_name'
            alt_name = kwargs.get('name')
            if alt_name:
                skill = self.get_skill(alt_name)
                
        if skill is None:
            available = ", ".join(self.get_skill_names())
            return json.dumps(
                {
                    "error": f"Skill '{skill_name}' not found",
                    "available_skills": available,
                }
            )
            
        # 兼容 LLM 可能把参数包在 'parameters' 字典里的情况
        parameters = kwargs.get("parameters", kwargs)
        
        # 路由策略分发
        if skill.execution_mode == "local_engine":
            log_debug(f"Routing skill '{skill_name}' to LocalEngine ({skill.engine_route})")
            return self._route_to_local_engine(skill, parameters)
        else:
            log_debug(f"Routing skill '{skill_name}' to Sandbox")
            # 默认 fallback 到要求 LLM 自己去读脚本并在沙箱里跑，
            # 或者直接触发沙箱的通用入口 (此处为简化，提示 LLM 继续使用 run_code)
            return json.dumps(
                {
                    "status": "delegated_to_sandbox",
                    "instruction": f"The skill '{skill_name}' requires sandbox execution. Please use `get_skill_script` to read its script, and then use `run_code` or `run_shell` from SandboxTools to execute it with parameters: {parameters}"
                }
            )
            
    def _route_to_local_engine(self, skill: Skill, parameters: Dict[str, Any]) -> str:
        """
        将请求路由给本地的高性能纯函数微服务
        """
        route = skill.engine_route
        if not route:
            return json.dumps({"error": f"Skill '{skill.name}' is marked as local_engine but lacks 'engine_route'"})
            
        if route == "node:md_to_docx":
            # 针对 MD 转 DOCX 的本地路由实现
            try:
                import tempfile
                from uuid import uuid4
                
                # 兼容大模型传递 content 或 markdown_content 的行为
                markdown_content = parameters.get("markdown_content") or parameters.get("content", "")
                if not markdown_content:
                    return json.dumps({"error": "Missing 'markdown_content' or 'content' parameter"})
                    
                output_filename = parameters.get("output_filename")
                if not output_filename:
                    output_filename = f"document_{uuid4().hex[:8]}.docx"
                elif not output_filename.endswith(".docx"):
                    output_filename += ".docx"
                    
                backend_dir = Path(__file__).resolve().parents[5]
                uploads_dir = backend_dir / "data" / "storage"
                uploads_dir.mkdir(parents=True, exist_ok=True)
                output_path = uploads_dir / output_filename
                
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as temp_md:
                    temp_md.write(markdown_content)
                    temp_md_path = temp_md.name
                    
                try:
                    script_path = backend_dir / "app" / "services" / "agent" / "tools" / "libs" / "scripts" / "md_to_docx.js"
                    process = subprocess.run(
                        ['node', str(script_path), temp_md_path, str(output_path)],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if process.returncode != 0:
                        return json.dumps({"error": f"Node renderer failed: {process.stderr}"})
                finally:
                    import os
                    if os.path.exists(temp_md_path):
                        os.remove(temp_md_path)
                        
                public_url = f"/uploads/{output_filename}"
                
                result_msg = (
                    f"Conversion successful! File generated: {output_filename}\n"
                    f"Download link: {public_url}\n"
                    f"Please provide this link to the user in your final response: [Download Word Document]({public_url})\n"
                    f"<tiga-artifact type=\"file\" url=\"{public_url}\" name=\"{output_filename}\"></tiga-artifact>"
                )
                
                return json.dumps({"status": "success", "result": result_msg})
                
            except Exception as e:
                return json.dumps({"error": f"Local engine execution failed: {str(e)}"})
                
        return json.dumps({"error": f"Unknown engine_route: {route}"})
