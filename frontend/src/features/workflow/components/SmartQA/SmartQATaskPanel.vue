<template>
  <div class="w-full h-full flex flex-col overflow-hidden">
    <AutoTaskPanel v-if="isAutoTaskMode" @run-task="$emit('run-task', $event)" @open-session="$emit('open-session', $event)" @close="$emit('close')" class="!border-0 !shadow-none" />
    <WorkspaceTabs v-else
      ref="workspaceTabsRef"
      :sessionId="sessionId || ''"
      :agentName="agentName || ''"
      :isWorkflowMode="isWorkflowMode"
      :attachmentsCount="attachmentsCount"
      :hasKnowledgeBase="hasKnowledgeBase"
      @close="$emit('close')"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import AutoTaskPanel from '@/features/workflow/components/AutoTaskPanel.vue';
import WorkspaceTabs from '@/features/workflow/components/WorkspaceTabs.vue';

// Props definition without generic <{ ... }> since defineProps isn't strictly necessary when no specific usage in script, but if we do:
const props = defineProps<{
    isWorkflowMode?: boolean;
    isAutoTaskMode?: boolean;
    sessionId?: string | null;
    agentName?: string;
    attachmentsCount?: number;
    hasKnowledgeBase?: boolean;
}>();

defineEmits(['run-task', 'close', 'open-session']);

const workspaceTabsRef = ref<any>(null);

defineExpose({
  openTaskLogs: () => workspaceTabsRef.value?.openTaskLogs?.()
});
</script>
