<template>
  <span 
    class="citation-link cursor-pointer text-indigo-600 dark:text-indigo-400 hover:underline font-medium mx-0.5" 
    @click="$emit('click', index)"
  >
    [{{ index }}]
  </span>
</template>

<script setup lang="ts">
defineProps<{
  index: number | string;
}>();

defineEmits<{
  (e: 'click', index: number | string): void;
}>();
</script>