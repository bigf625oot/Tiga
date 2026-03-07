<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableHeaderProps {
  class?: string
}

defineProps<TableHeaderProps>()
</script>

<template>
  <thead :class="cn('[&_tr]:border-b', $props.class)">
    <slot />
  </thead>
</template>
