<template>
  <div class="w-full h-full flex flex-col overflow-hidden">
    <AutoTaskPanel v-if="isAutoTaskMode" @run-task="$emit('run-task', $event)" @close="$emit('close')" class="!border-0 !shadow-none" />
    <WorkspaceTabs v-else
      ref="workspaceTabsRef"
      :sessionId="sessionId || ''"
      :agentName="agentName || ''"
      :isWorkflowMode="isWorkflowMode"
      :attachmentsCount="attachmentsCount"
      :hasKnowledgeBase="hasKnowledgeBase"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import AutoTaskPanel from '../AutoTaskPanel.vue';
import WorkspaceTabs from '@/features/workflow/components/WorkspaceTabs.vue';

defineProps<{
  isAutoTaskMode: boolean;
  isWorkflowMode: boolean;
  sessionId: string | null;
  agentName: string;
  attachmentsCount: number;
  hasKnowledgeBase: boolean;
}>();

defineEmits(['run-task', 'close']);

const workspaceTabsRef = ref<any>(null);

defineExpose({
  openTaskLogs: () => workspaceTabsRef.value?.openTaskLogs?.()
});
</script>
