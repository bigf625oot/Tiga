import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import type { Message, AgentEvent, AgentExecutionPlan } from '../../types';
import type { StreamEventHandlers } from './baseHandlers';

export function createWorkflowHandlers(
    assistantMsg: Message,
    workflowStore: ReturnType<typeof useWorkflowStore>
): Partial<StreamEventHandlers> {
    return {
        plan_created: (data: any) => {
            let inner = (data.content ?? data) as any;
            if (typeof inner === 'string') {
                try {
                    inner = JSON.parse(inner);
                } catch {
                    // ignore
                }
            }
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
                        let title = t.title || t.name || t.description || `步骤 ${idx + 1}`;
                        if (typeof title !== 'string') {
                            title = JSON.stringify(title);
                        }
                        assistantMsg.steps!.push({
                            step: idx,
                            content: title,
                            id: t.id || t.task_id || String(idx),
                        } as any);
                    });
                }
            } catch (e) { console.warn('[useChatSession] plan event parse failed', e); }
        },
        text: (data: any) => {
            let textChunk = data;
            if (typeof textChunk !== 'string') {
                const rawContent = textChunk.content;
                textChunk = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent || '');
            }
            assistantMsg.content = (assistantMsg.content || '') + textChunk;
            const runningTask = workflowStore.tasks.find((t: any) => t.status === 'running');
            if (runningTask) {
                workflowStore.handleWorkflowEvent({ type: 'task_content', task_id: runningTask.id, content: textChunk });
            }
        },
        task_start: (data: any) => workflowStore.handleAgentEvent(data as AgentEvent),
        execute_start: () => {
            const pendingTask = workflowStore.tasks.find((t: any) => t.status === 'pending');
            if (pendingTask) workflowStore.handleTaskStarted({ task_id: pendingTask.id, task_name: pendingTask.name });
        },
        subtask_done: (data: any) => {
            let finalOutput = data;
            if (typeof finalOutput !== 'string') {
                const rawContent = finalOutput.content;
                finalOutput = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent != null ? String(rawContent) : '');
            }
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
            let info = data.content || data;
            if (typeof info === 'string') {
                try {
                    info = JSON.parse(info);
                } catch {
                    info = { tool: info };
                }
            }
            assistantMsg.tools.push({
                id: info.tool_call_id || Math.random().toString(),
                name: info.tool || info.name || 'unknown_tool',
                args: info.args || info.arguments || {},
                status: 'running',
                startTime: Date.now()
            });
        },
        call: function(data) { this.tool_call?.(data); },
        tool_output: (data: any) => {
            workflowStore.handleAgentEvent(data as AgentEvent);
            if (assistantMsg.tools) {
                let info = data.content || data;
                if (typeof info === 'string') {
                    try {
                        info = JSON.parse(info);
                    } catch {
                        info = { tool: "unknown_tool", output: info };
                    }
                }
                const toolName = info.tool || info.name;
                const tool = [...assistantMsg.tools].reverse().find(t => t.name === toolName && t.status === 'running');
                if (tool) {
                    tool.status = info.is_error ? 'error' : 'success';
                    tool.result = typeof (info.result || info.output) === 'string' 
                        ? (info.result || info.output) 
                        : JSON.stringify(info.result || info.output);
                    if (tool.startTime) {
                        tool.duration = Date.now() - tool.startTime;
                    }
                }
            }
        },
        result: function(data) { this.tool_output?.(data); },
        artifact: (data: any) => workflowStore.handleAgentEvent(data as AgentEvent),
        status: (data: any) => {
            let statusText = data;
            if (typeof statusText !== 'string') {
                const rawContent = statusText.content;
                statusText = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent != null ? String(rawContent) : JSON.stringify(statusText));
            }
            if (statusText) workflowStore.addLog(statusText, 'info');
        },
        summary: (data: any) => {
            let summaryText = data;
            if (typeof summaryText !== 'string') {
                const rawContent = summaryText.content;
                summaryText = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent != null ? String(rawContent) : '');
            }
            if (summaryText) assistantMsg.content = summaryText;
        },
        step: (data: any) => {
            if (!assistantMsg.steps) assistantMsg.steps = [];
            let stepData = data;
            if (typeof stepData !== 'string') {
                const rawContent = stepData.content;
                stepData = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent != null ? String(rawContent) : JSON.stringify(stepData));
            }
            assistantMsg.steps.push(stepData);
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
