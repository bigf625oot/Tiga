<template>
  <div class="h-full w-full bg-background/50">
    <VueFlow
      v-model="nodes"
      v-model:edges="edges"
      :node-types="nodeTypes"
      :default-viewport="{ zoom: 1 }"
      :min-zoom="0.2"
      :max-zoom="4"
      :auto-pan-on-node-drag="true"
      :pan-on-drag="true"
      :zoom-on-scroll="true"
      :zoom-on-pinch="true"
      :fit-view-on-init="false"
      @node-drag-stop="onNodeDragStop"
      @pane-ready="onPaneReady"
      @viewport-change="onViewportChange"
    >
      <Background 
        :pattern-color="isLightMode ? '#94a3b8' : '#475569'" 
        :gap="20" 
        :size="1" 
        :variant="'dots'"
        class="transition-colors duration-300"
        :class="isLightMode ? 'opacity-10' : 'opacity-20'"
      />
      
      <!-- Custom Controls -->
      <div 
        class="absolute top-4 right-4 border rounded-lg flex items-center p-1 shadow-lg transition-colors duration-300 z-10 bg-card border-border"
      >
        <button 
          class="p-2 rounded text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          @click="zoomOut"
          title="缩小"
        >
          -
        </button>
        <span class="mx-2 text-[13px] font-din w-12 text-center text-foreground">
          {{ Math.round(zoom * 100) }}%
        </span>
        <button 
          class="p-2 rounded text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          @click="zoomIn"
          title="放大"
        >
          +
        </button>
        <div class="w-px h-4 mx-1 bg-border"></div>
        <button 
          class="p-2 rounded text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          @click="fitView"
          title="适应视图"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
          </svg>
        </button>
      </div>
    </VueFlow>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, markRaw } from 'vue';
import { VueFlow, type Node, type Edge, MarkerType, type VueFlowStore } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import FlowCanvasNode from './FlowCanvasNode.vue';
import type { FlowNode } from '../composables/useDashboardMock';
import { useTheme } from '@/composables/useTheme';

// Import Vue Flow styles
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';

const props = defineProps<{
  nodes: FlowNode[];
}>();

const emit = defineEmits(['add-node', 'delete-node']);

const { isLightMode } = useTheme();

const zoom = ref(1);
const vfInstance = ref<VueFlowStore | null>(null);

const onPaneReady = (instance: VueFlowStore) => {
  vfInstance.value = instance;
};

const onViewportChange = (v: { zoom: number }) => {
  zoom.value = v.zoom;
};

const zoomIn = () => vfInstance.value?.zoomIn();
const zoomOut = () => vfInstance.value?.zoomOut();
const fitView = () => vfInstance.value?.fitView();

const nodeTypes = {
  custom: markRaw(FlowCanvasNode),
};

const nodes = ref<Node[]>([]);
const edges = ref<Edge[]>([]);

// Initialize nodes from props
watch(() => props.nodes, (newNodes) => {
  const currentNodesMap = new Map(nodes.value.map(n => [n.id, n]));
  
  nodes.value = newNodes.map(n => {
    const existing = currentNodesMap.get(n.id);
    return {
      id: n.id,
      type: 'custom',
      position: existing ? existing.position : n.position,
      data: { ...n },
    };
  });

  const newEdges: Edge[] = [];
  for (let i = 0; i < newNodes.length - 1; i++) {
    const source = newNodes[i];
    const target = newNodes[i+1];
    newEdges.push({
      id: `e-${source.id}-${target.id}`,
      source: source.id,
      target: target.id,
      animated: true,
      style: { 
        stroke: isLightMode.value ? '#94a3b8' : '#475569', 
        strokeWidth: 1.5,
        strokeDasharray: '5,5',
      },
      markerEnd: MarkerType.ArrowClosed,
    });
  }
  edges.value = newEdges;
}, { immediate: true, deep: true });

watch(isLightMode, (light) => {
  edges.value = edges.value.map(e => ({
    ...e,
    style: { 
      ...e.style, 
      stroke: light ? '#94a3b8' : '#475569',
      strokeWidth: 1.5,
      strokeDasharray: '5,5',
    }
  }));
});

const onNodeDragStop = (event: any) => {
  console.log('Node dragged:', event.node.position);
};
</script>

<style scoped>
/* No extra styles needed */
</style>
