<template>
  <div class="fixed top-1/2 right-0 -translate-y-1/2 z-50 flex items-center">
    <Sheet :modal="false">
      <TooltipProvider>
        <Tooltip :delay-duration="200">
          <TooltipTrigger as-child>
            <div class="relative">
              <SheetTrigger as-child>
                <Button
                  variant="outline"
                  class="group relative h-20 w-8 hover:w-12 rounded-l-2xl rounded-r-none border-y border-l border-border/60 border-r-0 shadow-[-4px_0_24px_rgba(0,0,0,0.08)] transition-all duration-300 ease-spring p-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-xl hover:bg-background overflow-visible"
                >
                  <div class="absolute left-[3px] top-1/2 -translate-y-1/2 w-[3px] h-8 bg-muted-foreground/30 rounded-full transition-all duration-300 group-hover:h-12 group-hover:bg-primary"></div>

                  <ListTodo
                    class="h-4 w-4 text-muted-foreground transition-all duration-300 group-hover:text-primary group-hover:scale-110 ml-1"
                    :class="{ 'text-primary': processingCount > 0 }"
                  />

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
              <span>任务中心</span>
              <Button variant="ghost" size="sm" @click="refreshTasks" class="h-7 w-7 p-0 ml-1">
                <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoading }" />
              </Button>
            </SheetTitle>
          </div>
          <SheetDescription class="text-xs">
            查看和管理后台运行的异步任务进度
          </SheetDescription>
        </SheetHeader>

        <ScrollArea class="flex-1 min-h-0">
          <div class="p-6">
            <Empty
              v-if="tasks.length === 0 && !isLoading"
              title="暂无任务"
              description="当前没有运行中的任务"
              class="min-h-[calc(100vh-160px)]"
            />

            <div v-else-if="isLoading && tasks.length === 0" class="flex items-center justify-center min-h-[calc(100vh-160px)]">
              <Card class="w-full max-w-sm border-border/50 shadow-sm">
                <CardHeader class="space-y-1">
                  <CardTitle class="text-base">加载中</CardTitle>
                  <CardDescription class="text-xs">正在获取任务列表</CardDescription>
                </CardHeader>
                <CardContent class="space-y-4">
                  <div class="flex items-center gap-3">
                    <Skeleton class="h-8 w-8 rounded-full" />
                    <div class="flex-1 space-y-2">
                      <Skeleton class="h-3 w-3/4" />
                      <Skeleton class="h-2 w-1/2" />
                    </div>
                  </div>
                  <Skeleton class="h-2 w-full" />
                  <div class="flex items-center justify-between">
                    <Skeleton class="h-2 w-16" />
                    <Skeleton class="h-2 w-12" />
                  </div>
                </CardContent>
              </Card>
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
                    @click="handleRemoveTask(task.id)"
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

              <p v-if="task.msg" class="text-[10px] text-muted-foreground mt-1 truncate">
                {{ task.msg }}
              </p>
            </div>
            </div>
          </div>
        </ScrollArea>

        <div v-if="tasks.length > 0" class="p-4 border-t border-border/50 bg-background/95 backdrop-blur-sm mt-auto shadow-[0_-4px_16px_-4px_rgba(0,0,0,0.05)]">
          <Button
            variant="ghost"
            class="w-full text-muted-foreground hover:text-destructive hover:bg-destructive/10 border border-transparent hover:border-destructive/20 transition-all duration-300"
            @click="handleClearCompleted"
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
import { ref, onMounted, onUnmounted } from 'vue';
import { useTaskStore } from '@/store/useTaskStore';
import { storeToRefs } from 'pinia';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
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
import {
  ListTodo,
  RefreshCw,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  X
} from 'lucide-vue-next';

const taskStore = useTaskStore();
const { tasks, processingCount } = storeToRefs(taskStore);
const isLoading = ref(false);
const userId = 'anonymous';

onMounted(() => {
  initTaskCenter();
});

onUnmounted(() => {
  taskStore.disconnect();
});

async function initTaskCenter() {
  isLoading.value = true;
  try {
    await taskStore.fetchTasks(userId);
    taskStore.connectWebSocket(userId);
  } catch (err) {
    console.error('Failed to initialize task center:', err);
  } finally {
    isLoading.value = false;
  }
}

async function refreshTasks() {
  isLoading.value = true;
  try {
    await taskStore.fetchTasks(userId);
  } catch (err) {
    console.error('Failed to refresh tasks:', err);
  } finally {
    isLoading.value = false;
  }
}

async function handleRemoveTask(id: string) {
  try {
    await taskStore.removeTask(id);
  } catch (err) {
    console.error('Failed to remove task:', err);
  }
}

async function handleClearCompleted() {
  try {
    await taskStore.clearCompletedTasks();
  } catch (err) {
    console.error('Failed to clear completed tasks:', err);
  }
}

function formatDate(timestamp: number) {
  if (!timestamp) return '--:--:--';
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(new Date(timestamp));
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    success: '已完成',
    error: '失败'
  };
  return map[status] || status;
}
</script>
