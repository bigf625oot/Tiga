import asyncio
import statistics
import time
from typing import List

import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def _timed(coro):
    start = time.perf_counter()
    res = await coro
    return (time.perf_counter() - start) * 1000.0, res


async def main(concurrency: int = 50, iterations: int = 200):
    latencies: List[float] = []
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        t_ms, resp = await _timed(
            client.post(
                "/task-mode/tasks",
                json={"name": "benchmark-task", "description": "d", "status": "open", "priority": 3, "created_by": "bench"},
            )
        )
        task = resp.json()
        task_id = task["id"]
        latencies.append(t_ms)

        async def worker(i: int):
            t1, _ = await _timed(client.get(f"/task-mode/tasks/{task_id}"))
            t2, _ = await _timed(client.get(f"/task-mode/tasks/{task_id}/versions?limit=20"))
            t3, _ = await _timed(
                client.post(
                    f"/task-mode/tasks/{task_id}/qas",
                    json={"question": f"Q{i}", "answer": f"A{i}", "user_id": "bench"},
                )
            )
            t4, _ = await _timed(client.get(f"/task-mode/tasks/{task_id}/qas?limit=50"))
            return [t1, t2, t3, t4]

        sem = asyncio.Semaphore(concurrency)

        async def guarded(i: int):
            async with sem:
                return await worker(i)

        results = await asyncio.gather(*[guarded(i) for i in range(iterations)])
        for r in results:
            latencies.extend(r)

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    p99 = latencies[int(len(latencies) * 0.99) - 1]
    print(f"count={len(latencies)} p50_ms={p50:.2f} p95_ms={p95:.2f} p99_ms={p99:.2f}")


if __name__ == "__main__":
    asyncio.run(main())

