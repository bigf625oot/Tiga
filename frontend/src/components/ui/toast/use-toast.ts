import { ref } from 'vue'

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

type ToasterToast = {
  id: string
  title?: string
  description?: string
  action?: any
  variant?: 'default' | 'destructive'
  open?: boolean
}

const toasts = ref<ToasterToast[]>([])

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_VALUE
  return count.toString()
}

function addToast(toast: Omit<ToasterToast, 'id'>) {
  const id = genId()

  const update = (props: ToasterToast) => {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      toasts.value[index] = { ...toasts.value[index], ...props }
    }
  }

  const dismiss = () => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  const newToast = {
    ...toast,
    id,
    open: true,
    onOpenChange: (open: boolean) => {
      if (!open) dismiss()
    },
  }

  toasts.value = [newToast, ...toasts.value].slice(0, TOAST_LIMIT)

  return {
    id,
    dismiss,
    update,
  }
}

function useToast() {
  return {
    toasts,
    toast: addToast,
    dismiss: (id?: string) => {
      if (id) {
        toasts.value = toasts.value.filter((t) => t.id !== id)
      } else {
        toasts.value = []
      }
    },
  }
}

export { useToast, toasts }
