<script setup lang="ts">
import { ref } from 'vue';
import { Database, Search, Loader2, FileText, ChevronDown, ChevronRight, ExternalLink } from 'lucide-vue-next';
import type { KbRetrievalBlock } from '../../types';

const props = defineProps<{
  block: KbRetrievalBlock;
}>();

const isExpanded = ref(true);
</script>

<template>
  <div class="inline-flex flex-col transition-all duration-300 w-full my-1">
    <div 
      class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/50 hover:bg-muted/50 cursor-pointer transition-colors shadow-sm w-fit"
      @click="isExpanded = !isExpanded"
    >
      <Loader2 v-if="block.status === 'searching'" class="w-3.5 h-3.5 text-primary animate-spin" />
      <Database v-else class="w-3.5 h-3.5 text-muted-foreground" />
      
      <span class="text-xs font-medium text-foreground/80">
        分析了 {{ block.results?.length || 0 }} 个知识片段
      </span>
      
      <ChevronDown v-if="isExpanded" class="w-3.5 h-3.5 text-muted-foreground ml-1" />
      <ChevronRight v-else class="w-3.5 h-3.5 text-muted-foreground ml-1" />
    </div>

    <!-- Expanded Cards Layout -->
    <div v-show="isExpanded && block.results?.length > 0" class="mt-3 flex overflow-x-auto gap-3 pb-3 -mx-1 px-1 custom-scrollbar w-full" style="scroll-snap-type: x mandatory;">
      <div 
        v-for="(result, idx) in block.results" 
        :key="idx" 
        class="flex-shrink-0 w-[220px] bg-card border border-border/60 hover:border-primary/40 hover:bg-muted/30 rounded-xl p-3 flex flex-col justify-between cursor-pointer transition-all duration-300 shadow-sm hover:shadow group relative"
        style="scroll-snap-align: start;"
        :title="result.title || `Document ${idx + 1}`"
      >
        <div class="flex items-start gap-2.5 overflow-hidden mb-2">
           <div class="mt-0.5 flex-shrink-0 w-6 h-6 bg-muted rounded flex items-center justify-center border border-border/50 overflow-hidden">
             <FileText class="w-3.5 h-3.5 text-muted-foreground" />
           </div>
           <div class="flex-1 min-w-0">
              <div class="text-xs font-medium text-foreground line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                  {{ result.title || `Document ${idx + 1}` }}
              </div>
           </div>
        </div>
        <div class="flex items-center justify-between mt-auto pt-2 border-t border-border/30">
           <span class="text-[10px] text-muted-foreground truncate max-w-[150px]">{{ result.source || '知识库' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  height: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
</style>