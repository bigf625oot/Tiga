<script setup lang="ts">
import { Link2 } from 'lucide-vue-next';
import type { ReferencesBlock } from '@/features/llm-chat/shared/types';
import SourceCard from '@/features/llm-chat/shared/components/common/SourceCard.vue';

const props = defineProps<{
  block: ReferencesBlock;
}>();

const emit = defineEmits<{
  (e: 'locate-node', ref: any): void;
}>();

const handleSourceClick = (source: any) => {
  if (source.url) {
    window.open(source.url, '_blank', 'noopener,noreferrer');
  } else {
    emit('locate-node', source);
  }
};

const getSourceType = (ref: any): 'web' | 'doc' | 'file' => {
  if (ref.url) return 'web';
  if (ref.source === 'graph') return 'doc';
  if (ref.source === 'vector' || ref.source === 'kb') return 'doc';
  return 'doc';
};
</script>

<template>
  <div class="mt-4 pt-4 border-t border-border/40 w-full overflow-hidden">
    <div class="flex items-center gap-2 mb-3">
      <Link2 class="w-4 h-4 text-muted-foreground/70" />
      <span class="text-xs font-semibold text-foreground/80 tracking-wide">信息与知识来源</span>
    </div>

    <div role="list" class="flex flex-col gap-2">
      <SourceCard
        v-for="(ref, idx) in block.sources"
        :key="idx"
        :source="{
          url: ref.url,
          title: ref.title || '未知数据源',
          favicon: ref.favicon,
        }"
        :type="getSourceType(ref)"
        show-meta
        role="listitem"
        @click="handleSourceClick(ref)"
      >
        <template #action>
          <span class="flex items-center justify-center bg-primary/10 text-primary text-[10px] font-mono rounded w-5 h-5">
            {{ Number(idx) + 1 }}
          </span>
        </template>
      </SourceCard>
    </div>
  </div>
</template>
