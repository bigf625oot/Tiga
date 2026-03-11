<script setup lang="ts">
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()
</script>

<template>
  <div :class="cn('mt-auto p-4 border-t', props.class)">
    <slot />
  </div>
</template>
