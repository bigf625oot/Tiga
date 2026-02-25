<template>
  <div class="h-full flex flex-col bg-figma-bg animate-[fadeIn_0.3s_ease-out] overflow-hidden">
    <!-- Header -->
    <header class="h-16 bg-white border-b border-figma-border flex items-center justify-between px-6 shrink-0 z-20 shadow-sm">
        <div class="flex items-center gap-4">
            <button @click="$emit('back')" class="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500 transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            </button>
            <div class="flex flex-col">
                <h1 class="text-lg font-bold text-figma-heading leading-tight truncate max-w-md">{{ recording.filename }}</h1>
                <div class="flex items-center gap-2 text-xs text-figma-text-secondary">
                    <span>{{ formatDate(recording.created_at) }}</span>
                    <span class="w-1 h-1 rounded-full bg-slate-300"></span>
                    <span class="font-din">{{ formatDuration(recording.duration) }}</span>
                    <span class="w-1 h-1 rounded-full bg-slate-300"></span>
                    <span :class="getStatusColor(recording.asr_status)">{{ getStatusText(recording.asr_status) }}</span>
                </div>
            </div>
        </div>
        
        <div class="flex items-center gap-3">
             <button class="px-4 py-2 rounded-lg bg-brand-primary text-white text-sm font-medium shadow-sm hover:bg-brand-gradient-end transition-all flex items-center gap-2" @click="handleShare">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
                分享
            </button>
            <a-dropdown placement="bottomRight">
                <button class="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500 transition-colors">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>
                </button>
                <template #overlay>
                    <a-menu>
                        <a-menu-item key="export">导出文档</a-menu-item>
                        <a-menu-item key="download">下载音频</a-menu-item>
                        <a-menu-divider />
                        <a-menu-item key="delete" class="text-red-500">删除录音</a-menu-item>
                    </a-menu>
                </template>
            </a-dropdown>
        </div>
    </header>

    <!-- Split View Body -->
    <div class="flex-1 flex overflow-hidden">
        <!-- Left: Waveform & Player -->
        <div class="w-2/5 flex flex-col border-r border-figma-border bg-white z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
            <WaveformPlayer 
                :src="recording.play_url" 
                @timeupdate="onTimeUpdate"
            />
        </div>

        <!-- Right: Transcript & Summary -->
        <div class="w-3/5 flex flex-col bg-figma-bg overflow-hidden relative">
            <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
                 <a-tabs v-model:activeKey="activeKey" class="h-full custom-tabs" :animated="false">
                    <template #rightExtra>
                        <button v-if="activeKey === 'transcript'" class="text-xs text-brand-primary hover:text-brand-gradient-end flex items-center gap-1 px-2 py-1 rounded hover:bg-brand-primary/5 transition-colors">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            编辑模式
                        </button>
                    </template>

                    <a-tab-pane key="transcript" tab="全文转写">
                        <div v-if="isAsrLoading" class="space-y-4 animate-pulse">
                            <div class="h-4 bg-slate-200 rounded w-3/4"></div>
                            <div class="h-4 bg-slate-200 rounded w-full"></div>
                            <div class="h-4 bg-slate-200 rounded w-5/6"></div>
                        </div>
                        <div v-else class="prose max-w-none">
                            <div 
                                class="text-base text-figma-heading leading-loose whitespace-pre-wrap outline-none focus:ring-2 focus:ring-brand-primary/20 rounded p-2 -ml-2 transition-shadow"
                                contenteditable="true"
                                @blur="updateTranscript"
                            >
                                {{ recording.transcription_text || '暂无转写内容' }}
                            </div>
                        </div>
                    </a-tab-pane>

                    <a-tab-pane key="summary" tab="智能摘要">
                        <div v-if="isSummaryLoading" class="space-y-4 animate-pulse">
                            <div class="h-32 bg-slate-100 rounded-xl"></div>
                        </div>
                        <div v-else class="bg-white rounded-xl p-6 shadow-sm border border-figma-border">
                             <div class="flex items-center gap-2 mb-4 text-brand-primary font-bold">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                                会议纪要
                            </div>
                            <div class="text-slate-700 leading-relaxed whitespace-pre-line markdown-body">
                                {{ recording.summary_text || '暂无摘要' }}
                            </div>
                        </div>
                    </a-tab-pane>
                    
                    <a-tab-pane key="recommendation" tab="内容推荐">
                         <div v-if="isRecommendationLoading" class="space-y-4 animate-pulse">
                            <div class="h-24 bg-slate-100 rounded-xl"></div>
                        </div>
                        <div v-else class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                             <h3 class="font-bold text-blue-900 mb-3 flex items-center gap-2">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                                智能推荐
                            </h3>
                            <div class="text-blue-800 leading-relaxed whitespace-pre-line text-sm">
                                {{ recording.recommendation_text || '暂无推荐内容' }}
                            </div>
                        </div>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </div>
    </div>

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
import WaveformPlayer from './WaveformPlayer.vue';

const props = defineProps({
    recording: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['back']);

// Use the same base URL as App.vue
const api = axios.create({
    baseURL: '/api/v1' 
});

const activeKey = ref('transcript');
const shareModalVisible = ref(false);
const sharePermission = ref('comment');
const allowComments = ref(true);
const shareLink = ref('https://tiga.app/share/' + props.recording.id); // Mock link

const isAsrLoading = computed(() => ['processing', 'pending'].includes(props.recording.asr_status));
const isSummaryLoading = computed(() => ['processing', 'pending'].includes(props.recording.summary_status));
const isRecommendationLoading = computed(() => ['processing', 'pending'].includes(props.recording.recommendation_status));

const onTimeUpdate = (time) => {
    // Sync logic: Highlight text based on time?
    // Current backend doesn't provide word-level timestamps, so we just play.
};

const updateTranscript = async (e) => {
    const newText = e.target.innerText;
    if (newText === props.recording.transcription_text) return;
    
    // Save logic would go here
    // await api.put(...)
    message.success("已保存修改");
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
</script>

<style scoped>
.custom-tabs :deep(.ant-tabs-nav) {
    margin-bottom: 0;
    border-bottom: 1px solid #E5E7EB;
}
.custom-tabs :deep(.ant-tabs-tab) {
    padding: 12px 16px;
    font-size: 14px;
    margin: 0;
}
.custom-tabs :deep(.ant-tabs-tab-active) {
    font-weight: 600;
}
</style>
