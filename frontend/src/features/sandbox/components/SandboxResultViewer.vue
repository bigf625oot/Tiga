<template>
  <div class="sandbox-result-viewer h-full flex flex-col bg-white rounded-lg border border-slate-200 overflow-hidden">
    <!-- Tabs Header -->
    <div class="flex items-center border-b border-slate-200 bg-slate-50 px-2">
      <button 
        v-for="tab in ['result', 'env']" 
        :key="tab"
        @click="activeTab = tab"
        class="px-4 py-2 text-xs font-medium transition-colors border-b-2"
        :class="activeTab === tab ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
      >
        {{ tab === 'result' ? t('sandbox.tabs.result') : t('sandbox.tabs.env') }}
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-hidden flex flex-col relative">
      
      <!-- Environment Info Tab -->
      <div v-if="activeTab === 'env'" class="p-6 overflow-y-auto">
        <h3 class="text-sm font-bold text-slate-800 mb-4">{{ t('sandbox.env.title') }}</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <span class="text-xs text-slate-400 uppercase font-bold block mb-1">{{ t('sandbox.env.runtime') }}</span>
                <span class="text-sm font-mono text-slate-700">Python 3.10 (Isolated)</span>
            </div>
            <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <span class="text-xs text-slate-400 uppercase font-bold block mb-1">{{ t('sandbox.env.resourceLimits') }}</span>
                <div class="flex gap-4">
                    <div>
                        <span class="text-[10px] text-slate-400">{{ t('sandbox.env.cpu') }}</span>
                        <div class="font-mono text-sm">1.0 Core</div>
                    </div>
                    <div>
                        <span class="text-[10px] text-slate-400">{{ t('sandbox.env.memory') }}</span>
                        <div class="font-mono text-sm">512 MB</div>
                    </div>
                </div>
            </div>
             <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <span class="text-xs text-slate-400 uppercase font-bold block mb-1">{{ t('sandbox.env.network') }}</span>
                <span class="text-sm font-mono text-slate-700">{{ t('sandbox.env.egress') }}: Allowed (Whitelisted)</span>
            </div>
             <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <span class="text-xs text-slate-400 uppercase font-bold block mb-1">{{ t('sandbox.env.workspace') }}</span>
                <span class="text-sm font-mono text-slate-700">/workspace (Persistent)</span>
            </div>
        </div>
      </div>

      <!-- Result Tab -->
      <div v-else class="h-full flex flex-col">
          <div class="h-full overflow-y-auto p-4 custom-scrollbar relative">
             <div class="absolute top-2 right-2 z-10 flex gap-2">
                <a-button 
                  v-if="status === 'running'" 
                  type="text" 
                  danger 
                  size="small" 
                  @click="cancel"
                >
                  {{ t('sandbox.status.cancel') }}
                </a-button>
                <!-- Run Button Removed -->
             </div>
            <!-- Empty State -->
            <div v-if="!result && status !== 'running'" class="h-full flex flex-col items-center justify-center text-slate-400 select-none absolute inset-0">
               <div class="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-4 border border-slate-100">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="text-slate-300">
                      <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M10 8L16 12L10 16V8Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
               </div>
               <p class="text-sm font-medium text-slate-500">{{ t('sandbox.status.noData') }}</p>
            </div>

            <!-- Error State -->
            <div v-if="error" class="p-4 bg-red-50 border border-red-100 rounded-lg mb-4">
               <div class="flex items-start gap-3">
                  <CloseCircleFilled class="text-red-500 mt-0.5" />
                  <div class="flex-1">
                     <h4 class="text-sm font-bold text-red-800 mb-1">{{ t('sandbox.status.error') }}</h4>
                     <p class="text-sm text-red-600 whitespace-pre-wrap font-mono text-xs">{{ error.message || error }}</p>
                  </div>
               </div>
            </div>

            <!-- Result Content -->
            <div v-if="result" class="space-y-6">
                <!-- Text Output (Legacy view) -->
                <div v-if="result.content" class="prose prose-sm max-w-none">
                    <!-- ... existing text output logic ... -->
                    <div class="flex justify-between items-center mb-2">
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('sandbox.output.preview') }}</span>
                        </div>
                    </div>
                     <div class="markdown-body bg-white p-4 border border-slate-200 rounded-lg" v-html="renderedContent"></div>
                </div>

                <!-- Files/Images -->
                <div v-if="images.length > 0" class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('sandbox.output.generatedImages') }} ({{ images.length }})</span>
                        <div class="flex gap-1 bg-slate-100 p-1 rounded-lg">
                            <button 
                                v-for="mode in VIEW_MODES" 
                                :key="mode"
                                class="p-1 rounded hover:bg-white hover:shadow-sm transition-all text-slate-500"
                                :class="{ 'bg-white shadow-sm text-indigo-600': viewMode === mode }"
                                @click="viewMode = mode"
                            >
                                <AppstoreOutlined v-if="mode === 'grid'" />
                                <FileImageOutlined v-else />
                            </button>
                        </div>
                    </div>

                    <!-- Grid View -->
                    <div v-if="viewMode === 'grid'" class="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <div v-for="(img, idx) in images" :key="idx" class="group relative aspect-square bg-slate-100 rounded-lg overflow-hidden border border-slate-200">
                            <el-image 
                                :src="`data:image/png;base64,${img.content}`" 
                                class="w-full h-full object-contain"
                                :preview-src-list="images.map(i => `data:image/png;base64,${i.content}`)"
                                :initial-index="idx"
                                fit="contain"
                                loading="lazy"
                            />
                            <div class="absolute inset-x-0 bottom-0 bg-black/50 backdrop-blur-sm p-2 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity truncate">
                                {{ img.name }}
                            </div>
                        </div>
                    </div>

                    <!-- Carousel View -->
                    <el-carousel v-else :interval="4000" type="card" height="300px" class="bg-slate-50 rounded-lg border border-slate-200">
                        <el-carousel-item v-for="(img, idx) in images" :key="idx" class="flex items-center justify-center">
                            <el-image 
                                :src="`data:image/png;base64,${img.content}`" 
                                class="h-full w-auto max-w-full"
                                fit="contain"
                            />
                        </el-carousel-item>
                    </el-carousel>
                </div>
            </div>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue';
import { SandboxService } from '../api/sandbox';
import type { SandboxResult, SandboxFile } from '../types';
import { VueMonacoEditor } from '@guolao/vue-monaco-editor';
import { marked } from 'marked';
import { useI18n } from '../../../locales';
// import SandboxTerminal from './SandboxTerminal.vue';
import { 
    CodeOutlined, CheckCircleOutlined, CloseCircleOutlined, CloseCircleFilled,
    DownloadOutlined, AppstoreOutlined, FileImageOutlined, CopyOutlined, LeftOutlined, RightOutlined
} from '@ant-design/icons-vue';
import { ElMessage } from 'element-plus';
import { saveAs } from 'file-saver';

import JSZip from 'jszip';

const { t } = useI18n();

const props = defineProps<{
    code?: string;
    language?: string;
    template?: string;
    params?: Record<string, any>;
    title?: string;
    autoRun?: boolean;
}>();

const emit = defineEmits(['update:code', 'complete', 'error']);

// State
const activeTab = ref('result');
const localCode = ref(props.code || '');
const status = ref<'idle' | 'running' | 'success' | 'error'>('idle');
const result = ref<SandboxResult | null>(null);
const error = ref<any>(null);
const progress = ref(0);
const abortController = ref<AbortController | null>(null);
const viewMode = ref<'grid' | 'carousel'>('grid');
// const terminalRef = ref<InstanceType<typeof SandboxTerminal> | null>(null);

// Computed
const editorOptions = {
    minimap: { enabled: false },
    fontSize: 13,
    automaticLayout: true,
    scrollBeyondLastLine: false,
    theme: 'vs-light'
};

const VIEW_MODES = ['grid', 'carousel'] as const;

const statusColorClass = computed(() => {
    switch (status.value) {
        case 'running': return 'bg-blue-100 text-blue-600 animate-pulse';
        case 'success': return 'bg-green-100 text-green-600';
        case 'error': return 'bg-red-100 text-red-600';
        default: return 'bg-slate-100 text-slate-500';
    }
});


const images = computed(() => {
    return result.value?.files?.filter(f => f.name.match(/\.(png|jpg|jpeg|gif|webp)$/i)) || [];
});

const hasFiles = computed(() => result.value?.files && result.value.files.length > 0);

const renderedContent = computed(() => {
    if (!result.value?.content) return '';
    let content = result.value.content;

    // Handle <think> blocks
    // Replace <think>...</think> with a styled details block
    // We add newlines around the content to ensure markdown parsing inside if supported by the parser context,
    // though inside HTML blocks marked often skips parsing.
    // For now, we assume simple text or we parse it manually if needed.
    // Given the context, we'll try to preserve it as a block.
    const thinkingTitle = t('sandbox.output.thinking');
    content = content.replace(
        /<think>([\s\S]*?)<\/think>/g, 
        `<details class="think-details mb-4 bg-slate-50 border border-indigo-100 rounded-lg overflow-hidden group"><summary class="px-4 py-2 bg-indigo-50/50 cursor-pointer font-medium text-indigo-600 text-sm select-none hover:bg-indigo-50 transition-colors flex items-center gap-2 list-none marker:hidden [&::-webkit-details-marker]:hidden"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-brain w-4 h-4"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>${thinkingTitle} <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-auto transform transition-transform group-open:rotate-180 text-indigo-400"><path d="m6 9 6 6 6-6"/></svg></summary><div class="p-4 text-slate-600 text-sm font-mono whitespace-pre-wrap leading-relaxed bg-slate-50/30 border-t border-indigo-100/50">$1</div></details>`
    );

    try {
        return marked.parse(content);
    } catch (e) {
        return content;
    }
});

// Methods
const run = async () => {
    status.value = 'running';
    error.value = null;
    result.value = null;
    // activeTab.value = 'result'; // activeTab removed
    progress.value = 0;
    
    // Clear terminal (if we had one, but we removed it from this view)
    // nextTick(() => { ... });

    // Simulate progress
    const progressInterval = setInterval(() => {
        if (progress.value < 90) progress.value += 10;
    }, 500);

    abortController.value = new AbortController();

    try {
        const response = await SandboxService.runCode({
            language: props.language || 'python',
            code: localCode.value,
            template: props.template,
            params: props.params
        }, {
            signal: abortController.value.signal
        });

        if (response.status === 'success') {
            status.value = 'success';
            result.value = response.result;
            
            // Write output to terminal
            // if (response.result?.content) {
            //     ...
            // }
            
            // If images generated, notify user
            // if (images.value.length > 0) {
            //      ...
            // }
            
            emit('complete', response.result);
        } else {
            throw new Error(response.result?.content || 'Execution failed');
        }
    } catch (e: any) {
        if (e.name === 'CanceledError') {
            status.value = 'idle'; 
        } else {
            status.value = 'error';
            error.value = e;
            // terminalRef.value?.writeln(`\r\n\x1b[31m✖ Error: ${e.message || e}\x1b[0m`);
            emit('error', e);
        }
    } finally {
        clearInterval(progressInterval);
        progress.value = 100;
        abortController.value = null;
    }
};

const cancel = () => {
    if (abortController.value) {
        abortController.value.abort();
        abortController.value = null;
        ElMessage.info(t('sandbox.status.cancelled'));
    }
};

const copyText = async (text: string) => {
    try {
        await navigator.clipboard.writeText(text);
        ElMessage.success(t('sandbox.status.copied'));
    } catch (e) {
        ElMessage.error(t('sandbox.status.copyFailed'));
    }
};

const handleExport = async (e: any) => {
    const key = e.key;
    if (!result.value) return;

    if (key === 'markdown') {
        const blob = new Blob([result.value.content], { type: 'text/markdown;charset=utf-8' });
        saveAs(blob, `result-${Date.now()}.md`);
    } else if (key === 'json') {
        const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json;charset=utf-8' });
        saveAs(blob, `result-${Date.now()}.json`);
    } else if (key === 'files' && hasFiles.value) {
        const zip = new JSZip();
        result.value.files.forEach(file => {
             // Assuming base64 content for files
             zip.file(file.name, file.content, { base64: true });
        });
        const content = await zip.generateAsync({ type: "blob" });
        saveAs(content, `artifacts-${Date.now()}.zip`);
    }
};

// Lifecycle
watch(() => props.code, (val) => {
    if (val !== localCode.value) localCode.value = val || '';
});

watch(localCode, (val) => {
    emit('update:code', val);
});

onBeforeUnmount(() => {
    if (abortController.value) {
        abortController.value.abort();
    }
});

if (props.autoRun) {
    run();
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

.custom-tabs :deep(.ant-tabs-nav) { margin-bottom: 0; padding: 0 16px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.custom-tabs :deep(.ant-tabs-content) { flex: 1; height: 100%; }

/* Markdown Styles */
.markdown-body :deep(h1) { font-size: 1.5em; font-weight: 600; margin-bottom: 1em; }
.markdown-body :deep(h2) { font-size: 1.25em; font-weight: 600; margin-bottom: 0.8em; }
.markdown-body :deep(pre) { background: #1e293b; color: #e2e8f0; padding: 1em; border-radius: 0.5em; overflow-x: auto; }
.markdown-body :deep(code) { background: #f1f5f9; padding: 0.2em 0.4em; border-radius: 0.25em; font-family: monospace; font-size: 0.9em; }
.markdown-body :deep(pre code) { background: transparent; padding: 0; color: inherit; }
.markdown-body :deep(ul) { list-style-type: disc; padding-left: 1.5em; margin-bottom: 1em; }
.markdown-body :deep(ol) { list-style-type: decimal; padding-left: 1.5em; margin-bottom: 1em; }

/* Think Block Styles */
.markdown-body :deep(details > summary) { list-style: none; }
.markdown-body :deep(details > summary::-webkit-details-marker) { display: none; }
</style>
