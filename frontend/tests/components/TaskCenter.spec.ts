import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import TaskCenter from '../../src/components/TaskCenter.vue';
import { useTaskStore } from '../../src/store/useTaskStore';

function createDeferred<T = void>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: any) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

// Mock fetch globally
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ items: [] }),
});

// Mock WebSocket globally
class MockWebSocket {
  url: string;
  readyState: number;
  onopen: (() => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: any) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.readyState = 0; // CONNECTING
    // Simulate connection success after a short delay
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) this.onopen();
    }, 10);
  }

  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  }
}
global.WebSocket = MockWebSocket as any;

// Mock matchMedia for Radix UI (used by Shadcn)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe('TaskCenter Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('renders correctly', () => {
    const wrapper = mount(TaskCenter, {
      global: {
        stubs: {
          Sheet: true,
          SheetTrigger: true,
          SheetContent: true,
          SheetHeader: true,
          SheetTitle: true,
          SheetDescription: true,
          TooltipProvider: true,
          Tooltip: true,
          TooltipTrigger: true,
          TooltipContent: true,
          Button: true,
          Badge: true,
          ScrollArea: true,
          Progress: true,
          ListTodo: true,
          RefreshCw: true,
          Trash2: true,
          Loader2: true,
          CheckCircle2: true,
          AlertCircle: true,
          Clock: true,
          X: true
        }
      }
    });

    expect(wrapper.exists()).toBe(true);
  });

  it('displays processing count when tasks are processing', async () => {
    const store = useTaskStore();
    store.tasks = [
      { id: '1', name: 'Task 1', status: 'processing', progress: 50, createdAt: Date.now() },
      { id: '2', name: 'Task 2', status: 'pending', progress: 0, createdAt: Date.now() }
    ];

    const wrapper = mount(TaskCenter, {
      global: {
        stubs: {
          Sheet: { template: '<div><slot /></div>' },
          SheetTrigger: { template: '<div><slot /></div>' },
          SheetContent: { template: '<div><slot /></div>' },
          SheetHeader: true,
          SheetTitle: true,
          SheetDescription: true,
          TooltipProvider: { template: '<div><slot /></div>' },
          Tooltip: { template: '<div><slot /></div>' },
          TooltipTrigger: { template: '<div><slot /></div>' },
          TooltipContent: true,
          Button: { emits: ['click'], template: '<button :class="$attrs.class" :size="$attrs.size" :variant="$attrs.variant" @click="$emit(\'click\', $event)"><slot /></button>' },
          Badge: true,
          ScrollArea: true,
          Progress: true,
          ListTodo: true,
          RefreshCw: true,
          Trash2: true,
          Loader2: true,
          CheckCircle2: true,
          AlertCircle: true,
          Clock: true,
          X: true
        }
      }
    });

    // Check if processing count (1) is displayed
    expect(wrapper.text()).toContain('1');
  });

  it('initializes by fetching tasks and connecting ws, and disconnects on unmount', async () => {
    const store = useTaskStore() as any;
    store.fetchTasks = vi.fn().mockResolvedValue(undefined);
    store.connectWebSocket = vi.fn();
    store.disconnect = vi.fn();

    const wrapper = mount(TaskCenter, {
      global: {
        stubs: {
          Sheet: { template: '<div><slot /></div>' },
          SheetTrigger: { template: '<div><slot /></div>' },
          SheetContent: { template: '<div><slot /></div>' },
          SheetHeader: true,
          SheetTitle: true,
          SheetDescription: true,
          TooltipProvider: { template: '<div><slot /></div>' },
          Tooltip: { template: '<div><slot /></div>' },
          TooltipTrigger: { template: '<div><slot /></div>' },
          TooltipContent: true,
          Button: { emits: ['click'], template: '<button :class="$attrs.class" :size="$attrs.size" :variant="$attrs.variant" @click="$emit(\'click\', $event)"><slot /></button>' },
          Badge: true,
          ScrollArea: { template: '<div><slot /></div>' },
          Progress: true,
          ListTodo: true,
          RefreshCw: true,
          Trash2: true,
          Loader2: true,
          CheckCircle2: true,
          AlertCircle: true,
          Clock: true,
          X: true
        }
      }
    });

    await new Promise(r => setTimeout(r, 0));

    expect(store.fetchTasks).toHaveBeenCalledWith('anonymous');
    expect(store.connectWebSocket).toHaveBeenCalledWith('anonymous');

    wrapper.unmount();
    expect(store.disconnect).toHaveBeenCalled();
  });

  it('refresh button toggles spinner while fetching', async () => {
    const store = useTaskStore() as any;
    store.connectWebSocket = vi.fn();
    store.fetchTasks = vi.fn().mockResolvedValue(undefined);

    const wrapper = mount(TaskCenter, {
      global: {
        stubs: {
          Sheet: { template: '<div><slot /></div>' },
          SheetTrigger: { template: '<div><slot /></div>' },
          SheetContent: { template: '<div><slot /></div>' },
          SheetHeader: { template: '<div><slot /></div>' },
          SheetTitle: { template: '<div><slot /></div>' },
          SheetDescription: true,
          TooltipProvider: { template: '<div><slot /></div>' },
          Tooltip: { template: '<div><slot /></div>' },
          TooltipTrigger: { template: '<div><slot /></div>' },
          TooltipContent: true,
          Button: { emits: ['click'], template: '<button :class="$attrs.class" :size="$attrs.size" :variant="$attrs.variant" @click="$emit(\'click\', $event)"><slot /></button>' },
          Badge: true,
          ScrollArea: { template: '<div><slot /></div>' },
          Progress: true,
          ListTodo: true,
          RefreshCw: true,
          Trash2: true,
          Loader2: true,
          CheckCircle2: true,
          AlertCircle: true,
          Clock: true,
          X: true
        }
      }
    });

    await new Promise(r => setTimeout(r, 20));
    store.fetchTasks.mockClear();
    const d = createDeferred<void>();
    store.fetchTasks.mockImplementation(() => d.promise);

    const refreshBtn = wrapper.findAll('button').find(b => b.attributes('size') === 'sm');
    expect(refreshBtn).toBeTruthy();
    await refreshBtn!.trigger('click');
    await new Promise(r => setTimeout(r, 0));

    expect(store.fetchTasks).toHaveBeenCalledTimes(1);
    expect(wrapper.find('.animate-spin').exists()).toBe(true);

    d.resolve();
    await new Promise(r => setTimeout(r, 0));
    expect(wrapper.find('.animate-spin').exists()).toBe(false);
  });

  it('calls store actions when removing a task and clearing completed tasks', async () => {
    const store = useTaskStore() as any;
    store.tasks = [
      { id: 't-1', name: 'Task 1', status: 'pending', progress: 0, createdAt: Date.now() }
    ] as any;

    store.fetchTasks = vi.fn().mockResolvedValue(undefined);
    store.connectWebSocket = vi.fn();
    store.removeTask = vi.fn().mockResolvedValue(undefined);
    store.clearCompletedTasks = vi.fn().mockResolvedValue(undefined);

    const wrapper = mount(TaskCenter, {
      global: {
        stubs: {
          Sheet: { template: '<div><slot /></div>' },
          SheetTrigger: { template: '<div><slot /></div>' },
          SheetContent: { template: '<div><slot /></div>' },
          SheetHeader: true,
          SheetTitle: { template: '<div><slot /></div>' },
          SheetDescription: true,
          TooltipProvider: { template: '<div><slot /></div>' },
          Tooltip: { template: '<div><slot /></div>' },
          TooltipTrigger: { template: '<div><slot /></div>' },
          TooltipContent: true,
          Button: { emits: ['click'], template: '<button :class="$attrs.class" :size="$attrs.size" :variant="$attrs.variant" @click="$emit(\'click\', $event)"><slot /></button>' },
          Badge: true,
          ScrollArea: { template: '<div><slot /></div>' },
          Progress: true,
          ListTodo: true,
          RefreshCw: true,
          Trash2: true,
          Loader2: true,
          CheckCircle2: true,
          AlertCircle: true,
          Clock: true,
          X: true
        }
      }
    });

    await new Promise(r => setTimeout(r, 0));

    const removeBtn = wrapper.findAll('button').find(b => (b.attributes('class') || '').includes('h-6') && (b.attributes('class') || '').includes('w-6'));
    expect(removeBtn).toBeTruthy();
    await removeBtn!.trigger('click');
    expect(store.removeTask).toHaveBeenCalledWith('t-1');

    const clearBtn = wrapper.findAll('button').find(b => b.text().includes('清除已完成任务'));
    expect(clearBtn).toBeTruthy();
    await clearBtn!.trigger('click');
    expect(store.clearCompletedTasks).toHaveBeenCalled();
  });
});
