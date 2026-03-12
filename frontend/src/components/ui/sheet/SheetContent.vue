<script setup lang="ts">
import { DialogPortal, DialogOverlay, DialogContent, type DialogContentEmits, type DialogContentProps, useForwardPropsEmits, DialogClose } from 'radix-vue'
import { X } from 'lucide-vue-next'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { ref } from 'vue'

interface SheetContentProps extends DialogContentProps {
  side?: 'top' | 'bottom' | 'left' | 'right'
  class?: string
  overlay?: boolean
  resizable?: boolean
  defaultWidth?: number
}

const props = withDefaults(defineProps<SheetContentProps>(), {
  side: 'right',
  overlay: true,
  resizable: false,
  defaultWidth: 600
})

const emits = defineEmits<DialogContentEmits>()
const forwarded = useForwardPropsEmits(props, emits)

const sheetVariants = cva(
  'fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:duration-300 data-[state=open]:duration-500',
  {
    variants: {
      side: {
        top: 'inset-x-0 top-0 border-b data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top',
        bottom:
          'inset-x-0 bottom-0 border-t data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom',
        left: 'inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm',
        right:
          'inset-y-0 right-0 h-full w-3/4 border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-sm',
      },
    },
    defaultVariants: {
      side: 'right',
    },
  },
)

// Resize Logic
const width = ref(props.defaultWidth)
const isResizing = ref(false)

const startResize = (e: MouseEvent) => {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'ew-resize'
}

const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return
  
  if (props.side === 'right') {
    width.value = Math.max(300, Math.min(window.innerWidth - 50, window.innerWidth - e.clientX))
  } else if (props.side === 'left') {
    width.value = Math.max(300, Math.min(window.innerWidth - 50, e.clientX))
  }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}
</script>

<template>
  <DialogPortal>
    <DialogOverlay
      v-if="overlay"
      class="fixed inset-0 z-50 bg-black/80  data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
    />
    <DialogContent
      v-bind="forwarded"
      :class="cn(sheetVariants({ side }), props.class)"
      :style="resizable ? { width: width + 'px', maxWidth: '100vw' } : {}"
    >
      <div 
        v-if="resizable && (side === 'left' || side === 'right')"
        class="absolute top-0 bottom-0 w-1.5 cursor-ew-resize hover:bg-primary/20 active:bg-primary/40 transition-colors z-[60]"
        :class="side === 'right' ? 'left-0' : 'right-0'"
        @mousedown="startResize"
      />
      
      <slot />

      <DialogClose
        class="absolute right-4 top-4 rounded-md opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-secondary"
      >
        <X class="h-4 w-4" />
        <span class="sr-only">Close</span>
      </DialogClose>
    </DialogContent>
  </DialogPortal>
</template>
