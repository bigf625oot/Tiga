<template>
  <div class="h-full flex flex-col bg-background relative">
    <!-- Editor Area -->
    <div class="flex-1 flex flex-col overflow-hidden bg-background relative">
      <!-- Agent Status Dashboard (Only in Tasks view)
      <div v-if="(currentTask || store.isRunning) && activeView === 'tasks'" class="flex-none px-4 pt-4 pb-2 bg-background z-10 border-b border-border">
        <AgentStatusDashboard
          :agentName="agentName || '智能体'"
          :sessionId="sessionId"
          :status="dashboardStatus"
          :progress="store.progress"
          :currentPhase="taskPhase"
          :startTime="Date.now() - 10000"
          :steps="[
            { label: 'agentStatus.phases.init', status: 'completed' },
            { label: 'agentStatus.phases.planning', status: 'completed' },
            { label: 'agentStatus.phases.execution', status: dashboardStatus },
            { label: 'agentStatus.phases.review', status: 'pending' }
          ]"
          :cpuUsage="cpuUsage"
          :memoryUsage="memoryUsage"
          :networkUsage="networkUsage"
        />
      </div> -->

      <div class="flex-1 overflow-hidden relative flex flex-col">
        <template v-if="currentTask || activeView === 'tasks' || activeView === 'code' || activeView === 'results' || activeView === 'graph'">
          <!-- Task View -->
          <div v-if="activeView === 'tasks'" key="tasks" class="h-full overflow-y-auto p-4 custom-scrollbar">
            <!-- Plan summary bar -->
            <div v-if="store.tasks.length > 0" class="mb-4 flex items-center gap-3 px-1">
              <span class="text-xs text-muted-foreground font-mono">
                {{ store.completedTasks }} / {{ store.totalTasks }} 任务完成
              </span>
              <div class="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  class="h-full rounded-full transition-[width] duration-[600ms] ease-[cubic-bezier(0.34,1.56,0.64,1)]"
                  :class="store.progress === 100 ? 'bg-green-500' : 'bg-primary'"
                  :style="{ width: store.progress + '%' }"
                />
              </div>
              <span class="text-xs font-semibold text-primary">{{ store.progress }}%</span>
            </div>

            <!-- Task Cards -->
            <div class="space-y-3 pb-4">
              <div
                v-for="(task, idx) in store.tasks"
                :key="task.id"
                class="rounded-xl border transition-all bg-card shadow-sm overflow-hidden"
                :class="[
                  task.status === 'running' ? 'border-primary/60 ring-1 ring-primary/30 shadow-md' :
                  task.status === 'completed' ? 'border-green-500/30' :
                  task.status === 'failed' ? 'border-red-500/30' :
                  'border-border',
                  idx === currentStepIndex ? 'ring-1 ring-primary/50' : ''
                ]"
                @click="currentStepIndex = idx"
              >
                <!-- Card Header -->
                <div class="flex items-start gap-3 px-4 py-3">
                  <!-- Status Indicator -->
                  <div class="flex-none mt-0.5">
                    <span v-if="task.status === 'pending'" class="inline-block w-2.5 h-2.5 rounded-full bg-muted-foreground/40 mt-0.5" />
                    <span v-else-if="task.status === 'running'" class="relative inline-flex w-2.5 h-2.5 mt-0.5">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                      <span class="relative inline-flex rounded-full w-2.5 h-2.5 bg-primary" />
                    </span>
                    <span v-else-if="task.status === 'completed'" class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-green-500/15 text-green-500">
                      <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                    </span>
                    <span v-else-if="task.status === 'failed'" class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-red-500/15 text-red-500">
                      <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    </span>
                  </div>

                  <!-- Task Info -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between gap-2">
                      <h4 class="font-medium text-sm text-foreground truncate">{{ task.name }}</h4>
                      <div class="flex items-center gap-2 flex-none">
                        <!-- Elapsed time -->
                        <span v-if="task.startTime" class="text-[10px] text-muted-foreground font-mono">
                          {{ formatElapsed(task.startTime, task.endTime) }}
                        </span>
                        <!-- Status badge -->
                        <span
                          class="text-[10px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wide"
                          :class="{
                            'bg-muted text-muted-foreground': task.status === 'pending',
                            'bg-primary/10 text-primary': task.status === 'running',
                            'bg-green-500/10 text-green-600': task.status === 'completed',
                            'bg-red-500/10 text-red-600': task.status === 'failed'
                          }"
                        >{{ statusLabel(task.status) }}</span>
                      </div>
                    </div>
                    <p v-if="task.description && task.description !== task.name" class="text-xs text-muted-foreground mt-0.5 line-clamp-1">{{ task.description }}</p>
                  </div>
                </div>

                <!-- Tool Call Badges -->
                <div v-if="task.toolCalls && task.toolCalls.length > 0" class="px-4 pb-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="(tc, tcIdx) in task.toolCalls"
                    :key="tcIdx"
                    class="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border font-mono"
                    :class="{
                      'border-primary/30 bg-primary/5 text-primary': tc.status === 'running',
                      'border-green-500/30 bg-green-500/5 text-green-700': tc.status === 'completed',
                      'border-red-500/30 bg-red-500/5 text-red-600': tc.status === 'failed'
                    }"
                  >
                    <span v-if="tc.status === 'running'" class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                    <svg v-else-if="tc.status === 'completed'" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                    <svg v-else class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    {{ tc.tool_name }}
                  </span>
                </div>

                <!-- Output Area (collapsible) -->
                <div v-if="task.output || (task.logs && task.logs.length > 0)" class="border-t border-border/50">
                  <button
                    class="w-full flex items-center gap-2 px-4 py-1.5 text-[11px] text-muted-foreground hover:bg-muted/30 transition-colors text-left"
                    @click.stop="toggleOutput(task.id)"
                  >
                    <svg
                      class="w-3 h-3 transition-transform"
                      :class="expandedTasks.has(task.id) || task.status === 'running' ? 'rotate-90' : ''"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    ><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                    <span>{{ expandedTasks.has(task.id) || task.status === 'running' ? '收起输出' : '展开输出' }}</span>
                    <span v-if="task.output" class="text-[10px] text-muted-foreground/60 ml-auto">{{ outputLineCount(task.output) }} 行</span>
                  </button>
                  <div
                    v-show="expandedTasks.has(task.id) || task.status === 'running'"
                    class="px-4 pb-3"
                  >
                    <!-- Dark terminal console with auto-scroll -->
                    <div
                      :ref="el => setConsoleRef(task.id, el)"
                      class="font-mono text-[11px] text-green-400/90 bg-slate-950 rounded-lg p-3 max-h-48 overflow-y-auto leading-relaxed custom-scrollbar"
                    >
                      <div v-if="task.logs && task.logs.length > 0">
                        <div v-for="(line, i) in task.logs" :key="i" class="whitespace-pre-wrap break-all">{{ line }}</div>
                      </div>
                      <div v-else-if="task.output" class="whitespace-pre-wrap break-all text-green-300/80">{{ task.output }}</div>
                      <div v-else class="text-green-700/60 italic">(等待输出...)</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Artifact List -->
            <div v-if="store.artifacts && store.artifacts.length > 0" class="mt-4 rounded-xl border border-border bg-card shadow-sm overflow-hidden">
              <div class="flex items-center gap-2 px-4 py-3 border-b border-border/50">
                <svg class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1.293 12.707A2 2 0 008.285 22h7.43a2 2 0 001.993-1.293L19 8M10 12v6M14 12v6"/></svg>
                <span class="text-sm font-semibold text-foreground">产出物清单</span>
                <span class="text-xs text-muted-foreground ml-auto">{{ store.artifacts.length }} 个文件</span>
              </div>
              <div class="p-4 flex flex-wrap gap-2">
                <a
                  v-for="artifact in store.artifacts"
                  :key="artifact.url"
                  :href="artifact.url"
                  target="_blank"
                  class="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:border-primary/50 hover:bg-muted/50 transition-colors group"
                  :title="artifact.name"
                >
                  <span class="text-base">{{ artifactIcon(artifact.type) }}</span>
                  <div class="min-w-0">
                    <p class="text-xs font-medium text-foreground truncate max-w-[120px] group-hover:text-primary transition-colors">{{ artifact.name }}</p>
                    <p class="text-[10px] text-muted-foreground uppercase">{{ artifact.type }}{{ artifact.size ? ' · ' + formatSize(artifact.size) : '' }}</p>
                  </div>
                  <svg class="w-3 h-3 text-muted-foreground group-hover:text-primary transition-colors flex-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                </a>
              </div>
            </div>

            <!-- Empty state when no tasks yet but running -->
            <div v-if="store.tasks.length === 0 && store.isRunning" class="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <div class="relative w-12 h-12 mb-4">
                <div class="absolute inset-0 border-t-2 border-primary rounded-full animate-spin" />
                <div class="absolute inset-2 border-r-2 border-primary/50 rounded-full animate-[spin_2s_linear_infinite_reverse]" />
              </div>
              <p class="text-sm">正在生成任务计划...</p>
            </div>

            <!-- Empty state when no tasks and not running -->
            <EmptyState v-else-if="store.tasks.length === 0" />
          </div>

          <!-- Graph View -->
          <div v-else-if="activeView === 'graph'" key="graph" class="h-full w-full">
            <TaskGraph />
          </div>

          <!-- Code View -->
          <ArtifactEditor
            v-else-if="activeView === 'code'"
            key="code"
            :value="taskContent"
            :language="detectLanguage(currentTask)"
            :read-only="true"
            class="h-full w-full"
          />

          <!-- Results View -->
          <SandboxResultViewer
            v-else-if="activeView === 'results'"
            key="results"
            :code="currentTask ? taskContent : ''"
            :language="currentTask ? detectLanguage(currentTask) : 'python'"
            :title="currentTask && currentTask.name ? currentTask.name : '沙箱'"
            :auto-run="false"
            class="h-full w-full border-none rounded-none"
          />

          <!-- Terminal View -->
          <div v-else-if="activeView === 'terminal'" key="terminal" class="h-full w-full bg-slate-900">
            <SandboxTerminal
              ref="terminalRef"
              theme="dark"
              :readOnly="false"
            />
          </div>
        </template>

        <div v-else class="h-full w-full flex items-center justify-center bg-muted/20">
          <div v-if="store.isRunning" class="w-full max-w-md p-8 flex flex-col items-center select-none">
            <div class="relative w-24 h-24 mb-6">
              <div class="absolute inset-0 border-t-4 border-indigo-500 rounded-full animate-spin" />
              <div class="absolute inset-2 border-r-4 border-purple-500 rounded-full animate-[spin_3s_linear_infinite_reverse]" />
              <div class="absolute inset-4 border-b-4 border-pink-500 rounded-full animate-[spin_2s_linear_infinite]" />
              <div class="absolute inset-0 flex items-center justify-center font-mono text-xs font-semibold text-indigo-600 animate-pulse">AI</div>
            </div>
            <p class="text-center bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 font-semibold animate-pulse">
              {{ t('aiGenerating') }}
            </p>
            <p class="text-center text-muted-foreground text-xs mt-2 font-mono">
              Processing autonomous logic...
            </p>
          </div>
          <EmptyState v-else />
        </div>
      </div>
    </div>

    <!-- Log Navigation Footer (Player Style) -->
    <div v-if="totalSteps > 0" class="px-4 py-2 bg-background border-t border-border z-20">
      <div class="flex items-center gap-4 max-w-2xl mx-auto">
        <div class="flex items-center gap-0.5 p-0.5 bg-muted rounded-lg border border-border shadow-sm">
          <button
            @click="prevStep"
            :disabled="currentStepIndex <= 0"
            class="w-7 h-6 flex items-center justify-center rounded hover:bg-background hover:text-primary hover:shadow-sm text-muted-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
            title="上一步"
          >
            <LeftOutlined :style="{ fontSize: '10px' }" />
          </button>
          <button
            @click="nextStep"
            :disabled="currentStepIndex >= totalSteps - 1"
            class="w-7 h-6 flex items-center justify-center rounded hover:bg-background hover:text-primary hover:shadow-sm text-muted-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
            title="下一步"
          >
            <RightOutlined :style="{ fontSize: '10px' }" />
          </button>
        </div>

        <div class="flex-1 flex items-center gap-4 bg-muted/50 p-4 py-0.5 rounded-lg border border-border h-8">
          <span class="text-[10px] font-medium text-muted-foreground font-mono min-w-[1.2rem] text-right">{{ currentStepIndex + 1 }}</span>
          <a-slider
            v-model:value="currentStepIndex"
            :min="0"
            :max="Math.max(0, totalSteps - 1)"
            :disabled="totalSteps === 0"
            class="flex-1 !m-0"
            :tooltipOpen="false"
            size="small"
          />
          <span class="text-[10px] font-medium text-muted-foreground font-mono min-w-[1.2rem]">{{ totalSteps || 0 }}</span>
        </div>

        <button
          @click="openLogDrawer"
          class="w-7 h-6 flex items-center justify-center rounded hover:bg-muted text-muted-foreground transition-colors log-trigger"
          title="View Logs"
        >
          <FileTextOutlined :style="{ fontSize: '12px' }" />
        </button>
      </div>
    </div>

    <!-- Control Bar (only when running) -->
    <div v-if="store.isRunning" class="px-4 py-2 bg-muted/50 border-t border-border flex justify-between items-center text-xs text-muted-foreground">
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
        </span>
        <span>正在执行: {{ currentTask && currentTask.name ? currentTask.name : 'Processing...' }}</span>
      </div>
      <button
        @click="store.stopWorkflow"
        class="text-red-500 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded transition-colors flex items-center gap-1 font-medium"
      >
        <StopOutlined /> 停止
      </button>
    </div>

    <!-- Log Drawer -->
    <LogDrawer
      :visible="isLogDrawerOpen"
      :logs="store.logs"
      @close="isLogDrawerOpen = false"
      @clear="store.clearLogs"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, reactive, nextTick } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import ArtifactEditor from '@/features/workflow/components/editor/ArtifactEditor.vue';
import SandboxResultViewer from '@/features/sandbox/components/SandboxResultViewer.vue';
import EmptyState from '@/features/workflow/components/EmptyState.vue';
import LogDrawer from '@/features/workflow/components/drawer/LogDrawer.vue';
import AgentStatusDashboard from '@/features/workflow/components/AgentStatusDashboard.vue';
import SandboxTerminal from '@/features/sandbox/components/SandboxTerminal.vue';
import TaskGraph from './graph/TaskGraph.vue';
import { useI18n } from '../../../locales';
import {
  AppstoreOutlined,
  CodeOutlined,
  PlayCircleOutlined,
  LeftOutlined,
  RightOutlined,
  StopOutlined,
  FileTextOutlined,
  ApartmentOutlined
} from '@ant-design/icons-vue';

defineProps({
  embedded: { type: Boolean, default: false },
  showEmbeddedHeader: { type: Boolean, default: true },
  sessionId: { type: String, default: '' },
  agentName: { type: String, default: '' },
  isWorkflowMode: { type: Boolean, default: true },
  attachmentsCount: { type: Number, default: 0 }
});

const store = useWorkflowStore();
const { t } = useI18n();
const isLogDrawerOpen = ref(false);
const currentStepIndex = ref(0);
const autoScroll = ref(true);
const activeView = ref('tasks');
const terminalRef = ref(null);

// Track which task output panels are expanded (running tasks always expanded)
const expandedTasks = reactive(new Set());

// Per-task terminal console refs for auto-scroll
const consoleRefs = reactive(new Map());
const setConsoleRef = (taskId, el) => {
  if (el) consoleRefs.set(taskId, el);
  else consoleRefs.delete(taskId);
};
const scrollConsoleToBottom = (taskId) => {
  nextTick(() => {
    const el = consoleRefs.get(taskId);
    if (el) el.scrollTop = el.scrollHeight;
  });
};

const toggleOutput = (taskId) => {
  if (expandedTasks.has(taskId)) {
    expandedTasks.delete(taskId);
  } else {
    expandedTasks.add(taskId);
  }
};

// System Metrics (Simulated)
const cpuUsage = ref(12);
const memoryUsage = ref(248);
const networkUsage = ref(45);

let metricsInterval;
watch(() => store.isRunning, (running) => {
  if (running) {
    metricsInterval = setInterval(() => {
      cpuUsage.value = Math.floor(Math.random() * 30) + 10;
      memoryUsage.value = Math.floor(Math.random() * 100) + 200;
      networkUsage.value = Math.floor(Math.random() * 50) + 20;
    }, 2000);
  } else {
    clearInterval(metricsInterval);
    cpuUsage.value = 5;
    memoryUsage.value = 180;
    networkUsage.value = 0;
  }
});

const totalSteps = computed(() => store.tasks.length);
const currentTask = computed(() => store.tasks[currentStepIndex.value]);

const taskContent = computed(() => {
  if (currentTask.value) {
    return currentTask.value.output || currentTask.value.logs.join('\n') || '暂无输出内容';
  }
  // Solo/quick mode: no tasks, show accumulated executeBuffer content
  return store.executeBuffer || '';
});

const dashboardStatus = computed(() => {
  if (store.isRunning) return 'running';
  if (store.tasks.some(t => t.status === 'completed')) return 'completed';
  return 'idle';
});

const taskPhase = computed(() => {
  if (dashboardStatus.value === 'running') return 'agentStatus.phases.executing';
  if (dashboardStatus.value === 'completed') return 'agentStatus.phases.finished';
  return 'agentStatus.phases.ready';
});

const statusLabel = (status) => {
  const map = { pending: '待执行', running: '执行中', completed: '完成', failed: '失败' };
  return map[status] || status;
};

const formatElapsed = (startTime, endTime) => {
  const ms = (endTime || Date.now()) - startTime;
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`;
};

const outputLineCount = (text) => {
  if (!text) return 0;
  return text.split('\n').length;
};

const displayOutput = (task) => {
  const text = task.output || task.logs.join('\n') || '';
  return text.trim() || '(无输出)';
};

const artifactIcon = (type) => {
  const icons = {
    python: '🐍', notebook: '📓', markdown: '📝', text: '📄',
    csv: '📊', json: '📋', image: '🖼️', pdf: '📕',
    html: '🌐', excel: '📈', archive: '📦', file: '📄'
  };
  return icons[type] || '📄';
};

const formatSize = (bytes) => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
};

const detectLanguage = (task) => {
  const content = task
    ? (task.output || (task.logs ? task.logs.join('\n') : ''))
    : (store.executeBuffer || '');
  if (!content) return 'plaintext';
  if (content.trim().startsWith('{') || content.trim().startsWith('[')) return 'json';
  if (content.includes('def ') || content.includes('import ')) return 'python';
  return 'markdown';
};

const prevStep = () => {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--;
    autoScroll.value = false;
  }
};

const nextStep = () => {
  if (currentStepIndex.value < totalSteps.value - 1) {
    currentStepIndex.value++;
    if (currentStepIndex.value === totalSteps.value - 1) {
      autoScroll.value = true;
    }
  }
};

const handleKeydown = (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if (e.key === 'ArrowLeft') prevStep();
  if (e.key === 'ArrowRight') nextStep();
};

watch(() => store.tasks.length, (newLen) => {
  if (autoScroll.value) {
    currentStepIndex.value = Math.max(0, newLen - 1);
  }
});

watch(currentStepIndex, (newVal) => {
  const endIndex = Math.max(0, totalSteps.value - 1);
  autoScroll.value = newVal === endIndex;
});

// Auto-scroll terminal consoles when logs change
watch(() => store.tasks.map(t => t.logs.length), () => {
  store.tasks.forEach(t => {
    if ((expandedTasks.has(t.id) || t.status === 'running') && t.logs.length > 0) {
      scrollConsoleToBottom(t.id);
    }
  });
}, { deep: false });

// Auto-expand running tasks
watch(() => store.tasks.map(t => t.status), (statuses) => {
  store.tasks.forEach(task => {
    if (task.status === 'running') {
      expandedTasks.add(task.id);
    }
  });
}, { deep: true });

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown);
  clearInterval(metricsInterval);
});

const openLogDrawer = () => {
  isLogDrawerOpen.value = true;
};

defineExpose({ openLogDrawer });
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
</style>
