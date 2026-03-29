<script setup lang="ts">
import { computed, ref } from 'vue';
import { 
  Loader2, CheckCircle2, AlertCircle, ChevronRight, ChevronDown, 
  Globe, BookOpen, Wrench, Search
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
  return 'general';
});

const displayTitle = computed(() => {
  if (status.value === 'running') {
    if (toolCategory.value === 'web_search') return 'Searching the web...';
    if (toolCategory.value === 'knowledge') return 'Searching knowledge base...';
    return `Using ${props.toolCall.tool_name}...`;
  } else if (status.value === 'success') {
    if (toolCategory.value === 'web_search') return 'Searched the web';
    if (toolCategory.value === 'knowledge') return 'Analyzed knowledge base';
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
    return Wrench;
  }
  return AlertCircle;
});

const statusColor = computed(() => {
  if (status.value === 'running') return 'text-muted-foreground';
  if (status.value === 'success') return 'text-muted-foreground';
  return 'text-destructive';
});
</script>

<template>
  <div class="inline-flex flex-col transition-all duration-300">
    <!-- Compact Chip (OpenAI style) -->
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
    <div v-show="isExpanded" class="mt-2 rounded-xl border border-border bg-card shadow-sm overflow-hidden p-4 space-y-4 max-w-2xl">
      <!-- Arguments -->
      <div>
        <div class="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Arguments</div>
        <div class="bg-muted/50 p-2.5 rounded-md overflow-x-auto border border-border/50">
          <pre class="text-xs font-mono text-foreground/90 whitespace-pre-wrap">{{ typeof toolCall.arguments === 'string' ? toolCall.arguments : JSON.stringify(toolCall.arguments, null, 2) }}</pre>
        </div>
      </div>

      <!-- Result -->
      <div v-if="toolResult">
        <div class="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Result</div>
        <div class="bg-muted/50 p-2.5 rounded-md overflow-x-auto border border-border/50" :class="{'border-destructive/50 bg-destructive/5': toolResult.is_error}">
          <pre class="text-xs font-mono whitespace-pre-wrap" :class="toolResult.is_error ? 'text-destructive' : 'text-foreground/90'">{{ toolResult.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
