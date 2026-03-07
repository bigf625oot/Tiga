import { api } from '@/core/api/client';
import type { Pipeline, PipelineCreate, PipelineUpdate, PipelineRunResponse, LogEntry } from '../types/pipeline';

export const pipelineApi = {
  // List all pipelines
  list: async (params?: { skip?: number; limit?: number }) => {
    const response = await api.get<Pipeline[]>('/pathway/pipelines', { params });
    return response.data;
  },

  // Create a new pipeline
  create: async (data: PipelineCreate) => {
    const response = await api.post<Pipeline>('/pathway/pipelines', data);
    return response.data;
  },

  // Get pipeline by ID
  get: async (id: number) => {
    const response = await api.get<Pipeline>(`/pathway/pipelines/${id}`);
    return response.data;
  },

  // Update pipeline
  update: async (id: number, data: PipelineUpdate) => {
    const response = await api.put<Pipeline>(`/pathway/pipelines/${id}`, data);
    return response.data;
  },

  // Run pipeline
  run: async (id: number) => {
    const response = await api.post<PipelineRunResponse>(`/pathway/pipelines/${id}/run`);
    return response.data;
  },

  // Stop pipeline
  stop: async (id: number) => {
    const response = await api.post(`/pathway/pipelines/${id}/stop`);
    return response.data;
  },

  // Delete pipeline
  delete: async (id: number) => {
    const response = await api.delete(`/pathway/pipelines/${id}`);
    return response.data;
  },

  // Get pipeline logs
  logs: async (id: number) => {
    // Mock implementation if API fails or for demo
    try {
      const response = await api.get<LogEntry[]>(`/pathway/pipelines/${id}/logs`);
      return response.data;
    } catch (e) {
      // Return mock data for demo purposes if backend not ready
      console.warn('Failed to fetch logs, returning mock data', e);
      return [
        { timestamp: new Date(Date.now() - 10000).toISOString(), level: 'INFO', message: 'Pipeline initialization started.' },
        { timestamp: new Date(Date.now() - 8000).toISOString(), level: 'INFO', message: 'Loading configuration...' },
        { timestamp: new Date(Date.now() - 7000).toISOString(), level: 'INFO', message: 'Connecting to Kafka source...' },
        { timestamp: new Date(Date.now() - 6000).toISOString(), level: 'DEBUG', message: 'Kafka consumer group: etl-group-1' },
        { timestamp: new Date(Date.now() - 5000).toISOString(), level: 'INFO', message: 'Source connected successfully.' },
        { timestamp: new Date(Date.now() - 4000).toISOString(), level: 'INFO', message: 'Starting transform nodes...' },
        { timestamp: new Date(Date.now() - 2000).toISOString(), level: 'WARN', message: 'High memory usage detected in node: Transform_1' },
        { timestamp: new Date().toISOString(), level: 'INFO', message: 'Pipeline running.' }
      ] as LogEntry[];
    }
  },

  // Get system connections (mock)
  getSystemConnections: async (type: 'vector' | 'graph') => {
    // Mock response
    await new Promise(resolve => setTimeout(resolve, 500));
    if (type === 'vector') {
      return [
        { id: 'sys_vec_1', name: 'System Elasticsearch (Default)', type: 'elasticsearch', status: 'connected' },
        { id: 'sys_vec_2', name: 'Milvus Cluster A', type: 'milvus', status: 'connected' }
      ];
    } else if (type === 'graph') {
      return [
        { id: 'sys_graph_1', name: 'System Neo4j (Default)', type: 'neo4j', status: 'connected' },
        { id: 'sys_graph_2', name: 'Nebula Graph Dev', type: 'nebula', status: 'disconnected' }
      ];
    }
    return [];
  }
};
