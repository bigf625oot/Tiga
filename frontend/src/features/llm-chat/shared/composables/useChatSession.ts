import { ref } from 'vue';
import { chatService } from '@/features/llm-chat/services/chatService';
import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import { useToast } from '@/components/ui/toast/use-toast';
import { createEventDispatcher } from './modes/eventDispatcher';
import type {
  Session, Message, Attachment, ModeType, StreamEventItem,
} from '@/features/llm-chat/shared/types';

declare global {
  interface Window {
    _lastStreamEndTime?: number;
    _lastStreamSessionId?: string | null;
  }
}

/**
 * Manages chat session state, message streaming, and workflow integration.
 * 
 * @returns Chat session state and control functions
 */
export function useChatSession() {
  const { toast } = useToast();
  const workflowStore = useWorkflowStore();
  
  const currentSessionId = ref<string | null>(null);
  const currentSession = ref<Session | null>(null);
  const messages = ref<Message[]>([]);
  const isLoading = ref(false);
  const isFetchingSession = ref(false);
  const isStreaming = ref(false);
  const isStopping = ref(false);
  const loadingStatus = ref<string>('');
  const abortController = ref<AbortController | null>(null);
  // NexusExecutor 路径：存储 agent_run_id 供断线续传使用
  const agentRunId = ref<string | null>(null);

  const fetchSessionDetails = async (id: string) => {
    try {
      isFetchingSession.value = true;
      console.log('[useChatSession] fetching details for:', id);
      const data = await chatService.getSession(id);
      console.log('[useChatSession] fetched data:', data);
      
      currentSession.value = data;
      
      // Prevent overwriting optimistic messages if the user sent a message 
      // while the session details were still fetching.
      if (isLoading.value || isStreaming.value || messages.value.some(m => m.status === 'sending')) {
          console.log('[useChatSession] skip overwriting messages because user already sent a new message');
      } else {
          // Additional protection: Only overwrite if we aren't within 1s of a stream finishing
          // to prevent race conditions with backend persistence.
          // IMPORTANT: Also check if the last stream was for THIS session ID, otherwise switching
          // to a different session immediately after a stream ends will block loading messages.
          const isRecentStream = window._lastStreamEndTime && (Date.now() - window._lastStreamEndTime < 1500);
          const isSameSessionStream = window._lastStreamSessionId === id;
          
          if (!isRecentStream || !isSameSessionStream) {
              // Merge strategy instead of overwrite to preserve optimistic state
              const backendMessages = data.messages || [];
              if (messages.value.length === 0) {
                  messages.value = backendMessages;
              } else {
                  // If we have messages, only append ones we don't have
                  const existingIds = new Set(messages.value.map(m => m.id).filter(Boolean));
                  const newMessages = backendMessages.filter((m: any) => !existingIds.has(m.id));
                  if (newMessages.length > 0) {
                      messages.value = [...messages.value, ...newMessages];
                  }
              }
              console.log('[useChatSession] messages set to:', messages.value.length, 'items');
          } else {
              console.log('[useChatSession] skip overwriting messages due to recent stream end race condition protection');
          }
      }
      
      // Initialize workflow state if needed
              workflowStore.initWorkflow(id, data.workflow_state);
              
              // Reconstruct steps and tools for task mode messages if backend didn't persist them
              if (data.workflow_state?.tasks?.length > 0) {
                  // In workflow mode, chat messages might not be saved. Reconstruct them if empty.
                  if (messages.value.length === 0) {
                      messages.value.push({
                          role: 'user',
                          content: data.title || '任务对话',
                          timestamp: new Date().toISOString()
                      });
                      messages.value.push({
                          role: 'assistant',
                          content: '已启动任务规划模式。',
                          isSystem: true,
                          timestamp: new Date().toISOString()
                      });
                  }

                  const lastAssistantMsg = messages.value.slice().reverse().find(m => m.role === 'assistant');
                  if (lastAssistantMsg) {
                      if (!lastAssistantMsg.steps || lastAssistantMsg.steps.length === 0) {
                          lastAssistantMsg.steps = data.workflow_state.tasks.map((t: any, idx: number) => ({
                              step: idx,
                              content: t.name,
                              id: String(t.id || idx),
                              status: t.status
                          }));
                      }
                      
                      if (!lastAssistantMsg.tools || lastAssistantMsg.tools.length === 0) {
                          const reconstructedTools: any[] = [];
                          data.workflow_state.tasks.forEach((t: any) => {
                              if (t.toolCalls && t.toolCalls.length > 0) {
                                  t.toolCalls.forEach((tc: any) => {
                                      reconstructedTools.push({
                                          id: `recon-${Math.random().toString(36).slice(2)}`,
                                          name: tc.tool_name,
                                          args: tc.tool_args,
                                          status: tc.status,
                                          result: tc.result,
                                          task_id: t.id
                                      });
                                  });
                              }
                          });
                          if (reconstructedTools.length > 0) {
                              lastAssistantMsg.tools = reconstructedTools;
                          }
                      }
                  }
              }
    } catch (e) {
      console.error("Failed to fetch session details", e);
      // Don't reset session if we are actively streaming or loading
      if (!isLoading.value && !isStreaming.value) {
          currentSessionId.value = null;
          currentSession.value = null;
          messages.value = [];
          // Optionally clear URL param
          const url = new URL(window.location.href);
          if (url.searchParams.has('session_id')) {
              url.searchParams.delete('session_id');
              window.history.replaceState({}, '', url.toString());
          }
      }
    } finally {
      isFetchingSession.value = false;
    }
  };

  const createNewSession = async (title: string, agentId: string | null, mode: ModeType) => {
      try {
          const newSession = await chatService.createSession(title, agentId, mode);
          currentSessionId.value = newSession.id;
          currentSession.value = newSession;
          workflowStore.initWorkflow(newSession.id, (newSession as any).workflow_state);
          return newSession;
      } catch (e) {
          console.error(e);
          throw e;
      }
  };

  const stopGeneration = () => {
      isStopping.value = true;
      try {
          if (workflowStore.isRunning) {
              workflowStore.stopWorkflow();
          }
          if (abortController.value) {
              abortController.value.abort();
              abortController.value = null;
          }
      } finally {
          // Immediately reset loading states so session switches don't get blocked
          isLoading.value = false;
          isStreaming.value = false;
          
          // Capture current state to avoid overwriting new requests
          const currentAbortController = abortController.value;
          const stoppedSessionId = currentSessionId.value; // Capture the session ID being stopped
          setTimeout(() => {
              isStopping.value = false;
              // Trigger final persist locally if needed by firing a fake stream end
              if (abortController.value === currentAbortController) {
                  window._lastStreamEndTime = Date.now();
                  window._lastStreamSessionId = stoppedSessionId;
              }
          }, 300);
      }
  };

  const normalizeThink = (data: any): string => {
    if (data == null) return '';
    if (typeof data === 'string') return data;
    try { return JSON.stringify(data, null, 2); } catch { return String(data); }
  };

  const toEventContent = (eventType: string, data: any) => {
    const normalize = (v: any) => normalizeThink(v).trim();
    const truncate = (s: string, max = 180) => (s.length > max ? `${s.slice(0, max)}…` : s);

    if (data == null) return '';
    if (typeof data === 'string') return truncate(data.trim());

    const obj = data as any;

    if (typeof obj.content === 'string' && obj.content.trim()) return truncate(obj.content.trim());
    if (typeof obj.content === 'object' && obj.content !== null) return truncate(JSON.stringify(obj.content));
    if (typeof obj.message === 'string' && obj.message.trim()) return truncate(obj.message.trim());
    if (typeof obj.desc === 'string' && obj.desc.trim()) return truncate(obj.desc.trim());

    if (eventType === 'tool_start' || eventType === 'tool_end' || eventType === 'tool_call') {
      const tool = obj?.tool ? String(obj.tool) : 'tool';
      return truncate(`${tool}${obj?.status ? ` (${String(obj.status)})` : ''}`);
    }

    if (eventType === 'sources' && Array.isArray(obj)) return `${obj.length} sources`;
    if (eventType === 'plan_step' && Array.isArray(obj)) return `${obj.length} steps`;
    if (eventType === 'done') return 'done';
    
    if (typeof obj === 'object' && obj !== null) return truncate(JSON.stringify(obj));

    return truncate(normalize(obj));
  };

  const appendStreamEvent = (msg: Message, eventType: string, data: any) => {
    const content = toEventContent(eventType, data);
    if (!content) return;
    if (!msg.stream_events) msg.stream_events = [];

    const list = msg.stream_events as StreamEventItem[];
    const last = list.length > 0 ? list[list.length - 1] : null;
    const ts = Date.now();

    if (eventType === 'text' || eventType === 'think') {
      if (last && last.event === eventType) {
        last.content = content;
        last.ts = ts;
        last.raw = data;
        return;
      }
    }

    if (last && last.event === eventType && last.content === content) return;

    list.push({
      id: `${ts}-${Math.random().toString(16).slice(2)}`,
      event: eventType,
      content,
      ts,
      raw: data
    });

    if (list.length > 200) {
      msg.stream_events = list.slice(-200);
    }
  };

  const sendMessage = async (
    userMsg: string, 
    attachments: Attachment[], 
    agentId: string, 
    mode: ModeType, 
    enableSearch: boolean,
    onStreamUpdate?: () => void
  ) => {
    if (isLoading.value) return;

    // Prevent duplicate sending of the exact same message if we are already streaming
    if (isStreaming.value) {
        const lastUserMsg = messages.value.slice().reverse().find(m => m.role === 'user');
        if (lastUserMsg && lastUserMsg.content === userMsg) {
            console.log('[useChatSession] Preventing duplicate user message during streaming');
            return;
        }

        stopGeneration();
        // Give it a tiny tick to clean up state
        await new Promise(resolve => setTimeout(resolve, 50));
    }

    isLoading.value = true;
    loadingStatus.value = ''; // Reset status
    abortController.value = new AbortController();
    
    // Optimistically add user message with a consistent clock
    messages.value.push({
      role: 'user',
      content: userMsg,
      timestamp: new Date().toISOString(),
      // Handle attachments display if needed, but for now just text
    });

    let targetSessionId = currentSessionId.value;

    try {
      if (!currentSessionId.value) {
        // Auto create session if not exists
        await createNewSession(userMsg.slice(0, 20), agentId || null, mode);
        targetSessionId = currentSessionId.value;
      }
      
      if (!targetSessionId) throw new Error("Failed to create session");

        // Initialize workflow store so it's ready to accept events from /chat SSE
      if (mode === 'solo' || mode === 'team') {
          workflowStore.initWorkflow(targetSessionId);
          workflowStore.isRunning = true;
          // Clear only if empty to prevent UI flicker
          if (!workflowStore.tasks || workflowStore.tasks.length === 0) {
              workflowStore.tasks = [];
              workflowStore.logs = [];
          }
      }

      const payload = {
        message: userMsg,
        attachments: attachments.map(a => a.id).filter((id): id is string => id !== undefined),
        enable_search: enableSearch,
        mode: mode,
        intent: 'chat',
        agent_id: agentId || undefined,
      };

      const response = await chatService.sendChatMessage(
        targetSessionId, 
        payload,
        abortController.value.signal
      );

      await handleStreamResponse(response, onStreamUpdate);

    } catch (e: any) {
      if (e.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        console.error('Send message failed', e);
        toast({
          title: "发送失败",
          description: e.message || "未知错误",
          variant: "destructive"
        });
        // Remove failed user message? Or mark as error?
        // For now, let's just leave it but maybe append error to messages?
        messages.value.push({
          role: 'assistant',
          content: `**发送失败**: ${e.message}`,
          timestamp: new Date().toISOString()
        });
      }
    } finally {
      if (currentSessionId.value === targetSessionId) {
          isLoading.value = false;
          isStreaming.value = false;
      }
      abortController.value = null;
    }
  };

  const handleStreamResponse = async (
    response: Response,
    onUpdate?: () => void,
    onEvent?: (eventType: string, data: any) => void
  ) => {
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const startTime = Date.now();
      const streamSessionId = currentSessionId.value; // Capture the session ID for this stream

      messages.value.push({
          role: 'assistant',
          content: '',
          reasoning: '',
          // Ensure assistant message timestamp is not older than user message
          timestamp: messages.value.length > 0 ? messages.value[messages.value.length - 1].timestamp : new Date().toISOString()
      });
      const assistantMsg = messages.value[messages.value.length - 1];
      // 立即切换到 streaming 状态，消除 loading 空窗期
      isLoading.value = false;
      isStreaming.value = true;
      let buffer = '';

      try {
          while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              const chunk = decoder.decode(value, { stream: true });
              buffer += chunk;
              
              const parts = buffer.split(/\r\n\r\n|\n\n/);
              buffer = parts.pop() || '';
              
              for (const part of parts) {
                  const lines = part.split(/\r?\n/);
                  let eventType = 'message';
                  let data = '';
                  
                  for (const line of lines) {
                      if (line.startsWith('event: ')) {
                          eventType = line.substring(7).trim();
                      } else if (line.startsWith('data: ')) {
                          data += line.substring(6);
                      } else if (line.startsWith('data:')) {
                          data += line.substring(5);
                      }
                  }
                  
                  if (data) {
                      try {
                          const parsedData = JSON.parse(data);

                          // 不写入 stream_events 的系统级事件
                          const NO_STREAM_EVENTS = new Set(['meta', 'task_start', 'done']);
                          if (!NO_STREAM_EVENTS.has(eventType)) {
                              appendStreamEvent(assistantMsg, eventType, parsedData);
                          }

                          // 策略注册表与动态分发
                          const handlers = createEventDispatcher(
                              currentSession.value?.mode,
                              assistantMsg,
                              workflowStore,
                              normalizeThink,
                              agentRunId
                          );

                          if (handlers[eventType]) {
                              handlers[eventType](parsedData);
                              if (onEvent) onEvent(eventType, parsedData);
                          } else {
                              // Fallback for unknown events or default 'message' to prevent silent swallowing
                              const fallbackContent = parsedData.content || parsedData.message || parsedData.detail;
                              if (fallbackContent) {
                                  if (eventType === 'error') {
                                      assistantMsg.content = (assistantMsg.content || '') + `\n\n**系统错误**: ${fallbackContent}\n`;
                                  } else if (eventType === 'message' || eventType === 'text') {
                                      // Only append if it's not already at the end to prevent duplicates
                                      if (!assistantMsg.content?.endsWith(fallbackContent)) {
                                          assistantMsg.content = (assistantMsg.content || '') + fallbackContent;
                                      }
                                  } else {
                                      if (!assistantMsg.content?.includes(fallbackContent)) {
                                          assistantMsg.content = (assistantMsg.content || '') + `\n\n**[${eventType}]**: ${fallbackContent}\n`;
                                      }
                                  }
                              }
                          }
                      } catch (e) {
                          console.warn('Failed to parse SSE event data', e);
                      }
                  }
              }
              if (onUpdate) onUpdate();
          }
      } catch (e) {
          console.error(e);
      } finally {
          // Only reset loading states if we haven't switched sessions
          if (currentSessionId.value === streamSessionId) {
              isLoading.value = false;
              isStreaming.value = false;
          }
          window._lastStreamEndTime = Date.now();
          window._lastStreamSessionId = streamSessionId;
          
          if (workflowStore.isRunning && currentSessionId.value === streamSessionId) {
              workflowStore.isRunning = false;
              workflowStore.addLog('Execution completed', 'success');
              // Force a final flush to backend
              window._lastStreamEndTime = Date.now();
          }

          // Set duration when stream ends
          const durationMs = Date.now() - startTime;
          assistantMsg.meta_data = { ...(assistantMsg.meta_data || {}), duration: durationMs };
          
          if (onUpdate) onUpdate();
      }
  };

  return {
    currentSessionId,
    currentSession,
    messages,
    isLoading,
    isFetchingSession,
    isStreaming,
    isStopping,
    loadingStatus,
    fetchSessionDetails,
    createNewSession,
    stopGeneration,
    handleStreamResponse,
    abortController,
    agentRunId
  };
}
