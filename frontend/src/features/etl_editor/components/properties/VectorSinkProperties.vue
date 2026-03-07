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
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Database, 
  FolderInput, 
  AlertCircle, 
  ArrowRightLeft, 
  Tags,
  Plus,
  Trash2,
  FileText
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const loading = ref(false);
const connections = ref<any[]>([]);
const activeTab = ref('basic');

const fetchConnections = async () => {
  loading.value = true;
  try {
    connections.value = await pipelineApi.getSystemConnections('vector');
  } catch (e) {
    console.error('Failed to fetch vector connections', e);
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

// --- Metadata Logic ---
const newMetaField = ref('');
const addMetaField = () => {
  if (!newMetaField.value) return;
  const current = config.value.metadata_fields || [];
  if (!current.includes(newMetaField.value)) {
    updateConfig('metadata_fields', [...current, newMetaField.value]);
  }
  newMetaField.value = '';
};
const removeMetaField = (index: number) => {
  const current = [...(config.value.metadata_fields || [])];
  current.splice(index, 1);
  updateConfig('metadata_fields', current);
};
</script>

<template>
  <div class="flex flex-col w-full min-h-[500px] bg-background/50 border rounded-lg overflow-hidden">
    <Tabs v-model="activeTab" class="flex-1 flex flex-col min-h-0">
      <div class="px-4 pt-2 border-b bg-muted/20 shrink-0">
        <TabsList class="grid w-full grid-cols-2">
          <TabsTrigger value="basic" class="flex items-center gap-2">
            <Database class="w-3.5 h-3.5" />
            基础配置
          </TabsTrigger>
          <TabsTrigger value="mapping" class="flex items-center gap-2">
            <ArrowRightLeft class="w-3.5 h-3.5" />
            字段映射
          </TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea class="flex-1">
        <div class="p-4 space-y-6">
          
          <!-- Basic Config -->
          <TabsContent value="basic" class="mt-0 space-y-4">
            <div class="space-y-2">
              <Label class="flex items-center gap-1.5">
                <Database class="w-3.5 h-3.5 text-blue-500" />
                选择向量库连接 (Connection)
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
                系统未配置可用的向量库连接。
              </div>
            </div>

            <div class="space-y-2">
              <Label class="flex items-center gap-1.5">
                <FolderInput class="w-3.5 h-3.5 text-muted-foreground" />
                集合/索引名称 (Collection/Index)
              </Label>
              <Input 
                :model-value="config.collection_name || 'vectors'"
                @update:model-value="(v) => updateConfig('collection_name', v)"
                placeholder="vectors"
              />
              <p class="text-[10px] text-muted-foreground">存储向量数据的集合名称。</p>
            </div>

            <div class="space-y-2">
              <Label>相似度度量 (Metric Type)</Label>
              <Select 
                :model-value="config.metric_type || 'cosine'"
                @update:model-value="(v) => updateConfig('metric_type', v)"
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cosine">余弦相似度 (Cosine)</SelectItem>
                  <SelectItem value="l2">欧氏距离 (L2)</SelectItem>
                  <SelectItem value="ip">内积 (Inner Product)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>

          <!-- Mapping Config -->
          <TabsContent value="mapping" class="mt-0 space-y-6">
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">核心字段</CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="space-y-2">
                  <Label class="flex items-center gap-1.5">
                    <FileText class="w-3.5 h-3.5 text-muted-foreground" />
                    文本内容字段 (Content Field)
                  </Label>
                  <Input 
                    :model-value="config.content_field || 'text'"
                    @update:model-value="(v) => updateConfig('content_field', v)"
                    placeholder="text" 
                  />
                  <p class="text-[10px] text-muted-foreground">用于全文检索的原始内容字段。</p>
                </div>

                <div class="space-y-2">
                  <Label class="flex items-center gap-1.5">
                    <div class="w-3.5 h-3.5 rounded-full border border-current flex items-center justify-center text-[8px] font-bold">V</div>
                    向量字段 (Vector Field)
                  </Label>
                  <Input 
                    :model-value="config.vector_field || 'embedding'"
                    @update:model-value="(v) => updateConfig('vector_field', v)"
                    placeholder="embedding" 
                  />
                  <p class="text-[10px] text-muted-foreground">存储 Embedding 向量值的字段。</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">元数据字段 (Metadata)</CardTitle>
                <CardDescription class="text-xs">
                  选择需要随向量一起存储的附加字段（用于混合检索过滤）。
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-3">
                <div class="flex gap-2">
                  <Input 
                    v-model="newMetaField" 
                    placeholder="输入字段名 (e.g. source_url)" 
                    class="h-8 text-xs" 
                    @keyup.enter="addMetaField" 
                  />
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addMetaField">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>
                <div class="flex flex-wrap gap-2 min-h-[2rem]">
                  <Badge 
                    v-for="(field, idx) in (config.metadata_fields || [])" 
                    :key="idx" 
                    variant="outline" 
                    class="pr-1 gap-1"
                  >
                    {{ field }}
                    <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive" @click="removeMetaField(idx)" />
                  </Badge>
                  <span v-if="!(config.metadata_fields?.length)" class="text-xs text-muted-foreground italic">
                    暂无元数据字段
                  </span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </div>
      </ScrollArea>
    </Tabs>
  </div>
</template>
