<script setup lang="ts">
import SoloTaskCard from '../../../workflow/components/SmartQA/SoloTaskCard.vue';
import type { SoloLayoutBlock } from '../../types';

defineProps<{
  block: SoloLayoutBlock;
}>();

const emit = defineEmits<{
  (e: 'locate-node', ref: any): void;
  (e: 'resend-message'): void;
}>();
</script>

<template>
  <SoloTaskCard 
      :message="block.original_message"
      :is-last="block.is_last"
      :is-streaming="block.is_streaming"
      @locate-node="(ref: any) => emit('locate-node', ref)"
      @resend-message="emit('resend-message')"
  />
</template>