import { ref, nextTick } from 'vue';
import { chatService } from '../services/chatService';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import { useToast } from '@/components/ui/toast/use-toast';
import type { Session, Message, Attachment, ModeType } from '../types';

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
  const isStreaming = ref(false);
  const isStopping = ref(false);
  const abortController = ref<AbortController | null>(null);

  const fetchSessionDetails = async (id: string) => {
    try {
      console.log('[useChatSession] fetching details for:', id);
      const data = await chatService.getSession(id);
      console.log('[useChatSession] fetched data:', data);
      
      currentSession.value = data;
      
      // Prevent overwriting optimistic messages if the user sent a message 
      // while the session details were still fetching.
      if (isLoading.value || isStreaming.value || messages.value.some(m => m.status === 'sending')) {
          console.log('[useChatSession] skip overwriting messages because user already sent a new message');
      } else {
          messages.value = data.messages || [];
          console.log('[useChatSession] messages set to:', messages.value.length, 'items');
      }
      
      // Initialize workflow state if needed
      if (data.workflow_state) {
          workflowStore.initWorkflow(id, data.workflow_state);
      }
    } catch (e) {
      console.error("Failed to fetch session details", e);
      // Reset session if not found or error
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
  };

  const createNewSession = async (title: string, agentId: string | null, mode: ModeType) => {
      try {
          const newSession = await chatService.createSession(title, agentId, mode);
          currentSessionId.value = newSession.id;
          currentSession.value = newSession;
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
          setTimeout(() => {
              isStopping.value = false;
              isLoading.value = false;
              isStreaming.value = false;
          }, 300);
      }
  };

  const normalizeThink = (data: any): string => {
    if (data == null) return '';
    if (typeof data === 'string') return data;
    try { return JSON.stringify(data, null, 2); } catch { return String(data); }
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
    isLoading.value = true;
    abortController.value = new AbortController();

    // Optimistically add user message
    messages.value.push({
      role: 'user',
      content: userMsg,
      timestamp: new Date().toISOString(),
      // Handle attachments display if needed, but for now just text
    });

    try {
      if (!currentSessionId.value) {
        // Auto create session if not exists
        await createNewSession(userMsg.slice(0, 20), agentId, mode);
      }
      
      if (!currentSessionId.value) throw new Error("Failed to create session");

      const payload = {
        message: userMsg,
        attachments: attachments.map(a => a.id).filter((id): id is string => id !== undefined),
        enable_search: enableSearch,
        mode: mode,
        intent: 'chat'
      };

      const response = await chatService.sendChatMessage(
        currentSessionId.value, 
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
      isLoading.value = false;
      isStreaming.value = false;
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
      
      messages.value.push({ 
          role: 'assistant', 
          content: '', 
          reasoning: '', 
          timestamp: new Date().toISOString() 
      });
      const assistantMsg = messages.value[messages.value.length - 1];
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
                          switch (eventType) {
                              case 'meta':
                                  if (parsedData?.msg_type) assistantMsg.type = parsedData.msg_type;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'think':
                                  assistantMsg.reasoning = (assistantMsg.reasoning || '') + normalizeThink(parsedData);
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'step':
                                  if (!assistantMsg.steps) assistantMsg.steps = [];
                                  assistantMsg.steps.push(parsedData);
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'text':
                                  let textChunk = parsedData;
                                  if (typeof textChunk !== 'string') textChunk = normalizeThink(textChunk);
                                  assistantMsg.content = (assistantMsg.content || '') + textChunk;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'chart':
                                  assistantMsg.content = (assistantMsg.content || '') + `\n::: echarts\n${JSON.stringify(parsedData, null, 2)}\n:::\n`;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'sources':
                                  assistantMsg.sources = parsedData;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'file':
                                  assistantMsg.content = (assistantMsg.content || '') + `\n::: file\n${JSON.stringify(parsedData)}\n:::\n`;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              case 'error':
                                  assistantMsg.content += `\n**System Error**: ${parsedData}`;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
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
          isLoading.value = false;
          isStreaming.value = false;
          if (onUpdate) onUpdate();
      }
  };

  return {
    currentSessionId,
    currentSession,
    messages,
    isLoading,
    isStreaming,
    isStopping,
    fetchSessionDetails,
    createNewSession,
    stopGeneration,
    handleStreamResponse,
    abortController
  };
}
