import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Node, Edge } from '@vue-flow/core';
import { api } from '@/core/api/client';

export interface AgentWorkflow {
  id: string;
  name: string;
  description?: string;
  definition?: {
    nodes: Node[];
    edges: Edge[];
  };
  tags?: string[];
  is_active: boolean;
  is_template?: boolean;
  created_at: string;
  updated_at?: string;
}

export const useAgentFlowStore = defineStore('agent-flow', () => {
  // State
  const nodes = ref<Node[]>([]);
  const edges = ref<Edge[]>([]);
  const selectedNodeId = ref<string | null>(null);
  const loading = ref(false);
  const isRunning = ref(false);
  const flowName = ref('未命名智能体流');
  const flowDescription = ref('');
  const workflows = ref<AgentWorkflow[]>([]);
  const currentWorkflowId = ref<string | null>(null);

  // Getters
  const selectedNode = computed<Node | null>(() => {
    const allNodes: any[] = nodes.value;
    return (allNodes.find(n => n.id === selectedNodeId.value) as Node) || null;
  });

  // Actions - Node Operations
  const setSelectedNode = (id: string | null) => {
    selectedNodeId.value = id;
  };

  const addNode = (node: Node) => {
    (nodes.value as any[]).push(node);
  };

  const removeNode = (id: string) => {
    nodes.value = (nodes.value as any[]).filter(n => n.id !== id) as any;
    edges.value = (edges.value as any[]).filter(e => e.source !== id && e.target !== id) as any;
    if (selectedNodeId.value === id) {
      selectedNodeId.value = null;
    }
  };

  const updateNodeData = (id: string, data: any) => {
    const node = (nodes.value as any[]).find(n => n.id === id);
    if (node) {
      node.data = { ...node.data, ...data };
    }
  };

  // Actions - API Operations
  const fetchWorkflows = async (params: { q?: string; skip?: number; limit?: number; is_template?: boolean; _t?: number } = {}) => {
    loading.value = true;
    try {
      const response = await api.get('/agent-workflows/', { params });
      workflows.value = response.data;
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    } finally {
      loading.value = false;
    }
  };

  const createWorkflow = async (data: { name: string; description?: string; definition?: any; is_template?: boolean }) => {
    loading.value = true;
    try {
      const response = await api.post('/agent-workflows/', data);
      workflows.value.push(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to create workflow:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const updateWorkflow = async (id: string, data: any) => {
    loading.value = true;
    try {
      const response = await api.put(`/agent-workflows/${id}`, data);
      const index = workflows.value.findIndex(w => w.id === id);
      if (index !== -1) {
        workflows.value[index] = response.data;
      }
      return response.data;
    } catch (error) {
      console.error('Failed to update workflow:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const deleteWorkflow = async (id: string) => {
    loading.value = true;
    try {
      await api.delete(`/agent-workflows/${id}`);
      workflows.value = (workflows.value as any[]).filter(w => w.id !== id) as any;
    } catch (error) {
      console.error('Failed to delete workflow:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const loadWorkflow = async (id: string) => {
    loading.value = true;
    try {
      // Find in local list first, or fetch
      let workflow = (workflows.value as any[]).find(w => w.id === id);
      if (!workflow) {
         const response = await api.get(`/agent-workflows/${id}`);
         workflow = response.data;
      }
      
      if (workflow) {
          currentWorkflowId.value = workflow.id;
          flowName.value = workflow.name;
          flowDescription.value = workflow.description || '';
          if (workflow.definition) {
              nodes.value = workflow.definition.nodes || [];
              edges.value = workflow.definition.edges || [];
          } else {
              nodes.value = [];
              edges.value = [];
          }
      }
    } catch (error) {
      console.error('Failed to load workflow:', error);
    } finally {
      loading.value = false;
    }
  };
  
  const resetCurrentWorkflow = () => {
      currentWorkflowId.value = null;
      flowName.value = '未命名智能体流';
      flowDescription.value = '';
      nodes.value = [];
      edges.value = [];
  };

  const saveFlow = async () => {
    loading.value = true;
    try {
      const data = {
        name: flowName.value,
        description: flowDescription.value,
        definition: {
          nodes: nodes.value,
          edges: edges.value
        }
      };

      if (currentWorkflowId.value) {
        await updateWorkflow(currentWorkflowId.value, data);
      } else {
        const newWorkflow = await createWorkflow(data);
        currentWorkflowId.value = newWorkflow.id;
      }
    } catch (error) {
        console.error('Failed to save flow:', error);
    } finally {
      loading.value = false;
    }
  };

  const runFlow = async () => {
    loading.value = true;
    isRunning.value = true;
    try {
      // TODO: Implement actual run logic calling /agent-workflows/run or /agent-workflows/run_stream
      // For now, keep mock behavior or integrate later
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Running flow...');
    } finally {
      loading.value = false;
      isRunning.value = false;
    }
  };

  const stopFlow = async () => {
    isRunning.value = false;
  };

  // Undo/Redo placeholders
  const undo = () => {};
  const redo = () => {};
  const canUndo = computed(() => false);
  const canRedo = computed(() => false);

  return {
    nodes,
    edges,
    selectedNodeId,
    selectedNode,
    loading,
    isRunning,
    flowName,
    flowDescription,
    workflows,
    currentWorkflowId,
    setSelectedNode,
    addNode,
    removeNode,
    updateNodeData,
    fetchWorkflows,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    loadWorkflow,
    resetCurrentWorkflow,
    saveFlow,
    runFlow,
    stopFlow,
    undo,
    redo,
    canUndo,
    canRedo
  };
});
