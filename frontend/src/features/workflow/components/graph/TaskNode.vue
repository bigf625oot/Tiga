<template>
  <div class="task-node p-2 rounded-lg border shadow-sm min-w-[200px] bg-white" 
       :class="statusClass">
    <Handle type="target" position="top" class="w-2 h-2 !bg-slate-400" />
    
    <div class="flex items-center gap-2 mb-1">
      <div class="w-6 h-6 rounded-full flex items-center justify-center shrink-0" :class="iconBgClass">
        <component :is="statusIcon" class="w-3 h-3 text-white" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-bold text-xs truncate">{{ data.label }}</div>
        <div class="text-[10px] text-slate-500 capitalize">{{ data.status }}</div>
      </div>
    </div>

    <div v-if="data.status === 'running'" class="h-1 bg-slate-100 rounded-full overflow-hidden mt-1">
        <div class="h-full bg-blue-500 animate-pulse" :style="{ width: (data.progress || 0) + '%' }"></div>
    </div>

    <Handle type="source" position="bottom" class="w-2 h-2 !bg-slate-400" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Handle } from '@vue-flow/core';
import { 
  CheckCircleOutlined, 
  SyncOutlined, 
  ClockCircleOutlined, 
  CloseCircleOutlined 
} from '@ant-design/icons-vue';

const props = defineProps(['data']);

const statusClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'border-green-500 ring-1 ring-green-100';
    case 'running': return 'border-blue-500 ring-1 ring-blue-100';
    case 'failed': return 'border-red-500 ring-1 ring-red-100';
    default: return 'border-slate-200';
  }
});

const iconBgClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'bg-green-500';
    case 'running': return 'bg-blue-500';
    case 'failed': return 'bg-red-500';
    default: return 'bg-slate-200';
  }
});

const statusIcon = computed(() => {
  switch (props.data.status) {
    case 'completed': return CheckCircleOutlined;
    case 'running': return SyncOutlined;
    case 'failed': return CloseCircleOutlined;
    default: return ClockCircleOutlined;
  }
});
</script>

<style scoped>
.task-node {
  transition: all 0.2s ease;
}
.task-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style>
