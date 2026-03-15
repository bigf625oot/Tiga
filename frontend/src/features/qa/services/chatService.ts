import type { Session, ModeType } from '../types';
import { api } from '@/core/api/client'; // Assuming this exists based on imports in SmartQA.vue

export interface SendChatMessagePayload {
  message: string;
  attachments?: string[];
  enable_search?: boolean;
  mode?: ModeType;
  intent?: string;
}

const getHeaders = (contentType: string | null = 'application/json') => {
  const headers: Record<string, string> = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }
  const token = localStorage.getItem('token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const chatService = {
  async getSession(sessionId: string): Promise<Session> {
    const res = await api.get(`/chat/sessions/${sessionId}`);
    console.log('[chatService] getSession response:', res);
    // Compatibility for wrapped response { code: 200, data: ... }
    if (res.data && typeof res.data === 'object' && 'data' in res.data) {
        // Double check if 'messages' is missing in root but present in data
        if (!('messages' in res.data) && 'messages' in res.data.data) {
            return res.data.data;
        }
    }
    return res.data;
  },

  async createSession(title: string, agentId: string | null, mode: ModeType, signal?: AbortSignal): Promise<Session> {
    const res = await api.post('/chat/sessions', {
      title,
      agent_id: agentId,
      mode
    }, { signal });
    return res.data;
  },

  async updateSession(sessionId: string, data: Partial<Session>): Promise<void> {
    await api.put(`/chat/sessions/${sessionId}`, data);
  },

  async sendChatMessage(sessionId: string, payload: SendChatMessagePayload, signal?: AbortSignal): Promise<Response> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
      signal
    });
    if (!res.ok) throw new Error(res.statusText);
    return res;
  },

  async sendChatMessageMultipart(sessionId: string, formData: FormData, signal?: AbortSignal): Promise<Response> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}/chat_multipart`, {
      method: 'POST',
      headers: getHeaders(null), // Let browser set Content-Type for multipart
      body: formData,
      signal
    });
    if (!res.ok) throw new Error(res.statusText);
    return res;
  },
  
  async createAutoTask(prompt: string): Promise<any> {
      // Using axios based api client as in original code
      const res = await api.post('/openclaw/create_task', { prompt });
      return res.data;
  }
};
