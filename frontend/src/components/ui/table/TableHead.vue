<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableHeadProps {
  class?: string
}

defineProps<TableHeadProps>()
</script>

<template>
  <th :class="cn('h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0', $props.class)">
    <slot />
  </th>
</template>
