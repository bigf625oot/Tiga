<template>
  <div class="tool-status-container my-2 max-w-[85%]">
    <Collapsible v-model:open="isOpen" class="border border-border/50 rounded-lg overflow-hidden bg-background shadow-sm transition-all duration-300">
      
      <!-- 总体状态头部 -->
      <CollapsibleTrigger as-child>
        <button class="w-full flex items-center justify-between px-3 py-2 bg-muted/30 hover:bg-muted/50 transition-colors group outline-none">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 rounded flex items-center justify-center" :class="overallStatus === 'running' ? 'bg-primary/10 text-primary' : 'bg-emerald-500/10 text-emerald-600'">
              <Loader2 v-if="overallStatus === 'running'" class="w-3.5 h-3.5 animate-spin" />
              <CheckCircle2 v-else class="w-3.5 h-3.5" />
            </div>
            <div class="flex flex-col items-start">
              <span class="text-xs font-medium text-foreground">
                {{ overallStatus === 'running' ? '正在使用工具...' : `已完成 ${tools.length} 项操作` }}
              </span>
              <span class="text-[10px] text-muted-foreground line-clamp-1 text-left">
                {{ tools.map(t => t.name).join(', ') }}
              </span>
            </div>
          </div>
          <ChevronDown 
            class="w-4 h-4 text-muted-foreground/50 transition-transform duration-200"
            :class="isOpen ? 'rotate-180' : ''"
          />
        </button>
      </CollapsibleTrigger>

      <!-- 详细工具步骤条 -->
      <CollapsibleContent>
        <div class="px-3 py-2 border-t border-border/50 bg-muted/10 space-y-3">
          <div v-for="(tool, index) in tools" :key="index" class="relative pl-4">
            <!-- 连接线 -->
            <div v-if="index !== tools.length - 1" class="absolute left-[7px] top-4 bottom-[-16px] w-px bg-border/50"></div>
            
            <div class="flex flex-col gap-1.5">
              <!-- 节点头部 -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <!-- 状态圆点 -->
                  <div class="absolute left-0 top-1.5 w-3.5 h-3.5 rounded-full border-2 bg-background z-10 flex items-center justify-center"
                       :class="tool.status === 'running' ? 'border-primary' : (tool.status === 'error' ? 'border-destructive' : 'border-emerald-500')">
                       <div v-if="tool.status === 'running'" class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                  </div>
                  
                  <span class="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <Wrench class="w-3 h-3 text-muted-foreground" />
                    {{ tool.name }}
                  </span>
                </div>
                <Badge variant="outline" class="text-[9px] h-4 px-1.5 font-normal bg-background">
                  {{ tool.status === 'running' ? '执行中' : (tool.status === 'error' ? '失败' : '成功') }}
                </Badge>
              </div>

              <!-- 参数输入 (折叠) -->
              <details class="group/args">
                <summary class="text-[10px] text-muted-foreground cursor-pointer hover:text-foreground select-none">查看参数</summary>
                <div class="mt-1 p-2 rounded bg-background border border-border/50 overflow-x-auto">
                  <pre class="text-[10px] font-mono text-muted-foreground m-0">{{ formatJson(tool.args) }}</pre>
                </div>
              </details>

              <!-- 执行结果 (如果已完成) -->
              <div v-if="tool.result" class="mt-1 p-2 rounded bg-background border border-border/50 max-h-32 overflow-y-auto custom-scrollbar">
                <div class="text-[10px] font-mono whitespace-pre-wrap break-words"
                     :class="tool.status === 'error' ? 'text-destructive' : 'text-muted-foreground'">
                  {{ tool.result }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Loader2, CheckCircle2, ChevronDown, Wrench } from 'lucide-vue-next';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';

export interface ToolExecution {
  id: string;
  name: string;
  args: any;
  status: 'running' | 'success' | 'error';
  result?: string;
}

const props = defineProps<{
  tools: ToolExecution[];
}>();

const isOpen = ref(true);

const overallStatus = computed(() => {
  if (props.tools.length === 0) return 'idle';
  const hasRunning = props.tools.some(t => t.status === 'running');
  return hasRunning ? 'running' : 'completed';
});

// 当所有工具执行完毕时，自动收起
watch(overallStatus, (newVal, oldVal) => {
  if (oldVal === 'running' && newVal === 'completed') {
    setTimeout(() => {
      isOpen.value = false;
    }, 2000); // 给用户留出查看结果的时间
  }
});

const formatJson = (obj: any) => {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
};
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  border-radius: 2px;
}
</style>