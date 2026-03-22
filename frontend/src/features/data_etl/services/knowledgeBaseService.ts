import { knowledgeBaseApi, type KnowledgeBase, type KnowledgeBaseCreate, type KnowledgeBaseUpdate, type KnowledgeFile, type KnowledgeBaseConfig, type KnowledgeBasePermission } from '../api';

export const knowledgeBaseService = {
  async getKnowledgeBases(query?: string): Promise<KnowledgeBase[]> {
    return knowledgeBaseApi.list({ query });
  },

  async getKnowledgeBase(id: string): Promise<KnowledgeBase> {
    return knowledgeBaseApi.get(id);
  },

  async createKnowledgeBase(data: KnowledgeBaseCreate): Promise<KnowledgeBase> {
    return knowledgeBaseApi.create(data);
  },

  async updateKnowledgeBase(id: string, data: KnowledgeBaseUpdate): Promise<KnowledgeBase> {
    return knowledgeBaseApi.update(id, data);
  },

  async deleteKnowledgeBase(id: string): Promise<void> {
    return knowledgeBaseApi.delete(id);
  },

  async getFiles(kbId: string, parentId?: string): Promise<KnowledgeFile[]> {
    return knowledgeBaseApi.getFiles(kbId, { parent_id: parentId });
  },

  async createFolder(kbId: string, name: string, parentId?: string): Promise<KnowledgeFile> {
    return knowledgeBaseApi.createFile(kbId, { name, type: 'folder', parent_id: parentId });
  },

  async renameFile(kbId: string, fileId: string, name: string): Promise<KnowledgeFile> {
    return knowledgeBaseApi.updateFile(kbId, fileId, { name });
  },

  async deleteFile(kbId: string, fileId: string): Promise<void> {
    return knowledgeBaseApi.deleteFile(kbId, fileId);
  },

  async updateFile(kbId: string, fileId: string, data: Partial<KnowledgeFile>): Promise<KnowledgeFile> {
    return knowledgeBaseApi.updateFile(kbId, fileId, data);
  },

  async uploadFile(kbId: string, file: File, parentId?: string): Promise<KnowledgeFile> {
    return knowledgeBaseApi.uploadFile(kbId, file, parentId);
  },

  async getConfig(kbId: string): Promise<KnowledgeBaseConfig> {
    return knowledgeBaseApi.getConfig(kbId);
  },

  async updateConfig(kbId: string, config: KnowledgeBaseConfig): Promise<KnowledgeBaseConfig> {
    return knowledgeBaseApi.updateConfig(kbId, config);
  },

  async getPermissions(kbId: string): Promise<KnowledgeBasePermission> {
    return knowledgeBaseApi.getPermissions(kbId);
  },

  async updatePermissions(kbId: string, permissions: KnowledgeBasePermission): Promise<void> {
    return knowledgeBaseApi.updatePermissions(kbId, permissions);
  },
};