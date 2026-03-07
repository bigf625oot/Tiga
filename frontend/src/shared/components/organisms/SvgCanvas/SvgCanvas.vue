<template>
  <div 
    class="svg-canvas-wrapper relative overflow-hidden select-none"
    :style="{ width: `${width}px`, height: `${height}px` }"
    @mouseup="onGlobalMouseUp"
    @mouseleave="onGlobalMouseUp"
  >
    <!-- Background Layer -->
    <div class="absolute inset-0 -z-10 canvas-bg"></div>

    <svg 
      ref="svgRef"
      :width="width" 
      :height="height" 
      xmlns="http://www.w3.org/2000/svg"
      class="w-full h-full block"
      @mousemove="onMouseMove"
    >
      <!-- Grid Pattern -->
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" stroke-width="0.5" class="text-slate-200 dark:text-slate-800 opacity-50"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />

      <!-- Nodes Layer -->
      <g v-for="node in nodes" :key="node.id" 
         :transform="`translate(${node.x}, ${node.y})`"
         class="cursor-grab active:cursor-grabbing transition-colors duration-200"
         :class="{ 'cursor-grabbing': draggingNodeId === node.id }"
         @mousedown.stop="(e) => onNodeMouseDown(e, node)"
      >
        <!-- Node Body -->
        <rect 
            :width="node.width" 
            :height="node.height" 
            rx="6" 
            class="fill-white dark:fill-slate-800 stroke-slate-300 dark:stroke-slate-600 hover:stroke-blue-400 hover:stroke-2 transition-all shadow-sm"
            :class="{ '!stroke-blue-500 !stroke-2': node.selected || draggingNodeId === node.id }"
            :style="{ stroke: node.color }"
            stroke-width="1.5"
        />
        
        <!-- Node Label -->
        <text 
            :x="node.width / 2" 
            :y="node.height / 2" 
            text-anchor="middle" 
            dominant-baseline="middle" 
            class="text-xs font-medium fill-slate-700 dark:fill-slate-200 pointer-events-none select-none"
        >
            {{ node.label || node.id }}
        </text>
      </g>
    </svg>
    
    <!-- Boundary Warning Toast -->
    <transition name="fade">
        <div v-if="showBoundaryWarning" class="absolute bottom-4 right-4 bg-amber-50 text-amber-600 px-3 py-1.5 rounded-lg text-xs font-medium shadow-sm border border-amber-200 flex items-center gap-2">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            边界限制触发
        </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { clampNodePosition } from '@/shared/utils/boundary';
import type { SvgNode, BoundaryClampEvent } from './types';

// Props
const props = withDefaults(defineProps<{
    width?: number;
    height?: number;
    nodes: SvgNode[];
    isLightMode?: boolean; // Optional explicit mode override
}>(), {
    width: 1200,
    height: 800,
    nodes: () => []
});

// Emits
const emit = defineEmits<{
    (e: 'update:nodes', nodes: SvgNode[]): void;
    (e: 'nodeClick', nodeId: string): void;
    (e: 'boundaryClamp', event: BoundaryClampEvent): void;
}>();

// State
const draggingNodeId = ref<string | null>(null);
const dragOffset = ref({ x: 0, y: 0 });
const showBoundaryWarning = ref(false);
let warningTimeout: number | null = null;

// Methods
const validateAndClampNodes = () => {
    let hasChanges = false;
    const newNodes = props.nodes.map(node => {
        const { x, y, clamped } = clampNodePosition(
            node.x,
            node.y,
            node.width,
            node.height,
            props.width,
            props.height
        );
        
        if (clamped) {
            hasChanges = true;
            emit('boundaryClamp', { nodeId: node.id, x, y });
            return { ...node, x, y };
        }
        return node;
    });
    
    if (hasChanges) {
        emit('update:nodes', newNodes);
        triggerBoundaryWarning();
    }
};

// Watch for external changes (add/resize)
watch(() => props.nodes, () => {
    // Check if any node is out of bounds
    // We should do this in nextTick or just run it.
    // If we emit update:nodes immediately, parent updates prop, watch triggers again?
    // No, because new prop will be valid.
    validateAndClampNodes();
}, { deep: true });

const onNodeMouseDown = (e: MouseEvent, node: SvgNode) => {
    draggingNodeId.value = node.id;
    // Calculate offset relative to node top-left
    // e.clientX is global, node.x is relative to canvas
    // We need canvas bounding rect
    const svgRect = (e.currentTarget as Element).closest('svg')?.getBoundingClientRect();
    if (svgRect) {
        // Current mouse pos relative to svg
        const mouseX = e.clientX - svgRect.left;
        const mouseY = e.clientY - svgRect.top;
        
        dragOffset.value = {
            x: mouseX - node.x,
            y: mouseY - node.y
        };
    }
    emit('nodeClick', node.id);
};

const onMouseMove = (e: MouseEvent) => {
    if (!draggingNodeId.value) return;

    const svgElement = e.currentTarget as SVGSVGElement;
    const rect = svgElement.getBoundingClientRect();
    
    // Calculate new raw position
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    let newX = mouseX - dragOffset.value.x;
    let newY = mouseY - dragOffset.value.y;

    // Find the node being dragged
    const nodeIndex = props.nodes.findIndex(n => n.id === draggingNodeId.value);
    if (nodeIndex === -1) return;
    
    const node = props.nodes[nodeIndex];

    // Apply Boundary Clamping
    const { x: clampedX, y: clampedY, clamped } = clampNodePosition(
        newX, 
        newY, 
        node.width, 
        node.height, 
        props.width, 
        props.height
    );

    // Update Node Position
    // We emit update to parent (v-model pattern or event)
    // Here we assume we can mutate props for simplicity or emit updated array
    // Ideally we should clone and emit
    const updatedNodes = [...props.nodes];
    updatedNodes[nodeIndex] = {
        ...node,
        x: clampedX,
        y: clampedY
    };
    
    emit('update:nodes', updatedNodes);

    // Trigger Warning and API Event if Clamped
    if (clamped) {
        triggerBoundaryWarning();
        emit('boundaryClamp', {
            nodeId: node.id,
            x: clampedX,
            y: clampedY
        });
    }
};

const onGlobalMouseUp = () => {
    draggingNodeId.value = null;
};

const triggerBoundaryWarning = () => {
    showBoundaryWarning.value = true;
    if (warningTimeout) clearTimeout(warningTimeout);
    warningTimeout = window.setTimeout(() => {
        showBoundaryWarning.value = false;
    }, 2000);
};

// API: Expose manual clamp method for external usage (e.g. adding new nodes)
const checkAndClampNode = (node: SvgNode) => {
    const { x, y, clamped } = clampNodePosition(
        node.x,
        node.y,
        node.width,
        node.height,
        props.width,
        props.height
    );
    
    if (clamped) {
        emit('boundaryClamp', { nodeId: node.id, x, y });
        return { ...node, x, y };
    }
    return node;
};

defineExpose({
    checkAndClampNode
});
</script>

<style scoped>
/* Requirement 1: Force white background in light mode with high priority */
/* Using :where() or specific class strategy to ensure specificity */

/* Default (Light Mode) */
.canvas-bg {
    background-color: #ffffff !important;
}

/* Dark Mode Override (Only if .dark class is present on ancestor) */
:global(.dark) .canvas-bg {
    background-color: #0f172a !important; /* Slate 900 */
}

/* Force override if explicitly requested for light mode even inside dark context (if needed) */
/* But typically theme is global. The requirement says "In light theme... force... higher than any global". */
/* This implies if theme is Light, background MUST be white. */

:global(html:not(.dark)) .canvas-bg {
    background-color: #ffffff !important;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
