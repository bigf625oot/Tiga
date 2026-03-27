import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import type { Message, AgentEvent, AgentExecutionPlan } from '../../types';
import type { StreamEventHandlers } from './baseHandlers';

export function createWorkflowHandlers(
    assistantMsg: Message,
    workflowStore: ReturnType<typeof useWorkflowStore>
): Partial<StreamEventHandlers> {
    return {
        plan_created: (data: any) => {
            const inner = (data.content ?? data) as any;
            const taskList: any[] = inner?.tasks ?? inner?.steps ?? [];
            if (taskList.length > 0) {
                workflowStore.initFromAgentPlan({
                    ...inner,
                    tasks: taskList,
                } as AgentExecutionPlan);
            }
        },
        plan: (data: any) => {
            try {
                const planRaw = data.content;
                const planData = typeof planRaw === 'string' ? JSON.parse(planRaw) : (planRaw ?? data);
                const taskList: any[] = planData?.tasks ?? planData?.steps ?? [];
                if (taskList.length > 0) {
                    workflowStore.initFromAgentPlan({ ...planData, tasks: taskList } as AgentExecutionPlan);
                    if (!assistantMsg.steps) assistantMsg.steps = [];
                    taskList.forEach((t: any, idx: number) => {
                        assistantMsg.steps!.push({
                            step: idx,
                            content: t.title || t.name || t.description || `步骤 ${idx + 1}`,
                            id: t.id || t.task_id || String(idx),
                        } as any);
                    });
                }
            } catch (e) { console.warn('[useChatSession] plan event parse failed', e); }
        },
        task_start: (data: any) => workflowStore.handleAgentEvent(data as AgentEvent),
        execute_start: () => {
            const pendingTask = workflowStore.tasks.find((t: any) => t.status === 'pending');
            if (pendingTask) workflowStore.handleTaskStarted({ task_id: pendingTask.id, task_name: pendingTask.name });
        },
        subtask_done: (data: any) => {
            const rawContent = data.content;
            const finalOutput = typeof rawContent === 'string' ? rawContent : (rawContent != null ? JSON.stringify(rawContent) : '');
            const runningTask = workflowStore.tasks.find((t: any) => t.status === 'running');
            if (runningTask) {
                workflowStore.handleWorkflowEvent({ type: 'task_content', task_id: runningTask.id, content: finalOutput });
                workflowStore.handleWorkflowEvent({ type: 'task_completed', task_id: runningTask.id });
            }
            assistantMsg.content = finalOutput;
        },
        tool_call: (data: any) => {
            workflowStore.handleAgentEvent(data as AgentEvent);
            if (!assistantMsg.tools) assistantMsg.tools = [];
            const info = data.content || data;
            assistantMsg.tools.push({
                id: info.tool_call_id || Math.random().toString(),
                name: info.tool || info.name || 'unknown_tool',
                args: info.args || info.arguments || {},
                status: 'running'
            });
        },
        call: function(data) { this.tool_call(data); },
        tool_output: (data: any) => {
            workflowStore.handleAgentEvent(data as AgentEvent);
            if (assistantMsg.tools) {
                const info = data.content || data;
                const toolName = info.tool || info.name;
                const tool = [...assistantMsg.tools].reverse().find(t => t.name === toolName && t.status === 'running');
                if (tool) {
                    tool.status = info.is_error ? 'error' : 'success';
                    tool.result = typeof (info.result || info.output) === 'string' 
                        ? (info.result || info.output) 
                        : JSON.stringify(info.result || info.output);
                }
            }
        },
        result: function(data) { this.tool_output(data); },
        artifact: (data: any) => workflowStore.handleAgentEvent(data as AgentEvent),
        status: (data: any) => {
            const statusText = typeof data.content === 'string' ? data.content : JSON.stringify(data.content ?? '');
            if (statusText) workflowStore.addLog(statusText, 'info');
        },
        summary: (data: any) => {
            const summaryText = typeof data.content === 'string' ? data.content : '';
            if (summaryText) assistantMsg.content = summaryText;
        },
        step: (data: any) => {
            if (!assistantMsg.steps) assistantMsg.steps = [];
            assistantMsg.steps.push(data);
        },
        // 遗留兼容
        plan_step: (data: any) => workflowStore.handleWorkflowEvent(data),
        task_started: (data: any) => workflowStore.handleWorkflowEvent(data),
        task_content: (data: any) => workflowStore.handleWorkflowEvent(data),
        task_completed: (data: any) => workflowStore.handleWorkflowEvent(data),
        task_failed: (data: any) => workflowStore.handleWorkflowEvent(data),
        task_tool_call: (data: any) => workflowStore.handleWorkflowEvent(data),
        artifacts: (data: any) => workflowStore.handleWorkflowEvent(data),
    };
}
