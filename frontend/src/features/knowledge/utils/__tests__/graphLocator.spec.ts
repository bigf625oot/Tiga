import { VNetworkGraphLocator } from '../graphLocator';
import { ref } from 'vue';
import { describe, it, expect, vi } from 'vitest';

describe('graphLocator', () => {
    it('manages highlighted nodes queue', async () => {
        const mockGraph = { 
            transitionWhile: vi.fn((cb) => cb()), 
            setView: vi.fn() 
        };
        // Fix: Create a ref that holds the mockGraph directly
        const engine = ref(mockGraph);
        const nodes = ref<any>({ 'n1': {}, 'n2': {}, 'n3': {}, 'n4': {} });
        const layouts = ref<any>({ nodes: { 'n1': {x:0,y:0}, 'n2': {x:0,y:0}, 'n3': {x:0,y:0}, 'n4': {x:0,y:0} } });
        
        const locator = new VNetworkGraphLocator(engine, { nodes, layouts });

        await locator.locateNode('n1');
        // Access private property by casting to any
        expect((locator as any).highlightedNodes.value.has('n1')).toBe(true);
        expect((locator as any).highlightedNodes.value.size).toBe(1);

        await locator.locateNode('n2');
        await locator.locateNode('n3');
        expect((locator as any).highlightedNodes.value.size).toBe(3);

        await locator.locateNode('n4');
        expect((locator as any).highlightedNodes.value.size).toBe(3);
        expect((locator as any).highlightedNodes.value.has('n1')).toBe(false); // Should be removed (FIFO)
        expect((locator as any).highlightedNodes.value.has('n4')).toBe(true);
        
        expect(mockGraph.setView).toHaveBeenCalled();
    });
});
