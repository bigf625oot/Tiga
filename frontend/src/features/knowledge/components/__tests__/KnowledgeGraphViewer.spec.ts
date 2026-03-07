import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import KnowledgeGraphViewer from '../KnowledgeGraphViewer.vue';
import { nextTick } from 'vue';

// Mock dependencies
vi.mock('ant-design-vue', () => {
    return {
        message: { 
            warning: vi.fn(), 
            success: vi.fn(), 
            info: vi.fn(), 
            error: vi.fn() 
        }
    };
});

// Mock GraphViewer component
vi.mock('@/shared/components/organisms/GraphViewer', () => ({
    GraphViewer: {
        name: 'GraphViewer',
        template: '<div class="graph-viewer-stub"><slot name="toolbar-extras"></slot></div>',
        methods: {
            focusNode: vi.fn()
        }
    }
}));

// Mock Sidebar
vi.mock('../KnowledgeGraphSidebar.vue', () => ({
    default: {
        name: 'KnowledgeGraphSidebar',
        template: '<div class="sidebar-stub"></div>',
        props: ['searchQuery', 'selectedTypes', 'timeRange'],
        emits: ['update:searchQuery', 'update:selectedTypes', 'update:timeRange']
    }
}));

// Mock Axios
vi.mock('axios', () => ({
    default: {
        create: () => ({
            get: vi.fn().mockImplementation(() => new Promise(resolve => {
                setTimeout(() => {
                    resolve({ 
                        data: { 
                            nodes: { 
                                'n1': { name: 'Node 1', type: '人', timestamp: 1000 },
                                'n2': { name: 'Node 2', type: '组织', timestamp: 2000 }
                            },
                            edges: {
                                'e1': { source: 'n1', target: 'n2' }
                            },
                            reason: ''
                        } 
                    });
                }, 10);
            }))
        })
    }
}));

describe('KnowledgeGraphViewer.vue', () => {
    let wrapper: any;

    beforeEach(() => {
        wrapper = mount(KnowledgeGraphViewer, {
            props: {
                docId: 1,
                initialScope: 'doc',
                showChat: false
            }
        });
    });

    it('loads data and calculates stats', async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        await nextTick();
        
        expect(wrapper.vm.stats.totalNodes).toBe(2);
        expect(wrapper.vm.stats.totalEdges).toBe(1);
        expect(wrapper.vm.timeBounds.min).toBe(1000);
        expect(wrapper.vm.timeBounds.max).toBe(2000);
    });

    it('calculates type counts correctly', async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        await nextTick();
        
        expect(wrapper.vm.typeCounts['人']).toBe(1);
        expect(wrapper.vm.typeCounts['组织']).toBe(1);
    });

    it('filters nodes by search query', async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        await nextTick();

        // Initial state
        expect(Object.keys(wrapper.vm.filteredNodes).length).toBe(2);

        // Search for "Node 1"
        wrapper.vm.searchQuery = 'Node 1';
        await nextTick();
        
        // Should only have Node 1
        expect(Object.keys(wrapper.vm.filteredNodes).length).toBe(1);
        expect(Object.keys(wrapper.vm.filteredNodes)).toContain('n1');
        expect(Object.keys(wrapper.vm.filteredNodes)).not.toContain('n2');
        expect(wrapper.vm.filteredNodes['n1'].color).toBe('#ff0055');
    });

    it('filters nodes by type', async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        await nextTick();

        // Deselect 'n1' (Node 1)
        // In default data: n1 has 'type: person' -> '人'
        // n2 has 'type: org' -> '组织'
        
        // So allTypes should be ['人', '组织'].
        // selectedTypes should be ['人', '组织'].
        
        // Set selectedTypes to just ['组织']
        wrapper.vm.selectedTypes = ['组织'];
        
        await nextTick();
        
        expect(Object.keys(wrapper.vm.filteredNodes)).toContain('n2');
        expect(Object.keys(wrapper.vm.filteredNodes)).not.toContain('n1');
    });

    it('filters nodes by time range', async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        await nextTick();

        // Range 1500-2500 (Exclude Node 1 at 1000)
        wrapper.vm.timeRange = [1500, 2500];
        await nextTick();
        
        expect(Object.keys(wrapper.vm.filteredNodes)).toContain('n2'); // 2000
        expect(Object.keys(wrapper.vm.filteredNodes)).not.toContain('n1'); // 1000
    });
});
