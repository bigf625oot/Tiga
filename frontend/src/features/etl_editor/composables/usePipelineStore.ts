import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { pipelineApi } from '../api/pipeline';
import { type Pipeline, type PipelineCreate, type PipelineUpdate, type NodeData, type PipelineNode, type PipelineEdge, PipelineStatus } from '../types/pipeline';

export const usePipelineStore = defineStore('pipeline', () => {
  const pipelines = ref<Pipeline[]>([]);
  const currentPipeline = ref<Pipeline | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  type FlowNode = PipelineNode;
  type FlowEdge = PipelineEdge;
  type SelectedNode = PipelineNode;

  // Vue Flow State
  const nodes = ref<FlowNode[]>([]);
  const edges = ref<FlowEdge[]>([]);
  const selectedNodeId = ref<string | null>(null);

  const isRunning = computed(() => currentPipeline.value?.status === PipelineStatus.RUNNING);
  
  let pollTimer: any = null;

  const startPolling = (id?: number) => {
    if (pollTimer) return;
    const targetId = id || currentPipeline.value?.id;
    if (!targetId) return;
    
    pollTimer = setInterval(async () => {
      
      if (!currentPipeline.value) {
          stopPolling();
          return;
      }
      
      // If we were polling for a specific ID and currentPipeline changed, maybe stop?
      // But usually startPolling is called when running.
      
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
               nodes.value[localNodeIndex] = {
                 ...localNode,
                 data: {
                   ...(localNode.data ?? {}),
                   status: remoteNode.data.status,
                   metrics: remoteNode.data.metrics,
                 },
               };
             }
           });
        }

        if (pipeline.status !== PipelineStatus.RUNNING) {
          stopPolling();
        }
      } catch (e) {
        console.error('Status polling failed', e);
        stopPolling(); // Stop on error to avoid spam
      }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  };
  
  const selectedNode = computed<SelectedNode | null>(() => {
    const id = selectedNodeId.value;
    if (!id) return null;
    for (const n of nodes.value) {
      if (n.id === id) return n as unknown as SelectedNode;
    }
    return null;
  });

  // Actions
  const setSelectedNode = (id: string | null) => {
    selectedNodeId.value = id;
  };

  const updateNodeData = (id: string, data: Partial<NodeData>) => {
    nodes.value = nodes.value.map(n => {
      if (n.id === id) {
        return { ...n, data: { ...(n.data ?? {}), ...data } } as FlowNode;
      }
      return n;
    });
  };

  const addNode = (node: FlowNode) => {
    nodes.value = [...nodes.value, node];
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
        nodes.value = (pipeline.dag_config.nodes || []) as FlowNode[];
        edges.value = (pipeline.dag_config.edges || []) as FlowEdge[];
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

  const runPipeline = async (id?: number) => {
    const targetId = id || currentPipeline.value?.id;
    if (!targetId) return;

    // Auto save before run (creates if not exists) only if running current pipeline
    if (!id || (currentPipeline.value && id === currentPipeline.value.id)) {
      await savePipeline();
    }
    
    loading.value = true;
    try {
      const result = await pipelineApi.run(targetId);
      
      // Update pipeline in list
      const p = pipelines.value.find(p => p.id === targetId);
      if (p) p.status = PipelineStatus.RUNNING;

      // Update current pipeline if matches
      if (currentPipeline.value?.id === targetId) {
        currentPipeline.value.status = PipelineStatus.RUNNING; 
        startPolling(); // Start polling for metrics/status
      }
      return result;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  };

  const stopPipeline = async (id?: number) => {
    const targetId = id || currentPipeline.value?.id;
    if (!targetId) return;
    
    loading.value = true;
    try {
      await pipelineApi.stop(targetId);
      
      // Update pipeline in list
      const p = pipelines.value.find(p => p.id === targetId);
      if (p) p.status = PipelineStatus.STOPPED;

      if (currentPipeline.value?.id === targetId) {
        currentPipeline.value.status = PipelineStatus.STOPPED;
        stopPolling(); // Stop polling
      }
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  const deletePipeline = async (id: number) => {
    loading.value = true;
    try {
      await pipelineApi.delete(id);
      pipelines.value = pipelines.value.filter(p => p.id !== id);
      if (currentPipeline.value?.id === id) {
        currentPipeline.value = null;
      }
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  // Version Control State
  const versions = ref<{ id: string; name: string; timestamp: number; data: { nodes: FlowNode[]; edges: FlowEdge[] } }[]>([]);

  const createVersion = (name: string) => {
    const newVersion = {
      id: crypto.randomUUID(),
      name: name || `Version ${versions.value.length + 1}`,
      timestamp: Date.now(),
      data: {
        nodes: JSON.parse(JSON.stringify(nodes.value)) as FlowNode[],
        edges: JSON.parse(JSON.stringify(edges.value)) as FlowEdge[]
      }
    };
    versions.value.unshift(newVersion); // Add to top
    return newVersion;
  };

  const restoreVersion = (versionId: string) => {
    const version = versions.value.find(v => v.id === versionId);
    if (version) {
      nodes.value = JSON.parse(JSON.stringify(version.data.nodes)) as FlowNode[];
      edges.value = JSON.parse(JSON.stringify(version.data.edges)) as FlowEdge[];
      return true;
    }
    return false;
  };

  const initializeTemplate = (templateNodes: FlowNode[], templateEdges: FlowEdge[]) => {
    currentPipeline.value = null; // Reset current pipeline
    nodes.value = JSON.parse(JSON.stringify(templateNodes)) as FlowNode[];
    edges.value = JSON.parse(JSON.stringify(templateEdges)) as FlowEdge[];
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
    deletePipeline,
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
