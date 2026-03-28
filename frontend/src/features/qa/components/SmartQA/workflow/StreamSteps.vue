<template>
  <div class="w-full">
    <Collapsible v-model:open="isOpen" class="border border-indigo-200/40 dark:border-indigo-900/40 rounded-xl overflow-hidden bg-indigo-50/30 dark:bg-indigo-950/15 shadow-sm">
      <CollapsibleTrigger as-child>
        <button class="w-full flex items-center justify-between px-3 py-2.5 hover:bg-indigo-100/30 dark:hover:bg-indigo-900/20 transition-colors group outline-none">
          <div class="flex items-center gap-2 min-w-0">
            <div class="w-6 h-6 rounded flex items-center justify-center bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 shrink-0">
              <Loader2 v-if="isStreaming" class="w-3.5 h-3.5 animate-spin" />
              <Activity v-else class="w-3.5 h-3.5" />
            </div>
            <div class="flex flex-col items-start min-w-0">
              <span class="text-xs font-medium text-indigo-700/90 dark:text-indigo-300/90">
                {{ isStreaming ? '正在执行' : '执行记录' }} ({{ filteredEvents.length }})
              </span>
              <span v-if="lastLine" class="text-[10px] text-indigo-700/60 dark:text-indigo-300/60 line-clamp-1 text-left">
                {{ lastLine }}
              </span>
            </div>
          </div>
          <ChevronDown class="w-4 h-4 text-indigo-600/50 transition-transform duration-200" :class="isOpen ? 'rotate-180' : ''" />
        </button>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div class="px-3 py-2 border-t border-indigo-200/30 dark:border-indigo-900/30 bg-background/40 space-y-2">
          <div class="space-y-1.5 relative">
            <!-- 竖线 -->
            <div class="absolute left-[7px] top-2 bottom-2 w-px bg-indigo-200/60 dark:bg-indigo-800/30"></div>

            <div v-for="item in filteredEvents" :key="item.id" class="relative pl-5">
              <!-- 时间线节点 -->
              <div class="absolute left-[1px] top-[6px] w-3.5 h-3.5 rounded-full border-2 bg-background z-10"
                :class="dotClass(item.event)">
                <div v-if="isStreaming && item === lastItem"
                  class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"></div>
              </div>

              <div class="flex items-start gap-1.5 min-w-0">
                <!-- 事件类型标签 -->
                <Badge variant="outline" class="text-[9px] h-4 px-1.5 font-normal bg-background shrink-0 mt-0.5"
                  :class="badgeClass(item.event)">
                  {{ labelOf(item.event) }}
                </Badge>

                <!-- thought：斜体思维文本 -->
                <div v-if="item.event === 'thought'"
                  class="text-[11px] text-muted-foreground/80 italic break-words whitespace-pre-wrap leading-relaxed min-w-0">
                  {{ item.content }}
                </div>

                <!-- tool_call：工具调用条 -->
                <div v-else-if="item.event === 'tool_call'"
                  class="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-mono min-w-0 max-w-full">
                  <Wrench class="w-2.5 h-2.5 shrink-0" />
                  <span class="font-semibold truncate">{{ item.raw?.content?.tool || item.content }}</span>
                  <span v-if="item.raw?.content?.args" class="text-muted-foreground truncate max-w-[140px]">
                    {{ JSON.stringify(item.raw.content.args).slice(0, 60) }}
                  </span>
                </div>

                <!-- tool_output：终端日志行 -->
                <div v-else-if="item.event === 'tool_output'"
                  class="text-[10px] text-green-600/90 dark:text-green-400/80 font-mono bg-slate-950/5 dark:bg-slate-900/60 rounded px-2 py-0.5 break-all min-w-0 max-w-full">
                  <span v-if="item.raw?.content?.is_error" class="text-red-500">✗ </span>
                  <span v-else class="text-green-500">✓ </span>
                  {{ item.raw?.content?.tool || '' }}
                  <span v-if="item.raw?.content?.logs?.length" class="text-muted-foreground">
                    · {{ item.raw.content.logs[0] }}
                  </span>
                </div>

                <!-- artifact：产出物卡片 -->
                <div v-else-if="item.event === 'artifact'"
                  class="flex items-center gap-2 text-[11px] border border-border rounded-lg px-2 py-1 bg-muted/40 min-w-0 max-w-full">
                  <FileOutput class="w-3 h-3 text-primary shrink-0" />
                  <span class="truncate font-medium">{{ item.raw?.content?.file_name || (typeof item.content === 'object' && item.content !== null ? (item.content as any).file_name : item.content) }}</span>
                  <span v-if="item.raw?.content?.file_size || (typeof item.content === 'object' && item.content !== null && (item.content as any).file_size)" class="text-muted-foreground shrink-0">
                    {{ formatFileSize(item.raw?.content?.file_size || (item.content as any).file_size) }}
                  </span>
                </div>

                <!-- summary：总结陈词 -->
                <div v-else-if="item.event === 'summary'"
                  class="text-[11px] text-foreground/90 font-medium break-words whitespace-pre-wrap leading-relaxed min-w-0">
                  {{ typeof item.content === 'string' ? item.content : JSON.stringify(item.content) }}
                </div>

                <!-- error：报错 -->
                <div v-else-if="item.event === 'error'"
                  class="text-[11px] text-red-500/90 break-words whitespace-pre-wrap font-mono leading-relaxed min-w-0">
                  {{ typeof item.content === 'string' ? item.content : JSON.stringify(item.content) }}
                </div>

                <!-- 其他 -->
                <div v-else class="text-[11px] text-muted-foreground break-words whitespace-pre-wrap font-mono leading-relaxed min-w-0">
                  {{ typeof item.content === 'string' ? item.content : JSON.stringify(item.content) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { Activity, ChevronDown, Loader2, Wrench, FileOutput } from 'lucide-vue-next';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import type { StreamEventItem } from '../../../types';
import { formatFileSize } from '../../../utils/dateUtils';

const props = defineProps<{
  events: StreamEventItem[];
  isStreaming?: boolean;
}>();

const isOpen = ref(true);

const filteredEvents = computed(() => {
  return props.events.filter(e => !['thought', 'text', 'think'].includes(e.event));
});

// 流式结束后 1.5s 自动收起
watch(() => props.isStreaming, (n, o) => {
  if (o && !n) {
    setTimeout(() => { isOpen.value = false; }, 1500);
  }
});

const lastItem = computed(() => filteredEvents.value.length > 0 ? filteredEvents.value[filteredEvents.value.length - 1] : null);
const lastLine = computed(() => {
  if (!lastItem.value) return '';
  return `${labelOf(lastItem.value.event)}: ${lastItem.value.content}`;
});

// 事件中文标签
const labelOf = (event: string): string => {
  const map: Record<string, string> = {
    thought:      '思考',
    plan_created: '规划',
    task_start:   '任务',
    tool_call:    '调用',
    tool_output:  '输出',
    artifact:     '产出物',
    summary:      '总结',
    text:         '回复',
    think:        '推理',
    error:        '错误',
    sources:      '来源',
    file:         '文件',
    image:        '图片',
    step:         '步骤',
  };
  return map[event] || event;
};

// 时间线节点与标签颜色配置提取
const EVENT_COLORS: Record<string, { dot: string, badge: string }> = {
  thought: { dot: 'border-indigo-400/60 dark:border-indigo-600/60', badge: 'text-indigo-600/70 border-indigo-300/40' },
  tool_call: { dot: 'border-blue-400/70 dark:border-blue-600/60', badge: 'text-blue-600 border-blue-300/50' },
  tool_output: { dot: 'border-green-400/70 dark:border-green-600/60', badge: 'text-green-600 border-green-300/50' },
  artifact: { dot: 'border-purple-400/70 dark:border-purple-600/60', badge: 'text-purple-600 border-purple-300/50' },
  summary: { dot: 'border-amber-400/70 dark:border-amber-600/60', badge: 'text-amber-600 border-amber-300/50' },
  error: { dot: 'border-red-400/70 dark:border-red-600/60', badge: 'text-red-600 border-red-300/50' },
  default: { dot: 'border-indigo-400/60 dark:border-indigo-600/60', badge: 'text-indigo-600/70 border-indigo-300/40' }
};

const dotClass = (event: string): string => (EVENT_COLORS[event] || EVENT_COLORS.default).dot;
const badgeClass = (event: string): string => (EVENT_COLORS[event] || EVENT_COLORS.default).badge;

</script>
