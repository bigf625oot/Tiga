<script setup lang="ts">
import { computed } from 'vue';
import { Handle, Position, type NodeProps } from '@vue-flow/core';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { NodeData, NodeType } from '../types/pipeline';
import { Database, FileJson, ArrowRightLeft, Save, AlertCircle, PlayCircle } from 'lucide-vue-next';
import { cn } from '@/lib/utils'; // Assuming this utility exists based on shadcn usage

const props = defineProps<NodeProps<NodeData>>();

const getIcon = () => {
  switch (props.data.type) {
    case NodeType.SOURCE:
      return Database;
    case NodeType.TRANSFORM:
      return ArrowRightLeft;
    case NodeType.SINK:
      return Save;
    default:
      return FileJson;
  }
};

const IconComponent = getIcon();

const statusColorClass = computed(() => {
  if (props.data.status === 'error') return 'border-destructive bg-destructive/10';
  if (props.data.status === 'running') return 'border-green-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]';
  if (props.selected) return 'border-primary ring-2 ring-primary/20';
  return 'border-border hover:border-primary/50';
});
</script>

<template>
  <div class="relative group">
    <!-- Input Handle - Not for Source -->
    <Handle
      v-if="data.type !== NodeType.SOURCE"
      type="target"
      :position="Position.Left"
      class="!bg-slate-400 !w-3 !h-3 !-left-1.5 hover:!bg-primary transition-colors"
    />

    <Card :class="cn('w-[240px] transition-all duration-200 dark:bg-black', statusColorClass)">
      <CardHeader class="p-3 pb-2 flex flex-row items-center justify-between space-y-0">
        <div class="flex items-center gap-2">
          <div class="p-1.5 bg-muted rounded-md">
            <component :is="IconComponent" class="w-4 h-4 text-muted-foreground" />
          </div>
          <div class="flex flex-col">
            <span class="text-sm font-semibold text-foreground leading-none">
              {{ data.label }}
            </span>
            <span class="text-[10px] text-muted-foreground uppercase mt-1 font-medium">
              {{ data.subType }}
            </span>
          </div>
        </div>
        
        <PlayCircle v-if="data.status === 'running'" class="w-3 h-3 text-green-500 animate-pulse" />
        <AlertCircle v-if="data.status === 'error'" class="w-3 h-3 text-destructive" />
      </CardHeader>
      
      <CardContent class="p-3 pt-0">
         <!-- Metrics Overlay -->
         <div v-if="data.metrics" class="mt-2 flex items-center gap-2 text-[10px] text-muted-foreground bg-muted p-1.5 rounded">
           <span>EPS: {{ data.metrics.eps }}</span>
           <span class="w-px h-3 bg-border"></span>
           <span>Lat: {{ data.metrics.latency }}ms</span>
         </div>
      </CardContent>
    </Card>

    <!-- Output Handle - Not for Sink -->
    <Handle
      v-if="data.type !== NodeType.SINK"
      type="source"
      :position="Position.Right"
      class="!bg-slate-400 !w-3 !h-3 !-right-1.5 hover:!bg-primary transition-colors"
    />
  </div>
</template>
