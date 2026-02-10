<template>
  <div class="max-w-[800px] mx-auto animate-[fadeIn_0.3s_ease-out]">
    <button @click="$emit('back')" class="mb-6 flex items-center text-slate-500 hover:text-slate-800 transition-colors">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        返回列表
    </button>

    <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 mb-6">
        <h1 class="text-2xl font-bold text-slate-900 mb-4">{{ recording.filename }}</h1>
        <div class="text-sm text-slate-400 mb-6 flex gap-4 font-din">
            <span>{{ formatDate(recording.created_at) }}</span>
            <span>{{ formatDuration(recording.duration) }}</span>
        </div>

        <!-- Audio Player -->
        <div class="bg-slate-50 rounded-xl p-4 mb-8">
            <audio controls class="w-full" :src="recording.play_url"></audio>
        </div>

        <!-- Content Tabs -->
        <a-tabs v-model:activeKey="activeKey">
            <template #rightExtra>
                <a-button type="link" danger v-if="recording.asr_status === 'failed' || recording.transcription_text === '转写失败'" @click="retryTranscription">手动转写</a-button>
            </template>
            <a-tab-pane key="transcript" tab="全文转写">
                <a-skeleton :active="true" :loading="isAsrLoading" :paragraph="{ rows: 10 }">
                    <div class="text-slate-600 leading-loose whitespace-pre-wrap p-2">
                        {{ recording.transcription_text }}
                    </div>
                </a-skeleton>
            </a-tab-pane>
            <a-tab-pane key="summary" tab="智能摘要">
                <a-skeleton :active="true" :loading="isSummaryLoading" :paragraph="{ rows: 6 }">
                    <div class="bg-purple-50/50 rounded-xl p-6 text-slate-700 leading-relaxed whitespace-pre-line border border-purple-100">
                        {{ recording.summary_text }}
                    </div>
                </a-skeleton>
            </a-tab-pane>
            <a-tab-pane key="recommendation" tab="内容推荐">
                <a-skeleton :active="true" :loading="isRecommendationLoading" :paragraph="{ rows: 6 }">
                    <div class="bg-blue-50/50 rounded-xl p-6 text-slate-700 leading-relaxed whitespace-pre-line border border-blue-100">
                        {{ recording.recommendation_text }}
                    </div>
                </a-skeleton>
            </a-tab-pane>
        </a-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';

const props = defineProps({
    recording: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['back']);

// Use the same base URL as App.vue (ideally should be in a shared config)
const api = axios.create({
    baseURL: '/api/v1' 
});

const activeKey = ref('transcript');

const isAsrLoading = computed(() => {
    return props.recording.asr_status === 'processing' || props.recording.asr_status === 'pending';
});

const isSummaryLoading = computed(() => {
    return props.recording.summary_status === 'processing' || props.recording.summary_status === 'pending';
});

const isRecommendationLoading = computed(() => {
    return props.recording.recommendation_status === 'processing' || props.recording.recommendation_status === 'pending';
});

const retryTranscription = async () => {
    try {
        message.loading({ content: '提交重试请求...', key: 'retry' });
        await api.post(`/recordings/${props.recording.id}/retry`);
        message.success({ content: '已提交重试', key: 'retry' });
        
        // Optimistic update
        props.recording.asr_status = 'processing';
        props.recording.transcription_text = '重试处理中...';
        props.recording.summary_text = '重试处理中...';
        props.recording.recommendation_text = '重试处理中...';
        
    } catch (e) {
        message.error({ content: '重试请求失败', key: 'retry' });
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

const formatDuration = (ms) => {
    // Backend stores duration in ms or s? 
    // In endpoints I saw `duration` passed from frontend. 
    // If frontend passed ms, then it is ms.
    // Let's assume ms for consistency with frontend logic.
    const durationSec = Math.floor(ms / 1000);
    const min = Math.floor(durationSec / 60);
    const sec = durationSec % 60;
    return (min > 0 ? min + "分" : "") + sec + "秒";
};
</script>