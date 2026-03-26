import { ref } from 'vue';
import { chatService } from '../services/chatService';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import { useToast } from '@/components/ui/toast/use-toast';
import type {
  Session, Message, Attachment, ModeType, StreamEventItem,
  AgentEvent, AgentExecutionPlan, AgentToolCallInfo, AgentObservationInfo,
  AgentArtifactCard,
} from '../types';

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
  const loadingStatus = ref<string>('');
  const abortController = ref<AbortController | null>(null);
  // NexusExecutor 路径：存储 agent_run_id 供断线续传使用
  const agentRunId = ref<string | null>(null);

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
      workflowStore.initWorkflow(id, data.workflow_state);
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
          // Capture current state to avoid overwriting new requests
          const currentAbortController = abortController.value;
          setTimeout(() => {
              isStopping.value = false;
              // Only reset if no new request has started
              if (abortController.value === currentAbortController) {
                  isLoading.value = false;
                  isStreaming.value = false;
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
    if (typeof obj.message === 'string' && obj.message.trim()) return truncate(obj.message.trim());
    if (typeof obj.desc === 'string' && obj.desc.trim()) return truncate(obj.desc.trim());

    if (eventType === 'tool_start' || eventType === 'tool_end' || eventType === 'tool_call') {
      const tool = obj?.tool ? String(obj.tool) : 'tool';
      return truncate(`${tool}${obj?.status ? ` (${String(obj.status)})` : ''}`);
    }

    if (eventType === 'sources' && Array.isArray(obj)) return `${obj.length} sources`;
    if (eventType === 'plan_step' && Array.isArray(obj)) return `${obj.length} steps`;
    if (eventType === 'done') return 'done';

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

    if (isStreaming.value) {
        stopGeneration();
        // Give it a tiny tick to clean up state
        await new Promise(resolve => setTimeout(resolve, 50));
    }

    isLoading.value = true;
    loadingStatus.value = ''; // Reset status
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
        await createNewSession(userMsg.slice(0, 20), agentId || null, mode);
      }
      
      if (!currentSessionId.value) throw new Error("Failed to create session");

      // Initialize workflow store so it's ready to accept events from /chat SSE
      if (mode === 'solo' || mode === 'team') {
          workflowStore.initWorkflow(currentSessionId.value);
          workflowStore.isRunning = true;
          workflowStore.tasks = [];
          workflowStore.logs = [];
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
      const startTime = Date.now();

      messages.value.push({
          role: 'assistant',
          content: '',
          reasoning: '',
          timestamp: new Date().toISOString()
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

                          switch (eventType) {
                              // ── NexusExecutor 新协议 ──────────────────────────────────
                              case 'meta':
                                  if (parsedData?.agent_run_id) agentRunId.value = parsedData.agent_run_id;
                                  if (parsedData?.msg_type) assistantMsg.type = parsedData.msg_type;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;

                              case 'thought': {
                                  const thoughtText = typeof parsedData.content === 'string' ? parsedData.content : '';
                                  assistantMsg.reasoning = (assistantMsg.reasoning || '') + thoughtText;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'plan_created': {
                                  const planContent = parsedData.content as AgentExecutionPlan | undefined;
                                  if (planContent?.tasks) {
                                      workflowStore.initFromAgentPlan(planContent);
                                  }
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'task_start': {
                                  workflowStore.handleAgentEvent(parsedData as AgentEvent);
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'tool_call':
                              case 'call': {
                                  workflowStore.handleAgentEvent(parsedData as AgentEvent);
                                  if (!assistantMsg.tools) assistantMsg.tools = [];
                                  const info = parsedData.content || parsedData;
                                  assistantMsg.tools.push({
                                      id: info.tool_call_id || Math.random().toString(),
                                      name: info.tool || info.name || 'unknown_tool',
                                      args: info.args || info.arguments || {},
                                      status: 'running'
                                  });
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'tool_output':
                              case 'result': {
                                  workflowStore.handleAgentEvent(parsedData as AgentEvent);
                                  if (assistantMsg.tools) {
                                      const info = parsedData.content || parsedData;
                                      const toolName = info.tool || info.name;
                                      const tool = [...assistantMsg.tools].reverse().find(t => t.name === toolName && t.status === 'running');
                                      if (tool) {
                                          tool.status = info.is_error ? 'error' : 'success';
                                          tool.result = typeof (info.result || info.output) === 'string' 
                                              ? (info.result || info.output) 
                                              : JSON.stringify(info.result || info.output);
                                      }
                                  }
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'artifact': {
                                  workflowStore.handleAgentEvent(parsedData as AgentEvent);
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'summary': {
                                  const summaryText = typeof parsedData.content === 'string' ? parsedData.content : '';
                                  if (summaryText) {
                                      assistantMsg.content = summaryText;
                                  }
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              // ── AgnoControlPlane 路径（chat/quick 模式）─────────────────
                              case 'text': {
                                  let textChunk = parsedData;
                                  if (typeof textChunk !== 'string') {
                                      textChunk = textChunk.content || normalizeThink(textChunk);
                                  }
                                  assistantMsg.content = (assistantMsg.content || '') + textChunk;
                                  workflowStore.appendOutput(textChunk);
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'think': {
                                  let thinking = parsedData;
                                  if (typeof thinking !== 'string') {
                                      thinking = thinking.content || normalizeThink(thinking);
                                  }
                                  assistantMsg.reasoning = (assistantMsg.reasoning || '') + thinking;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'sources':
                                  assistantMsg.sources = parsedData;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;

                              case 'error': {
                                  let errorText = parsedData;
                                  if (typeof errorText !== 'string') {
                                      errorText = errorText.content || errorText.message || errorText.detail || normalizeThink(errorText);
                                  }
                                  assistantMsg.content = (assistantMsg.content || '') + `\n**错误**: ${errorText}`;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'file':
                                  assistantMsg.content = (assistantMsg.content || '') + `\n::: file\n${JSON.stringify(parsedData)}\n:::\n`;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;

                              case 'image':
                                  if (parsedData?.url) {
                                      assistantMsg.content = (assistantMsg.content || '') + `\n![生成图片](${parsedData.url})\n`;
                                  }
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;

                              case 'step':
                                  if (!assistantMsg.steps) assistantMsg.steps = [];
                                  assistantMsg.steps.push(parsedData);
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;

                              case 'chart':
                                  assistantMsg.chart_config = parsedData;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;

                              // 遗留兼容
                              case 'plan_step':
                              case 'task_started':
                              case 'task_content':
                              case 'task_completed':
                              case 'task_failed':
                              case 'task_tool_call':
                              case 'artifacts':
                                  workflowStore.handleWorkflowEvent(parsedData);
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
          
          if (workflowStore.isRunning) {
              workflowStore.isRunning = false;
              workflowStore.addLog('Execution completed', 'success');
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
