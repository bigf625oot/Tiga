<template>
  <div class="h-full w-full bg-slate-50">
    <VueFlow
      v-model="elements"
      :default-zoom="1"
      :min-zoom="0.2"
      :max-zoom="4"
      :fit-view-on-init="true"
      :node-types="nodeTypes"
    >
      <Background pattern-color="#aaa" gap="8" />
      <Controls />
      <MiniMap />
    </VueFlow>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { MiniMap } from '@vue-flow/minimap';
import TaskNode from './TaskNode.vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';

// Import CSS
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';
import '@vue-flow/controls/dist/style.css';
import '@vue-flow/minimap/dist/style.css';

const store = useWorkflowStore();
const { fitView } = useVueFlow();

const nodeTypes = {
  custom: TaskNode,
};

const elements = computed({
  get: () => [...store.graph.nodes, ...store.graph.edges],
  set: (val) => {
    // Optional: handle changes if graph is interactive
  }
});

watch(() => store.graph.nodes.length, () => {
  setTimeout(() => {
    fitView({ padding: 0.2, duration: 500 });
  }, 100);
});
</script>
