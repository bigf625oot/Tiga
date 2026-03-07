import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import KnowledgeGraphSidebar from '../KnowledgeGraphSidebar.vue';
import { nextTick } from 'vue';

describe('KnowledgeGraphSidebar.vue', () => {
    const defaultProps = {
        searchQuery: '',
        selectedTypes: ['A', 'B'],
        allTypes: ['A', 'B', 'C'],
        colorMap: { A: 'red', B: 'blue', C: 'green' },
        typeCounts: { A: 10, B: 20, C: 30 },
        stats: {
            totalNodes: 100,
            totalEdges: 50,
            visibleNodes: 100,
            visibleEdges: 50
        },
        timeRange: [1000, 2000] as [number, number],
        timeBounds: { min: 1000, max: 2000 }
    };

    const stubs = {
        'a-input-search': {
            template: '<input :value="value" @input="handleInput" @change="handleChange" @keyup.enter="$emit(\'search\')" />',
            props: ['value'],
            setup(props: any, { emit }: any) {
                const handleInput = (e: any) => {
                    const val = e.target.value;
                    emit('update:value', val);
                    emit('input', e);
                };
                const handleChange = (e: any) => {
                    emit('change', e);
                };
                return { handleInput, handleChange };
            }
        },
        'a-checkbox-group': {
            template: '<div><slot></slot></div>',
            props: ['value']
        },
        'a-checkbox': {
            template: '<div class="ant-checkbox-wrapper" @click="handleClick"><slot></slot></div>',
            props: ['value'],
            methods: {
                handleClick() {
                    // Logic to simulate group update would be complex here without real component
                    // Just emit click/change event on wrapper?
                    // But the test checks "update:selectedTypes".
                    // The parent component handles "change" from group.
                    // We need to trigger "change" on group.
                }
            }
        },
        'a-slider': {
            name: 'ASlider',
            template: '<div class="ant-slider" @change="handleChange"></div>',
            props: ['value', 'min', 'max', 'range'],
            setup(props: any, { emit }: any) {
                const handleChange = (e: any) => {
                    emit('update:value', e);
                    emit('change', e);
                };
                return { handleChange };
            }
        }
    };

    it('renders stats correctly', () => {
        const wrapper = mount(KnowledgeGraphSidebar, { props: defaultProps, global: { stubs } });
        expect(wrapper.text()).toContain('100 / 100');
        expect(wrapper.text()).toContain('50 / 50');
    });

    it('renders entity type counts', () => {
        const wrapper = mount(KnowledgeGraphSidebar, { props: defaultProps, global: { stubs } });
        expect(wrapper.text()).toContain('10');
        expect(wrapper.text()).toContain('20');
        expect(wrapper.text()).toContain('30');
    });

    it('emits update:searchQuery when input changes', async () => {
        const wrapper = mount(KnowledgeGraphSidebar, { props: defaultProps, global: { stubs } });
        const input = wrapper.find('input');
        await input.setValue('test');
        expect(wrapper.emitted('update:searchQuery')?.[0]).toEqual(['test']);
    });

    it('emits update:selectedTypes when checkboxes change', async () => {
        const wrapper = mount(KnowledgeGraphSidebar, { props: defaultProps, global: { stubs } });
        
        // Simulate select all
        const selectAllBtn = wrapper.findAll('button').find(b => b.text() === '全选');
        await selectAllBtn?.trigger('click');
        expect(wrapper.emitted('update:selectedTypes')?.[0]).toEqual([['A', 'B', 'C']]);
        
        // Reset local state to match props for next step (since props didn't update)
        // Or just update the prop manually to simulate parent response
        await wrapper.setProps({ selectedTypes: ['A', 'B', 'C'] });

        // Simulate inverse
        const invertBtn = wrapper.findAll('button').find(b => b.text() === '反选');
        await invertBtn?.trigger('click');
        // Initial selected: A, B, C. All: A, B, C. Inverse -> [].
        // Wait, defaultProps selectedTypes is ['A', 'B'].
        // If I setProps to ['A', 'B', 'C'], then invert gives [].
        // If I want to test inverse functionality properly:
        
        await wrapper.setProps({ selectedTypes: ['A', 'B'] });
        await invertBtn?.trigger('click');
        // All: A, B, C. Selected: A, B. Inverse -> C.
        
        // Check the LAST emit
        const emits = wrapper.emitted('update:selectedTypes');
        expect(emits?.[emits.length - 1]).toEqual([['C']]);
    });

    it('emits update:timeRange when slider changes', async () => {
        const wrapper = mount(KnowledgeGraphSidebar, { props: defaultProps, global: { stubs } });
        const slider = wrapper.findComponent({ name: 'ASlider' });
        // Simulate v-model update from child
        await slider.vm.$emit('update:value', [1200, 1800]);
        // Simulate change event
        await slider.vm.$emit('change', [1200, 1800]);
        expect(wrapper.emitted('update:timeRange')?.[0]).toEqual([[1200, 1800]]);
    });
});
