<script setup lang="ts">
import { computed, ref } from 'vue';
import { 
  Loader2, AlertCircle, ChevronRight, ChevronDown, 
  Globe, BookOpen, Wrench,Code2, Terminal
} from 'lucide-vue-next';
import type { ToolCallBlock, ToolResultBlock } from '@/features/llm-chat/shared/types';

const props = defineProps<{
  toolCall: ToolCallBlock;
  toolResult?: ToolResultBlock;
}>();

const isExpanded = ref(false);

const toggle = () => {
  isExpanded.value = !isExpanded.value;
};

const status = computed(() => props.toolCall.state);

// Determine tool category
const toolCategory = computed(() => {
  const name = props.toolCall.tool_name.toLowerCase();
  if (name.includes('search') || name.includes('tavily') || name.includes('exa') || name.includes('website') || name.includes('wikipedia') || name.includes('arxiv') || name.includes('brave')) {
    if (name.includes('knowledge') || name.includes('kb')) {
      return 'knowledge';
    }
    return 'web_search';
  }
  if (name.includes('knowledge') || name.includes('rag') || name.includes('kb')) {
    return 'knowledge';
  }
  if (name.includes('edit') || name.includes('write') || name.includes('replace') || name.includes('file')) {
    return 'file_edit';
  }
  if (name.includes('shell') || name.includes('bash') || name.includes('cmd') || name.includes('run')) {
    return 'terminal';
  }
  return 'general';
});

const displayTitle = computed(() => {
  if (status.value === 'running') {
    if (toolCategory.value === 'web_search') return 'Searching the web...';
    if (toolCategory.value === 'knowledge') return 'Searching knowledge base...';
    if (toolCategory.value === 'file_edit') return 'Editing file...';
    if (toolCategory.value === 'terminal') return 'Running command...';
    return `Using ${props.toolCall.tool_name}...`;
  } else if (status.value === 'success') {
    if (toolCategory.value === 'web_search') return 'Searched the web';
    if (toolCategory.value === 'knowledge') return 'Analyzed knowledge base';
    if (toolCategory.value === 'file_edit') return 'Edited file';
    if (toolCategory.value === 'terminal') return 'Ran command';
    return `Used ${props.toolCall.tool_name}`;
  } else {
    return `Failed to use ${props.toolCall.tool_name}`;
  }
});

const statusIcon = computed(() => {
  if (status.value === 'running') return Loader2;
  if (status.value === 'success') {
    if (toolCategory.value === 'web_search') return Globe;
    if (toolCategory.value === 'knowledge') return BookOpen;
    if (toolCategory.value === 'file_edit') return Code2;
    if (toolCategory.value === 'terminal') return Terminal;
    return Wrench;
  }
  return AlertCircle;
});

const statusColor = computed(() => {
  if (status.value === 'running') return 'text-muted-foreground';
  if (status.value === 'success') return 'text-muted-foreground';
  return 'text-destructive';
});

// Trae Style Code Diff parser
const diffContent = computed(() => {
  if (toolCategory.value !== 'file_edit') return null;
  const args = props.toolCall.arguments;
  if (!args) return null;
  
  let contentStr = '';
  let filePath = '';
  
  if (typeof args === 'string') {
    try {
      const parsed = JSON.parse(args) as Record<string, any>;
      contentStr = parsed.content || parsed.diff || parsed.new_str || '';
      filePath = parsed.path || parsed.file_path || '';
    } catch {
      contentStr = args;
    }
  } else if (typeof args === 'object' && args !== null) {
    const objArgs = args as Record<string, any>;
    contentStr = objArgs.content || objArgs.diff || objArgs.new_str || '';
    filePath = objArgs.path || objArgs.file_path || '';
  }
  
  if (!contentStr) return null;
  
  return {
    path: filePath,
    lines: contentStr.split('\n')
  };
});
</script>

<template>
  <div class="inline-flex flex-col transition-all duration-300 w-full">
    <!-- Trae Style Action Block (For file edits) -->
    <div v-if="diffContent" class="my-2 border border-border rounded-xl overflow-hidden bg-card shadow-sm w-full">
      <div class="px-4 py-2 bg-muted/50 flex items-center justify-between border-b border-border">
        <div class="flex items-center gap-2">
          <Code2 class="w-3.5 h-3.5 text-primary" />
          <span class="text-xs font-mono font-medium truncate max-w-[300px]">{{ diffContent.path || toolCall.tool_name }}</span>
        </div>
        <div class="flex gap-2 items-center">
          <Loader2 v-if="status === 'running'" class="w-3.5 h-3.5 animate-spin text-muted-foreground" />
          <span v-else :class="['text-[10px] font-bold px-2 py-1 rounded', status === 'success' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-destructive/10 text-destructive']">
            {{ status.toUpperCase() }}
          </span>
        </div>
      </div>
      <div class="p-4 bg-zinc-950 text-[12px] font-mono leading-6 overflow-x-auto text-zinc-300 max-h-[300px] overflow-y-auto custom-scrollbar">
        <div v-for="(line, idx) in diffContent.lines" :key="idx" 
             class="whitespace-pre"
             :class="line.startsWith('+') ? 'text-emerald-400 bg-emerald-900/20 px-2 -mx-2' : line.startsWith('-') ? 'text-rose-400 bg-rose-900/20 px-2 -mx-2' : 'px-2 -mx-2'">
          {{ line || ' ' }}
        </div>
      </div>
    </div>

    <!-- Default Compact Chip (For other tools) -->
    <template v-else>
      <div 
        class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/50 hover:bg-muted/50 cursor-pointer transition-colors shadow-sm w-fit"
        @click="toggle"
      >
        <component 
          :is="statusIcon" 
          class="w-3.5 h-3.5" 
          :class="[statusColor, { 'animate-spin': status === 'running' }]" 
        />
        <span class="text-xs font-medium text-foreground/80">
          {{ displayTitle }}
        </span>
        <ChevronDown v-if="isExpanded" class="w-3.5 h-3.5 text-muted-foreground ml-1" />
        <ChevronRight v-else class="w-3.5 h-3.5 text-muted-foreground ml-1" />
      </div>

      <!-- Expanded Details -->
      <div v-show="isExpanded" class="mt-2 rounded-xl border border-border bg-card shadow-sm overflow-hidden p-4 space-y-4 max-w-2xl w-full">
        <!-- Arguments -->
        <div>
          <div class="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Arguments</div>
          <div class="bg-muted/50 p-2.5 rounded-md overflow-x-auto border border-border/50 max-h-[200px] custom-scrollbar">
            <pre class="text-xs font-mono text-foreground/90 whitespace-pre-wrap">{{ typeof toolCall.arguments === 'string' ? toolCall.arguments : JSON.stringify(toolCall.arguments, null, 2) }}</pre>
          </div>
        </div>

        <!-- Result -->
        <div v-if="toolResult">
          <div class="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Result</div>
          <div class="bg-muted/50 p-2.5 rounded-md overflow-x-auto border border-border/50 max-h-[200px] custom-scrollbar" :class="{'border-destructive/50 bg-destructive/5': toolResult.is_error}">
            <pre v-if="typeof toolResult.content === 'string' && !toolResult.content.startsWith('[') && !toolResult.content.startsWith('{')" class="text-xs font-mono whitespace-pre-wrap" :class="toolResult.is_error ? 'text-destructive' : 'text-foreground/90'">{{ toolResult.content }}</pre>
            <pre v-else class="text-xs font-mono whitespace-pre-wrap" :class="toolResult.is_error ? 'text-destructive' : 'text-foreground/90'">{{ typeof toolResult.content === 'string' ? (toolResult.content.length > 500 ? toolResult.content.substring(0, 500) + '\n\n... (Result truncated for display)' : toolResult.content) : JSON.stringify(toolResult.content, null, 2).substring(0, 500) + '\n\n... (Result truncated for display)' }}</pre>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
