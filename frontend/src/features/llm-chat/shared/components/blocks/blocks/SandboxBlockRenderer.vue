<script setup lang="ts">
import { Code, Play, CheckCircle2, XCircle, Loader2 } from 'lucide-vue-next';
import type { SandboxBlock } from '@/features/llm-chat/shared/types';

defineProps<{
  block: SandboxBlock;
}>();
</script>

<template>
  <div class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden my-2">
    <div class="p-3 border-b border-border bg-muted/30 flex items-center justify-between">
      <span class="text-xs font-semibold text-foreground flex items-center gap-2">
        <Code class="w-4 h-4 text-primary" />
        代码沙箱执行
      </span>
      <div class="flex items-center gap-1.5">
        <Loader2 v-if="block.status === 'running'" class="w-3.5 h-3.5 text-primary animate-spin" />
        <CheckCircle2 v-else-if="block.status === 'success'" class="w-3.5 h-3.5 text-green-500" />
        <XCircle v-else-if="block.status === 'error'" class="w-3.5 h-3.5 text-red-500" />
        <Play v-else class="w-3.5 h-3.5 text-muted-foreground" />
        <span class="text-[10px] uppercase font-medium" :class="{
          'text-primary': block.status === 'running',
          'text-green-500': block.status === 'success',
          'text-red-500': block.status === 'error',
          'text-muted-foreground': block.status === 'pending'
        }">
          {{ block.status }}
        </span>
      </div>
    </div>
    <div class="p-3 bg-muted/10">
      <pre class="text-xs font-mono text-foreground/80 overflow-x-auto p-2 bg-background rounded border border-border/50"><code>{{ block.code }}</code></pre>
      
      <div v-if="block.output" class="mt-2 pt-2 border-t border-border/30">
        <span class="text-[10px] text-muted-foreground uppercase font-semibold mb-1 block">Output</span>
        <pre class="text-xs font-mono text-foreground/70 overflow-x-auto whitespace-pre-wrap max-h-32"><code>{{ block.output }}</code></pre>
      </div>
    </div>
  </div>
</template>