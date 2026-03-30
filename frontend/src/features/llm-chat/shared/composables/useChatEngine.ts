import { ref, computed, onMounted, watch, onErrorCaptured } from 'vue';
import { useToast } from '@/components/ui/toast/use-toast';
import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import { useChatSession } from '@/features/llm-chat/shared/composables/useChatSession';
import { useAgentSelection } from '@/features/llm-chat/shared/composables/useAgentSelection';
import { useAttachments } from '@/features/llm-chat/shared/composables/useAttachments';
import { chatService } from '@/features/llm-chat/services/chatService';
import { knowledgeService } from '@/features/llm-chat/shared/services/knowledgeService';
import { MODES, STORAGE_KEYS } from '@/features/llm-chat/shared/constants';
import type { ModeConfig, ModeType, Agent, Attachment, Message } from '@/features/llm-chat/shared/types';
import { getSmartQADefaults } from '@/features/llm-chat/shared/utils/qa/smartqaDefaults';
import type { Memo } from '@/features/llm-chat/shared/components/common/MemoDrawer.vue';

export function useChatEngine(props: { sessionId: string | null; embedded?: boolean }, emit: any, initialModeId: string = 'quick') {
    const { toast } = useToast();
    const workflowStore = useWorkflowStore();

    // UI State
    const input = ref('');
    const initialModeConfig = MODES.find(m => m.id === initialModeId);
    const initialModeValue = (initialModeConfig ? initialModeConfig.value : 'quick') as ModeType;
    const mode = ref<ModeType>(initialModeValue);
    const currentModeId = ref<string | null>(initialModeId);
    
    // Feature States
    const isNetworkSearchEnabled = ref(true);
    const isMemoDrawerOpen = ref(false);
    const memos = ref<Memo[]>([]);
    const docPreviewVisible = ref(false);
    const previewDocId = ref<string | number | null>(null);

    // Computed modes
    const isWorkflowMode = computed(() => mode.value === 'workflow');
    const isAutoTaskMode = computed(() => mode.value === 'auto_task');

    // Composables
    const agentSelection = useAgentSelection(currentModeId);
    const { agents, teams, selectedAgentId, currentAgent, userScripts, fetchAgents } = agentSelection;

    const attachmentsManager = useAttachments();
    const {
        attachmentModalVisible, activeAttachmentTab, selectedAttachments,
        fetchKnowledgeDocs, selectedKnowledgeRowKeys
    } = attachmentsManager;

    const chatSession = useChatSession();
    const {
        currentSessionId, currentSession, messages, isLoading, isFetchingSession, isStreaming, isStopping, loadingStatus,
        fetchSessionDetails, createNewSession, stopGeneration, handleStreamResponse
    } = chatSession;

    // Watch session mode to sync currentModeId
    watch(
        () => currentSession.value,
        (newSession) => {
            if (newSession && newSession.mode) {
                const sessionMode = newSession.mode;
                const modeConfig = MODES.find(m => m.value === sessionMode);
                if (modeConfig) {
                    currentModeId.value = modeConfig.id;
                    mode.value = modeConfig.value as ModeType;
                }
            }
        },
        { immediate: true, deep: true }
    );

    const isTaskRunning = computed(() => isLoading.value || workflowStore.isRunning || isStreaming.value);

    // --- State Synchronization ---
    const syncSessionAgent = async () => {
        const sid = currentSessionId.value;
        const aid = selectedAgentId.value;
        if (!sid || !aid || isTaskRunning.value) return;
        if (!currentSession.value || currentSession.value.id !== sid) return;
        if ((currentSession.value as any).agent_id === aid) return;
        
        try {
            await chatService.updateSession(sid, { agent_id: aid } as any);
            if (currentSession.value) (currentSession.value as any).agent_id = aid;
            emit('refresh-sessions');
        } catch (e) {
            console.error(e);
        }
    };

    watch([selectedAgentId, currentSessionId], syncSessionAgent);
    watch(isTaskRunning, (running) => { if (!running) syncSessionAgent(); });

    // --- Actions ---
    const handleModeSelect = async (m: ModeConfig) => {
        currentModeId.value = m.id;
        mode.value = m.value;

        if (currentSessionId.value) {
            try {
                await chatService.updateSession(currentSessionId.value, { mode: m.value } as any);
                emit('refresh-sessions');
            } catch (e) {
                console.error('Failed to update session mode', e);
            }
        }

        // Reset agent selection logic
        if (m.id === 'quick') {
            const defaultAgent = agents.value.find(a => a.name === '通用' || a.name === '快问快答') || agents.value[0];
            if (defaultAgent) selectedAgentId.value = defaultAgent.id;
        } else if (m.id === 'team') {
            const currentTeamExists = teams.value.find(t => t.id === selectedAgentId.value);
            if (!currentTeamExists && teams.value.length > 0) {
                selectedAgentId.value = teams.value[0].id;
            }
        } else if (m.id === 'solo') {
            const currentAgentExists = agents.value.find(a => a.id === selectedAgentId.value);
            if (!currentAgentExists && agents.value.length > 0) {
                selectedAgentId.value = agents.value[0].id;
            }
        }
        
        // Force layout update via resize event
        setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
    };

    const sessionAttachments = ref<Attachment[]>([]);

    const onSendMessage = async (customInput?: string | Event, parentMessageId?: number) => {
        const textToSend = typeof customInput === 'string' ? customInput : input.value;
        if (!textToSend.trim() && !isTaskRunning.value) return;

        const pendingSelected = [...selectedAttachments.value];
        for (const a of pendingSelected) {
            if (a.type === 'knowledge') {
                sessionAttachments.value.push({ ...a, status: a.status || 'success' });
            } else {
                sessionAttachments.value.push({ ...a, status: a.status || 'uploading', progress: a.progress ?? 0, file: null });
            }
        }

        const attachmentIds: string[] = [];
        const mediaFiles: File[] = [];

        selectedAttachments.value.filter(a => a.type === 'knowledge').forEach(att => {
            if (att.id) attachmentIds.push(String(att.id));
        });

        const localFiles = selectedAttachments.value.filter(a => a.type === 'local' && a.file);
        for (const att of localFiles) {
            if (!att.file) continue;
            const f = att.file;
            const mime = (f.type || '').toLowerCase();
            const name = (f.name || '').toLowerCase();
            const isMedia = mime.startsWith('image/') || mime.startsWith('video/') || mime.startsWith('audio/') ||
                /\.(png|jpe?g|gif|webp|bmp|mp4|mov|m4v|webm|mp3|wav|m4a|aac|flac|ogg)$/.test(name);

            if (isMedia) {
                mediaFiles.push(f);
                continue;
            }

            try {
                const doc = await knowledgeService.uploadFile(f);
                const newId = String((doc as any).id);
                attachmentIds.push(newId);
                const idx = sessionAttachments.value.findIndex(a => a.type === 'local' && a.name === att.name);
                if (idx >= 0) {
                    sessionAttachments.value.splice(idx, 1, {
                        type: 'knowledge', name: att.name, size: att.size, id: newId, status: 'parsing'
                    } as any);
                }
            } catch (e) {
                console.error('Failed to upload', att.name);
                const idx = sessionAttachments.value.findIndex(a => a.type === 'local' && a.name === att.name);
                if (idx >= 0) {
                    sessionAttachments.value[idx] = { ...sessionAttachments.value[idx], status: 'error', errorMessage: '上传失败' } as any;
                }
            }
        }

        if (customInput === undefined) {
            input.value = '';
        }
        selectedAttachments.value = [];

        messages.value.push({ role: 'user', content: textToSend, timestamp: new Date().toISOString(), status: 'sending', parent_id: parentMessageId ? String(parentMessageId) : undefined });

        if (!currentSessionId.value) {
            try {
                if (!selectedAgentId.value) {
                    await fetchAgents();
                    const preferred = agents.value.find(a => a.name === '快问快答') || agents.value.find(a => (a.name || '').includes('通用')) || agents.value[0];
                    if (preferred) selectedAgentId.value = preferred.id;
                }
                const sess = await createNewSession(textToSend.slice(0, 20) || '新对话', selectedAgentId.value || null, mode.value);
                currentSessionId.value = sess.id;
                
                const url = new URL(window.location.href);
                url.searchParams.set('session_id', sess.id);
                window.history.pushState({}, '', url.toString());
                
                emit('update:sessionId', sess.id);
                emit('refresh-sessions');
            } catch (e) {
                messages.value[messages.value.length - 1].status = 'error';
                return;
            }
        }

        // --- DISPATCH TO MODES ---
        if (isWorkflowMode.value && currentSessionId.value) {
            // Only Workflow mode goes to runWorkflow path, other task modes use regular chat path
            workflowStore.runWorkflow(textToSend, selectedAgentId.value || undefined, attachmentIds);
            messages.value.push({ role: 'assistant', content: '已启动任务规划模式。', isSystem: true, timestamp: new Date().toISOString() });
            return;
        }

        if (isAutoTaskMode.value) {
            try {
                isLoading.value = true;
                const res = await chatService.createAutoTask(textToSend);
                if (res && res.status === 'SKIPPED') {
                    messages.value.push({ role: 'assistant', content: res.chat_response || '收到。', timestamp: new Date().toISOString() });
                } else {
                    messages.value.push({ role: 'assistant', content: '任务已创建成功！', timestamp: new Date().toISOString() });
                }
            } catch (e) {
                messages.value.push({ role: 'assistant', content: '系统错误：无法连接到任务服务。', timestamp: new Date().toISOString() });
            } finally {
                isLoading.value = false;
            }
            return;
        }

        if (currentSessionId.value) {
            try {
                isLoading.value = true;
                const enableReasoning = localStorage.getItem('enable_reasoning') === '1';
                let res: Response;
                
        if (isWorkflowMode.value || mode.value === 'solo' || mode.value === 'team') {
            workflowStore.initWorkflow(currentSessionId.value);
            workflowStore.isRunning = true;
            workflowStore.tasks = [];
            workflowStore.logs = [];
        }

                if (mediaFiles.length > 0) {
                    const formData = new FormData();
                    formData.append('message', textToSend);
                    formData.append('stream', 'true');
                    formData.append('enable_search', String(isNetworkSearchEnabled.value));
                    formData.append('enable_reasoning', String(enableReasoning));
                    formData.append('mode', mode.value);
                    if (selectedAgentId.value) formData.append('agent_id', selectedAgentId.value);
                    if (parentMessageId) formData.append('parent_id', String(parentMessageId));
                    for (const id of attachmentIds) formData.append('attachments', id);
                    for (const f of mediaFiles) formData.append('files', f, f.name);
                    res = await chatService.sendChatMessageMultipart(currentSessionId.value, formData);
                } else {
                    res = await chatService.sendChatMessage(currentSessionId.value, {
                        message: textToSend,
                        attachments: attachmentIds,
                        enable_search: isNetworkSearchEnabled.value,
                        enable_reasoning: enableReasoning,
                        mode: mode.value,
                        agent_id: selectedAgentId.value || undefined,
                        parent_id: parentMessageId ? String(parentMessageId) : undefined
                    });
                }
                
                await handleStreamResponse(res, undefined, (eventType, data) => {
                    if (eventType !== 'file') return;
                    const id = String((data as any)?.id ?? '');
                    const name = String((data as any)?.name ?? (data as any)?.title ?? '附件');
                    const size = (data as any)?.size;
                    const status = (data as any)?.status;
                    const errorMessage = (data as any)?.errorMessage;

                    const idx = sessionAttachments.value.findIndex(a => a.type === 'local' && a.name === name && a.status !== 'success');
                    const next: Attachment = { type: 'knowledge', name, size: typeof size === 'number' ? size : undefined, id, status: status || 'success', errorMessage } as any;
                    if (idx >= 0) sessionAttachments.value.splice(idx, 1, next);
                    else sessionAttachments.value.push(next);
                });
            } catch (e) {
                console.error(e);
                messages.value.push({ role: 'assistant', content: "Error: " + (e as Error).message });
                isLoading.value = false;
                isStreaming.value = false;
                if (workflowStore.isRunning) workflowStore.isRunning = false;
            }
        }
    };

    const handleUpdateTitle = async ({ id, title }: { id: string, title: string }) => {
        try {
            await chatService.updateSession(id, { title });
            if (currentSession.value && currentSession.value.id === id) {
                currentSession.value.title = title;
            }
            emit('refresh-sessions');
            toast({ title: "标题更新成功" });
        } catch (e) {
            console.error(e);
            toast({ variant: "destructive", title: "标题更新失败" });
        }
    };

    const handleExcerptMessage = (content: string) => {
        memos.value.unshift({
            id: Date.now().toString(),
            content,
            sender: currentAgent.value?.name || 'Tiga',
            avatar: (currentAgent.value as Agent)?.icon || (currentAgent.value as Agent)?.icon_url,
            timestamp: new Date().toISOString()
        });
        isMemoDrawerOpen.value = true;
    };

    const deleteMessagesFromIndex = async (startIndex: number) => {
        if (startIndex < 0 || startIndex >= messages.value.length) return;
        const msgsToDelete = messages.value.slice(startIndex);
        messages.value.splice(startIndex);
        if (currentSessionId.value) {
            for (const msg of msgsToDelete) {
                if (msg.id) {
                    try { await chatService.deleteMessage(currentSessionId.value, Number(msg.id)); } catch (e) {}
                }
            }
        }
    };

    const handleResendMessage = async (msg: Message) => {
        // Find the index of the message to resend
        const idx = messages.value.indexOf(msg);
        if (idx < 0) return;

        // Instead of physical deletion, we pass the parent_id to the backend
        // to create a new branch in the conversation tree.
        // The parent of the User message we are resending is the previous Assistant message (or null if first)
        const parentMsg = idx > 0 ? messages.value[idx - 1] : null;
        const parentMessageId = parentMsg?.id ? Number(parentMsg.id) : undefined;

        // Update UI locally by slicing the array (hiding the old branch)
        // We do not call deleteMessagesFromIndex anymore
        messages.value.splice(idx);

        // Put the message back in the input box
        input.value = msg.content;
        
        // Trigger send, passing the parent_id
        await onSendMessage(undefined, parentMessageId);
    };

    const handleEditMessage = async ({ originalMessage, newContent }: { originalMessage: Message, newContent: string }) => {
        input.value = newContent;
        const idx = messages.value.indexOf(originalMessage);
        if (idx >= 0) await deleteMessagesFromIndex(idx);
        await onSendMessage();
    };

    const handleDeleteMessage = async (msg: Message) => {
        const idx = messages.value.indexOf(msg);
        if (idx >= 0) {
            messages.value.splice(idx, 1);
            if (currentSessionId.value && msg.id) {
                try { await chatService.deleteMessage(currentSessionId.value, Number(msg.id)); } catch (e) { toast({ variant: "destructive", title: "删除失败" }); }
            }
        }
    };

    // Chat Area Props mapping
    const chatAreaProps = computed(() => ({
        messages: messages.value,
        modes: MODES,
        currentModeId: currentModeId.value,
        embedded: props.embedded || false,
        isLoading: isLoading.value,
        isFetchingSession: isFetchingSession.value,
        isStreaming: isStreaming.value,
        isTaskRunning: isTaskRunning.value,
        isStopping: isStopping.value,
        loadingStatus: loadingStatus.value,
        selectedAttachments: selectedAttachments.value,
        currentAgent: currentAgent.value,
        selectedAgentId: selectedAgentId.value,
        agentList: currentModeId.value === 'team' ? teams.value : agents.value,
        userScripts: userScripts.value,
    }));

    const chatAreaEvents = {
        'update:selectedAgentId': (val: string) => { selectedAgentId.value = val; },
        'send': onSendMessage,
        'stop': stopGeneration,
        'select-mode': handleModeSelect,
        'send-script': (c: string) => { input.value = c; },
        'open-doc-space': (id: string) => { previewDocId.value = id; docPreviewVisible.value = true; },
        'open-attachment': () => { attachmentModalVisible.value = true; },
        'remove-attachment': attachmentsManager.removeAttachment,
        'add-attachment': attachmentsManager.addLocalAttachments,
        'excerpt-message': handleExcerptMessage,
        'delete-message': handleDeleteMessage,
        'resend-message': handleResendMessage,
        'edit-message': handleEditMessage,
    };

    // Auto-fetch knowledge docs when tab is active
    watch([attachmentModalVisible, activeAttachmentTab], ([visible, tab]) => {
        if (visible && tab === 'knowledge') {
            const agent = currentAgent.value as Agent | undefined;
            if (agent && 'knowledge_config' in agent) {
                fetchKnowledgeDocs(agent.knowledge_config);
            } else {
                fetchKnowledgeDocs();
            }
        }
    });

    return {
        input, mode, currentModeId, isNetworkSearchEnabled, isMemoDrawerOpen, memos,
        docPreviewVisible, previewDocId, sessionAttachments, isWorkflowMode, isAutoTaskMode,
        agentSelection, attachmentsManager, chatSession,
        chatAreaProps, chatAreaEvents,
        handleUpdateTitle, onSendMessage, handleModeSelect
    };
}
