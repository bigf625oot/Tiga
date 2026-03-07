<script setup lang="ts">
import { computed } from 'vue';
import { Handle, Position, type NodeProps } from '@vue-flow/core';
import { NodeToolbar } from '@vue-flow/node-toolbar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { NodeData, NodeType, SourceType, TransformType, SinkType } from '../types/pipeline';
import { Database, FileJson, ArrowRightLeft, Save, AlertCircle, PlayCircle, Copy, Trash2, Settings2 } from 'lucide-vue-next';
import { cn } from '@/lib/utils';
import { usePipelineStore } from '../composables/usePipelineStore';

// import '@vue-flow/node-toolbar/dist/style.css';

const props = defineProps<NodeProps<NodeData>>();
const store = usePipelineStore();

const subTypeLabels: Record<string, string> = {
  [SourceType.KAFKA]: 'Kafka',
  [SourceType.POSTGRES]: 'Postgres',
  [SourceType.S3]: 'S3',
  [SourceType.REST]: 'REST API',
  [SourceType.GENERIC_SQL]: '通用 SQL',
  [TransformType.CLEAN_TEXT]: '文本清洗',
  [TransformType.FILTER]: '过滤',
  [TransformType.MAP]: '映射',
  [TransformType.UDF]: 'Python UDF',
  [TransformType.AGGREGATE]: '聚合',
  [SinkType.REDIS]: 'Redis',
  [SinkType.CLICKHOUSE]: 'ClickHouse',
  [SinkType.NEO4J]: 'Neo4j',
  [SinkType.ELASTICSEARCH]: 'Elasticsearch',
};

const subTypeLabel = computed(() => {
  if (!props.data.subType) return '';
  return subTypeLabels[props.data.subType] || props.data.subType;
});

const onCopy = () => {
  // Simple copy logic: create a new node with same data but new ID
  const newNode = {
    id: `node_${Date.now()}`,
    type: props.type,
    position: { x: props.position.x + 20, y: props.position.y + 20 },
    data: { ...props.data, label: `${props.data.label} (副本)` }
  };
  store.addNode(newNode);
};

const onDelete = () => {
  store.removeNode(props.id);
};

const onSettings = () => {
  store.setSelectedNode(props.id);
};

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
  if (props.data.status === 'running') return 'border-green-500 shadow-[0_0_8px_rgba(16,185,129,0.2)] bg-green-500/10';
  if (props.selected) return 'border-primary ring-2 ring-primary/20';
  return 'border-border hover:border-primary/50';
});
</script>

<template>
  <div class="relative group select-none">
    <NodeToolbar
      :is-visible="props.selected"
      :position="Position.Top"
      class="flex items-center gap-1 p-1 bg-background border rounded-md shadow-sm mb-2"
    >
      <Button variant="ghost" size="icon" class="h-6 w-6" @click.stop="onSettings" title="设置">
        <Settings2 class="w-3 h-3" />
      </Button>
      <Button variant="ghost" size="icon" class="h-6 w-6" @click.stop="onCopy" title="复制">
        <Copy class="w-3 h-3" />
      </Button>
      <div class="w-px h-3 bg-border mx-0.5" />
      <Button variant="ghost" size="icon" class="h-6 w-6 text-destructive hover:text-destructive hover:bg-destructive/10" @click.stop="onDelete" title="删除">
        <Trash2 class="w-3 h-3" />
      </Button>
    </NodeToolbar>

    <!-- Input Handle - Not for Source -->
    <Handle
      v-if="props.data.type !== NodeType.SOURCE"
      type="target"
      :position="Position.Left"
      class="!bg-slate-400 !w-2.5 !h-2.5 !-left-1.5 hover:!bg-primary transition-colors z-50"
    />

    <Card :class="cn('w-[120px] transition-all duration-200 dark:bg-black overflow-hidden border', statusColorClass)">
      <div class="p-1.5 flex flex-col gap-1">
        <!-- Main Content -->
        <div class="flex items-center gap-1.5 min-w-0">
          <div class="p-1 bg-muted rounded shrink-0">
            <component :is="IconComponent" class="w-3.5 h-3.5 text-muted-foreground" />
          </div>
          
          <div class="flex flex-col min-w-0 flex-1 leading-tight">
            <div class="flex items-center justify-between gap-0.5">
              <span class="text-[10px] font-bold text-foreground truncate">
                {{ props.data.label }}
              </span>
              <!-- Status Icon -->
              <div class="shrink-0 flex items-center">
                <PlayCircle v-if="props.data.status === 'running'" class="w-2.5 h-2.5 text-green-500 animate-pulse" />
                <AlertCircle v-if="props.data.status === 'error'" class="w-2.5 h-2.5 text-destructive" />
              </div>
            </div>
            <!-- SubType -->
            <span v-if="props.data.subType" class="text-[8px] text-muted-foreground uppercase truncate opacity-70">
              {{ subTypeLabel }}
            </span>
          </div>
        </div>
        
        <!-- Metrics Footer -->
        <div v-if="props.data.metrics" class="flex items-center justify-between text-[7px] text-muted-foreground/50 border-t border-border/50 pt-0.5 mt-0.5 overflow-hidden whitespace-nowrap">
          <span>{{ Math.round(props.data.metrics.eps ?? 0) }} EPS</span>
          <span>{{ (props.data.metrics.latency ?? 0).toFixed(1) }}ms</span>
        </div>
      </div>
    </Card>

    <!-- Output Handle - Not for Sink -->
    <Handle
      v-if="props.data.type !== NodeType.SINK"
      type="source"
      :position="Position.Right"
      class="!bg-slate-400 !w-2.5 !h-2.5 !-right-1.5 hover:!bg-primary transition-colors z-50"
    />
  </div>
</template>
