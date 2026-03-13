<template>
  <div 
    class="flex flex-col h-full bg-background border-r border-border transition-all duration-300 ease-in-out relative group"
    :class="[isOpen ? 'w-96 translate-x-0' : 'w-0 -translate-x-full overflow-hidden border-r-0']"
  >
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-border/40 min-w-[384px]">
      <div class="flex items-center gap-2">
        <h3 class="font-semibold text-sm">文件</h3>
        <Badge variant="secondary" class="text-xs px-1.5 h-5">{{ attachments.length }}</Badge>
      </div>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground" @click="$emit('toggle')">
              <ChevronsLeft class="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>收起侧边栏</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>

    <!-- Toolbar -->
    <div class="p-4 flex flex-col gap-4 min-w-[384px]">
      <!-- Search -->
      <div class="relative">
        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input 
          v-model="searchQuery" 
          placeholder="搜索文件..." 
          class="h-9 pl-9 text-sm bg-muted/30 focus-visible:bg-background"
        />
      </div>
      
      <!-- Actions Row -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
            <!-- Filter Menu -->
            <DropdownMenu>
                <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8">
                        <Filter class="w-4 h-4 text-muted-foreground" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                    <DropdownMenuItem>全部文件</DropdownMenuItem>
                    <DropdownMenuItem>文档</DropdownMenuItem>
                    <DropdownMenuItem>图片</DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <!-- Sort Menu -->
            <DropdownMenu>
                <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8">
                        <ArrowUpDown class="w-4 h-4 text-muted-foreground" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                    <DropdownMenuItem>按时间排序</DropdownMenuItem>
                    <DropdownMenuItem>按名称排序</DropdownMenuItem>
                    <DropdownMenuItem>按大小排序</DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
        
        <Button size="sm" variant="outline" class="h-8 text-xs gap-1.5 border-dashed" @click="$emit('add-files')">
          <Plus class="w-3.5 h-3.5" />
          添加文件
        </Button>
      </div>
      
      <!-- Active Filters (Mock) -->
      <div class="flex flex-wrap gap-2">
         <DropdownMenu>
            <DropdownMenuTrigger as-child>
                <Badge variant="outline" class="cursor-pointer hover:bg-muted/80 transition-colors gap-1 pr-1 pl-2 py-0.5 h-6 font-normal">
                    来源: {{ currentFilterLabel }}
                    <ChevronDown class="h-3 w-3 ml-1 opacity-50" />
                </Badge>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
                <DropdownMenuItem @click="currentFilter = 'all'">全部</DropdownMenuItem>
                <DropdownMenuItem @click="currentFilter = 'local'">本地上传</DropdownMenuItem>
                <DropdownMenuItem @click="currentFilter = 'knowledge'">知识库</DropdownMenuItem>
            </DropdownMenuContent>
         </DropdownMenu>
      </div>
    </div>

    <Separator />

    <!-- Empty State -->
    <div v-if="filteredAttachments.length === 0" class="flex-1 min-w-[384px] flex flex-col items-center justify-center p-8 text-center animate-in fade-in zoom-in duration-300">
        <div class="w-20 h-20 rounded-full bg-muted/30 flex items-center justify-center mb-6 ring-1 ring-border/50 shadow-sm">
            <FileStack class="w-10 h-10 text-muted-foreground/40" stroke-width="1.5" />
        </div>
        <p class="text-sm font-medium text-foreground">暂无文件</p>
        <p class="text-xs text-muted-foreground mt-1 max-w-[180px]">
            {{ searchQuery ? '未找到匹配的文件' : '上传文档以开始分析' }}
        </p>
        <Button v-if="!searchQuery" variant="link" size="sm" class="mt-2 h-auto p-0 text-primary" @click="$emit('add-files')">
            立即上传
        </Button>
    </div>

    <!-- File List -->
    <ScrollArea v-else class="flex-1 min-w-[384px]">
      <div class="p-3 space-y-1">
        <!-- List Items -->
        <div 
          v-for="(file, index) in filteredAttachments" 
          :key="index"
          class="group flex items-start gap-3 p-3 rounded-md hover:bg-accent/50 transition-all cursor-default relative border border-transparent hover:border-border/50"
        >
          <!-- Icon -->
          <div class="w-9 h-9 rounded bg-background border shadow-sm flex items-center justify-center shrink-0 text-primary/80">
            <FileText class="w-5 h-5" />
          </div>
          
          <!-- Info -->
          <div class="flex flex-col min-w-0 flex-1 gap-1">
            <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium text-foreground truncate" :title="file.name">{{ file.name }}</span>
                <!-- Status Badge -->
                <div v-if="file.status" class="shrink-0">
                    <TooltipProvider v-if="file.status === 'error'">
                        <Tooltip>
                            <TooltipTrigger>
                                <Badge variant="destructive" class="h-5 px-1.5 text-[10px] gap-1">
                                    <FileX class="w-3 h-3" />
                                    失败
                                </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                                {{ file.errorMessage || '解析失败' }}
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>

                    <div v-else-if="file.status === 'success'" class="inline-flex">
                        <HoverCard :open-delay="200">
                            <HoverCardTrigger as-child>
                                <Badge variant="outline" class="h-5 px-1.5 text-[10px] gap-1 bg-green-500/10 text-green-600 border-green-200 hover:bg-green-500/20 hover:border-green-300 transition-colors cursor-help">
                                    <FileCheck class="w-3 h-3" />
                                    已完成
                                </Badge>
                            </HoverCardTrigger>
                            <HoverCardContent align="end" class="w-80 p-4">
                                <div class="space-y-2">
                                    <h4 class="text-sm font-semibold flex items-center gap-2">
                                        <Info class="w-4 h-4 text-primary" />
                                        文档摘要
                                    </h4>
                                    <p class="text-xs text-muted-foreground leading-relaxed">
                                        {{ file.summary || '暂无摘要信息。' }}
                                    </p>
                                    <div class="flex items-center gap-2 pt-2 border-t border-border/50">
                                        <Badge variant="secondary" class="text-[10px] h-5">页数: {{ file.pageCount || '-' }}</Badge>
                                        <Badge variant="secondary" class="text-[10px] h-5">字数: {{ file.wordCount || '-' }}</Badge>
                                    </div>
                                </div>
                            </HoverCardContent>
                        </HoverCard>
                    </div>
                    
                    <Badge v-else variant="secondary" class="h-5 px-1.5 text-[10px] gap-1">
                        <Loader2 class="w-3 h-3 animate-spin" />
                        {{ file.status === 'uploading' ? '上传中' : '解析中' }}
                    </Badge>
                </div>
            </div>
            
            <!-- Progress Bar -->
            <div v-if="file.status === 'uploading' || file.status === 'parsing'" class="space-y-1">
                <div class="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span>{{ file.status === 'uploading' ? '上传文件...' : '智能解析...' }}</span>
                    <span>{{ file.progress || 0 }}%</span>
                </div>
                <Progress :model-value="file.progress || 0" class="h-1" />
            </div>

            <span v-else class="text-[10px] text-muted-foreground truncate font-mono">
               {{ file.size ? formatSize(file.size) : '未知大小' }} · {{ new Date().toLocaleDateString() }}
            </span>
          </div>
          
          <!-- Actions -->
          <div class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity absolute right-2 top-1/2 -translate-y-1/2 bg-accent/50 rounded-md backdrop-blur-sm shadow-sm border border-border/50">
             <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger as-child>
                         <Button 
                            variant="ghost" 
                            size="icon" 
                            class="h-7 w-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                            @click.stop="$emit('remove-file', attachments.indexOf(file))"
                          >
                            <Trash2 class="w-3.5 h-3.5" />
                          </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">移除文件</TooltipContent>
                </Tooltip>
             </TooltipProvider>
          </div>
        </div>
      </div>
    </ScrollArea>
  </div>
  
  <!-- Toggle Button (Closed State) -->
  <div v-if="!isOpen" class="absolute left-0 top-4 z-20">
      <TooltipProvider>
        <Tooltip>
            <TooltipTrigger as-child>
                <Button 
                    variant="secondary" 
                    size="icon" 
                    class="h-9 w-6 rounded-l-none rounded-r-lg shadow-md border-y border-r border-border/50 bg-background/95 backdrop-blur hover:w-8 transition-all"
                    @click="$emit('toggle')"
                >
                    <ChevronsRight class="w-4 h-4 text-muted-foreground" />
                </Button>
            </TooltipTrigger>
            <TooltipContent side="right">展开文件列表</TooltipContent>
        </Tooltip>
      </TooltipProvider>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  PanelLeftClose, PanelLeftOpen, Search, Filter, 
  ArrowUpDown, Plus, FileText, Trash2, ChevronDown,
  ChevronsLeft, ChevronsRight, FileStack, Loader2, FileCheck, FileX, Info
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';

import type { Attachment } from '../../types';

const props = defineProps<{
  isOpen: boolean;
  attachments: Attachment[];
}>();

defineEmits(['toggle', 'add-files', 'remove-file']);

const searchQuery = ref('');
const currentFilter = ref<'all' | 'local' | 'knowledge'>('all');

const currentFilterLabel = computed(() => {
    switch (currentFilter.value) {
        case 'local': return '本地上传';
        case 'knowledge': return '知识库';
        default: return '全部';
    }
});

const filteredAttachments = computed(() => {
  let list = props.attachments;
  
  if (currentFilter.value !== 'all') {
      // 假设 Attachment 类型中有一个 source 或 type 字段来区分
      // 如果没有，这里暂时只能做 Mock，或者需要您确认 Attachment 的结构
      // 这里假设 type 字段存在，如果不存在，需要父组件传入带有类型的附件列表
      // 目前 Attachment 定义在 index.ts 中，通常包含 file 对象
      // 这里我们做一个简单的模拟判断，或者需要更新 Attachment 类型
      if (currentFilter.value === 'local') {
          // 本地文件通常有 file 对象
          list = list.filter(f => f.file);
      } else if (currentFilter.value === 'knowledge') {
          // 知识库文件可能没有 file 对象，或者有特定的标记
          list = list.filter(f => !f.file);
      }
  }

  if (!searchQuery.value) return list;
  const q = searchQuery.value.toLowerCase();
  return list.filter(f => f.name.toLowerCase().includes(q));
});

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};
</script>
