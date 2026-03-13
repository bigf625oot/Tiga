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
      class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden mt-0 transition-all duration-300 hover:scale-105"
      :class="[isUser ? 'bg-indigo-600 ml-4' : 'bg-muted mr-4']"
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
      <!-- Sender Name & Time (Agent) -->
      <div v-if="!isUser" class="flex items-center gap-2 mb-2 px-1">
        <span class="text-xs font-medium text-muted-foreground/70">{{ agent?.name || 'Tiga' }}</span>
        <span class="text-[10px] text-muted-foreground/50">{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Sender Name & Time (User - Optional, usually hidden or on right) -->
      <div v-if="isUser && showMeta" class="flex items-center gap-2 mb-2 px-1 text-xs text-muted-foreground">
         <span>{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Bubble -->
      <div 
        class="relative px-5 py-4 text-sm leading-relaxed transition-all duration-200 shadow-sm"
        :class="bubbleClasses"
      >
        <!-- User Mode: Simple Text -->
        <div v-if="isUser" class="whitespace-pre-wrap">{{ message.content }}</div>

        <!-- Agent Mode: Rich Content -->
        <div v-else class="agent-content flex flex-col gap-4">
            
            <!-- 1. Thinking Process (Collapsed by default) -->
            <div v-if="parsed.think" class="w-full">
                <details class="bg-primary/5 rounded-lg border border-primary/10 overflow-hidden group transition-all duration-300" :open="parsed.think.isPartial">
                    <summary class="p-4 py-2 text-xs font-medium text-primary cursor-pointer flex items-center gap-2 select-none outline-none hover:bg-primary/10 transition-colors">
                        <div class="flex items-center gap-2 flex-1">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                            <span>思考过程</span>
                        </div>
                        <svg class="w-3 h-3 text-primary/50 transform group-open:rotate-180 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </summary>
                    <div class="p-4 py-2 text-xs text-muted-foreground border-t border-primary/10 bg-card/50 leading-relaxed font-mono" v-html="parsed.think.html"></div>
                </details>
            </div>

            <!-- 2. Chart (Visual Priority) -->
            <div v-if="chartOption" class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                 <div class="p-4 py-2 border-b border-border bg-muted/50 flex items-center justify-between">
                    <span class="text-xs font-semibold text-foreground flex items-center gap-2">
                        <svg class="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                        </svg>
                        数据可视化
                    </span>
                 </div>
                 <div class="h-64 w-full relative bg-card">
                    <ChartFrame :option="chartOption" />
                 </div>
            </div>

            <!-- 3. Data Summary (Text + Table + SQL) -->
            <div 
                v-if="parsed.text || parsed.html || parsed.sql" 
                class="w-full group/summary"
                :class="chartOption ? 'bg-card rounded-lg border border-border shadow-sm p-4' : ''"
            >
                <!-- Title (Optional, only if chart exists to separate sections) -->
                <div v-if="chartOption" class="mb-2 pb-2 border-b border-border flex items-center gap-2">
                     <svg class="w-3.5 h-3.5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                     </svg>
                     <span class="text-xs font-semibold text-muted-foreground">数据详情</span>
                </div>

                <!-- Markdown Content (Table, Summary) -->
                <div v-if="parsed.html" class="markdown-body table-wrapper text-sm text-muted-foreground" v-html="parsed.html"></div>
                
                <!-- Embedded Resources -->
                <div v-if="parsed.resources.length > 0" class="flex flex-col gap-2" :class="chartOption ? 'm-4' : 'mt-4'">
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
                <div v-if="parsed.sql" class="pt-2 border-t border-border" :class="chartOption ? 'm-4' : 'mt-4'">
                    <details class="group/sql">
                        <summary class="flex items-center gap-2 text-[10px] text-muted-foreground cursor-pointer hover:text-primary transition-colors select-none w-fit">
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
                                <button @click.stop="copyText(parsed.sql)" class="p-1 text-muted-foreground hover:text-primary transition-colors" title="复制 SQL">
                                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                </button>
                             </div>
                             <pre class="!m-0 !p-2 !bg-transparent overflow-x-auto custom-scrollbar"><code class="text-primary/80 font-mono text-[10px] leading-4 whitespace-pre">{{ parsed.sql }}</code></pre>
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
                        class="group/ref flex items-center gap-1.5 px-2 py-1 bg-muted/50 border border-border rounded text-[11px] text-muted-foreground cursor-pointer hover:bg-accent hover:border-primary/30 hover:shadow-sm hover:text-primary transition-all duration-200 max-w-[200px]"
                        @click="$emit('locate-node', ref)"
                        :title="ref.title || 'Unknown Source'"
                    >
                        <span class="font-mono text-muted-foreground group-hover/ref:text-primary/70 text-[9px]">{{ Number(idx) + 1 }}</span>
                        <span class="truncate">{{ ref.title || 'Unknown Source' }}</span>
                    </div>
                </div>
            </div>

        </div>

        <!-- Actions (Footer) -->
        <div v-if="!isUser" class="mt-2 pt-2 flex items-center gap-4 text-muted-foreground border-t border-border/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
             <button class="hover:text-indigo-600 transition-colors" title="复制" @click="copyText(message.content)">
                <Copy class="w-4 h-4" />
             </button>
             <button class="hover:text-green-600 transition-colors" title="赞">
                <ThumbsUp class="w-4 h-4" />
             </button>
             <button class="hover:text-red-600 transition-colors" title="踩">
                <ThumbsDown class="w-4 h-4" />
             </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue';
import dayjs from 'dayjs';
import { Copy, ThumbsUp, ThumbsDown } from 'lucide-vue-next';
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
    return 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm';
  } else {
    // #F0F4F8 is slate-50/blue-50 like, #1F2937 is gray-800
    // Using Tailwind classes to approximate: bg-slate-100 text-gray-800
    // Or custom style if needed. Let's use Tailwind's slate palette which is close.
    // rounded-xl is 12px usually (0.75rem = 12px)
    return 'bg-[#F0F4F8] text-[#1F2937] rounded-xl border-none';
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
.markdown-body { font-size: 14px; line-height: 1.6; color: hsl(var(--foreground)); }
.markdown-body :deep(h3) { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: hsl(var(--foreground)); display: flex; align-items: center; gap: 8px; }
.markdown-body :deep(h3)::before { content: ''; display: inline-block; width: 4px; height: 16px; background: hsl(var(--primary)); border-radius: 2px; }
.markdown-body :deep(strong) { font-weight: 600; color: hsl(var(--foreground)); }

/* Table Styles */
.table-wrapper :deep(table) {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
    margin: 8px 0;
    border: 1px solid hsl(var(--border));
    border-radius: 8px;
    overflow: hidden;
}
.table-wrapper :deep(th) {
    background-color: hsl(var(--muted));
    font-weight: 600;
    text-align: left;
    padding: 10px 16px;
    color: hsl(var(--muted-foreground));
    border-bottom: 1px solid hsl(var(--border));
}
.table-wrapper :deep(td) {
    padding: 10px 16px;
    color: hsl(var(--foreground));
    border-bottom: 1px solid hsl(var(--muted));
    background-color: hsl(var(--card));
}
.table-wrapper :deep(tr:last-child td) {
    border-bottom: none;
}
.table-wrapper :deep(tr:hover td) {
    background-color: hsl(var(--muted) / 0.5);
}
</style>
