<template>
  <div class="h-full flex flex-col">
    <SmartQAHeader
      :is-left-collapsed="isLeftCollapsed"
      :is-right-collapsed="isRightCollapsed"
      :progress="workflowStore.progress || 0"
      :current-session="chatSession.currentSession.value"
      :current-agent="agentSelection.currentAgent.value"
      :current-mode-id="currentModeId"
      show-controls
      @toggle-left="toggleLeftPane"
      @toggle-right="toggleRightPane"
      @open-logs="() => taskPanelRef?.openTaskLogs?.()"
      @open-memo="isMemoDrawerOpen = true"
      @update-title="handleUpdateTitle"
    />

    <div ref="splitContainerRef" class="flex-1 min-h-0 flex flex-col xl:flex-row bg-transparent overflow-hidden">
      <!-- Left Pane: Chat -->
      <div v-show="!isLeftCollapsed"
        class="flex flex-col min-w-0 flex-1 bg-background/50 backdrop-blur-sm relative transition-all duration-150"
        :style="leftPaneStyle">
        <SmartQAChatArea
          v-bind="chatAreaProps"
          v-on="chatAreaEvents"
          v-model="input"
          v-model:is-network-search-enabled="isNetworkSearchEnabled"
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
        class="w-full h-1/2 xl:h-auto xl:flex-1 xl:min-w-0 xl:w-auto flex-shrink-0 bg-muted/30 z-20 transition-all duration-150 flex flex-col overflow-hidden"
        :style="rightPaneStyle">
        <SmartQATaskPanel
          ref="taskPanelRef"
          class="w-full h-full"
          :is-auto-task-mode="isAutoTaskMode"
          :is-workflow-mode="isWorkflowMode"
          :session-id="chatSession.currentSessionId.value"
          :agent-name="agentSelection.currentAgent.value?.name || ''"
          :attachments-count="attachmentsManager.selectedAttachments.value.length"
          :has-knowledge-base="hasKnowledgeBase"
          @run-task="handleRunTask"
          @open-session="(id) => $emit('update:sessionId', id)"
          @close="isRightCollapsed = true"
        />
      </div>
    </div>

    <MemoDrawer 
      :is-open="isMemoDrawerOpen" 
      :memos="memos" 
      @close="isMemoDrawerOpen = false" 
      @remove="(id) => memos = memos.filter(m => m.id !== id)"
      @update="(id, content) => { const m = memos.find(m => m.id === id); if(m) m.content = content; }"
    />

    <AttachmentDialog
      v-model:open="attachmentsManager.attachmentModalVisible.value"
      v-model:activeTab="attachmentsManager.activeAttachmentTab.value"
      v-model:knowledgeSearchKeyword="attachmentsManager.knowledgeSearchKeyword.value"
      :local-file-list="attachmentsManager.localFileList.value"
      :knowledge-docs="attachmentsManager.knowledgeDocs.value"
      :filtered-knowledge-docs="attachmentsManager.filteredKnowledgeDocs.value"
      :selected-knowledge-row-keys="attachmentsManager.selectedKnowledgeRowKeys.value"
      :knowledge-loading="attachmentsManager.knowledgeLoading.value"
      :search-suggestions="attachmentsManager.searchSuggestions.value"
      @file-change="(files: File[]) => files.forEach(f => attachmentsManager.handleLocalUpload(f))"
      @remove-local-file="attachmentsManager.removeLocalFile"
      @refresh-knowledge="(kw) => attachmentsManager.fetchKnowledgeDocs('knowledge_config' in (agentSelection.currentAgent.value || {}) ? (agentSelection.currentAgent.value as any).knowledge_config : undefined, kw)"
      @toggle-knowledge-selection="(id, checked) => { if(checked) attachmentsManager.selectedKnowledgeRowKeys.value.push(id); else attachmentsManager.selectedKnowledgeRowKeys.value = attachmentsManager.selectedKnowledgeRowKeys.value.filter(k => k !== id); }"
      @confirm="attachmentsManager.handleAttachmentOk"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, provide } from 'vue';
import { useChatEngine } from '@/features/llm-chat/shared/composables/useChatEngine';
import { useSmartQALayout } from '@/features/llm-chat/shared/composables/useSmartQALayout';
import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import SmartQAHeader from '@/features/llm-chat/shared/components/layout/SmartQAHeader.vue';
import SmartQAChatArea from '@/features/llm-chat/shared/components/layout/SmartQAChatArea.vue';
import SmartQATaskPanel from '@/features/llm-chat/workflow/components/SmartQA/SmartQATaskPanel.vue';
import MemoDrawer from '@/features/llm-chat/shared/components/common/MemoDrawer.vue';
import AttachmentDialog from '@/features/llm-chat/shared/components/common/AttachmentDialog.vue';
import { ChatContextKey } from '@/features/llm-chat/shared/context/ChatContext';

const props = defineProps<{ sessionId: string | null; embedded: boolean; initialModeId?: string }>();
const emit = defineEmits(['refresh-sessions', 'update:sessionId']);

const engine = useChatEngine(props, emit, props.initialModeId || 'workflow');
const {
    input, currentModeId, isNetworkSearchEnabled, isMemoDrawerOpen, memos,
    isWorkflowMode, isAutoTaskMode, agentSelection, attachmentsManager, chatSession,
    chatAreaProps, chatAreaEvents, handleUpdateTitle
} = engine;

const workflowStore = useWorkflowStore();
const taskPanelRef = ref<any>(null);

const {
  isLeftCollapsed, isRightCollapsed, isDesktop, leftPaneStyle, rightPaneStyle,
  toggleLeftPane, toggleRightPane, startResize, splitContainerRef
} = useSmartQALayout();

const hasKnowledgeBase = computed(() => {
    const agent = agentSelection.currentAgent.value as any;
    if (!agent || !agent.knowledge_config) return false;
    let docs = [];
    if (typeof agent.knowledge_config === 'string') {
        try { docs = JSON.parse(agent.knowledge_config).document_ids || []; } catch (e) { return false; }
    } else {
        docs = agent.knowledge_config.document_ids || [];
    }
    return docs.length > 0;
});

const handleRunTask = (prompt: string) => {
    engine.input.value = prompt;
    setTimeout(() => {
        engine.onSendMessage();
    }, 0);
};

provide(ChatContextKey, {
  modeId: currentModeId,
  currentAgent: computed(() => agentSelection.currentAgent.value as any),
  sessionId: chatSession.currentSessionId,
  isWorkflowRunning: computed(() => workflowStore.isRunning)
});

onMounted(() => {
    isRightCollapsed.value = false;
    if (props.sessionId) {
        chatSession.currentSessionId.value = props.sessionId;
        chatSession.fetchSessionDetails(props.sessionId).then(() => {
             if (chatSession.currentSession.value && (chatSession.currentSession.value as any).agent_id) {
                 agentSelection.selectedAgentId.value = (chatSession.currentSession.value as any).agent_id;
             }
        });
    }
});

watch(() => props.sessionId, (newId, oldId) => {
    if (newId === oldId) return;
    if (newId && newId === chatSession.currentSessionId.value && chatSession.messages.value.length > 0) return;

    chatSession.stopGeneration();
    chatSession.currentSessionId.value = newId;
    chatSession.messages.value = [];
    workflowStore.resetWorkflow();

    if (newId) {
        chatSession.fetchSessionDetails(newId).then(() => {
             if (chatSession.currentSession.value && (chatSession.currentSession.value as any).agent_id) {
                 agentSelection.selectedAgentId.value = (chatSession.currentSession.value as any).agent_id;
             }
        });
    } else {
        chatSession.currentSession.value = null;
        attachmentsManager.selectedAttachments.value = [];
        input.value = '';
    }
});
</script>
