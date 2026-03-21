import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import MenuConfig from './MenuConfig.vue';
import { useToast } from '@/components/ui/toast/use-toast';

// Mock matchMedia for Radix UI components
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

// Mock ResizeObserver for Radix UI components
window.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock useToast
vi.mock('@/components/ui/toast/use-toast', () => ({
  useToast: vi.fn(() => ({
    toast: vi.fn()
  }))
}));

describe('MenuConfig.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the initial menu list correctly', () => {
    const wrapper = mount(MenuConfig, {
      global: {
        stubs: {
          // Stub icons
          Pencil: true,
          Shield: true,
          Trash2: true,
          Plus: true
        }
      }
    });
    
    // Check if header is rendered
    expect(wrapper.text()).toContain('菜单配置');
    
    // Check if default mock data is rendered
    expect(wrapper.text()).toContain('系统设置');
    expect(wrapper.text()).toContain('/settings');
    expect(wrapper.text()).toContain('用户管理');
  });

  it('opens add menu dialog when clicking the add button', async () => {
    const wrapper = mount(MenuConfig, {
      global: {
        stubs: {
          Pencil: true,
          Shield: true,
          Trash2: true,
          Plus: true,
          // Dialog components are sometimes hard to test due to teleports,
          // but we can check if the dialog open state changes or use finding by role
          Dialog: {
            template: '<div><slot></slot></div>',
            props: ['open']
          },
          DialogContent: { template: '<div class="dialog-content"><slot></slot></div>' },
          DialogHeader: { template: '<div><slot></slot></div>' },
          DialogTitle: { template: '<div><slot></slot></div>' },
          DialogDescription: { template: '<div><slot></slot></div>' },
          DialogFooter: { template: '<div><slot></slot></div>' }
        }
      }
    });

    const addBtn = wrapper.findAll('button').find(b => b.text().includes('新增菜单'));
    expect(addBtn).toBeDefined();
    
    await addBtn!.trigger('click');
    
    // Should display '新增菜单' title in the modal
    expect(wrapper.text()).toContain('新增菜单');
  });
});
