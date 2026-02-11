
import { mount } from '@vue/test-utils';
import SourcePanel from '../SourcePanel.vue';

describe('SourcePanel.vue', () => {
  it('renders doc mode correctly', () => {
    const sources = [
      { docId: 1, title: 'Test Doc', summary: 'Summary', score: 0.9, updateTime: '2023-01-01' }
    ];
    const wrapper = mount(SourcePanel, {
      props: { sources }
    });
    expect(wrapper.text()).toContain('文档来源');
    expect(wrapper.text()).toContain('Test Doc');
    expect(wrapper.find('.doc-card').exists()).toBe(true);
  });

  it('renders chunk mode correctly', () => {
    const sources = [
      { chunkId: 1, docId: 1, nodeId: 'n1', text: 'Chunk Text', score: 0.8, pageNo: 5 }
    ];
    const wrapper = mount(SourcePanel, {
      props: { sources }
    });
    expect(wrapper.text()).toContain('图谱/文档片段');
    expect(wrapper.text()).toContain('Chunk Text');
    expect(wrapper.find('.chunk-card').exists()).toBe(true);
  });

  it('emits locate-node event on chunk click', async () => {
    const sources = [
      { chunkId: 1, docId: 1, nodeId: 'n1', text: 'Chunk Text', score: 0.8 }
    ];
    const wrapper = mount(SourcePanel, {
      props: { sources }
    });
    await wrapper.find('.chunk-card').trigger('click');
    expect(wrapper.emitted('locate-node')).toBeTruthy();
    expect(wrapper.emitted('locate-node')[0][0]).toEqual(sources[0]);
  });
});
