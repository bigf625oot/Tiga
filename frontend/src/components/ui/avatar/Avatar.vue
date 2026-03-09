<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { AvatarRoot, type AvatarRootProps } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<AvatarRootProps & { class?: HTMLAttributes['class'] }>(), {
  shape: 'circle',
})

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props
  return delegated
})
</script>

<template>
  <AvatarRoot
    v-bind="delegatedProps"
    :class="cn('relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full', props.class)"
  >
    <slot />
  </AvatarRoot>
</template>
