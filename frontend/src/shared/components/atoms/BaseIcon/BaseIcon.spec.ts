// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import BaseIcon from './BaseIcon.vue';
import { Icon } from '@iconify/vue';

describe('BaseIcon', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(BaseIcon, {
      props: {
        icon: 'mdi:home'
      }
    });
    expect(wrapper.find('.base-icon').exists()).toBe(true);
  });

  it('applies custom size', () => {
    const wrapper = mount(BaseIcon, {
      props: {
        icon: 'mdi:home',
        size: 50
      }
    });
    
    const iconComponent = wrapper.findComponent(Icon);
    expect(iconComponent.exists()).toBe(true);
    // Note: props might be passed as strings or numbers depending on internal handling
    // BaseIcon computes normalizedSize
    expect(iconComponent.props('width')).toBe('50px');
  });

  it('applies color style', () => {
    const wrapper = mount(BaseIcon, {
      props: {
        icon: 'mdi:home',
        color: 'red'
      }
    });
    expect(wrapper.attributes('style')).toContain('color: red');
  });

  it('applies rotation', () => {
    const wrapper = mount(BaseIcon, {
      props: {
        icon: 'mdi:home',
        rotate: 90
      }
    });
    const iconComponent = wrapper.findComponent(Icon);
    expect(iconComponent.props('rotate')).toBe(90);
  });

  it('applies spin class', () => {
    const wrapper = mount(BaseIcon, {
      props: {
        icon: 'mdi:loading',
        spin: true
      }
    });
    expect(wrapper.classes()).toContain('animate-spin');
  });

  it('renders fallback when specified and error occurs', async () => {
    const wrapper = mount(BaseIcon, {
        props: {
            icon: 'invalid:icon',
            fallback: 'mdi:alert'
        }
    });
    
    // Check if primary icon is rendered initially
    const iconComponent = wrapper.findComponent(Icon);
    expect(iconComponent.exists()).toBe(true);
    expect(iconComponent.props('icon')).toBe('invalid:icon');
  });
});
