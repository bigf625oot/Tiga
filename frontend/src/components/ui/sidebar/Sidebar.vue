<script setup lang="ts">
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
  collapsed?: boolean
}>()
</script>

<template>
  <aside 
    :class="cn(
      'flex flex-col border-r bg-card transition-all duration-300 relative z-20',
      props.collapsed ? 'w-[72px]' : 'w-[280px]',
      props.class
    )"
  >
    <slot />
  </aside>
</template>
