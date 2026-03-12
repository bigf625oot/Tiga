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
    return nodes.value.find(n => n.id === selectedNodeId.value) || null;
  });

  // Actions - Node Operations
  const setSelectedNode = (id: string | null) => {
    selectedNodeId.value = id;
  };

  const addNode = (node: Node) => {
    nodes.value.push(node);
  };

  const removeNode = (id: string) => {
    nodes.value = nodes.value.filter(n => n.id !== id);
    edges.value = edges.value.filter(e => e.source !== id && e.target !== id);
    if (selectedNodeId.value === id) {
      selectedNodeId.value = null;
    }
  };

  const updateNodeData = (id: string, data: any) => {
    const node = nodes.value.find(n => n.id === id);
    if (node) {
      node.data = { ...node.data, ...data };
    }
  };

  // Actions - API Operations
  const fetchWorkflows = async (params: { q?: string; skip?: number; limit?: number } = {}) => {
    loading.value = true;
    try {
      const response = await api.get('/agent_workflows/', { params });
      workflows.value = response.data;
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    } finally {
      loading.value = false;
    }
  };

  const createWorkflow = async (data: { name: string; description?: string; definition?: any }) => {
    loading.value = true;
    try {
      const response = await api.post('/agent_workflows/', data);
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
      const response = await api.put(`/agent_workflows/${id}`, data);
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
      await api.delete(`/agent_workflows/${id}`);
      workflows.value = workflows.value.filter(w => w.id !== id);
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
      let workflow = workflows.value.find(w => w.id === id);
      if (!workflow) {
         const response = await api.get(`/agent_workflows/${id}`);
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
      // TODO: Implement actual run logic calling /agent_workflow/run or /agent_workflow/run_stream
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
