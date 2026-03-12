<template>
  <div class="h-full flex flex-col bg-background overflow-hidden">
    <div class="bg-background border-b px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <LayoutDashboard class="w-4 h-4 text-muted-foreground" />
        <h3 class="text-sm font-semibold">任务空间</h3>
        <Badge 
          :variant="store.isRunning ? 'default' : 'secondary'"
          class="ml-1 px-1.5 py-0 h-5 text-[10px] font-normal"
        >
          {{ store.isRunning ? '执行中' : '空闲' }}
        </Badge>
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-hidden bg-background relative">
      <div class="h-full">
        <TaskPanel
          ref="taskPanelRef"
          embedded
          :showEmbeddedHeader="true"
          :sessionId="sessionId"
          :agentName="agentName"
          :isWorkflowMode="isWorkflowMode"
          :attachmentsCount="attachmentsCount"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import TaskPanel from '@/features/workflow/components/TaskPanel.vue';
import { Badge } from '@/components/ui/badge';
import { LayoutDashboard } from 'lucide-vue-next';

const props = defineProps({
  sessionId: { type: String, default: '' },
  agentName: { type: String, default: '' },
  isWorkflowMode: { type: Boolean, default: true },
  attachmentsCount: { type: Number, default: 0 }
});

const store = useWorkflowStore();
const taskPanelRef = ref(null);

const openTaskLogs = () => {
  taskPanelRef.value?.openLogDrawer?.();
};

defineExpose({
  openTaskLogs
});
</script>
