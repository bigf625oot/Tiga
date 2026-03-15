<template>
  <Card
    class="group relative overflow-hidden transition-all duration-300 cursor-pointer flex flex-col h-full min-h-[190px]"
    :class="selected ? 'border-primary shadow-md bg-primary/5 ring-1 ring-primary' : 'border-muted hover:shadow-lg hover:border-primary/40 bg-gradient-to-br from-card to-muted/10 hover:-translate-y-1'"
    role="button"
    tabindex="0"
    @click="$emit('edit')"
    @keydown.enter.prevent="$emit('edit')"
    @keydown.space.prevent="$emit('edit')"
  >
    <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-bl-full -mr-8 -mt-8 transition-opacity opacity-40 group-hover:opacity-80"></div>

    <div class="absolute left-3 top-3 z-20" @click.stop>
      <Checkbox :checked="selected" @update:checked="$emit('toggleSelect')" aria-label="选择" />
    </div>

    <div class="absolute right-2 top-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80">
            <MoreVertical class="h-4 w-4 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem class="cursor-pointer" @click="$emit('edit')">
            <Pencil class="mr-2 h-4 w-4" /> 编辑
          </DropdownMenuItem>
          <DropdownMenuItem class="cursor-pointer" @click="$emit('duplicate')">
            <Copy class="mr-2 h-4 w-4" /> 复制
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem class="text-destructive focus:text-destructive cursor-pointer" @click="$emit('delete')">
            <Trash2 class="mr-2 h-4 w-4" /> 删除
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>

    <CardHeader class="p-5 pb-3 space-y-0 relative z-10">
      <div class="flex items-start gap-4 w-full overflow-hidden">
        <div class="h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden shadow-sm text-white font-semibold text-sm" :class="statusColorClass">
          {{ initial }}
        </div>
        <div class="space-y-1.5 flex-1 min-w-0">
          <CardTitle class="text-base font-bold leading-tight tracking-tight truncate" :title="pipeline?.name">
            {{ pipeline?.name }}
          </CardTitle>
          <div class="flex items-center gap-2">
            <Badge :variant="statusBadgeVariant" class="capitalize text-[10px] font-medium px-1.5 py-0 h-5 rounded-md">
              {{ statusLabel }}
            </Badge>
            <span class="text-[10px] text-muted-foreground/60 font-mono truncate max-w-[160px]">
              ID: {{ String(pipeline?.id) }}
            </span>
          </div>
        </div>
      </div>
    </CardHeader>

    <CardContent class="p-5 pt-2 pb-4 min-h-[5rem] relative z-10">
      <div class="grid grid-cols-2 gap-3 text-xs">
        <div class="text-muted-foreground">
          <div class="text-[10px] uppercase tracking-wide text-muted-foreground/60">最近运行</div>
          <div class="text-foreground/80 truncate">{{ lastRunText }}</div>
        </div>
        <div class="text-muted-foreground">
          <div class="text-[10px] uppercase tracking-wide text-muted-foreground/60">创建时间</div>
          <div class="text-foreground/80 truncate">{{ createdAtText }}</div>
        </div>
      </div>
    </CardContent>

    <CardFooter class="p-5 pt-0 flex items-center justify-between mt-auto border-t border-border/30 pt-3 relative z-10">
      <Button variant="ghost" size="icon" class="h-8 w-8" :title="isRunning ? '暂停' : '启动'" @click.stop="$emit('toggleStatus')">
        <Pause v-if="isRunning" class="h-4 w-4 text-amber-500" />
        <Play v-else class="h-4 w-4 text-green-500" />
      </Button>
      <span class="text-[10px] text-muted-foreground/40 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
        {{ sortHint }}
      </span>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { MoreVertical, Pencil, Copy, Trash2, Play, Pause } from 'lucide-vue-next'

const props = defineProps({
  pipeline: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  statusLabel: { type: String, default: '' },
  statusBadgeVariant: { type: String, default: 'outline' },
  statusColorClass: { type: String, default: 'bg-muted' },
  lastRunText: { type: String, default: '-' },
  createdAtText: { type: String, default: '-' },
  isRunning: { type: Boolean, default: false },
  sortHint: { type: String, default: '' }
})

defineEmits(['toggleSelect', 'edit', 'toggleStatus', 'duplicate', 'delete'])

const initial = computed(() => {
  const name = (props.pipeline as any)?.name || ''
  return name ? String(name).substring(0, 1).toUpperCase() : '—'
})
</script>
