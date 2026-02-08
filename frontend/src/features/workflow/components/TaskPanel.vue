<template>
  <div class="h-full flex flex-col bg-slate-50 relative">
     <!-- Header -->
     <div v-if="!embedded" class="bg-white px-4 py-3 border-b border-slate-100 flex justify-between items-center shadow-sm z-10">
         <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                <AppstoreOutlined class="text-indigo-600" />
            </div>
            <span class="text-sm font-bold text-slate-800 leading-none">任务详情</span>
         </div>
         
         <div class="flex items-center gap-2">
             <span class="text-xs px-2 py-0.5 rounded-full font-medium transition-colors" 
                :class="store.isRunning ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'">
                {{ store.isRunning ? '执行中' : '空闲' }}
             </span>
             
             <button 
               @click="isLogDrawerOpen = true"
               class="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 transition-colors"
               title="查看系统日志"
            >
               <CodeOutlined />
            </button>
        </div>
    </div>
     
     <!-- Editor Area (Replacing Task Tree) -->
    <div class="flex-1 flex flex-col overflow-hidden bg-white relative">
       <div v-if="embedded && showEmbeddedHeader" class="flex-none px-4 py-3 border-b border-slate-100 bg-white/80 backdrop-blur-sm">
           <div class="flex items-center justify-between gap-3">
               <div class="min-w-0">
                   <div class="flex items-center gap-2">
                       <span class="text-sm font-bold text-slate-800 leading-none">任务空间</span>
                       <span class="text-xs px-2 py-0.5 rounded-full font-medium transition-colors"
                           :class="store.isRunning ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'">
                           {{ store.isRunning ? '执行中' : '空闲' }}
                       </span>
                       <button
                          @click="isLogDrawerOpen = true"
                          class="shrink-0 p-1.5 rounded-md hover:bg-slate-100 text-slate-500 transition-colors"
                          title="查看系统日志"
                      >
                          <CodeOutlined />
                      </button>
                  </div>
                   <div class="mt-2">
                       <a-progress :percent="store.progress" size="small" :strokeWidth="6" :showInfo="false" />
                   </div>
               </div>
           </div>
       </div>

       <div class="flex-1 overflow-hidden">
           <ArtifactEditor 
               v-if="currentTask"
               :value="taskContent"
               :language="detectLanguage(currentTask)"
               :read-only="true"
               class="h-full w-full"
           />
           <div v-else class="h-full w-full">
               <div v-if="store.isRunning" class="h-full w-full p-8 flex flex-col justify-center">
                   <a-skeleton active :paragraph="{ rows: 8 }" />
               </div>
               <EmptyState v-else />
           </div>
       </div>
    </div>
    
    <!-- Log Navigation Footer (Player Style) -->
    <div v-if="totalSteps > 0" class="px-4 py-2 bg-white/95 backdrop-blur-md border-t border-slate-200/60 shadow-[0_-4px_20px_rgba(0,0,0,0.03)] z-20">
        <div class="flex items-center gap-3 max-w-2xl mx-auto">
            <!-- Controls Group -->
            <div class="flex items-center gap-0.5 p-0.5 bg-slate-100/80 rounded-lg border border-slate-200/60 shadow-sm">
                <button 
                    @click="prevStep" 
                    :disabled="currentStepIndex <= 0"
                    class="w-6 h-6 flex items-center justify-center rounded hover:bg-white hover:text-indigo-600 hover:shadow-sm text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
                    title="上一步"
                >
                    <LeftOutlined :style="{ fontSize: '10px' }" />
                </button>
                <div class="w-px h-3 bg-slate-200 mx-0.5"></div>
                <button 
                    @click="nextStep" 
                    :disabled="currentStepIndex >= totalSteps - 1"
                    class="w-6 h-6 flex items-center justify-center rounded hover:bg-white hover:text-indigo-600 hover:shadow-sm text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
                    title="下一步"
                >
                    <RightOutlined :style="{ fontSize: '10px' }" />
                </button>
            </div>

            <!-- Slider Group -->
            <div class="flex-1 flex items-center gap-3 bg-slate-50/50 px-3 py-0.5 rounded-lg border border-slate-100 h-8">
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
        </div>
    </div>

    <!-- Control Bar (only when running) -->
    <div v-if="store.isRunning" class="px-4 py-2 bg-slate-50 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
        <span class="animate-pulse">正在执行: {{ currentTask?.name || '初始化...' }}</span>
        <button 
            @click="store.stopWorkflow" 
            class="text-red-500 hover:text-red-600 hover:bg-red-50 p-1 rounded transition-colors"
            title="停止"
        >
            <StopOutlined />
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
import EmptyState from '@/features/workflow/components/EmptyState.vue';
import LogDrawer from '@/features/workflow/components/drawer/LogDrawer.vue';
import { 
    AppstoreOutlined, CodeOutlined, LeftOutlined, RightOutlined, StopOutlined 
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
const isLogDrawerOpen = ref(false);
const currentStepIndex = ref(0);
const autoScroll = ref(true);

const totalSteps = computed(() => store.tasks.length);
const currentTask = computed(() => store.tasks[currentStepIndex.value]);

const taskContent = computed(() => {
    if (!currentTask.value) return '';
    return currentTask.value.logs.join('\n') || '暂无输出内容';
});

const detectLanguage = (task) => {
    if (!task) return 'plaintext';
    const content = task.logs.join('\n');
    if (content.trim().startsWith('{') || content.trim().startsWith('[')) return 'json';
    if (content.includes('def ') || content.includes('import ')) return 'python';
    if (task.name.includes('Markdown')) return 'markdown';
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
        // If we reached the end, maybe re-enable autoScroll?
        if (currentStepIndex.value === totalSteps.value - 1) {
            autoScroll.value = true;
        }
    }
};

// Keyboard Shortcuts
const handleKeydown = (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowLeft') prevStep();
    if (e.key === 'ArrowRight') nextStep();
};

watch(() => store.tasks.length, (newLen, oldLen) => {
    if (autoScroll.value) {
        currentStepIndex.value = Math.max(0, newLen - 1);
    }
});

// Also watch user manual interaction with slider to disable autoScroll if not at end
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
</style>
