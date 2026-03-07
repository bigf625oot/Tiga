<template>
  <div 
    class="rounded-lg border p-4 relative overflow-hidden group transition-all duration-300"
    :class="isLightMode ? 'bg-white border-border hover:border-blue-400 shadow-sm' : 'bg-[#111827] border-gray-800 hover:border-blue-500/50'"
  >
    <div class="flex justify-between items-start mb-4">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center shadow-lg shadow-blue-500/20">
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
          <h3 class="font-medium text-[15px]" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ data.name }}</h3>
          <div class="flex items-center gap-1.5 mt-1">
            <div class="w-1.5 h-1.5 rounded-full" :class="statusColor"></div>
            <span class="text-[13px]" :class="statusTextColor">{{ statusText }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="flex justify-between items-end mb-4">
      <span class="text-[13px]" :class="isLightMode ? 'text-gray-500' : 'text-gray-500'">实时吞吐</span>
      <span class="text-[22px] font-din font-semibold text-blue-400 leading-none">{{ data.throughput }}</span>
    </div>

    <div class="flex justify-between items-center mb-2">
      <span class="text-[13px]" :class="isLightMode ? 'text-gray-500' : 'text-gray-500'">活跃流水线</span>
      <span class="text-[14px] font-din" :class="isLightMode ? 'text-gray-600' : 'text-gray-400'">{{ data.active_pipelines }} 个</span>
    </div>

    <!-- Active Pipeline Card -->
    <div 
      v-if="data.current_pipeline" 
      class="rounded-lg p-4 border flex items-center justify-between group/item cursor-pointer transition-colors relative overflow-hidden"
      :class="isLightMode ? 'bg-gray-50 border-border hover:bg-gray-100' : 'bg-[#1F2937] border-gray-700/50 hover:bg-[#374151]'"
    >
      <!-- Flow Effect -->
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/10 to-transparent -translate-x-full animate-flow pointer-events-none"></div>
      
      <!-- Border Flow Effects -->
      <div class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent -translate-x-full animate-border-top"></div>
      <div class="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-transparent via-blue-400 to-transparent -translate-y-full animate-border-right"></div>
      <div class="absolute bottom-0 right-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent translate-x-full animate-border-bottom"></div>
      <div class="absolute bottom-0 left-0 w-[1px] h-full bg-gradient-to-b from-transparent via-blue-400 to-transparent translate-y-full animate-border-left"></div>

      <div class="flex items-center gap-2 relative z-10">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
        <div>
          <div class="text-[13px] font-medium" :class="isLightMode ? 'text-gray-700' : 'text-gray-300'">{{ data.current_pipeline.name }}</div>
          <div class="text-[12px] font-din text-blue-400 mt-0.5">已处理 {{ data.current_pipeline.processed.toLocaleString() }}</div>
        </div>
      </div>
      <svg 
        class="w-4 h-4 transition-colors relative z-10" 
        :class="isLightMode ? 'text-gray-400 group-hover/item:text-gray-600' : 'text-gray-500 group-hover/item:text-white'"
        fill="none" viewBox="0 0 24 24" stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { DataSource } from '../composables/useDashboardMock';
import { useTheme } from '@/composables/useTheme';

const props = defineProps<{
  data: DataSource;
}>();

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
