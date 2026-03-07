<script setup lang="ts">
import { ref, computed } from 'vue';
import { VueFlow, useVueFlow, type Node, type Edge, type Connection, MarkerType, type VueFlowStore } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { MiniMap } from '@vue-flow/minimap';
import { usePipelineStore } from '../composables/usePipelineStore';
import CustomNode from './CustomNode.vue';
import { Button } from '@/components/ui/button';
import { Play, Square, Save, Undo, Redo } from 'lucide-vue-next';
import { useTheme } from '@/composables/useTheme';

// Styles
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';
import '@vue-flow/controls/dist/style.css';
import '@vue-flow/minimap/dist/style.css';

const store = usePipelineStore();
const { isLightMode } = useTheme();
let flowInstance: VueFlowStore | null = null;

// Register node types
const nodeTypes = {
  custom: CustomNode,
};

const onPaneReady = (instance: VueFlowStore) => {
  flowInstance = instance;
};

// Handle connections
const onConnect = (params: Connection) => {
  if (!flowInstance) return;
  
  // Basic validation: Check for self-loops and duplicates
  if (params.source === params.target) return;
  const exists = store.edges.some(e => e.source === params.source && e.target === params.target);
  if (exists) return;

  flowInstance.addEdges([{
    ...params,
    animated: true,
    style: { 
      stroke: isLightMode.value ? '#94a3b8' : '#475569', 
      strokeWidth: 2 
    },
    markerEnd: MarkerType.ArrowClosed,
  }]);
};

const onDragOver = (event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move';
  }
};

const onDrop = (event: DragEvent) => {
  const typeStr = event.dataTransfer?.getData('application/vueflow');
  if (!typeStr || !flowInstance) return;

  const { type, subType, label } = JSON.parse(typeStr);
  
  // Use project to convert screen coordinates to flow coordinates
  // We need to subtract the bounding rect of the flow container to get relative coordinates
  // But flowInstance.project usually expects coordinates relative to the viewport? 
  // Actually, project() maps a coordinate {x, y} to the graph's coordinate system.
  // The input to project() should be relative to the flow pane if the pane is offset.
  // But typically with event.clientX/Y and screenToFlowCoordinate is better.
  
  // Assuming we have screenToFlowCoordinate from instance in newer versions, 
  // but to be safe with unknown version, let's use project with a calculated offset.
  // Or better, let's just use event.offsetX/Y which is relative to the target.
  // If the drop target is the pane, offsetX/Y is correct-ish (ignoring zoom/pan for a moment).
  // BUT, we need to account for zoom and pan. `project` does that.
  
  // Best bet without screenToFlowCoordinate:
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const position = flowInstance.project({
    x: event.clientX - bounds.left,
    y: event.clientY - bounds.top
  });

  // Create a new node
  const newNode: Node = {
    id: `node_${Date.now()}`,
    type: 'custom',
    position, 
    data: { 
      label: label || `New ${subType}`, 
      type, 
      subType,
      config: {},
      status: 'idle' 
    },
  };
  
  store.addNode(newNode);
};

const patternColor = computed(() => isLightMode.value ? '#cbd5e1' : '#334155');
const bgColor = computed(() => isLightMode.value ? '#ffffff' : '#000000');
const edgeOptions = computed(() => ({
  animated: true,
  style: { 
    stroke: isLightMode.value ? '#94a3b8' : '#475569', 
    strokeWidth: 2 
  },
  markerEnd: MarkerType.ArrowClosed,
}));
</script>

<template>
  <div class="w-full h-full bg-white dark:bg-black relative" @dragover="onDragOver" @drop="onDrop">
    <VueFlow
      v-model="store.nodes"
      v-model:edges="store.edges"
      :node-types="nodeTypes"
      :default-viewport="{ zoom: 1 }"
      :min-zoom="0.2"
      :max-zoom="4"
      :default-edge-options="edgeOptions"
      fit-view-on-init
      class="etl-flow"
      @pane-ready="onPaneReady"
      @connect="onConnect"
      @node-click="(e) => store.setSelectedNode(e.node.id)"
      @pane-click="() => store.setSelectedNode(null)"
    >
      <Background :pattern-color="patternColor" :bg-color="bgColor" :gap="20" />
      <Controls />
      <MiniMap />
      
      <!-- Controls Panel -->
      <div class="absolute top-4 right-4 flex gap-2 p-1.5 bg-background/80 backdrop-blur border border-border rounded-lg shadow-sm z-10">
        <Button variant="ghost" size="icon" class="h-8 w-8" @click="store.undo" :disabled="!store.canUndo">
          <Undo class="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon" class="h-8 w-8" @click="store.redo" :disabled="!store.canRedo">
          <Redo class="w-4 h-4" />
        </Button>
      </div>
    </VueFlow>
  </div>
</template>

<style>
/* Vue Flow Overrides */
.vue-flow__node-custom {
  /* Ensure custom node doesn't have default styles interfering */
  padding: 0;
  border: none;
  background: transparent;
}
</style>
