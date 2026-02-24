<template>
  <div class="agent-status-dashboard bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col gap-5">
    
    <!-- Header: Identity & Status -->
    <div class="flex items-start justify-between">
      <div class="flex items-center gap-4">
        <div class="relative w-14 h-14 shrink-0">
          <div v-if="status === 'running'" class="absolute inset-0 rounded-full bg-indigo-500/20 animate-ping"></div>
          <div class="relative w-full h-full rounded-full bg-slate-100 border-2 border-white shadow-md overflow-hidden flex items-center justify-center">
             <img src="/bot.svg" class="w-full h-full object-cover" alt="Agent" />
          </div>
          <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-sm">
            <div 
              class="w-3 h-3 rounded-full"
              :class="{
                'bg-emerald-500': status === 'running',
                'bg-slate-400': status === 'idle',
                'bg-amber-500': status === 'paused',
                'bg-blue-500': status === 'completed',
                'bg-red-500': status === 'failed'
              }"
            ></div>
          </div>
        </div>
        
        <div class="flex flex-col">
          <h3 class="font-bold text-slate-800 text-lg leading-tight">{{ agentName }}</h3>
          <div class="flex items-center gap-2 text-xs text-slate-500 font-mono mt-1">
            <span class="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 border border-slate-200">{{ sessionId.slice(0, 8) }}</span>
            <span v-if="startTime" class="flex items-center gap-1">
              <span class="w-1 h-1 rounded-full bg-slate-400"></span>
              {{ durationFormatted }}
            </span>
          </div>
        </div>
      </div>

      <!-- Current Phase Badge -->
      <div class="flex flex-col items-end gap-1">
        <div class="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-100 flex items-center gap-1.5 shadow-sm">
          <span v-if="status === 'running'" class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
          {{ t(currentPhase || 'agentStatus.phases.ready') }}
        </div>
      </div>
    </div>

    <!-- Progress Section -->
    <div class="flex flex-col gap-2">
      <div class="flex justify-between items-end">
        <span class="text-xs font-bold text-slate-700 uppercase tracking-wider">{{ t('agentStatus.progress') }}</span>
        <span class="text-sm font-bold text-indigo-600">{{ progress }}%</span>
      </div>
      <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner border border-slate-200/60">
        <div 
          class="bg-indigo-600 h-full rounded-full transition-all duration-500 ease-out relative overflow-hidden" 
          :style="{ width: `${progress}%` }"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[shimmer_2s_infinite]"></div>
        </div>
      </div>
    </div>
      
    <!-- Steps Timeline -->
    <div class="w-full overflow-x-auto pb-2 -mb-2 scrollbar-thin">
      <div class="flex items-center min-w-max gap-1">
        <div 
          v-for="(step, idx) in steps" 
          :key="idx"
          class="flex items-center"
        >
          <!-- Step Item -->
          <div 
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all duration-300"
            :class="[
              step.status === 'running' ? 'bg-indigo-50 border-indigo-200 ring-2 ring-indigo-100 ring-offset-1' : 
              step.status === 'completed' ? 'bg-emerald-50/50 border-emerald-100 text-emerald-700' :
              'bg-white border-slate-100 text-slate-400 grayscale'
            ]"
          >
            <div 
              class="w-2 h-2 rounded-full shrink-0"
              :class="[
                step.status === 'completed' ? 'bg-emerald-500' : 
                step.status === 'running' ? 'bg-indigo-500 animate-pulse' : 
                step.status === 'failed' ? 'bg-red-500' :
                'bg-slate-300'
              ]"
            ></div>
            <span class="text-xs font-medium whitespace-nowrap">{{ t(step.label) }}</span>
          </div>
          
          <!-- Connector -->
          <div v-if="idx < (steps?.length || 0) - 1" class="w-4 h-0.5 bg-slate-100 mx-1"></div>
        </div>
      </div>
    </div>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-slate-100">
       <!-- CPU -->
       <div class="bg-slate-50 rounded-lg p-2.5 border border-slate-100 flex flex-col gap-1.5">
         <span class="text-[10px] uppercase tracking-wider text-slate-400 font-bold truncate">{{ t('agentStatus.metrics.cpu') }}</span>
         <div class="flex items-center justify-between">
            <span class="text-sm font-mono font-bold text-slate-700">{{ cpuUsage || 0 }}%</span>
            <div class="w-12 h-1 bg-slate-200 rounded-full overflow-hidden">
              <div class="h-full bg-emerald-500 transition-all duration-500" :style="{ width: `${cpuUsage || 0}%` }"></div>
            </div>
         </div>
       </div>

       <!-- Memory -->
       <div class="bg-slate-50 rounded-lg p-2.5 border border-slate-100 flex flex-col gap-1.5">
         <span class="text-[10px] uppercase tracking-wider text-slate-400 font-bold truncate">{{ t('agentStatus.metrics.memory') }}</span>
         <div class="flex items-center justify-between">
            <span class="text-sm font-mono font-bold text-slate-700">{{ memoryUsage || 0 }}MB</span>
            <div class="w-12 h-1 bg-slate-200 rounded-full overflow-hidden">
              <div class="h-full bg-blue-500 transition-all duration-500" :style="{ width: `${Math.min(100, (memoryUsage || 0) / 10)}%` }"></div>
            </div>
         </div>
       </div>

       <!-- Network -->
       <div class="bg-slate-50 rounded-lg p-2.5 border border-slate-100 flex flex-col gap-1.5">
         <span class="text-[10px] uppercase tracking-wider text-slate-400 font-bold truncate">{{ t('agentStatus.metrics.network') }}</span>
         <div class="flex items-center gap-2">
            <span class="text-sm font-mono font-bold text-slate-700">↓{{ networkUsage || 0 }}KB/s</span>
         </div>
       </div>

       <!-- Errors -->
       <div class="bg-slate-50 rounded-lg p-2.5 border border-slate-100 flex flex-col gap-1.5">
         <span class="text-[10px] uppercase tracking-wider text-slate-400 font-bold truncate">{{ t('agentStatus.metrics.errors') }}</span>
         <div class="flex items-center gap-2">
            <span 
              class="text-sm font-mono font-bold transition-colors duration-300" 
              :class="errorCount && errorCount > 0 ? 'text-red-600' : 'text-slate-700'"
            >
              {{ errorCount || 0 }}
            </span>
            <span class="text-[10px] text-slate-400">{{ t('agentStatus.metrics.events') }}</span>
         </div>
       </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import { useI18n } from '../../../locales';

dayjs.extend(duration);

const { t } = useI18n();

const props = defineProps<{
  agentName: string;
  sessionId: string;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  startTime?: number;
  currentPhase?: string;
  errorCount?: number;
  steps?: Array<{ label: string, status: 'pending' | 'running' | 'completed' | 'failed' }>;
  cpuUsage?: number;
  memoryUsage?: number;
  networkUsage?: number;
}>();

const now = ref(dayjs().valueOf());
let timer: ReturnType<typeof setInterval> | null = null;

const durationFormatted = computed(() => {
  if (!props.startTime) return '00:00';
  // If status is completed/failed/idle, maybe we shouldn't keep ticking? 
  // But for now let's keep it simple or assume startTime resets on new run.
  // If we want to stop ticking when not running, we need an endTime prop.
  // Assuming startTime is reliable:
  const diff = Math.max(0, now.value - props.startTime);
  return dayjs.duration(diff).format('mm:ss');
});

onMounted(() => {
  timer = setInterval(() => {
    now.value = dayjs().valueOf();
  }, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
@keyframes shimmer {
  0% { transform: translateX(-150%); }
  100% { transform: translateX(150%); }
}

.scrollbar-thin::-webkit-scrollbar {
  height: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 20px;
}
</style>
