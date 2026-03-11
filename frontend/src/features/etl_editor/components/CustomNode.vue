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
  [SourceType.FILE_UPLOAD]: '文件上传',
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

const iconBgClass = computed(() => {
  switch (props.data.type) {
    case NodeType.SOURCE: return 'bg-blue-500/10 dark:bg-blue-500/20';
    case NodeType.TRANSFORM: return 'bg-amber-500/10 dark:bg-amber-500/20';
    case NodeType.SINK: return 'bg-indigo-500/10 dark:bg-indigo-500/20';
    default: return 'bg-muted';
  }
});

const iconColorClass = computed(() => {
  switch (props.data.type) {
    case NodeType.SOURCE: return 'text-blue-600 dark:text-blue-400';
    case NodeType.TRANSFORM: return 'text-amber-600 dark:text-amber-400';
    case NodeType.SINK: return 'text-indigo-600 dark:text-indigo-400';
    default: return 'text-muted-foreground';
  }
});

const getLatencyColor = (latency?: number) => {
  if (!latency) return '';
  if (latency < 100) return 'text-green-600 dark:text-green-400';
  if (latency < 500) return 'text-amber-600 dark:text-amber-400';
  return 'text-destructive';
};

const statusColorClass = computed(() => {
  if (props.data.status === 'error') return 'border-destructive bg-destructive/10';
  if (props.data.status === 'running') return 'border-green-500 shadow-[0_0_8px_rgba(16,185,129,0.2)] bg-green-500/10';
  if (props.selected) return 'border-primary ring-2 ring-primary/20';
  return 'border-border hover:border-primary/50';
});

const configSummary = computed(() => {
  const config = props.data.config || {};
  const subType = props.data.subType;
  
  if (!config) return null;

  // Source Types
  if (subType === SourceType.KAFKA && config.topic) {
    return { label: '主题', value: config.topic };
  }
  if ((subType === SourceType.POSTGRES || subType === SourceType.DATABASE) && config.table) {
    return { label: '表名', value: config.table };
  }
  if (subType === SourceType.S3 && config.bucket) {
    return { label: '桶名', value: config.bucket };
  }
  if ((subType === SourceType.REST || subType === SourceType.API) && config.url) {
    try {
      const url = new URL(config.url);
      return { label: '域名', value: url.hostname };
    } catch {
      return { label: '地址', value: config.url };
    }
  }
  if (subType === SourceType.FILE_UPLOAD && config.filename) {
    return { label: '文件', value: config.filename };
  }
  if (subType === SourceType.GENERIC_SQL && config.query) {
    return { label: '查询', value: '自定义 SQL' };
  }
  if (subType === SourceType.CRAWLER) {
     return { label: '目标', value: config.url || config.start_urls?.[0] || '未配置' };
  }

  // Sink Types
  if (subType === SinkType.REDIS && config.key_prefix) {
    return { label: '前缀', value: config.key_prefix };
  }
  if ((subType === SinkType.CLICKHOUSE || subType === SinkType.POSTGRES) && config.table) {
    return { label: '表名', value: config.table };
  }
  if (subType === SinkType.ELASTICSEARCH && config.index) {
    return { label: '索引', value: config.index };
  }
  
  // Transform Types
  if (subType === TransformType.FILTER && config.condition) {
    return { label: '条件', value: config.condition };
  }
  if (subType === TransformType.MAP && config.fields) {
    return { label: '映射', value: `${Object.keys(config.fields).length} 个字段` };
  }
  if (subType === TransformType.CLEAN_TEXT) {
     return { label: '规则', value: config.operations?.length ? `${config.operations.length} 项` : '默认' };
  }
  if (subType === TransformType.VECTOR_EMBEDDING) {
    return { label: '模型', value: config.model || 'text-embedding-3' };
  }

  // Fallback for demo/empty state if needed, or just return null to hide
  // If we want to show "Not Configured" for everything:
  if (Object.keys(config).length === 0) {
      return { label: '配置', value: '待配置' };
  }

  return null;
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
      class="!bg-muted-foreground !w-3 !h-3 !-left-1.5 hover:!bg-primary transition-all z-50 border-2 border-background"
    />

    <Card :class="cn('w-[180px] transition-all duration-300 dark:bg-card/95 backdrop-blur-sm overflow-visible border shadow-md hover:shadow-lg group-hover:border-primary/50', statusColorClass)">
      <!-- Status Indicator Line -->
      <div v-if="props.data.status === 'running'" class="absolute top-0 left-0 w-full h-0.5 bg-green-500 animate-pulse-fast"></div>
      
      <div class="p-3 flex flex-col gap-2">
        <!-- Header -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <div 
              class="p-1.5 rounded-md shrink-0 transition-colors"
              :class="iconBgClass"
            >
              <component :is="IconComponent" class="w-4 h-4" :class="iconColorClass" />
            </div>
            <div class="flex flex-col min-w-0">
              <span class="text-xs font-semibold text-foreground truncate leading-none mb-1">
                {{ props.data.label }}
              </span>
              <span class="text-[10px] text-muted-foreground uppercase tracking-wider truncate">
                {{ subTypeLabel }}
              </span>
            </div>
          </div>
          
          <!-- Status Icon -->
          <div class="shrink-0 flex items-center pt-0.5">
            <div v-if="props.data.status === 'running'" class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </div>
            <AlertCircle v-else-if="props.data.status === 'error'" class="w-3.5 h-3.5 text-destructive" />
            <div v-else class="w-1.5 h-1.5 rounded-full bg-muted-foreground/30"></div>
          </div>
        </div>
        
        <!-- Config Summary -->
        <div v-if="configSummary" class="flex items-center gap-1.5 px-2 py-1 bg-background/50 rounded border border-border/50 text-[10px] text-muted-foreground truncate">
          <span class="font-semibold text-foreground/80 shrink-0">{{ configSummary.label }}:</span>
          <span class="truncate" :title="configSummary.value">{{ configSummary.value }}</span>
        </div>

        <!-- Metrics (Conditional) -->
        <div v-if="props.data.metrics" class="grid grid-cols-2 gap-1 mt-1">
          <div class="bg-muted/30 rounded px-1.5 py-1 flex flex-col">
            <span class="text-[9px] text-muted-foreground uppercase">EPS</span>
            <span class="text-[10px] font-mono font-medium">{{ Math.round(props.data.metrics.eps ?? 0) }}</span>
          </div>
          <div class="bg-muted/30 rounded px-1.5 py-1 flex flex-col">
            <span class="text-[9px] text-muted-foreground uppercase">Latency</span>
            <span class="text-[10px] font-mono font-medium" :class="getLatencyColor(props.data.metrics.latency)">
              {{ (props.data.metrics.latency ?? 0).toFixed(0) }}ms
            </span>
          </div>
        </div>
      </div>
    </Card>

    <!-- Output Handle - Not for Sink -->
    <Handle
      v-if="props.data.type !== NodeType.SINK"
      type="source"
      :position="Position.Right"
      class="!bg-muted-foreground !w-3 !h-3 !-right-1.5 hover:!bg-primary transition-all z-50 border-2 border-background"
    />
  </div>
</template>
