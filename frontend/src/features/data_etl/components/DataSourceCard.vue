<template>
  <div 
    class="rounded-xl border p-5 relative overflow-hidden group transition-all duration-300 flex flex-col gap-5 cursor-pointer"
    :class="[
      isLightMode 
        ? 'bg-white border-slate-200 hover:-translate-y-[2px] hover:shadow-[0_8px_16px_rgba(0,0,0,0.06)]' 
        : 'bg-[#111827] border-gray-800 hover:border-blue-500/50 hover:-translate-y-[2px] hover:shadow-lg',
      isSelected 
        ? (isLightMode ? 'ring-2 ring-blue-500/20 shadow-[inset_0_0_0_1px_rgba(59,130,246,0.1)]' : 'ring-2 ring-blue-500/40')
        : ''
    ]"
    @click="$emit('select', data.id)"
  >
    <!-- Selected Indicator Strip -->
    <div 
      v-if="isSelected"
      class="absolute left-0 top-0 bottom-0 w-1 bg-blue-500"
    ></div>
    <!-- Header Section -->
    <div class="flex justify-between items-start">
      <div class="flex items-center gap-4">
        <div 
          class="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20"
          :class="isLightMode ? 'bg-gradient-to-br from-blue-500 to-cyan-500' : 'bg-gradient-to-br from-blue-600 to-blue-800'"
        >
          <svg v-if="data.type === 'sftp'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          <svg v-else-if="data.type === 'crawler'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
          <svg v-else class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
        </div>
        <div>
          <h3 class="font-bold text-[16px] tracking-tight" :class="isLightMode ? 'text-slate-900' : 'text-white'">{{ data.name }}</h3>
          <div class="flex items-center gap-2 mt-1.5">
            <div class="relative flex h-2 w-2">
              <span v-if="data.status === 'healthy'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" :class="statusColor"></span>
            </div>
            <span class="text-[12px] font-medium uppercase tracking-wide opacity-80" :class="statusTextColor">{{ statusText }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bento Grid Layout -->
    <div class="grid grid-cols-2 gap-3">
      <!-- Throughput Box -->
      <div 
        class="rounded-xl p-3 flex flex-col justify-between h-20"
        :class="isLightMode ? 'bg-slate-50' : 'bg-[#1F2937]/50'"
      >
        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">实时吞吐</span>
        <div class="flex items-end justify-between">
            <span class="text-[18px] font-inter font-bold tracking-tight text-slate-700 dark:text-gray-200">{{ data.throughput }}</span>
        </div>
      </div>

      <!-- Active Pipeline Box -->
      <div 
        class="rounded-xl p-3 flex flex-col justify-between h-20"
        :class="isLightMode ? 'bg-slate-50' : 'bg-[#1F2937]/50'"
      >
        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">活跃流水线</span>
        <div class="flex items-end gap-1">
            <span class="text-[20px] font-inter font-bold tracking-tight text-slate-700 dark:text-gray-200">{{ data.active_pipelines }}</span>
            <span class="text-[11px] font-medium text-slate-400 mb-1.5">个</span>
        </div>
      </div>
    </div>

    <!-- Active Task Status (Full Width) -->
    <div 
      v-if="data.current_pipeline" 
      class="rounded-xl p-3 flex items-center justify-between group/item cursor-pointer transition-colors relative overflow-hidden"
      :class="isLightMode ? 'bg-blue-50/50 hover:bg-blue-50' : 'bg-blue-900/10 hover:bg-blue-900/20'"
    >
      <!-- Flow Effect -->
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/5 to-transparent -translate-x-full animate-flow pointer-events-none"></div>

      <div class="flex items-center gap-3 relative z-10">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
        <div class="flex flex-col">
            <span class="text-[11px] font-bold uppercase tracking-wider text-blue-400">正在处理</span>
            <span class="text-[13px] font-semibold text-slate-700 dark:text-slate-200">{{ data.current_pipeline.name }}</span>
        </div>
      </div>
      <div class="text-right z-10">
        <div class="text-[14px] font-inter font-bold text-blue-600 dark:text-blue-400">{{ data.current_pipeline.processed.toLocaleString() }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { DataSource } from '../composables/useDashboardMock';
import { useTheme } from '@/composables/useTheme';

const props = defineProps<{
  data: DataSource;
  isSelected?: boolean;
}>();

defineEmits(['select']);

const { isLightMode } = useTheme();

const statusColor = computed(() => {
  switch (props.data.status) {
    case 'healthy': return 'bg-green-500';
    case 'warning': return 'bg-yellow-500';
    case 'error': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
});

const statusTextColor = computed(() => {
  switch (props.data.status) {
    case 'healthy': return 'text-green-500';
    case 'warning': return 'text-yellow-500';
    case 'error': return 'text-red-500';
    default: return 'text-gray-500';
  }
});

const statusText = computed(() => {
  switch (props.data.status) {
    case 'healthy': return '健康';
    case 'warning': return '警告';
    case 'error': return '异常';
    default: return '未知';
  }
});
</script>

<style scoped>
@keyframes flow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.animate-flow {
  animation: flow 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes border-top {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
@keyframes border-right {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}
@keyframes border-bottom {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
@keyframes border-left {
  0% { transform: translateY(100%); }
  100% { transform: translateY(-100%); }
}

.animate-border-top {
  animation: border-top 2s linear infinite;
}
.animate-border-right {
  animation: border-right 2s linear infinite;
  animation-delay: 0.5s;
}
.animate-border-bottom {
  animation: border-bottom 2s linear infinite;
  animation-delay: 1s;
}
.animate-border-left {
  animation: border-left 2s linear infinite;
  animation-delay: 1.5s;
}
</style>
