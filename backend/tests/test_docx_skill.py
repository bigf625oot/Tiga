import asyncio
import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Pre-import to resolve SQLAlchemy mapper issue
import app.models.agent
import app.models.chat

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.agent.orchestration.control_plane import AgnoControlPlane

# Create a mock class for request to bypass Pydantic issues in tests
class MockChatRequest:
    def __init__(self, message, mode="quick", stream=False):
        self.message = message
        self.mode = mode
        self.stream = stream
        self.agent_id = "" # Force AgentAssembler to create adhoc agent

logging.basicConfig(level=logging.INFO)

async def test_docx_skill():
    async for db in get_db():
        # Create control plane with a dummy agent
        control_plane = AgnoControlPlane()
        
        # Prepare request
        request = MockChatRequest(
            message="请使用 docx 技能，将以下内容转换为 word 文档：\n\n# 这是一个测试文档\n这是用来测试本地引擎的。你必须调用 execute_skill 工具。",
            mode="quick",
            stream=False
        )
        
        # We need a session ID, using a mock one
        session_id = "test-session-123"
        
        # Get iterator
        try:
            print("--- Starting Execution ---")
            iterator = control_plane.process_stream(
                user_input=request.message,
                db=db,
                session_id=session_id,
                agent_id=request.agent_id,
                mode=request.mode
            )
            async for chunk in iterator:
                print(chunk)
            print("--- Execution Finished ---")
        except Exception as e:
            print(f"Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_docx_skill())