<template>
  <div class="h-full w-full relative bg-muted/10" @dragover="onDragOver" @drop="onDrop">
    <VueFlow
      v-model="store.nodes"
      v-model:edges="store.edges"
      :node-types="nodeTypes"
      :edge-types="edgeTypes"
      :default-viewport="{ zoom: 1.5 }"
      :min-zoom="0.2"
      :max-zoom="4"
      fit-view-on-init
      class="agent-flow"
      @pane-ready="onPaneReady"
      @node-click="onNodeClick"
      @pane-click="onPaneClick"
      @connect="onConnect"
    >
      <Background variant="dots" />
      <Controls />
      <MiniMap />
    </VueFlow>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue';
import { VueFlow, useVueFlow, type Node, type Edge, type Connection, MarkerType } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { MiniMap } from '@vue-flow/minimap';
import { useAgentFlowStore } from '../../store/agentFlow.store';
import AgentFlowNode from './AgentFlowNode.vue';
import AgentFlowEdge from './AgentFlowEdge.vue';

// Styles
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';
import '@vue-flow/controls/dist/style.css';
import '@vue-flow/minimap/dist/style.css';

const store = useAgentFlowStore();
const { addEdges, project, findNode } = useVueFlow();
let flowInstance: any = null;

const nodeTypes = {
  custom: markRaw(AgentFlowNode) as any,
};

const edgeTypes = {
  custom: markRaw(AgentFlowEdge) as any,
};

const onPaneReady = (instance: any) => {
  flowInstance = instance;
  instance.fitView();
};

const onNodeClick = (event: any) => {
  store.setSelectedNode(event.node.id);
};

const onPaneClick = () => {
  store.setSelectedNode(null);
};

const onConnect = (params: Connection) => {
  addEdges([{
    ...params,
    type: 'custom',
    animated: true,
    style: { stroke: '#94a3b8', strokeWidth: 2 },
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

  const nodeInfo = JSON.parse(typeStr);
  
  // Calculate position
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const position = flowInstance.project({
    x: event.clientX - bounds.left,
    y: event.clientY - bounds.top
  });

  const newNode: Node = {
    id: `node_${Date.now()}`,
    type: 'custom', // Use custom type wrapper
    position,
    data: { 
      label: nodeInfo.label,
      type: nodeInfo.type,
      description: '',
      config: {} 
    },
  };

  store.addNode(newNode);
};
</script>

<style>
/* Vue Flow Overrides */
.vue-flow__node-custom {
  padding: 0;
  border: none;
  background: transparent;
  width: auto;
}
</style>
