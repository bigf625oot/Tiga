import type { Session, ModeType } from '@/features/llm-chat/shared/types';
import { api } from '@/core/api/client'; // Assuming this exists based on imports in SmartQA.vue

export interface SendChatMessagePayload {
  message: string;
  attachments?: string[];
  enable_search?: boolean;
  enable_reasoning?: boolean;
  mode?: ModeType;
  intent?: string;
  agent_id?: string;
}

type RoutedMode = 'quick' | 'solo' | 'team' | 'workflow';
type ChatRouteConfig = {
  chat: (sessionId: string) => string;
  multipart: (sessionId: string) => string;
};

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

const modeRouteTable: Record<RoutedMode, ChatRouteConfig> = {
  quick: {
    chat: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat`,
    multipart: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat_multipart`,
  },
  solo: {
    chat: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat`,
    multipart: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat_multipart`,
  },
  team: {
    chat: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat`,
    multipart: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat_multipart`,
  },
  workflow: {
    chat: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat`,
    multipart: (sessionId) => `/api/v1/chat/sessions/${sessionId}/chat_multipart`,
  },
};

const resolveChatRoute = (mode?: ModeType): ChatRouteConfig => {
  if (mode === 'solo' || mode === 'team' || mode === 'workflow' || mode === 'quick') {
    return modeRouteTable[mode];
  }
  return modeRouteTable.quick;
};

export const chatService = {
  async getSession(sessionId: string): Promise<Session> {
    const res = await api.get(`/chat/sessions/${sessionId}`);
    // 兼容 { code: 200, data: ... } 包装
    let raw = res.data;
    if (raw && typeof raw === 'object' && 'data' in raw && !('messages' in raw)) {
        raw = raw.data;
    }
    // 映射后端字段到前端 Message 结构
    if (raw?.messages) {
        raw.messages = raw.messages.map((m: any) => ({
            ...m,
            // reasoning_content → reasoning（ThinkingBlock 使用）
            reasoning: m.reasoning_content || m.reasoning || undefined,
            // meta_data.stream_events → stream_events（StreamSteps 使用）
            stream_events: m.meta_data?.stream_events || m.stream_events || undefined,
        }));
    }
    return raw;
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

  async deleteMessage(sessionId: string, messageId: number): Promise<void> {
    await api.delete(`/chat/sessions/${sessionId}/messages/${messageId}`);
  },

  async sendChatMessage(sessionId: string, payload: SendChatMessagePayload, signal?: AbortSignal): Promise<Response> {
    const route = resolveChatRoute(payload.mode);
    const res = await fetch(route.chat(sessionId), {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
      signal
    });
    if (!res.ok) throw new Error(res.statusText);
    return res;
  },

  async sendChatMessageMultipart(sessionId: string, formData: FormData, signal?: AbortSignal): Promise<Response> {
    const route = resolveChatRoute((formData.get('mode') as ModeType | null) || undefined);
    const res = await fetch(route.multipart(sessionId), {
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
