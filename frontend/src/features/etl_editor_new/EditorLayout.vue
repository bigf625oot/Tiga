<script setup lang="ts">
import { Database, ArrowRightLeft, Save, Box, Search } from 'lucide-vue-next';
import PipelineCanvas from './components/PipelineCanvas.vue';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { ref } from 'vue';

const components = [
  {
    category: "输入源 (Extract)",
    items: [
      { label: "Kafka 流", type: "SOURCE", subType: "kafka", icon: Database },
      { label: "Postgres CDC", type: "SOURCE", subType: "postgres", icon: Database },
      { label: "S3 文件", type: "SOURCE", subType: "s3", icon: Database },
      { label: "REST API", type: "SOURCE", subType: "rest", icon: Database },
      { label: "通用 SQL", type: "SOURCE", subType: "generic_sql", icon: Database },
    ]
  },
  {
    category: "转换 (Transform)",
    items: [
      { label: "清洗文本", type: "TRANSFORM", subType: "clean_text", icon: ArrowRightLeft },
      { label: "聚合统计", type: "TRANSFORM", subType: "aggregate", icon: ArrowRightLeft },
      { label: "自定义 Python", type: "TRANSFORM", subType: "udf", icon: ArrowRightLeft },
      { label: "字段映射", type: "TRANSFORM", subType: "map", icon: ArrowRightLeft },
      { label: "数据过滤", type: "TRANSFORM", subType: "filter", icon: ArrowRightLeft },
    ]
  },
  {
    category: "输出 (Load)",
    items: [
      { label: "ClickHouse", type: "SINK", subType: "clickhouse", icon: Save },
      { label: "Neo4j 图库", type: "SINK", subType: "neo4j", icon: Save },
      { label: "Redis 缓存", type: "SINK", subType: "redis", icon: Save },
      { label: "Elasticsearch", type: "SINK", subType: "elasticsearch", icon: Save },
    ]
  }
];

const searchQuery = ref('');

const onDragStart = (event: DragEvent, type: string, subType: string) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify({ type, subType }));
    event.dataTransfer.effectAllowed = 'move';
  }
};
</script>

<template>
  <div class="flex h-screen w-full bg-background overflow-hidden">
    <!-- Left Sidebar - Component Library -->
    <div class="w-64 bg-card border-r border-border flex flex-col z-10 shadow-sm">
      <div class="p-4 border-b border-border space-y-4">
        <div class="flex items-center gap-2">
          <div class="p-1.5 bg-primary/10 rounded-md">
            <Box class="w-5 h-5 text-primary" />
          </div>
          <h1 class="font-semibold text-foreground tracking-tight">ETL Studio</h1>
        </div>
        <div class="relative">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            v-model="searchQuery"
            placeholder="搜索组件..." 
            class="pl-9 h-9 bg-background/50"
          />
        </div>
      </div>
      
      <ScrollArea class="flex-1 p-4">
        <div class="space-y-6">
          <div v-for="(group, idx) in components" :key="idx" class="space-y-3">
            <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">{{ group.category }}</h3>
            
            <div 
              v-for="item in group.items.filter(i => i.label.includes(searchQuery))" 
              :key="item.label"
              class="flex items-center gap-3 p-3 bg-background border border-border rounded-lg cursor-grab hover:border-primary hover:shadow-md transition-all group active:cursor-grabbing select-none"
              draggable="true"
              @dragstart="(e) => onDragStart(e, item.type, item.subType)"
            >
              <div class="p-2 bg-muted rounded-md group-hover:bg-primary/10 transition-colors">
                <component :is="item.icon" class="w-4 h-4 text-muted-foreground group-hover:text-primary" />
              </div>
              <span class="text-sm font-medium text-foreground">{{ item.label }}</span>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>

    <!-- Main Canvas Area -->
    <div class="flex-1 relative">
      <PipelineCanvas />
    </div>

    <!-- Right Sidebar - Properties (Placeholder) -->
    <div class="w-80 bg-card border-l border-border z-10 shadow-sm hidden lg:flex flex-col">
      <div class="p-4 border-b border-border">
        <h2 class="font-medium text-foreground">属性配置</h2>
      </div>
      <div class="flex-1 flex items-center justify-center p-8 text-center text-muted-foreground text-sm">
        <div class="flex flex-col items-center gap-2">
          <Box class="w-8 h-8 opacity-20" />
          <p>选中节点以配置参数</p>
        </div>
      </div>
    </div>
  </div>
</template>
