import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
import pytest

# 压测配置
CONCURRENT_REQUESTS = 100
TOTAL_REQUESTS = 1000
DURATION_SECONDS = 300  # 5分钟

class LoadTestResult:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.connection_errors = 0
        self.status_codes = {}
        self.start_time = None
        self.end_time = None
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0
    
    @property
    def avg_response_time(self) -> float:
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0
    
    @property
    def requests_per_second(self) -> float:
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        return self.total_requests / duration if duration > 0 else 0

async def make_request(session: aiohttp.ClientSession, base_url: str, prompt: str) -> Dict[str, Any]:
    """发送单个请求"""
    url = f"{base_url}/api/openclaw/create_task"
    payload = {
        "prompt": prompt
    }
    
    start_time = time.time()
    
    try:
        async with session.post(url, json=payload) as response:
            response_time = time.time() - start_time
            
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "status_code": response.status,
                    "response_time": response_time,
                    "task_id": data.get("task_id"),
                    "status": data.get("status")
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status,
                    "response_time": response_time,
                    "error": await response.text()
                }
                
    except aiohttp.ClientError as e:
        return {
            "success": False,
            "status_code": 0,
            "response_time": time.time() - start_time,
            "error": str(e),
            "connection_error": True
        }

async def worker(
    worker_id: int,
    session: aiohttp.ClientSession,
    base_url: str,
    result: LoadTestResult,
    semaphore: asyncio.Semaphore,
    stop_event: asyncio.Event
):
    """工作协程"""
    prompts = [
        "每天早上9点抓取百度首页",
        "每小时检查一次GitHub状态",
        "每天晚上备份数据库",
        "每周一清理临时文件",
        "实时监控网站可用性"
    ]
    
    while not stop_event.is_set():
        async with semaphore:
            try:
                prompt = prompts[worker_id % len(prompts)]
                response = await make_request(session, base_url, prompt)
                
                result.total_requests += 1
                
                if response["success"]:
                    result.successful_requests += 1
                else:
                    result.failed_requests += 1
                
                if response.get("connection_error"):
                    result.connection_errors += 1
                
                status_code = response["status_code"]
                result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
                
                result.response_times.append(response["response_time"])
                
                # 小延迟避免过载
                await asyncio.sleep(0.01)
                
            except Exception as e:
                result.failed_requests += 1
                result.total_requests += 1
                logger.error(f"Worker {worker_id} error: {e}")

async def run_load_test(base_url: str) -> LoadTestResult:
    """运行压测"""
    result = LoadTestResult()
    result.start_time = datetime.utcnow()
    
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    stop_event = asyncio.Event()
    
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_REQUESTS * 2,
        limit_per_host=CONCURRENT_REQUESTS,
        ttl_dns_cache=300,
        keepalive_timeout=30
    )
    
    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector
    ) as session:
        # 启动工作协程
        workers = []
        for i in range(CONCURRENT_REQUESTS):
            worker_task = asyncio.create_task(
                worker(i, session, base_url, result, semaphore, stop_event)
            )
            workers.append(worker_task)
        
        # 运行指定时间
        await asyncio.sleep(DURATION_SECONDS)
        
        # 停止所有工作协程
        stop_event.set()
        
        # 等待所有工作协程完成
        await asyncio.gather(*workers, return_exceptions=True)
    
    result.end_time = datetime.utcnow()
    return result

def print_test_report(result: LoadTestResult):
    """打印测试报告"""
    print("\n" + "="*60)
    print("OpenClaw create_task 压测报告")
    print("="*60)
    
    print(f"测试时间: {result.start_time} - {result.end_time}")
    print(f"总请求数: {result.total_requests}")
    print(f"成功请求: {result.successful_requests}")
    print(f"失败请求: {result.failed_requests}")
    print(f"成功率: {result.success_rate:.2%}")
    print(f"QPS: {result.requests_per_second:.2f}")
    print(f"平均响应时间: {result.avg_response_time*1000:.2f}ms")
    
    if result.response_times:
        response_times_ms = [t*1000 for t in result.response_times]
        print(f"最小响应时间: {min(response_times_ms):.2f}ms")
        print(f"最大响应时间: {max(response_times_ms):.2f}ms")
        
        # 计算百分位数
        response_times_ms.sort()
        p50_idx = int(len(response_times_ms) * 0.5)
        p95_idx = int(len(response_times_ms) * 0.95)
        p99_idx = int(len(response_times_ms) * 0.99)
        
        print(f"P50响应时间: {response_times_ms[p50_idx]:.2f}ms")
        print(f"P95响应时间: {response_times_ms[p95_idx]:.2f}ms")
        print(f"P99响应时间: {response_times_ms[p99_idx]:.2f}ms")
    
    print(f"\n状态码分布:")
    for status_code, count in sorted(result.status_codes.items()):
        print(f"  {status_code}: {count}")
    
    print(f"\n连接错误: {result.connection_errors}")
    
    # 验收标准检查
    print("\n" + "="*60)
    print("验收标准检查")
    print("="*60)
    
    # 标准1: 成功率 >= 95%
    success_rate_ok = result.success_rate >= 0.95
    print(f"✓ 成功率 >= 95%: {success_rate_ok} ({result.success_rate:.2%})")
    
    # 标准2: QPS >= 100
    qps_ok = result.requests_per_second >= 100
    print(f"✓ QPS >= 100: {qps_ok} ({result.requests_per_second:.2f})")
    
    # 标准3: P95响应时间 <= 1000ms
    if result.response_times:
        p95_time = sorted([t*1000 for t in result.response_times])[int(len(result.response_times) * 0.95)]
        p95_ok = p95_time <= 1000
        print(f"✓ P95响应时间 <= 1000ms: {p95_ok} ({p95_time:.2f}ms)")
    
    # 标准4: 连接错误率 <= 1%
    connection_error_rate = result.connection_errors / result.total_requests if result.total_requests > 0 else 0
    connection_ok = connection_error_rate <= 0.01
    print(f"✓ 连接错误率 <= 1%: {connection_ok} ({connection_error_rate:.2%})")
    
    overall_ok = success_rate_ok and qps_ok and (not result.response_times or p95_ok) and connection_ok
    print(f"\n总体结果: {'✓ 通过' if overall_ok else '✗ 未通过'}")
    print("="*60)

@pytest.mark.asyncio
async def test_openclaw_create_task_load():
    """OpenClaw create_task 压测"""
    # 这里需要配置实际的测试服务器地址
    base_url = "http://localhost:8000"
    
    print(f"开始压测: {base_url}")
    print(f"并发数: {CONCURRENT_REQUESTS}")
    print(f"持续时间: {DURATION_SECONDS}秒")
    print(f"预期总请求数: ~{CONCURRENT_REQUESTS * (DURATION_SECONDS / 0.1)}")
    
    result = await run_load_test(base_url)
    print_test_report(result)
    
    # 保存结果到文件
    import json
    result_data = {
        "total_requests": result.total_requests,
        "successful_requests": result.successful_requests,
        "failed_requests": result.failed_requests,
        "success_rate": result.success_rate,
        "requests_per_second": result.requests_per_second,
        "avg_response_time": result.avg_response_time,
        "response_times": result.response_times,
        "status_codes": result.status_codes,
        "connection_errors": result.connection_errors,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat()
    }
    
    with open("load_test_result.json", "w") as f:
        json.dump(result_data, f, indent=2)
    
    # 断言验收标准
    assert result.success_rate >= 0.95, f"成功率 {result.success_rate:.2%} 低于 95%"
    assert result.requests_per_second >= 100, f"QPS {result.requests_per_second:.2f} 低于 100"
    assert result.connection_errors / result.total_requests <= 0.01, f"连接错误率过高"

if __name__ == "__main__":
    # 命令行运行
    import sys
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"运行压测: {base_url}")
    result = asyncio.run(run_load_test(base_url))
    print_test_report(result)