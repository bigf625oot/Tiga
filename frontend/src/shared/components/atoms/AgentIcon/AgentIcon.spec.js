import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import AgentIcon from './AgentIcon.vue';

describe('AgentIcon.vue', () => {
  const observe = vi.fn();
  const disconnect = vi.fn();

  beforeEach(() => {
    const mockConstructor = vi.fn();
    
    // Mock IntersectionObserver
    global.IntersectionObserver = class IntersectionObserver {
      constructor(callback) {
        mockConstructor(callback);
        this.callback = callback;
      }
      observe() { observe(); }
      disconnect() { disconnect(); }
      takeRecords() { return []; }
    };
    
    // Expose mock property to access calls
    global.IntersectionObserver.mock = mockConstructor.mock;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default props', () => {
    const wrapper = mount(AgentIcon);
    expect(wrapper.classes()).toContain('rounded-full');
    expect(wrapper.element.style.width).toBe('24px');
  });

  it('applies custom size', () => {
    const wrapper = mount(AgentIcon, {
      props: { size: 40 }
    });
    expect(wrapper.element.style.width).toBe('40px');
    expect(wrapper.element.style.height).toBe('40px');
  });

  it('initially shows loading state if visible', async () => {
    const wrapper = mount(AgentIcon, {
      props: { src: 'test.png' }
    });
    
    // Simulate IntersectionObserver callback
    const observerCallback = global.IntersectionObserver.mock.calls[0][0];
    observerCallback([{ isIntersecting: true }]);
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.shouldLoad).toBe(true);
    expect(wrapper.find('.animate-pulse').exists()).toBe(true);
  });

  it('renders image when loaded', async () => {
    const wrapper = mount(AgentIcon, {
      props: { src: 'test.png' }
    });
    
    // Trigger visible
    const observerCallback = global.IntersectionObserver.mock.calls[0][0];
    observerCallback([{ isIntersecting: true }]);
    await wrapper.vm.$nextTick();

    // Trigger load
    const img = wrapper.find('img');
    await img.trigger('load');
    
    expect(wrapper.vm.isLoading).toBe(false);
    expect(wrapper.find('.animate-pulse').exists()).toBe(false);
  });

  it('retries on error', async () => {
    vi.useFakeTimers();
    const wrapper = mount(AgentIcon, {
      props: { src: 'error.png' }
    });
    
    // Trigger visible
    const observerCallback = global.IntersectionObserver.mock.calls[0][0];
    observerCallback([{ isIntersecting: true }]);
    await wrapper.vm.$nextTick();

    const img = wrapper.find('img');
    
    // First Error
    await img.trigger('error');
    expect(wrapper.vm.retryCount).toBe(1);
    
    // Fast forward timer
    vi.advanceTimersByTime(1000);
    await wrapper.vm.$nextTick();
    
    // Check if src changed (retry param added)
    expect(wrapper.vm.displaySrc).toContain('retry=');
    
    vi.useRealTimers();
  });

  it('shows fallback after max retries', async () => {
    vi.useFakeTimers();
    const wrapper = mount(AgentIcon, {
      props: { src: 'error.png' }
    });
    
    // Trigger visible
    const observerCallback = global.IntersectionObserver.mock.calls[0][0];
    observerCallback([{ isIntersecting: true }]);
    await wrapper.vm.$nextTick();

    const img = wrapper.find('img');
    
    // Fail 3 times
    for (let i = 0; i < 3; i++) {
        await img.trigger('error');
        vi.advanceTimersByTime(1000);
        await wrapper.vm.$nextTick();
    }
    
    // Final error triggers fallback
    await img.trigger('error');
    
    expect(wrapper.vm.isError).toBe(true);
    expect(wrapper.find('svg').exists()).toBe(true); // Fallback svg
    
    vi.useRealTimers();
  });
});
