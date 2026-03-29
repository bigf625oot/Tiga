/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import EmptyLogState from '../EmptyLogState.vue';

describe('EmptyLogState.vue', () => {
  it('renders correctly', () => {
    const wrapper = mount(EmptyLogState);
    expect(wrapper.text()).toContain('暂无日志');
    expect(wrapper.find('img').exists()).toBe(true);
    expect(wrapper.find('img').attributes('alt')).toBe('暂无日志');
    expect(wrapper.find('span').classes()).toContain('font-sans');
  });

  it('applies light mode styles by default', () => {
    const wrapper = mount(EmptyLogState, {
      props: { isDarkMode: false }
    });
    expect(wrapper.find('span').classes()).toContain('text-[#909399]');
    // Check if src is valid (data URI or file path)
    const src = wrapper.find('img').attributes('src');
    expect(src).toBeTruthy();
  });

  it('applies dark mode styles', () => {
    const wrapper = mount(EmptyLogState, {
      props: { isDarkMode: true }
    });
    expect(wrapper.find('span').classes()).toContain('text-[#C0C4CC]');
    const src = wrapper.find('img').attributes('src');
    expect(src).toBeTruthy();
  });
});
