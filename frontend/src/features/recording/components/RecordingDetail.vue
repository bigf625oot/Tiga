<template>
  <div class="h-full flex flex-col bg-figma-bg animate-[fadeIn_0.3s_ease-out] overflow-hidden font-sans text-slate-900">
    <!-- 1. Header Container -->
    <header class="h-16 bg-white border-b border-figma-border flex items-center justify-between px-6 shrink-0 z-20 shadow-sm">
        <div class="flex items-center gap-4 min-w-0">
            <button @click="$emit('back')" class="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500 transition-colors" aria-label="返回">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            </button>
            <div class="flex flex-col min-w-0">
                <h1 class="text-lg font-bold text-figma-heading leading-tight truncate max-w-md" :title="recording.filename">{{ recording.filename }}</h1>
                <div class="flex items-center gap-2 text-xs text-figma-text-secondary mt-0.5">
                    <span>{{ formatDate(recording.created_at) }}</span>
                    <span class="w-0.5 h-0.5 rounded-full bg-slate-300"></span>
                    <span class="font-din">{{ formatDuration(recording.duration) }}</span>
                    <span class="w-0.5 h-0.5 rounded-full bg-slate-300"></span>
                    <span :class="getStatusColor(recording.asr_status)" class="font-medium">{{ getStatusText(recording.asr_status) }}</span>
                </div>
            </div>
        </div>
        
        <div class="flex items-center gap-2">
             <button class="px-3 py-1.5 rounded-lg bg-brand-primary text-white text-sm font-medium shadow-sm hover:bg-brand-gradient-end transition-all flex items-center gap-2" @click="handleShare">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
                分享
            </button>
            
            <div class="h-6 w-px bg-slate-200 mx-1"></div>

            <a-tooltip title="导出文档">
                <button class="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500 transition-colors">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
                </button>
            </a-tooltip>
            
            <a-tooltip title="下载音频">
                <button class="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500 transition-colors">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                </button>
            </a-tooltip>
            
            <a-tooltip title="删除录音">
                <button class="w-9 h-9 rounded-lg hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </a-tooltip>
        </div>
    </header>

    <!-- 2. Main Content Container -->
    <main class="flex-1 flex flex-col min-h-0 relative bg-white">
        <!-- Player Section (Moved to top) -->
        <div class="border-b border-slate-100 bg-slate-50/50">
            <WaveformPlayer 
                :src="recording.play_url" 
                :seekTime="seekTime"
                @timeupdate="onTimeUpdate"
            />
        </div>

        <div class="flex-1 flex flex-col min-h-0 p-6">
             <a-tabs v-model:activeKey="activeKey" class="custom-tabs flex-1 flex flex-col min-h-0" :animated="false" :tabBarStyle="{ borderBottom: 'none' }">
                <template #rightExtra>
                    <div class="flex items-center gap-4">
                        <!-- Font Size Controls -->
                        <div class="flex items-center bg-slate-100 rounded-lg p-0.5">
                            <button @click="adjustFontSize(-2)" class="px-2 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-white rounded transition-colors" title="减小字号">A-</button>
                            <span class="text-[10px] text-slate-400 px-1 select-none">{{ fontSize }}</span>
                            <button @click="adjustFontSize(2)" class="px-2 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-white rounded transition-colors" title="增大字号">A+</button>
                        </div>

                        <div v-if="activeKey === 'transcript'" class="flex items-center gap-2 border-l border-slate-200 pl-4">
                            <template v-if="isEditing">
                                <button @click="isEditing = false" class="text-xs text-slate-500 hover:text-slate-700 px-3 py-1 rounded transition-colors">
                                    取消
                                </button>
                                <button @click="saveTranscript" class="text-xs bg-brand-primary text-white hover:bg-brand-gradient-end px-3 py-1 rounded shadow-sm transition-all font-medium">
                                    保存
                                </button>
                            </template>
                            <button v-else @click="toggleEditMode" class="text-xs text-brand-primary hover:text-brand-gradient-end flex items-center gap-1 px-2 py-1 rounded hover:bg-brand-primary/5 transition-colors">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                                编辑模式
                            </button>
                        </div>
                    </div>
                </template>

                <a-tab-pane key="transcript" tab="全文转写" class="h-full overflow-y-auto custom-scrollbar">
                    <div v-if="isAsrLoading" class="space-y-4 animate-pulse max-w-none w-full py-8 px-4">
                        <div class="h-4 bg-slate-200 rounded w-3/4"></div>
                        <div class="h-4 bg-slate-200 rounded w-full"></div>
                        <div class="h-4 bg-slate-200 rounded w-5/6"></div>
                        <div class="h-4 bg-slate-200 rounded w-4/5"></div>
                    </div>
                    <div v-else class="h-full flex flex-col max-w-none w-full py-4 px-4">
                            <textarea 
                                v-if="isEditing"
                                v-model="editContent"
                                class="w-full h-full p-0 border-0 outline-none bg-transparent resize-none leading-relaxed font-sans"
                                :style="{ fontSize: fontSize + 'px' }"
                                placeholder="输入转写内容..."
                            ></textarea>
                            <div 
                                v-else
                                class="prose max-w-none text-slate-700 leading-loose whitespace-pre-wrap font-sans text-left"
                                :style="{ fontSize: fontSize + 'px' }"
                            >
                                <template v-if="transcriptionData && transcriptionData.length > 0">
                                    <span 
                                        v-for="(sentence, index) in transcriptionData" 
                                        :key="index"
                                        class="cursor-pointer hover:bg-brand-primary/10 transition-colors rounded px-0.5 py-0.5"
                                        :class="{ 'bg-brand-primary/20 text-brand-primary font-medium': isCurrentSentence(sentence) }"
                                        @click="handleSentenceClick(sentence)"
                                        :title="formatTime(sentence.BeginTime/1000)"
                                    >{{ sentence.Text }}</span>
                                </template>
                                <template v-else>
                                    {{ recording.transcription_text || '暂无转写内容' }}
                                </template>
                            </div>
                        </div>
                </a-tab-pane>

                <a-tab-pane key="summary" tab="智能摘要" class="h-full overflow-y-auto custom-scrollbar">
                    <div v-if="isSummaryLoading" class="space-y-4 animate-pulse max-w-none w-full py-8 px-4">
                        <div class="h-32 bg-slate-100 rounded-xl"></div>
                    </div>
                    <div v-else class="max-w-none w-full mt-4 px-4">
                        
                        <div class="markdown-body text-slate-700 leading-relaxed text-left" 
                             :style="{ fontSize: fontSize + 'px' }"
                             v-html="renderMarkdown(recording.summary_text)"></div>
                    </div>
                </a-tab-pane>
                
                <a-tab-pane key="recommendation" tab="内容推荐" class="h-full overflow-y-auto custom-scrollbar">
                     <div v-if="isRecommendationLoading" class="max-w-none w-full mt-4 px-4">
                        <div class="h-4 w-32 bg-slate-100 rounded mb-4 animate-pulse"></div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                            <div v-for="i in 8" :key="i" class="flex items-center gap-2 p-1.5 border border-slate-100 rounded-md animate-pulse">
                                <div class="w-6 h-6 rounded bg-slate-100 shrink-0"></div>
                                <div class="flex-1 min-w-0 space-y-1">
                                    <div class="h-3 bg-slate-100 rounded w-3/4"></div>
                                    <div class="h-2 bg-slate-100 rounded w-1/4"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-else class="max-w-none w-full mt-4 px-4">
                        
                        <!-- Recommendation Content -->
                        <div class="space-y-6">
                            <!-- 2. Related Documents Cards -->
                            <div v-if="relatedDocs.length > 0">
                                <h4 class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide scale-90 origin-left">相关知识库文档</h4>
                                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                                    <div 
                                        v-for="(doc, idx) in relatedDocs" 
                                        :key="idx"
                                        class="group flex items-center gap-2 p-1.5 bg-white border border-slate-200 rounded-md hover:border-brand-primary/50 hover:shadow-sm transition-all cursor-pointer relative overflow-hidden"
                                        @click="handleDocClick(doc)"
                                    >
                                        <!-- File Icon -->
                                        <div class="w-6 h-6 rounded bg-blue-50 flex items-center justify-center shrink-0 text-brand-primary">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                                <polyline points="14 2 14 8 20 8"></polyline>
                                            </svg>
                                        </div>
                                        
                                        <div class="flex-1 min-w-0 flex items-center gap-2">
                                            <h5 class="text-[11px] font-medium text-slate-900 truncate group-hover:text-brand-primary transition-colors flex-1" :title="doc.title">{{ doc.title }}</h5>
                                            <div class="flex items-center gap-1 shrink-0">
                                                <span class="px-1 py-[1px] rounded-[2px] bg-slate-100 text-[9px] text-slate-500 font-medium leading-none scale-90">{{ doc.type || 'DOC' }}</span>
                                            </div>
                                        </div>
                                        
                                        <!-- Arrow Icon (Subtle) -->
                                        <div class="opacity-0 group-hover:opacity-100 transition-opacity -ml-1">
                                            <svg class="text-brand-primary" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="flex flex-col items-center justify-center py-20 text-slate-400">
                                <div class="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="text-slate-300">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                        <polyline points="14 2 14 8 20 8"></polyline>
                                        <line x1="16" y1="13" x2="8" y2="13"></line>
                                        <line x1="16" y1="17" x2="8" y2="17"></line>
                                        <polyline points="10 9 9 9 8 9"></polyline>
                                    </svg>
                                </div>
                                <p class="text-sm">暂无相关推荐内容</p>
                                <p class="text-xs text-slate-300 mt-1">系统未找到与此录音相关的知识库文档</p>
                            </div>
                        </div>
                    </div>
                </a-tab-pane>
            </a-tabs>
        </div>
    </main>

    <!-- Share Modal -->
    <a-modal v-model:open="shareModalVisible" title="分享录音" @ok="handleShareConfirm" ok-text="复制链接" centered>
        <div class="py-4 space-y-4">
            <div>
                <label class="text-sm font-medium text-slate-700 mb-1 block">链接权限</label>
                <a-select v-model:value="sharePermission" class="w-full">
                    <a-select-option value="view">仅查看</a-select-option>
                    <a-select-option value="comment">允许评论</a-select-option>
                    <a-select-option value="edit">允许编辑</a-select-option>
                </a-select>
            </div>
            <div class="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span class="text-sm text-slate-500 truncate mr-2">{{ shareLink }}</span>
                <button class="text-brand-primary text-sm font-medium hover:underline">复制</button>
            </div>
            <div class="flex items-center gap-2">
                 <a-switch v-model:checked="allowComments" size="small" />
                 <span class="text-sm text-slate-600">允许评论</span>
            </div>
        </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';
import { marked } from 'marked';
import WaveformPlayer from './WaveformPlayer.vue';

const props = defineProps({
    recording: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['back']);

const api = axios.create({
    baseURL: '/api/v1' 
});

const activeKey = ref('transcript');
const isEditing = ref(false);
const editContent = ref('');
const shareModalVisible = ref(false);
const sharePermission = ref('comment');
const allowComments = ref(true);
const shareLink = ref('https://tiga.app/share/' + props.recording.id);
const fontSize = ref(14);
const currentTime = ref(0);
const seekTime = ref(undefined);

const isAsrLoading = computed(() => ['processing', 'pending'].includes(props.recording.asr_status));
const isSummaryLoading = computed(() => ['processing', 'pending'].includes(props.recording.summary_status));
const isRecommendationLoading = computed(() => ['processing', 'pending'].includes(props.recording.recommendation_status));

const relatedDocs = computed(() => {
    try {
        const text = props.recording.recommendation_text;
        if (!text) return [];
        
        // Check if it's JSON
        if (text.trim().startsWith('[')) {
            const parsed = JSON.parse(text);
            return parsed.map(item => ({
                ...item,
                type: getFileType(item.title || item.file_path),
                title: item.title || '无标题文档'
            }));
        }
        return [];
    } catch (e) {
        console.error("Failed to parse recommendation_text", e);
        return [];
    }
});

const getFileType = (filename) => {
    if (!filename) return 'DOC';
    const ext = filename.split('.').pop().toLowerCase();
    if (['pdf'].includes(ext)) return 'PDF';
    if (['doc', 'docx'].includes(ext)) return 'DOC';
    if (['ppt', 'pptx'].includes(ext)) return 'PPT';
    if (['xls', 'xlsx', 'csv'].includes(ext)) return 'XLS';
    if (['md', 'txt'].includes(ext)) return 'TXT';
    return 'FILE';
};

const handleDocClick = (doc) => {
    message.info(`打开文档: ${doc.title}`);
    // 实际逻辑可以是跳转到文档详情页或下载
};

const toggleEditMode = () => {
    if (isEditing.value) {
        isEditing.value = false;
        editContent.value = '';
    } else {
        editContent.value = props.recording.transcription_text || '';
        isEditing.value = true;
    }
};

const saveTranscript = async () => {
    try {
        const oldText = props.recording.transcription_text;
        props.recording.transcription_text = editContent.value;
        isEditing.value = false;
        
        await api.patch(`/recordings/${props.recording.id}`, {
            transcription_text: editContent.value
        });
        message.success("已保存修改");
    } catch (e) {
        console.error(e);
        message.error("保存失败");
    }
};

const renderMarkdown = (text) => {
    try {
        return marked.parse(text || '');
    } catch (e) {
        return text;
    }
};

const onTimeUpdate = (time) => {
    currentTime.value = time;
};

const handleShare = () => {
    shareModalVisible.value = true;
};

const handleShareConfirm = () => {
    navigator.clipboard.writeText(shareLink.value);
    message.success("链接已复制");
    shareModalVisible.value = false;
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm');
};

const formatDuration = (ms) => {
    const durationSec = Math.floor(ms / 1000);
    const min = Math.floor(durationSec / 60);
    const sec = durationSec % 60;
    return (min > 0 ? min + ":" : "0:") + (sec < 10 ? "0" + sec : sec);
};

const getStatusColor = (status) => {
    switch(status) {
        case 'completed': return 'text-green-500';
        case 'processing': return 'text-blue-500';
        case 'failed': return 'text-red-500';
        default: return 'text-slate-400';
    }
};

const getStatusText = (status) => {
    switch(status) {
        case 'completed': return '已完成';
        case 'processing': return '转写中';
        case 'failed': return '失败';
        default: return '待处理';
    }
};

const adjustFontSize = (delta) => {
    const newSize = fontSize.value + delta;
    if (newSize >= 12 && newSize <= 24) {
        fontSize.value = newSize;
    }
};
</script>

<style scoped>
.custom-tabs {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.custom-tabs :deep(.ant-tabs-nav) {
    margin-bottom: 0;
    flex-shrink: 0;
}
.custom-tabs :deep(.ant-tabs-nav)::before {
    display: none;
}
.custom-tabs :deep(.ant-tabs-content) {
    flex: 1;
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
}
.custom-tabs :deep(.ant-tabs-tabpane) {
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}
.custom-tabs :deep(.ant-tabs-tab) {
    padding: 12px 20px;
    font-size: 14px;
    margin: 0;
}
.custom-tabs :deep(.ant-tabs-tab-active) {
    font-weight: 600;
}

/* Markdown Styles */
.markdown-body {
    color: #334155; /* slate-700 */
    line-height: 1.8;
}
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) {
    font-weight: 600;
    margin-bottom: 0.5em;
    margin-top: 1em;
    color: #1e293b;
}
.markdown-body :deep(ul), .markdown-body :deep(ol) {
    padding-left: 1.5em;
    margin-bottom: 1em;
}
.markdown-body :deep(li) {
    margin-bottom: 0.25em;
}
.markdown-body :deep(p) {
    margin-bottom: 1em;
}
</style>