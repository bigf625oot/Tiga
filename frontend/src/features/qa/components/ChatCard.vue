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
      :class="isUser ? 'ml-4' : 'mr-4'"
    >
      <img :src="avatarSrc" :alt="avatarAlt" class="w-full h-full object-cover" />
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
        <span v-if="message.meta_data?.duration" class="text-[10px] text-muted-foreground/40">耗时 {{ formatDuration(message.meta_data.duration) }}</span>
      </div>

      <!-- Sender Name & Time (User - Optional, usually hidden or on right) -->
      <div v-if="isUser && showMeta" class="flex items-center gap-2 mb-2 px-1 text-xs text-muted-foreground">
         <span>{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Bubble -->
      <div 
        class="relative px-4 py-3 text-sm leading-normal transition-all duration-200 shadow-sm"
        :class="bubbleClasses"
      >
        <template v-if="isUser">
            <div v-if="isEditing" class="flex flex-col gap-2 min-w-[200px]">
                <textarea 
                    v-model="editContent" 
                    class="w-full bg-transparent text-primary-foreground placeholder:text-primary-foreground/50 resize-none outline-none border border-primary-foreground/20 rounded p-2 focus:border-primary-foreground/50 transition-colors custom-scrollbar"
                    rows="3"
                    @keydown.ctrl.enter="saveEdit"
                    @keydown.esc="cancelEdit"
                ></textarea>
                <div class="flex justify-end gap-2 text-xs">
                    <button @click="cancelEdit" class="px-2 py-1 rounded bg-primary-foreground/10 hover:bg-primary-foreground/20 transition-colors">取消</button>
                    <button @click="saveEdit" class="px-2 py-1 rounded bg-primary-foreground text-primary hover:bg-primary-foreground/90 transition-colors">发送</button>
                </div>
            </div>
            <div v-else class="user-markdown" v-html="userHtml"></div>
        </template>

        <!-- Agent Mode: Rich Content -->
        <div v-else class="agent-content flex flex-col gap-3">
            
            <StreamSteps
                v-if="showStreamSteps"
                :events="message.stream_events"
                :is-streaming="isStreaming && isLast"
            />

            <!-- 0. Empty State / Initial Loading -->
            <div v-if="!parsed.text && !parsed.sql && !thinkingContent && !chartOption && !message.steps?.length && (!showStreamSteps) && isStreaming && isLast" class="flex items-center gap-2 py-1">
                <span class="relative flex h-2.5 w-2.5">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                </span>
                <span class="text-xs text-muted-foreground/60 font-medium animate-pulse">正在生成回复...</span>
            </div>

            <!-- 0. Process Steps (New) -->
            <div v-if="message.steps && message.steps.length > 0" class="border border-amber-200/40 dark:border-amber-900/40 rounded-xl overflow-hidden mb-2 bg-amber-50/40 dark:bg-amber-950/20 w-full shadow-sm">
                <button 
                    @click="isStepsExpanded = !isStepsExpanded"
                    class="w-full flex items-center justify-between px-3 py-2.5 hover:bg-amber-100/30 dark:hover:bg-amber-900/30 transition-colors group"
                >
                    <div class="flex items-center gap-2 text-xs font-medium text-amber-700/80 dark:text-amber-500/90">
                        <Brain class="w-3.5 h-3.5" />
                        <span>思考链 ({{ message.steps.length }} 步)</span>
                    </div>
                    <ChevronRight 
                        class="w-3.5 h-3.5 text-amber-600/50 dark:text-amber-500/50 transition-transform duration-200 group-hover:text-amber-600 dark:group-hover:text-amber-400"
                        :class="isStepsExpanded ? 'rotate-90' : ''"
                    />
                </button>
                <div v-show="isStepsExpanded" class="bg-background/40 px-3 py-2 border-t border-amber-200/30 dark:border-amber-900/30">
                    <div class="space-y-3 relative">
                        <div class="absolute left-[5px] top-1.5 bottom-1.5 w-px bg-amber-200/50 dark:bg-amber-800/30"></div>
                        <div v-for="(step, sIdx) in message.steps" :key="sIdx" class="flex gap-3 relative">
                            <div class="flex flex-col items-center pt-1.5 shrink-0 z-10">
                                <div class="w-2.5 h-2.5 rounded-full bg-background border-2 border-amber-400/60 dark:border-amber-600/60 shadow-sm"></div>
                            </div>
                            <div class="pb-1 min-w-0 flex-1">
                                <div class="text-[11px] text-muted-foreground break-words whitespace-pre-wrap font-mono leading-relaxed">
                                    {{ step.content }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 1. Thinking Process -->
            <ThinkingBlock 
                v-if="thinkingContent" 
                :content="thinkingContent.raw" 
                :is-thinking="thinkingContent.isPartial"
            />

            <!-- 1.5. Tools Status (新加入的工具流状态) -->
            <ToolStatus 
                v-if="message.tools && message.tools.length > 0" 
                :tools="message.tools" 
            />

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
                v-if="parsed.text || parsed.sql" 
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
                <div v-if="parsed.text" class="w-full mt-2">
                    <MarkdownRenderer :content="parsed.text" />
                </div>
                
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

            <!-- 5. Error Alert -->
            <ErrorCallout 
                v-if="message.error" 
                :message="message.error" 
                :can-retry="true"
                @retry="$emit('resend-message', message)"
            />

            <!-- 6. Streaming Cursor -->
            <div v-if="isStreaming && isLast && (parsed.text || thinkingContent)" class="h-4 mt-1">
                 <span class="inline-block w-2 h-4 bg-indigo-500/80 animate-pulse rounded-sm"></span>
            </div>

        </div>
      </div>

      <!-- Actions (Outside Bubble) -->
      <div class="flex items-center gap-2 mt-2" :class="isUser ? 'mr-1 justify-end' : 'ml-1'">
          <template v-if="isUser">
              <button v-if="!isEditing" class="p-1 text-muted-foreground/60 hover:text-indigo-600 transition-colors" title="编辑" @click="startEdit">
                  <Pencil class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/60 hover:text-indigo-600 transition-colors" title="复制" @click="copyText(message.content)">
                  <Copy class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/60 hover:text-indigo-600 transition-colors" title="重新发送" @click="$emit('resend-message', message)">
                  <RotateCcw class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/60 hover:text-destructive transition-colors" title="删除" @click="$emit('delete-message', message)">
                  <Trash2 class="w-3.5 h-3.5" />
              </button>
          </template>
          <template v-else>
              <button class="p-1 text-muted-foreground/60 hover:text-indigo-600 transition-colors" title="引用" @click="$emit('quote-message', message.content)">
                  <Quote class="w-3.5 h-3.5" />
              </button>
              <button
                  class="p-1 text-muted-foreground/60 hover:text-amber-500 transition-colors relative"
                  title="摘录到秒记"
                  @click="handleExcerpt"
              >
                  <Bookmark class="w-3.5 h-3.5" :class="{'fill-current text-amber-500 animate-pulse': isExcerptionAnimating}" />
                  <span v-if="isExcerptionAnimating" class="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] text-amber-600 font-bold animate-out fade-out slide-out-to-top-2 duration-500">+1</span>
              </button>
              <button class="p-1 text-muted-foreground/60 hover:text-indigo-600 transition-colors" title="复制" @click="copyText(message.content)">
                  <Copy class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/60 hover:text-green-600 transition-colors" title="赞">
                  <ThumbsUp class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/60 hover:text-red-600 transition-colors" title="踩">
                  <ThumbsDown class="w-3.5 h-3.5" />
              </button>
          </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef, ref, watch, nextTick } from 'vue';
import dayjs from 'dayjs';
import { Activity, Copy, ThumbsUp, ThumbsDown, Quote, Bookmark, Brain, ChevronRight, Trash2, Pencil, RotateCcw } from 'lucide-vue-next';
import ChartFrame from '../../analytics/components/ChartFrame.vue';
import GenericResourceCard from './GenericResourceCard.vue';
import { useMessageParser } from '../composables/useMessageParser';
import { useChartOptions } from '../composables/useChart';
import { useMarkdown, isHighlighterReady } from '../composables/useMarkdown';

// 新引入的 UI 组件
import ThinkingBlock from './SmartQA/ThinkingBlock.vue';
import ToolStatus from './SmartQA/ToolStatus.vue';
import MarkdownRenderer from './SmartQA/MarkdownRenderer.vue';
import ErrorCallout from './SmartQA/ErrorCallout.vue';
import StreamSteps from './SmartQA/StreamSteps.vue';

const props = defineProps({
  message: { type: Object, required: true },
  type: { type: String, default: 'knowledge_qa' },
  isUser: { type: Boolean, default: false },
  showAvatar: { type: Boolean, default: true },
  showMeta: { type: Boolean, default: false },
  agent: { type: Object, default: null },
  isLast: { type: Boolean, default: false },
  isStreaming: { type: Boolean, default: false },
  currentModeId: { type: String, default: null }
});

const emit = defineEmits(['locate-node', 'open-doc-space', 'quote-message', 'excerpt-message', 'delete-message', 'resend-message', 'edit-message']);

const isExcerptionAnimating = ref(false);
const isStepsExpanded = ref(true);

const isEditing = ref(false);
const editContent = ref('');

const startEdit = () => {
    editContent.value = props.message.content;
    isEditing.value = true;
};

const cancelEdit = () => {
    isEditing.value = false;
    editContent.value = '';
};

const saveEdit = () => {
    if (!editContent.value.trim()) return;
    emit('edit-message', { originalMessage: props.message, newContent: editContent.value });
    isEditing.value = false;
};

const handleExcerpt = () => {
    isExcerptionAnimating.value = true;
    emit('excerpt-message', props.message.content);
    setTimeout(() => {
        isExcerptionAnimating.value = false;
    }, 600);
};

// Composables
const contentRef = computed(() => props.message?.content || '');
const { parsed } = useMessageParser(contentRef);
const { processOption } = useChartOptions();
const { render } = useMarkdown();
const userHtml = computed(() => {
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions
    isHighlighterReady.value;
    return render(contentRef.value, { allowHtml: false });
});

watch(() => props.message.steps, (newVal, oldVal) => {
    if (newVal && newVal.length > 0 && (!oldVal || oldVal.length === 0)) {
        isStepsExpanded.value = true;
    }
}, { deep: true });

// Computed
const showStreamSteps = computed(() => {
    if (!props.message.stream_events || props.message.stream_events.length === 0) return false;
    // Filter out pure generation events to see if there's any actual execution trace
    const hasExecutionEvents = props.message.stream_events.some((e: any) => 
        !['thought', 'text', 'think'].includes(e.event)
    );
    if (!hasExecutionEvents) return false;
    
    // 不在 quick 模式下展示执行记录
    if (props.currentModeId === 'quick') return false;
    return true;
});

type ThinkingContent = {
    raw: string;
    html: string;
    isPartial: boolean;
};

const thinkingContent = computed<ThinkingContent | null>(() => {
    // 1. Parsed from content <think> tags (highest priority)
    if (parsed.value.think) {
        return parsed.value.think;
    }

    // 2. Explicit reasoning field (from stream)
    if (props.message.reasoning) {
        // PERF: Don't call render() during streaming — ThinkingBlock uses `raw` only.
        // render() (Shiki+marked) blocks the main thread and runs on every token.
        // Only compute html after streaming completes.
        const isActive = props.isStreaming && props.isLast;
        return {
            raw: props.message.reasoning,
            html: '', // HTML is not used by ThinkingBlock anyway
            isPartial: isActive,
        };
    }

    // 3. Metadata reasoning (from history)
    if (props.message.meta_data && props.message.meta_data.reasoning) {
        return {
            raw: props.message.meta_data.reasoning,
            html: '', // Not used
            isPartial: false // History defaults to collapsed
        };
    }

    return null;
});

const bubbleClasses = computed(() => {
  if (props.isUser) {
    return 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm';
  } else {
    // Use semantic colors for dark mode compatibility
    // Light mode: bg-muted (~#F1F5F9) text-foreground
    // Dark mode: bg-muted (Darker grey) text-foreground (White)
    return 'bg-muted text-foreground rounded-xl border-none';
  }
});

const chartOption = computed(() => {
    // Prefer parsed chart config from markdown, fallback to prop
    const config = parsed.value.chartConfig || props.message.chart_config;
    return processOption(config);
});

const hasReferences = computed(() => props.message.sources && props.message.sources.length > 0);
const combinedSources = computed(() => props.message.sources || []);
const avatarSrc = computed(() => {
  if (props.isUser) return '/user/hair.svg';
  return props.agent?.icon || props.agent?.icon_url || '/tiga.svg';
});
const avatarAlt = computed(() => (props.isUser ? 'user' : 'agent'));

// Methods
const formatTime = (ts: any) => dayjs(ts).format('YYYY-MM-DD HH:mm');
const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
};
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
.markdown-body :deep(img) { max-width: 100%; height: auto; border-radius: 8px; margin: 8px 0; border: 1px solid hsl(var(--border)); }

.user-markdown :deep(p) { margin: 0; }
.user-markdown :deep(p + p) { margin-top: 0.75rem; }
.user-markdown :deep(strong) { font-weight: 600; }
.user-markdown :deep(a) { color: inherit; text-decoration: underline; }
.user-markdown :deep(blockquote) { margin: 0; padding-left: 0.75rem; border-left: 2px solid hsl(var(--primary-foreground) / 0.35); }
.user-markdown :deep(ul) { list-style-type: disc; padding-left: 1.25rem; margin-bottom: 0.5rem; }
.user-markdown :deep(ol) { list-style-type: decimal; padding-left: 1.25rem; margin-bottom: 0.5rem; }
.user-markdown :deep(li) { margin-bottom: 0.25rem; }
.user-markdown :deep(pre) { 
    background-color: hsl(var(--primary-foreground) / 0.1); 
    padding: 0.75rem; 
    border-radius: 0.5rem; 
    overflow-x: auto; 
    margin: 0.5rem 0;
    font-family: "Hack", monospace;
    font-size: 0.9em;
}
.user-markdown :deep(code) { 
    background-color: hsl(var(--primary-foreground) / 0.15); 
    padding: 0.125rem 0.25rem; 
    border-radius: 0.25rem; 
    font-family: "Hack", monospace;
    font-size: 0.9em;
}
.user-markdown :deep(pre code) {
    background-color: transparent;
    padding: 0;
    font-size: 1em;
    color: inherit;
}
.user-markdown :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 0.5rem 0;
    font-size: 0.9em;
}
.user-markdown :deep(th), .user-markdown :deep(td) {
    border: 1px solid hsl(var(--primary-foreground) / 0.2);
    padding: 0.25rem 0.5rem;
}
.user-markdown :deep(th) {
    background-color: hsl(var(--primary-foreground) / 0.1);
    font-weight: 600;
}

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
