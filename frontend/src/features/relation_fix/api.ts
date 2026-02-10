import { api } from '@/core/api/client';

export interface RelationFix {
  source: string;
  target: string;
  type?: string;
  description?: string;
  keywords?: string;
  reason?: string;
  attributes?: Record<string, any>;
}

export const relationFixApi = {
  detectRelations: async (mainNode: string, keyword: string) => {
    const response = await api.post<RelationFix[]>('/relation-fix/detect', { main_node: mainNode, keyword });
    return response.data;
  },

  applyFixes: async (fixes: RelationFix[]) => {
    const response = await api.post<{ count: number }>('/relation-fix/fix', { fixes });
    return response.data;
  },

  createRelation: async (source: string, target: string, relType: string, attributes: Record<string, any> = {}) => {
    const response = await api.post<{ success: boolean }>('/relation-fix/create', {
      source,
      target,
      rel_type: relType,
      attributes,
    });
    return response.data;
  },

  backupGraph: async () => {
    const response = await api.post<{ path: string }>('/relation-fix/backup');
    return response.data;
  },

  restoreBackup: async (filename?: string) => {
    const response = await api.post<{ success: boolean }>('/relation-fix/restore', { filename });
    return response.data;
  },

  getLogs: async (limit = 100) => {
    const response = await api.get<string[]>('/relation-fix/logs', { params: { limit } });
    return response.data;
  },
  
  searchNodes: async (q: string) => {
      const response = await api.get<string[]>('/relation-fix/search', { params: { q } });
      return response.data;
  },
  
  getNodeRelations: async (nodeId: string) => {
      const response = await api.get<{nodes: any[], edges: any[]}>(`/relation-fix/node/${nodeId}`);
      return response.data;
  }
};
