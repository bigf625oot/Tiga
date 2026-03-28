<script setup lang="ts">
import ErrorCallout from '@/features/qa/components/SmartQA/common/ErrorCallout.vue';
import type { ErrorBlock } from '../../types';

defineProps<{
  block: ErrorBlock;
}>();

const emit = defineEmits<{
  (e: 'resend-message'): void;
}>();
</script>

<template>
  <ErrorCallout 
      :message="block.message" 
      :can-retry="block.can_retry"
      @retry="emit('resend-message')"
  />
</template>