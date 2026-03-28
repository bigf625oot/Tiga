<script setup lang="ts">
import { Globe, Database, Network, FileText, Link2 } from 'lucide-vue-next';
import type { ReferencesBlock } from '../../types';

const props = defineProps<{
  block: ReferencesBlock;
}>();

const emit = defineEmits<{
  (e: 'locate-node', ref: any): void;
}>();

const getSourceType = (ref: any) => {
  if (ref.url) return 'web';
  if (ref.source === 'graph') return 'graph';
  if (ref.source === 'vector' || ref.source === 'kb') return 'kb';
  return 'unknown';
};

const getSourceIcon = (ref: any) => {
  const type = getSourceType(ref);
  if (type === 'web') return Globe;
  if (type === 'graph') return Network;
  if (type === 'kb') return Database;
  return FileText;
};

const getSourceDomain = (ref: any) => {
  if (ref.url) {
    try {
      const url = new URL(ref.url);
      return url.hostname.replace(/^www\./, '');
    } catch {
      return 'Web Link';
    }
  }
  if (ref.source === 'graph') return '知识图谱';
  if (ref.source === 'vector' || ref.source === 'kb') return '知识库';
  return ref.source || '未知来源';
};

const handleClick = (ref: any) => {
  if (ref.url) {
    window.open(ref.url, '_blank');
  } else {
    emit('locate-node', ref);
  }
};
</script>

<template>
  <div class="mt-4 pt-4 border-t border-border/40 w-full overflow-hidden">
      <div class="flex items-center gap-2 mb-3">
          <Link2 class="w-4 h-4 text-muted-foreground/70" />
          <span class="text-xs font-semibold text-foreground/80 tracking-wide">信息与知识来源</span>
      </div>
      
      <!-- Horizontal Scrollable Cards -->
      <div class="flex overflow-x-auto gap-3 pb-3 -mx-1 px-1 custom-scrollbar w-full" style="scroll-snap-type: x mandatory;">
          <div 
              v-for="(ref, idx) in block.sources" 
              :key="idx"
              class="flex-shrink-0 w-[220px] bg-card border border-border/60 hover:border-primary/40 hover:bg-muted/30 rounded-xl p-3 flex flex-col justify-between cursor-pointer transition-all duration-300 shadow-sm hover:shadow group relative"
              style="scroll-snap-align: start;"
              @click="handleClick(ref)"
              :title="ref.title || '未知数据源'"
          >
              <div class="flex items-start gap-2.5 overflow-hidden mb-2">
                 <div class="mt-0.5 flex-shrink-0 w-6 h-6 bg-muted rounded flex items-center justify-center border border-border/50 overflow-hidden">
                   <img v-if="ref.favicon" :src="ref.favicon" class="w-3.5 h-3.5" />
                   <component v-else :is="getSourceIcon(ref)" class="w-3.5 h-3.5 text-muted-foreground" />
                 </div>
                 <div class="flex-1 min-w-0">
                    <div class="text-xs font-medium text-foreground line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                        {{ ref.title || '未知数据源' }}
                    </div>
                 </div>
              </div>
              <div class="flex items-center gap-1.5 mt-auto pt-2 border-t border-border/30">
                 <span class="flex items-center justify-center bg-primary/10 text-primary text-[9px] font-mono rounded w-4 h-4">{{ Number(idx) + 1 }}</span>
                 <span class="text-[10px] text-muted-foreground truncate">{{ getSourceDomain(ref) }}</span>
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