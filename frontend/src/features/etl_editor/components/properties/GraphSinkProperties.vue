<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { pipelineApi } from '@/features/etl_editor/api/pipeline';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  Trash2
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const loading = ref(false);
const connections = ref<any[]>([]);
const activeTab = ref('basic');

const fetchConnections = async () => {
  loading.value = true;
  try {
    connections.value = await pipelineApi.getSystemConnections('graph');
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
                @update:model-value="(v) => updateConfig('connection_id', v)"
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
                      :value="conn.id"
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
              <Input 
                :model-value="config.graph_name || 'default'"
                @update:model-value="(v) => updateConfig('graph_name', v)"
                placeholder="default"
              />
              <p class="text-[10px] text-muted-foreground">如果目标支持多图谱，请指定名称。</p>
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
