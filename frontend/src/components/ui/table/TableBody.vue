<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableBodyProps {
  class?: string
}

defineProps<TableBodyProps>()
</script>

<template>
  <tbody :class="cn('[&_tr:last-child]:border-0', $props.class)">
    <slot />
  </tbody>
</template>
