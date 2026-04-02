<script setup lang="ts">
import type { ImageBlock } from '@/features/llm-chat/shared/types';

const props = defineProps<{
  block: ImageBlock;
}>();

const getImageUrl = (block: ImageBlock): string => {
  if (block.source_type === 'base64' && block.base64) {
    return block.base64;
  }
  if (block.url) {
    if (!block.url.startsWith('http') && !block.url.startsWith('/') && !block.url.startsWith('data:')) {
      if (block.url.endsWith('.png') || block.url.endsWith('.jpg') || block.url.endsWith('.jpeg')) {
        return `/uploads/${block.url}`;
      }
    }
    return block.url;
  }
  return '';
};

const openImage = (url: string) => {
  if (url && typeof window !== 'undefined') {
    window.open(url, '_blank');
  }
};
</script>

<template>
  <div class="user-image-block my-2">
    <img
      :src="getImageUrl(block)"
      :alt="block.alt || 'image'"
      class="max-w-full h-auto rounded-lg shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
      @click="openImage(getImageUrl(block))"
    />
  </div>
</template>
