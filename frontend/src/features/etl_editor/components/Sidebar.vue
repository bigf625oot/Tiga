<script setup lang="ts">
import { ref, computed } from 'vue';
import { Database, ArrowRightLeft, Save, FileJson, Globe, FileText, Webhook, Brain, Sparkles, Network, UploadCloud, Search } from 'lucide-vue-next';
import { Card } from '@/components/ui/card';
import { NodeType, SourceType, TransformType, SinkType } from '../types/pipeline';

const props = defineProps<{
  searchQuery?: string;
}>();

const onDragStart = (event: DragEvent, type: NodeType, subType: string, label: string) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify({ type, subType, label }));
    event.dataTransfer.effectAllowed = 'move';
  }
};

const components = [
  {
    category: '数据源 (Sources)',
    items: [
      { type: NodeType.SOURCE, subType: SourceType.SFTP, label: 'SFTP 文件流', icon: FileText },
      { type: NodeType.SOURCE, subType: SourceType.CRAWLER, label: 'Web 爬虫', icon: Globe },
      { type: NodeType.SOURCE, subType: SourceType.DATABASE, label: '结构化数据库', icon: Database },
      { type: NodeType.SOURCE, subType: SourceType.API, label: '外部 API', icon: Webhook },
      { type: NodeType.SOURCE, subType: SourceType.FILE_UPLOAD, label: '单文件上传', icon: UploadCloud },
    ]
  },
  {
    category: '数据转换 (Transforms)',
    items: [
      { type: NodeType.TRANSFORM, subType: TransformType.CLEAN_TEXT, label: '文本清洗', icon: ArrowRightLeft },
      { type: NodeType.TRANSFORM, subType: TransformType.FILTER, label: '数据过滤', icon: ArrowRightLeft },
      { type: NodeType.TRANSFORM, subType: TransformType.MAP, label: '字段映射', icon: ArrowRightLeft },
      { type: NodeType.TRANSFORM, subType: TransformType.UDF, label: 'Python UDF', icon: ArrowRightLeft },
      { type: NodeType.TRANSFORM, subType: TransformType.AGGREGATE, label: '聚合计算', icon: ArrowRightLeft },
      { type: NodeType.TRANSFORM, subType: TransformType.LLM_INTENT, label: 'LLM 意图识别', icon: Brain },
      { type: NodeType.TRANSFORM, subType: TransformType.VECTOR_EMBEDDING, label: '向量嵌入', icon: Sparkles },
      { type: NodeType.TRANSFORM, subType: TransformType.GRAPH_EXTRACT, label: '知识图谱提取', icon: Network },
      { type: NodeType.TRANSFORM, subType: TransformType.KNOWLEDGE_RETRIEVAL, label: '知识库检索 (RAG)', icon: Search },
    ]
  },
  {
    category: '数据输出 (Sinks)',
    items: [
      { type: NodeType.SINK, subType: SinkType.REDIS, label: 'Redis 输出', icon: Save },
      { type: NodeType.SINK, subType: SinkType.CLICKHOUSE, label: '结构化数据库', icon: Database },
      { type: NodeType.SINK, subType: SinkType.NEO4J, label: 'Neo4j 图数据库', icon: Save },
      { type: NodeType.SINK, subType: SinkType.ELASTICSEARCH, label: 'Elasticsearch', icon: Save },
    ]
  }
];

const filteredComponents = computed(() => {
  if (!props.searchQuery) return components;
  
  const query = props.searchQuery.toLowerCase();
  return components.map(group => ({
    ...group,
    items: group.items.filter(item => 
      item.label.toLowerCase().includes(query) || 
      item.subType.toLowerCase().includes(query)
    )
  })).filter(group => group.items.length > 0);
});
</script>

<template>
  <div class="flex-1 p-4 overflow-y-auto">
    <div class="space-y-6">
      <div v-for="group in filteredComponents" :key="group.category">
        <h3 class="mb-2 text-sm font-semibold text-muted-foreground">{{ group.category }}</h3>
        <div class="grid gap-2">
          <Card
            v-for="item in group.items"
            :key="item.subType"
            class="cursor-grab border hover:border-primary/50 transition-colors active:cursor-grabbing p-3 flex items-center gap-3"
            draggable="true"
            @dragstart="(event: DragEvent) => onDragStart(event, item.type, item.subType, item.label)"
          >
            <component :is="item.icon" class="h-4 w-4 text-muted-foreground" />
            <span class="text-sm font-medium">{{ item.label }}</span>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>
