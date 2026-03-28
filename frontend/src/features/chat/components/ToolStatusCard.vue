<script setup lang="ts">
import { computed } from 'vue';
import { Wrench, Loader2, CheckCircle2, AlertCircle, ChevronRight, ChevronDown } from 'lucide-vue-next';
import { ref } from 'vue';
import type { ToolCallBlock, ToolResultBlock } from '../types';

const props = defineProps<{
  toolCall: ToolCallBlock;
  toolResult?: ToolResultBlock;
}>();

const isExpanded = ref(false);

const toggle = () => {
  isExpanded.value = !isExpanded.value;
};

const status = computed(() => props.toolCall.state);

const statusIcon = computed(() => {
  if (status.value === 'running') return Loader2;
  if (status.value === 'success') return CheckCircle2;
  return AlertCircle;
});

const statusColor = computed(() => {
  if (status.value === 'running') return 'text-blue-500';
  if (status.value === 'success') return 'text-green-500';
  return 'text-red-500';
});
</script>

<template>
  <div class="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col transition-all duration-300">
    <div 
      class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-muted/30 transition-colors"
      @click="toggle"
    >
      <div class="flex items-center gap-3">
        <component 
          :is="statusIcon" 
          class="w-4 h-4" 
          :class="[statusColor, { 'animate-spin': status === 'running' }]" 
        />
        <div class="flex flex-col">
          <span class="text-sm font-medium text-foreground">
            Using {{ toolCall.tool_name }}
          </span>
          <span class="text-xs text-muted-foreground" v-if="status === 'running'">
            Running tool...
          </span>
          <span class="text-xs text-muted-foreground" v-else-if="status === 'success'">
            Completed successfully
          </span>
          <span class="text-xs text-destructive" v-else>
            Tool failed
          </span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <ChevronDown v-if="isExpanded" class="w-4 h-4 text-muted-foreground" />
        <ChevronRight v-else class="w-4 h-4 text-muted-foreground" />
      </div>
    </div>

    <div v-show="isExpanded" class="border-t border-border bg-muted/10 p-4 space-y-4">
      <!-- Arguments -->
      <div>
        <div class="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Arguments</div>
        <div class="bg-muted p-3 rounded-md overflow-x-auto">
          <pre class="text-xs font-mono text-foreground">{{ typeof toolCall.arguments === 'string' ? toolCall.arguments : JSON.stringify(toolCall.arguments, null, 2) }}</pre>
        </div>
      </div>

      <!-- Result -->
      <div v-if="toolResult">
        <div class="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Result</div>
        <div class="bg-muted p-3 rounded-md overflow-x-auto" :class="{'border border-destructive/50 bg-destructive/10': toolResult.is_error}">
          <pre class="text-xs font-mono" :class="toolResult.is_error ? 'text-destructive' : 'text-foreground'">{{ toolResult.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
