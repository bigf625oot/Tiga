<script setup lang="ts">
import MarkdownRenderer from '@/features/qa/components/SmartQA/common/MarkdownRenderer.vue';
import type { TextBlock } from '../../types';

defineProps<{
  block: TextBlock;
  messageBlocks: any[];
}>();

const emit = defineEmits<{
  (e: 'locate-node', ref: any): void;
  (e: 'open-doc-space', id: string): void;
}>();
</script>

<template>
  <MarkdownRenderer 
      :content="block.content" 
      @citation-click="(idx: number) => emit('locate-node', messageBlocks.find(b => b.type === 'references')?.sources?.[idx - 1])" 
      @open-doc-space="(id: string) => emit('open-doc-space', id)"
  />
</template>