<template>
  <div class="h-full flex flex-col bg-white relative">
    <!-- Unified Header -->
    <div class="flex-none px-4 py-1.5 border-b border-indigo-100/50 flex items-center justify-end bg-white z-20">
      <!-- Center: View Switcher (Tabs) -->
      <a-segmented v-model:value="activeView" :options="views.map(v => ({ value: v.id, payload: v }))" size="small">
        <template #label="{ payload }">
          <div class="flex items-center gap-1.5 px-1 py-0.5">
            <component :is="payload.icon" class="text-xs" />
            <span class="text-xs font-medium">{{ t(payload.labelKey) }}</span>
          </div>
        </template>
      </a-segmented>
    </div>

     <!-- Editor Area -->
    <div class="flex-1 flex flex-col overflow-hidden bg-white relative">
       <!-- Agent Status Dashboard (Only in Tasks view) -->
       <div v-if="(currentTask || store.isRunning) && activeView === 'tasks'" class="flex-none px-4 pt-4 pb-2 bg-white z-10 border-b border-slate-50">
              <AgentStatusDashboard 
                  :agentName="agentName || '智能体'"
                  :sessionId="sessionId"
                  :status="dashboardStatus"
                  :progress="taskProgress"
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
       </div>

       <div class="flex-1 overflow-hidden relative flex flex-col">
          <template v-if="currentTask || activeView === 'code' || activeView === 'results' || activeView === 'graph'">
              <!-- Task View -->
              <div v-if="activeView === 'tasks'" class="h-full overflow-y-auto p-4 custom-scrollbar">
                 <!-- Task List / Details -->
                  <div class="space-y-4 pb-20">
                      <div v-for="(task, idx) in store.tasks" :key="idx" 
                           class="p-4 rounded-lg border transition-all cursor-pointer bg-white shadow-sm group"
                           :class="idx === currentStepIndex ? 'border-indigo-500 ring-1 ring-indigo-500 shadow-md' : 'border-slate-200 hover:border-indigo-300'"
                           @click="currentStepIndex = idx"
                      >
                          <div class="flex justify-between items-start mb-2">
                              <h4 class="font-bold text-slate-800 text-sm group-hover:text-indigo-600 transition-colors">{{ task.name || `Task #${idx + 1}` }}</h4>
                              <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200 uppercase tracking-wide">
                                  {{ detectLanguage(task) }}
                              </span>
                          </div>
                          <p class="text-xs text-slate-500 font-mono bg-slate-50 p-2 rounded border border-slate-100 line-clamp-3">
                              {{ task.logs.join('\n') || 'No output' }}
                          </p>
                      </div>
                  </div>
              </div>

              <!-- Graph View -->
              <div v-else-if="activeView === 'graph'" class="h-full w-full">
                  <TaskGraph />
              </div>

              <!-- Code View -->
              <ArtifactEditor  
                  v-else-if="activeView === 'code'"
                  :value="taskContent"
                  :language="detectLanguage(currentTask)"
                  :read-only="true"
                  class="h-full w-full"
              />

              <!-- Results View -->
              <SandboxResultViewer 
                  v-else-if="activeView === 'results'"
                  :code="currentTask ? taskContent : ''"
                  :language="currentTask ? detectLanguage(currentTask) : 'python'"
                  :title="currentTask ? currentTask.name : '沙箱'"
                  :auto-run="false"
                  class="h-full w-full border-none rounded-none"
              />

              <!-- Terminal View -->
              <div v-else-if="activeView === 'terminal'" class="h-full w-full bg-slate-900">
                   <SandboxTerminal 
                       ref="terminalRef" 
                       theme="dark" 
                       :readOnly="false"
                   />
              </div>
          </template>
          
          <div v-else class="h-full w-full flex items-center justify-center bg-slate-50/20">
               <div v-if="store.isRunning" class="w-full max-w-md p-8 flex flex-col items-center select-none">
                   <!-- AI Loading Animation -->
                   <div class="relative w-24 h-24 mb-6">
                       <div class="absolute inset-0 border-t-4 border-indigo-500 rounded-full animate-spin"></div>
                       <div class="absolute inset-2 border-r-4 border-purple-500 rounded-full animate-[spin_3s_linear_infinite_reverse]"></div>
                       <div class="absolute inset-4 border-b-4 border-pink-500 rounded-full animate-[spin_2s_linear_infinite]"></div>
                       <div class="absolute inset-0 flex items-center justify-center font-mono text-xs font-bold text-indigo-600 animate-pulse">AI</div>
                   </div>
                   <p class="text-center bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 font-bold animate-pulse">
                       {{ t('aiGenerating') }}
                   </p>
                   <p class="text-center text-slate-400 text-xs mt-2 font-mono">
                       Processing autonomous logic...
                   </p>
               </div>
               <EmptyState v-else />
           </div>

           <!-- Terminal Overlay (Bottom Drawer) - Removed as it is now a main view -->
           <!-- <transition name="slide-up"> ... </transition> -->
       </div>
    </div>
    
    <!-- Log Navigation Footer (Player Style) -->
    <div v-if="totalSteps > 0" class="px-4 py-2 bg-white border-t border-slate-200 z-20">
        <div class="flex items-center gap-3 max-w-2xl mx-auto">
            <!-- Controls Group -->
            <div class="flex items-center gap-0.5 p-0.5 bg-slate-100 rounded-lg border border-slate-200 shadow-sm">
                <button 
                    @click="prevStep" 
                    :disabled="currentStepIndex <= 0"
                    class="w-7 h-6 flex items-center justify-center rounded hover:bg-white hover:text-indigo-600 hover:shadow-sm text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
                    title="上一步"
                >
                    <LeftOutlined :style="{ fontSize: '10px' }" />
                </button>
                <button 
                    @click="nextStep" 
                    :disabled="currentStepIndex >= totalSteps - 1"
                    class="w-7 h-6 flex items-center justify-center rounded hover:bg-white hover:text-indigo-600 hover:shadow-sm text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
                    title="下一步"
                >
                    <RightOutlined :style="{ fontSize: '10px' }" />
                </button>
            </div>

            <!-- Slider Group -->
            <div class="flex-1 flex items-center gap-3 bg-slate-50 px-3 py-0.5 rounded-lg border border-slate-200 h-8">
                <span class="text-[10px] font-medium text-slate-400 font-mono min-w-[1.2rem] text-right">{{ currentStepIndex + 1 }}</span>
                <a-slider 
                    v-model:value="currentStepIndex" 
                    :min="0" 
                    :max="Math.max(0, totalSteps - 1)" 
                    :disabled="totalSteps === 0"
                    class="flex-1 !m-0"
                    :tooltipOpen="false"
                    size="small"
                />
                <span class="text-[10px] font-medium text-slate-400 font-mono min-w-[1.2rem]">{{ totalSteps || 0 }}</span>
            </div>

            <!-- Log Button -->
            <button 
                @click="openLogDrawer"
                class="w-7 h-6 flex items-center justify-center rounded hover:bg-slate-100 text-slate-500 transition-colors log-trigger"
                title="View Logs"
            >
                <FileTextOutlined :style="{ fontSize: '12px' }" />
            </button>
        </div>
    </div>

    <!-- Control Bar (only when running) -->
    <div v-if="store.isRunning" class="px-4 py-2 bg-slate-50 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
        <div class="flex items-center gap-2">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span>正在执行: {{ currentTask?.name || 'Processing...' }}</span>
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
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import ArtifactEditor from '@/features/workflow/components/editor/ArtifactEditor.vue';
import SandboxResultViewer from '@/features/sandbox/components/SandboxResultViewer.vue';
import EmptyState from '@/features/workflow/components/EmptyState.vue';
import LogDrawer from '@/features/workflow/components/drawer/LogDrawer.vue';
import AgentStatusDashboard from '@/features/workflow/components/AgentStatusDashboard.vue';
import SandboxTerminal from '@/features/sandbox/components/SandboxTerminal.vue';
import TaskTree from './TaskTree.vue';
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
    DownOutlined,
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
const isTerminalOpen = ref(false);
const terminalRef = ref(null);

// System Metrics (Simulated)
const cpuUsage = ref(12);
const memoryUsage = ref(248);
const networkUsage = ref(45);

// Update metrics periodically when running
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

const views = [
    { id: 'tasks', labelKey: 'taskView', icon: AppstoreOutlined },
    { id: 'graph', labelKey: 'graphView', icon: ApartmentOutlined },
    { id: 'code', labelKey: 'codeView', icon: CodeOutlined },
    { id: 'results', labelKey: 'runResults', icon: PlayCircleOutlined },
    { id: 'terminal', labelKey: 'terminal', icon: CodeOutlined }
];

const totalSteps = computed(() => store.tasks.length);
const currentTask = computed(() => store.tasks[currentStepIndex.value]);

const taskContent = computed(() => {
    if (!currentTask.value) return '';
    return currentTask.value.logs.join('\n') || '暂无输出内容';
});

// Mock data for dashboard
const dashboardStatus = computed(() => {
    if (store.isRunning && currentStepIndex.value === totalSteps.value - 1) return 'running';
    if (currentTask.value) return 'completed';
    return 'idle';
});

const taskProgress = computed(() => {
    if (dashboardStatus.value === 'running') return 65; 
    if (dashboardStatus.value === 'completed') return 100;
    return 0;
});

const taskPhase = computed(() => {
    if (dashboardStatus.value === 'running') return 'agentStatus.phases.executing';
    if (dashboardStatus.value === 'completed') return 'agentStatus.phases.finished';
    return 'agentStatus.phases.ready';
});

// Auto-switch view logic
watch(dashboardStatus, (newStatus) => {
    if (newStatus === 'running') {
        activeView.value = 'code';
    } else if (newStatus === 'completed') {
        activeView.value = 'results';
    }
});

const detectLanguage = (task) => {
    if (!task) return 'plaintext';
    const content = task.logs.join('\n');
    if (content.trim().startsWith('{') || content.trim().startsWith('[')) return 'json';
    if (content.includes('def ') || content.includes('import ')) return 'python';
    if (task.name.includes('Markdown')) return 'markdown';
    return 'markdown'; 
};

const toggleTerminal = () => {
    isTerminalOpen.value = !isTerminalOpen.value;
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
    if (e.ctrlKey && e.key === '`') {
        toggleTerminal();
        e.preventDefault();
    }
};

watch(() => store.tasks.length, (newLen, oldLen) => {
    if (autoScroll.value) {
        currentStepIndex.value = Math.max(0, newLen - 1);
    }
});

watch(currentStepIndex, (newVal) => {
    const endIndex = Math.max(0, totalSteps.value - 1);
    autoScroll.value = newVal === endIndex;
});

onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
});

onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleKeydown);
});

const openLogDrawer = () => {
    isLogDrawerOpen.value = true;
};

defineExpose({
    openLogDrawer
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
