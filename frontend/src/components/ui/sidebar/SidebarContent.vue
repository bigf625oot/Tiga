<script setup lang="ts">
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()
</script>

<template>
  <div :class="cn('flex-1 overflow-auto custom-scrollbar', props.class)">
    <slot />
  </div>
</template>
