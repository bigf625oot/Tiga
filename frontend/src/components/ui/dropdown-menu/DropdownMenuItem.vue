<script setup lang="ts">
import { DropdownMenuItem, type DropdownMenuItemEmits, type DropdownMenuItemProps } from 'radix-vue'
import { computed, useAttrs, type HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<DropdownMenuItemProps & { class?: HTMLAttributes['class']; inset?: boolean }>()
const emit = defineEmits<DropdownMenuItemEmits>()
const attrs = useAttrs()

const delegatedProps = computed(() => {
  const { class: _, inset: __, ...delegated } = props
  return delegated
})

const handleSelect = (event: Event) => {
  emit('select', event)

  const onClick = (attrs as any).onClick
  if (typeof onClick === 'function') onClick(event)
  else if (Array.isArray(onClick)) onClick.forEach((fn) => fn?.(event))
}
</script>

<template>
  <DropdownMenuItem
    v-bind="delegatedProps"
    @select="handleSelect"
    :class="
      cn(
        'relative flex cursor-default select-none items-center rounded-md px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        inset && 'pl-8',
        props.class,
      )
    "
  >
    <slot />
  </DropdownMenuItem>
</template>
