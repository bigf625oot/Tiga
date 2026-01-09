<template>
  <div class="max-w-[1200px] mx-auto p-4 flex flex-col lg:flex-row gap-6 h-[calc(100vh-140px)]">
    <!-- Left Panel: Configuration -->
    <div class="w-full lg:w-1/3 flex flex-col gap-5 overflow-y-auto pr-2 pb-10">
        
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <span class="w-1 h-5 bg-blue-600 rounded-full"></span>
                指标定义
            </h3>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">指标名称</label>
                    <input v-model="form.indicator_name" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none" placeholder="例如：营业收入">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">指标别名 (可选)</label>
                    <input v-model="form.aliases" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none" placeholder="例如：营收, 销售额">
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">指标定义</label>
                    <textarea v-model="form.definition" rows="4" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none resize-none" placeholder="详细描述该指标的定义、计算方式或口径..."></textarea>
                </div>
            </div>
        </div>

        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <span class="w-1 h-5 bg-green-600 rounded-full"></span>
                数据来源
            </h3>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">选择录音文件</label>
                    <select v-model="selectedFileId" @change="handleFileChange" class="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none bg-white">
                        <option :value="null">-- 请选择已转写的文件 --</option>
                        <option v-for="file in files" :key="file.id" :value="file.id">
                            {{ file.filename }} ({{ file.duration }}s)
                        </option>
                    </select>
                </div>
                
                <div v-if="loadingFiles" class="text-xs text-slate-400">加载文件列表中...</div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">文本内容预览</label>
                    <textarea v-model="form.text_content" rows="6" readonly class="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-500 text-xs resize-none font-mono" placeholder="选择文件后自动加载文本..."></textarea>
                </div>
            </div>
        </div>
        
        <button 
            @click="handleExtract" 
            :disabled="extracting || !form.text_content || !form.indicator_name"
            class="bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-bold shadow-lg shadow-blue-600/20 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
            <svg v-if="extracting" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span>{{ extracting ? 'AI 提取中...' : '开始智能提取' }}</span>
        </button>

    </div>

    <!-- Right Panel: Results -->
    <div class="w-full lg:w-2/3 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        <div class="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h3 class="font-bold text-slate-700">提取结果</h3>
            <div class="flex gap-2">
                <span class="text-xs px-2 py-1 bg-slate-200 rounded text-slate-600">Model: Qwen-Plus</span>
                <span class="text-xs px-2 py-1 bg-slate-200 rounded text-slate-600">Format: JSON</span>
            </div>
        </div>
        
        <div class="flex-1 p-6 overflow-y-auto font-mono text-sm relative">
            <div v-if="!result && !extracting" class="absolute inset-0 flex flex-col items-center justify-center text-slate-300">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <span class="mt-4 text-sm">暂无提取结果</span>
            </div>
            
            <div v-if="extracting" class="absolute inset-0 flex flex-col items-center justify-center bg-white/80 z-10">
                <div class="w-16 h-16 border-4 border-blue-100 border-t-blue-500 rounded-full animate-spin mb-4"></div>
                <p class="text-blue-600 font-medium animate-pulse">正在进行思维链推理 (CoT)...</p>
            </div>

            <div v-if="result">
                <pre class="whitespace-pre-wrap text-slate-700 bg-slate-50 p-4 rounded-lg border border-slate-100">{{ result }}</pre>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1' 
});

const files = ref([]);
const loadingFiles = ref(false);
const selectedFileId = ref(null);
const extracting = ref(false);
const result = ref('');

const form = reactive({
    indicator_name: '',
    aliases: '',
    definition: '',
    text_content: '',
    output_format: 'JSON',
    language: 'CN',
    extraction_mode: 'Multi'
});

onMounted(async () => {
    loadingFiles.value = true;
    try {
        const res = await api.get('/recordings/');
        // Filter only files with successful transcription
        files.value = res.data.filter(f => !f.is_folder && f.asr_status === 'completed');
    } catch (e) {
        console.error(e);
    } finally {
        loadingFiles.value = false;
    }
});

const handleFileChange = async () => {
    if (!selectedFileId.value) {
        form.text_content = '';
        return;
    }
    
    // Find file content locally if available, or fetch detail
    // The list API usually doesn't return full text. We might need to fetch detail.
    try {
        const res = await api.get(`/recordings/${selectedFileId.value}`);
        form.text_content = res.data.transcription_text || "无转写内容";
    } catch (e) {
        message.error("获取文件内容失败");
    }
};

const handleExtract = async () => {
    extracting.value = true;
    result.value = '';
    
    try {
        const res = await api.post('/metrics/extract', {
            indicator_name: form.indicator_name,
            definition: form.definition,
            text_content: form.text_content,
            aliases: form.aliases,
            output_format: form.output_format,
            language: form.language,
            extraction_mode: form.extraction_mode
        });
        
        if (res.data.status === 'success') {
            result.value = res.data.content;
            message.success("提取完成");
        } else {
            result.value = res.data.content; // Show error message
            message.error("提取遇到问题");
        }
    } catch (e) {
        message.error("请求失败");
        console.error(e);
    } finally {
        extracting.value = false;
    }
};
</script>
