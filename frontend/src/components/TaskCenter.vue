<template>
  <div class="fixed top-1/2 right-0 -translate-y-1/2 z-50 flex items-center">
    <Sheet :modal="false">
      <TooltipProvider>
        <Tooltip :delay-duration="200">
          <TooltipTrigger as-child>
            <div class="relative">
              <SheetTrigger as-child>
                <!-- 
                  尼尔森原则应用:
                  1. 极简设计 (Aesthetic and minimalist design): 吸边隐藏，不干扰主视线，hover 时平滑展开
                  2. 系统状态可见性 (Visibility of system status): 右上角的呼吸动画指示器清晰显示正在处理的任务数
                  3. 灵活性与使用效率 (Flexibility and efficiency of use): 加大触发区域(h-20)，Fitts定律优化
                -->
                <Button 
                  variant="outline" 
                  class="group relative h-20 w-8 hover:w-12 rounded-l-2xl rounded-r-none border-y border-l border-border/60 border-r-0 shadow-[-4px_0_24px_rgba(0,0,0,0.08)] transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] p-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-xl hover:bg-background overflow-visible"
                >
                  <!-- 左侧提示条，增强视觉反馈 -->
                  <div class="absolute left-[3px] top-1/2 -translate-y-1/2 w-[3px] h-8 bg-muted-foreground/30 rounded-full transition-all duration-300 group-hover:h-12 group-hover:bg-primary"></div>
                  
                  <ListTodo 
                    class="h-4 w-4 text-muted-foreground transition-all duration-300 group-hover:text-primary group-hover:scale-110 ml-1" 
                    :class="{ 'text-primary': processingCount > 0 }"
                  />
                  
                  <!-- 动态任务数量角标 -->
                  <div v-if="processingCount > 0" class="absolute -top-2 -left-2 z-10">
                    <span class="relative flex h-5 w-5">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-60"></span>
                      <span class="relative inline-flex rounded-full h-5 w-5 bg-primary text-[10px] font-bold text-primary-foreground items-center justify-center shadow-sm border-2 border-background">
                        {{ processingCount }}
                      </span>
                    </span>
                  </div>
                </Button>
              </SheetTrigger>
            </div>
          </TooltipTrigger>
          
          <!-- 尼尔森原则: 识别而非记忆 (Recognition rather than recall) -->
          <TooltipContent side="left" :side-offset="15" class="flex items-center gap-2 px-3 py-2 shadow-xl border border-border/50 bg-background/95 backdrop-blur-md rounded-lg text-foreground z-[100]">
            <span class="text-sm font-medium">任务中心</span>
            <Badge v-if="processingCount > 0" variant="secondary" class="h-5 px-1.5 text-[10px] bg-primary/10 text-primary border-primary/20">
              {{ processingCount }} 个运行中
            </Badge>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      
      <SheetContent :overlay="false" side="right" class="w-[400px] sm:w-[540px] flex flex-col p-0 border-l border-border/50 shadow-2xl z-[60]">
        <SheetHeader class="px-6 py-4 border-b border-border/50 bg-muted/20">
          <div class="flex items-center justify-between">
            <SheetTitle class="flex items-center gap-2 text-lg">
              <!-- <Inbox class="w-5 h-5 text-primary" /> -->
              任务中心
            </SheetTitle>
          </div>
          <SheetDescription class="text-xs">
            查看和管理后台运行的异步任务进度
          </SheetDescription>
        </SheetHeader>

        <ScrollArea class="flex-1 p-6">
          <div v-if="tasks.length === 0" class="flex flex-col items-center justify-center h-[40vh] text-muted-foreground opacity-60">
            <CheckCircle2 class="w-12 h-12 mb-4 text-muted-foreground/50" />
            <p class="text-sm">当前没有运行中的任务</p>
          </div>

          <div v-else class="space-y-4">
            <div 
              v-for="task in tasks" 
              :key="task.id"
              class="p-4 rounded-xl border border-border/50 bg-card shadow-sm transition-all hover:shadow-md group relative overflow-hidden"
              :class="{
                'bg-muted/10': task.status === 'success',
                'bg-destructive/5 border-destructive/20': task.status === 'error'
              }"
            >
              <div class="flex justify-between items-start mb-2">
                <div class="flex items-center gap-2">
                  <div class="flex items-center justify-center w-6 h-6 rounded-full" 
                    :class="{
                      'bg-primary/10 text-primary': task.status === 'processing',
                      'bg-green-500/10 text-green-500': task.status === 'success',
                      'bg-destructive/10 text-destructive': task.status === 'error',
                      'bg-muted text-muted-foreground': task.status === 'pending'
                    }">
                    <Loader2 v-if="task.status === 'processing'" class="w-3.5 h-3.5 animate-spin" />
                    <CheckCircle2 v-else-if="task.status === 'success'" class="w-3.5 h-3.5" />
                    <AlertCircle v-else-if="task.status === 'error'" class="w-3.5 h-3.5" />
                    <Clock v-else class="w-3.5 h-3.5" />
                  </div>
                  <h4 class="font-medium text-sm truncate max-w-[200px]" :title="task.name">
                    {{ task.name }}
                  </h4>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold tabular-nums" 
                    :class="{
                      'text-primary': task.status === 'processing',
                      'text-green-500': task.status === 'success',
                      'text-destructive': task.status === 'error',
                      'text-muted-foreground': task.status === 'pending'
                    }">
                    {{ task.progress }}%
                  </span>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity -mr-1"
                    @click="taskStore.removeTask(task.id)"
                  >
                    <X class="w-3.5 h-3.5 text-muted-foreground" />
                  </Button>
                </div>
              </div>

              <Progress 
                :model-value="task.progress" 
                class="h-1.5 w-full bg-secondary/50" 
                :class="{
                  '[&>div]:bg-green-500': task.status === 'success',
                  '[&>div]:bg-destructive': task.status === 'error'
                }"
              />
              
              <div class="flex justify-between items-center mt-2">
                <span class="text-[10px] text-muted-foreground">
                  {{ formatDate(task.createdAt) }}
                </span>
                <span class="text-[10px] uppercase font-medium tracking-wider"
                  :class="{
                    'text-primary': task.status === 'processing',
                    'text-green-500': task.status === 'success',
                    'text-destructive': task.status === 'error',
                    'text-muted-foreground': task.status === 'pending'
                  }">
                  {{ getStatusText(task.status) }}
                </span>
              </div>
            </div>
          </div>
        </ScrollArea>
        
        <!-- 底部操作区 -->
        <div v-if="tasks.length > 0" class="p-4 border-t border-border/50 bg-background/95 backdrop-blur-sm mt-auto shadow-[0_-4px_16px_-4px_rgba(0,0,0,0.05)]">
          <Button 
            variant="ghost" 
            class="w-full text-muted-foreground hover:text-destructive hover:bg-destructive/10 border border-transparent hover:border-destructive/20 transition-all duration-300"
            @click="taskStore.clearCompletedTasks()"
          >
            <Trash2 class="w-4 h-4 mr-2" />
            清除已完成任务
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useTaskStore } from '@/store/useTaskStore';
import { storeToRefs } from 'pinia';

// UI Components
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

// Icons
import { 
  ListTodo, 
  Inbox, 
  Trash2, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  X 
} from 'lucide-vue-next';

// Store
const taskStore = useTaskStore();
const { tasks, processingCount } = storeToRefs(taskStore);

import { onMounted } from 'vue';

// Mock Data initialization for UI/UX testing
onMounted(() => {
  if (tasks.value.length === 0) {
    taskStore.addTask({
      name: '解析年度财务报表.xlsx',
      progress: 45,
      status: 'processing'
    });
    taskStore.addTask({
      name: '导出用户数据_2023.csv',
      progress: 100,
      status: 'success'
    });
    taskStore.addTask({
      name: '同步远程知识库',
      progress: 12,
      status: 'error'
    });
    taskStore.addTask({
      name: '生成大模型微调训练集',
      progress: 0,
      status: 'pending'
    });
    
    // Simulate progress updates for the processing task
    const interval = setInterval(() => {
      const processingTask = tasks.value.find(t => t.status === 'processing');
      if (processingTask) {
        let newProgress = processingTask.progress + Math.floor(Math.random() * 5);
        if (newProgress >= 100) {
          newProgress = 100;
          taskStore.updateTaskStatus(processingTask.id, 'success');
        }
        taskStore.updateTaskProgress(processingTask.id, newProgress);
      } else {
        clearInterval(interval);
      }
    }, 2000);
  }
});

// Utilities
const formatDate = (timestamp: number) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(new Date(timestamp));
};

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    success: '已完成',
    error: '失败'
  };
  return map[status] || status;
};
</script>
