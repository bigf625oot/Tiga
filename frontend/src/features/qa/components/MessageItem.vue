<template>
  <div 
    class="flex w-full mb-1 group message-item" 
    :class="[
      isUser ? 'flex-row-reverse' : 'flex-row',
      !showAvatar ? (isUser ? 'mr-10' : 'ml-10') : ''
    ]"
  >
    <!-- Avatar -->
    <div 
      v-if="showAvatar" 
      class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden mt-1 transition-all duration-300 hover:scale-105"
      :class="[isUser ? 'bg-indigo-600 ml-2' : 'bg-slate-100 mr-2']"
    >
      <img v-if="isUser" src="https://api.dicebear.com/7.x/notionists/svg?seed=Admin" alt="user" class="w-full h-full object-cover" @error="handleImgError" />
      <img v-else-if="agentIcon" :src="agentIcon" alt="agent" class="w-full h-full object-cover" @error="handleImgError" />
      <img v-else src="/tiga.svg" alt="agent" class="w-full h-full object-cover" />
    </div>

    <!-- Message Content Wrapper -->
    <div 
      class="flex flex-col max-w-[85%]" 
      :class="[isUser ? 'items-end' : 'items-start']"
    >
      <!-- Sender Name & Time (Optional) -->
      <div v-if="showMeta" class="flex items-center gap-2 mb-1 text-xs text-slate-400 px-1">
        <span v-if="!isUser" class="font-medium text-slate-500">{{ agent?.name || 'Tiga' }}</span>
        <span>{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Bubble -->
      <div 
        class="relative px-4 py-3 text-sm leading-relaxed transition-all duration-200"
        :class="bubbleClasses"
      >
        <!-- Status Indicator (User only) -->
        <div v-if="isUser" class="absolute -left-5 bottom-1 text-slate-300 text-[10px]">
          <span v-if="message.status === 'sending'" class="animate-pulse">...</span>
          <span v-else-if="message.status === 'error'" class="text-red-400">!</span>
        </div>

        <!-- Content -->
        <div v-if="!isUser">
            <!-- Reasoning / Thinking Process -->
            <div v-if="message.reasoning" class="mb-3 p-3 bg-slate-50/50 border-l-2 border-indigo-200/50 rounded-r text-xs text-slate-500 font-mono whitespace-pre-wrap">
                <div class="flex items-center gap-1 mb-1 text-indigo-400/80 font-semibold uppercase tracking-wider text-[10px]">
                    <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                    <span>Thinking</span>
                </div>
                {{ message.reasoning }}
            </div>

            <!-- AMIS or Markdown -->
            <div v-if="isAmisJSON(message.content)" :id="'amis-' + uniqueId" class="amis-container my-2 rounded-lg overflow-hidden bg-white border border-slate-100"></div>
            <div v-else class="markdown-body" v-html="renderedContent"></div>

            <!-- References / Sources -->
            <SourcePanel 
              v-if="hasReferences || hasSources" 
              :sources="combinedSources" 
              @locate-node="handleLocateNode"
              @show-doc-summary="handleDocSummary"
            />
        </div>
        <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, nextTick, inject } from 'vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import BaseIcon from '@/shared/components/atoms/BaseIcon';
import SourcePanel from './SourcePanel.vue';
import dayjs from 'dayjs';

const props = defineProps({
  message: { type: Object, required: true },
  isUser: { type: Boolean, default: false },
  showAvatar: { type: Boolean, default: true },
  showMeta: { type: Boolean, default: false },
  agent: { type: Object, default: null },
  uniqueId: { type: String, default: () => Math.random().toString(36).substr(2, 9) }
});

const emit = defineEmits(['locate-node', 'show-doc-summary']);

const bubbleClasses = computed(() => {
  if (props.isUser) {
    return 'bg-indigo-600 text-white rounded-2xl rounded-tr-sm shadow-sm';
  } else {
    // Agent: No border, neutral background, distinct font weight
    return 'bg-slate-50 text-slate-700 rounded-2xl rounded-tl-sm font-normal';
  }
});

const hasReferences = computed(() => {
    return props.message.meta_data && (props.message.meta_data.structured_references || props.message.meta_data.references);
});

const hasSources = computed(() => {
    return props.message.sources && props.message.sources.length > 0;
});

const combinedSources = computed(() => {
    if (props.message.sources && props.message.sources.length > 0) {
        return props.message.sources;
    }
    const sr = props.message.meta_data?.structured_references || [];
    if (sr.length) return sr.map(r => ({
        docId: r.id,
        title: r.title,
        summary: r.summary,
        score: 1.0, // Default
        updateTime: r.createTime
    }));
    const refs = props.message.meta_data?.references || [];
    return refs.map((r, i) => ({
        docId: i + 1,
        title: r.title || 'Unknown Source',
        summary: r.preview || '',
        score: r.score || 1.0
    }));
});

const handleLocateNode = (item) => {
    emit('locate-node', item);
};

const handleDocSummary = (item) => {
    emit('show-doc-summary', item);
};


const agentIcon = computed(() => {
    return props.agent?.icon || props.agent?.icon_url;
});

const handleImgError = (e) => {
    if (e.target.alt === 'user') {
        e.target.src = '/tiga.svg'; 
    } else {
        e.target.src = '/tiga.svg';
    }
    e.target.onerror = null; // Prevent infinite loop
};

const formatTime = (ts) => {
    if (!ts) return '';
    return dayjs(ts).format('HH:mm');
};

const isAmisJSON = (text) => {
    if (!text || !text.trim().startsWith('```json')) return false;
    return text.includes('"type": "page"') || text.includes('"type": "chart"');
};

const renderMarkdown = (text) => {
    try {
        let inputText = (text || '').trim();
        // Simple markdown config
        marked.setOptions({
            breaks: true,
            gfm: true
        });
        
        // Katex support (simplified from SmartQA)
        let html = marked.parse(inputText);
        return html;
    } catch (e) {
        return text;
    }
};

const renderedContent = computed(() => {
    return renderMarkdown(props.message.content);
});

onMounted(() => {
    if (isAmisJSON(props.message.content) && window.amis) {
        const jsonMatch = props.message.content.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch && jsonMatch[1]) {
             try {
                const schema = JSON.parse(jsonMatch[1]);
                const container = document.getElementById('amis-' + props.uniqueId);
                if (container) window.amis.embed(container, schema);
             } catch (e) { console.error(e); }
        }
    }
});
</script>

<style scoped>
.markdown-body { font-size: 14px; line-height: 1.6; }
.markdown-body :deep(p) { margin-bottom: 0.5em; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(pre) { background: #e2e8f0; padding: 10px; border-radius: 6px; overflow-x: auto; margin: 8px 0; }
.markdown-body :deep(code) { font-family: monospace; background: rgba(0,0,0,0.05); padding: 2px 4px; border-radius: 4px; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.5em; margin-bottom: 0.5em; }
.markdown-body :deep(li) { margin-bottom: 0.25em; }
</style>