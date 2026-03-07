<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableCellProps {
  class?: string
}

defineProps<TableCellProps>()
</script>

<template>
  <td :class="cn('p-4 align-middle [&:has([role=checkbox])]:pr-0', $props.class)">
    <slot />
  </td>
</template>
