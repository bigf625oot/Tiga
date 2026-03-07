import { defineStore } from 'pinia';
import { ref } from 'vue';
import { 
  type Node, 
  type Edge, 
  type Connection, 
  useVueFlow
} from '@vue-flow/core';
import { NodeData } from '../types/pipeline';

export const usePipelineStore = defineStore('etl-pipeline', () => {
  const nodes = ref<Node<NodeData>[]>([]);
  const edges = ref<Edge[]>([]);
  const selectedNodeId = ref<string | null>(null);
  const isRunning = ref(false);

  // Vue Flow instance actions are handled via useVueFlow inside components mostly,
  // but we can manage global state here.

  function addNode(node: Node<NodeData>) {
    nodes.value.push(node);
  }

  function updateNodeConfig(id: string, config: any) {
    const node = nodes.value.find(n => n.id === id);
    if (node) {
      node.data.config = { ...node.data.config, ...config };
    }
  }

  function selectNode(id: string | null) {
    selectedNodeId.value = id;
  }

  async function startPipeline() {
    isRunning.value = true;
    // Mock API call
    console.log("Starting pipeline...");
  }

  async function stopPipeline() {
    isRunning.value = false;
    console.log("Stopping pipeline...");
  }

  return {
    nodes,
    edges,
    selectedNodeId,
    isRunning,
    addNode,
    updateNodeConfig,
    selectNode,
    startPipeline,
    stopPipeline
  };
});
