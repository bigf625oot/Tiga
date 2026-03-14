from typing import List, Dict, Optional
import logging
from app.core.i18n import _

class InstructionBuilder:
    """
    Builds the system prompt (instructions) for the agent.
    """
    
    def __init__(self, base_instructions: str = _("You are a helpful assistant.")):
        self.instructions = base_instructions
        self.skill_instructions: List[str] = []
        self.capability_instructions: List[str] = []
        
    def add_market_skills(self, tools_config: List[Dict]):
        """
        Add instructions for market skills.
        """
        market_skills = [t for t in tools_config if isinstance(t, dict) and t.get('type') == 'skill']
        if market_skills:
            skill_instructions = []
            for skill in market_skills:
                if skill.get('content'):
                    skill_instructions.append(f"### Skill: {skill.get('name')}\n{skill.get('content')}")
            
            if skill_instructions:
                self.skill_instructions.extend(skill_instructions)
                
    def add_file_skills(self, snippet: Optional[str]):
        """
        Add instructions for file-based skills.
        """
        if snippet:
            self.skill_instructions.append(snippet)
            
    def add_openclaw_capabilities(self):
        """
        Add instructions for OpenClaw capabilities.
        """
        oc_instructions = _("""
## OpenClaw Capabilities
You have FULL access to OpenClaw tools for automation tasks. You can and should use them directly:
1. `oc_web_search` / `oc_web_fetch`: Search and read web content.
2. `oc_browser`: Control a browser for screenshots, PDF generation, or UI interaction.
3. `oc_cron`: Create, list, and delete scheduled crawl tasks. USE THIS to create new tasks.
4. `oc_nodes`: Manage and execute commands on connected nodes.
5. `oc_message`: Send notifications.

When the user asks to "create a task", "crawl a site", or "configure automation", you MUST use these tools.
Do not say you cannot access the configuration; instead, use the tools to perform the actions.
""")
        self.capability_instructions.append(oc_instructions)

    def add_sandbox_capabilities(self):
        """
        Add instructions for Sandbox capabilities.
        """
        sb_instructions = _("""
## Sandbox Capabilities
You have access to a secure E2B sandbox environment. You can:
1. Execute Python code using `run_code`.
2. Run shell commands using `run_shell` (e.g., install packages, run other languages).
3. Manage files using `read_file`, `write_file`, `list_files`.

When asked to write code or perform tasks:
- Always check the environment first if unsure (e.g., `list_files`).
- Write necessary files before executing them.
- If you need to install packages, use `run_shell('pip install package')`.
""")
        self.capability_instructions.append(sb_instructions)
        
    def add_knowledge_capabilities(self):
        """
        Add instructions for Knowledge Base capabilities.
        """
        kb_instructions = _("""
## Knowledge Base Capabilities
You have access to an advanced Knowledge Graph retrieval system via tools:
1. `search_knowledge_base`: Use for finding specific documents or text chunks (Vector Search).
2. `query_knowledge_graph`: Use for complex questions requiring understanding of entity relationships, global themes, or multi-hop reasoning (Graph Search).
   - Use `mode='local'` for specific entities.
   - Use `mode='global'` for high-level summaries.
   - Use `mode='mix'` (default) for best hybrid results.
""")
        self.capability_instructions.append(kb_instructions)

    def add_cot_prompt(self):
        """
        Add Chain of Thought prompt.
        """
        cot_instructions = _("""
## Reasoning Strategy
Let's think step by step. Break down complex problems into smaller, manageable parts.
Analyze the request, plan your approach, and then execute.
""")
        self.instructions += "\n" + cot_instructions

    def build(self) -> str:
        """
        Construct the final instruction string.
        """
        final_instructions = self.instructions
        
        if self.skill_instructions:
            final_instructions += "\n\n## Enabled Skills\n" + "\n\n".join(self.skill_instructions)
            
        for capability in self.capability_instructions:
            if capability not in final_instructions:
                final_instructions += "\n" + capability
                
        return final_instructions
