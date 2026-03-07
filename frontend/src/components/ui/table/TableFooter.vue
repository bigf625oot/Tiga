<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableFooterProps {
  class?: string
}

defineProps<TableFooterProps>()
</script>

<template>
  <tfoot :class="cn('border-t bg-muted/50 font-medium [&>tr]:last:border-b-0', $props.class)">
    <slot />
  </tfoot>
</template>
