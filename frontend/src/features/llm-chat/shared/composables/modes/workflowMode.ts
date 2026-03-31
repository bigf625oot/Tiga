import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import { useSmartQALayout } from '@/features/llm-chat/shared/composables/useSmartQALayout';
import type { Message, AgentEvent, AgentExecutionPlan } from '@/features/llm-chat/shared/types';
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
                
                // Sync to assistantMsg.steps so PlanProcessor can render it in the chat bubble
                if (!assistantMsg.steps) assistantMsg.steps = [];
                taskList.forEach((t: any, idx: number) => {
                    let title = t.title || t.name || t.description || `步骤 ${idx + 1}`;
                    if (typeof title !== 'string') {
                        title = JSON.stringify(title);
                    }
                    // Only add if not already present
                    const stepId = String(t.id || t.task_id || idx);
                    if (!assistantMsg.steps!.some((s: any) => String(s.id) === stepId)) {
                        assistantMsg.steps!.push({
                            step: idx,
                            content: title,
                            id: stepId,
                            status: 'pending'
                        } as any);
                    }
                });
            }
        },
        plan: (data: any) => {
            try {
                const planRaw = data.content || data.plan;
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
                            id: String(t.id || t.task_id || idx),
                            status: 'pending'
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
        task_start: (data: any) => {
            workflowStore.handleAgentEvent(data as AgentEvent);
            // Ensure right panel opens when task starts in solo mode
            const { isRightCollapsed } = useSmartQALayout();
            if (isRightCollapsed.value) {
                isRightCollapsed.value = false;
            }
            
            // 同步更新左侧步骤状态
            let taskId = typeof data === 'string' ? null : (data.task_id || data.content?.task_id || data.id);
            if (!taskId && typeof data === 'object' && data.content && typeof data.content === 'object') {
                taskId = data.content.id;
            }
            if (taskId && assistantMsg.steps) {
                const step = assistantMsg.steps.find((s: any) => String(s.id) === String(taskId));
                if (step) step.status = 'running';
            }
        },
        execute_start: () => {
            const pendingTask = workflowStore.tasks.find((t: any) => t.status === 'pending');
            if (pendingTask) workflowStore.handleTaskStarted({ task_id: pendingTask.id, task_name: pendingTask.name });
        },
        subtask_done: (data: any) => {
            let finalOutput = data;
            let taskId = typeof data === 'string' ? null : (data.task_id || data.content?.task_id || data.id);
            if (!taskId && typeof data === 'object' && data.content && typeof data.content === 'object') {
                taskId = data.content.id;
            }
            
            if (typeof finalOutput !== 'string') {
                const rawContent = finalOutput.content;
                finalOutput = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent != null ? String(rawContent) : '');
            }
            const runningTask = workflowStore.tasks.find((t: any) => t.status === 'running' || String(t.id) === String(taskId));
            if (runningTask) {
                workflowStore.handleWorkflowEvent({ type: 'task_content', task_id: runningTask.id, content: finalOutput });
                workflowStore.handleWorkflowEvent({ type: 'task_completed', task_id: runningTask.id });
                
                // 同步更新左侧步骤状态
                if (assistantMsg.steps) {
                    const step = assistantMsg.steps.find((s: any) => String(s.id) === String(runningTask.id));
                    if (step) step.status = 'done';
                }
            } else if (taskId && assistantMsg.steps) {
                // Fallback: update left side even if workflowStore didn't match
                const step = assistantMsg.steps.find((s: any) => String(s.id) === String(taskId));
                if (step) step.status = 'done';
            }
            
            // Append instead of overwrite to preserve incremental content
            if (finalOutput && !assistantMsg.content?.includes(finalOutput)) {
                assistantMsg.content = (assistantMsg.content || '') + (assistantMsg.content ? '\n\n' : '') + finalOutput;
            }
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
            
            const toolCallId = info.tool_call_id || Math.random().toString();
            // 尝试获取 task_id 以便精确绑定
            const taskId = info.task_id || data.task_id || workflowStore.tasks.find(t => t.status === 'running')?.id;
            
            assistantMsg.tools.push({
                id: toolCallId,
                name: info.tool || info.name || 'unknown_tool',
                args: info.args || info.arguments || {},
                status: 'running',
                startTime: Date.now(),
                task_id: taskId
            });
        },
        tool_start: function(data) { this.tool_call?.(data); },
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
                const toolId = info.tool_call_id;
                
                // 优先使用 ID 匹配，降级使用名称匹配
                let tool = null;
                if (toolId) {
                    tool = assistantMsg.tools.find(t => t.id === toolId);
                }
                if (!tool) {
                    tool = [...assistantMsg.tools].reverse().find(t => t.name === toolName && t.status === 'running');
                }
                
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
        tool_end: function(data) { this.tool_output?.(data); },
        tool_error: function(data) { this.tool_output?.(data); },
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
        task_started: (data: any) => {
            workflowStore.handleWorkflowEvent(data);
            const { isRightCollapsed } = useSmartQALayout();
            if (isRightCollapsed.value) isRightCollapsed.value = false;
        },
        task_content: (data: any) => {
            workflowStore.handleWorkflowEvent(data);
            // 增量同步到左侧对话区域
            const textChunk = typeof data === 'string' ? data : (data.content || '');
            if (textChunk && !assistantMsg.content?.endsWith(textChunk)) {
                assistantMsg.content = (assistantMsg.content || '') + textChunk;
            }
        },
        task_completed: (data: any) => workflowStore.handleWorkflowEvent(data),
        task_failed: (data: any) => {
            workflowStore.handleWorkflowEvent(data);
            let taskId = typeof data === 'string' ? null : (data.task_id || data.content?.task_id || data.id);
            if (!taskId && typeof data === 'object' && data.content && typeof data.content === 'object') {
                taskId = data.content.id;
            }
            if (taskId && assistantMsg.steps) {
                const step = assistantMsg.steps.find((s: any) => String(s.id) === String(taskId));
                if (step) step.status = 'error';
            }
        },
        task_tool_call: (data: any) => workflowStore.handleWorkflowEvent(data),
        artifacts: (data: any) => workflowStore.handleWorkflowEvent(data),
    };
}
