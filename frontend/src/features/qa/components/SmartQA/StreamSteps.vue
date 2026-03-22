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
              <span class="text-xs font-medium text-indigo-700/90 dark:text-indigo-300/90 truncate">
                {{ isStreaming ? '正在执行' : '执行记录' }} ({{ events.length }})
              </span>
              <span v-if="lastLine" class="text-[10px] text-indigo-700/60 dark:text-indigo-300/60 line-clamp-1 text-left">
                {{ lastLine }}
              </span>
            </div>
          </div>
          <ChevronDown class="w-4 h-4 text-indigo-600/50 dark:text-indigo-400/50 transition-transform duration-200" :class="isOpen ? 'rotate-180' : ''" />
        </button>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div class="px-3 py-2 border-t border-indigo-200/30 dark:border-indigo-900/30 bg-background/40 space-y-2">
          <div class="space-y-2 relative">
            <div class="absolute left-[7px] top-2 bottom-2 w-px bg-indigo-200/60 dark:bg-indigo-800/30"></div>
            <div v-for="item in events" :key="item.id" class="relative pl-5">
              <div class="absolute left-[1px] top-[6px] w-3.5 h-3.5 rounded-full border-2 bg-background z-10 border-indigo-400/60 dark:border-indigo-600/60">
                <div v-if="isStreaming && item === lastItem" class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"></div>
              </div>
              <div class="flex items-start gap-2 min-w-0">
                <Badge variant="outline" class="text-[9px] h-4 px-1.5 font-normal bg-background shrink-0">
                  {{ normalizeEventLabel(item.event) }}
                </Badge>
                <div class="text-[11px] text-muted-foreground break-words whitespace-pre-wrap font-mono leading-relaxed min-w-0">
                  {{ item.content }}
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
import { Activity, ChevronDown, Loader2 } from 'lucide-vue-next';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import type { StreamEventItem } from '../../types';

const props = defineProps<{
  events: StreamEventItem[];
  isStreaming?: boolean;
}>();

const isOpen = ref(true);

watch(
  () => props.isStreaming,
  (n, o) => {
    if (o && !n) {
      setTimeout(() => {
        isOpen.value = false;
      }, 1500);
    }
  }
);

const lastItem = computed(() => (props.events.length > 0 ? props.events[props.events.length - 1] : null));
const lastLine = computed(() => (lastItem.value ? `${normalizeEventLabel(lastItem.value.event)}: ${lastItem.value.content}` : ''));

const normalizeEventLabel = (event: string) => {
  if (!event) return 'event';
  const map: Record<string, string> = {
    status: 'status',
    step: 'step',
    plan: 'plan',
    plan_step: 'plan_step',
    tool_start: 'tool_start',
    tool_end: 'tool_end',
    tool_call: 'tool_call',
    think: 'think',
    text: 'text',
    sources: 'sources',
    file: 'file',
    image: 'image',
    meta: 'meta',
    error: 'error',
    done: 'done'
  };
  return map[event] || event;
};
</script>
