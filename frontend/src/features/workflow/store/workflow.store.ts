import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';

export interface WorkflowTask {
    id: string;
    name: string;
    description?: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number; // 0-100
    startTime?: number;
    endTime?: number;
    logs: string[];
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
    const eventSource = ref<EventSource | null>(null);
    const executeBuffer = ref<string>('');
    
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
        } else {
            tasks.value = [];
            logs.value = [];
            documents.value = [];
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
    const debouncedSave = () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(saveStateToBackend, 2000);
    };

    watch([tasks, logs, documents, currentStep], () => {
        if (sessionId.value) {
            localStorage.setItem(`workflow-${sessionId.value}`, JSON.stringify({
                tasks: tasks.value,
                logs: logs.value,
                documents: documents.value,
                currentStep: currentStep.value
            }));
            debouncedSave();
        }
    }, { deep: true });

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
            updateGraph(runningTask);
            return;
        }
        const lastTask = tasks.value[tasks.value.length - 1];
        if (lastTask) {
            lastTask.logs.push(output);
            updateGraph(lastTask);
            return;
        }
        addLog(output, 'info', step);
    };

    const clearLogs = () => {
        logs.value = [];
    };

    const resetWorkflow = () => {
        sessionId.value = '';
        tasks.value = [];
        logs.value = [];
        documents.value = [];
        currentStep.value = '';
        executeBuffer.value = '';
        isRunning.value = false;
    };

    const updateGraph = (task: WorkflowTask) => {
        // Check if node exists
        const existingNodeIndex = graph.value.nodes.findIndex(n => n.id === task.id);
        
        const nodeData = {
            label: task.name,
            status: task.status,
            progress: task.progress,
            logs: task.logs
        };

        if (existingNodeIndex !== -1) {
            // Update existing node
            graph.value.nodes[existingNodeIndex].data = nodeData;
        } else {
            // Add new node
            // Simple layout for now: vertical stack based on order
            const y = graph.value.nodes.length * 100;
            
            graph.value.nodes.push({
                id: task.id,
                type: 'custom', // We will create a custom node component
                data: nodeData,
                position: { x: 250, y: y }
            });
        }

        // Add edges based on dependencies
        if (task.dependencies) {
            task.dependencies.forEach(depId => {
                const edgeId = `e-${depId}-${task.id}`;
                if (!graph.value.edges.find(e => e.id === edgeId)) {
                    graph.value.edges.push({
                        id: edgeId,
                        source: depId,
                        target: task.id,
                        animated: true
                    });
                }
            });
        }
    };

    const updateTaskStatus = (stepName: string, status: WorkflowTask['status'], output?: string) => {
        // Find the last task with this stepName to see if we need a new one
        // If the last one is completed/failed, and we get 'running', create a new one.
        
        let taskIndex = -1;
        
        if (status === 'running') {
            // 1. Try to find a pending task from the plan (future steps)
            const formattedName = formatStepName(stepName);
            taskIndex = tasks.value.findIndex(t => t.status === 'pending' && t.name === formattedName);

            // 2. If no pending task, check if we have a running task (re-entrant)
            if (taskIndex === -1) {
                 for (let i = tasks.value.length - 1; i >= 0; i--) {
                    if (tasks.value[i].id.startsWith(stepName) && tasks.value[i].status === 'running') {
                        taskIndex = i;
                        break;
                    }
                }
            }
        } else {
             // For completion/failure, we must find the currently running task or the last one with this prefix
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
            // If the found task is already finished, and we are starting running again, create new
            createNew = true;
        }

        if (createNew) {
            // Generate unique ID
            const count = tasks.value.filter(t => t.id.startsWith(stepName)).length;
            const newId = count > 0 ? `${stepName}-${count + 1}` : stepName;
            
            task = {
                id: newId,
                name: formatStepName(stepName) + (count > 0 ? ` (${count + 1})` : ''),
                status: 'pending',
                progress: 0,
                logs: [],
                priority: 'medium'
            };
            tasks.value.push(task);
        }

        if (task) {
            if (status === 'running' && task.status !== 'running') {
                task.status = 'running';
                task.startTime = Date.now();
                // Update ID if it was a future task to indicate it's now active/real?
                // Actually keeping ID 'future-x' is fine, it just becomes running.
            } else if (status === 'completed' || status === 'failed') {
                task.status = status;
                task.endTime = Date.now();
                task.progress = 100;
            }

            if (output) {
                task.logs.push(output);
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
        // Reset tasks for new run? 
        // If we want to keep history of previous run in the same session, maybe not.
        // But usually a run is a new set of tasks.
        // Let's keep it cumulative for now, or clear?
        // User might want to "Retry", which means clearing or updating.
        // Let's clear logs/tasks for a NEW run.
        tasks.value = [];
        logs.value = [];
        documents.value = [];
        executeBuffer.value = '';
        
        // Use fetch with ReadableStream for SSE handling to support POST
        try {
            const response = await fetch('/api/v1/agent-workflows/run_stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId.value,
                    message: message,
                    agent_id: agentId,
                    mode: 'dynamic', // Use dynamic for full experience
                    params: {
                        attachments
                    }
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
                    
                    // Process SSE lines
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() || ''; // Keep incomplete line
                    
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
            // If loop finishes without return, it means stream ended without [DONE]
            isRunning.value = false;
            addLog('Connection closed', 'warning');
        } catch (e: any) {
            addLog(`Error: ${e.message}`, 'error');
            isRunning.value = false;
        }
    };

    const handleEvent = (data: any) => {
        // data: { step: string, status: string, output?: string, plan?: any }
        if (data.system) {
            addLog(data.output, data.status === 'failed' ? 'error' : 'info');
            return;
        }

        currentStep.value = data.step;
        
        // Handle Plan Update
        if (data.step === 'plan' && data.status === 'success' && data.plan) {
             // Remove all PENDING tasks (old plan) as they are superseded
             tasks.value = tasks.value.filter(t => t.status !== 'pending');
             
             // Add new plan tasks
              if (data.plan.steps && Array.isArray(data.plan.steps)) {
                  // Add reasoning as a log if available
                  if (data.plan.reasoning) {
                      addLog(`规划思路: ${data.plan.reasoning}`, 'info', 'plan');
                      // Also add to the Planning task logs so it shows on the card
                      const planTask = tasks.value.find(t => t.id.startsWith('plan') || t.name.includes('Planning') || t.name.includes('任务规划'));
                      if (planTask) {
                          planTask.logs.push(`规划思路: ${data.plan.reasoning}`);
                      }
                  }
                  
                  data.plan.steps.forEach((step: any) => {
                     // Use step.description if available (it should be in Chinese now), otherwise fallback to formatted name
                     const taskName = step.description || formatStepName(step.operation);
                     
                     tasks.value.push({
                         id: `future-${step.step_id}`, // Use prefix to avoid collision but simple enough
                         name: taskName,
                         description: step.description,
                         status: 'pending',
                         progress: 0,
                         logs: [],
                         priority: 'medium',
                         dependencies: step.dependencies?.map(String) || [],
                         estimatedTime: step.estimated_time,
                         requiredResources: step.required_resources || []
                     });
                 });
                 addLog(`任务规划已更新: ${data.plan.steps.length} 个步骤`, 'success', 'plan');
             }
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
        if (typeof data === 'object' && (data.step || data.system || data.status || data.output || data.plan)) {
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
        // In a real implementation, call an API to stop.
        // For now, just close client side.
        isRunning.value = false;
        addLog('Workflow stopped by user', 'warning');
    };

    const updatePlanFromBackend = (steps: Array<{ title: string, description?: string, status: string }>) => {
        // Sync tasks with backend plan
        // Strategy: 
        // 1. Identify existing tasks by title/name to preserve logs/progress/history
        // 2. Add new tasks
        // 3. Update status of existing tasks
        // 4. Remove tasks not in the plan (careful with completed history?)
        //    Actually, if the agent re-plans, it might remove steps. So we should reflect that.
        
        const newTasks: WorkflowTask[] = [];
        
        steps.forEach((step, index) => {
            // Try to find existing task
            const existingTask = tasks.value.find(t => t.name === step.title);
            
            if (existingTask) {
                // Update existing
                // Map backend status string to frontend status
                let newStatus: WorkflowTask['status'] = 'pending';
                const s = step.status.toLowerCase();
                if (s === 'running') newStatus = 'running';
                else if (s === 'completed') newStatus = 'completed';
                else if (s === 'failed') newStatus = 'failed';
                
                // If status changed to running, set start time
                if (newStatus === 'running' && existingTask.status !== 'running') {
                    existingTask.startTime = Date.now();
                }
                // If completed/failed, set end time
                if ((newStatus === 'completed' || newStatus === 'failed') && existingTask.status !== 'completed' && existingTask.status !== 'failed') {
                    existingTask.endTime = Date.now();
                    existingTask.progress = 100;
                }
                
                existingTask.status = newStatus;
                existingTask.description = step.description || existingTask.description;
                
                newTasks.push(existingTask);
            } else {
                // Create new
                let newStatus: WorkflowTask['status'] = 'pending';
                const s = step.status.toLowerCase();
                if (s === 'running') newStatus = 'running';
                else if (s === 'completed') newStatus = 'completed';
                else if (s === 'failed') newStatus = 'failed';

                newTasks.push({
                    id: `step-${index}-${Date.now()}`, // Unique ID
                    name: step.title,
                    description: step.description,
                    status: newStatus,
                    progress: newStatus === 'completed' ? 100 : 0,
                    logs: [],
                    startTime: newStatus === 'running' ? Date.now() : undefined,
                    endTime: (newStatus === 'completed' || newStatus === 'failed') ? Date.now() : undefined
                });
            }
        });
        
        tasks.value = newTasks;
        
        // Update graph nodes
        graph.value = { nodes: [], edges: [] };
        tasks.value.forEach(t => updateGraph(t));
        
        // Log update
        addLog(`任务计划已更新: ${steps.length} 个步骤`, 'info', 'plan');
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
                logs: []
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
        graph, // Export graph state
        initWorkflow,
        runWorkflow,
        stopWorkflow,
        addLog,
        appendOutput,
        clearLogs,
        resetWorkflow,
        updateGraph, // Export updateGraph action
        updatePlanFromBackend, // Export new action
        updateToolStatus,
        handleWorkflowEvent
    };
});
