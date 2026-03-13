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
          :show-controls="false"
      />

      <div class="flex-1 flex min-h-0 relative overflow-hidden">
        <!-- File Sidebar for Quick Mode -->
        <FileSidebar 
          v-if="(!currentModeId || currentModeId === 'quick') && messages.length > 0"
          :is-open="isFileSidebarOpen"
          :attachments="selectedAttachments"
          @toggle="isFileSidebarOpen = !isFileSidebarOpen"
          @add-files="attachmentModalVisible = true"
          @remove-file="removeAttachment"
        />

        <div class="flex-1 flex flex-col h-full relative min-w-0">
          <SmartQAChatArea
            v-model="input"
            :messages="messages"
            :modes="MODES"
            :current-mode-id="currentModeId"
            :embedded="embedded"
            :is-loading="isLoading"
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
          />
        </div>
      </div>
    </div>

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
import DynamicGridBackground from '@/shared/components/molecules/DynamicGridBackground.vue';

// Subcomponents
import SmartQAHeader from './SmartQA/SmartQAHeader.vue';
import SmartQAChatArea from './SmartQA/SmartQAChatArea.vue';
import SmartQATaskPanel from './SmartQA/SmartQATaskPanel.vue';
import AttachmentDialog from './SmartQA/AttachmentDialog.vue';
import FileSidebar from './SmartQA/FileSidebar.vue';

// Composables
import { useChatSession } from '../composables/useChatSession';
import { useAgentSelection } from '../composables/useAgentSelection';
import { useAttachments } from '../composables/useAttachments';
import { useSmartQALayout } from '../composables/useSmartQALayout';

// Services & Constants
import { chatService } from '../services/chatService';
import { knowledgeService } from '../services/knowledgeService';
import { MODES, STORAGE_KEYS } from '../constants';
import type { ModeConfig, ModeType, Agent } from '../types';

const props = defineProps<{
  sessionId: string | null;
  embedded: boolean;
}>();

const emit = defineEmits(['refresh-sessions']);

const workflowStore = useWorkflowStore();
const { isLightMode } = useTheme();
const isDark = computed(() => !isLightMode.value);
const blobColors = computed(() => isDark.value
  ? ['rgba(99, 102, 241, 0.15)', 'rgba(59, 130, 246, 0.15)', 'rgba(168, 85, 247, 0.15)']
  : ['rgba(99, 102, 241, 0.12)', 'rgba(59, 130, 246, 0.12)', 'rgba(168, 85, 247, 0.12)']);

// UI State
const input = ref('');
const mode = ref<ModeType>('chat');
const currentModeId = ref<string | null>(null);
const isFileSidebarOpen = ref(true);
const isNetworkSearchEnabled = ref(true);
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

const {
  currentSessionId, currentSession, messages, isLoading, isStreaming, isStopping,
  fetchSessionDetails, createNewSession, stopGeneration, handleStreamResponse
} = useChatSession();

const isTaskRunning = computed(() => isLoading.value || workflowStore.isRunning || isStreaming.value);
const taskPanelRef = ref<any>(null);

// Methods
const handleModeSelect = (m: ModeConfig) => {
  currentModeId.value = m.id;
  mode.value = m.value;

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
  
  // Upload attachments first
  const attachmentIds: string[] = [];
  const knowledgeFiles = selectedAttachments.value.filter(a => a.type === 'knowledge');
  knowledgeFiles.forEach(att => { if (att.id) attachmentIds.push(att.id); });

  const localFiles = selectedAttachments.value.filter(a => a.type === 'local' && a.file);
  for (const att of localFiles) {
    if (att.file) {
      try {
        const doc = await knowledgeService.uploadFile(att.file);
        attachmentIds.push(doc.id);
      } catch (e) {
        console.error('Failed to upload', att.name);
      }
    }
  }

  const userMsg = input.value;
  input.value = '';
  selectedAttachments.value = [];
  
  messages.value.push({ role: 'user', content: userMsg, timestamp: new Date().toISOString(), status: 'sending' });

  // Create session if needed
  if (!currentSessionId.value) {
    try {
      const sess = await createNewSession(
        (userMsg && userMsg.slice(0, 20)) || '新对话',
        selectedAgentId.value || null,
        mode.value
      );
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
          const res = await chatService.createAutoTask(userMsg);
          if (res && res.status === 'SKIPPED') {
              messages.value.push({ role: 'assistant', content: res.chat_response || '收到。', timestamp: new Date().toISOString() });
          } else {
              messages.value.push({ role: 'assistant', content: '任务已创建成功！', timestamp: new Date().toISOString() });
              isRightCollapsed.value = false;
          }
      } catch (e) {
          messages.value.push({ role: 'assistant', content: '系统错误：无法连接到任务服务。', timestamp: new Date().toISOString() });
      }
      return;
  }

  // Chat Mode
  if (currentSessionId.value) {
      try {
          const res = await chatService.sendChatMessage(currentSessionId.value, {
              message: userMsg,
              attachments: attachmentIds,
              enable_search: isNetworkSearchEnabled.value
          });
          await handleStreamResponse(res);
      } catch (e) {
          console.error(e);
          messages.value.push({ role: 'assistant', content: "Error: " + (e as Error).message });
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

// Lifecycle
onMounted(() => {
    try {
        const saved = localStorage.getItem(STORAGE_KEYS.IS_NETWORK_SEARCH_ENABLED);
        if (saved !== null) isNetworkSearchEnabled.value = saved === 'true';
    } catch {}

    if (props.sessionId) {
        currentSessionId.value = props.sessionId;
        fetchSessionDetails(props.sessionId);
    }
});

watch(() => props.sessionId, (newId) => {
    currentSessionId.value = newId;
    mode.value = 'chat';
    currentModeId.value = null;
    isRightCollapsed.value = true;
    workflowStore.resetWorkflow();
    if (newId) fetchSessionDetails(newId);
    else {
        currentSession.value = null;
        messages.value = [];
        selectedAttachments.value = [];
        input.value = '';
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
