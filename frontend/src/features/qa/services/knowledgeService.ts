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
  },

  async retryProcess(docId: number): Promise<any> {
    const res = await fetch(`/api/v1/knowledge/${docId}/retry`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to retry processing');
    return res.json();
  },

  async getDocumentContent(docId: string | number): Promise<{content: string, filename: string}> {
    const res = await fetch(`/api/v1/knowledge/${docId}/content`);
    if (!res.ok) throw new Error('Failed to fetch document content');
    return res.json();
  },

  async getDocMeta(docId: string | number): Promise<{ id: number; filename: string; file_size: number; created_at: string | null; updated_at: string | null }> {
    const res = await fetch(`/api/v1/knowledge/${docId}/meta`);
    if (!res.ok) throw new Error('Failed to fetch document meta');
    return res.json();
  }
};
