<template>
  <div 
    class="relative rounded-xl border shadow-lg w-72 transition-all duration-300 group overflow-hidden bg-card text-card-foreground border-border hover:border-primary/50 hover:shadow-xl"
  >
    <!-- Left Status Strip -->
    <div 
      class="absolute left-0 top-0 bottom-0 w-1 transition-all duration-300"
      :class="{
        'bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.4)]': data.type === 'source',
        'bg-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)]': data.type === 'transform',
        'bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.4)]': data.type === 'sink'
      }"
    ></div>

    <div class="p-4 pl-5">
      <!-- Node Header -->
      <div class="flex items-center gap-3 mb-4">
        <div 
          class="w-10 h-10 rounded-lg flex items-center justify-center shadow-inner"
          :class="{
            'bg-blue-500/10 text-blue-600 dark:text-blue-400': data.type === 'source',
            'bg-purple-500/10 text-purple-600 dark:text-purple-400': data.type === 'transform',
            'bg-green-500/10 text-green-600 dark:text-green-400': data.type === 'sink'
          }"
        >
          <!-- Source Icons -->
          <svg v-if="data.type === 'source'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
          
          <!-- Transform Icons -->
          <svg v-else-if="data.type === 'transform'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>

          <!-- Sink Icons -->
          <svg v-else class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="font-bold text-[14px] text-foreground truncate" :title="data.label">{{ data.label }}</div>
          <div class="text-[12px] text-muted-foreground flex items-center gap-1.5">
            <span class="uppercase tracking-wider text-[10px] font-semibold bg-muted px-1.5 py-0.5 rounded">{{ subTypeMap[data.subType] || data.subType }}</span>
          </div>
        </div>
      </div>

      <!-- Config Preview -->
      <div v-if="data.config" class="mb-4 bg-muted/30 rounded-md p-2 text-xs border border-border/50">
        <div class="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wide">节点配置</div>
        <div class="space-y-1">
          <div 
            v-for="[key, value] in Object.entries(data.config).slice(0, 4)" 
            :key="key" 
            class="flex justify-between items-start gap-2"
          >
            <span class="text-muted-foreground opacity-80 shrink-0">{{ configKeyMap[key] || key }}:</span>
            <span class="font-mono text-foreground truncate text-right max-w-[140px]" :title="String(value)">
              {{ typeof value === 'object' ? JSON.stringify(value) : value }}
            </span>
          </div>
          <div v-if="Object.keys(data.config).length > 4" class="text-[10px] text-muted-foreground text-center pt-1 italic">
            + 还有 {{ Object.keys(data.config).length - 4 }} 项配置
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="space-y-3 pt-1 border-t border-border/50">
        <div class="flex justify-between items-center text-[12px]">
          <span class="text-muted-foreground">处理效率</span>
          <span class="font-mono font-medium text-foreground">
            {{ data.stats.total.toLocaleString() }} 
            <span class="text-[10px] text-muted-foreground">条/秒</span>
          </span>
        </div>
        
        <!-- Refined Progress Bar -->
        <div class="space-y-1.5">
          <div class="flex justify-between text-[11px]">
            <span class="text-muted-foreground">成功率</span>
            <span class="font-mono font-medium" :class="data.stats.pass_rate > 90 ? 'text-green-500' : 'text-yellow-500'">
              {{ data.stats.pass_rate }}
              <span class="text-muted-foreground">%</span>
            </span>
          </div>
          <div class="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div 
              class="h-full rounded-full transition-all duration-500"
              :class="data.stats.pass_rate > 90 ? 'bg-green-500' : 'bg-yellow-500'"
              :style="{ width: `${data.stats.pass_rate}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Refined Handles -->
    <Handle 
      v-if="data.type !== 'source'"
      type="target" 
      :position="Position.Left" 
      class="!w-3 !h-3 !bg-background !border-2 !border-muted-foreground/50 !-ml-1.5 transition-colors hover:!border-primary hover:!bg-primary/10" 
    />
    <Handle 
      v-if="data.type !== 'sink'"
      type="source" 
      :position="Position.Right" 
      class="!w-3 !h-3 !bg-background !border-2 !border-muted-foreground/50 !-mr-1.5 transition-colors hover:!border-primary hover:!bg-primary/10" 
    />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position, type NodeProps } from '@vue-flow/core';

defineProps<NodeProps>();

const subTypeMap: Record<string, string> = {
  sftp: 'SFTP',
  kafka: 'Kafka',
  clean_text: '文本清洗',
  llm_intent: '意图识别',
  filter: '数据过滤',
  elasticsearch: 'Elasticsearch',
  postgres: 'PostgreSQL',
  redis: 'Redis',
  api: 'API',
  crawler: '爬虫',
  database: '数据库',
  file_upload: '文件上传',
  rest: 'REST',
  generic_sql: '通用SQL',
  s3: 'S3',
  aggregate: '聚合',
  udf: '自定义函数',
  map: '映射',
  vector_embedding: '向量化',
  graph_extract: '图谱提取',
  knowledge_retrieval: '知识检索',
  clickhouse: 'ClickHouse',
  neo4j: 'Neo4j'
};

const configKeyMap: Record<string, string> = {
  host: '主机地址',
  port: '端口',
  username: '用户名',
  password: '密码',
  path: '路径',
  file_pattern: '文件匹配',
  remove_stopwords: '去除停用词',
  lowercase: '转小写',
  remove_punctuation: '去除标点',
  language: '语言',
  model: '模型',
  temperature: '温度',
  prompt_template: '提示词模板',
  categories: '分类类别',
  hosts: '主机列表',
  index_name: '索引名称',
  shards: '分片数',
  replicas: '副本数',
  bootstrap_servers: 'Kafka地址',
  topic: '主题',
  group_id: '消费组ID',
  offset: '偏移量',
  condition: '过滤条件',
  drop_nulls: '丢弃空值',
  database: '数据库名',
  table: '表名',
  endpoint: '接口地址',
  method: '请求方法',
  db: '数据库索引'
};
</script>
