<template>
  <div class="h-full flex flex-col bg-slate-950 font-mono text-slate-300">
    <!-- Header bar -->
    <div class="flex-none flex items-center gap-4 px-4 py-3 border-b border-slate-800 bg-slate-900">
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span v-if="store.isRunning" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex h-2 w-2 rounded-full"
            :class="store.isRunning ? 'bg-green-400' : 'bg-slate-600'"></span>
        </span>
        <span class="text-xs font-semibold text-slate-200 tracking-wide">Agent Workflow Monitor</span>
      </div>

      <div class="flex items-center gap-4 ml-2">
        <div class="flex flex-col">
          <span class="text-[9px] text-slate-500 uppercase tracking-wider">步骤</span>
          <span class="text-xs text-slate-200">{{ store.completedTasks }}/{{ store.totalTasks }}</span>
        </div>
        <div class="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            :class="store.progress === 100 ? 'bg-green-400' : 'bg-blue-400'"
            :style="{ width: store.progress + '%' }">
          </div>
        </div>
        <span class="text-xs text-blue-400 font-semibold">{{ store.progress }}%</span>
      </div>

      <div class="ml-auto flex items-center gap-2">
        <span class="text-[10px] text-slate-500">{{ store.currentStep || 'idle' }}</span>
        <button
          v-if="store.isRunning"
          @click="store.stopWorkflow"
          class="text-[10px] px-3 py-1 bg-red-900/40 text-red-400 border border-red-800/50 rounded hover:bg-red-800/60 transition-colors">
          STOP
        </button>
      </div>
    </div>

    <!-- Split content: left=tasks, right=logs -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left: Task timeline -->
      <div class="w-72 flex-none border-r border-slate-800 flex flex-col overflow-hidden">
        <div class="flex-none px-3 py-2 border-b border-slate-800 text-[10px] text-slate-500 uppercase tracking-wider">
          Task Steps
        </div>
        <div class="flex-1 overflow-y-auto py-2">
          <div v-if="store.tasks.length === 0"
            class="flex flex-col items-center justify-center h-full gap-2 text-slate-600">
            <span class="text-xs">等待任务分配...</span>
          </div>
          <div v-else class="px-2 space-y-0.5">
            <div
              v-for="(task, idx) in store.tasks"
              :key="task.id"
              class="relative flex items-start gap-2 px-2 py-2 rounded cursor-pointer transition-colors hover:bg-slate-800/50"
              :class="selectedTaskId === task.id ? 'bg-slate-800 ring-1 ring-slate-600' : ''"
              @click="selectedTaskId = task.id"
            >
              <!-- Connector line -->
              <div v-if="idx < store.tasks.length - 1"
                class="absolute left-[18px] top-[24px] bottom-0 w-px bg-slate-700/50 z-0" />

              <!-- Status icon -->
              <div class="relative flex-none z-10 mt-0.5 w-4">
                <span v-if="task.status === 'running'" class="relative inline-flex h-3 w-3 mt-0.5">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-60"></span>
                  <span class="relative inline-flex h-3 w-3 rounded-full bg-blue-400"></span>
                </span>
                <span v-else-if="task.status === 'completed'" class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-green-500/20 text-green-400 text-[10px]">✓</span>
                <span v-else-if="task.status === 'failed'" class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-red-500/20 text-red-400 text-[10px]">✗</span>
                <span v-else class="inline-block w-2.5 h-2.5 mt-0.5 rounded-full bg-slate-600 border border-slate-500"></span>
              </div>

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <p class="text-[11px] truncate"
                  :class="{
                    'text-blue-300': task.status === 'running',
                    'text-green-400': task.status === 'completed',
                    'text-red-400': task.status === 'failed',
                    'text-slate-400': task.status === 'pending',
                  }">
                  {{ task.name }}
                </p>
                <p v-if="task.startTime" class="text-[9px] text-slate-600 mt-0.5">
                  {{ formatElapsed(task.startTime, task.endTime) }}
                </p>
              </div>

              <span class="text-[9px] text-slate-600 flex-none">{{ idx + 1 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Execution logs -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <div class="flex-none px-4 py-2 border-b border-slate-800 flex items-center gap-2 bg-slate-900/50">
          <div class="flex gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-red-500/60"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-yellow-500/60"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-green-500/60"></span>
          </div>
          <span class="text-[10px] text-slate-500 ml-1">
            {{ selectedTask ? selectedTask.name : 'stdout' }}
          </span>
          <span v-if="store.isRunning" class="ml-auto text-[9px] text-blue-400 animate-pulse">● LIVE</span>
        </div>

        <div ref="logContainerRef"
          class="flex-1 overflow-y-auto p-4 text-[11px] leading-relaxed">
          <template v-if="selectedTask">
            <div v-if="selectedTask.logs && selectedTask.logs.length > 0">
              <div v-for="(line, i) in selectedTask.logs" :key="i"
                class="whitespace-pre-wrap break-all"
                :class="isErrorLine(line) ? 'text-red-400' : isSuccessLine(line) ? 'text-green-400' : 'text-slate-400'">
                {{ line }}
              </div>
            </div>
            <div v-else-if="selectedTask.output"
              class="whitespace-pre-wrap break-all text-slate-300">{{ selectedTask.output }}</div>
            <div v-else class="text-slate-600 italic">（无输出）</div>
          </template>
          <template v-else>
            <div v-for="(log, i) in store.logs" :key="i"
              class="flex items-start gap-3 py-0.5 border-b border-slate-800/30 last:border-0">
              <span class="text-[9px] text-slate-600 flex-none font-mono pt-0.5">{{ formatTime(log.timestamp) }}</span>
              <span class="flex-none w-2 h-2 rounded-full mt-0.5 flex-shrink-0"
                :class="{
                  'bg-blue-400': log.level === 'info',
                  'bg-yellow-400': log.level === 'warning',
                  'bg-red-400': log.level === 'error',
                  'bg-green-400': log.level === 'success',
                }">
              </span>
              <span class="text-[11px] whitespace-pre-wrap break-all"
                :class="{
                  'text-slate-300': log.level === 'info',
                  'text-yellow-400': log.level === 'warning',
                  'text-red-400': log.level === 'error',
                  'text-green-400': log.level === 'success',
                }">{{ log.message }}</span>
            </div>
            <div v-if="store.logs.length === 0" class="text-slate-600 italic text-xs">日志为空</div>
          </template>

          <span v-if="store.isRunning"
            class="inline-block w-2 h-3.5 bg-slate-400/60 animate-pulse ml-0.5 align-text-bottom"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useWorkflowStore } from '../store/workflow.store';

const store = useWorkflowStore();
const selectedTaskId = ref(null);
const logContainerRef = ref(null);

const selectedTask = computed(() =>
  selectedTaskId.value ? store.tasks.find(t => t.id === selectedTaskId.value) : null
);

// Auto-select running task
watch(() => store.tasks.map(t => t.status), () => {
  const running = store.tasks.find(t => t.status === 'running');
  if (running) selectedTaskId.value = running.id;
}, { deep: false });

// Auto-scroll logs
watch(() => store.logs.length, () => {
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight;
    }
  });
});

const formatElapsed = (startTime, endTime) => {
  const ms = (endTime || Date.now()) - startTime;
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`;
};

const formatTime = (ts) => {
  return new Date(ts).toTimeString().slice(0, 8);
};

const isErrorLine = (line) => /error|exception|traceback|failed/i.test(line);
const isSuccessLine = (line) => /success|done|completed|✓/i.test(line);
</script>
