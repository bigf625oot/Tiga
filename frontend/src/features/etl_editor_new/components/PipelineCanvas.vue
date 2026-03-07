<script setup lang="ts">
import { ref, computed } from 'vue';
import { VueFlow, useVueFlow, type Node, type Edge, type Connection, MarkerType } from '@vue-flow/core';
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
const { onConnect, addEdges } = useVueFlow();
const { isLightMode } = useTheme();

// Register node types
const nodeTypes = {
  custom: CustomNode,
};

// Handle connections
onConnect((params: Connection) => {
  addEdges([{
    ...params,
    animated: true,
    style: { 
      stroke: isLightMode.value ? '#94a3b8' : '#475569', 
      strokeWidth: 2 
    },
    markerEnd: MarkerType.ArrowClosed,
  }]);
});

const onDragOver = (event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move';
  }
};

const onDrop = (event: DragEvent) => {
  const typeStr = event.dataTransfer?.getData('application/vueflow');
  if (!typeStr) return;

  const { type, subType } = JSON.parse(typeStr);
  
  // Create a new node
  const newNode: Node = {
    id: `node_${Date.now()}`,
    type: 'custom',
    position: { x: event.offsetX, y: event.offsetY }, // Simplify position logic for now
    data: { 
      label: `New ${subType}`, 
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
    >
      <Background :pattern-color="patternColor" :bg-color="bgColor" :gap="20" />
      <Controls />
      <MiniMap />
      
      <!-- Top Toolbar Panel -->
      <div class="absolute top-4 right-4 flex gap-2 p-2 bg-background/80 backdrop-blur border border-border rounded-lg shadow-sm z-10">
        <Button variant="ghost" size="icon" class="h-8 w-8">
          <Undo class="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon" class="h-8 w-8">
          <Redo class="w-4 h-4" />
        </Button>
        <div class="w-px h-6 bg-border mx-1" />
        <Button variant="outline" size="sm" class="h-8 gap-2">
          <Save class="w-3.5 h-3.5" />
          保存
        </Button>
        <Button 
          size="sm" 
          :variant="store.isRunning ? 'destructive' : 'default'"
          class="h-8 gap-2"
          @click="store.isRunning ? store.stopPipeline() : store.startPipeline()"
        >
          <template v-if="store.isRunning">
            <Square class="w-3.5 h-3.5 fill-current" />
            停止
          </template>
          <template v-else>
            <Play class="w-3.5 h-3.5 fill-current" />
            运行
          </template>
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
