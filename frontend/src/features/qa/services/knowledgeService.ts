import type { KnowledgeDoc } from '../types';

export const knowledgeService = {
  async getKnowledgeDocs(): Promise<KnowledgeDoc[]> {
    const res = await fetch('/api/v1/knowledge/list');
    if (!res.ok) throw new Error('Failed to fetch knowledge docs');
    return res.json();
  },

  async uploadFile(file: File, signal?: AbortSignal): Promise<KnowledgeDoc> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/v1/knowledge/upload', {
      method: 'POST',
      body: formData,
      signal
    });
    if (!res.ok) throw new Error(`Failed to upload file: ${file.name}`);
    return res.json();
  }
};
