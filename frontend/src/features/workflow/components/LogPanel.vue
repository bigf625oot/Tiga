<template>
  <div class="h-full flex flex-col bg-slate-900 text-slate-300 font-mono text-xs overflow-hidden rounded-lg">
    <div class="px-4 py-2 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
      <span class="font-bold text-slate-100">系统日志</span>
      <span class="text-slate-500">{{ logs.length }} 条记录</span>
    </div>
    <div class="flex-1 overflow-y-auto p-4 space-y-1 custom-scrollbar" ref="logContainer">
       <EmptyLogState v-if="logs.length === 0" :isDarkMode="true" />
       <div v-else v-for="(log, idx) in logs" :key="idx" class="flex gap-2 hover:bg-slate-800/50 p-0.5 rounded">
          <span class="text-slate-500 shrink-0">[{{ formatTime(log.timestamp) }}]</span>
          <span :class="levelColor(log.level)" class="shrink-0 w-16 uppercase font-bold text-[10px] pt-0.5">{{ log.level }}</span>
          <span v-if="log.step" class="text-indigo-400 shrink-0">[{{ log.step }}]</span>
          <span class="break-all whitespace-pre-wrap">{{ log.message }}</span>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import dayjs from 'dayjs';
import EmptyLogState from './common/EmptyLogState.vue';

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  }
});

const logContainer = ref(null);

const formatTime = (ts) => dayjs(ts).format('HH:mm:ss.SSS');

const levelColor = (l) => {
    switch(l) {
        case 'error': return 'text-red-500';
        case 'warning': return 'text-yellow-500';
        case 'success': return 'text-green-500';
        default: return 'text-blue-400';
    }
};

watch(() => props.logs.length, () => {
    nextTick(() => {
        if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight;
        }
    });
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
</style>
