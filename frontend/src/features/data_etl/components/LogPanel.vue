<template>
  <div 
    class="absolute bottom-0 left-0 right-0 border-t backdrop-blur-md z-10 transition-all duration-300 bg-background/95 border-border shadow-[0_-4px_20px_-5px_rgba(0,0,0,0.1)]"
    :class="[isExpanded ? 'h-64' : 'h-9']"
  >
    <!-- Header / Toggle Bar -->
    <div 
      class="flex items-center justify-between px-4 h-9 cursor-pointer hover:bg-muted/50 transition-colors group"
      @click="toggleExpanded"
    >
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 text-primary">
            <Activity class="w-3.5 h-3.5" />
            <span class="text-[13px] font-semibold">实时日志流</span>
        </div>
        
        <!-- Mini Status (Visible when collapsed) -->
        <div v-if="!isExpanded && logs.length > 0" class="flex items-center gap-2 text-[12px] text-muted-foreground animate-in fade-in slide-in-from-bottom-1 duration-300">
           <div class="h-3 w-px bg-border"></div>
           <span class="truncate max-w-[300px]">{{ logs[0].message }}</span>
        </div>

        <div v-else class="flex items-center gap-2 text-[12px] text-muted-foreground animate-in fade-in slide-in-from-bottom-1 duration-300">
           <div class="h-3 w-px bg-border"></div>
           <span>共 {{ logs.length }} 条记录</span>
           <span class="flex items-center gap-1.5 ml-2">
             <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
             <span class="text-[11px] opacity-80">LIVE</span>
           </span>
        </div>
      </div>
      
      <div class="flex items-center gap-1">
        <Button 
          variant="ghost" 
          size="icon" 
          class="h-6 w-6 text-muted-foreground group-hover:text-foreground"
        >
            <component :is="isExpanded ? ChevronDown : ChevronUp" class="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="h-[calc(100%-36px)] overflow-hidden relative font-mono text-sm bg-background/50">
      <!-- Controls inside expanded view -->
      <div v-if="isExpanded" class="absolute top-2 right-4 z-20 flex gap-2">
         <Button 
            variant="secondary" 
            size="sm" 
            class="h-6 text-[10px] px-2 bg-muted/80 hover:bg-muted"
            @click.stop="isPaused = !isPaused"
          >
            <Pause v-if="!isPaused" class="w-3 h-3 mr-1" />
            <Play v-else class="w-3 h-3 mr-1" />
            {{ isPaused ? '继续' : '暂停' }}
          </Button>
      </div>

      <div 
        class="absolute inset-0 p-4 space-y-2 overflow-y-auto custom-scrollbar"
        :class="{'animate-scroll': !isPaused && !isHovering}"
        @mouseenter="isHovering = true"
        @mouseleave="isHovering = false"
      >
        <div 
          v-for="log in logs" 
          :key="log.id" 
          class="flex items-start gap-3 border-b border-border/40 pb-2 last:border-0 hover:bg-muted/30 p-1.5 rounded transition-colors"
        >
          <div class="flex flex-col items-center gap-1 shrink-0 pt-0.5">
             <div class="text-[11px] text-muted-foreground/60 font-mono">{{ log.timestamp }}</div>
          </div>
          
          <div class="shrink-0 pt-0.5">
            <CheckCircle2 v-if="log.level === 'success'" class="w-3.5 h-3.5 text-green-500" />
            <Info v-else-if="log.level === 'info'" class="w-3.5 h-3.5 text-blue-500" />
            <AlertTriangle v-else-if="log.level === 'warning'" class="w-3.5 h-3.5 text-yellow-500" />
            <XCircle v-else class="w-3.5 h-3.5 text-red-500" />
          </div>

          <div class="min-w-0 flex-1">
             <div 
               class="text-[13px] leading-snug break-all"
               :class="{
                'text-green-600 dark:text-green-400': log.level === 'success',
                'text-blue-600 dark:text-blue-400': log.level === 'info',
                'text-yellow-600 dark:text-yellow-400': log.level === 'warning',
                'text-red-600 dark:text-red-400': log.level === 'error',
                'text-muted-foreground': !['success', 'info', 'warning', 'error'].includes(log.level)
               }" 
               v-html="highlightLog(log.message)"
             ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { LogEntry } from '../composables/useDashboardMock';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  ChevronUp, 
  ChevronDown, 
  Pause, 
  Play,
  CheckCircle2,
  Info,
  AlertTriangle,
  XCircle
} from 'lucide-vue-next';

const props = defineProps<{
  logs: LogEntry[];
  expanded?: boolean;
}>();

const emit = defineEmits(['update:expanded']);

const isExpanded = ref(props.expanded ?? true); // Default expanded to show activity, user can collapse
const isPaused = ref(false);
const isHovering = ref(false);

watch(() => props.expanded, (newVal) => {
  if (newVal !== undefined) {
    isExpanded.value = newVal;
  }
});

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value;
  emit('update:expanded', isExpanded.value);
};

const highlightLog = (message: string) => {
  if (!message) return '';

  let highlighted = message;

  // 1. Keywords (Purple)
  highlighted = highlighted.replace(/(Pathway|LLM|Neo4j|S3|Kafka|Crawler)/g, 
    match => `<span class="text-purple-600 dark:text-purple-400 font-bold">${match}</span>`
  );

  // 2. Parameters (Orange)
  highlighted = highlighted.replace(/\b(project_name|pipeline_id|batch_size|source_type)\b/g, 
    match => `<span class="text-orange-600 dark:text-orange-400">${match}</span>`
  );

  // 3. Metrics/Numbers (Cyan)
  highlighted = highlighted.replace(/(\d+ms|\d+\.\d+s|\d+\s*records|\d+%)/g, 
    match => `<span class="text-cyan-600 dark:text-cyan-400">${match}</span>`
  );

  return highlighted;
};
</script>
<style scoped>
/* Simplified scroll animation for the list container if needed, 
   but for a real log panel, standard overflow-y is often better for usability. 
   I've removed the infinite CSS animation in favor of standard scrolling 
   because "live" logs usually just append to top/bottom. 
   If auto-scroll is strictly required, we can re-add it, 
   but for "Optimization", usability comes first.
*/
</style>
