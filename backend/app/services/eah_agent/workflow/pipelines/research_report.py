"""
研究报告工作流
"""

from typing import AsyncGenerator, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.eah_agent.workflow.base import EAHWorkflow
from app.services.eah_agent.workflow.schemas.research_flow import ResearchFlowState
from app.services.eah_agent.workflow.helpers import format_workflow_event, persist_workflow_state
from app.services.eah_agent.core.agent_manager import agent_manager

class ResearchReportWorkflow(EAHWorkflow):
    def __init__(self, db: AsyncSession, session_id: str, query: str, team_config: Dict):
        super().__init__(session_id)
        self.db = db
        self.team_config = team_config
        # Initialize specialized state
        self.state = ResearchFlowState(session_id=session_id, query=query)

    async def run_stream(self) -> AsyncGenerator[str, None]:
        """
        Execute the research workflow using ResearchTeam.
        """
        
        # 1. Initialize Research Team
        yield format_workflow_event("init", "running", "Initializing Research Team...")
        try:
            team_agent = await agent_manager.create_team(self.db, "research", self.team_config)
        except Exception as e:
            yield format_workflow_event("init", "failed", f"Failed to initialize team: {str(e)}")
            return

        # 2. Step: Research
        self.state.current_step = "research"
        yield format_workflow_event("research", "running", f"Researching: {self.state.query}")
        
        # Call the team agent to perform research
        # We use a specific prompt to tell the coordinator to focus on research first
        research_prompt = f"Please research the following topic and provide detailed findings: {self.state.query}"
        
        findings = ""
        async for chunk in team_agent.run(research_prompt, stream=True):
            # We can pass through chunks if needed, but for workflow we might just want to collect
            if isinstance(chunk, str):
                findings += chunk
        
        self.state.results = {"findings": findings}
        self.state.steps_completed.append("research")
        await persist_workflow_state(self.session_id, self.state)
        yield format_workflow_event("research", "completed", "Research phase finished.")
        
        # 3. Step: Write Report
        self.state.current_step = "write"
        yield format_workflow_event("write", "running", "Drafting final report based on findings...")
        
        # Tell the coordinator to write the report based on findings
        write_prompt = f"Based on these findings: {findings}\n\nProduce a formal research report for: {self.state.query}"
        
        report_content = ""
        async for chunk in team_agent.run(write_prompt, stream=True):
            if isinstance(chunk, str):
                report_content += chunk
                # Optionally yield partial content for better UX
                yield format_workflow_event("write", "processing", chunk)
        
        self.state.report_content = report_content
        self.state.steps_completed.append("write")
        await persist_workflow_state(self.session_id, self.state)
        
        yield format_workflow_event("write", "completed", report_content)
        yield format_workflow_event("workflow", "finished", "Research workflow completed successfully.")
