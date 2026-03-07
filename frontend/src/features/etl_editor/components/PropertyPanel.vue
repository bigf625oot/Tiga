<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../composables/usePipelineStore';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Box, Trash2 } from 'lucide-vue-next';
import { NodeType, SourceType, SinkType, TransformType } from '../types/pipeline';
import { dataSourceApi, type DataSource } from '@/features/data_etl/api';
import LlmIntentProperties from './properties/LlmIntentProperties.vue';
import FilterBuilder from './properties/FilterBuilder.vue';
import TextCleaningProperties from './properties/TextCleaningProperties.vue';
import EmbeddingProperties from './properties/EmbeddingProperties.vue';
import GraphExtractProperties from './properties/GraphExtractProperties.vue';
import AggregateProperties from './properties/AggregateProperties.vue';
import UdfProperties from './properties/UdfProperties.vue';
import MapProperties from './properties/MapProperties.vue';
import StructuredSinkProperties from './properties/StructuredSinkProperties.vue';
import VectorSinkProperties from './properties/VectorSinkProperties.vue';
import GraphSinkProperties from './properties/GraphSinkProperties.vue';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const dataSources = ref<DataSource[]>([]);

const fetchDataSources = async () => {
  try {
    dataSources.value = await dataSourceApi.list();
  } catch (e) {
    console.error('Failed to fetch data sources', e);
  }
};

onMounted(fetchDataSources);

const availableDataSources = computed(() => {
  if (!node.value) return [];
  return dataSources.value.filter(ds => ds.type === node.value?.data?.subType);
});

const handleDelete = () => {
  if (node.value) {
    store.removeNode(node.value.id);
  }
};

const updateLabel = (value: string | number) => {
  if (node.value) {
    store.updateNodeData(node.value.id, { label: String(value) });
  }
};

const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};
</script>

<template>
  <div class="h-full flex flex-col bg-card border-l border-border relative">
    <div class="p-4 border-b border-border flex items-center justify-between">
      <h2 class="font-medium text-foreground">属性配置</h2>
    </div>

    <div v-if="!node || !node.data" class="flex-1 flex items-center justify-center p-8 text-center text-muted-foreground text-sm">
      <div class="flex flex-col items-center gap-2">
        <Box class="w-8 h-8 opacity-20" />
        <p>选中节点以配置参数</p>
      </div>
    </div>

    <div v-else class="flex-1 overflow-y-auto p-4 space-y-6 pb-20">
      <!-- Common Settings -->
      <div class="space-y-4">
        <div class="space-y-2">
          <Label>节点名称</Label>
          <Input :model-value="node.data?.label" @update:model-value="updateLabel" />
        </div>
        <div class="space-y-2">
          <Label>节点类型</Label>
          <div class="text-sm text-muted-foreground bg-muted p-2 rounded capitalize font-mono">
            {{ node.data?.subType }} ({{ node.data?.type }})
          </div>
        </div>
      </div>

      <div class="h-px bg-border my-4" />

      <!-- Specific Config based on SubType -->
      <div class="space-y-4">
        <h3 class="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          参数配置
        </h3>

        <!-- Data Source Connection Selection for SFTP, Crawler, Database, API -->
        <template v-if="[SourceType.SFTP, SourceType.CRAWLER, SourceType.DATABASE, SourceType.API].includes(node.data?.subType as SourceType)">
          <div class="space-y-2">
            <Label>选择数据连接 (Connection)</Label>
            <Select 
              :model-value="node.data?.config?.data_source_id?.toString()"
              @update:model-value="(v) => updateConfig('data_source_id', parseInt(v))"
            >
              <SelectTrigger>
                <SelectValue placeholder="请选择已创建的数据源..." />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>可用连接</SelectLabel>
                  <SelectItem 
                    v-for="ds in availableDataSources" 
                    :key="ds.id" 
                    :value="ds.id.toString()"
                  >
                    {{ ds.name }}
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
            <p v-if="!availableDataSources.length" class="text-xs text-muted-foreground text-destructive">
              未找到相关类型的连接，请先在数据源管理中创建。
            </p>
          </div>
        </template>

        <!-- Kafka Source Config -->
        <template v-if="node.data?.subType === SourceType.KAFKA">
          <div class="space-y-2">
            <Label>引导服务器 (Bootstrap Servers)</Label>
            <Input 
              placeholder="localhost:9092" 
              :model-value="node.data?.config?.bootstrap_servers"
              @update:model-value="(v) => updateConfig('bootstrap_servers', v)"
            />
          </div>
          <div class="space-y-2">
            <Label>主题 (Topic)</Label>
            <Input 
              placeholder="input_topic" 
              :model-value="node.data?.config?.topic"
              @update:model-value="(v) => updateConfig('topic', v)"
            />
          </div>
          <div class="space-y-2">
            <Label>消费组 ID (Group ID)</Label>
            <Input 
              placeholder="group_id" 
              :model-value="node.data?.config?.group_id"
              @update:model-value="(v) => updateConfig('group_id', v)"
            />
          </div>
        </template>

        <!-- Postgres Source Config -->
        <template v-if="node.data?.subType === SourceType.POSTGRES">
          <div class="space-y-2">
            <Label>主机地址 (Host)</Label>
            <Input 
              placeholder="localhost" 
              :model-value="node.data?.config?.host"
              @update:model-value="(v) => updateConfig('host', v)"
            />
          </div>
          <div class="space-y-2">
            <Label>端口 (Port)</Label>
            <Input 
              type="number"
              placeholder="5432" 
              :model-value="node.data?.config?.port"
              @update:model-value="(v) => updateConfig('port', parseInt(v as string))"
            />
          </div>
          <div class="space-y-2">
            <Label>数据库 (Database)</Label>
            <Input 
              placeholder="mydb" 
              :model-value="node.data?.config?.database"
              @update:model-value="(v) => updateConfig('database', v)"
            />
          </div>
          <div class="space-y-2">
            <Label>表名 (Table)</Label>
            <Input 
              placeholder="users" 
              :model-value="node.data?.config?.table"
              @update:model-value="(v) => updateConfig('table', v)"
            />
          </div>
        </template>

        <!-- Redis Sink Config -->
        <template v-if="node.data?.subType === SinkType.REDIS">
          <div class="space-y-2">
            <Label>主机地址 (Host)</Label>
            <Input 
              placeholder="localhost" 
              :model-value="node.data?.config?.host"
              @update:model-value="(v) => updateConfig('host', v)"
            />
          </div>
          <div class="space-y-2">
            <Label>端口 (Port)</Label>
            <Input 
              type="number"
              placeholder="6379" 
              :model-value="node.data?.config?.port"
              @update:model-value="(v) => updateConfig('port', parseInt(v as string))"
            />
          </div>
           <div class="space-y-2">
            <Label>键前缀 (Key Prefix)</Label>
            <Input 
              placeholder="data:" 
              :model-value="node.data?.config?.key_prefix"
              @update:model-value="(v) => updateConfig('key_prefix', v)"
            />
          </div>
        </template>
        
        <!-- Structured Sink Config (ClickHouse, etc) -->
        <template v-if="node.data?.subType === SinkType.CLICKHOUSE">
          <StructuredSinkProperties />
        </template>

        <!-- Vector Sink Config (Elasticsearch, etc) -->
        <template v-if="node.data?.subType === SinkType.ELASTICSEARCH">
          <VectorSinkProperties />
        </template>

        <!-- Graph Sink Config (Neo4j, etc) -->
        <template v-if="node.data?.subType === SinkType.NEO4J">
          <GraphSinkProperties />
        </template>

        <!-- Filter Transform Config -->
        <template v-if="node.data?.subType === TransformType.FILTER">
          <div class="space-y-2">
            <Label>过滤规则 (Filter Rules)</Label>
            <FilterBuilder 
              :model-value="node.data?.config?.expression"
              @update:model-value="(v) => updateConfig('expression', v)"
            />
          </div>
        </template>
        
        <!-- Map Config -->
        <template v-if="node.data?.subType === TransformType.MAP">
           <MapProperties />
        </template>

        <!-- Python UDF Config -->
        <template v-if="node.data?.subType === TransformType.UDF">
           <UdfProperties />
        </template>

        <!-- Clean Text Config -->
        <template v-if="node.data?.subType === TransformType.CLEAN_TEXT">
          <div class="space-y-2">
            <Label>清洗配置 (Cleaning Rules)</Label>
            <TextCleaningProperties 
              :code="node.data?.config?.code"
              :rules="node.data?.config?.cleaning_rules"
              @update:code="(v) => updateConfig('code', v)"
              @update:rules="(v) => updateConfig('cleaning_rules', v)"
            />
          </div>
        </template>

        <!-- Generic SQL Config -->
        <template v-if="node.data?.subType === SourceType.GENERIC_SQL">
           <div class="space-y-2">
            <Label>SQL 查询 (SQL Query)</Label>
            <textarea 
              placeholder="SELECT * FROM table" 
              class="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono text-xs h-32"
              :value="node.data?.config?.query"
              @input="(e) => updateConfig('query', (e.target as HTMLTextAreaElement).value)"
            />
          </div>
        </template>

        <!-- Aggregate Config -->
        <template v-if="node.data?.subType === TransformType.AGGREGATE">
           <AggregateProperties />
        </template>

        <!-- LLM Intent Config -->
        <template v-if="node.data?.subType === TransformType.LLM_INTENT">
           <LlmIntentProperties />
        </template>

        <!-- Vector Embedding Config -->
        <template v-if="node.data?.subType === TransformType.VECTOR_EMBEDDING">
           <EmbeddingProperties />
        </template>

        <!-- Knowledge Graph Extraction Config -->
        <template v-if="node.data?.subType === TransformType.GRAPH_EXTRACT">
           <GraphExtractProperties />
        </template>
      </div>
    </div>
    
    <div v-if="node" class="p-4 border-t border-border mt-auto bg-card">
      <Button 
        variant="destructive" 
        class="w-full gap-2"
        @click="handleDelete"
      >
        <Trash2 class="w-4 h-4" />
        删除节点
      </Button>
    </div>
  </div>
</template>