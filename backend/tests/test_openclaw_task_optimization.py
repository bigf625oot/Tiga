import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.models.openclaw_task import OpenClawTask
from app.crud.crud_openclaw_task import OpenClawTaskCRUD
from app.services.openclaw.task.worker.task_worker_service import OpenClawTaskWorker, task_worker

@pytest.fixture
async def task_worker_instance():
    """提供任务工作器实例"""
    worker = OpenClawTaskWorker()
    await worker.start()
    yield worker
    await worker.stop()

@pytest.mark.asyncio
async def test_create_task_success(db: AsyncSession):
    """测试成功创建任务"""
    prompt = "每天9点抓取百度首页"
    parsed_command = {"name": "抓取百度", "schedule": "0 9 * * *", "command": "crawl https://baidu.com"}
    
    task, created = await OpenClawTaskCRUD.create_task(
        db,
        original_prompt=prompt,
        parsed_command=parsed_command,
        schedule=datetime.utcnow(),
        target_node_id="node_123"
    )
    
    assert created is True
    assert task.task_id is not None
    assert task.status == "PENDING"
    assert task.original_prompt == prompt
    assert task.parsed_command == parsed_command
    assert task.target_node_id == "node_123"

@pytest.mark.asyncio
async def test_create_task_idempotent(db: AsyncSession):
    """测试幂等性创建"""
    prompt = "每天9点抓取百度首页"
    parsed_command = {"name": "抓取百度", "schedule": "0 9 * * *", "command": "crawl https://baidu.com"}
    schedule = datetime.utcnow()
    target_node_id = "node_123"
    
    # 第一次创建
    task1, created1 = await OpenClawTaskCRUD.create_task(
        db,
        original_prompt=prompt,
        parsed_command=parsed_command,
        schedule=schedule,
        target_node_id=target_node_id
    )
    
    assert created1 is True
    task1_id = task1.task_id
    
    # 第二次创建（应该返回已存在的任务）
    task2, created2 = await OpenClawTaskCRUD.create_task(
        db,
        original_prompt=prompt,
        parsed_command=parsed_command,
        schedule=schedule,
        target_node_id=target_node_id
    )
    
    assert created2 is False
    assert task2.task_id == task1_id

@pytest.mark.asyncio
async def test_update_task_status_with_optimistic_lock(db: AsyncSession):
    """测试乐观锁更新"""
    # 创建任务
    task, _ = await OpenClawTaskCRUD.create_task(
        db,
        original_prompt="测试任务",
        parsed_command={"command": "test"}
    )
    
    # 成功更新
    success = await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
        db,
        task.task_id,
        "PENDING",
        "DISPATCHED"
    )
    
    assert success is True
    
    # 验证状态已更新
    updated_task = await OpenClawTaskCRUD.get_task_by_id(db, task.task_id)
    assert updated_task.status == "DISPATCHED"
    
    # 尝试用旧的预期状态更新（应该失败）
    success2 = await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
        db,
        task.task_id,
        "PENDING",  # 错误的旧状态
        "FAILED"
    )
    
    assert success2 is False

@pytest.mark.asyncio
async def test_task_worker_dispatch_success(db: AsyncSession):
    """测试任务工作器成功分发"""
    # 创建任务
    task, _ = await OpenClawTaskCRUD.create_task(
        db,
        original_prompt="测试任务",
        parsed_command={"command": "test"}
    )
    
    # 模拟成功的网关调用
    async def mock_gateway_call():
        return {"status": "success"}
    
    # 启动工作器并分发任务
    await task_worker.start()
    
    try:
        await task_worker.dispatch_task(
            task_id=task.task_id,
            gateway_call_func=mock_gateway_call,
            db_session_factory=lambda: db
        )
        
        # 等待工作器处理
        await asyncio.sleep(0.5)
        
        # 验证状态已更新
        updated_task = await OpenClawTaskCRUD.get_task_by_id(db, task.task_id)
        assert updated_task.status == "DISPATCHED"
        
    finally:
        await task_worker.stop()

@pytest.mark.asyncio
async def test_task_worker_dispatch_failure(db: AsyncSession):
    """测试任务工作器处理失败"""
    # 创建任务
    task, _ = await OpenClawTaskCRUD.create_task(
        db,
        original_prompt="测试任务",
        parsed_command={"command": "test"}
    )
    
    # 模拟失败的网关调用
    async def mock_gateway_call():
        raise Exception("Gateway connection failed")
    
    # 启动工作器并分发任务
    await task_worker.start()
    
    try:
        await task_worker.dispatch_task(
            task_id=task.task_id,
            gateway_call_func=mock_gateway_call,
            db_session_factory=lambda: db
        )
        
        # 等待工作器处理
        await asyncio.sleep(0.5)
        
        # 验证状态已更新为失败
        updated_task = await OpenClawTaskCRUD.get_task_by_id(db, task.task_id)
        assert updated_task.status == "FAILED"
        assert updated_task.error_log is not None
        assert "Gateway connection failed" in updated_task.error_log
        
    finally:
        await task_worker.stop()

@pytest.mark.asyncio
async def test_get_tasks_by_status(db: AsyncSession):
    """测试按状态查询任务"""
    # 先清空所有任务，确保测试环境纯净
    from sqlalchemy import delete
    from app.models.openclaw_task import OpenClawTask
    await db.execute(delete(OpenClawTask))
    await db.commit()

    # 创建不同状态的任务
    for i in range(3):
        await OpenClawTaskCRUD.create_task(
            db,
            original_prompt=f"任务{i}",
            parsed_command={"command": f"test{i}"}
        )
    
    # 获取所有待处理任务
    pending_tasks = await OpenClawTaskCRUD.get_tasks_by_status(db, "PENDING")
    assert len(pending_tasks) == 3
    
    # 更新一个任务状态
    task = pending_tasks[0]
    await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
        db,
        task.task_id,
        "PENDING",
        "DISPATCHED"
    )
    
    # 重新查询
    pending_tasks = await OpenClawTaskCRUD.get_tasks_by_status(db, "PENDING")
    assert len(pending_tasks) == 2
    
    dispatched_tasks = await OpenClawTaskCRUD.get_tasks_by_status(db, "DISPATCHED")
    assert len(dispatched_tasks) == 1