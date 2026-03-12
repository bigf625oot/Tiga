<template>
  <div class="w-full h-[420px] xl:h-auto xl:flex-1 xl:min-w-0 xl:w-auto flex-shrink-0 bg-muted/30 z-20 transition-all duration-150 flex flex-col overflow-hidden"
    :style="style">
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
  style: any;
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
