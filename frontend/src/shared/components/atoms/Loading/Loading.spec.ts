import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import Loading from './Loading.vue';

describe('Loading.vue', () => {
  it('renders spinner by default', () => {
    const wrapper = mount(Loading);
    expect(wrapper.find('svg').exists()).toBe(true);
    expect(wrapper.text()).toContain('加载中...');
  });

  it('does not render when loading is false', () => {
    const wrapper = mount(Loading, {
      props: { loading: false }
    });
    expect(wrapper.text()).toBe('');
  });
});
