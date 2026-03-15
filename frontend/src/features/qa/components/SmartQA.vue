<template>
  <DynamicGridBackground class="h-full overflow-hidden relative bg-background" background-color="transparent"
    :grid-size="30" :grid-color="isDark ? '#333' : '#e5e7eb'" :blob-count="3" :blob-colors="blobColors"
    :animation-speed="20" :show-grid="!useTaskUI">
    
    <!-- Task/Workflow Mode UI -->
    <div v-if="useTaskUI" class="h-full flex flex-col">
      <SmartQAHeader
        :is-left-collapsed="isLeftCollapsed"
        :is-right-collapsed="isRightCollapsed"
        :progress="workflowStore.progress || 0"
        :current-session="currentSession"
        :current-agent="currentAgent"
        :current-mode-id="currentModeId"
        show-controls
        @toggle-left="toggleLeftPane"
        @toggle-right="toggleRightPane"
        @open-logs="openTaskLogs"
        @open-memo="isMemoDrawerOpen = true"
        @update-title="handleUpdateTitle"
      />

      <div ref="splitContainerRef" class="flex-1 min-h-0 flex flex-col xl:flex-row bg-transparent overflow-hidden">
        <!-- Left Pane: Chat -->
        <div v-show="!isLeftCollapsed"
          class="flex flex-col min-w-0 flex-1 bg-background/50 backdrop-blur-sm relative transition-all duration-150"
          :style="leftPaneStyle">
          <SmartQAChatArea
            v-model="input"
            :messages="messages"
            :modes="MODES"
            :current-mode-id="currentModeId"
            :embedded="embedded"
            :is-loading="isLoading"
            :is-streaming="isStreaming"
            :is-task-running="isTaskRunning"
            :is-stopping="isStopping"
            :selected-attachments="selectedAttachments"
            :current-agent="currentAgent"
            :selected-agent-id="selectedAgentId"
            :agent-list="currentModeId === 'team' ? teams : agents"
            :user-scripts="userScripts"
            v-model:is-network-search-enabled="isNetworkSearchEnabled"
            @update:selectedAgentId="selectedAgentId = $event"
            @send="onSendMessage"
            @stop="onStop"
            @select-mode="handleModeSelect"
            @send-script="onSendScript"
            @locate-node="handleLocateNode"
            @open-doc-space="handleOpenDocSpace"
            @open-attachment="attachmentModalVisible = true"
            @remove-attachment="removeAttachment"
            @add-attachment="addLocalAttachments"
            @excerpt-message="handleExcerptMessage"
          />
        </div>

        <!-- Resizer -->
        <div v-if="isDesktop && !isLeftCollapsed && !isRightCollapsed"
          class="hidden xl:flex w-1 shrink-0 items-center justify-center cursor-col-resize bg-transparent z-50 relative group hover:bg-primary/10 transition-colors"
          @mousedown="startResize">
          <div class="w-[1px] h-full bg-border group-hover:bg-primary group-hover:w-[2px] transition-all"></div>
        </div>

        <!-- Right Pane: Task -->
        <div v-show="!isRightCollapsed"
          class="w-full h-[420px] xl:h-auto xl:flex-1 xl:min-w-0 xl:w-auto flex-shrink-0 bg-muted/30 z-20 transition-all duration-150 flex flex-col overflow-hidden"
          :style="rightPaneStyle">
          <SmartQATaskPanel
            ref="taskPanelRef"
            class="w-full h-full"
            :is-auto-task-mode="isAutoTaskMode"
            :is-workflow-mode="isWorkflowMode"
            :session-id="currentSessionId"
            :agent-name="currentAgent?.name || ''"
            :attachments-count="selectedAttachments.length"
            :has-knowledge-base="hasKnowledgeBase"
            @run-task="handleRunTask"
            @open-session="handleOpenSession"
            @close="isRightCollapsed = true"
          />
        </div>
      </div>
    </div>

    <!-- Standalone Chat UI -->
    <div v-else class="h-full flex flex-col bg-background overflow-hidden relative">
      <SmartQAHeader
          v-if="messages.length > 0 && !embedded"
          :is-left-collapsed="false"
          :is-right-collapsed="false"
          :progress="workflowStore.progress || 0"
          :current-session="currentSession"
          :current-agent="currentAgent"
          :current-mode-id="currentModeId"
          show-controls
          @open-memo="isMemoDrawerOpen = true"
          @update-title="handleUpdateTitle"
      />

      <div class="flex-1 flex min-h-0 relative overflow-hidden">
        <!-- File Sidebar for Quick Mode -->
        <FileSidebar 
          v-if="(!currentModeId || currentModeId === 'quick') && messages.length > 0"
          :is-open="isFileSidebarOpen"
          :attachments="sidebarAttachments"
          @toggle="isFileSidebarOpen = !isFileSidebarOpen"
          @add-files="attachmentModalVisible = true"
          @remove-file="removeSidebarAttachment"
        />

        <div class="flex-1 flex flex-col h-full relative min-w-0">
          <SmartQAChatArea
            v-model="input"
            :messages="messages"
            :modes="MODES"
            :current-mode-id="currentModeId"
            :embedded="embedded"
            :is-loading="isLoading"
            :is-streaming="isStreaming"
            :is-task-running="isTaskRunning"
            :is-stopping="isStopping"
            :selected-attachments="selectedAttachments"
            :current-agent="currentAgent"
            :selected-agent-id="selectedAgentId"
            :agent-list="currentModeId === 'team' ? teams : agents"
            :user-scripts="userScripts"
            v-model:is-network-search-enabled="isNetworkSearchEnabled"
            @update:selectedAgentId="selectedAgentId = $event"
            @send="onSendMessage"
            @stop="onStop"
            @select-mode="handleModeSelect"
            @send-script="onSendScript"
            @locate-node="handleLocateNode"
            @open-doc-space="handleOpenDocSpace"
            @open-attachment="attachmentModalVisible = true"
            @remove-attachment="removeAttachment"
            @add-attachment="addLocalAttachments"
            @excerpt-message="handleExcerptMessage"
          />
        </div>
      </div>
    </div>

    <MemoDrawer 
      :is-open="isMemoDrawerOpen" 
      :memos="memos" 
      @close="isMemoDrawerOpen = false" 
      @remove="removeMemo"
      @update="updateMemo"
    />

    <AttachmentDialog
      v-model:open="attachmentModalVisible"
      v-model:activeTab="activeAttachmentTab"
      v-model:knowledgeSearchKeyword="knowledgeSearchKeyword"
      :local-file-list="localFileList"
      :knowledge-docs="knowledgeDocs"
      :filtered-knowledge-docs="filteredKnowledgeDocs"
      :selected-knowledge-row-keys="selectedKnowledgeRowKeys"
      :knowledge-loading="knowledgeLoading"
      :search-suggestions="searchSuggestions"
      @file-change="onFileChange"
      @remove-local-file="removeLocalFile"
      @refresh-knowledge="onRefreshKnowledge"
      @toggle-knowledge-selection="onToggleKnowledgeSelection"
      @confirm="handleAttachmentOk"
    />
  </DynamicGridBackground>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import { useTheme } from '@/composables/useTheme';
import { useToast } from '@/components/ui/toast/use-toast';
import DynamicGridBackground from '@/shared/components/molecules/DynamicGridBackground.vue';

// Subcomponents
import SmartQAHeader from './SmartQA/SmartQAHeader.vue';
import SmartQAChatArea from './SmartQA/SmartQAChatArea.vue';
import SmartQATaskPanel from './SmartQA/SmartQATaskPanel.vue';
import AttachmentDialog from './SmartQA/AttachmentDialog.vue';
import FileSidebar from './SmartQA/FileSidebar.vue';
import MemoDrawer, { type Memo } from './SmartQA/MemoDrawer.vue';

// Composables
import { useChatSession } from '../composables/useChatSession';
import { useAgentSelection } from '../composables/useAgentSelection';
import { useAttachments } from '../composables/useAttachments';
import { useSmartQALayout } from '../composables/useSmartQALayout';

// Services & Constants
import { chatService } from '../services/chatService';
import { knowledgeService } from '../services/knowledgeService';
import { MODES, STORAGE_KEYS } from '../constants';
import type { ModeConfig, ModeType, Agent, Attachment } from '../types';
import { getSmartQADefaults } from '../utils/smartqaDefaults';

const props = defineProps<{
  sessionId: string | null;
  embedded: boolean;
}>();

const emit = defineEmits(['refresh-sessions', 'update:sessionId']);

const { toast } = useToast();
const workflowStore = useWorkflowStore();
const { isLightMode } = useTheme();
const isDark = computed(() => !isLightMode.value);
const blobColors = computed(() => isDark.value
  ? ['rgba(99, 102, 241, 0.15)', 'rgba(59, 130, 246, 0.15)', 'rgba(168, 85, 247, 0.15)']
  : ['rgba(99, 102, 241, 0.12)', 'rgba(59, 130, 246, 0.12)', 'rgba(168, 85, 247, 0.12)']);

// UI State
const input = ref('');
const defaults = getSmartQADefaults(props.sessionId);
const mode = ref<ModeType>(defaults.mode);
const currentModeId = ref<string | null>(defaults.currentModeId);
const isFileSidebarOpen = ref(true);
const isNetworkSearchEnabled = ref(true);
const isMemoDrawerOpen = ref(false);
const memos = ref<Memo[]>([]);

const isWorkflowMode = computed(() => mode.value === 'workflow');
const isAutoTaskMode = computed(() => mode.value === 'auto_task');
const useTaskUI = computed(() => 
  isWorkflowMode.value || 
  isAutoTaskMode.value || 
  currentModeId.value === 'solo' || 
  currentModeId.value === 'team' ||
  workflowStore.isRunning || 
  (workflowStore.tasks?.length || 0) > 0
);

// Composables
const {
  isLeftCollapsed, isRightCollapsed, isDesktop, leftPaneStyle, rightPaneStyle,
  toggleLeftPane, toggleRightPane, startResize, splitContainerRef
} = useSmartQALayout();

const {
  agents, teams, selectedAgentId, currentAgent, userScripts, fetchAgents, fetchTeams
} = useAgentSelection(currentModeId);

const {
  attachmentModalVisible, activeAttachmentTab, localFileList, knowledgeDocs,
  selectedKnowledgeRowKeys, knowledgeSearchKeyword, knowledgeLoading, selectedAttachments,
  fetchKnowledgeDocs, handleLocalUpload, removeLocalFile, handleAttachmentOk, removeAttachment, filteredKnowledgeDocs, addLocalAttachments,
  searchSuggestions
} = useAttachments();

const sessionAttachments = ref<Attachment[]>([]);

const sidebarAttachments = computed(() => {
  const combined = [...sessionAttachments.value, ...selectedAttachments.value];
  const out: Attachment[] = [];
  const seen = new Set<string>();
  for (const a of combined) {
    const key = a.type === 'knowledge'
      ? `knowledge:${String(a.id ?? '')}`
      : `local:${a.name}:${a.size ?? 0}`;
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(a);
  }
  return out;
});

const isSameAttachment = (a: Attachment, b: Attachment) => {
  if (a.type !== b.type) return false;
  if (a.type === 'knowledge') return String(a.id ?? '') === String(b.id ?? '');
  return a.name === b.name && (a.size ?? 0) === (b.size ?? 0);
};

const removeSidebarAttachment = (index: number) => {
  const target = sidebarAttachments.value[index];
  if (!target) return;
  selectedAttachments.value = selectedAttachments.value.filter(a => !isSameAttachment(a, target));
  sessionAttachments.value = sessionAttachments.value.filter(a => !isSameAttachment(a, target));
};

const {
  currentSessionId, currentSession, messages, isLoading, isStreaming, isStopping,
  fetchSessionDetails, createNewSession, stopGeneration, handleStreamResponse
} = useChatSession();

const isTaskRunning = computed(() => isLoading.value || workflowStore.isRunning || isStreaming.value);
const taskPanelRef = ref<any>(null);

// Methods
const handleOpenSession = (sid: string) => {
  emit('update:sessionId', sid);
};

const handleModeSelect = (m: ModeConfig) => {
  // 手动切换模式后，更新 currentModeId 和 mode
  currentModeId.value = m.id;
  mode.value = m.value;

  // 如果手动选择了“秒懂”模式 (auto)，我们需要确保下次加载会话时不会因为它有消息而强制切回 auto?
  // 不，这里的逻辑是“加载会话”时的默认状态。手动切换是用户行为，优先级更高。
  // 但这里只是处理点击事件。
  
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

  if (m.value === 'workflow' || m.value === 'auto_task') {
    isRightCollapsed.value = false;
    if (m.value === 'auto_task') isNetworkSearchEnabled.value = false;
  } else if (m.id === 'solo' || m.id === 'team') {
    isRightCollapsed.value = false;
  } else {
    isRightCollapsed.value = true;
  }
  // Force update to trigger layout re-calculation
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
  }, 50);
};

const hasKnowledgeBase = computed(() => {
    const agent = currentAgent.value as Agent | undefined;
    if (!agent) return false;
    if (!('knowledge_config' in agent)) return false;
    
    const config = agent.knowledge_config;
    if (!config) return false;
    let docs = [];
    if (typeof config === 'string') {
        try {
            const parsed = JSON.parse(config);
            docs = parsed.document_ids || parsed.knowledge_base_ids || [];
        } catch (e) { return false; }
    } else {
        docs = config.document_ids || config.knowledge_base_ids || [];
    }
    return docs.length > 0;
});

const onSendMessage = async () => {
  if (!input.value.trim() && !isTaskRunning.value) return;
  
  const pendingSelected = [...selectedAttachments.value];

  for (const a of pendingSelected) {
    if (a.type === 'knowledge') {
      sessionAttachments.value.push({ ...a, status: a.status || 'success' });
    } else {
      sessionAttachments.value.push({ ...a, status: a.status || 'uploading', progress: a.progress ?? 0, file: null });
    }
  }

  // Upload attachments first
  const attachmentIds: string[] = [];
  const mediaFiles: File[] = [];

  const knowledgeFiles = selectedAttachments.value.filter(a => a.type === 'knowledge');
  knowledgeFiles.forEach(att => { if (att.id) attachmentIds.push(String(att.id)); });

  const localFiles = selectedAttachments.value.filter(a => a.type === 'local' && a.file);
  for (const att of localFiles) {
    if (!att.file) continue;
    const f = att.file;
    const mime = (f.type || '').toLowerCase();
    const name = (f.name || '').toLowerCase();
    const isMedia =
      mime.startsWith('image/') ||
      mime.startsWith('video/') ||
      mime.startsWith('audio/') ||
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
          type: 'knowledge',
          name: att.name,
          size: att.size,
          id: newId,
          status: 'parsing'
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

  const userMsg = input.value;
  input.value = '';
  selectedAttachments.value = [];

  messages.value.push({ role: 'user', content: userMsg, timestamp: new Date().toISOString(), status: 'sending' });

  // Create session if needed
  let isNewSession = false;
  if (!currentSessionId.value) {
    try {
      const sess = await createNewSession(
        (userMsg && userMsg.slice(0, 20)) || '新对话',
        selectedAgentId.value || null,
        mode.value
      );
      // We do not emit update:sessionId yet to prevent the watcher from firing
      // and wiping our optimistic messages. We will emit it after setting URL.
      currentSessionId.value = sess.id;
      isNewSession = true;
      
      // Update URL
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

  // Workflow Mode
  if (isWorkflowMode.value && currentSessionId.value) {
      workflowStore.initWorkflow(currentSessionId.value);
      workflowStore.runWorkflow(userMsg, selectedAgentId.value || undefined, attachmentIds);
      messages.value.push({ role: 'assistant', content: '已启动任务规划模式。', isSystem: true, timestamp: new Date().toISOString() });
      return;
  }

  // Auto Task Mode
  if (isAutoTaskMode.value) {
      try {
          isLoading.value = true;
          const res = await chatService.createAutoTask(userMsg);
          if (res && res.status === 'SKIPPED') {
              messages.value.push({ role: 'assistant', content: res.chat_response || '收到。', timestamp: new Date().toISOString() });
          } else {
              messages.value.push({ role: 'assistant', content: '任务已创建成功！', timestamp: new Date().toISOString() });
              isRightCollapsed.value = false;
          }
      } catch (e) {
          messages.value.push({ role: 'assistant', content: '系统错误：无法连接到任务服务。', timestamp: new Date().toISOString() });
      } finally {
          isLoading.value = false;
      }
      return;
  }

  // Chat Mode
  if (currentSessionId.value) {
      try {
          isLoading.value = true;
          let res: Response;
          if (mediaFiles.length > 0) {
              const formData = new FormData();
              formData.append('message', userMsg);
              formData.append('stream', 'true');
              formData.append('enable_search', String(isNetworkSearchEnabled.value));
              formData.append('mode', mode.value);
              for (const id of attachmentIds) formData.append('attachments', id);
              for (const f of mediaFiles) formData.append('files', f, f.name);
              res = await chatService.sendChatMessageMultipart(currentSessionId.value, formData);
          } else {
              res = await chatService.sendChatMessage(currentSessionId.value, {
                  message: userMsg,
                  attachments: attachmentIds,
                  enable_search: isNetworkSearchEnabled.value,
                  mode: mode.value
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
              const next: Attachment = {
                type: 'knowledge',
                name,
                size: typeof size === 'number' ? size : undefined,
                id,
                status: status || 'success',
                errorMessage
              } as any;
              if (idx >= 0) {
                sessionAttachments.value.splice(idx, 1, next);
              } else {
                sessionAttachments.value.push(next);
              }
          });
      } catch (e) {
          console.error(e);
          messages.value.push({ role: 'assistant', content: "Error: " + (e as Error).message });
          isLoading.value = false;
      }
  }
};

const onStop = () => stopGeneration();

const onSendScript = (content: string) => {
  input.value = content;
};

const handleRunTask = async (prompt: string) => {
    // Logic to switch agent if needed (simplified from original)
    input.value = prompt;
    // Assuming next tick handled by watcher or direct call
    setTimeout(() => onSendMessage(), 0);
};

const openTaskLogs = () => taskPanelRef.value?.openTaskLogs?.();
const handleLocateNode = (item: any) => {
    isRightCollapsed.value = false;
    // taskPanelRef.value?.locateNode?.(item.nodeId || item.title, item.docId);
};
const handleOpenDocSpace = (docId: string) => {
    isRightCollapsed.value = false;
    // taskPanelRef.value?.openDocSpace?.(docId);
};

const onFileChange = (files: File[]) => {
  files.forEach(f => handleLocalUpload(f));
};

const onRefreshKnowledge = (keyword?: string) => {
  const agent = currentAgent.value as Agent | undefined;
  // Team does not have knowledge_config, so we check existence
  if (agent && 'knowledge_config' in agent) {
    fetchKnowledgeDocs(agent.knowledge_config, keyword);
  } else {
    fetchKnowledgeDocs(undefined, keyword);
  }
};

const onToggleKnowledgeSelection = (id: string, checked: boolean) => {
  if (checked) {
    selectedKnowledgeRowKeys.value.push(id);
  } else {
    selectedKnowledgeRowKeys.value = selectedKnowledgeRowKeys.value.filter(k => k !== id);
  }
};

const handleUpdateTitle = async ({ id, title }: { id: string, title: string }) => {
  try {
    await chatService.updateSession(id, { title });
    // Update local session title
    if (currentSession.value && currentSession.value.id === id) {
      currentSession.value.title = title;
    }
    // Refresh sessions list in parent
    emit('refresh-sessions');
    toast({ title: "标题更新成功" });
  } catch (e) {
    console.error("Failed to update session title", e);
    toast({ variant: "destructive", title: "标题更新失败" });
  }
};

const handleExcerptMessage = (content: string) => {
  const newMemo: Memo = {
    id: Date.now().toString(),
    content: content,
    sender: currentAgent.value?.name || 'Tiga',
    avatar: (currentAgent.value as Agent)?.icon || (currentAgent.value as Agent)?.icon_url,
    timestamp: new Date().toISOString()
  };
  memos.value.unshift(newMemo);
  isMemoDrawerOpen.value = true;
};

const removeMemo = (id: string) => {
  memos.value = memos.value.filter(m => m.id !== id);
};

const updateMemo = (id: string, content: string) => {
  const memo = memos.value.find(m => m.id === id);
  if (memo) {
    memo.content = content;
  }
};

// Lifecycle
onMounted(() => {
    try {
        const saved = localStorage.getItem(STORAGE_KEYS.IS_NETWORK_SEARCH_ENABLED);
        if (saved !== null) isNetworkSearchEnabled.value = saved === 'true';
    } catch {}

    if (props.sessionId) {
        currentSessionId.value = props.sessionId;
        messages.value = [];
        fetchSessionDetails(props.sessionId).then(() => {
          // fetch 完成后，根据消息内容修正模式
          // 初始化时不知道是否有消息，默认先用了 quick (通过 getSmartQADefaults 传入 undefined 得到的)
          // 但这里需要手动更新一下，因为 getSmartQADefaults 只在 setup 跑了一次
          const nextDefaults = getSmartQADefaults(props.sessionId, messages.value);
          mode.value = nextDefaults.mode;
          currentModeId.value = nextDefaults.currentModeId;
        });
    } else {
        // Default to Auto mode on new session
        const nextDefaults = getSmartQADefaults(null);
        mode.value = nextDefaults.mode;
        currentModeId.value = nextDefaults.currentModeId;
        
        // Wait for agents to load then select default
        if (agents.value.length === 0) {
            fetchAgents();
        }
        const defaultAgent = agents.value.find(a => a.name === '通用' || a.name === '快问快答') || agents.value[0];
        if (defaultAgent) selectedAgentId.value = defaultAgent.id;
    }
});

watch(() => props.sessionId, (newId, oldId) => {
    if (newId === oldId) return;
    
    // If the prop update matches our internal state and we already have messages,
    // it means we initiated this session change locally (e.g., creating a new session)
    // and we shouldn't interrupt the ongoing stream or wipe the messages.
    if (newId && newId === currentSessionId.value && messages.value.length > 0) {
        return;
    }

    stopGeneration();
    currentSessionId.value = newId;
    messages.value = [];
    isRightCollapsed.value = true;
    workflowStore.resetWorkflow();
    if (newId) {
        // 先设为 quick（假设空），等 fetch 完再根据内容决定
        // 这样可以避免 Loading 期间显示秒懂卡片
        const loadingDefaults = getSmartQADefaults(newId, []); 
        mode.value = loadingDefaults.mode;
        currentModeId.value = loadingDefaults.currentModeId;
        
        fetchSessionDetails(newId).then(() => {
             const nextDefaults = getSmartQADefaults(newId, messages.value);
             mode.value = nextDefaults.mode;
             currentModeId.value = nextDefaults.currentModeId;
        });
    } else {
        const nextDefaults = getSmartQADefaults(null);
        mode.value = nextDefaults.mode;
        currentModeId.value = nextDefaults.currentModeId;
        currentSession.value = null;
        messages.value = [];
        selectedAttachments.value = [];
        input.value = '';
        if (agents.value.length === 0) {
            fetchAgents();
        }
        const defaultAgent = agents.value.find(a => a.name === '通用' || a.name === '快问快答') || agents.value[0];
        if (defaultAgent) selectedAgentId.value = defaultAgent.id;
    }
});

watch(isNetworkSearchEnabled, (val) => {
    try { localStorage.setItem(STORAGE_KEYS.IS_NETWORK_SEARCH_ENABLED, String(val)); } catch {}
});

// Auto-fetch knowledge docs when tab is active
watch([attachmentModalVisible, activeAttachmentTab], ([visible, tab]) => {
  if (visible && tab === 'knowledge') {
    // Check if we already have docs to avoid unnecessary fetching? 
    // Or just fetch every time to be fresh. Let's fetch if empty or force refresh logic needed.
    // For now, simple fetch.
    onRefreshKnowledge();
  }
});
</script>

<style scoped>
/* Scoped styles if needed, mostly handled by subcomponents */
</style>
