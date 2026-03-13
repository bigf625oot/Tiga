<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import {
  HoverCardRoot,
  type HoverCardRootEmits,
  type HoverCardRootProps,
  useForwardPropsEmits,
} from 'radix-vue'

const props = withDefaults(defineProps<HoverCardRootProps>(), {
  openDelay: 700,
})

const emits = defineEmits<HoverCardRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <HoverCardRoot v-bind="forwarded">
    <slot />
  </HoverCardRoot>
</template>
