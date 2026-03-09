<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { AvatarImage, type AvatarImageProps } from 'radix-vue'

const props = defineProps<AvatarImageProps & { class?: HTMLAttributes['class'] }>()

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props
  return delegated
})
</script>

<template>
  <AvatarImage
    v-bind="delegatedProps"
    :class="props.class"
    class="h-full w-full object-cover"
  />
</template>
