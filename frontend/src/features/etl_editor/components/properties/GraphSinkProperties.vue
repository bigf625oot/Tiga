<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { dataSourceApi, type DataSource } from '@/features/data_etl/api';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Network, 
  FolderInput, 
  AlertCircle, 
  ArrowRightLeft, 
  CircleDot,
  ArrowRight,
  Plus,
  Trash2,
  Check,
  ChevronsUpDown
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const loading = ref(false);
const connections = ref<DataSource[]>([]);
const activeTab = ref('basic');

const getDataSourceDedupKey = (ds: DataSource) => {
  const url = ds.url?.trim();
  if (url) return `${ds.type}|${url}|${ds.username ?? ''}|${ds.database ?? ''}`;
  const host = ds.host?.trim() ?? '';
  const port = ds.port ?? '';
  return `${ds.type}|${host}|${port}|${ds.username ?? ''}|${ds.database ?? ''}|${ds.name}`;
};

const fetchConnections = async () => {
  loading.value = true;
  try {
    const dataSources = await dataSourceApi.list();
    const neo4jConnections = dataSources.filter(ds => ds.type === 'neo4j');
    const uniq = new Map<string, DataSource>();
    for (const ds of neo4jConnections) {
      const key = getDataSourceDedupKey(ds);
      if (!uniq.has(key)) uniq.set(key, ds);
    }
    connections.value = Array.from(uniq.values());
  } catch (e) {
    console.error('Failed to fetch graph connections', e);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchConnections);

const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

const config = computed(() => node.value?.data?.config || {});
const nodeMappings = computed(() => config.value.node_mappings || []);
const edgeMappings = computed(() => config.value.edge_mappings || []);

const graphDatabases = ref<string[]>([]);
const fetchingDatabases = ref(false);

const openGraphNamePopover = ref(false);
const graphNameSearchTerm = ref('');

const fetchGraphDatabases = async (connectionId?: number) => {
  if (!connectionId) {
    graphDatabases.value = [];
    return;
  }
  fetchingDatabases.value = true;
  try {
    const meta = await dataSourceApi.fetchMetadata(connectionId);
    graphDatabases.value = meta
      .filter((m: any) => m.type === 'database')
      .map((m: any) => m.name);
  } catch (e) {
    console.error('Failed to fetch graph databases', e);
    graphDatabases.value = [];
  } finally {
    fetchingDatabases.value = false;
  }
};

watch(() => config.value.connection_id, async (newId, oldId) => {
  await fetchGraphDatabases(newId);
  if (oldId !== undefined && graphDatabases.value.length > 0 && !graphDatabases.value.includes(config.value.graph_name)) {
    updateConfig('graph_name', graphDatabases.value[0]);
  }
}, { immediate: true });

// --- Node Mapping Logic ---
const newNodeLabel = ref('');
const newNodeIdField = ref('');

const addNodeMapping = () => {
  if (!newNodeLabel.value || !newNodeIdField.value) return;
  const current = [...nodeMappings.value];
  current.push({ label: newNodeLabel.value, id_field: newNodeIdField.value });
  updateConfig('node_mappings', current);
  newNodeLabel.value = '';
  newNodeIdField.value = '';
};

const removeNodeMapping = (index: number) => {
  const current = [...nodeMappings.value];
  current.splice(index, 1);
  updateConfig('node_mappings', current);
};

// --- Edge Mapping Logic ---
const newEdgeType = ref('');
const newSourceField = ref('');
const newTargetField = ref('');

const addEdgeMapping = () => {
  if (!newEdgeType.value || !newSourceField.value || !newTargetField.value) return;
  const current = [...edgeMappings.value];
  current.push({ 
    type: newEdgeType.value, 
    source_field: newSourceField.value, 
    target_field: newTargetField.value 
  });
  updateConfig('edge_mappings', current);
  newEdgeType.value = '';
  newSourceField.value = '';
  newTargetField.value = '';
};

const removeEdgeMapping = (index: number) => {
  const current = [...edgeMappings.value];
  current.splice(index, 1);
  updateConfig('edge_mappings', current);
};
</script>

<template>
  <div class="flex flex-col w-full min-h-[500px] bg-background/50 border rounded-lg overflow-hidden">
    <Tabs v-model="activeTab" class="flex-1 flex flex-col min-h-0">
      <div class="px-4 pt-2 border-b bg-muted/20 shrink-0">
        <TabsList class="grid w-full grid-cols-2">
          <TabsTrigger value="basic" class="flex items-center gap-2">
            <Network class="w-3.5 h-3.5" />
            基础配置
          </TabsTrigger>
          <TabsTrigger value="mapping" class="flex items-center gap-2">
            <ArrowRightLeft class="w-3.5 h-3.5" />
            图谱映射
          </TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea class="flex-1">
        <div class="p-4 space-y-6">
          
          <!-- Basic Config -->
          <TabsContent value="basic" class="mt-0 space-y-4">
            <div class="space-y-2">
              <Label class="flex items-center gap-1.5">
                <Network class="w-3.5 h-3.5 text-blue-500" />
                选择图数据库连接 (Connection)
              </Label>
              <Select 
                :model-value="config.connection_id?.toString()"
                @update:model-value="(v) => updateConfig('connection_id', Number(v))"
                :disabled="loading"
              >
                <SelectTrigger>
                  <SelectValue placeholder="从系统配置中选择..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem 
                      v-for="conn in connections" 
                      :key="conn.id" 
                      :value="conn.id.toString()"
                    >
                      {{ conn.name }} ({{ conn.type }})
                    </SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
              <div v-if="!loading && connections.length === 0" class="flex items-center gap-1.5 text-xs text-muted-foreground p-2 bg-muted/30 rounded-md">
                <AlertCircle class="w-3.5 h-3.5 text-yellow-500" />
                系统未配置可用的图数据库连接。
              </div>
            </div>

            <div class="space-y-2">
              <Label class="flex items-center gap-1.5">
                <FolderInput class="w-3.5 h-3.5 text-muted-foreground" />
                目标图谱名称 (Graph Name)
              </Label>
              <Popover v-model:open="openGraphNamePopover">
                <PopoverTrigger as-child>
                  <Button
                    variant="outline"
                    role="combobox"
                    :aria-expanded="openGraphNamePopover"
                    class="w-full justify-between px-3 font-normal"
                    :disabled="fetchingDatabases"
                  >
                    <span class="truncate">{{ config.graph_name || 'default' }}</span>
                    <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="w-full p-0">
                  <Command v-model:searchTerm="graphNameSearchTerm">
                    <CommandInput placeholder="搜索或输入新的图谱名称..." />
                    <CommandEmpty>
                      <Button
                        variant="ghost"
                        class="w-full justify-start text-sm px-2 py-1.5 h-auto font-normal text-muted-foreground"
                        @click="() => {
                          updateConfig('graph_name', graphNameSearchTerm || 'default');
                          openGraphNamePopover = false;
                        }"
                      >
                        <Plus class="mr-2 h-4 w-4" />
                        创建 / 使用 "{{ graphNameSearchTerm }}"
                      </Button>
                    </CommandEmpty>
                    <CommandList>
                      <CommandGroup>
                        <CommandItem
                          v-for="db in graphDatabases"
                          :key="db"
                          :value="db"
                          @select="() => {
                            updateConfig('graph_name', db);
                            openGraphNamePopover = false;
                          }"
                        >
                          <Check
                            :class="['mr-2 h-4 w-4', config.graph_name === db ? 'opacity-100' : 'opacity-0']"
                          />
                          {{ db }}
                        </CommandItem>
                        <CommandItem
                          v-if="graphNameSearchTerm && !graphDatabases.includes(graphNameSearchTerm)"
                          :value="graphNameSearchTerm"
                          @select="() => {
                            updateConfig('graph_name', graphNameSearchTerm);
                            openGraphNamePopover = false;
                          }"
                        >
                          <Plus class="mr-2 h-4 w-4 text-muted-foreground" />
                          创建 / 使用 "{{ graphNameSearchTerm }}"
                        </CommandItem>
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
              <p class="text-[10px] text-muted-foreground">
                <span v-if="fetchingDatabases" class="text-blue-500 mr-1">正在加载可用图谱...</span>
                如果目标支持多图谱，请选择或指定名称。
              </p>
            </div>

            <div class="space-y-2">
              <Label>写入批次大小 (Batch Size)</Label>
              <Input 
                type="number"
                :model-value="config.batch_size || 1000"
                @update:model-value="(v) => updateConfig('batch_size', parseInt(v as string))"
                placeholder="1000"
              />
            </div>
          </TabsContent>

          <!-- Mapping Config -->
          <TabsContent value="mapping" class="mt-0 space-y-6">
            <!-- Node Mappings -->
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">节点映射 (Nodes)</CardTitle>
                <CardDescription class="text-xs">
                  定义如何从数据中提取节点。
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="flex gap-2 items-end">
                  <div class="space-y-1 flex-1">
                    <Label class="text-[10px] text-muted-foreground">节点标签 (Label)</Label>
                    <Input v-model="newNodeLabel" placeholder="e.g. Person" class="h-8 text-xs" />
                  </div>
                  <div class="space-y-1 flex-1">
                    <Label class="text-[10px] text-muted-foreground">ID 字段</Label>
                    <Input v-model="newNodeIdField" placeholder="e.g. user_id" class="h-8 text-xs" />
                  </div>
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addNodeMapping">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>

                <div class="space-y-2">
                  <div 
                    v-for="(map, idx) in nodeMappings" 
                    :key="idx"
                    class="flex items-center justify-between p-2 rounded-md border bg-muted/10 text-xs"
                  >
                    <div class="flex items-center gap-2">
                      <CircleDot class="w-3.5 h-3.5 text-blue-500" />
                      <span class="font-bold">{{ map.label }}</span>
                      <span class="text-muted-foreground">from</span>
                      <span class="font-mono bg-background px-1 rounded">{{ map.id_field }}</span>
                    </div>
                    <Trash2 
                      class="w-3.5 h-3.5 cursor-pointer text-muted-foreground hover:text-destructive transition-colors" 
                      @click="removeNodeMapping(Number(idx))" 
                    />
                  </div>
                  <div v-if="!nodeMappings.length" class="text-center py-4 text-xs text-muted-foreground bg-muted/5 rounded border border-dashed">
                    暂无节点映射
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Edge Mappings -->
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">关系映射 (Relationships)</CardTitle>
                <CardDescription class="text-xs">
                  定义节点之间的连接关系。
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="grid grid-cols-3 gap-2 items-end">
                  <div class="space-y-1">
                    <Label class="text-[10px] text-muted-foreground">起始节点 ID</Label>
                    <Input v-model="newSourceField" placeholder="source_id" class="h-8 text-xs" />
                  </div>
                  <div class="space-y-1">
                    <Label class="text-[10px] text-muted-foreground">关系类型</Label>
                    <Input v-model="newEdgeType" placeholder="KNOWS" class="h-8 text-xs" />
                  </div>
                  <div class="space-y-1">
                    <Label class="text-[10px] text-muted-foreground">目标节点 ID</Label>
                    <Input v-model="newTargetField" placeholder="target_id" class="h-8 text-xs" />
                  </div>
                </div>
                <Button size="sm" variant="secondary" class="w-full h-7 text-xs mt-2" @click="addEdgeMapping">
                  <Plus class="w-3.5 h-3.5 mr-1.5" />
                  添加关系
                </Button>

                <div class="space-y-2 mt-3">
                  <div 
                    v-for="(map, idx) in edgeMappings" 
                    :key="idx"
                    class="flex items-center justify-between p-2 rounded-md border bg-muted/10 text-xs"
                  >
                    <div class="flex items-center gap-1.5 flex-1 min-w-0">
                      <span class="font-mono truncate max-w-[30%]">{{ map.source_field }}</span>
                      <ArrowRight class="w-3 h-3 text-muted-foreground/50 shrink-0" />
                      <span class="font-bold text-primary truncate max-w-[30%] text-center px-1">[:{{ map.type }}]</span>
                      <ArrowRight class="w-3 h-3 text-muted-foreground/50 shrink-0" />
                      <span class="font-mono truncate max-w-[30%]">{{ map.target_field }}</span>
                    </div>
                    <Trash2 
                      class="w-3.5 h-3.5 cursor-pointer text-muted-foreground hover:text-destructive transition-colors shrink-0 ml-2" 
                      @click="removeEdgeMapping(Number(idx))" 
                    />
                  </div>
                  <div v-if="!edgeMappings.length" class="text-center py-4 text-xs text-muted-foreground bg-muted/5 rounded border border-dashed">
                    暂无关系映射
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </div>
      </ScrollArea>
    </Tabs>
  </div>
</template>
