import pytest
import json
from unittest.mock import AsyncMock, patch

# Mock AppWorkflow
async def mock_run_stream(*args, **kwargs):
    events = [
        json.dumps({"system": True, "status": "info", "output": "System initialized"}),
        json.dumps({"step": "retrieve", "status": "running"}),
        json.dumps({"step": "retrieve", "status": "success", "output": "Retrieving data..."}),
        json.dumps({"step": "execute", "status": "running"}),
        json.dumps({"step": "execute", "status": "running", "output": "Processing..."}),
        json.dumps({"step": "finish", "status": "success", "output": "Final Result"}),
    ]
    for event in events:
        yield event

@pytest.mark.asyncio
async def test_run_workflow_stream_full_event(client):
    with patch("app.api.endpoints.agent_workflow.AppWorkflow") as MockWorkflow:
        instance = MockWorkflow.return_value
        instance.run_stream = mock_run_stream
        
        # Mock crud_chat dependencies
        with patch("app.api.endpoints.agent_workflow.crud_chat") as mock_crud:
            mock_crud.create_message = AsyncMock()
            mock_crud.get_history = AsyncMock(return_value=[])
            
            response = client.post(
                "/api/v1/agent-workflows/run_stream",
                json={
                    "session_id": "test_session",
                    "message": "test message",
                    "mode": "static"
                }
            )
            
            assert response.status_code == 200
            
            content = response.content.decode("utf-8")
            lines = [l for l in content.strip().split("\n\n") if l]
            
            data_lines = [l for l in lines if "[DONE]" not in l and l.startswith("data: ")]
            
            assert len(data_lines) == 6
            
            # Check 1st event (System)
            e0 = json.loads(data_lines[0].replace("data: ", ""))
            assert e0["system"] is True
            assert e0["output"] == "System initialized"
            
            # Check 2nd event (Step Running)
            e1 = json.loads(data_lines[1].replace("data: ", ""))
            assert e1["step"] == "retrieve"
            assert e1["status"] == "running"
            
            # Check 3rd event (Step Success with Output)
            e2 = json.loads(data_lines[2].replace("data: ", ""))
            assert e2["output"] == "Retrieving data..."
            assert "step" in e2
            
            # Check 5th event (Execution Output)
            e4 = json.loads(data_lines[4].replace("data: ", ""))
            assert e4["output"] == "Processing..."
