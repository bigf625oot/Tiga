import asyncio
import time
import httpx
import argparse
import statistics
from concurrent.futures import ThreadPoolExecutor

async def run_request(client, url, payload):
    start = time.time()
    try:
        response = await client.post(url, json=payload)
        elapsed = time.time() - start
        return response.status_code, elapsed
    except Exception as e:
        return 0, time.time() - start

async def benchmark(url: str, concurrency: int, requests: int):
    print(f"Starting benchmark: {requests} requests with concurrency {concurrency}")
    print(f"Target: {url}")
    
    payload = {
        "code": "print('Hello Benchmark')",
        "session_id": "bench-session"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for _ in range(requests):
            tasks.append(run_request(client, url, payload))
            
        # Run in batches if requests > concurrency? 
        # Actually asyncio.gather runs them all. 
        # To limit concurrency, we should use a semaphore.
        
        sem = asyncio.Semaphore(concurrency)
        
        async def sem_task():
            async with sem:
                return await run_request(client, url, payload)
        
        start_time = time.time()
        results = await asyncio.gather(*[sem_task() for _ in range(requests)])
        total_time = time.time() - start_time
        
    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]
    
    success_count = status_codes.count(200)
    avg_latency = statistics.mean(latencies) if latencies else 0
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    
    print("\n--- Results ---")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests: {requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Success Rate: {success_count/requests*100:.1f}% ({success_count}/{requests})")
    print(f"Avg Latency: {avg_latency*1000:.2f}ms")
    print(f"P95 Latency: {p95_latency*1000:.2f}ms")
    print(f"RPS: {requests/total_time:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sandbox Benchmark Tool")
    parser.add_argument("--url", default="http://localhost:8000/api/v1/sandbox/run", help="Target URL")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--requests", type=int, default=50, help="Total requests")
    
    args = parser.parse_args()
    
    asyncio.run(benchmark(args.url, args.concurrency, args.requests))
