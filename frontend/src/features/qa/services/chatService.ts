import type { Session, ModeType } from '../types';
import { api } from '@/core/api/client'; // Assuming this exists based on imports in SmartQA.vue

export const chatService = {
  async getSession(sessionId: string): Promise<Session> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}`);
    if (!res.ok) throw new Error('Failed to fetch session details');
    return res.json();
  },

  async createSession(title: string, agentId: string | null, mode: ModeType, signal?: AbortSignal): Promise<Session> {
    const res = await fetch('/api/v1/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        agent_id: agentId,
        mode
      }),
      signal
    });
    if (!res.ok) throw new Error('Failed to create session');
    return res.json();
  },

  async updateSession(sessionId: string, data: Partial<Session>): Promise<void> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to update session');
  },

  async sendChatMessage(sessionId: string, payload: any, signal?: AbortSignal): Promise<Response> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
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
