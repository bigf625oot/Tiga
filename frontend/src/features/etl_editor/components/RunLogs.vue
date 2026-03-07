<script setup lang="ts">
import { ref, watch } from 'vue';
import { usePipelineStore } from '../composables/usePipelineStore';
import { pipelineApi } from '../api/pipeline';
import type { LogEntry } from '../types/pipeline';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, RefreshCw, Loader2, AlertCircle, Info, Bug, AlertTriangle } from 'lucide-vue-next';
import dayjs from 'dayjs';

const store = usePipelineStore();
const isOpen = ref(false);
const logs = ref<LogEntry[]>([]);
const loading = ref(false);

const fetchLogs = async () => {
  if (!store.currentPipeline) return;
  loading.value = true;
  try {
    logs.value = await pipelineApi.logs(store.currentPipeline.id);
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

watch(isOpen, (val) => {
  if (val) {
    fetchLogs();
  }
});

const getLevelColor = (level: string) => {
  switch (level) {
    case 'ERROR': return 'text-destructive';
    case 'WARN': return 'text-yellow-500';
    case 'DEBUG': return 'text-muted-foreground';
    default: return 'text-blue-500';
  }
};
</script>

<template>
  <Sheet v-model:open="isOpen">
    <SheetTrigger as-child>
      <Button variant="outline" size="sm" class="gap-2 h-8">
        <FileText class="w-4 h-4" />
        <span class="hidden sm:inline">运行日志</span>
      </Button>
    </SheetTrigger>
    <SheetContent class="w-[400px] sm:w-[800px] flex flex-col h-full">
      <SheetHeader>
        <SheetTitle class="flex items-center gap-2">
          <FileText class="w-5 h-5" />
          运行日志
        </SheetTitle>
        <SheetDescription>
          查看当前流水线的执行日志和系统消息。
        </SheetDescription>
      </SheetHeader>

      <div class="flex-1 flex flex-col min-h-0 mt-6">
        <div class="flex justify-between items-center mb-2 px-1">
          <span class="text-xs text-muted-foreground">共 {{ logs.length }} 条记录</span>
          <Button variant="ghost" size="sm" class="h-6 text-xs gap-1" @click="fetchLogs" :disabled="loading">
            <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': loading }" />
            刷新
          </Button>
        </div>
        
        <div class="flex-1 border rounded-md bg-muted/30 overflow-hidden flex flex-col">
          <ScrollArea class="flex-1 h-full">
            <div class="p-4 space-y-1.5 font-mono text-xs">
              <div v-if="loading && logs.length === 0" class="flex items-center justify-center py-8 text-muted-foreground">
                <Loader2 class="w-4 h-4 animate-spin mr-2" />
                加载中...
              </div>
              
              <div v-else-if="logs.length === 0" class="text-center py-8 text-muted-foreground opacity-60">
                暂无日志记录
              </div>
              
              <div v-else v-for="(log, idx) in logs" :key="idx" class="flex gap-3 leading-relaxed hover:bg-muted/50 p-1 rounded -mx-1 border-b border-border/40 last:border-0">
                <div class="shrink-0 text-muted-foreground w-[140px] select-none opacity-70">
                  {{ dayjs(log.timestamp).format('YYYY-MM-DD HH:mm:ss.SSS') }}
                </div>
                <div class="shrink-0 w-[45px] font-bold" :class="getLevelColor(log.level)">
                  {{ log.level }}
                </div>
                <div class="flex-1 break-all whitespace-pre-wrap text-foreground/90">
                  {{ log.message }}
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>
    </SheetContent>
  </Sheet>
</template>
