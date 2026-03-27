<template>
  <div class="tool-call-panel rounded-md border overflow-hidden transition-all duration-200"
       :class="panelBorderClass">
    <!-- Header row: always visible -->
    <button
      @click="isExpanded = !isExpanded"
      class="w-full flex items-center gap-2 px-2.5 py-1.5 transition-colors text-left group/tchead"
      :class="panelHeaderClass"
    >
      <!-- Tool icon -->
      <div class="w-4 h-4 flex-shrink-0 flex items-center justify-center" :class="iconColorClass">
        <component :is="toolIcon" class="w-3.5 h-3.5" />
      </div>

      <!-- Function signature -->
      <div class="flex-1 min-w-0 flex items-center gap-1.5 font-mono">
        <span class="text-xs font-semibold" :class="toolNameClass">{{ toolCall.name }}</span>
        <span class="text-[11px] text-muted-foreground/50 truncate max-w-[200px]">{{ argsPreview }}</span>
      </div>

      <!-- Status badge + chevron -->
      <div class="flex-shrink-0 flex items-center gap-2">
        <span v-if="toolCall.status === 'error'" class="flex items-center gap-1 text-[10px] text-destructive font-medium">
          <XCircle class="w-3 h-3" />失败
        </span>
        <span v-else-if="toolCall.status === 'success'" class="flex items-center gap-1 text-[10px] text-emerald-500 font-medium">
          <CheckCircle2 class="w-3 h-3" />完成
        </span>
        <span v-else class="flex items-center gap-1 text-[10px] text-muted-foreground/50">
          <Loader2 class="w-3 h-3 animate-spin" />执行中
        </span>
        <ChevronDown
          class="w-3 h-3 text-muted-foreground/30 transition-transform duration-200 group-hover/tchead:text-muted-foreground/60"
          :class="isExpanded ? 'rotate-180' : ''"
        />
      </div>
    </button>

    <!-- Expanded body: input args + output -->
    <div v-if="isExpanded" class="border-t" :class="panelDividerClass">
      <!-- Input -->
      <div v-if="hasArgs" class="px-3 py-2 bg-muted/5">
        <div class="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground/40 mb-1.5">输入参数</div>
        <pre class="text-[11px] font-mono text-foreground/70 overflow-x-auto whitespace-pre-wrap leading-relaxed custom-scrollbar">{{ formattedArgs }}</pre>
      </div>

      <!-- Output -->
      <div v-if="toolCall.result !== undefined" class="px-3 py-2 border-t"
           :class="toolCall.status === 'error' ? 'border-destructive/10 bg-destructive/5' : 'border-border/20 bg-emerald-500/5'">
        <div class="text-[10px] uppercase tracking-widest font-semibold mb-1.5"
             :class="toolCall.status === 'error' ? 'text-destructive/50' : 'text-emerald-600/50 dark:text-emerald-400/50'">
          {{ toolCall.status === 'error' ? '错误信息' : '执行结果' }}
        </div>
        <pre class="text-[11px] font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed custom-scrollbar"
             :class="toolCall.status === 'error' ? 'text-destructive/80' : 'text-foreground/65'">{{ formatOutput(toolCall.result) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  ChevronDown, CheckCircle2, XCircle, Loader2,
  Search, FileText, Terminal, Globe, Database,
  Code2, Wrench, BookOpen, Calculator, Zap
} from 'lucide-vue-next';

import type { ToolCall } from '../../../types';

const props = defineProps<{
  toolCall: ToolCall;
}>();

const isExpanded = ref(false);

// ── Icon mapping: tool name → lucide icon (extensible)
const TOOL_ICON_MAP: Record<string, any> = {
  search: Search,
  web_search: Globe,
  read_file: FileText,
  write_file: FileText,
  execute: Terminal,
  run_code: Terminal,
  python: Terminal,
  bash: Terminal,
  sql: Database,
  query: Database,
  database: Database,
  calculate: Calculator,
  math: Calculator,
  knowledge: BookOpen,
  rag: BookOpen,
};

const toolIcon = computed(() => {
  const name = (props.toolCall.name || '').toLowerCase();
  for (const key of Object.keys(TOOL_ICON_MAP)) {
    if (name.includes(key)) return TOOL_ICON_MAP[key];
  }
  return Wrench;
});

// ── Status-driven styles
const panelBorderClass = computed(() => {
  if (props.toolCall.status === 'error') return 'border-destructive/30 bg-destructive/5';
  if (props.toolCall.status === 'success') return 'border-border/30 bg-muted/5';
  return 'border-border/40 bg-muted/10';
});

const panelHeaderClass = computed(() => {
  if (props.toolCall.status === 'error') return 'hover:bg-destructive/5';
  if (props.toolCall.status === 'success') return 'hover:bg-muted/15';
  return 'hover:bg-muted/20';
});

const panelDividerClass = computed(() => {
  if (props.toolCall.status === 'error') return 'border-destructive/20';
  return 'border-border/25';
});

const iconColorClass = computed(() => {
  if (props.toolCall.status === 'error') return 'text-destructive/60';
  if (props.toolCall.status === 'success') return 'text-emerald-500/70';
  return 'text-primary/60';
});

const toolNameClass = computed(() => {
  if (props.toolCall.status === 'error') return 'text-destructive/80';
  if (props.toolCall.status === 'success') return 'text-foreground/70';
  return 'text-foreground/85';
});

// ── Args formatting
const hasArgs = computed(() => {
  const a = props.toolCall.args;
  return a && typeof a === 'object' && Object.keys(a).length > 0;
});

const argsPreview = computed(() => {
  const a = props.toolCall.args;
  if (!a || typeof a !== 'object') return '()';
  const entries = Object.entries(a);
  if (entries.length === 0) return '()';
  // Show first key=value pair as preview
  const [k, v] = entries[0];
  const valStr = typeof v === 'string' ? `"${v.slice(0, 40)}"` : JSON.stringify(v)?.slice(0, 40) ?? '';
  const more = entries.length > 1 ? ` +${entries.length - 1}项` : '';
  return `(${k}=${valStr}${more})`;
});

const formattedArgs = computed(() => {
  const a = props.toolCall.args;
  if (!a) return '';
  try { return JSON.stringify(a, null, 2); } catch { return String(a); }
});

const formatOutput = (result: string | undefined) => {
  if (!result) return '';
  // Attempt JSON pretty print
  try {
    const parsed = JSON.parse(result);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return result;
  }
};
</script>
