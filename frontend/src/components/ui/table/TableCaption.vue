<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableCaptionProps {
  class?: string
}

defineProps<TableCaptionProps>()
</script>

<template>
  <caption :class="cn('mt-4 text-sm text-muted-foreground', $props.class)">
    <slot />
  </caption>
</template>
