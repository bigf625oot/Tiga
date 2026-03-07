<script setup lang="ts">
import { cn } from '@/lib/utils'

interface TableProps {
  class?: string
}

defineProps<TableProps>()
</script>

<template>
  <div class="relative w-full overflow-auto">
    <table :class="cn('w-full caption-bottom text-sm', $props.class)">
      <slot />
    </table>
  </div>
</template>
