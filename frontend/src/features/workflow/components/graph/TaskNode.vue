<template>
  <div class="task-node group relative rounded-xl border bg-card text-card-foreground shadow-sm w-[280px] transition-all duration-300 hover:shadow-md"
       :class="cardBorderClass">
       
    <!-- Top Progress Bar for Running State -->
    <div v-if="data.status === 'running'" class="absolute top-0 left-0 h-[3px] bg-blue-500/10 w-full overflow-hidden rounded-t-xl">
      <div class="h-full bg-blue-500 animate-pulse" :style="{ width: `${data.progress || 100}%` }"></div>
    </div>

    <Handle type="target" position="top" class="w-2.5 h-2.5 border-2 border-background !bg-muted-foreground/30 transition-colors group-hover:!bg-muted-foreground/60" />

    <!-- Node Header -->
    <div class="p-3 border-b border-border/40 flex items-start gap-3 bg-muted/10 rounded-t-xl">
      <!-- Status Icon -->
      <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border shadow-sm" :class="iconContainerClass">
        <component :is="statusIcon" :class="['w-4 h-4', iconColorClass]" :spin="data.status === 'running'" />
      </div>
      
      <!-- Title & Status -->
      <div class="flex-1 min-w-0 pt-0.5">
        <h4 class="font-semibold text-[13px] truncate text-foreground leading-tight mb-1">{{ data.label }}</h4>
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-medium flex items-center gap-1.5" :class="statusTextColorClass">
            <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass"></span>
            {{ statusText }}
          </span>
          <span v-if="elapsedTime" class="text-[10px] text-muted-foreground/80 font-mono">{{ elapsedTime }}</span>
        </div>
      </div>
    </div>

    <!-- Node Body -->
    <div class="p-3 flex flex-col gap-3" v-if="data.description || (data.toolCalls && data.toolCalls.length > 0)">
      <!-- Description -->
      <div v-if="data.description" class="text-xs text-muted-foreground leading-relaxed line-clamp-2" :title="data.description">
        {{ data.description }}
      </div>

      <!-- Tools list -->
      <div v-if="data.toolCalls && data.toolCalls.length > 0" class="flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 mb-0.5">
          <AppstoreOutlined class="text-[10px] text-muted-foreground" />
          <span class="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Tools</span>
        </div>
        <div class="flex flex-col gap-1.5">
          <div v-for="(tool, idx) in data.toolCalls" :key="idx" 
               class="flex flex-col bg-muted/20 border border-border/60 rounded-md overflow-hidden transition-colors hover:bg-muted/40">
            
            <!-- Tool Header -->
            <div class="flex items-center justify-between px-2 py-1.5">
              <div class="flex items-center gap-2 min-w-0">
                <span class="truncate font-mono text-[11px] font-medium text-foreground/80">{{ tool.tool_name }}</span>
              </div>
              <component :is="getToolStatusIcon(tool.status)" 
                         :class="['shrink-0 text-[11px]', getToolStatusColor(tool.status)]" 
                         :spin="tool.status === 'running'" />
            </div>

            <!-- Tool Args (e.g., Query) -->
            <div v-if="tool.tool_args && getSearchQuery(tool)" class="px-2 pb-1.5 pt-0">
               <div class="text-[9px] font-mono text-muted-foreground/80 bg-background/50 px-1.5 py-0.5 rounded truncate border border-border/30">
                 > {{ getSearchQuery(tool) }}
               </div>
            </div>

            <!-- Search Results Preview -->
            <div v-if="getSearchResults(tool).length > 0" class="px-2 pb-2 pt-1 border-t border-border/30 bg-background/30">
              <div class="text-[9px] text-muted-foreground mb-1 font-medium flex items-center gap-1">
                <LinkOutlined /> Sources:
              </div>
              <div class="flex flex-col gap-1">
                <a v-for="(res, i) in getSearchResults(tool)" :key="i"
                   :href="res.url || res.link" target="_blank"
                   class="group/link flex flex-col gap-0.5 no-underline block hover:bg-muted p-1 rounded-sm border border-transparent hover:border-border/50 transition-colors">
                  <div class="text-[10px] text-blue-600 dark:text-blue-400 font-medium truncate group-hover/link:underline leading-tight">
                    {{ res.title || res.name || res.url || 'Untitled Source' }}
                  </div>
                  <div v-if="res.content || res.snippet" class="text-[9px] text-muted-foreground/70 line-clamp-1 leading-tight" :title="res.content || res.snippet">
                    {{ res.content || res.snippet }}
                  </div>
                </a>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

    <Handle type="source" position="bottom" class="w-2.5 h-2.5 border-2 border-background !bg-muted-foreground/30 transition-colors group-hover:!bg-muted-foreground/60" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Handle } from '@vue-flow/core';
import { 
  CheckCircleOutlined, 
  SyncOutlined, 
  ClockCircleOutlined, 
  CloseCircleOutlined,
  ToolOutlined,
  AppstoreOutlined
} from '@ant-design/icons-vue';

const props = defineProps(['data']);

const cardBorderClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'border-green-500/40 ring-1 ring-green-500/10';
    case 'running': return 'border-blue-500/50 ring-1 ring-blue-500/20';
    case 'failed': return 'border-red-500/50 ring-1 ring-red-500/20';
    default: return 'border-border/80 border-dashed';
  }
});

const iconContainerClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'bg-green-500/10 border-green-500/20';
    case 'running': return 'bg-blue-500/10 border-blue-500/20';
    case 'failed': return 'bg-red-500/10 border-red-500/20';
    default: return 'bg-muted border-border/50';
  }
});

const iconColorClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'text-green-600 dark:text-green-500';
    case 'running': return 'text-blue-600 dark:text-blue-500';
    case 'failed': return 'text-red-600 dark:text-red-500';
    default: return 'text-muted-foreground';
  }
});

const statusTextColorClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'text-green-600 dark:text-green-500';
    case 'running': return 'text-blue-600 dark:text-blue-500';
    case 'failed': return 'text-red-600 dark:text-red-500';
    default: return 'text-muted-foreground';
  }
});

const statusDotClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'bg-green-500';
    case 'running': return 'bg-blue-500 animate-pulse';
    case 'failed': return 'bg-red-500';
    default: return 'bg-muted-foreground';
  }
});

const statusIcon = computed(() => {
  switch (props.data.status) {
    case 'completed': return CheckCircleOutlined;
    case 'running': return SyncOutlined;
    case 'failed': return CloseCircleOutlined;
    default: return ClockCircleOutlined;
  }
});

const statusText = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'Success';
    case 'running': return 'Running...';
    case 'failed': return 'Failed';
    default: return 'Pending';
  }
});

const elapsedTime = computed(() => {
  if (!props.data.startTime) return '';
  const end = props.data.endTime || Date.now();
  const ms = end - props.data.startTime;
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
});

const getToolStatusIcon = (status) => {
  switch (status) {
    case 'completed': return CheckCircleOutlined;
    case 'failed': return CloseCircleOutlined;
    case 'running': return SyncOutlined;
    default: return ClockCircleOutlined;
  }
};

const getToolStatusColor = (status) => {
  switch (status) {
    case 'completed': return 'text-green-500';
    case 'failed': return 'text-red-500';
    case 'running': return 'text-blue-500 animate-spin';
    default: return 'text-muted-foreground';
  }
};
</script>

<style scoped>
.task-node {
  transform: translateZ(0);
}
</style>
