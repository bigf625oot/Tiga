<script setup lang="ts">
import GenericResourceCard from '../../message/GenericResourceCard.vue';
import type { ResourceBlock } from '@/features/llm-chat/shared/types';

defineProps<{
  block: ResourceBlock;
}>();

const emit = defineEmits<{
  (e: 'open-doc-space', id: string): void;
}>();
</script>

<template>
  <GenericResourceCard 
      :type="block.resource_type"
      :id="block.data.id"
      :title="block.data.title || block.data.name || 'Unknown Resource'"
      :meta="block.data.size"
      @click="(id: string) => emit('open-doc-space', id)"
  />
</template>
