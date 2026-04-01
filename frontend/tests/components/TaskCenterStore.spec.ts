import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useTaskStore } from '../../src/store/useTaskStore';

// Mock globals
global.fetch = vi.fn();
class MockWebSocket {
  url: string;
  readyState: number = 0;
  onmessage: ((e: any) => void) | null = null;
  onopen: (() => void) | null = null;
  constructor(url: string) {
    this.url = url;
    setTimeout(() => { this.readyState = 1; if(this.onopen) this.onopen(); }, 10);
  }
  close() {}
}
global.WebSocket = MockWebSocket as any;

describe('TaskStore Full Flow', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('creates task, receives ws updates, and counts processing', async () => {
    const store = useTaskStore();
    
    // 1. Mock create task API response
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ task_id: 'task-123' })
    });

    // 2. Create task
    const taskId = await store.createTask({ name: 'Test Task', task_type: 'CELERY' });
    expect(taskId).toBe('task-123');
    expect(store.tasks.length).toBe(1);
    expect(store.tasks[0].status).toBe('pending');
    expect(store.processingCount).toBe(0);

    // 3. Connect WS
    store.connectWebSocket('user-1');
    
    // Simulate WS open delay
    await new Promise(r => setTimeout(r, 20));
    
    // 4. Simulate WS message (Task Running)
    const wsInstance = store.ws as unknown as MockWebSocket;
    wsInstance.onmessage!({
      data: JSON.stringify({
        task_id: 'task-123',
        type: 'progress',
        data: { percent: 50, status: 'RUNNING', msg: 'Processing...', step: 'step_1' }
      })
    });

    // Verify store updated
    expect(store.tasks[0].progress).toBe(50);
    expect(store.tasks[0].status).toBe('processing'); // mapped from RUNNING
    expect(store.processingCount).toBe(1);

    // 5. Simulate WS message (Task Success)
    wsInstance.onmessage!({
      data: JSON.stringify({
        task_id: 'task-123',
        type: 'progress',
        data: { percent: 100, status: 'SUCCESS', msg: 'Done', step: 'completed' }
      })
    });

    expect(store.tasks[0].status).toBe('success');
    expect(store.processingCount).toBe(0);
  });

  it('creates a new task from ws progress message when task does not exist', () => {
    const store = useTaskStore();

    store.handleWebSocketMessage({
      task_id: 't-1',
      type: 'progress',
      data: { name: 'From WS', percent: 10, status: 'RUNNING', msg: 'Working', step: 's1' }
    });

    expect(store.tasks.length).toBe(1);
    expect(store.tasks[0].id).toBe('t-1');
    expect(store.tasks[0].name).toBe('From WS');
    expect(store.tasks[0].progress).toBe(10);
    expect(store.tasks[0].status).toBe('processing');

    store.handleWebSocketMessage({
      task_id: 't-1',
      type: 'progress',
      data: { percent: 100, status: 'SUCCESS', msg: 'Done', step: 'completed' }
    });

    expect(store.tasks[0].progress).toBe(100);
    expect(store.tasks[0].status).toBe('success');
    expect(store.processingCount).toBe(0);
  });

  it('falls back to deleting tasks one by one when batch clear completed fails', async () => {
    const store = useTaskStore();
    store.wsUserId = 'user-1';
    store.tasks = [
      { id: 'a', name: 'A', status: 'success', progress: 100, createdAt: Date.now() },
      { id: 'b', name: 'B', status: 'error', progress: 100, createdAt: Date.now() },
      { id: 'c', name: 'C', status: 'processing', progress: 50, createdAt: Date.now() }
    ] as any;

    (global.fetch as any).mockResolvedValueOnce({ ok: false, status: 500 });

    const removeSpy = vi.spyOn(store, 'removeTask').mockImplementation(async (id: string) => {
      store.tasks = store.tasks.filter(t => t.id !== id) as any;
    });

    await store.clearCompletedTasks();

    expect(removeSpy).toHaveBeenCalledTimes(2);
    expect(removeSpy).toHaveBeenCalledWith('a');
    expect(removeSpy).toHaveBeenCalledWith('b');
    expect(store.tasks.map(t => t.id)).toEqual(['c']);
  });
});
