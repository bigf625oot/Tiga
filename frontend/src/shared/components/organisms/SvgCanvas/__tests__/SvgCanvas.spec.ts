import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import SvgCanvas from '../SvgCanvas.vue';

describe('SvgCanvas.vue', () => {
    // Mock getBoundingClientRect
    // This is needed for drag calculations
    const mockRect = {
        left: 0,
        top: 0,
        width: 1200,
        height: 800,
        x: 0,
        y: 0,
        bottom: 800,
        right: 1200,
        toJSON: () => {}
    };

    beforeEach(() => {
        // Reset mocks
        vi.clearAllMocks();
    });

    it('renders with correct dimensions', () => {
        const wrapper = mount(SvgCanvas, {
            props: {
                width: 800,
                height: 600,
                nodes: []
            }
        });
        
        const container = wrapper.find('.svg-canvas-wrapper');
        expect(container.attributes('style')).toContain('width: 800px');
        expect(container.attributes('style')).toContain('height: 600px');
    });

    it('forces white background in light mode', async () => {
        const wrapper = mount(SvgCanvas, {
            props: { nodes: [], isLightMode: true }
        });
        
        const bg = wrapper.find('.canvas-bg');
        expect(bg.exists()).toBe(true);
        // We verify the class exists and component renders
        // CSS rules are verified by integration or visual tests usually
    });

    it('clamps node position when dragged out of bounds', async () => {
        const wrapper = mount(SvgCanvas, {
            props: {
                width: 500,
                height: 500,
                nodes: [{ id: '1', x: 100, y: 100, width: 50, height: 50 }]
            }
        });

        const svg = wrapper.find('svg');
        // Mock getBoundingClientRect on the SVG element
        svg.element.getBoundingClientRect = vi.fn(() => ({ ...mockRect, width: 500, height: 500 }));

        // 1. Mouse Down on Node
        const nodeGroup = wrapper.find('g');
        await nodeGroup.trigger('mousedown', { 
            clientX: 100, 
            clientY: 100,
        });
        
        // 2. Mouse Move (Drag to -50, -50)
        // clientX = -50 (relative to 0,0)
        // Offset was 0 (since mousedown at 100, node at 100)
        // Wait, dragOffset calculation:
        // mouseX = clientX - rect.left = 100 - 0 = 100
        // dragOffset = mouseX - node.x = 100 - 100 = 0
        
        // Move to -50:
        // mouseX = -50 - 0 = -50
        // newX = -50 - 0 = -50
        // Clamped should be 0
        
        await svg.trigger('mousemove', { 
            clientX: -50, 
            clientY: -50 
        });
        
        // Check emits
        expect(wrapper.emitted('boundaryClamp')).toBeTruthy();
        const clampEvent = wrapper.emitted('boundaryClamp')![0][0] as any;
        expect(clampEvent.nodeId).toBe('1');
        expect(clampEvent.x).toBe(0); // 0 instead of -50
        expect(clampEvent.y).toBe(0); // 0 instead of -50
        
        // Check update:nodes
        expect(wrapper.emitted('update:nodes')).toBeTruthy();
        const updatedNodes = wrapper.emitted('update:nodes')![0][0] as any[];
        expect(updatedNodes[0].x).toBe(0);
        expect(updatedNodes[0].y).toBe(0);
    });

    it('clamps node when resized via props to exceed boundaries', async () => {
        const wrapper = mount(SvgCanvas, {
            props: {
                width: 500,
                height: 500,
                nodes: [{ id: '1', x: 400, y: 400, width: 50, height: 50 }]
            }
        });

        // Update props: Resize to 200x200
        // x=400, w=200 -> x+w=600 > 500
        // Should clamp x to 500-200=300
        await wrapper.setProps({
            nodes: [{ id: '1', x: 400, y: 400, width: 200, height: 200 }]
        });
        
        await wrapper.vm.$nextTick(); // Wait for watch
        
        expect(wrapper.emitted('boundaryClamp')).toBeTruthy();
        const clampEvent = wrapper.emitted('boundaryClamp')![0][0] as any;
        expect(clampEvent.nodeId).toBe('1');
        expect(clampEvent.x).toBe(300);
        expect(clampEvent.y).toBe(300);
    });
});
