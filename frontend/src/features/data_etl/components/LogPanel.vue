<template>
  <div 
    class="absolute bottom-0 left-0 right-0 border-t backdrop-blur-md z-10 transition-all duration-300"
    :class="isLightMode ? 'bg-white/80 border-slate-200' : 'bg-[#0B0C10]/90 border-gray-800'"
  >
    <div 
      class="flex items-center justify-between px-4 py-2 border-b transition-colors"
      :class="isLightMode ? 'bg-slate-50 border-slate-200' : 'bg-[#111827] border-gray-800'"
    >
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span class="text-[15px] font-semibold" :class="isLightMode ? 'text-slate-900' : 'text-white'">实时日志流</span>
        <span 
          class="px-1.5 py-0.5 text-[11px] font-semibold rounded border"
          :class="isLightMode ? 'bg-blue-100 text-blue-600 border-blue-200' : 'bg-[#1E3A8A] text-[#60A5FA] border-[#1E40AF]'"
        >LIVE</span>
      </div>
      <button 
        class="text-[13px] px-2 py-1 rounded transition-colors"
        :class="isLightMode ? 'text-slate-500 hover:text-slate-900 bg-slate-200 hover:bg-slate-300' : 'text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700'"
      >
        暂停
      </button>
    </div>
    <div class="h-40 overflow-hidden relative font-mono text-sm">
      <div class="absolute inset-0 p-4 space-y-2 animate-scroll">
        <div 
          v-for="log in logs" 
          :key="log.id" 
          class="flex items-center gap-4 border rounded-lg p-2 transition-colors"
          :class="isLightMode ? 'bg-slate-100/50 border-transparent hover:bg-slate-100' : 'bg-[#1F2937]/50 border-gray-800 hover:bg-[#1F2937]'"
        >
          <span class="text-slate-400 shrink-0 font-mono text-[12px] opacity-60">{{ log.timestamp }}</span>
          <div class="shrink-0">
            <svg v-if="log.level === 'success'" class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else-if="log.level === 'info'" class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <svg v-else-if="log.level === 'warning'" class="w-4 h-4 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <svg v-else class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="truncate font-mono text-[13px]" :class="{
            'text-green-600': isLightMode && log.level === 'success',
            'text-blue-600': isLightMode && log.level === 'info',
            'text-yellow-600': isLightMode && log.level === 'warning',
            'text-red-600': isLightMode && log.level === 'error',
            'text-green-400': !isLightMode && log.level === 'success',
            'text-blue-400': !isLightMode && log.level === 'info',
            'text-yellow-400': !isLightMode && log.level === 'warning',
            'text-red-400': !isLightMode && log.level === 'error',
            'text-gray-300': !isLightMode && !['success', 'info', 'warning', 'error'].includes(log.level),
            'text-slate-600': isLightMode && !['success', 'info', 'warning', 'error'].includes(log.level)
          }" v-html="highlightLog(log.message)"></span>
        </div>
        <!-- Duplicate logs for seamless loop -->
        <div 
          v-for="log in logs" 
          :key="`dup-${log.id}`" 
          class="flex items-center gap-4 border rounded-lg p-2 transition-colors"
          :class="isLightMode ? 'bg-slate-100/50 border-transparent hover:bg-slate-100' : 'bg-[#1F2937]/50 border-gray-800 hover:bg-[#1F2937]'"
        >
          <span class="text-slate-400 shrink-0 font-mono text-[12px] opacity-60">{{ log.timestamp }}</span>
          <div class="shrink-0">
            <svg v-if="log.level === 'success'" class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else-if="log.level === 'info'" class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <svg v-else-if="log.level === 'warning'" class="w-4 h-4 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <svg v-else class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="truncate font-mono text-[13px]" :class="{
            'text-green-600': isLightMode && log.level === 'success',
            'text-blue-600': isLightMode && log.level === 'info',
            'text-yellow-600': isLightMode && log.level === 'warning',
            'text-red-600': isLightMode && log.level === 'error',
            'text-green-400': !isLightMode && log.level === 'success',
            'text-blue-400': !isLightMode && log.level === 'info',
            'text-yellow-400': !isLightMode && log.level === 'warning',
            'text-red-400': !isLightMode && log.level === 'error',
            'text-gray-300': !isLightMode && !['success', 'info', 'warning', 'error'].includes(log.level),
            'text-slate-600': isLightMode && !['success', 'info', 'warning', 'error'].includes(log.level)
          }" v-html="highlightLog(log.message)"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LogEntry } from '../composables/useDashboardMock';
import { useTheme } from '@/composables/useTheme';

const props = defineProps<{
  logs: LogEntry[];
}>();

const { isLightMode } = useTheme();

const highlightLog = (message: string) => {
  if (!message) return '';

  let highlighted = message;

  // 1. Keywords (Purple)
  highlighted = highlighted.replace(/(Pathway|LLM|Neo4j|S3|Kafka|Crawler)/g, 
    match => `<span class="${isLightMode.value ? 'text-purple-600 font-bold' : 'text-purple-400 font-bold'}">${match}</span>`
  );

  // 2. Parameters (Orange)
  highlighted = highlighted.replace(/\b(project_name|pipeline_id|batch_size|source_type)\b/g, 
    match => `<span class="${isLightMode.value ? 'text-orange-600' : 'text-orange-400'}">${match}</span>`
  );

  // 3. Metrics/Numbers (Cyan)
  highlighted = highlighted.replace(/(\d+ms|\d+\.\d+s|\d+\s*records|\d+%)/g, 
    match => `<span class="${isLightMode.value ? 'text-cyan-600' : 'text-cyan-400'}">${match}</span>`
  );

  return highlighted;
};
</script>
<style scoped>
@keyframes scroll {
  0% { transform: translateY(0); }
  100% { transform: translateY(-50%); }
}
.animate-scroll {
  animation: scroll 20s linear infinite;
}
.animate-scroll:hover {
  animation-play-state: paused;
}
</style>
