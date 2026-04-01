<template>
  <Card
    class="group relative flex flex-col h-full min-h-[200px] overflow-hidden transition-all duration-200"
    :class="[
      selected ? 'border-primary ring-1 ring-primary shadow-sm bg-primary/5' : 'border-border hover:border-primary/50 hover:shadow-md bg-card',
      'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
    ]"
    role="button"
    tabindex="0"
    aria-label="编辑数据流"
    @click="$emit('edit')"
    @keydown.enter.prevent="$emit('edit')"
    @keydown.space.prevent="$emit('edit')"
  >
    <!-- 头部：包含复选框、状态标签和操作菜单 -->
    <div class="flex items-center justify-between p-4 pb-2 relative z-10">
      <div class="flex items-center gap-3" @click.stop>
        <Checkbox 
          :checked="selected" 
          @update:checked="$emit('toggleSelect')" 
          aria-label="选择数据流" 
          class="transition-colors"
        />
        <Badge :variant="statusBadgeVariant" class="px-2 py-0.5 text-xs font-medium flex items-center gap-1.5">
          <span class="relative flex h-2 w-2" v-if="isRunning">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-current"></span>
          </span>
          <span class="relative flex h-2 w-2 rounded-full bg-current opacity-70" v-else></span>
          {{ statusLabel }}
        </Badge>
      </div>

      <!-- 操作菜单 -->
      <div class="flex items-center" @click.stop>
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground opacity-60 group-hover:opacity-100 transition-opacity">
              <MoreVertical class="h-4 w-4" />
              <span class="sr-only">打开菜单</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-40">
            <DropdownMenuItem @click="$emit('edit')">
              <Pencil class="mr-2 h-4 w-4" />
              <span>编辑</span>
            </DropdownMenuItem>
            <DropdownMenuItem @click="$emit('duplicate')">
              <Copy class="mr-2 h-4 w-4" />
              <span>复制</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem class="text-destructive focus:text-destructive focus:bg-destructive/10" @click="$emit('delete')">
              <Trash2 class="mr-2 h-4 w-4" />
              <span>删除</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="px-4 py-2 flex-1 flex flex-col gap-2 relative z-10">
      <div class="flex items-start gap-3">
        <div 
          class="h-10 w-10 rounded-lg flex items-center justify-center shrink-0 shadow-sm"
          :class="statusColorClass"
        >
          <Workflow class="h-5 w-5 text-white/90" v-if="!initial || initial === '—'" />
          <span v-else class="text-white font-semibold text-sm">{{ initial }}</span>
        </div>
        <div class="space-y-1 min-w-0 flex-1">
          <TooltipProvider :delay-duration="300">
            <Tooltip>
              <TooltipTrigger as-child>
                <h3 class="font-semibold text-base leading-tight truncate text-foreground group-hover:text-primary transition-colors">
                  {{ pipeline?.name || '未命名数据流' }}
                </h3>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p>{{ pipeline?.name || '未命名数据流' }}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <p class="text-xs text-muted-foreground font-mono truncate">
            ID: {{ String(pipeline?.id || '—') }}
          </p>
        </div>
      </div>

      <!-- 统计信息网格 -->
      <div class="grid grid-cols-2 gap-4 mt-4 bg-muted/30 rounded-lg p-3 border border-border/50">
        <div class="space-y-1">
          <div class="flex items-center text-xs text-muted-foreground gap-1">
            <Clock class="h-3 w-3" />
            <span>最近运行</span>
          </div>
          <div class="text-sm font-medium text-foreground/90 truncate" :title="lastRunText">
            {{ lastRunText }}
          </div>
        </div>
        <div class="space-y-1">
          <div class="flex items-center text-xs text-muted-foreground gap-1">
            <Calendar class="h-3 w-3" />
            <span>创建时间</span>
          </div>
          <div class="text-sm font-medium text-foreground/90 truncate" :title="createdAtText">
            {{ createdAtText }}
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="px-4 py-3 mt-auto border-t border-border/40 bg-muted/10 flex items-center justify-between relative z-10">
      <div class="flex items-center" @click.stop>
        <TooltipProvider :delay-duration="200">
          <Tooltip>
            <TooltipTrigger as-child>
              <Button 
                :variant="isRunning ? 'secondary' : 'default'" 
                size="sm" 
                class="h-8 gap-1.5 shadow-sm" 
                :class="isRunning ? 'bg-amber-500/10 text-amber-600 hover:bg-amber-500/20 border-amber-500/20' : 'bg-primary text-primary-foreground hover:bg-primary/90'"
                @click="$emit('toggleStatus')"
              >
                <Pause v-if="isRunning" class="h-3.5 w-3.5" />
                <Play v-else class="h-3.5 w-3.5" />
                <span class="text-xs">{{ isRunning ? '暂停运行' : '启动数据流' }}</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{{ isRunning ? '暂停当前数据流' : '立即启动数据流' }}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      
      <span class="text-xs text-muted-foreground/60 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
        {{ sortHint }}
      </span>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { 
  MoreVertical, 
  Pencil, 
  Copy, 
  Trash2, 
  Play, 
  Pause,
  Workflow,
  Clock,
  Calendar
} from 'lucide-vue-next'

const props = defineProps({
  pipeline: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  statusLabel: { type: String, default: '' },
  statusBadgeVariant: { type: String as PropType<"default" | "destructive" | "outline" | "secondary" | null | undefined>, default: 'outline' },
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
