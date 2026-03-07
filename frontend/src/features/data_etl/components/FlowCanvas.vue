<template>
  <div class="h-full w-full" :class="isLightMode ? 'bg-[#F9FAFB]' : 'bg-[#0B0C10]'">
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
      :fit-view-on-init="true"
      @node-drag-stop="onNodeDragStop"
      @pane-ready="onPaneReady"
      @viewport-change="onViewportChange"
    >
      <Background 
        :pattern-color="isLightMode ? '#9CA3AF' : '#3B82F6'" 
        :gap="20" 
        :size="1" 
        :variant="isLightMode ? 'dots' : 'dots'"
        class="transition-colors duration-300"
        :class="isLightMode ? 'opacity-10' : 'opacity-20'"
      />
      
      <!-- Custom Controls -->
      <div 
        class="absolute top-4 left-1/2 transform -translate-x-1/2 border rounded-lg flex items-center p-1 shadow-lg transition-colors duration-300 z-10"
        :class="isLightMode ? 'bg-white border-border' : 'bg-[#1F2937] border-gray-700'"
      >
        <button 
          class="p-2 rounded" 
          :class="isLightMode ? 'text-gray-500 hover:bg-gray-100 hover:text-gray-900' : 'text-gray-400 hover:bg-gray-700 hover:text-white'"
          @click="zoomOut"
          title="缩小"
        >
          -
        </button>
        <span class="mx-2 text-[13px] font-din w-12 text-center" :class="isLightMode ? 'text-gray-700' : 'text-gray-300'">
          {{ Math.round(zoom * 100) }}%
        </span>
        <button 
          class="p-2 rounded"
          :class="isLightMode ? 'text-gray-500 hover:bg-gray-100 hover:text-gray-900' : 'text-gray-400 hover:bg-gray-700 hover:text-white'"
          @click="zoomIn"
          title="放大"
        >
          +
        </button>
        <div class="w-px h-4 mx-1" :class="isLightMode ? 'bg-gray-200' : 'bg-gray-700'"></div>
        <button 
          class="p-2 rounded"
          :class="isLightMode ? 'text-gray-500 hover:bg-gray-100 hover:text-gray-900' : 'text-gray-400 hover:bg-gray-700 hover:text-white'"
          @click="fitView"
          title="适应视图"
        >
          [ ]
        </button>
        <div class="w-px h-4 mx-1" :class="isLightMode ? 'bg-gray-200' : 'bg-gray-700'"></div>
        <button 
          class="p-4 py-1 text-xs hover:opacity-80"
          :class="isLightMode ? 'text-primary' : 'text-blue-400'"
          @click="emit('add-node')"
        >
          + 添加节点
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
      style: { stroke: isLightMode.value ? '#CBD5E1' : '#1E3A8A', strokeWidth: 2 },
      markerEnd: MarkerType.ArrowClosed,
    });
  }
  edges.value = newEdges;
}, { immediate: true, deep: true });

watch(isLightMode, (light) => {
  edges.value = edges.value.map(e => ({
    ...e,
    style: { ...e.style, stroke: light ? '#CBD5E1' : '#1E3A8A' }
  }));
});

const onNodeDragStop = (event: any) => {
  console.log('Node dragged:', event.node.position);
};
</script>

<style scoped>
/* No extra styles needed */
</style>
