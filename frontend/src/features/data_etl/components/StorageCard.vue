<template>
  <div 
    class="rounded-lg border p-4 relative overflow-hidden group transition-all duration-300"
    :class="isLightMode ? 'bg-white border-border hover:border-blue-400 shadow-sm' : 'bg-[#111827] border-gray-800 hover:border-blue-500/50'"
  >
    <div class="flex items-center gap-4 mb-4">
      <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-800 flex items-center justify-center shadow-lg shadow-purple-500/20">
        <svg v-if="data.type === 'neo4j'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
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

    <div class="grid grid-cols-1 gap-4 mb-4">
      <div 
        v-for="(metric, idx) in data.metrics" 
        :key="idx" 
        class="rounded-lg p-4 border transition-colors"
        :class="isLightMode ? 'bg-gray-50 border-border' : 'bg-[#1F2937] border-gray-700/50'"
      >
        <div class="text-[13px] text-gray-500 mb-1">{{ metric.label }}</div>
        <div class="flex items-end justify-between">
          <span class="text-[22px] font-din font-semibold leading-none" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ metric.value }}</span>
          <div v-if="metric.trend" class="flex items-center" :class="metric.trend === 'up' ? 'text-green-500' : 'text-red-500'">
            <svg v-if="metric.trend === 'up'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div 
      class="rounded-lg p-4 border transition-colors"
      :class="isLightMode ? 'bg-gray-50 border-border' : 'bg-[#1F2937] border-gray-700/50'"
    >
      <div class="flex justify-between items-center mb-1">
        <span class="text-[13px] text-gray-500">系统健康度</span>
        <span class="text-[16px] font-din font-semibold" :class="healthColor">{{ data.health_score }}%</span>
      </div>
      <div class="w-full rounded-full h-1.5" :class="isLightMode ? 'bg-gray-200' : 'bg-gray-700'">
        <div class="h-1.5 rounded-full transition-all duration-500" :class="healthBarColor" :style="{ width: `${data.health_score}%` }"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { StorageNode } from '../composables/useDashboardMock';
import { useTheme } from '@/composables/useTheme';

const props = defineProps<{
  data: StorageNode;
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
    case 'healthy': return '健康运行';
    case 'warning': return '警告';
    case 'error': return '异常';
    default: return '未知';
  }
});

const healthColor = computed(() => {
  if (props.data.health_score >= 90) return 'text-green-500';
  if (props.data.health_score >= 70) return 'text-yellow-500';
  return 'text-red-500';
});

const healthBarColor = computed(() => {
  if (props.data.health_score >= 90) return 'bg-green-500';
  if (props.data.health_score >= 70) return 'bg-yellow-500';
  return 'bg-red-500';
});
</script>
