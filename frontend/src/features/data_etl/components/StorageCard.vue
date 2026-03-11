<template>
  <div 
    class="rounded-xl border p-5 relative overflow-hidden group transition-all duration-300 flex flex-col gap-5 bg-card text-card-foreground border-border hover:border-primary/50 shadow-sm"
  >
    <!-- Header -->
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-800 flex items-center justify-center shadow-lg shadow-purple-500/20">
        <svg v-if="data.type === 'neo4j'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <svg v-else class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
        </svg>
      </div>
      <div>
        <h3 class="font-bold text-[16px] tracking-tight text-foreground">{{ data.name }}</h3>
        <div class="flex items-center gap-2 mt-1.5">
          <div class="relative flex h-2 w-2">
            <span v-if="data.status === 'healthy'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2" :class="statusColor"></span>
          </div>
          <span class="text-[12px] font-medium uppercase tracking-wide opacity-80" :class="statusTextColor">{{ statusText }}</span>
        </div>
      </div>
    </div>

    <!-- Bento Metrics Grid -->
    <div class="grid grid-cols-2 gap-3">
      <div 
        v-for="(metric, idx) in data.metrics" 
        :key="idx" 
        class="rounded-xl p-3 flex flex-col justify-between h-24 bg-muted/50"
      >
        <div class="flex justify-between items-start">
            <span class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">{{ metric.label }}</span>
            <!-- Trend Indicator (Mini) -->
            <div v-if="metric.trend" class="flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full" 
                :class="metric.trend === 'up' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'">
                <svg v-if="metric.trend === 'up'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>
            </div>
        </div>
        
        <div class="flex items-end justify-between mt-2">
          <span class="text-[20px] font-inter font-bold tracking-tight leading-none text-foreground">{{ metric.value }}</span>
        </div>
      </div>
    </div>

    <!-- Health Status (Full Width) -->
    <div 
      class="rounded-xl p-3 flex items-center gap-4 transition-colors bg-muted/50"
    >
      <div class="relative w-10 h-10 flex items-center justify-center">
         <svg class="w-full h-full -rotate-90" viewBox="0 0 36 36">
            <path class="text-muted/20" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" stroke-width="3" />
            <path :class="healthColor" :stroke-dasharray="`${data.health_score}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" stroke-width="3" />
         </svg>
         <span class="absolute text-[10px] font-bold text-muted-foreground">{{ data.health_score }}</span>
      </div>
      <div class="flex flex-col">
         <span class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">系统健康度</span>
         <span class="text-[13px] font-medium text-foreground">运行平稳，无异常告警</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { StorageNode } from '../composables/useDashboardMock';

const props = defineProps<{
  data: StorageNode;
}>();

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
    case 'healthy': return 'text-green-600 dark:text-green-500';
    case 'warning': return 'text-yellow-600 dark:text-yellow-500';
    case 'error': return 'text-red-600 dark:text-red-500';
    default: return 'text-muted-foreground';
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
</script>
