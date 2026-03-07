import { defineStore } from 'pinia';
import { ref, computed, type ComputedRef } from 'vue';
import { pipelineApi } from '../api/pipeline';
import { type Pipeline, type PipelineCreate, type PipelineUpdate, type NodeData, PipelineStatus } from '../types/pipeline';
import type { Node, Edge } from '@vue-flow/core';

export const usePipelineStore = defineStore('pipeline', () => {
  const pipelines = ref<Pipeline[]>([]);
  const currentPipeline = ref<Pipeline | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Vue Flow State
  const nodes = ref<Node<NodeData>[]>([]);
  const edges = ref<Edge[]>([]);
  const selectedNodeId = ref<string | null>(null);

  const isRunning = computed(() => currentPipeline.value?.status === PipelineStatus.RUNNING);
  
  let pollTimer: any = null;

  const startPolling = () => {
    if (pollTimer) return;
    pollTimer = setInterval(async () => {
      if (!currentPipeline.value) return;
      try {
        // Silent fetch to update status
        const pipeline = await pipelineApi.get(currentPipeline.value.id);
        
        // Update status and stats
        currentPipeline.value.status = pipeline.status;
        currentPipeline.value.last_run_at = pipeline.last_run_at;
        
        // Update nodes metrics if available
        if (pipeline.dag_config?.nodes) {
           // Create a new array to trigger reactivity
           pipeline.dag_config.nodes.forEach((remoteNode: any) => {
             // Use findIndex and array reassignment to ensure reactivity without deep type issues
             const localNodeIndex = nodes.value.findIndex(n => n.id === remoteNode.id);
             if (localNodeIndex !== -1 && remoteNode.data) {
               const localNode = nodes.value[localNodeIndex];
               // Avoid deep merge that might confuse TS
               nodes.value[localNodeIndex].data = {
                 ...(localNode.data as any),
                 status: remoteNode.data.status,
                 metrics: remoteNode.data.metrics
               };
             }
           });
           
           // Force update if needed, but reactivity should handle deep changes
        }

        if (pipeline.status !== PipelineStatus.RUNNING) {
          stopPolling();
        }
      } catch (e) {
        console.error('Status polling failed', e);
      }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  };
  
  // @ts-ignore
  const selectedNode = computed<any>(() => {
    const found = nodes.value.find(n => n.id === selectedNodeId.value);
    return found || null;
  });

  // Actions
  const setSelectedNode = (id: string | null) => {
    selectedNodeId.value = id;
  };

  const updateNodeData = (id: string, data: Partial<NodeData>) => {
    const node = nodes.value.find(n => n.id === id);
    if (node) {
      node.data = { ...node.data, ...data };
    }
  };

  const addNode = (node: Node<NodeData>) => {
    nodes.value.push(node);
    // Auto save or mark dirty?
  };

  const removeNode = (id: string) => {
    nodes.value = nodes.value.filter(n => n.id !== id);
    edges.value = edges.value.filter(e => e.source !== id && e.target !== id);
    if (selectedNodeId.value === id) {
      selectedNodeId.value = null;
    }
  };

  const fetchPipelines = async () => {
    loading.value = true;
    try {
      pipelines.value = await pipelineApi.list();
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  const loadPipeline = async (id: number) => {
    loading.value = true;
    try {
      const pipeline = await pipelineApi.get(id);
      currentPipeline.value = pipeline;
      if (pipeline.dag_config) {
        nodes.value = pipeline.dag_config.nodes || [];
        edges.value = pipeline.dag_config.edges || [];
      } else {
        nodes.value = [];
        edges.value = [];
      }
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  const createPipeline = async (data: PipelineCreate) => {
    loading.value = true;
    try {
      const newPipeline = await pipelineApi.create(data);
      pipelines.value.push(newPipeline);
      currentPipeline.value = newPipeline;
      return newPipeline;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  };

  const savePipeline = async () => {
    if (!currentPipeline.value) {
      return createPipeline({
        name: `新建流水线 ${new Date().toLocaleString()}`,
        dag_config: {
          nodes: nodes.value,
          edges: edges.value
        }
      });
    }
    
    loading.value = true;
    try {
      const updateData: PipelineUpdate = {
        dag_config: {
          nodes: nodes.value,
          edges: edges.value
        }
      };
      const updated = await pipelineApi.update(currentPipeline.value.id, updateData);
      currentPipeline.value = updated;
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  const runPipeline = async () => {
    // Auto save before run (creates if not exists)
    await savePipeline();
    
    if (!currentPipeline.value) return;
    
    loading.value = true;
    try {
      const result = await pipelineApi.run(currentPipeline.value.id);
      // Optimistically update status
      currentPipeline.value.status = PipelineStatus.RUNNING; 
      startPolling(); // Start polling for metrics/status
      return result;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  };

  const stopPipeline = async () => {
    if (!currentPipeline.value) return;
    
    loading.value = true;
    try {
      await pipelineApi.stop(currentPipeline.value.id);
      currentPipeline.value.status = PipelineStatus.STOPPED;
      stopPolling(); // Stop polling
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  // Version Control State
  const versions = ref<{ id: string; name: string; timestamp: number; data: { nodes: any[]; edges: any[] } }[]>([]);

  const createVersion = (name: string) => {
    const newVersion = {
      id: crypto.randomUUID(),
      name: name || `Version ${versions.value.length + 1}`,
      timestamp: Date.now(),
      data: {
        nodes: JSON.parse(JSON.stringify(nodes.value)),
        edges: JSON.parse(JSON.stringify(edges.value))
      }
    };
    versions.value.unshift(newVersion); // Add to top
    return newVersion;
  };

  const restoreVersion = (versionId: string) => {
    const version = versions.value.find(v => v.id === versionId);
    if (version) {
      nodes.value = JSON.parse(JSON.stringify(version.data.nodes));
      edges.value = JSON.parse(JSON.stringify(version.data.edges));
      return true;
    }
    return false;
  };

  const initializeTemplate = (templateNodes: Node[], templateEdges: Edge[]) => {
    currentPipeline.value = null; // Reset current pipeline
    nodes.value = JSON.parse(JSON.stringify(templateNodes));
    edges.value = JSON.parse(JSON.stringify(templateEdges));
    versions.value = []; // Reset history
  };

  const undo = () => {
    // Placeholder for undo
  };
  
  const redo = () => {
    // Placeholder for redo
  };

  const canUndo = computed(() => false);
  const canRedo = computed(() => false);

  return {
    pipelines,
    currentPipeline,
    nodes,
    edges,
    versions, // Export versions
    loading,
    error,
    fetchPipelines,
    loadPipeline,
    createPipeline,
    savePipeline,
    runPipeline,
    stopPipeline,
    addNode,
    removeNode,
    createVersion, // Export action
    restoreVersion, // Export action
    initializeTemplate, // Export action
    undo,
    redo,
    canUndo,
    canRedo,
    isRunning,
    selectedNodeId,
    selectedNode,
    setSelectedNode,
    updateNodeData
  };
});
