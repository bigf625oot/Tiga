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
                                  // 兼容后端两种 payload 布局：
                                  //   格式 A（AgentEvent 标准）: { type, content: { plan_id, tasks: [...] } }
                                  //   格式 B（直接展开）:        { type, plan_id, tasks: [...] }
                                  // 同时兼容 tasks / steps 两种 key 名（历史字段差异）
                                  const inner = (parsedData.content ?? parsedData) as any;
                                  const taskList: any[] = inner?.tasks ?? inner?.steps ?? [];
                                  if (taskList.length > 0) {
                                      workflowStore.initFromAgentPlan({
                                          ...inner,
                                          tasks: taskList,
                                      } as AgentExecutionPlan);
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

                              // ── 后端实际协议事件（与 AgentEvent 字段名不同）──────────────
                              case 'plan': {
                                  // 后端: { type:'plan', content: '{ "reasoning":..., "tasks":[...] }' }
                                  // content 是 JSON 字符串，必须先 parse 再取 tasks
                                  try {
                                      const planRaw = parsedData.content;
                                      const planData = typeof planRaw === 'string'
                                          ? JSON.parse(planRaw)
                                          : (planRaw ?? parsedData);
                                      const taskList: any[] = planData?.tasks ?? planData?.steps ?? [];
                                      if (taskList.length > 0) {
                                          workflowStore.initFromAgentPlan({
                                              ...planData,
                                              tasks: taskList,
                                          } as AgentExecutionPlan);

                                          // Bug Fix #1: SoloTaskCard.execSteps 依赖 message.steps 而非 Store。
                                          // plan 事件只写 Store 不写 message，导致左侧步骤时间线永远为空。
                                          // 将 taskList 同步到 assistantMsg.steps，统一数据源。
                                          if (!assistantMsg.steps) assistantMsg.steps = [];
                                          taskList.forEach((t: any, idx: number) => {
                                              assistantMsg.steps!.push({
                                                  step: idx,
                                                  content: t.title || t.name || t.description || `步骤 ${idx + 1}`,
                                                  id: t.id || t.task_id || String(idx),
                                              } as any);
                                          });
                                      }
                                  } catch (e) {
                                      console.warn('[useChatSession] plan event parse failed', e);
                                  }
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'execute_start': {
                                  // 后端: { type:'execute_start', content: '任务描述' }
                                  // 找第一个 pending 任务标记为 running（顺序执行协议）
                                  const pendingTask = workflowStore.tasks.find((t: any) => t.status === 'pending');
                                  if (pendingTask) {
                                      // Bug Fix #2: 原来使用 'task_started' 走 handleEvent 路由，
                                      // 但 handleTaskStarted 内部逻辑与 initFromAgentPlan 建立的任务
                                      // 结构存在 id 查找不一致风险。直接调用专属处理器，保证链路确定性。
                                      workflowStore.handleTaskStarted({
                                          task_id: pendingTask.id,
                                          task_name: pendingTask.name,
                                      });
                                  }
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'subtask_done': {
                                  // 后端: { type:'subtask_done', content: '完整任务输出（markdown）' }
                                  // 1. 将最终输出写入任务的 output 字段
                                  // 2. 将任务标记为 completed（触发文档保存逻辑）
                                  // 3. 用权威输出覆盖流式累积的 assistantMsg.content
                                  const rawContent = parsedData.content;
                                  const finalOutput = typeof rawContent === 'string'
                                      ? rawContent
                                      : (rawContent != null ? JSON.stringify(rawContent) : '');
                                  const runningTask = workflowStore.tasks.find((t: any) => t.status === 'running');
                                  if (runningTask) {
                                      // 先写 output，handleTaskCompleted 会读取它保存为文档
                                      workflowStore.handleWorkflowEvent({
                                          type: 'task_content',
                                          task_id: runningTask.id,
                                          content: finalOutput,
                                      });
                                      workflowStore.handleWorkflowEvent({
                                          type: 'task_completed',
                                          task_id: runningTask.id,
                                      });
                                  }
                                  // 流式 text 事件逐 token 累积，但可能包含前缀噪音；
                                  // subtask_done 给出的是后端归整后的权威版本，用它覆盖。
                                  // Bug Fix #3: 原条件 `if (finalOutput)` 在内容为空字符串时会跳过赋值，
                                  // 导致 text 流中的噪音内容残留在 assistantMsg.content 里。
                                  // 改为无条件覆盖：只要 subtask_done 到达，content 就以后端为准。
                                  assistantMsg.content = finalOutput;
                                  if (onEvent) onEvent(eventType, parsedData);
                                  break;
                              }

                              case 'status': {
                                  // 后端: { type:'status', content: '执行阶段说明文字' }
                                  // 写入工作流日志供 LogDrawer 展示，不影响消息内容
                                  const statusText = typeof parsedData.content === 'string'
                                      ? parsedData.content
                                      : JSON.stringify(parsedData.content ?? '');
                                  if (statusText) workflowStore.addLog(statusText, 'info');
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
