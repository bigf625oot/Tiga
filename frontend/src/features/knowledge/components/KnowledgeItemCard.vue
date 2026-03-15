<template>
  <Card
    class="group relative overflow-hidden transition-all duration-300 flex flex-col h-full min-h-[190px]"
    :class="selected ? 'border-primary shadow-md bg-primary/5 ring-1 ring-primary' : 'border-muted hover:shadow-lg hover:border-primary/40 bg-gradient-to-br from-card to-muted/10 hover:-translate-y-1'"
    :role="primaryAction ? 'button' : undefined"
    :tabindex="primaryAction ? 0 : undefined"
    @click="handlePrimaryClick"
    @keydown.enter.prevent="handlePrimaryClick"
    @keydown.space.prevent="handlePrimaryClick"
  >
    <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-bl-full -mr-8 -mt-8 transition-opacity opacity-40 group-hover:opacity-80"></div>

    <div class="absolute left-3 top-3 z-20" @click.stop>
      <Checkbox :checked="selected" @update:checked="$emit('toggleSelect')" :disabled="readonly" aria-label="选择" />
    </div>

    <div class="absolute right-2 top-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80">
            <MoreVertical class="h-4 w-4 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem v-if="item?.is_folder" class="cursor-pointer" @click="$emit('openFolder')">
            <Folder class="mr-2 h-4 w-4" /> 打开
          </DropdownMenuItem>
          <DropdownMenuItem v-else-if="canViewGraph" class="cursor-pointer" @click="$emit('viewGraph')">
            <Share2 class="mr-2 h-4 w-4" /> 查看图谱
          </DropdownMenuItem>
          <DropdownMenuSeparator v-if="!readonly" />
          <DropdownMenuItem v-if="!readonly" class="cursor-pointer" @click="$emit('move')">
            <FolderInput class="mr-2 h-4 w-4" /> 移动
          </DropdownMenuItem>
          <DropdownMenuItem v-if="!readonly" class="text-destructive focus:text-destructive cursor-pointer" @click="$emit('delete')">
            <Trash2 class="mr-2 h-4 w-4" /> 删除
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>

    <CardHeader class="p-5 pb-3 space-y-0 relative z-10">
      <div class="flex items-start gap-4 w-full overflow-hidden">
        <div class="h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden">
          <Folder v-if="item?.is_folder" class="h-9 w-9 text-blue-600" />
          <img v-else :src="iconSrc" class="h-9 w-9 object-contain opacity-80" alt="icon" />
        </div>

        <div class="space-y-1.5 flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <CardTitle class="text-base font-bold leading-tight tracking-tight truncate" :title="item?.filename">
              {{ item?.filename }}
            </CardTitle>
          </div>

          <div class="flex items-center gap-2">
            <Badge v-if="item?.is_folder" variant="outline" class="text-[10px] font-medium px-1.5 py-0 h-5 rounded-md bg-muted/30 text-muted-foreground border-border/60">
              文件夹
            </Badge>
            <Badge
              v-else
              variant="outline"
              class="text-[10px] font-medium px-1.5 py-0 h-5 rounded-md"
              :class="statusBadgeClass"
            >
              {{ item?.status_text || '未知' }}
            </Badge>
            <span v-if="!item?.is_folder && item?.id" class="text-[10px] text-muted-foreground/60 font-mono truncate max-w-[120px]">
              ID: {{ String(item.id).slice(0, 10) }}
            </span>
          </div>
        </div>
      </div>
    </CardHeader>

    <CardContent class="p-5 pt-2 pb-4 min-h-[5rem] relative z-10">
      <div v-if="!item?.is_folder && showProgress" class="w-full">
        <div class="flex justify-between items-center mb-1.5">
          <span class="text-[10px] text-primary font-medium">{{ item?.status_text }}</span>
          <span class="text-[10px] text-muted-foreground">{{ item?.progress || 0 }}%</span>
        </div>
        <Progress :model-value="item?.progress || 0" class="h-1.5" />
      </div>

      <div v-else class="grid grid-cols-2 gap-3 text-xs">
        <div class="text-muted-foreground">
          <div class="text-[10px] uppercase tracking-wide text-muted-foreground/60">大小</div>
          <div class="font-mono text-foreground/80 truncate">{{ item?.is_folder ? '-' : sizeText }}</div>
        </div>
        <div class="text-muted-foreground">
          <div class="text-[10px] uppercase tracking-wide text-muted-foreground/60">创建</div>
          <div class="text-foreground/80 truncate">{{ item?.is_folder ? '-' : createdAtText }}</div>
        </div>
      </div>
    </CardContent>

    <CardFooter class="p-5 pt-0 flex items-center justify-between mt-auto border-t border-border/30 pt-3 relative z-10">
      <Button
        v-if="item?.is_folder"
        variant="outline"
        size="sm"
        class="h-8 px-3 text-xs"
        @click="$emit('openFolder')"
      >
        打开
      </Button>
      <Button
        v-else-if="canViewGraph"
        variant="outline"
        size="sm"
        class="h-8 px-3 text-xs"
        @click="$emit('viewGraph')"
      >
        <Share2 class="w-3.5 h-3.5 mr-2" />
        查看图谱
      </Button>
      <span v-else class="text-[10px] text-muted-foreground/60">—</span>

      <span class="text-[10px] text-muted-foreground/40 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
        {{ footerHint }}
      </span>
    </CardFooter>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { Folder, MoreVertical, Share2, Trash2, FolderInput } from 'lucide-vue-next'

const props = defineProps({
  item: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  iconSrc: { type: String, default: '' },
  sizeText: { type: String, default: '-' },
  createdAtText: { type: String, default: '-' }
})

const emit = defineEmits(['toggleSelect', 'openFolder', 'viewGraph', 'move', 'delete'])

const showProgress = computed(() => ['上传中', '解析中'].includes(props.item?.status_text))
const canViewGraph = computed(() => !props.item?.is_folder && props.item?.status_text === '已完成')
const primaryAction = computed(() => !!props.item?.is_folder || canViewGraph.value)

const handlePrimaryClick = () => {
  if (!primaryAction.value) return
  if (props.item?.is_folder) {
    return emit('openFolder')
  }
  if (canViewGraph.value) return emit('viewGraph')
}

const statusBadgeClass = computed(() => {
  const status = props.item?.status_text
  if (status === '已完成') return 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-900'
  if (status === '失败') return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900'
  return 'bg-muted text-muted-foreground border-border'
})

const footerHint = computed(() => {
  if (props.item?.is_folder) return 'Folder'
  if (props.item?.status_text) return props.item.status_text
  return '—'
})
</script>
