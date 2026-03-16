import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.eah_agent.handlers.plan_handler import PlanHandler
from app.models.llm_model import LLMModel
from app.services.eah_agent.core.nlu import IntentResult

@pytest.mark.asyncio
async def test_plan_handler_flow():
    # Mock LLM Model
    mock_model = LLMModel(model_id="gpt-4-turbo", provider="openai", api_key="test")
    
    # Initialize Handler
    handler = PlanHandler(llm_model=mock_model)
    
    # Helper to create tool call mock
    def create_tool_call(name, args):
        tc = MagicMock()
        tc.function.name = name
        tc.function.arguments = args
        return tc

    # Mock AgentFactory to return a Mock Agent
    mock_agent = MagicMock()
    mock_response_stream = [
        # Chunk 1: Thinking
        MagicMock(content=None, reasoning="I need to search for policies first.", tool_calls=[]),
        # Chunk 2: Tool Call (Update Plan)
        MagicMock(content=None, reasoning=None, tool_calls=[
            create_tool_call("update_plan", '{"steps": [{"title": "Search Policy", "status": "pending"}]}')
        ]),
        # Chunk 3: Tool Call (Search)
        MagicMock(content=None, reasoning=None, tool_calls=[
            create_tool_call("duckduckgo", '{"query": "Low Altitude Economy Policy 2024"}')
        ]),
        # Chunk 4: Tool Call (Python - Generate Code)
        MagicMock(content=None, reasoning=None, tool_calls=[
            create_tool_call("python", '{"code": "print(\'Generating Report...\')"}')
        ]),
        # Chunk 5: File Generation
        MagicMock(content=None, reasoning=None, tool_calls=[
            create_tool_call("save_file", '{"file_path": "report.docx", "content": "..."}')
        ]),
        # Chunk 6: Final Content
        MagicMock(content="Report generated successfully.", reasoning=None, tool_calls=[])
    ]
    
    # Mock agent.run to return the stream
    mock_agent.run.return_value = mock_response_stream
    handler.agent = mock_agent # Inject mock agent directly or via mock factory
    
    # Process
    input_text = "Research Low Altitude Economy"
    intent = IntentResult(intent="task", confidence=1.0)
    
    results = []
    async for chunk in handler.process(input_text, intent, db=AsyncMock(), session_id="test-session"):
        results.append(chunk)
        print(f"Received chunk: {chunk}")

    # Assertions
    # 1. Check for status
    assert any(r['type'] == 'status' and 'Analyzing' in r['content'] for r in results)
    
    # 2. Check for think
    assert any(r['type'] == 'think' and 'search' in r['content'] for r in results)
    
    # 3. Check for plan_step
    plan_chunk = next((r for r in results if r['type'] == 'plan_step'), None)
    assert plan_chunk is not None
    assert plan_chunk['content'][0]['title'] == "Search Policy"
    
    # 4. Check for tool_call (python)
    python_chunk = next((r for r in results if r['type'] == 'tool_call' and r['content']['tool'] == 'python'), None)
    assert python_chunk is not None
    assert "print" in python_chunk['content']['input']
    
    # 5. Check for file
    file_chunk = next((r for r in results if r['type'] == 'file'), None)
    assert file_chunk is not None
    assert file_chunk['content']['name'] == "report.docx"
    
    # 6. Check for final content
    assert any(r['type'] == 'content' and 'Report generated' in r['content'] for r in results)

if __name__ == "__main__":
    asyncio.run(test_plan_handler_flow())
