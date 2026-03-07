<template>
  <div 
    class="flex w-full mb-4 group chat-card" 
    :class="[
      isUser ? 'flex-row-reverse' : 'flex-row',
      !showAvatar ? (isUser ? 'mr-10' : 'ml-10') : ''
    ]"
  >
    <!-- Avatar -->
    <div 
      v-if="showAvatar" 
      class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden mt-1 transition-all duration-300 hover:scale-105"
      :class="[isUser ? 'bg-indigo-600 ml-2' : 'bg-muted mr-2']"
    >
      <img v-if="isUser" src="https://api.dicebear.com/7.x/notionists/svg?seed=Admin" alt="user" class="w-full h-full object-cover" />
      <img v-else-if="agent?.icon || agent?.icon_url" :src="agent?.icon || agent?.icon_url" alt="agent" class="w-full h-full object-cover" />
      <img v-else src="/tiga.svg" alt="agent" class="w-full h-full object-cover" />
    </div>

    <!-- Message Content Wrapper -->
    <div 
      class="flex flex-col max-w-[85%]" 
      :class="[isUser ? 'items-end' : 'items-start']"
    >
      <!-- Sender Name & Time -->
      <div v-if="showMeta" class="flex items-center gap-2 mb-1 text-xs text-muted-foreground px-1">
        <span v-if="!isUser" class="font-medium text-muted-foreground">{{ agent?.name || 'Tiga' }}</span>
        <span>{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Bubble -->
      <div 
        class="relative px-4 p-4 text-sm leading-relaxed transition-all duration-200 shadow-sm"
        :class="bubbleClasses"
      >
        <!-- User Mode: Simple Text -->
        <div v-if="isUser" class="whitespace-pre-wrap">{{ message.content }}</div>

        <!-- Agent Mode: Rich Content -->
        <div v-else class="agent-content flex flex-col gap-4">
            
            <!-- 1. Thinking Process (Collapsed by default) -->
            <div v-if="parsed.think" class="w-full">
                <details class="bg-indigo-50/30 rounded-lg border border-indigo-100/50 overflow-hidden group transition-all duration-300" :open="parsed.think.isPartial">
                    <summary class="p-4 py-2 text-xs font-medium text-indigo-500 cursor-pointer flex items-center gap-2 select-none outline-none hover:bg-indigo-50/50 transition-colors">
                        <div class="flex items-center gap-2 flex-1">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                            <span>思考过程</span>
                        </div>
                        <svg class="w-3 h-3 text-indigo-300 transform group-open:rotate-180 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </summary>
                    <div class="p-4 py-2 text-xs text-slate-600 border-t border-indigo-100/30 bg-white/50 leading-relaxed font-mono" v-html="parsed.think.html"></div>
                </details>
            </div>

            <!-- 2. Chart (Visual Priority) -->
            <div v-if="chartOption" class="w-full bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                 <div class="p-4 py-2 border-b border-slate-50 bg-muted/50/50 flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-700 flex items-center gap-2">
                        <svg class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                        </svg>
                        数据可视化
                    </span>
                 </div>
                 <div class="h-64 w-full relative bg-white">
                    <ChartFrame :option="chartOption" />
                 </div>
            </div>

            <!-- 3. Data Summary (Text + Table + SQL) -->
            <div v-if="parsed.text || parsed.html || parsed.sql" class="w-full bg-white rounded-lg border border-border shadow-sm p-4 group/summary">
                <!-- Title (Optional, only if chart exists to separate sections) -->
                <div v-if="chartOption" class="mb-2 pb-2 border-b border-slate-50 flex items-center gap-2">
                     <svg class="w-3.5 h-3.5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                     </svg>
                     <span class="text-xs font-semibold text-slate-600">数据详情</span>
                </div>

                <!-- Markdown Content (Table, Summary) -->
                <div v-if="parsed.html" class="markdown-body table-wrapper text-sm text-slate-600" v-html="parsed.html"></div>
                
                <!-- Embedded Resources -->
                <div v-if="parsed.resources.length > 0" class="m-4 flex flex-col gap-2">
                    <GenericResourceCard 
                        v-for="(res, idx) in parsed.resources" 
                        :key="idx"
                        :type="res.type"
                        :id="res.data.id"
                        :title="res.data.title || res.data.name || 'Unknown Resource'"
                        :meta="res.data.size"
                        @click="handleResourceClick"
                    />
                </div>

                <!-- SQL Section (Collapsed inside Summary) -->
                <div v-if="parsed.sql" class="m-4 pt-2 border-t border-slate-50">
                    <details class="group/sql">
                        <summary class="flex items-center gap-2 text-[10px] text-muted-foreground cursor-pointer hover:text-blue-500 transition-colors select-none w-fit">
                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                            </svg>
                            <span>查看查询 SQL</span>
                            <svg class="w-2.5 h-2.5 transform group-open/sql:rotate-180 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                        </summary>
                        <div class="mt-2 relative rounded bg-muted/50 border border-border">
                             <div class="absolute top-1 right-1">
                                <button @click.stop="copyText(parsed.sql)" class="p-1 text-muted-foreground hover:text-blue-500 transition-colors" title="复制 SQL">
                                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                </button>
                             </div>
                             <pre class="!m-0 !p-2 !bg-transparent overflow-x-auto custom-scrollbar"><code class="text-blue-500/80 font-mono text-[10px] leading-4 whitespace-pre">{{ parsed.sql }}</code></pre>
                        </div>
                    </details>
                </div>
            </div>
            
            <!-- 4. References (Footer) -->
            <div v-if="hasReferences" class="mt-1 pt-2 border-t border-border/50">
                <div class="flex items-center gap-2 mb-2">
                    <svg class="w-3 h-3 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    <span class="text-xs font-semibold text-muted-foreground">参考来源</span>
                </div>
                <div class="flex flex-wrap gap-2">
                    <div 
                        v-for="(ref, idx) in combinedSources" 
                        :key="idx"
                        class="group/ref flex items-center gap-1.5 px-2 py-1 bg-muted/50 border border-slate-200 rounded text-[11px] text-slate-600 cursor-pointer hover:bg-white hover:border-indigo-200 hover:shadow-sm hover:text-indigo-600 transition-all duration-200 max-w-[200px]"
                        @click="$emit('locate-node', ref)"
                        :title="ref.title || 'Unknown Source'"
                    >
                        <span class="font-mono text-muted-foreground group-hover/ref:text-indigo-400 text-[9px]">{{ Number(idx) + 1 }}</span>
                        <span class="truncate">{{ ref.title || 'Unknown Source' }}</span>
                    </div>
                </div>
            </div>

        </div>

        <!-- Actions (Footer) -->
        <div v-if="!isUser" class="mt-2 pt-2 flex items-center gap-4 text-muted-foreground border-t border-border/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
             <button class="hover:text-indigo-600 transition-colors" title="复制" @click="copyText(message.content)">
                <span class="text-xs">Copy</span>
             </button>
             <button class="hover:text-green-600 transition-colors" title="赞">
                <span class="text-xs">Like</span>
             </button>
             <button class="hover:text-red-600 transition-colors" title="踩">
                <span class="text-xs">Dislike</span>
             </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue';
import dayjs from 'dayjs';
import ChartFrame from '../../analytics/components/ChartFrame.vue';
import GenericResourceCard from './GenericResourceCard.vue';
import { useMessageParser } from '../composables/useMessageParser';
import { useChartOptions } from '../composables/useChart';

const props = defineProps({
  message: { type: Object, required: true },
  type: { type: String, default: 'knowledge_qa' },
  isUser: { type: Boolean, default: false },
  showAvatar: { type: Boolean, default: true },
  showMeta: { type: Boolean, default: false },
  agent: { type: Object, default: null }
});

const emit = defineEmits(['locate-node', 'open-doc-space']);

// Composables
const { parsed } = useMessageParser(toRef(props.message, 'content'));
const { processOption } = useChartOptions();

// Computed
const bubbleClasses = computed(() => {
  if (props.isUser) {
    return 'bg-indigo-600 text-white rounded-lg rounded-tr-sm';
  } else {
    return 'bg-white text-slate-700 rounded-lg rounded-tl-sm border border-slate-200';
  }
});

const chartOption = computed(() => {
    // Prefer parsed chart config from markdown, fallback to prop
    const config = parsed.value.chartConfig || props.message.chart_config;
    return processOption(config);
});

const hasReferences = computed(() => props.message.sources && props.message.sources.length > 0);
const combinedSources = computed(() => props.message.sources || []);

// Methods
const formatTime = (ts: any) => dayjs(ts).format('HH:mm');
const copyText = (text: string) => navigator.clipboard.writeText(text || '');

const handleResourceClick = (id: string) => {
    // Simple routing logic based on ID format or just emit
    emit('open-doc-space', id);
};

</script>

<style scoped>
.markdown-body { font-size: 14px; line-height: 1.6; color: #334155; }
.markdown-body :deep(h3) { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #1e293b; display: flex; align-items: center; gap: 8px; }
.markdown-body :deep(h3)::before { content: ''; display: inline-block; width: 4px; height: 16px; background: #3b82f6; border-radius: 2px; }
.markdown-body :deep(strong) { font-weight: 600; color: #1e293b; }

/* Table Styles */
.table-wrapper :deep(table) {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
    margin: 8px 0;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
}
.table-wrapper :deep(th) {
    background-color: #f8fafc;
    font-weight: 600;
    text-align: left;
    padding: 10px 16px;
    color: #475569;
    border-bottom: 1px solid #e2e8f0;
}
.table-wrapper :deep(td) {
    padding: 10px 16px;
    color: #334155;
    border-bottom: 1px solid #f1f5f9;
    background-color: #ffffff;
}
.table-wrapper :deep(tr:last-child td) {
    border-bottom: none;
}
.table-wrapper :deep(tr:hover td) {
    background-color: #f1f5f9;
}
</style>
