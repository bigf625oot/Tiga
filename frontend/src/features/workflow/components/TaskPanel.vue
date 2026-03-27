<template>
  <div class="h-full flex flex-col bg-background relative font-sans">

    <!-- ── 3.1 任务概览 Header ── -->
    <div class="flex-none border-b border-border bg-background/95 backdrop-blur-sm">
      <!-- Tab Nav -->
      <div class="flex items-center gap-1 px-3 pt-2 pb-0">
        <button
          v-for="v in VIEWS"
          :key="v.id"
          @click="activeView = v.id"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t-md transition-all border-b-2"
          :class="activeView === v.id
            ? 'border-primary text-primary bg-primary/5'
            : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'"
        >
          <component :is="v.icon" class="w-3.5 h-3.5" />
          {{ v.label }}
        </button>
      </div>

      <!-- Task Overview (only in tasks view) -->
      <div v-if="activeView === 'tasks'" class="px-4 py-3 space-y-2">
        <!-- Goal title -->
        <div class="flex items-start justify-between gap-3">
          <h3 class="text-sm font-semibold text-foreground line-clamp-2 leading-tight flex-1">
            {{ goalTitle || (store.isRunning ? '任务执行中...' : '等待任务分配') }}
          </h3>
          <div class="flex items-center gap-2 flex-none">
            <!-- Status badge -->
            <span v-if="store.isRunning"
              class="inline-flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-medium animate-pulse">
              <span class="w-1.5 h-1.5 rounded-full bg-primary inline-block"></span>
              Running
            </span>
            <span v-else-if="store.tasks.length > 0 && store.tasks.every(t => t.status === 'completed')"
              class="inline-flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 border border-green-500/20 font-medium">
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
              Success
            </span>
            <span v-else-if="store.tasks.some(t => t.status === 'failed')"
              class="inline-flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-600 border border-red-500/20 font-medium">
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              Failed
            </span>
            <span v-else class="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border font-medium">
              Idle
            </span>
          </div>
        </div>

        <!-- Progress bar -->
        <div v-if="store.tasks.length > 0" class="flex items-center gap-2">
          <div class="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              class="h-full rounded-full transition-[width] duration-700 ease-out"
              :class="store.progress === 100 ? 'bg-green-500' : 'bg-primary'"
              :style="{ width: store.progress + '%' }"
            />
          </div>
          <span class="text-[10px] font-mono font-semibold text-primary min-w-[2.5rem] text-right">
            {{ store.completedTasks }}/{{ store.totalTasks }}
          </span>
        </div>
      </div>
    </div>

    <!-- ── Main Content Area ── -->
    <div class="flex-1 overflow-hidden relative flex">

      <!-- Tasks Timeline View -->
      <div v-if="activeView === 'tasks'" class="flex-1 flex overflow-hidden">

        <!-- Left: Timeline Steps -->
        <div class="w-64 flex-none border-r border-border flex flex-col overflow-hidden bg-muted/20">
          <div class="flex-1 overflow-y-auto py-3 custom-scrollbar">
            <!-- Empty state -->
            <div v-if="store.tasks.length === 0 && !store.isRunning"
              class="flex flex-col items-center justify-center py-12 px-4 text-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
                <svg class="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
              </div>
              <p class="text-xs text-muted-foreground font-mono">等待任务分配...</p>
            </div>

            <!-- Waiting for plan -->
            <div v-else-if="store.tasks.length === 0 && store.isRunning"
              class="flex flex-col items-center justify-center py-12 px-4 gap-3">
              <div class="relative w-8 h-8">
                <div class="absolute inset-0 border-t-2 border-primary rounded-full animate-spin"></div>
                <div class="absolute inset-1.5 border-r-2 border-primary/40 rounded-full animate-[spin_1.5s_linear_infinite_reverse]"></div>
              </div>
              <p class="text-xs text-muted-foreground font-mono">规划中...</p>
            </div>

            <!-- Step Timeline -->
            <div v-else class="px-3 space-y-0.5">
              <div
                v-for="(task, idx) in store.tasks"
                :key="task.id"
                class="relative flex items-start gap-2.5 group cursor-pointer rounded-lg px-2 py-2.5 transition-all"
                :class="[
                  selectedStepId === task.id
                    ? 'bg-primary/8 ring-1 ring-primary/20'
                    : 'hover:bg-muted/60',
                ]"
                @click="selectedStepId = task.id"
              >
                <!-- Vertical line connector -->
                <div v-if="idx < store.tasks.length - 1"
                  class="absolute left-[19px] top-[28px] bottom-0 w-px bg-border z-0"
                />

                <!-- Step status indicator -->
                <div class="relative flex-none z-10 mt-0.5">
                  <!-- Running: pulse -->
                  <span v-if="task.status === 'running'"
                    class="relative inline-flex w-5 h-5 items-center justify-center">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-60"></span>
                    <span class="relative inline-flex w-3 h-3 rounded-full bg-primary"></span>
                  </span>
                  <!-- Completed: green check -->
                  <span v-else-if="task.status === 'completed'"
                    class="inline-flex w-5 h-5 items-center justify-center rounded-full bg-green-500/15 text-green-500">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                    </svg>
                  </span>
                  <!-- Failed: red X -->
                  <span v-else-if="task.status === 'failed'"
                    class="inline-flex w-5 h-5 items-center justify-center rounded-full bg-red-500/15 text-red-500">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </span>
                  <!-- Pending: grey dot -->
                  <span v-else
                    class="inline-flex w-5 h-5 items-center justify-center">
                    <span class="w-2.5 h-2.5 rounded-full bg-muted-foreground/30 border border-muted-foreground/20"></span>
                  </span>
                </div>

                <!-- Step info -->
                <div class="flex-1 min-w-0 pt-0.5">
                  <div class="flex items-center justify-between gap-1">
                    <p class="text-xs font-medium text-foreground truncate leading-tight"
                      :class="task.status === 'running' ? 'text-primary' : ''">
                      {{ task.name }}
                    </p>
                    <span class="text-[9px] font-mono text-muted-foreground/60 flex-none">
                      {{ idx + 1 }}
                    </span>
                  </div>
                  <!-- Elapsed time -->
                  <p v-if="task.startTime" class="text-[10px] text-muted-foreground font-mono mt-0.5">
                    {{ formatElapsed(task.startTime, task.endTime) }}
                  </p>
                  <!-- Tool call mini badges -->
                  <div v-if="task.toolCalls && task.toolCalls.length > 0" class="flex flex-wrap gap-1 mt-1">
                    <span v-for="(tc, ti) in task.toolCalls.slice(0, 3)" :key="ti"
                      class="inline-flex items-center gap-0.5 text-[9px] px-1.5 py-0.5 rounded font-mono border"
                      :class="{
                        'border-primary/30 bg-primary/5 text-primary': tc.status === 'running',
                        'border-green-500/30 bg-green-500/5 text-green-700': tc.status === 'completed',
                        'border-red-500/30 bg-red-500/5 text-red-600': tc.status === 'failed',
                      }">
                      <span v-if="tc.status === 'running'" class="w-1 h-1 rounded-full bg-primary animate-pulse"></span>
                      {{ tc.tool_name }}
                    </span>
                    <span v-if="task.toolCalls.length > 3"
                      class="text-[9px] text-muted-foreground font-mono">
                      +{{ task.toolCalls.length - 3 }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Resource monitor footer (PRD §3.4) -->
          <div v-if="store.isRunning" class="flex-none border-t border-border px-3 py-2 flex items-center gap-3 bg-muted/10">
            <div class="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground">
              <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
              <span>CPU {{ cpuUsage }}%</span>
            </div>
            <div class="flex items-center gap-1 text-[10px] font-mono text-muted-foreground">
              <span>MEM {{ memoryUsage }}M</span>
            </div>
          </div>
        </div>

        <!-- Right: Sandbox Detail (PRD §3.3) -->
        <div class="flex-1 flex flex-col overflow-hidden bg-slate-950">
          <!-- Detail header -->
          <div class="flex-none flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/80">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full"
                :class="{
                  'bg-primary animate-pulse': selectedStep?.status === 'running',
                  'bg-green-400': selectedStep?.status === 'completed',
                  'bg-red-400': selectedStep?.status === 'failed',
                  'bg-slate-500': !selectedStep || selectedStep.status === 'pending',
                }">
              </span>
              <span class="text-xs text-slate-300 font-mono truncate">
                {{ selectedStep ? selectedStep.name : '选择左侧步骤查看详情' }}
              </span>
            </div>
            <div v-if="selectedStep?.startTime" class="flex items-center gap-3 text-[10px] font-mono text-slate-500">
              <span>{{ formatElapsed(selectedStep.startTime, selectedStep.endTime) }}</span>
              <span v-if="selectedStep.toolCalls?.length"
                class="text-primary/80">{{ selectedStep.toolCalls.length }} tools</span>
            </div>
          </div>

          <!-- No step selected -->
          <div v-if="!selectedStep" class="flex-1 flex flex-col items-center justify-center text-slate-600 gap-3">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
            <p class="text-xs font-mono">← 选择步骤</p>
          </div>

          <!-- Step detail content -->
          <div v-else class="flex-1 flex flex-col overflow-hidden">
            <!-- Tool calls section -->
            <div v-if="selectedStep.toolCalls && selectedStep.toolCalls.length > 0"
              class="flex-none border-b border-slate-800 px-4 py-2 flex flex-wrap gap-2">
              <span class="text-[10px] font-mono text-slate-500 mr-1">TOOLS:</span>
              <span
                v-for="(tc, ti) in selectedStep.toolCalls"
                :key="ti"
                class="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded font-mono border"
                :class="{
                  'border-blue-500/40 bg-blue-500/10 text-blue-300': tc.status === 'running',
                  'border-green-500/40 bg-green-500/10 text-green-300': tc.status === 'completed',
                  'border-red-500/40 bg-red-500/10 text-red-300': tc.status === 'failed',
                }">
                <span v-if="tc.status === 'running'" class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
                <svg v-else-if="tc.status === 'completed'" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                </svg>
                <svg v-else-if="tc.status === 'failed'" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
                <span>{{ tc.tool_name }}</span>
                <span v-if="tc.tool_args && Object.keys(tc.tool_args).length > 0"
                  class="text-slate-500 truncate max-w-[120px]">
                  ({{ formatArgs(tc.tool_args) }})
                </span>
              </span>
            </div>

            <!-- Terminal output (PRD §3.3 — stdout) -->
            <div class="flex-1 overflow-hidden flex flex-col">
              <div class="flex-none flex items-center gap-2 px-4 py-1.5 bg-slate-900 border-b border-slate-800">
                <div class="flex gap-1.5">
                  <span class="w-2.5 h-2.5 rounded-full bg-red-500/70"></span>
                  <span class="w-2.5 h-2.5 rounded-full bg-yellow-500/70"></span>
                  <span class="w-2.5 h-2.5 rounded-full bg-green-500/70"></span>
                </div>
                <span class="text-[10px] font-mono text-slate-500 ml-1">stdout / log</span>
                <div class="ml-auto flex items-center gap-2">
                  <span v-if="selectedStep.status === 'running'"
                    class="text-[9px] font-mono text-blue-400 animate-pulse">● LIVE</span>
                  <button
                    @click="copyOutput(selectedStep)"
                    class="text-[10px] font-mono text-slate-500 hover:text-slate-300 transition-colors"
                    title="复制输出">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div
                ref="terminalOutputRef"
                class="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed custom-scrollbar-dark"
              >
                <!-- Logs lines -->
                <div v-if="selectedStep.logs && selectedStep.logs.length > 0">
                  <div
                    v-for="(line, i) in selectedStep.logs"
                    :key="i"
                    class="whitespace-pre-wrap break-all"
                    :class="isErrorLine(line) ? 'text-red-400' : isWarningLine(line) ? 'text-yellow-400' : isSuccessLine(line) ? 'text-green-400' : 'text-slate-300'"
                  >{{ line }}</div>
                </div>
                <!-- Output (LLM content) -->
                <div v-else-if="selectedStep.output"
                  class="whitespace-pre-wrap break-all text-slate-300">{{ selectedStep.output }}</div>
                <!-- Empty -->
                <div v-else class="text-slate-600 italic text-xs">
                  {{ selectedStep.status === 'running' ? '等待输出...' : '无输出记录' }}
                </div>

                <!-- Blinking cursor when running -->
                <span v-if="selectedStep.status === 'running'"
                  class="inline-block w-2 h-3.5 bg-primary/80 animate-pulse ml-0.5 align-text-bottom" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Graph View -->
      <div v-else-if="activeView === 'graph'" key="graph" class="flex-1 h-full w-full overflow-hidden">
        <TaskGraph />
      </div>

      <!-- Code View -->
      <ArtifactEditor
        v-else-if="activeView === 'code'"
        key="code"
        :value="taskContent"
        :language="detectLanguage(currentTask)"
        :read-only="true"
        class="flex-1 h-full w-full"
      />

      <!-- Results / Sandbox View -->
      <SandboxResultViewer
        v-else-if="activeView === 'results'"
        key="results"
        :code="currentTask ? taskContent : ''"
        :language="currentTask ? detectLanguage(currentTask) : 'python'"
        :title="currentTask && currentTask.name ? currentTask.name : '沙箱'"
        :auto-run="false"
        class="flex-1 h-full w-full border-none rounded-none"
      />

      <!-- Terminal View -->
      <div v-else-if="activeView === 'terminal'" key="terminal" class="flex-1 h-full w-full bg-slate-900">
        <SandboxTerminal
          ref="terminalRef"
          theme="dark"
          :readOnly="false"
        />
      </div>
    </div>

    <!-- ── Artifacts panel (always visible if any) ── -->
    <div v-if="store.artifacts && store.artifacts.length > 0"
      class="flex-none border-t border-border bg-muted/10 px-4 py-2">
      <div class="flex items-center gap-2 mb-2">
        <svg class="w-3.5 h-3.5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1.293 12.707A2 2 0 008.285 22h7.43a2 2 0 001.993-1.293L19 8"/>
        </svg>
        <span class="text-xs font-semibold text-foreground">产出物</span>
        <span class="text-[10px] text-muted-foreground ml-auto">{{ store.artifacts.length }} 个文件</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <a
          v-for="artifact in store.artifacts"
          :key="artifact.url"
          :href="artifact.url"
          target="_blank"
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-border hover:border-primary/50 hover:bg-muted/50 transition-all group"
        >
          <span class="text-sm">{{ artifactIcon(artifact.type) }}</span>
          <div class="min-w-0">
            <p class="text-xs font-medium text-foreground truncate max-w-[100px] group-hover:text-primary">{{ artifact.name }}</p>
            <p class="text-[9px] text-muted-foreground uppercase">{{ artifact.type }}{{ artifact.size ? ' · ' + formatSize(artifact.size) : '' }}</p>
          </div>
        </a>
      </div>
    </div>

    <!-- ── Control bar when running ── -->
    <div v-if="store.isRunning"
      class="flex-none px-4 py-2 bg-muted/30 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span class="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
        </span>
        <span class="font-mono">{{ currentRunningTask?.name || '执行中...' }}</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="openLogDrawer"
          class="flex items-center gap-1 px-2 py-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        >
          <FileTextOutlined :style="{ fontSize: '11px' }" />
          <span class="text-[10px]">日志</span>
        </button>
        <button
          @click="store.stopWorkflow"
          class="flex items-center gap-1 px-2 py-1 rounded text-red-500 hover:text-red-600 hover:bg-red-50 transition-colors font-medium"
        >
          <StopOutlined :style="{ fontSize: '11px' }" />
          <span class="text-[10px]">停止</span>
        </button>
      </div>
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
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import ArtifactEditor from '@/features/workflow/components/editor/ArtifactEditor.vue';
import SandboxResultViewer from '@/features/sandbox/components/SandboxResultViewer.vue';
import LogDrawer from '@/features/workflow/components/drawer/LogDrawer.vue';
import SandboxTerminal from '@/features/sandbox/components/SandboxTerminal.vue';
import TaskGraph from './graph/TaskGraph.vue';
import {
  AppstoreOutlined,
  CodeOutlined,
  PlayCircleOutlined,
  StopOutlined,
  FileTextOutlined,
  ApartmentOutlined
} from '@ant-design/icons-vue';
import { markRaw } from 'vue';

defineProps({
  embedded: { type: Boolean, default: false },
  showEmbeddedHeader: { type: Boolean, default: true },
  sessionId: { type: String, default: '' },
  agentName: { type: String, default: '' },
  isWorkflowMode: { type: Boolean, default: true },
  attachmentsCount: { type: Number, default: 0 }
});

// ── Views config ──
const VIEWS = [
  { id: 'tasks', label: '执行详情', icon: markRaw(AppstoreOutlined) },
  { id: 'graph', label: '任务图', icon: markRaw(ApartmentOutlined) },
  { id: 'code', label: '代码', icon: markRaw(CodeOutlined) },
  { id: 'results', label: '沙箱', icon: markRaw(PlayCircleOutlined) },
];

const store = useWorkflowStore();
const activeView = ref('tasks');
const isLogDrawerOpen = ref(false);
const terminalRef = ref(null);
const terminalOutputRef = ref(null);

// ── Step selection ──
const selectedStepId = ref(null);

const selectedStep = computed(() =>
  selectedStepId.value ? store.tasks.find(t => t.id === selectedStepId.value) : null
);

// Auto-select running task
watch(() => store.tasks.map(t => t.status), () => {
  const runningTask = store.tasks.find(t => t.status === 'running');
  if (runningTask) selectedStepId.value = runningTask.id;
}, { deep: false });

// Auto-select first task when plan arrives
watch(() => store.tasks.length, (newLen, oldLen) => {
  if (oldLen === 0 && newLen > 0 && !selectedStepId.value) {
    selectedStepId.value = store.tasks[0].id;
  }
});

// Auto-scroll terminal when logs update
watch(
  () => selectedStep.value?.logs?.length,
  () => {
    nextTick(() => {
      if (terminalOutputRef.value) {
        terminalOutputRef.value.scrollTop = terminalOutputRef.value.scrollHeight;
      }
    });
  }
);

// ── Goal title (derived from first log or first task description) ──
const goalTitle = computed(() => {
  const planLog = store.logs.find(l => l.step === 'plan' && l.message?.includes('规划'));
  if (planLog) return planLog.message.replace(/规划.*?：/, '').slice(0, 60);
  if (store.tasks.length > 0) return `执行计划：${store.tasks.length} 个步骤`;
  return '';
});

// ── Current running task ──
const currentRunningTask = computed(() => store.tasks.find(t => t.status === 'running'));

// ── Current task for code view ──
const currentTask = computed(() => store.tasks.find(t => t.status === 'running') || store.tasks[store.tasks.length - 1] || null);

const taskContent = computed(() => {
  if (currentTask.value) {
    return currentTask.value.output || currentTask.value.logs.join('\n') || '';
  }
  return store.executeBuffer || '';
});

// ── Resource metrics (simulated, PRD §3.4) ──
const cpuUsage = ref(12);
const memoryUsage = ref(248);
let metricsInterval;
watch(() => store.isRunning, (running) => {
  if (running) {
    metricsInterval = setInterval(() => {
      cpuUsage.value = Math.floor(Math.random() * 30) + 10;
      memoryUsage.value = Math.floor(Math.random() * 100) + 200;
    }, 2000);
  } else {
    clearInterval(metricsInterval);
    cpuUsage.value = 5;
    memoryUsage.value = 180;
  }
});

// ── Helpers ──
const formatElapsed = (startTime, endTime) => {
  const ms = (endTime || Date.now()) - startTime;
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`;
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

const isErrorLine = (line) => /error|exception|traceback|failed|err:/i.test(line);
const isWarningLine = (line) => /warning|warn:/i.test(line);
const isSuccessLine = (line) => /success|done|completed|✓|✅/i.test(line);

const formatArgs = (args) => {
  try {
    const keys = Object.keys(args);
    if (keys.length === 0) return '';
    const first = keys[0];
    const val = String(args[first]).slice(0, 30);
    return `${first}=${val}${keys.length > 1 ? '...' : ''}`;
  } catch {
    return '';
  }
};

const copyOutput = (task) => {
  const text = (task.logs?.join('\n') || task.output || '').trim();
  if (text && navigator.clipboard) {
    navigator.clipboard.writeText(text);
  }
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

const openLogDrawer = () => { isLogDrawerOpen.value = true; };
defineExpose({ openLogDrawer });

onMounted(() => {});
onBeforeUnmount(() => { clearInterval(metricsInterval); });
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

.custom-scrollbar-dark::-webkit-scrollbar { width: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-track { background: transparent; }
</style>
