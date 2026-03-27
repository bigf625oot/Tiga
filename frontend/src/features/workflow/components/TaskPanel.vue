<template>
  <div class="h-full flex flex-col bg-background relative font-sans">

    <!-- ── 3.1 任务概览 Header ── -->
    <div v-if="showEmbeddedHeader && (store.isRunning || store.tasks.length > 0)" class="flex-none border-b border-border bg-background/95 backdrop-blur-sm">
      <!-- Tab Nav -->
      <div class="flex items-center gap-1 px-3 pt-2 pb-0">
        <!-- Goal title -->
        <div class="flex items-start justify-between gap-3 flex-1">
          <h3 class="text-sm font-semibold text-foreground line-clamp-2 leading-tight flex-1">
            {{ goalTitle || (store.isRunning ? '任务执行中...' : '等待任务分配') }}
          </h3>
          <div class="flex items-center gap-2 flex-none">
            <!-- View Switcher -->
            <div class="flex gap-1 bg-muted/50 p-1 rounded-md mr-2" v-if="store.tasks.length > 0">
              <button v-for="view in ['graph', 'markdown', 'code', 'results']" :key="view"
                      @click="activeView = view"
                      class="px-2 py-1 text-[10px] font-medium rounded transition-colors capitalize"
                      :class="activeView === view ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'">
                {{ view }}
              </button>
            </div>
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
    <div class="flex-1 overflow-hidden relative flex flex-col">
      <!-- Empty State -->
      <div v-if="!store.isRunning && store.tasks.length === 0 && !store.artifacts?.length && activeView === 'graph'" class="flex-1 h-full w-full flex flex-col items-center justify-center bg-muted/5 text-muted-foreground gap-4">
        <div class="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-muted/40 to-muted/10 flex items-center justify-center border border-border/50 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
          <Network class="w-8 h-8 text-muted-foreground/40 drop-shadow-sm stroke-[1.5]" />
          <!-- 装饰性光晕点 -->
          <div class="absolute -top-1 -right-1 w-3 h-3 bg-primary/20 rounded-full blur-[2px]"></div>
          <div class="absolute -bottom-2 -left-2 w-4 h-4 bg-muted-foreground/10 rounded-full blur-[3px]"></div>
        </div>
        <div class="text-center">
          <p class="text-sm font-medium text-foreground mb-1">等待任务分配</p>
          <p class="text-xs max-w-[200px]">系统正在分析您的需求，即将在此生成工作流图谱并开始执行任务。</p>
        </div>
      </div>

      <!-- Graph View -->
      <div v-show="activeView === 'graph' && (store.isRunning || store.tasks.length > 0 || store.artifacts?.length)" key="graph" class="flex-1 h-full w-full overflow-hidden bg-muted/5">
        <TaskGraph v-if="activeView === 'graph' || store.tasks.length > 0" />
      </div>

      <!-- Code View -->
      <ArtifactEditor
        v-show="activeView === 'code'"
        key="code"
        :value="taskContent"
        :language="detectLanguage(currentTask)"
        :read-only="true"
        class="flex-1 h-full w-full"
      />

      <!-- Markdown Output View -->
      <div v-show="activeView === 'markdown'" key="markdown" class="flex-1 h-full w-full overflow-y-auto p-6 bg-background custom-scrollbar">
        <div class="max-w-3xl mx-auto prose prose-sm dark:prose-invert">
          <div class="mb-6 flex items-center gap-2 border-b border-border pb-2">
            <h3 class="text-lg font-semibold m-0 p-0 text-foreground">{{ currentTask ? currentTask.name : '执行结果' }}</h3>
            <span v-if="currentTask?.status === 'completed'" class="px-2 py-0.5 rounded text-[10px] bg-green-500/10 text-green-600 border border-green-500/20">已完成</span>
            <span v-else-if="currentTask?.status === 'failed'" class="px-2 py-0.5 rounded text-[10px] bg-red-500/10 text-red-600 border border-red-500/20">执行失败</span>
          </div>
          <div v-if="taskContent" v-html="renderMarkdown(taskContent)"></div>
          <div v-else class="text-muted-foreground italic text-sm">暂无文本输出内容</div>
        </div>
      </div>

      <!-- Results / Sandbox View -->
      <SandboxResultViewer
        v-show="activeView === 'results'"
        key="results"
        :code="currentTask ? taskContent : ''"
        :language="currentTask ? detectLanguage(currentTask) : 'python'"
        :title="currentTask && currentTask.name ? currentTask.name : '沙箱'"
        :auto-run="false"
        class="flex-1 h-full w-full border-none rounded-none"
      />

      <!-- Terminal View -->
      <div v-show="activeView === 'terminal'" key="terminal" class="flex-1 h-full w-full bg-slate-900">
        <!-- Optional SandboxTerminal could go here if needed -->
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
import TaskGraph from './graph/TaskGraph.vue';
import { Network } from 'lucide-vue-next';
import {
  CodeOutlined,
  PlayCircleOutlined,
  StopOutlined,
  FileTextOutlined,
  ApartmentOutlined
} from '@ant-design/icons-vue';
import { markRaw } from 'vue';
import { marked } from 'marked';

defineProps({
  embedded: { type: Boolean, default: false },
  showEmbeddedHeader: { type: Boolean, default: true },
  sessionId: { type: String, default: '' },
  agentName: { type: String, default: '' },
  isWorkflowMode: { type: Boolean, default: true },
  attachmentsCount: { type: Number, default: 0 }
});

const store = useWorkflowStore();
const activeView = ref('graph');
const isLogDrawerOpen = ref(false);

// ── Display Data ──
const currentTask = computed(() => {
  if (store.selectedTaskId) {
    return store.tasks.find(t => t.id === store.selectedTaskId) || null;
  }
  return store.tasks.find(t => t.status === 'running') || store.tasks[store.tasks.length - 1] || null;
});

const taskContent = computed(() => {
  if (currentTask.value) {
    return currentTask.value.output || currentTask.value.logs.join('\n') || '';
  }
  return store.executeBuffer || '';
});

const renderMarkdown = (text) => {
  if (!text) return '';
  return marked(text);
};

// ── Context-Aware View Switching ──
watch(() => [currentTask.value?.status, store.artifacts.length, taskContent.value], ([status, artifactCount, content]) => {
  if (!currentTask.value) return;

  // 1. If task is running and has code, show code view
  if (status === 'running') {
    const lang = detectLanguage(currentTask.value);
    if (lang === 'python' || lang === 'json' || lang === 'vue') {
       activeView.value = 'code';
    } else {
       activeView.value = 'graph';
    }
  }

  // 2. If task completed
  if (status === 'completed') {
    if (artifactCount > 0) {
      // Check if artifacts are visual (image, html, pdf)
      const hasVisualArtifacts = store.artifacts.some(a => ['image', 'html', 'pdf'].includes(a.type));
      if (hasVisualArtifacts) {
        activeView.value = 'results';
      } else {
        activeView.value = 'markdown'; // Switch to output view if just files
      }
    } else if (content) {
      // If there is textual output, switch to markdown view so user can read it
      const lang = detectLanguage(currentTask.value);
      if (lang === 'python' || lang === 'json' || lang === 'vue') {
        activeView.value = 'code';
      } else {
        activeView.value = 'markdown';
      }
    } else {
      activeView.value = 'graph';
    }
  }
});

// Watch for manual selection from graph to switch view
watch(() => store.selectedTaskId, (newId) => {
  if (newId) {
     const task = store.tasks.find(t => t.id === newId);
     if (task && (task.output || task.logs.length > 0)) {
        const lang = detectLanguage(task);
        if (lang === 'python' || lang === 'json' || lang === 'vue') {
          activeView.value = 'code';
        } else {
          activeView.value = 'markdown';
        }
     }
  }
});

// ── Goal title (derived from first log or first task description) ──
const goalTitle = computed(() => {
  const planLog = store.logs.find(l => l.step === 'plan' && l.message?.includes('规划'));
  if (planLog) return planLog.message.replace(/规划.*?：/, '').slice(0, 60);
  if (store.tasks.length > 0) return `执行计划：${store.tasks.length} 个步骤`;
  return '';
});

// ── Current running task ──
const currentRunningTask = computed(() => store.tasks.find(t => t.status === 'running'));

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
onBeforeUnmount(() => { });
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

.custom-scrollbar-dark::-webkit-scrollbar { width: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-track { background: transparent; }
</style>
