<template>
  <div class="h-full flex flex-col bg-background overflow-hidden relative">
    <SmartQAHeader
      v-if="chatSession.messages.value.length > 0 && !embedded"
      :is-left-collapsed="false"
      :is-right-collapsed="false"
      :progress="0"
      :current-session="chatSession.currentSession.value"
      :current-agent="agentSelection.currentAgent.value"
      :current-mode-id="currentModeId"
      show-controls
      @open-memo="isMemoDrawerOpen = true"
      @update-title="handleUpdateTitle"
    />

    <div class="flex-1 flex min-h-0 relative overflow-hidden">
      <!-- File Sidebar for Quick Mode -->
      <FileSidebar 
        v-if="(!currentModeId || currentModeId === 'quick') && chatSession.messages.value.length > 0"
        :is-open="isFileSidebarOpen"
        :attachments="sidebarAttachments"
        @toggle="isFileSidebarOpen = !isFileSidebarOpen"
        @add-files="attachmentsManager.attachmentModalVisible.value = true"
        @remove-file="removeSidebarAttachment"
      />

      <div class="flex-1 flex flex-col h-full relative min-w-0">
        <SmartQAChatArea
          v-bind="chatAreaProps"
          v-on="chatAreaEvents"
          v-model="input"
          v-model:is-network-search-enabled="isNetworkSearchEnabled"
        />
      </div>

      <DocPreviewPanel
        :visible="docPreviewVisible"
        :doc-id="previewDocId"
        @close="docPreviewVisible = false"
      />
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
import SmartQAHeader from '@/features/llm-chat/shared/components/layout/SmartQAHeader.vue';
import SmartQAChatArea from '@/features/llm-chat/shared/components/layout/SmartQAChatArea.vue';
import FileSidebar from '@/features/llm-chat/shared/components/common/FileSidebar.vue';
import DocPreviewPanel from '@/features/llm-chat/shared/components/common/DocPreviewPanel.vue';
import MemoDrawer from '@/features/llm-chat/shared/components/common/MemoDrawer.vue';
import AttachmentDialog from '@/features/llm-chat/shared/components/common/AttachmentDialog.vue';
import { ChatContextKey } from '@/features/llm-chat/shared/context/ChatContext';
import type { Attachment } from '@/features/llm-chat/shared/types';
import { getSmartQADefaults } from '@/features/llm-chat/shared/utils/qa/smartqaDefaults';

const props = defineProps<{ sessionId: string | null; embedded: boolean; initialModeId?: string }>();
const emit = defineEmits(['refresh-sessions', 'update:sessionId']);

const engine = useChatEngine(props, emit, props.initialModeId || 'quick');
const {
    input, currentModeId, isNetworkSearchEnabled, isMemoDrawerOpen, memos,
    docPreviewVisible, previewDocId, sessionAttachments, agentSelection,
    attachmentsManager, chatSession, chatAreaProps, chatAreaEvents, handleUpdateTitle
} = engine;

const isFileSidebarOpen = ref(false);

const sidebarAttachments = computed(() => {
  const combined = [...sessionAttachments.value, ...attachmentsManager.selectedAttachments.value];
  const out: Attachment[] = [];
  const seen = new Set<string>();
  for (const a of combined) {
    const key = a.type === 'knowledge' ? `knowledge:${String(a.id ?? '')}` : `local:${a.name}:${a.size ?? 0}`;
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(a);
  }
  return out;
});

watch(() => sidebarAttachments.value.length, (len, prev) => {
  if ((prev === 0 || prev === undefined) && len > 0) {
    isFileSidebarOpen.value = true;
  }
});

const removeSidebarAttachment = (index: number) => {
  const target = sidebarAttachments.value[index];
  if (!target) return;
  const isSame = (a: Attachment, b: Attachment) => a.type === b.type && (a.type === 'knowledge' ? String(a.id ?? '') === String(b.id ?? '') : a.name === b.name && a.size === b.size);
  attachmentsManager.selectedAttachments.value = attachmentsManager.selectedAttachments.value.filter(a => !isSame(a, target));
  sessionAttachments.value = sessionAttachments.value.filter(a => !isSame(a, target));
};

provide(ChatContextKey, {
  modeId: currentModeId,
  currentAgent: computed(() => agentSelection.currentAgent.value as any),
  sessionId: chatSession.currentSessionId,
  isWorkflowRunning: computed(() => false)
});

onMounted(() => {
    if (props.sessionId) {
        chatSession.currentSessionId.value = props.sessionId;
        chatSession.fetchSessionDetails(props.sessionId).then(() => {
             if (chatSession.currentSession.value && (chatSession.currentSession.value as any).agent_id) {
                 agentSelection.selectedAgentId.value = (chatSession.currentSession.value as any).agent_id;
             }
        });
    } else {
        if (agentSelection.agents.value.length === 0) {
            agentSelection.fetchAgents();
        }
        const defaultAgent = agentSelection.agents.value.find(a => a.name === '通用' || a.name === '快问快答') || agentSelection.agents.value[0];
        if (defaultAgent) agentSelection.selectedAgentId.value = defaultAgent.id;
    }
});

watch(() => props.sessionId, (newId, oldId) => {
    if (newId === oldId) return;
    if (newId && newId === chatSession.currentSessionId.value && chatSession.messages.value.length > 0) return;

    chatSession.stopGeneration();
    chatSession.currentSessionId.value = newId;
    chatSession.messages.value = [];
    sessionAttachments.value = [];
    isFileSidebarOpen.value = false;
    docPreviewVisible.value = false;
    previewDocId.value = null;

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
        if (agentSelection.agents.value.length === 0) agentSelection.fetchAgents();
        const defaultAgent = agentSelection.agents.value.find(a => a.name === '通用' || a.name === '快问快答') || agentSelection.agents.value[0];
        if (defaultAgent) agentSelection.selectedAgentId.value = defaultAgent.id;
    }
});
</script>
