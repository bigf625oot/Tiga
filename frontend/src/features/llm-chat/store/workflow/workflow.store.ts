import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import type {
    AgentEvent, AgentExecutionPlan, AgentToolCallInfo,
    AgentObservationInfo, AgentArtifactCard, AgentTaskStartInfo,
} from '@/features/llm-chat/shared/types';
import { STORAGE_KEYS } from '@/features/llm-chat/shared/constants';

export interface TaskToolCall {
    tool_name: string;
    tool_args?: Record<string, any>;
    status: 'running' | 'completed' | 'failed';
    result?: string;
}

export interface TaskArtifact {
    name: string;
    url: string;
    type: string;
    size?: number;
}

export interface WorkflowTask {
    id: string;
    name: string;
    description?: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number; // 0-100
    startTime?: number;
    endTime?: number;
    logs: string[];
    output: string;          // realtime streamed content for this task
    toolCalls: TaskToolCall[];
    children?: WorkflowTask[];
    dependencies?: string[]; // IDs
    priority?: 'high' | 'medium' | 'low';
    estimatedTime?: number;
    requiredResources?: string[];
}

export interface WorkflowLog {
    timestamp: number;
    level: 'info' | 'warning' | 'error' | 'success';
    message: string;
    step?: string;
}

export interface WorkflowDocument {
    id: string;
    title: string;
    content: string;
    /**
     * @description 文档的 MIME/语言类型（如 markdown, json, python 等）。
     * @trade_off 设为可选（`?`）而非必填，是基于对存量本地化状态（LocalStorage `workflow-${sid}`）
     * 的平滑兼容（向后兼容）。下游渲染层需对 `undefined` 状态做默认降级处理（如默认 'markdown'），
     * 以保证分布式及多版本迭代下的架构确定性。
     */
    type?: string;
    step?: string;
    createdAt: number;
}

export const useWorkflowStore = defineStore('workflow', () => {
    const isRunning = ref(false);
    const tasks = ref<WorkflowTask[]>([]);
    const logs = ref<WorkflowLog[]>([]);
    const documents = ref<WorkflowDocument[]>([]);
    const currentStep = ref<string>('');
    const sessionId = ref<string>('');
    const executeBuffer = ref<string>('');
    const artifacts = ref<TaskArtifact[]>([]);

    // Graph State
    const graph = ref<{ nodes: any[], edges: any[] }>({ nodes: [], edges: [] });
    const selectedTaskId = ref<string | null>(null);

    // Stats
    const totalTasks = computed(() => {
        let count = 0;
        const traverse = (list: WorkflowTask[]) => {
            count += list.length;
            list.forEach(t => { if (t.children) traverse(t.children); });
        };
        traverse(tasks.value);
        return count;
    });

    const completedTasks = computed(() => {
        let count = 0;
        const traverse = (list: WorkflowTask[]) => {
            count += list.filter(t => t.status === 'completed').length;
            list.forEach(t => { if (t.children) traverse(t.children); });
        };
        traverse(tasks.value);
        return count;
    });

    const progress = computed(() => {
        if (totalTasks.value === 0) return 0;
        return Math.round((completedTasks.value / totalTasks.value) * 100);
    });

    // Actions
    const initWorkflow = (sid: string, initialState?: any) => {
        sessionId.value = sid;
        const saved = localStorage.getItem(`workflow-${sid}`);

        let data = null;
        if (initialState) {
            data = initialState;
        } else if (saved) {
            try {
                data = JSON.parse(saved);
            } catch (e) {
                console.error("Failed to restore workflow state", e);
            }
        }

        graph.value = { nodes: [], edges: [] };
        selectedTaskId.value = null;

        if (data) {
            tasks.value = data.tasks || [];
            logs.value = data.logs || [];
            documents.value = data.documents || [];
            currentStep.value = data.currentStep || '';
            artifacts.value = data.artifacts || [];
        } else {
            tasks.value = [];
            logs.value = [];
            documents.value = [];
            artifacts.value = [];
        }
        tasks.value.forEach(t => updateGraph(t));
        isRunning.value = false;
        executeBuffer.value = '';
    };

    const saveStateToBackend = async () => {
        if (!sessionId.value) return;
        try {
            const state = {
                tasks: tasks.value,
                logs: logs.value,
                documents: documents.value,
                currentStep: currentStep.value
            };
            await fetch(`/api/v1/chat/sessions/${sessionId.value}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workflow_state: state })
            });
        } catch (e) {
            console.error("Failed to save workflow state", e);
        }
    };

    let saveTimeout: any;
    // 增加节流保存逻辑，避免在高频输出时阻塞，同时允许 solo 模式在流式输出中增量持久化
    const debouncedSave = () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(saveStateToBackend, 1500);
    };

    watch([tasks, logs, isRunning], () => {
        if (sessionId.value) {
            localStorage.setItem(STORAGE_KEYS.WORKFLOW_STATE(sessionId.value), JSON.stringify({
                tasks: tasks.value,
                logs: logs.value,
                isRunning: isRunning.value,
                currentStep: currentStep.value
            }));
            // Allow saving even when running for real-time persistence (optimistic locking style)
            debouncedSave();
        }
    }, { deep: true });

    // 工作流结束时触发一次权威持久化，确保最终状态落地后端
    watch(isRunning, (running) => {
        if (!running && sessionId.value) {
            debouncedSave();
        }
    });

    const addLog = (message: string, level: WorkflowLog['level'] = 'info', step?: string) => {
        logs.value.push({
            timestamp: Date.now(),
            level,
            message,
            step
        });
    };

    const appendOutput = (output: string, step?: string) => {
        if (!output) return;
        const runningTask = tasks.value.find(t => t.status === 'running');
        if (runningTask) {
            runningTask.logs.push(output);
            runningTask.output = (runningTask.output || '') + output;
            updateGraph(runningTask);
            return;
        }
        const lastTask = tasks.value[tasks.value.length - 1];
        if (lastTask) {
            lastTask.logs.push(output);
            lastTask.output = (lastTask.output || '') + output;
            updateGraph(lastTask);
            return;
        }
        // No tasks (solo/quick mode): accumulate into executeBuffer so code editor can display it
        executeBuffer.value += output;
        addLog(output, 'info', step);
    };

    const clearLogs = () => {
        logs.value = [];
    };

    const resetArtifacts = () => {
        artifacts.value = [];
    };

    const resetWorkflow = () => {
        sessionId.value = '';
        tasks.value = [];
        logs.value = [];
        documents.value = [];
        currentStep.value = '';
        executeBuffer.value = '';
        isRunning.value = false;
        artifacts.value = [];
    };

    const updateGraph = (task: WorkflowTask) => {
        const existingNodeIndex = graph.value.nodes.findIndex(n => n.id === task.id);

        const nodeData = {
            label: task.name,
            status: task.status,
            progress: task.progress,
            logs: task.logs,
            output: task.output,       // ← 节点卡片显示输出字符数需要
            description: task.description,
            toolCalls: task.toolCalls,
            children: task.children,
            startTime: task.startTime,
            endTime: task.endTime
        };

        if (existingNodeIndex !== -1) {
            // 必须替换整个节点对象而非原地 mutate data，
            // VueFlow 通过 object identity 追踪变更：同一引用会被跳过，导致节点视觉不刷新。
            graph.value.nodes[existingNodeIndex] = {
                ...graph.value.nodes[existingNodeIndex],
                data: nodeData,
            };
        } else {
            const taskIndex = tasks.value.findIndex(t => t.id === task.id);
            const y = (taskIndex !== -1 ? taskIndex : graph.value.nodes.length) * 160;
            graph.value.nodes.push({
                id: task.id,
                type: 'custom',
                data: nodeData,
                position: { x: 250, y: y }
            });
        }

        // Update edges: strictly follow backend dependencies
        const newEdges: any[] = [];
        tasks.value.forEach((t) => {
            if (t.dependencies && t.dependencies.length > 0) {
                t.dependencies.forEach(depId => {
                    const edgeId = `e-${depId}-${t.id}`;
                    newEdges.push({
                        id: edgeId,
                        source: depId,
                        target: t.id,
                        animated: t.status === 'running' || t.status === 'pending',
                        style: { stroke: t.status === 'completed' ? '#22c55e' : '#94a3b8', strokeWidth: 2 }
                    });
                });
            }
        });
        graph.value.edges = newEdges;
    };

    const updateTaskStatus = (stepName: string, status: WorkflowTask['status'], output?: string) => {
        let taskIndex = -1;

        if (status === 'running') {
            const formattedName = formatStepName(stepName);
            taskIndex = tasks.value.findIndex(t => t.status === 'pending' && t.name === formattedName);

            if (taskIndex === -1) {
                 for (let i = tasks.value.length - 1; i >= 0; i--) {
                    if (tasks.value[i].id.startsWith(stepName) && tasks.value[i].status === 'running') {
                        taskIndex = i;
                        break;
                    }
                }
            }
        } else {
             for (let i = tasks.value.length - 1; i >= 0; i--) {
                if (tasks.value[i].id.startsWith(stepName) || (tasks.value[i].status === 'running' && tasks.value[i].name === formatStepName(stepName))) {
                    taskIndex = i;
                    break;
                }
            }
        }

        let task = taskIndex !== -1 ? tasks.value[taskIndex] : null;
        let createNew = false;

        if (!task) {
            createNew = true;
        } else if (status === 'running' && (task.status === 'completed' || task.status === 'failed')) {
            createNew = true;
        }

        if (createNew) {
            const count = tasks.value.filter(t => t.id.startsWith(stepName)).length;
            const newId = count > 0 ? `${stepName}-${count + 1}` : stepName;

            task = {
                id: newId,
                name: formatStepName(stepName) + (count > 0 ? ` (${count + 1})` : ''),
                status: 'pending',
                progress: 0,
                logs: [],
                output: '',
                toolCalls: [],
                priority: 'medium'
            };
            tasks.value.push(task);
        }

        if (task) {
            if (status === 'running' && task.status !== 'running') {
                task.status = 'running';
                task.startTime = Date.now();
            } else if (status === 'completed' || status === 'failed') {
                task.status = status;
                task.endTime = Date.now();
                task.progress = 100;
            }

            if (output) {
                task.logs.push(output);
                // 修复大模型流式文本未正确归入 output 导致在日志区降级展示碎片的 bug
                if (typeof output === 'string') {
                    task.output = (task.output || '') + output;
                } else {
                    task.output = (task.output || '') + JSON.stringify(output) + '\n';
                }
            }

            updateGraph(task);
        }
    };

    const formatStepName = (step: string) => {
        const map: Record<string, string> = {
            'plan': '任务规划 (Planning)',
            'retrieve': '知识检索 (Retrieval)',
            'execute': '智能执行 (Execution)',
            'persist': '结果保存 (Persistence)',
            'finish': '完成 (Finish)'
        };
        return map[step] || step;
    };

    const runWorkflow = async (message: string, agentId?: string, attachments?: string[]) => {
        if (isRunning.value) return;
        isRunning.value = true;
        tasks.value = [];
        logs.value = [];
        documents.value = [];
        artifacts.value = [];
        executeBuffer.value = '';

        try {
            const response = await fetch('/api/v1/agent-workflows/run_stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId.value,
                    message: message,
                    agent_id: agentId,
                    mode: 'dynamic',
                    params: { attachments }
                })
            });

            if (!response.ok) throw new Error(response.statusText);

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;

                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.slice(6);
                            if (dataStr === '[DONE]') {
                                isRunning.value = false;
                                addLog('Workflow finished', 'success');
                                return;
                            }

                            try {
                                const data = JSON.parse(dataStr);
                                handleEvent(data);
                            } catch (e) {
                                console.error('JSON Parse Error', e);
                            }
                        }
                    }
                }
            }
            isRunning.value = false;
            addLog('Connection closed', 'warning');
        } catch (e: any) {
            addLog(`Error: ${e.message}`, 'error');
            isRunning.value = false;
        }
    };

    // --- Per-task event handlers ---

    const _findTaskById = (taskId: string): WorkflowTask | undefined => {
        return tasks.value.find(t => t.id === taskId);
    };

    const handleTaskStarted = (data: any) => {
        const taskId = data.task_id;
        // Try to find a matching pending task from plan (by task name if id mismatch)
        let task = _findTaskById(taskId);
        if (!task) {
            // Try to find by name match (plan tasks may have different ids)
            task = tasks.value.find(t => t.status === 'pending' && t.name === data.task_name);
        }

        if (task) {
            task.id = taskId; // align id
            task.status = 'running';
            task.startTime = Date.now();
            task.output = '';
            task.toolCalls = [];
            updateGraph(task);
        } else {
            // Task not in plan yet — create it
            const newTask: WorkflowTask = {
                id: taskId,
                name: data.task_name || taskId,
                description: data.task_description || '',
                status: 'running',
                progress: 0,
                logs: [],
                output: '',
                toolCalls: [],
                startTime: Date.now()
            };
            tasks.value.push(newTask);
            updateGraph(newTask);
        }
    };

    const handleTaskContent = (data: any) => {
        const task = _findTaskById(data.task_id);
        if (task && data.content) {
            task.output += data.content;
        }
    };

    const handleTaskToolCall = (data: any) => {
        const task = _findTaskById(data.task_id);
        if (!task || !data.tool) return;
        const toolInfo = data.tool;

        // Find existing tool call entry (to update status)
        const existingIdx = task.toolCalls.findIndex(tc =>
            tc.tool_name === toolInfo.tool_name && tc.status === 'running'
        );

        if (toolInfo.status === 'started') {
            task.toolCalls.push({
                tool_name: toolInfo.tool_name,
                tool_args: toolInfo.tool_args,
                status: 'running'
            });
        } else if (existingIdx !== -1) {
            task.toolCalls[existingIdx].status = toolInfo.status === 'completed' ? 'completed' : 'failed';
            task.toolCalls[existingIdx].result = toolInfo.result;
        }
    };

    const handleTaskCompleted = (data: any) => {
        const task = _findTaskById(data.task_id);
        if (task) {
            task.status = 'completed';
            task.endTime = Date.now();
            task.progress = 100;
            updateGraph(task);

            // Save output as document if non-empty
            const content = (task.output || '').trim();
            if (content) {
                let docType = 'markdown';
                let docContent = content;
                const match = content.match(/^```(\w+)\s*([\s\S]*?)```$/);
                if (match) {
                    docType = match[1];
                    docContent = match[2].trim();
                }

                const title = deriveDocumentTitle(content) || task.name;
                documents.value.unshift({
                    id: `doc-${Date.now()}-${Math.random().toString(16).slice(2)}`,
                    title,
                    content: docContent,
                    type: docType,
                    step: task.name,
                    createdAt: Date.now()
                });
            }
        }
    };

    const handleTaskFailed = (data: any) => {
        const task = _findTaskById(data.task_id);
        if (task) {
            task.status = 'failed';
            task.endTime = Date.now();
            task.progress = 100;
            if (data.error) task.logs.push(`错误: ${data.error}`);
            updateGraph(task);
        }
    };

    const handleArtifacts = (data: any) => {
        if (Array.isArray(data.files)) {
            artifacts.value = data.files;
            addLog(`产出物清单已生成: ${data.files.length} 个文件`, 'success');
        }
    };

    const handleEvent = (data: any) => {
        if (data.system) {
            addLog(data.output, data.status === 'failed' ? 'error' : 'info');
            return;
        }

        // --- New per-task event types ---
        if (data.type === 'task_started') { handleTaskStarted(data); return; }
        if (data.type === 'task_content') { handleTaskContent(data); return; }
        if (data.type === 'task_tool_call') { handleTaskToolCall(data); return; }
        if (data.type === 'task_completed') { handleTaskCompleted(data); return; }
        if (data.type === 'task_failed') { handleTaskFailed(data); return; }
        if (data.type === 'artifacts') { handleArtifacts(data); return; }

        // --- Legacy tool_call (step-based) ---
        if (data.type === 'tool_call' || data.type === 'tool_start') {
            const toolInfo = data.tool || data.content || {};
            const logMsg = (toolInfo.status === 'started' || !toolInfo.status)
                ? `🔧 调用工具: ${toolInfo.tool_name || toolInfo.tool || toolInfo.name}\n参数: ${JSON.stringify(toolInfo.tool_args || toolInfo.args || toolInfo.arguments)}`
                : `✅ 工具 ${toolInfo.tool_name || toolInfo.tool || toolInfo.name} 执行完成\n结果: ${toolInfo.result || '无'}`;
            
            // 尝试找到最近的任务
            const activeTask = tasks.value.find(t => t.status === 'running') || tasks.value[tasks.value.length - 1];
            if (activeTask) {
                activeTask.logs.push(logMsg);
            } else {
                addLog(logMsg, (toolInfo.status === 'started' || !toolInfo.status) ? 'info' : 'success', data.step || 'execute');
            }
            return;
        }

        if (data.type === 'tool_output' || data.type === 'tool_end' || data.type === 'tool_error') {
            const toolInfo = data.content || data || {};
            const isError = toolInfo.is_error || data.type === 'tool_error';
            const logMsg = isError
                ? `❌ 工具 ${toolInfo.tool || toolInfo.name} 执行失败: ${toolInfo.logs?.join('\n') || toolInfo.error}`
                : `✅ 工具 ${toolInfo.tool || toolInfo.name} 执行成功`;
            
            const activeTask = tasks.value.find(t => t.status === 'running') || tasks.value[tasks.value.length - 1];
            if (activeTask) {
                activeTask.logs.push(logMsg);
            } else {
                addLog(logMsg, isError ? 'error' : 'success', data.step || 'execute');
            }
            return;
        }

        currentStep.value = data.step;

        // Handle Plan Update (legacy + new "plan" type)
        if ((data.step === 'plan' && data.status === 'success' && data.plan) || (data.type === 'plan' && data.plan)) {
            const planData = data.plan;
            tasks.value = tasks.value.filter(t => t.status !== 'pending');

            // New structured plan format from unified_workflow
            const planTasks = planData.tasks || planData.steps || [];
            planTasks.forEach((step: any) => {
                const taskName = step.name || step.description || formatStepName(step.operation);
                tasks.value.push({
                    id: step.id ? `${step.id}` : `future-${Math.random().toString(16).slice(2)}`,
                    name: taskName,
                    description: step.description || step.name || '',
                    status: 'pending',
                    progress: 0,
                    logs: [],
                    output: '',
                    toolCalls: [],
                    priority: 'medium',
                    dependencies: step.dependencies?.map(String) || [],
                    estimatedTime: step.estimated_time,
                    requiredResources: step.required_resources || []
                });
            });

            // 规划完成后立即将所有 pending 任务写入 graph（含 edges），
            // 避免等到 task_started 才逐一注册节点导致 edges 无法渲染
            graph.value = { nodes: [], edges: [] };
            tasks.value.forEach(t => updateGraph(t));

            if (planData.reasoning) {
                addLog(`规划思路: ${planData.reasoning}`, 'info', 'plan');
            }
            addLog(`任务规划已生成: ${planTasks.length} 个步骤`, 'success', 'plan');
            return;
        }

        if (data.status === 'running') {
            updateTaskStatus(data.step, 'running', data.output);
            if (data.step === 'execute' && typeof data.output === 'string') {
                if (data.type !== 'reasoning' && !data.output.includes('<think>')) {
                    executeBuffer.value += data.output;
                }
            }
        } else if (data.status === 'success') {
            updateTaskStatus(data.step, 'completed', data.output);
            addLog(`Step ${data.step} completed`, 'success', data.step);
            if (data.step === 'execute') {
                const content = (executeBuffer.value || '').trim();
                if (content) {
                    const title = deriveDocumentTitle(content);
                    documents.value.unshift({
                        id: `doc-${Date.now()}-${Math.random().toString(16).slice(2)}`,
                        title,
                        content,
                        type: 'markdown', // 补充显式类型，增强下游确定性
                        step: 'execute',
                        createdAt: Date.now()
                    });
                }
                executeBuffer.value = '';
            }
        } else if (data.status === 'failed') {
            updateTaskStatus(data.step, 'failed', data.output);
            addLog(`Step ${data.step} failed: ${data.output}`, 'error', data.step);
            if (data.step === 'execute') {
                executeBuffer.value = '';
            }
        }
    };

    const handleWorkflowEvent = (data: any) => {
        if (data == null) return;
        if (typeof data === 'string') {
            addLog(data, 'info', 'status');
            return;
        }
        if (typeof data === 'object' && (data.step || data.system || data.status || data.output || data.plan || data.type)) {
            handleEvent(data);
            return;
        }
        try {
            addLog(JSON.stringify(data, null, 2), 'info', 'status');
        } catch {
            addLog(String(data), 'info', 'status');
        }
    };

    const deriveDocumentTitle = (content: string) => {
        const m = content.match(/^\s{0,3}#{1,6}\s+(.+?)\s*$/m);
        if (m && m[1]) return m[1].trim().slice(0, 40);
        const firstLine = content.split('\n').find(l => l.trim()) || '';
        if (firstLine) return firstLine.trim().slice(0, 40);
        return '任务文档';
    };

    const stopWorkflow = () => {
        isRunning.value = false;
        addLog('Workflow stopped by user', 'warning');
    };

    const updatePlanFromBackend = (steps: Array<{ title?: string, name?: string, id?: string, description?: string, status: string, assigned_agent_role?: string }>) => {
        const newTasks: WorkflowTask[] = [];

        steps.forEach((step, index) => {
            const stepName = step.title || step.name || `Task ${index + 1}`;
            const existingTask = tasks.value.find(t => t.name === stepName);

            if (existingTask) {
                let newStatus: WorkflowTask['status'] = 'pending';
                const s = step.status.toLowerCase();
                if (s === 'running') newStatus = 'running';
                else if (s === 'completed') newStatus = 'completed';
                else if (s === 'failed') newStatus = 'failed';

                if (newStatus === 'running' && existingTask.status !== 'running') {
                    existingTask.startTime = Date.now();
                }
                if ((newStatus === 'completed' || newStatus === 'failed') && existingTask.status !== 'completed' && existingTask.status !== 'failed') {
                    existingTask.endTime = Date.now();
                    existingTask.progress = 100;
                }

                existingTask.status = newStatus;
                existingTask.description = step.description || existingTask.description;
                newTasks.push(existingTask);
            } else {
                let newStatus: WorkflowTask['status'] = 'pending';
                const s = step.status.toLowerCase();
                if (s === 'running') newStatus = 'running';
                else if (s === 'completed') newStatus = 'completed';
                else if (s === 'failed') newStatus = 'failed';

                newTasks.push({
                    id: step.id ? `step-${step.id}` : `step-${index}-${Date.now()}`,
                    name: stepName,
                    description: step.description,
                    status: newStatus,
                    progress: newStatus === 'completed' ? 100 : 0,
                    logs: [],
                    output: '',
                    toolCalls: [],
                    startTime: newStatus === 'running' ? Date.now() : undefined,
                    endTime: (newStatus === 'completed' || newStatus === 'failed') ? Date.now() : undefined
                });
            }
        });

        tasks.value = newTasks;
        graph.value = { nodes: [], edges: [] };
        tasks.value.forEach(t => updateGraph(t));
        addLog(`任务计划已更新: ${steps.length} 个步骤`, 'info', 'plan');
    };

    // ── AgentEvent 协议（NexusExecutor 路径）──

    const initFromAgentPlan = (plan: AgentExecutionPlan) => {
        tasks.value = plan.tasks.map((t: any) => ({
            // 兼容 id / task_id 两种 key（不同后端路径差异）
            id: t.id || t.task_id || `plan-${Math.random().toString(16).slice(2)}`,
            // 兼容 title / name 两种字段（后端历史差异）
            name: t.title || t.name || t.id || t.task_id || '未命名任务',
            description: t.description || '',
            status: (t.status as WorkflowTask['status']) || 'pending',
            progress: 0,
            logs: [],
            output: '',
            toolCalls: [],
            dependencies: t.dependencies?.map(String) || [],
        }));
        tasks.value.forEach(t => updateGraph(t));
        if (plan.reasoning) {
            addLog(`规划完成：${plan.reasoning}`, 'info', 'plan');
        }
        addLog(`任务计划已生成: ${plan.tasks.length} 个步骤`, 'success', 'plan');
    };

    const handleAgentEvent = (event: AgentEvent) => {
        switch (event.type) {
            // task_start：pending/running/completed/failed 状态变更
            case 'task_start': {
                const info = event.content as AgentTaskStartInfo;
                let task = tasks.value.find(t => t.id === info.task_id);

                if (!task) {
                    // 兜底创建：plan_created 未到达或 task_id 与 plan 不对齐时，
                    // 动态建立任务条目，与 handleTaskStarted（legacy 路径）行为对齐。
                    task = {
                        id: info.task_id,
                        name: info.title || info.task_id,
                        status: 'pending',
                        progress: 0,
                        logs: [],
                        output: '',
                        toolCalls: [],
                    };
                    tasks.value.push(task);
                    updateGraph(task);
                }

                const prevStatus = task.status;
                task.status = info.status as WorkflowTask['status'];
                // 只在状态首次转入 running 时记录 startTime，避免重复触发覆盖
                if (info.status === 'running' && prevStatus !== 'running') {
                    task.startTime = Date.now();
                }
                if ((info.status === 'completed' || info.status === 'failed') && prevStatus === 'running') {
                    task.endTime = Date.now();
                    task.progress = 100;
                }
                // 用 title 补全 name（plan_created 阶段名称可能比 task_start 更精准）
                if (info.title && task.name !== info.title) task.name = info.title;
                updateGraph(task);
                break;
            }

            // tool_call / call：工具调用开始
            case 'tool_call':
            case 'call':
            case 'tool_start': {
                const info = event.content as AgentToolCallInfo;
                const taskId = event.task_id || info.task_id;
                const task = taskId ? tasks.value.find(t => t.id === taskId) : undefined;
                if (task) {
                    task.toolCalls.push({
                        tool_name: info.tool || (info as any).name || 'unknown_tool',
                        tool_args: info.args || (info as any).arguments || {},
                        status: 'running',
                    });
                }
                break;
            }

            // tool_output / result：工具执行结果 + 日志
            case 'tool_output':
            case 'result':
            case 'tool_end':
            case 'tool_error': {
                const info = event.content as AgentObservationInfo;
                const taskId = event.task_id || info.task_id;
                const task = taskId ? tasks.value.find(t => t.id === taskId) : undefined;
                if (task) {
                    const toolName = info.tool || (info as any).name;
                    const tc = [...task.toolCalls].reverse().find(tc => tc.tool_name === toolName && tc.status === 'running');
                    if (tc) {
                        const isError = info.is_error || event.type === 'tool_error';
                        tc.status = isError ? 'failed' : 'completed';
                        // Capture output to display search results or other tool outputs
                        tc.result = typeof (info.output || (info as any).result) === 'string' 
                            ? (info.output || (info as any).result) 
                            : JSON.stringify(info.output || (info as any).result);
                    }
                    info.logs?.forEach(line => task.logs.push(line));
                    updateGraph(task);
                }
                break;
            }

            // artifact：产出物卡片
            case 'artifact': {
                const card = event.content as AgentArtifactCard;
                artifacts.value.push({
                    name: card.file_name,
                    url: card.url,
                    type: card.type,
                    size: card.file_size,
                });
                addLog(`产出物已生成: ${card.file_name}`, 'success');
                break;
            }

            default:
                break;
        }
    };

    const updateToolStatus = (toolName: string, status: 'running' | 'completed' | 'failed', payload?: any) => {
        const idBase = `tool:${toolName}`;
        let task = tasks.value.find(t => t.id === idBase || t.name === idBase);
        if (!task) {
            task = {
                id: idBase,
                name: idBase,
                status: 'pending',
                progress: 0,
                logs: [],
                output: '',
                toolCalls: []
            };
            tasks.value.push(task);
        }

        if (status === 'running') {
            task.status = 'running';
            task.startTime = Date.now();
            task.progress = 0;
            if (payload?.args != null) {
                task.logs.push(`args: ${JSON.stringify(payload.args, null, 2)}`);
            }
        } else {
            task.status = status === 'failed' ? 'failed' : 'completed';
            task.endTime = Date.now();
            task.progress = 100;
            const res = payload?.result;
            if (res != null) {
                try {
                    task.logs.push(typeof res === 'string' ? res : JSON.stringify(res, null, 2));
                } catch {
                    task.logs.push(String(res));
                }
            }
        }

        updateGraph(task);
    };

    return {
        isRunning,
        tasks,
        logs,
        documents,
        currentStep,
        progress,
        totalTasks,
        completedTasks,
        artifacts,
        executeBuffer,
        graph,
        selectedTaskId,   // ← 节点点击 → 详情导航的响应式句柄
        initWorkflow,
        runWorkflow,
        stopWorkflow,
        addLog,
        appendOutput,
        clearLogs,
        resetWorkflow,
        resetArtifacts,
        updateGraph,
        updatePlanFromBackend,
        updateToolStatus,
        handleWorkflowEvent,
        handleTaskStarted,
        initFromAgentPlan,
        handleAgentEvent
    };
});
