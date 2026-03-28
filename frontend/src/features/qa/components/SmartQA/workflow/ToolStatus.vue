<template>
  <div class="tool-status-container my-2 max-w-[90%]">
    <Collapsible v-model:open="isOpen" class="border border-border/40 rounded-md overflow-hidden bg-background/50 shadow-sm transition-all duration-300">
      
      <!-- 总体状态头部 -->
      <CollapsibleTrigger as-child>
        <button class="w-full flex items-center justify-between px-3 py-1.5 hover:bg-muted/30 transition-colors group outline-none">
          <div class="flex items-center gap-2">
            <div class="w-5 h-5 rounded-full flex items-center justify-center" :class="overallStatus === 'running' ? 'bg-primary/10 text-primary' : 'bg-emerald-500/10 text-emerald-600'">
              <Loader2 v-if="overallStatus === 'running'" class="w-3 h-3 animate-spin" />
              <CheckCircle2 v-else class="w-3 h-3" />
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-medium text-foreground/80">
                {{ overallStatus === 'running' ? 'Using tools...' : `Completed ${tools.length} tool(s)` }}
              </span>
              <span v-if="!isOpen" class="text-[10px] text-muted-foreground/60 line-clamp-1 max-w-[150px]">
                {{ tools.map(t => t.name).join(', ') }}
              </span>
            </div>
          </div>
          <ChevronDown 
            class="w-3.5 h-3.5 text-muted-foreground/40 transition-transform duration-200 group-hover:text-muted-foreground/70"
            :class="isOpen ? 'rotate-180' : ''"
          />
        </button>
      </CollapsibleTrigger>

      <!-- 详细工具步骤条 -->
      <CollapsibleContent>
        <div class="px-3 py-2 border-t border-border/40 bg-muted/5 space-y-3">
          <div v-for="(tool, index) in tools" :key="index" class="relative pl-4">
            <!-- 连接线 -->
            <div v-if="index !== tools.length - 1" class="absolute left-[7px] top-4 bottom-[-16px] w-px bg-border/40"></div>
            
            <div class="flex flex-col gap-1">
              <!-- 节点头部 -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <!-- 状态圆点 -->
                  <div class="absolute left-0 top-1.5 w-3.5 h-3.5 rounded-full border-2 bg-background z-10 flex items-center justify-center"
                       :class="tool.status === 'running' ? 'border-primary' : (tool.status === 'error' ? 'border-destructive' : 'border-emerald-500/60')">
                       <div v-if="tool.status === 'running'" class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                  </div>
                  
                  <span class="text-[11px] font-medium text-foreground/90 flex items-center gap-1.5">
                    <Wrench class="w-3 h-3 text-muted-foreground/60" />
                    {{ tool.name }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <span v-if="tool.duration !== undefined" class="text-[9px] text-muted-foreground/40 font-mono">
                    {{ (tool.duration / 1000).toFixed(1) }}s
                  </span>
                  <span class="text-[9px] text-muted-foreground/60">
                    {{ tool.status === 'running' ? 'Running' : (tool.status === 'error' ? 'Failed' : 'Success') }}
                  </span>
                </div>
              </div>

              <!-- 参数输入 (折叠) -->
              <details class="group/args ml-1">
                <summary class="text-[9px] text-muted-foreground/60 cursor-pointer hover:text-foreground/80 select-none transition-colors">Show args</summary>
                <div class="mt-1 p-1.5 rounded bg-muted/30 border border-border/30 overflow-x-auto">
                  <pre class="text-[10px] font-mono text-muted-foreground/80 m-0">{{ formatJson(tool.args) }}</pre>
                </div>
              </details>

              <!-- 执行结果 (如果已完成) -->
              <div v-if="tool.result" class="mt-1 p-1.5 rounded bg-muted/30 border border-border/30 max-h-24 overflow-y-auto custom-scrollbar ml-1">
                <div class="text-[10px] font-mono whitespace-pre-wrap break-words"
                     :class="tool.status === 'error' ? 'text-destructive/80' : 'text-muted-foreground/80'">
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

export interface ToolExecution {
  id: string;
  name: string;
  args: any;
  status: 'running' | 'success' | 'error';
  result?: string;
  startTime?: number;
  duration?: number;
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
    // 如果存在任何失败的工具，禁止自动折叠，暴露错误给用户
    const hasError = props.tools.some(t => t.status === 'error');
    if (hasError) return;

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