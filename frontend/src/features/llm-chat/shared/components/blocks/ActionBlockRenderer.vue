<script setup lang="ts">
import ActionCard from '../ActionCard.vue';
import type { ActionBlock } from '@/features/llm-chat/shared/types';

defineProps<{
  block: ActionBlock;
}>();

const emit = defineEmits<{
  (e: 'apply-action', path: string): void;
  (e: 'discard-action', path: string): void;
}>();
</script>

<template>
  <ActionCard 
    :block="block" 
    @apply="(path: string) => emit('apply-action', path)"
    @discard="(path: string) => emit('discard-action', path)"
  />
</template>