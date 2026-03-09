<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { dataSourceApi, type DataSource } from '@/features/data_etl/api';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Database, 
  Table, 
  AlertCircle, 
  Settings2, 
  ArrowRightLeft, 
  Plus, 
  Trash2,
  Key
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const dataSources = ref<DataSource[]>([]);
const loading = ref(false);
const activeTab = ref('basic');

const fetchDataSources = async () => {
  loading.value = true;
  try {
    dataSources.value = await dataSourceApi.list();
  } catch (e) {
    console.error('Failed to fetch data sources', e);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchDataSources);

const availableDataSources = computed(() => {
  if (!node.value) return [];
  // Allow selecting any structured database connection
  // In a real app, we might check against a list of supported sink types or metadata
  const structuredDbTypes = ['clickhouse', 'postgres', 'mysql', 'database', 'generic_sql'];
  return dataSources.value.filter(ds => structuredDbTypes.includes(ds.type) || ds.type === node.value?.data?.subType);
});

const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

const config = computed(() => node.value?.data?.config || {});
const mappings = computed(() => config.value.field_mappings || []);

// --- Mapping Logic ---
const newSourceField = ref('');
const newTargetColumn = ref('');

const addMapping = () => {
  if (!newSourceField.value || !newTargetColumn.value) return;
  const current = [...mappings.value];
  current.push({ source: newSourceField.value, target: newTargetColumn.value });
  updateConfig('field_mappings', current);
  newSourceField.value = '';
  newTargetColumn.value = '';
};

const removeMapping = (index: number) => {
  const current = [...mappings.value];
  current.splice(index, 1);
  updateConfig('field_mappings', current);
};

// --- Upsert Keys Logic ---
const newKeyField = ref('');
const addKeyField = () => {
  if (!newKeyField.value) return;
  const current = config.value.upsert_keys || [];
  if (!current.includes(newKeyField.value)) {
    updateConfig('upsert_keys', [...current, newKeyField.value]);
  }
  newKeyField.value = '';
};
const removeKeyField = (index: number) => {
  const current = [...(config.value.upsert_keys || [])];
  current.splice(index, 1);
  updateConfig('upsert_keys', current);
};
</script>

<template>
  <div class="flex flex-col w-full min-h-[500px] bg-background/50 border rounded-lg overflow-hidden">
    <Tabs v-model="activeTab" class="flex-1 flex flex-col min-h-0">
      <div class="px-4 pt-2 border-b bg-muted/20 shrink-0">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="basic" class="flex items-center gap-2">
            <Database class="w-3.5 h-3.5" />
            基础配置
          </TabsTrigger>
          <TabsTrigger value="mapping" class="flex items-center gap-2">
            <ArrowRightLeft class="w-3.5 h-3.5" />
            字段映射
          </TabsTrigger>
          <TabsTrigger value="advanced" class="flex items-center gap-2">
            <Settings2 class="w-3.5 h-3.5" />
            高级设置
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
                选择数据连接 (Connection)
              </Label>
              <Select 
                :model-value="config.data_source_id?.toString()"
                @update:model-value="(v) => updateConfig('data_source_id', parseInt(v))"
                :disabled="loading"
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择目标数据库..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
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
              
              <div v-if="!loading && availableDataSources.length === 0" class="flex items-center gap-1.5 text-xs text-muted-foreground p-2 bg-muted/30 rounded-md">
                <AlertCircle class="w-3.5 h-3.5 text-yellow-500" />
                未找到相关连接，请先在数据源管理中创建。
              </div>
            </div>

            <div class="space-y-2">
              <Label class="flex items-center gap-1.5">
                <Table class="w-3.5 h-3.5 text-muted-foreground" />
                目标表 (Target Table)
              </Label>
              <Input 
                :model-value="config.table"
                @update:model-value="(v) => updateConfig('table', v)"
                placeholder="e.g. analytical_results"
              />
              <p class="text-[10px] text-muted-foreground">数据将被写入此表，如果不存在可能会自动创建。</p>
            </div>

            <div class="space-y-2">
              <Label>写入模式 (Write Mode)</Label>
              <Select 
                :model-value="config.write_mode || 'append'"
                @update:model-value="(v) => updateConfig('write_mode', v)"
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="append">追加 (Append) - 保留现有数据</SelectItem>
                  <SelectItem value="overwrite">覆盖 (Overwrite) - 清空表后写入</SelectItem>
                  <SelectItem value="upsert">更新插入 (Upsert) - 按主键更新</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Upsert Keys (Only visible for upsert) -->
            <div v-if="config.write_mode === 'upsert'" class="space-y-3 pt-2 border-t">
              <Label class="text-xs flex items-center gap-1">
                <Key class="w-3 h-3 text-yellow-600" />
                业务主键 (Primary Keys)
              </Label>
              <div class="flex gap-2">
                <Input 
                  v-model="newKeyField" 
                  placeholder="输入主键字段 (e.g. id)" 
                  class="h-8 text-xs" 
                  @keyup.enter="addKeyField" 
                />
                <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addKeyField">
                  <Plus class="w-4 h-4" />
                </Button>
              </div>
              <div class="flex flex-wrap gap-2">
                <Badge 
                  v-for="(key, idx) in (config.upsert_keys || [])" 
                  :key="idx" 
                  variant="outline" 
                  class="pr-1 gap-1"
                >
                  {{ key }}
                  <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive" @click="removeKeyField(Number(idx))" />
                </Badge>
              </div>
            </div>
          </TabsContent>

          <!-- Field Mapping -->
          <TabsContent value="mapping" class="mt-0 space-y-4">
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">字段映射关系</CardTitle>
                <CardDescription class="text-xs">
                  将上游字段映射到数据库列名。留空则默认按同名映射。
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="flex gap-2 items-end">
                  <div class="space-y-1 flex-1">
                    <Label class="text-[10px] text-muted-foreground">上游字段</Label>
                    <Input v-model="newSourceField" placeholder="source_field" class="h-8 text-xs" />
                  </div>
                  <ArrowRightLeft class="w-4 h-4 mb-2 text-muted-foreground" />
                  <div class="space-y-1 flex-1">
                    <Label class="text-[10px] text-muted-foreground">数据库列</Label>
                    <Input v-model="newTargetColumn" placeholder="target_column" class="h-8 text-xs" />
                  </div>
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addMapping">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>

                <div class="space-y-2">
                  <div 
                    v-for="(map, idx) in mappings" 
                    :key="idx"
                    class="flex items-center justify-between p-2 rounded-md border bg-muted/10 text-xs"
                  >
                    <div class="flex items-center gap-2 flex-1">
                      <span class="font-mono text-muted-foreground">{{ map.source }}</span>
                      <ArrowRightLeft class="w-3 h-3 text-muted-foreground/50" />
                      <span class="font-bold text-primary">{{ map.target }}</span>
                    </div>
                    <Trash2 
                      class="w-3.5 h-3.5 cursor-pointer text-muted-foreground hover:text-destructive transition-colors" 
                      @click="removeMapping(Number(idx))" 
                    />
                  </div>
                  <div v-if="!mappings.length" class="text-center py-4 text-xs text-muted-foreground bg-muted/5 rounded border border-dashed">
                    未配置映射，将使用自动同名匹配
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <!-- Advanced Settings -->
          <TabsContent value="advanced" class="mt-0 space-y-4">
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label>批量大小 (Batch Size)</Label>
                  <Input 
                    type="number" 
                    :model-value="config.batch_size || 1000"
                    @update:model-value="(v) => updateConfig('batch_size', parseInt(v as string))"
                  />
                </div>
                <div class="space-y-2">
                  <Label>最大重试 (Max Retries)</Label>
                  <Input 
                    type="number" 
                    :model-value="config.max_retries || 3"
                    @update:model-value="(v) => updateConfig('max_retries', parseInt(v as string))"
                  />
                </div>
              </div>

              <div class="space-y-2 pt-2 border-t">
                <Label>写入前执行 SQL (Pre-execution)</Label>
                <Input 
                  :model-value="config.pre_sql"
                  @update:model-value="(v) => updateConfig('pre_sql', v)"
                  placeholder="e.g. TRUNCATE TABLE temp_table"
                  class="font-mono text-xs"
                />
                <p class="text-[10px] text-muted-foreground">在数据写入开始前执行的 SQL 语句。</p>
              </div>

              <div class="space-y-2">
                <Label>写入后执行 SQL (Post-execution)</Label>
                <Input 
                  :model-value="config.post_sql"
                  @update:model-value="(v) => updateConfig('post_sql', v)"
                  placeholder="e.g. UPDATE status_table SET updated = NOW()"
                  class="font-mono text-xs"
                />
                <p class="text-[10px] text-muted-foreground">在数据写入完成后执行的 SQL 语句。</p>
              </div>

              <div class="flex items-center justify-between pt-2 border-t">
                <div class="space-y-0.5">
                  <Label class="text-sm">失败时继续 (Continue on Error)</Label>
                  <p class="text-xs text-muted-foreground">遇到写入错误时忽略并继续处理下一批次</p>
                </div>
                <Switch 
                  :checked="config.continue_on_error ?? false" 
                  @update:checked="(v) => updateConfig('continue_on_error', v)" 
                />
              </div>
            </div>
          </TabsContent>
        </div>
      </ScrollArea>
    </Tabs>
  </div>
</template>
