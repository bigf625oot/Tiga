import type { KnowledgeDoc } from '../types';

export const knowledgeService = {
  async getKnowledgeDocs(keyword?: string): Promise<KnowledgeDoc[]> {
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    const res = await fetch(`/api/v1/knowledge/list?${params.toString()}`);
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
