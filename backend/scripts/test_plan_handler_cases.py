import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
sys.path.append("d:/Tiga/backend")

from app.services.agent.handlers.plan_handler import PlanHandler
from app.services.agent.core.agent_nlu import IntentResult

async def test_case_13():
    print("Running Test Case 13: Agent 装配失败隔离测试")
    handler = PlanHandler()
    
    # Mocking
    handler._assemble_plan_agent = AsyncMock(side_effect=Exception("Simulated AgentAssembler Error"))
    handler._prepare_history = AsyncMock(return_value=([], False))
    
    with patch("app.services.agent.handlers.plan_handler.FileOrchestrator.process_batch", new_callable=AsyncMock) as mock_file:
        mock_file.return_value = {"context": "", "media": [], "results": []}
        
        try:
            gen = handler.process(
                input_text="Test",
                db=MagicMock(),
                session_id="test_session",
                agent_id="test_agent"
            )
            
            events = []
            async for event in gen:
                events.append(event)
                
            error_events = [e for e in events if e.get("type") == "error"]
            if error_events:
                print("✅ Pass: Caught error and yielded error event")
            else:
                print("❌ Fail: Generator finished without error event")
        except Exception as e:
            print(f"❌ Fail: Unhandled exception escaped the generator: {e}")

async def test_case_55():
    print("\nRunning Test Case 55: 空输入参数边界测试")
    handler = PlanHandler()
    
    try:
        gen = handler.process(input_text="Test") # No db, no session_id
        # We just need to trigger the first step
        await gen.__anext__() # status yield
        await gen.__anext__() # setup tasks trigger
        print("❌ Fail: No assertion protection for missing db/session_id at early stage")
    except AssertionError:
        print("✅ Pass: Asserted missing parameters")
    except Exception as e:
        print(f"❌ Fail: Failed with some other error: {e}")

async def test_case_10():
    print("\nRunning Test Case 10: 任务目标增强验证")
    handler = PlanHandler()
    res = handler._enrich_goal("测试目标", "测试指令")
    if "respect dependencies" in res or "遵循依赖感知协议" in res:
        print("✅ Pass: Contains mandatory dependency perception protocol mission")
    else:
        print("❌ Fail: Missing mandatory mission description")

async def main():
    await test_case_13()
    await test_case_55()
    await test_case_10()

if __name__ == "__main__":
    asyncio.run(main())
