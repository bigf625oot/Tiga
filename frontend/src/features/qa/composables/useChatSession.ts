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
      const data = await chatService.getSession(id);
      currentSession.value = data;
      messages.value = data.messages || [];
      
      // Initialize workflow state if needed
      if (data.workflow_state) {
          workflowStore.initWorkflow(id, data.workflow_state);
      }
    } catch (e) {
      console.error("Failed to fetch session details", e);
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

    // 1. Upload attachments first (if any) -> This logic should ideally be in the component or useAttachments, 
    // but for now we assume they are already uploaded or we handle IDs here. 
    // In SmartQA.vue, it uploads them before calling chat API.
    // We will assume `attachments` passed here are already processed or we need to upload them.
    // To keep it simple, let's assume the component handles upload and passes IDs.
    // Wait, the component passed `selectedAttachments` which has files.
    // Let's handle upload here or in the caller. 
    // The caller `SmartQA.vue` had the upload logic inside `sendMessage`.
    // I will extract upload logic to `useAttachments` and call it from the component, 
    // then pass IDs to this function.
    // So `attachments` here will be just IDs or metadata? 
    // Let's change the signature to accept `attachmentIds`.
    
    // But wait, I can't easily change the flow without changing `SmartQA.vue` first.
    // I'll stick to the plan: The component orchestrates. 
    // But `useChatSession` should handle the actual chat API call.

    // Let's assume the caller handles upload and passes `attachmentIds`.
  };

  const handleStreamResponse = async (response: Response, onUpdate?: () => void) => {
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
              
              const parts = buffer.split('\n\n');
              buffer = parts.pop() || '';
              
              for (const part of parts) {
                  const lines = part.split('\n');
                  let eventType = 'message';
                  let data = '';
                  
                  for (const line of lines) {
                      if (line.startsWith('event: ')) eventType = line.substring(7).trim();
                      else if (line.startsWith('data: ')) data = line.substring(6);
                  }
                  
                  if (data) {
                      try {
                          const parsedData = JSON.parse(data);
                          switch (eventType) {
                              case 'meta':
                                  if (parsedData?.msg_type) assistantMsg.type = parsedData.msg_type;
                                  break;
                              case 'think':
                                  assistantMsg.reasoning = (assistantMsg.reasoning || '') + normalizeThink(parsedData);
                                  break;
                              case 'text':
                                  let textChunk = parsedData;
                                  if (typeof textChunk !== 'string') textChunk = normalizeThink(textChunk);
                                  assistantMsg.content = (assistantMsg.content || '') + textChunk;
                                  break;
                              case 'chart':
                                  assistantMsg.content = (assistantMsg.content || '') + `\n::: echarts\n${JSON.stringify(parsedData, null, 2)}\n:::\n`;
                                  break;
                              case 'sources':
                                  assistantMsg.sources = parsedData;
                                  break;
                              case 'file':
                                  assistantMsg.content = (assistantMsg.content || '') + `\n::: file\n${JSON.stringify(parsedData)}\n:::\n`;
                                  break;
                              case 'error':
                                  assistantMsg.content += `\n**System Error**: ${parsedData}`;
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
