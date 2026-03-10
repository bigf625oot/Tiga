<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../composables/usePipelineStore';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Eye, Box, Trash2, UploadCloud, FileText, Play } from 'lucide-vue-next';
import CodeEditor from '@/components/ui/code-editor/CodeEditor.vue';
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
import DataPreviewModal from './DataPreviewModal.vue';
import KnowledgeRetrievalTest from './properties/KnowledgeRetrievalTest.vue';
import { watch } from 'vue';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const dataSources = ref<DataSource[]>([]);
const tables = ref<string[]>([]);
const columns = ref<string[]>([]); // New: for storing column names

const fetchDataSources = async () => {
  try {
    dataSources.value = await dataSourceApi.list();
  } catch (e) {
    console.error('Failed to fetch data sources', e);
  }
};

// Fetch tables when data source changes
watch(
  () => [node.value?.id, node.value?.data?.config?.data_source_id, node.value?.data?.subType],
  async ([nodeId, newId, subType], oldValue) => {
    // Only reset if we are on the SAME node but changed the data source
    // oldValue might be undefined on first run (immediate)
    const oldId = oldValue ? oldValue[1] : undefined;
    const oldNodeId = oldValue ? oldValue[0] : undefined;

    const isSameNode = nodeId === oldNodeId;
    const isDataSourceChanged = newId !== oldId;

    if (isSameNode && isDataSourceChanged && oldId !== undefined) {
      // Clear dependent config
      updateConfig('table_name', undefined);
      updateConfig('incremental_column', undefined);
      // Also clear query if switching data sources to avoid running wrong SQL on wrong DB
      updateConfig('query', undefined);
      columns.value = [];
    }

    if (newId && subType === SourceType.DATABASE) {
      try {
        const metadata = await dataSourceApi.fetchMetadata(newId as number);
        tables.value = metadata.map((m: any) => m.name);
      } catch (e) {
        console.error(e);
        tables.value = [];
      }
    } else {
      tables.value = [];
    }
  },
  { immediate: true }
);

// Fetch columns when table changes
watch(
  () => [node.value?.data?.config?.data_source_id, node.value?.data?.config?.table_name],
  async ([dataSourceId, tableName]) => {
    // 确保 dataSourceId 和 tableName 存在且有效
    // 宽松检查类型，尝试转换
    if (dataSourceId && tableName) {
      const id = Number(dataSourceId);
      const table = String(tableName);
      
      if (!isNaN(id) && table.trim() !== '') {
        try {
          const res = await dataSourceApi.fetchColumns(id, table);
          columns.value = res || []; 
        } catch (e) {
          console.error('Failed to fetch columns', e);
          columns.value = [];
        }
      } else {
        columns.value = [];
      }
    } else {
      columns.value = [];
    }
  },
  { immediate: true }
);

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

  const isPreviewOpen = ref(false);
  const previewSourceId = ref<number | null>(null);
  const previewTableName = ref<string | undefined>(undefined);
  const previewQuery = ref<string | undefined>(undefined);

  // Function to preview data
  const previewData = (dataSourceId: number, tableName?: string, query?: string) => {
    // 确保参数存在且有效
    if (!dataSourceId) return;
    if (!tableName && !query) return;
    
    previewSourceId.value = dataSourceId;
    previewTableName.value = tableName;
    previewQuery.value = query;
    isPreviewOpen.value = true;
  };

  // Helper functions for Output Configuration
  const updateOutputColumn = (index: number, field: 'original' | 'target', value: string | number) => {
    const currentCols = node.value?.data?.config?.output_columns || [];
    const newCols = [...currentCols];
    if (newCols[index]) {
      newCols[index] = { ...newCols[index], [field]: value };
      updateConfig('output_columns', newCols);
    }
  };

  const removeOutputColumn = (index: number) => {
    const currentCols = node.value?.data?.config?.output_columns || [];
    const newCols = [...currentCols];
    newCols.splice(index, 1);
    updateConfig('output_columns', newCols);
  };

  const addOutputColumn = () => {
    const currentCols = node.value?.data?.config?.output_columns || [];
    const newCols = [...currentCols, { original: '', target: '' }];
    updateConfig('output_columns', newCols);
  };
</script>

<template>
  <div class="h-full flex flex-col bg-card border-l border-border relative">
    <div class="p-4 border-b border-border flex items-center justify-between">
      <h2 class="font-medium text-foreground">属性配置</h2>
    </div>

    <DataPreviewModal 
      :is-open="isPreviewOpen"
      :data-source-id="previewSourceId"
      :table-name="previewTableName"
      :query="previewQuery"
      @close="isPreviewOpen = false"
    />

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

        <!-- SFTP Source Extended Config (Simplified UX) -->
        <template v-if="node.data?.subType === SourceType.SFTP">
          <div class="space-y-6 pt-2 border-t border-border mt-4">
            
            <!-- 1. What to read? (Path & Pattern) -->
            <div class="space-y-3">
              <Label class="text-sm font-medium">读取目标 (What to Read)</Label>
              <div class="grid grid-cols-[1fr,auto] gap-2">
                <div class="space-y-1">
                  <Input 
                    placeholder="/data/uploads" 
                    :model-value="node.data?.config?.remote_path"
                    @update:model-value="(v) => updateConfig('remote_path', v)"
                    class="h-9"
                  />
                  <p class="text-[10px] text-muted-foreground">文件夹路径</p>
                </div>
                <div class="flex items-center h-9 px-2 border rounded-md bg-muted/20" title="包含子文件夹">
                   <input 
                    type="checkbox" 
                    id="recursive" 
                    class="rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
                    :checked="node.data?.config?.recursive"
                    @change="(e) => updateConfig('recursive', (e.target as HTMLInputElement).checked)"
                  />
                  <Label for="recursive" class="text-xs font-normal cursor-pointer ml-2 whitespace-nowrap">含子目录</Label>
                </div>
              </div>
              
              <div class="space-y-1">
                <Input 
                  placeholder="*.csv (默认所有文件)" 
                  :model-value="node.data?.config?.file_pattern"
                  @update:model-value="(v) => updateConfig('file_pattern', v)"
                  class="h-9"
                />
                <p class="text-[10px] text-muted-foreground">可选：只读取特定后缀的文件</p>
              </div>
            </div>

            <!-- 2. How to process? (Strategy) -->
            <div class="space-y-3 pt-2 border-t border-dashed border-border/50">
              <Label class="text-sm font-medium">处理方式 (Processing)</Label>
              
              <div class="grid grid-cols-1 gap-2">
                <!-- Option A: Standard (New files only) -->
                <div 
                  class="border rounded-md p-3 cursor-pointer flex items-start gap-3 transition-all hover:border-primary/50"
                  :class="(!node.data?.config?.strategy || node.data?.config?.strategy === 'new') ? 'bg-primary/5 border-primary ring-1 ring-primary' : 'bg-card'"
                  @click="updateConfig('strategy', 'new')"
                >
                  <div class="mt-0.5 w-4 h-4 rounded-full border border-primary flex items-center justify-center flex-shrink-0">
                    <div v-if="!node.data?.config?.strategy || node.data?.config?.strategy === 'new'" class="w-2 h-2 rounded-full bg-primary" />
                  </div>
                  <div class="flex flex-col gap-0.5">
                    <span class="text-xs font-medium">只读新文件 (标准模式)</span>
                    <span class="text-[10px] text-muted-foreground">自动记住上次读取位置，不重复处理旧文件。</span>
                  </div>
                </div>

                <!-- Option B: Move/Archive -->
                <div 
                  class="border rounded-md p-3 cursor-pointer flex flex-col gap-2 transition-all hover:border-primary/50"
                  :class="node.data?.config?.strategy === 'move' ? 'bg-primary/5 border-primary ring-1 ring-primary' : 'bg-card'"
                  @click="updateConfig('strategy', 'move')"
                >
                  <div class="flex items-start gap-3">
                    <div class="mt-0.5 w-4 h-4 rounded-full border border-primary flex items-center justify-center flex-shrink-0">
                      <div v-if="node.data?.config?.strategy === 'move'" class="w-2 h-2 rounded-full bg-primary" />
                    </div>
                    <div class="flex flex-col gap-0.5">
                      <span class="text-xs font-medium">读完后归档 (移走文件)</span>
                      <span class="text-[10px] text-muted-foreground">处理成功后将文件移动到备份文件夹。</span>
                    </div>
                  </div>
                  
                  <!-- Archive Path Input (Only show when selected) -->
                  <div v-if="node.data?.config?.strategy === 'move'" class="pl-7 animate-in fade-in slide-in-from-top-1">
                    <Input 
                      placeholder="/data/processed (备份目录)" 
                      :model-value="node.data?.config?.move_to_path"
                      @update:model-value="(v) => updateConfig('move_to_path', v)"
                      class="h-8 text-xs"
                    />
                  </div>
                </div>

                <!-- Option C: Delete -->
                <div 
                  class="border rounded-md p-3 cursor-pointer flex items-start gap-3 transition-all hover:border-destructive/50"
                  :class="node.data?.config?.strategy === 'delete' ? 'bg-destructive/5 border-destructive ring-1 ring-destructive' : 'bg-card'"
                  @click="updateConfig('strategy', 'delete')"
                >
                  <div class="mt-0.5 w-4 h-4 rounded-full border border-current flex items-center justify-center flex-shrink-0" :class="node.data?.config?.strategy === 'delete' ? 'text-destructive' : 'text-muted-foreground'">
                    <div v-if="node.data?.config?.strategy === 'delete'" class="w-2 h-2 rounded-full bg-destructive" />
                  </div>
                  <div class="flex flex-col gap-0.5">
                    <span class="text-xs font-medium" :class="node.data?.config?.strategy === 'delete' ? 'text-destructive' : ''">读完后删除</span>
                    <span class="text-[10px] text-muted-foreground">危险操作：处理成功后直接删除源文件。</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Crawler Source Extended Config (Enhanced UX) -->
        <template v-if="node.data?.subType === SourceType.CRAWLER">
           <div class="space-y-6 pt-2 border-t border-border mt-4">
            
            <!-- 1. Target URL -->
            <div class="space-y-2">
              <Label class="text-sm font-medium">目标网址 (Target URL)</Label>
              <Input 
                placeholder="https://example.com/news" 
                :model-value="node.data?.config?.url"
                @update:model-value="(v) => updateConfig('url', v)"
                class="h-9"
              />
              <p class="text-[10px] text-muted-foreground">请输入您希望采集的新闻列表或文章详情页链接</p>
            </div>

            <!-- 2. Crawl Scope (Depth) -->
            <div class="space-y-2">
               <Label class="text-sm font-medium">抓取范围 (Scope)</Label>
               <Select 
                 :model-value="node.data?.config?.depth?.toString() || '1'"
                 @update:model-value="(v) => updateConfig('depth', parseInt(v))"
               >
                 <SelectTrigger class="h-9">
                   <SelectValue />
                 </SelectTrigger>
                 <SelectContent>
                   <SelectItem value="1">仅抓取当前页面 (Single Page)</SelectItem>
                   <SelectItem value="2">当前页 + 直接链接 (Depth 2)</SelectItem>
                   <SelectItem value="3">深度抓取 (Depth 3)</SelectItem>
                 </SelectContent>
               </Select>
            </div>

            <!-- 3. Page Type (JS Render) -->
            <div class="space-y-2">
               <Label class="text-sm font-medium">网页类型 (Page Type)</Label>
               <div class="grid grid-cols-2 gap-3">
                 <div 
                   class="border rounded-md p-3 cursor-pointer flex flex-col gap-1 transition-all hover:border-primary/50"
                   :class="!node.data?.config?.js_render ? 'bg-primary/10 border-primary ring-1 ring-primary' : 'bg-card hover:bg-muted/50'"
                   @click="updateConfig('js_render', false)"
                 >
                   <span class="font-medium text-xs">普通网页 (Static)</span>
                   <span class="text-[10px] text-muted-foreground leading-tight">加载速度快，适用于大多数新闻/博客网站</span>
                 </div>
                 <div 
                   class="border rounded-md p-3 cursor-pointer flex flex-col gap-1 transition-all hover:border-primary/50"
                   :class="node.data?.config?.js_render ? 'bg-primary/10 border-primary ring-1 ring-primary' : 'bg-card hover:bg-muted/50'"
                   @click="updateConfig('js_render', true)"
                 >
                   <span class="font-medium text-xs">动态网页 (Dynamic)</span>
                   <span class="text-[10px] text-muted-foreground leading-tight">适用于 SPA 或需 JS 渲染的复杂网站 (较慢)</span>
                 </div>
               </div>
            </div>

            <!-- 4. Extraction Strategy (Selector) -->
            <div class="space-y-3 pt-2 border-t border-dashed border-border/50">
               <div class="flex items-center justify-between">
                 <Label class="text-sm font-medium">正文提取方式</Label>
                 <span 
                    class="text-[10px] text-primary cursor-pointer hover:underline select-none"
                    @click="updateConfig('use_custom_selector', !node.data?.config?.use_custom_selector)"
                 >
                   {{ node.data?.config?.use_custom_selector ? '切换回智能模式' : '切换到高级模式' }}
                 </span>
               </div>
               
               <div v-if="!node.data?.config?.use_custom_selector" class="bg-muted/30 p-3 rounded-md border border-dashed flex items-center gap-3">
                  <div class="flex flex-col">
                    <span class="text-xs font-medium">AI 智能自动识别 (Auto Detect)</span>
                    <span class="text-[10px] text-muted-foreground">系统将自动分析页面结构并提取主要正文内容</span>
                  </div>
               </div>

               <div v-else class="space-y-2 animate-in fade-in slide-in-from-top-1 duration-300">
                 <Label class="text-xs">CSS 选择器 (Selector)</Label>
                 <Input 
                   placeholder="例如: .article-content, #main-body" 
                   :model-value="node.data?.config?.selector"
                   @update:model-value="(v) => updateConfig('selector', v)"
                   class="h-8 text-xs font-mono"
                 />
                 <p class="text-[10px] text-muted-foreground">
                   高级功能：手动指定页面中包含正文的 HTML 元素类名或 ID
                 </p>
               </div>
            </div>
          </div>
        </template>

        <!-- API Source Extended Config -->
        <template v-if="node.data?.subType === SourceType.API">
          <div class="space-y-4 pt-2 border-t border-border mt-4">
            <div class="space-y-2">
              <Label>请求方法 (Method)</Label>
              <Select 
                :model-value="node.data?.config?.method || 'GET'"
                @update:model-value="(v) => updateConfig('method', v)"
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div class="space-y-2">
              <Label>端点路径 (Endpoint Path)</Label>
              <Input 
                placeholder="/v1/users" 
                :model-value="node.data?.config?.endpoint"
                @update:model-value="(v) => updateConfig('endpoint', v)"
              />
              <p class="text-[10px] text-muted-foreground">相对于基础 URL 的路径</p>
            </div>

            <div class="space-y-2">
              <Label>请求参数 (Params/Body)</Label>
              <div class="h-32 border rounded-md overflow-hidden">
                <CodeEditor 
                  :model-value="node.data?.config?.params || '{}'"
                  @update:model-value="(v) => updateConfig('params', v)"
                  language="json"
                  theme="vs-dark"
                />
              </div>
              <p class="text-[10px] text-muted-foreground">JSON 格式的查询参数或请求体</p>
            </div>

            <div class="space-y-2">
              <Label>分页配置 (Pagination)</Label>
              <div class="grid grid-cols-2 gap-2">
                <div class="space-y-1">
                   <Label class="text-xs">页码参数</Label>
                   <Input 
                     placeholder="page" 
                     :model-value="node.data?.config?.page_param"
                     @update:model-value="(v) => updateConfig('page_param', v)"
                   />
                </div>
                <div class="space-y-1">
                   <Label class="text-xs">每页条数参数</Label>
                   <Input 
                     placeholder="page_size" 
                     :model-value="node.data?.config?.size_param"
                     @update:model-value="(v) => updateConfig('size_param', v)"
                   />
                </div>
              </div>
            </div>

            <div class="space-y-2">
              <Label>提取路径 (Data Path)</Label>
              <Input 
                placeholder="data.items" 
                :model-value="node.data?.config?.data_path"
                @update:model-value="(v) => updateConfig('data_path', v)"
              />
              <p class="text-[10px] text-muted-foreground">JSON 响应中数据列表的路径，如 data.items</p>
            </div>
          </div>
        </template>

        <!-- Database Source Extended Config -->
        <template v-if="node.data?.subType === SourceType.DATABASE">
          <div class="space-y-4 pt-2 border-t border-border mt-4">
             <div class="space-y-2">
                <Label>提取模式 (Extraction Mode)</Label>
                <Select 
                  :model-value="node.data?.config?.extraction_mode || 'table'"
                  @update:model-value="(v) => updateConfig('extraction_mode', v)"
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="table">整表/增量 (Table)</SelectItem>
                    <SelectItem value="query">自定义 SQL (Custom Query)</SelectItem>
                  </SelectContent>
                </Select>
             </div>

             <div v-if="node.data?.config?.extraction_mode === 'query'" class="space-y-2">
                <Label>SQL 查询语句</Label>
                <div class="relative h-64 border rounded-md overflow-hidden">
                  <CodeEditor 
                    :model-value="node.data?.config?.query || ''"
                    @update:model-value="(v) => updateConfig('query', v)"
                    language="sql"
                    theme="vs-dark"
                  />
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    title="预览查询结果"
                    class="absolute bottom-2 right-4 z-10 shadow-md gap-1"
                    :disabled="!node.data?.config?.query"
                    @click="previewData(node.data?.config?.data_source_id, undefined, node.data?.config?.query)"
                  >
                    <Play class="w-3 h-3" /> 运行
                  </Button>
                </div>
                <p class="text-[10px] text-muted-foreground">支持参数 :last_time 用于增量提取</p>
             </div>

             <div v-else-if="!node.data?.config?.extraction_mode || node.data?.config?.extraction_mode === 'table'" class="space-y-2">
                <Label>目标表 (Table)</Label>
                <div class="flex gap-2">
                  <Select 
                    :model-value="node.data?.config?.table_name"
                    @update:model-value="(v) => updateConfig('table_name', v)"
                  >
                    <SelectTrigger class="flex-1">
                      <SelectValue placeholder="选择数据表" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="t in tables" :key="t" :value="t">{{ t }}</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button 
                    variant="outline" 
                    size="icon" 
                    title="预览数据"
                    :disabled="!node.data?.config?.table_name"
                    @click="previewData(node.data?.config?.data_source_id, node.data?.config?.table_name)"
                  >
                    <Eye class="w-4 h-4" />
                  </Button>
                </div>
             </div>
             
             <div class="space-y-2">
                <Label>增量字段 (Incremental Column)</Label>
                <Select 
                  :model-value="node.data?.config?.incremental_column"
                  @update:model-value="(v) => updateConfig('incremental_column', v === 'none_selection' ? '' : v)"
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择字段 (可选)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none_selection">- 不使用增量 (全量) -</SelectItem>
                    <SelectItem v-for="c in columns" :key="c" :value="c">{{ c }}</SelectItem>
                  </SelectContent>
                </Select>
                <p class="text-[10px] text-muted-foreground">通常选择自增主键或更新时间字段</p>
             </div>
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
            <div class="h-64 border rounded-md overflow-hidden">
              <CodeEditor 
                :model-value="node.data?.config?.query || ''"
                @update:model-value="(v) => updateConfig('query', v)"
                language="sql"
                theme="vs-dark"
              />
            </div>
          </div>
        </template>

        <!-- File Upload Config -->
        <template v-if="node.data?.subType === SourceType.FILE_UPLOAD">
          <div class="space-y-2">
            <Label>上传文件 (Upload File)</Label>
            <div class="flex flex-col gap-2">
              <div 
                class="border-2 border-dashed border-muted-foreground/25 hover:border-muted-foreground/50 transition-colors rounded-lg p-6 flex flex-col items-center justify-center gap-2 cursor-pointer bg-muted/5 relative"
                @click="(e) => {
                   // Find the file input within this specific container
                   const target = e.currentTarget as HTMLElement;
                   const fileInput = target.querySelector('input[type=file]') as HTMLInputElement;
                   if (fileInput) fileInput.click();
                }"
              >
                 <UploadCloud class="w-8 h-8 text-muted-foreground" />
                 <p class="text-xs text-muted-foreground text-center">
                   点击或拖拽文件到此处上传
                 </p>
                 <input 
                   type="file" 
                   class="hidden"
                   @click.stop
                   @change="(e) => {
                    const file = (e.target as HTMLInputElement).files?.[0];
                    if (file) {
                      updateConfig('file_path', file.name); 
                    }
                  }"
                 />
              </div>

              <div v-if="node.data?.config?.file_path" class="flex items-center gap-2 bg-muted p-2 rounded text-xs border">
                <FileText class="w-4 h-4 text-primary" />
                <span class="flex-1 truncate font-medium">{{ node.data?.config?.file_path }}</span>
                <Button 
                   variant="ghost" 
                   size="icon" 
                   class="h-6 w-6 text-muted-foreground hover:text-destructive"
                   @click.stop="() => updateConfig('file_path', '')"
                >
                  <Trash2 class="w-3 h-3" />
                </Button>
              </div>
            </div>
          </div>
          <div class="space-y-2">
            <Label>文件格式 (Format)</Label>
            <Select 
              :model-value="node.data?.config?.format || 'csv'"
              @update:model-value="(v) => updateConfig('format', v)"
            >
              <SelectTrigger>
                <SelectValue placeholder="选择格式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="parquet">Parquet</SelectItem>
                <SelectItem value="excel">Excel</SelectItem>
                <SelectItem value="pdf">PDF</SelectItem>
                <SelectItem value="doc">Word (DOC/DOCX)</SelectItem>
                <SelectItem value="ppt">PowerPoint (PPT/PPTX)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <!-- Unstructured Document Config (PDF, DOC, PPT) -->
          <div v-if="['pdf', 'doc', 'ppt'].includes(node.data?.config?.format)" class="space-y-4 pt-2 border-t border-border/50">
            <div class="flex items-center space-x-2">
              <input 
                type="checkbox" 
                id="use_ocr" 
                class="rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
                :checked="node.data?.config?.use_ocr"
                @change="(e) => updateConfig('use_ocr', (e.target as HTMLInputElement).checked)"
              />
              <Label for="use_ocr" class="text-xs font-normal cursor-pointer">启用 OCR (Enable OCR)</Label>
            </div>
            <p class="text-[10px] text-muted-foreground">
              适用于扫描件或图片型文档。开启后处理速度较慢。
            </p>
          </div>

          <!-- Excel Specific Config -->
          <div v-if="node.data?.config?.format === 'excel'" class="space-y-4 pt-2 border-t border-border/50">
            <div class="space-y-2">
              <Label>读取模式 (Read Mode)</Label>
              <Select 
                :model-value="node.data?.config?.read_mode || 'auto'"
                @update:model-value="(v) => updateConfig('read_mode', v)"
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择读取模式" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">自动/跳过 (Auto/Skip)</SelectItem>
                  <SelectItem value="range">固定范围 (Fixed Range)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Auto/Skip Mode -->
            <template v-if="!node.data?.config?.read_mode || node.data?.config?.read_mode === 'auto'">
               <div class="grid grid-cols-2 gap-4">
                 <div class="space-y-2">
                    <Label>工作表 (Sheet)</Label>
                    <Input 
                      placeholder="Sheet1" 
                      :model-value="node.data?.config?.sheet_name"
                      @update:model-value="(v) => updateConfig('sheet_name', v)"
                    />
                 </div>
                 <div class="space-y-2">
                    <Label>表头行 (Header)</Label>
                    <Input 
                      type="number"
                      placeholder="0" 
                      :model-value="node.data?.config?.header_row"
                      @update:model-value="(v) => updateConfig('header_row', parseInt(v as string))"
                    />
                 </div>
               </div>

               <div class="grid grid-cols-2 gap-4">
                 <div class="space-y-2">
                   <Label>跳过头部 (Skip Top)</Label>
                   <Input 
                     type="number"
                     placeholder="0" 
                     :model-value="node.data?.config?.skip_rows"
                     @update:model-value="(v) => updateConfig('skip_rows', parseInt(v as string))"
                   />
                </div>
                <div class="space-y-2">
                   <Label>跳过尾部 (Skip Bottom)</Label>
                   <Input 
                     type="number"
                     placeholder="0" 
                     :model-value="node.data?.config?.skip_footer"
                     @update:model-value="(v) => updateConfig('skip_footer', parseInt(v as string))"
                   />
                </div>
              </div>

              <div class="space-y-2">
                   <Label>跳过指定行 (Skip Specific Rows)</Label>
                   <Input 
                     placeholder="例如: 1,3,5-10" 
                     :model-value="node.data?.config?.skip_specific_rows"
                     @update:model-value="(v) => updateConfig('skip_specific_rows', v)"
                   />
                   <p class="text-[10px] text-muted-foreground">
                     支持单个行号或范围（如 5-10），多个用逗号分隔。行号从 0 开始。
                   </p>
              </div>
  
              <div class="space-y-2">
                   <Label>读取列 (Use Cols)</Label>
                   <Input 
                     placeholder="A:Z 或 A,C,E" 
                     :model-value="node.data?.config?.use_cols"
                     @update:model-value="(v) => updateConfig('use_cols', v)"
                   />
              </div>
            </template>

            <!-- Fixed Range Mode -->
            <template v-else-if="node.data?.config?.read_mode === 'range'">
              <div class="space-y-2">
                 <Label>工作表 (Sheet)</Label>
                 <Input 
                   placeholder="Sheet1" 
                   :model-value="node.data?.config?.sheet_name"
                   @update:model-value="(v) => updateConfig('sheet_name', v)"
                 />
              </div>
              <div class="space-y-2">
                 <Label>数据区域 (Cell Range)</Label>
                 <Input 
                   placeholder="A2:E20" 
                   :model-value="node.data?.config?.data_range"
                   @update:model-value="(v) => updateConfig('data_range', v)"
                 />
                 <p class="text-[10px] text-muted-foreground">
                   使用标准 Excel 区域格式，例如 "A2:E20" 或 "Sheet2!C5:H50"
                 </p>
              </div>
              <div class="flex items-center space-x-2 pt-1">
                <input 
                  type="checkbox" 
                  id="has_header" 
                  class="rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
                  :checked="node.data?.config?.range_has_header !== false"
                  @change="(e) => updateConfig('range_has_header', (e.target as HTMLInputElement).checked)"
                />
                <Label for="has_header" class="text-xs font-normal cursor-pointer">区域首行包含表头 (Header included)</Label>
              </div>
            </template>
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
        
        <!-- Knowledge Retrieval (RAG) Config -->
        <template v-if="node.data?.subType === TransformType.KNOWLEDGE_RETRIEVAL">
           <div class="space-y-4 pt-2 border-t border-border mt-4">
             <div class="space-y-2">
                <Label>知识库 (Knowledge Base)</Label>
                <Select 
                  :model-value="node.data?.config?.knowledge_base"
                  @update:model-value="(v) => updateConfig('knowledge_base', v)"
                >
                  <SelectTrigger><SelectValue placeholder="选择知识库" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default_kb">默认知识库 (Default)</SelectItem>
                    <SelectItem value="product_docs">产品文档库</SelectItem>
                    <SelectItem value="technical_specs">技术规范库</SelectItem>
                  </SelectContent>
                </Select>
             </div>

             <div class="space-y-2">
               <Label>检索字段 (Query Column)</Label>
               <Input 
                 placeholder="content" 
                 :model-value="node.data?.config?.query_column"
                 @update:model-value="(v) => updateConfig('query_column', v)"
               />
               <p class="text-[10px] text-muted-foreground">
                 上游数据中用于检索的字段名（如用户提问）
               </p>
             </div>

             <div class="space-y-2">
               <Label>Top K (召回数量)</Label>
               <Input 
                 type="number"
                 placeholder="3" 
                 :model-value="node.data?.config?.top_k"
                 @update:model-value="(v) => updateConfig('top_k', parseInt(v as string))"
               />
             </div>

             <div class="space-y-2">
               <Label>相似度阈值 (Threshold)</Label>
               <div class="flex items-center gap-4">
                  <input 
                    type="range" 
                    min="0" 
                    max="1" 
                    step="0.01"
                    class="flex-1"
                    :value="node.data?.config?.score_threshold || 0.7"
                    @input="(e) => updateConfig('score_threshold', parseFloat((e.target as HTMLInputElement).value))"
                  />
                  <span class="w-8 text-xs text-right">{{ node.data?.config?.score_threshold || 0.7 }}</span>
               </div>
               <p class="text-[10px] text-muted-foreground">低于此分数的检索结果将被丢弃</p>
             </div>

             <!-- Knowledge Test Component -->
             <div class="pt-4 border-t border-dashed border-border/50">
               <KnowledgeRetrievalTest 
                 :config="node.data?.config"
               />
             </div>
           </div>
        </template>
        
        <!-- Output Schema Config for Transforms (Exclude Retrieval) -->
        <template v-if="node.data?.type === NodeType.TRANSFORM && node.data?.subType !== TransformType.KNOWLEDGE_RETRIEVAL">
           <div class="space-y-4 pt-4 border-t border-border mt-4">
             <div class="flex items-center justify-between">
               <h3 class="text-sm font-medium text-muted-foreground uppercase tracking-wider">输出配置 (Output)</h3>
             </div>
             
             <div class="space-y-2">
                <Label>输出字段重命名 (Rename Columns)</Label>
                <div class="space-y-2">
                  <div v-for="(col, index) in (node.data?.config?.output_columns || [])" :key="index" class="flex gap-2 items-center">
                    <Input 
                      placeholder="原字段名" 
                      :model-value="col.original"
                      class="h-8 text-xs flex-1"
                      @update:model-value="(v) => updateOutputColumn(index as number, 'original', v)"
                    />
                    <span class="text-muted-foreground text-xs">→</span>
                    <Input 
                      placeholder="新字段名" 
                      :model-value="col.target"
                      class="h-8 text-xs flex-1"
                      @update:model-value="(v) => updateOutputColumn(index as number, 'target', v)"
                    />
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      class="h-8 w-8 text-muted-foreground hover:text-destructive"
                      @click="removeOutputColumn(index as number)"
                    >
                      <Trash2 class="w-3 h-3" />
                    </Button>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    class="w-full text-xs h-8 border-dashed text-muted-foreground hover:text-primary hover:border-primary/50"
                    @click="addOutputColumn"
                  >
                    + 添加字段重命名规则
                  </Button>
                </div>
              </div>
             
             <div class="space-y-2 pt-2">
               <div class="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    id="drop_extra" 
                    class="rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
                    :checked="node.data?.config?.drop_extra_columns"
                    @change="(e) => updateConfig('drop_extra_columns', (e.target as HTMLInputElement).checked)"
                  />
                  <Label for="drop_extra" class="text-xs font-normal cursor-pointer">
                    仅输出映射字段 (Drop Extra Columns)
                    <span class="block text-[10px] text-muted-foreground font-normal mt-0.5">
                      勾选后，未在上方定义的字段将被丢弃，仅输出重命名的字段。
                    </span>
                  </Label>
               </div>
             </div>
           </div>
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