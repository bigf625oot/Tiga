import asyncio
import time
import statistics
from app.workflow.app_workflow import AppWorkflow

async def run_benchmark():
    print("Starting Workflow Benchmark...")
    
    # Mock data
    session_id = "bench_session"
    user_msg = "What is the time?"
    
    # Static Mode
    print("\n--- Static Mode ---")
    static_times = []
    for i in range(5):
        start = time.perf_counter()
        wf = AppWorkflow(session_id=session_id, mode="static")
        # We assume we can run without actual API keys if we mock or if env is set.
        # Since we can't easily mock here without external lib, we rely on the environment or failure.
        # But for benchmark script, usually we want it to run.
        # We will try to run, if it fails, we catch.
        try:
            await wf.run(user_msg)
        except Exception as e:
            print(f"Run {i} failed: {e}")
            continue
        duration = time.perf_counter() - start
        static_times.append(duration)
        print(f"Run {i}: {duration:.4f}s")
    
    # Dynamic Mode
    print("\n--- Dynamic Mode ---")
    dynamic_times = []
    for i in range(5):
        start = time.perf_counter()
        wf = AppWorkflow(session_id=session_id, mode="dynamic")
        try:
            await wf.run(user_msg)
        except Exception as e:
            print(f"Run {i} failed: {e}")
            continue
        duration = time.perf_counter() - start
        dynamic_times.append(duration)
        print(f"Run {i}: {duration:.4f}s")
        
    print("\n=== Results ===")
    if static_times:
        print(f"Static: Mean={statistics.mean(static_times):.4f}s")
    if dynamic_times:
        print(f"Dynamic: Mean={statistics.mean(dynamic_times):.4f}s")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
