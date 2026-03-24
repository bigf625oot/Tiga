/**
 * 测试套件: frontend/src/features/workflow/store/workflow.store.ts
 * 覆盖需求:
 *  - REQ-STORE-1: 初始化状态（tasks/logs/artifacts 均为空）
 *  - REQ-STORE-2: plan 事件 → 创建 pending 任务列表
 *  - REQ-STORE-3: task_started 事件 → 找到匹配任务改为 running
 *  - REQ-STORE-4: task_started 事件 → 未找到则动态创建
 *  - REQ-STORE-5: task_content 事件 → 追加到 task.output（实时 stream）
 *  - REQ-STORE-6: task_tool_call started → push 新 toolCall 条目 status=running
 *  - REQ-STORE-7: task_tool_call completed → 更新 toolCall status=completed + result
 *  - REQ-STORE-8: task_completed 事件 → status=completed，endTime 设置
 *  - REQ-STORE-9: task_failed 事件 → status=failed，logs 含 error
 *  - REQ-STORE-10: artifacts 事件 → artifacts.value 被更新
 *  - REQ-STORE-11: resetWorkflow → 清空 tasks/logs/artifacts
 *  - REQ-STORE-12: progress 计算正确（completed/total * 100）
 *  - REQ-STORE-13: 旧格式 plan step/status 事件向后兼容
 *  - REQ-STORE-14: runWorkflow 发起 fetch 时重置 artifacts
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useWorkflowStore } from '../workflow.store';

// ── 辅助：直接调用 handleWorkflowEvent（store 公开导出）──────────────────────
function dispatchEvent(store: ReturnType<typeof useWorkflowStore>, data: any) {
    store.handleWorkflowEvent(data);
}

// ── 基础 SSE 流模拟 ───────────────────────────────────────────────────────────
function makeMockStream(...events: any[]) {
    const chunks = events.map(e => `data: ${JSON.stringify(e)}\n\n`);
    chunks.push('data: [DONE]\n\n');
    let idx = 0;
    return new ReadableStream({
        pull(controller) {
            if (idx < chunks.length) {
                controller.enqueue(new TextEncoder().encode(chunks[idx++]));
            } else {
                controller.close();
            }
        }
    });
}

// ─────────────────────────────────────────────────────────────────────────────

describe('workflow.store — 初始化', () => {
    beforeEach(() => {
        setActivePinia(createPinia());
        vi.stubGlobal('fetch', vi.fn());
        vi.stubGlobal('localStorage', {
            getItem: vi.fn().mockReturnValue(null),
            setItem: vi.fn(),
        });
    });

    it('REQ-STORE-1: 默认状态全为空/false', () => {
        const store = useWorkflowStore();
        expect(store.tasks).toEqual([]);
        expect(store.logs).toEqual([]);
        expect(store.artifacts).toEqual([]);
        expect(store.isRunning).toBe(false);
        expect(store.progress).toBe(0);
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('workflow.store — plan 事件', () => {
    beforeEach(() => {
        setActivePinia(createPinia());
        vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
    });

    it('REQ-STORE-2: type=plan 创建 pending 任务列表', () => {
        const store = useWorkflowStore();
        dispatchEvent(store, {
            type: 'plan',
            plan: {
                id: 'p1',
                reasoning: '先搜再分析',
                tasks: [
                    { id: '1', name: '搜索数据', description: '从网络搜索', status: 'pending' },
                    { id: '2', name: '分析数据', description: '用 Python 分析', status: 'pending' },
                ]
            }
        });
        expect(store.tasks.length).toBe(2);
        expect(store.tasks[0].name).toBe('搜索数据');
        expect(store.tasks[1].name).toBe('分析数据');
        expect(store.tasks.every(t => t.status === 'pending')).toBe(true);
    });

    it('REQ-STORE-13: 旧格式 step/status plan 事件向后兼容', () => {
        const store = useWorkflowStore();
        dispatchEvent(store, {
            step: 'plan',
            status: 'success',
            plan: {
                reasoning: '兼容测试',
                steps: [
                    { step_id: 1, operation: 'execute', description: '执行步骤A' },
                ]
            }
        });
        expect(store.tasks.length).toBe(1);
        expect(store.logs.some(l => l.message.includes('兼容测试'))).toBe(true);
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('workflow.store — task lifecycle 事件', () => {
    let store: ReturnType<typeof useWorkflowStore>;

    beforeEach(() => {
        setActivePinia(createPinia());
        vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
        store = useWorkflowStore();
        // 先建立 plan
        dispatchEvent(store, {
            type: 'plan',
            plan: {
                tasks: [
                    { id: 'task-1', name: '数据清洗', status: 'pending' },
                    { id: 'task-2', name: '模型训练', status: 'pending' },
                ]
            }
        });
    });

    // REQ-STORE-3: task_started → 找到匹配的 pending 任务
    it('REQ-STORE-3: task_started 将匹配的 pending 任务改为 running', () => {
        dispatchEvent(store, {
            type: 'task_started',
            task_id: 'task-1',
            task_name: '数据清洗',
            task_description: '清洗原始数据'
        });
        const task = store.tasks.find(t => t.id === 'task-1');
        expect(task?.status).toBe('running');
        expect(task?.startTime).toBeGreaterThan(0);
    });

    // REQ-STORE-4: task_started → 未找到时动态创建
    it('REQ-STORE-4: task_started 未匹配时动态创建任务', () => {
        dispatchEvent(store, {
            type: 'task_started',
            task_id: 'task-new-99',
            task_name: '新增临时任务',
        });
        const task = store.tasks.find(t => t.id === 'task-new-99');
        expect(task).toBeDefined();
        expect(task?.status).toBe('running');
    });

    // REQ-STORE-5: task_content → 追加 output
    it('REQ-STORE-5: task_content 实时追加到 task.output', () => {
        dispatchEvent(store, { type: 'task_started', task_id: 'task-1', task_name: '数据清洗' });
        dispatchEvent(store, { type: 'task_content', task_id: 'task-1', content: '第一行' });
        dispatchEvent(store, { type: 'task_content', task_id: 'task-1', content: '第二行' });
        const task = store.tasks.find(t => t.id === 'task-1');
        expect(task?.output).toContain('第一行');
        expect(task?.output).toContain('第二行');
    });

    it('REQ-STORE-5: task_content 对未知 task_id 不崩溃', () => {
        expect(() => {
            dispatchEvent(store, { type: 'task_content', task_id: 'ghost', content: 'x' });
        }).not.toThrow();
    });

    // REQ-STORE-6: task_tool_call started
    it('REQ-STORE-6: tool_call started 推入 toolCalls 列表', () => {
        dispatchEvent(store, { type: 'task_started', task_id: 'task-1', task_name: '数据清洗' });
        dispatchEvent(store, {
            type: 'task_tool_call',
            task_id: 'task-1',
            tool: { tool_name: 'run_code', tool_args: { code: 'print(1)' }, status: 'started' }
        });
        const task = store.tasks.find(t => t.id === 'task-1');
        expect(task?.toolCalls.length).toBe(1);
        expect(task?.toolCalls[0].tool_name).toBe('run_code');
        expect(task?.toolCalls[0].status).toBe('running');
    });

    // REQ-STORE-7: task_tool_call completed
    it('REQ-STORE-7: tool_call completed 更新 status=completed + result', () => {
        dispatchEvent(store, { type: 'task_started', task_id: 'task-1', task_name: '数据清洗' });
        dispatchEvent(store, {
            type: 'task_tool_call',
            task_id: 'task-1',
            tool: { tool_name: 'run_code', status: 'started' }
        });
        dispatchEvent(store, {
            type: 'task_tool_call',
            task_id: 'task-1',
            tool: { tool_name: 'run_code', status: 'completed', result: 'output data' }
        });
        const task = store.tasks.find(t => t.id === 'task-1');
        expect(task?.toolCalls[0].status).toBe('completed');
        expect(task?.toolCalls[0].result).toBe('output data');
    });

    // REQ-STORE-8: task_completed
    it('REQ-STORE-8: task_completed 设置 status=completed 并记录 endTime', () => {
        dispatchEvent(store, { type: 'task_started', task_id: 'task-1', task_name: '数据清洗' });
        dispatchEvent(store, { type: 'task_completed', task_id: 'task-1', result_summary: '完成' });
        const task = store.tasks.find(t => t.id === 'task-1');
        expect(task?.status).toBe('completed');
        expect(task?.endTime).toBeGreaterThan(0);
        expect(task?.progress).toBe(100);
    });

    // REQ-STORE-9: task_failed
    it('REQ-STORE-9: task_failed 设置 status=failed，logs 包含错误', () => {
        dispatchEvent(store, { type: 'task_started', task_id: 'task-2', task_name: '模型训练' });
        dispatchEvent(store, {
            type: 'task_failed',
            task_id: 'task-2',
            error: '内存不足，OOM'
        });
        const task = store.tasks.find(t => t.id === 'task-2');
        expect(task?.status).toBe('failed');
        expect(task?.logs.some(l => l.includes('内存不足'))).toBe(true);
    });
});

// ───────────���─────────────────────────────────────────────────────────────────

describe('workflow.store — artifacts 事件', () => {
    let store: ReturnType<typeof useWorkflowStore>;

    beforeEach(() => {
        setActivePinia(createPinia());
        vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
        store = useWorkflowStore();
    });

    it('REQ-STORE-10: artifacts 事件更新 artifacts.value', () => {
        dispatchEvent(store, {
            type: 'artifacts',
            files: [
                { name: 'report.md', url: '/uploads/report.md', type: 'markdown', size: 1024 },
                { name: 'data.py',   url: '/uploads/data.py',   type: 'python',   size: 2048 },
            ]
        });
        expect(store.artifacts.length).toBe(2);
        expect(store.artifacts[0].name).toBe('report.md');
        expect(store.artifacts[1].type).toBe('python');
    });

    it('REQ-STORE-10: artifacts 包含 size 字段', () => {
        dispatchEvent(store, {
            type: 'artifacts',
            files: [{ name: 'f.csv', url: '/uploads/f.csv', type: 'csv', size: 512 }]
        });
        expect(store.artifacts[0].size).toBe(512);
    });

    it('REQ-STORE-10: artifacts 事件携带空数组时清空列表', () => {
        // 先设置一些 artifacts
        dispatchEvent(store, {
            type: 'artifacts',
            files: [{ name: 'old.txt', url: '/uploads/old.txt', type: 'text', size: 0 }]
        });
        dispatchEvent(store, { type: 'artifacts', files: [] });
        expect(store.artifacts.length).toBe(0);
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('workflow.store — resetWorkflow', () => {
    it('REQ-STORE-11: resetWorkflow 清空所有状态包括 artifacts', () => {
        setActivePinia(createPinia());
        vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
        const store = useWorkflowStore();

        dispatchEvent(store, {
            type: 'plan',
            plan: { tasks: [{ id: '1', name: 'T', status: 'pending' }] }
        });
        dispatchEvent(store, {
            type: 'artifacts',
            files: [{ name: 'x.py', url: '/uploads/x.py', type: 'python', size: 0 }]
        });

        store.resetWorkflow();

        expect(store.tasks).toEqual([]);
        expect(store.logs).toEqual([]);
        expect(store.artifacts).toEqual([]);
        expect(store.isRunning).toBe(false);
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('workflow.store — progress 计算', () => {
    let store: ReturnType<typeof useWorkflowStore>;

    beforeEach(() => {
        setActivePinia(createPinia());
        vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
        store = useWorkflowStore();
        dispatchEvent(store, {
            type: 'plan',
            plan: {
                tasks: [
                    { id: 't1', name: 'A', status: 'pending' },
                    { id: 't2', name: 'B', status: 'pending' },
                    { id: 't3', name: 'C', status: 'pending' },
                    { id: 't4', name: 'D', status: 'pending' },
                ]
            }
        });
    });

    it('REQ-STORE-12: 初始 0%', () => {
        expect(store.progress).toBe(0);
    });

    it('REQ-STORE-12: 完成一半 = 50%', () => {
        ['t1', 't2'].forEach(id => {
            dispatchEvent(store, { type: 'task_started',   task_id: id, task_name: id });
            dispatchEvent(store, { type: 'task_completed', task_id: id });
        });
        expect(store.progress).toBe(50);
    });

    it('REQ-STORE-12: 全部完成 = 100%', () => {
        ['t1', 't2', 't3', 't4'].forEach(id => {
            dispatchEvent(store, { type: 'task_started',   task_id: id, task_name: id });
            dispatchEvent(store, { type: 'task_completed', task_id: id });
        });
        expect(store.progress).toBe(100);
    });

    it('REQ-STORE-12: failed 任务不计入 completed', () => {
        dispatchEvent(store, { type: 'task_started',   task_id: 't1', task_name: 'A' });
        dispatchEvent(store, { type: 'task_failed',    task_id: 't1', error: 'err' });
        dispatchEvent(store, { type: 'task_started',   task_id: 't2', task_name: 'B' });
        dispatchEvent(store, { type: 'task_completed', task_id: 't2' });
        // 1 completed / 4 total = 25%
        expect(store.progress).toBe(25);
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('workflow.store — runWorkflow SSE 集成', () => {
    beforeEach(() => {
        setActivePinia(createPinia());
        vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
    });

    it('REQ-STORE-14: runWorkflow 开始时重置 artifacts', async () => {
        const store = useWorkflowStore();
        // 先手动设置 artifacts
        dispatchEvent(store, {
            type: 'artifacts',
            files: [{ name: 'stale.txt', url: '/uploads/stale.txt', type: 'text', size: 0 }]
        });
        expect(store.artifacts.length).toBe(1);

        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
            ok: true,
            body: makeMockStream()  // 空流
        }));

        await store.runWorkflow('测试消息');
        expect(store.artifacts).toEqual([]);
    });

    it('REQ-STORE-2+8: 完整 plan→task_started→task_completed 流程', async () => {
        const store = useWorkflowStore();
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
            ok: true,
            body: makeMockStream(
                {
                    type: 'plan',
                    plan: {
                        tasks: [{ id: 'x1', name: '清洗数据', status: 'pending' }]
                    }
                },
                { type: 'task_started',   task_id: 'x1', task_name: '清洗数据' },
                { type: 'task_content',   task_id: 'x1', content: '正在处理...' },
                { type: 'task_completed', task_id: 'x1', result_summary: '完成' },
                {
                    type: 'artifacts',
                    files: [{ name: 'out.csv', url: '/uploads/out.csv', type: 'csv', size: 256 }]
                }
            )
        }));

        await store.runWorkflow('清洗任务');

        const task = store.tasks.find(t => t.id === 'x1');
        expect(task?.status).toBe('completed');
        expect(task?.output).toContain('正在处理');
        expect(store.artifacts.length).toBe(1);
        expect(store.artifacts[0].name).toBe('out.csv');
    });
});
