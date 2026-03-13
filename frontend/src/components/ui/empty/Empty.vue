<script setup lang="ts">
import { type HTMLAttributes, type Component, computed } from 'vue'
import { cn } from '@/lib/utils'
import { Inbox } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  class?: HTMLAttributes['class']
  image?: Component
  title?: string
  description?: string
  imageClass?: HTMLAttributes['class']
}>(), {
  title: '暂无数据',
  description: '这里什么都没有',
})

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props
  return delegated
})
</script>

<template>
  <div :class="cn('flex h-full min-h-[350px] flex-col items-center justify-center space-y-1 p-8 text-center animate-in fade-in-50', props.class)">
    <div class="flex items-center justify-center mb-4 text-muted-foreground/20">
      <slot name="image">
        <component :is="image" v-if="image" :class="cn('h-16 w-16', imageClass)" />
        <Inbox v-else :class="cn('h-16 w-16', imageClass)" />
      </slot>
    </div>
    <h3 v-if="title" class="text-lg font-medium tracking-tight text-foreground">
      {{ title }}
    </h3>
    <p v-if="description" class="text-sm text-muted-foreground max-w-sm mx-auto mt-2">
      {{ description }}
    </p>
    <div v-if="$slots.default" class="mt-6">
      <slot />
    </div>
  </div>
</template>
