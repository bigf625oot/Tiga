<script setup lang="ts">
import { computed, ref } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Plus, 
  Trash2, 
  Group, 
  Layers, 
  Clock, 
  Sigma,
  AlertCircle
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const activeTab = ref('grouping');

// --- Helpers ---
const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

const config = computed(() => node.value?.data?.config || {});

// --- Group By Management ---
const newGroupField = ref('');
const addGroupField = () => {
  const val = newGroupField.value.trim();
  if (!val) return;
  const current = config.value.group_by || [];
  if (!current.includes(val)) {
    updateConfig('group_by', [...current, val]);
  }
  newGroupField.value = '';
};
const removeGroupField = (index: number | string) => {
  const current = [...(config.value.group_by || [])];
  current.splice(Number(index), 1);
  updateConfig('group_by', current);
};

// --- Aggregations Management ---
const newAggField = ref('');
const newAggFunc = ref('count');
const addAggregation = () => {
  const field = newAggField.value.trim();
  const func = newAggFunc.value;
  if (!field && func !== 'count') return; // Count can be *
  
  const current = config.value.aggregations || [];
  // Check duplicate
  if (!current.some((a: any) => a.field === field && a.function === func)) {
    updateConfig('aggregations', [...current, { field: field || '*', function: func }]);
  }
  newAggField.value = '';
};
const removeAggregation = (index: number | string) => {
  const current = [...(config.value.aggregations || [])];
  current.splice(Number(index), 1);
  updateConfig('aggregations', current);
};

// --- Window Config ---
const windowType = computed({
  get: () => config.value.window_type || 'tumbling',
  set: (v) => updateConfig('window_type', v)
});

// --- Validation ---
const validationErrors = computed(() => {
  const errors: string[] = [];
  if (!config.value.group_by?.length && !config.value.aggregations?.length) {
    errors.push('请至少配置分组字段或聚合函数');
  }
  if (config.value.window_type !== 'none' && !config.value.window_size) {
    errors.push('窗口大小不能为空');
  }
  return errors;
});
</script>

<template>
  <div class="flex flex-col w-full min-h-[500px] bg-background/50 border rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b bg-muted/20">
      <div class="flex items-center gap-2">
        <div class="p-1.5 bg-primary/10 rounded-md">
          <Sigma class="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 class="text-sm font-medium">聚合计算</h3>
          <p class="text-[10px] text-muted-foreground">配置数据分组、窗口及聚合逻辑</p>
        </div>
      </div>
    </div>

    <!-- Main Config Tabs -->
    <Tabs v-model="activeTab" class="flex-1 flex flex-col min-h-0">
      <div class="px-4 pt-2 border-b bg-background shrink-0">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="grouping" class="flex items-center gap-2">
            <Group class="w-3.5 h-3.5" />
            分组
          </TabsTrigger>
          <TabsTrigger value="aggregation" class="flex items-center gap-2">
            <Sigma class="w-3.5 h-3.5" />
            聚合
          </TabsTrigger>
          <TabsTrigger value="window" class="flex items-center gap-2">
            <Clock class="w-3.5 h-3.5" />
            窗口
          </TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea class="flex-1">
        <div class="p-4 space-y-6">
          
          <!-- Tab 1: Group By -->
          <TabsContent value="grouping" class="mt-0 space-y-4">
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">分组字段 (Group By)</CardTitle>
                <CardDescription class="text-xs">添加用于数据分组的字段名称</CardDescription>
              </CardHeader>
              <CardContent class="space-y-3">
                <div class="flex gap-2">
                  <Input 
                    v-model="newGroupField" 
                    placeholder="输入字段名 (e.g. user_id)" 
                    class="h-8 text-xs" 
                    @keyup.enter="addGroupField" 
                  />
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addGroupField">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>
                <div class="flex flex-wrap gap-2 min-h-[2rem]">
                  <Badge 
                    v-for="(field, idx) in (config.group_by || [])" 
                    :key="idx"
                    variant="outline"
                    class="bg-background pr-1 gap-1 group hover:border-destructive/50 transition-colors"
                  >
                    {{ field }}
                    <Trash2 
                      class="w-3 h-3 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors" 
                      @click="removeGroupField(idx)" 
                    />
                  </Badge>
                  <span v-if="!(config.group_by?.length)" class="text-xs text-muted-foreground italic">
                    暂无分组字段 (将对全局数据聚合)
                  </span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <!-- Tab 2: Aggregations -->
          <TabsContent value="aggregation" class="mt-0 space-y-4">
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium">聚合函数 (Functions)</CardTitle>
                <CardDescription class="text-xs">定义字段的聚合计算方式</CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="flex gap-2 items-end">
                  <div class="space-y-1 flex-1">
                    <Label class="text-[10px] text-muted-foreground">函数</Label>
                    <Select v-model="newAggFunc">
                      <SelectTrigger class="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="count">计数 (Count)</SelectItem>
                        <SelectItem value="sum">求和 (Sum)</SelectItem>
                        <SelectItem value="avg">平均值 (Avg)</SelectItem>
                        <SelectItem value="max">最大值 (Max)</SelectItem>
                        <SelectItem value="min">最小值 (Min)</SelectItem>
                        <SelectItem value="first">首个 (First)</SelectItem>
                        <SelectItem value="last">最新 (Last)</SelectItem>
                        <SelectItem value="collect_list">列表 (List)</SelectItem>
                        <SelectItem value="collect_set">去重集合 (Set)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div class="space-y-1 flex-[1.5]">
                    <Label class="text-[10px] text-muted-foreground">字段</Label>
                    <Input 
                      v-model="newAggField" 
                      :placeholder="newAggFunc === 'count' ? '*' : 'e.g. price'" 
                      class="h-8 text-xs" 
                      @keyup.enter="addAggregation"
                    />
                  </div>
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addAggregation">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>

                <div class="space-y-2">
                  <div 
                    v-for="(agg, idx) in (config.aggregations || [])" 
                    :key="idx"
                    class="flex items-center justify-between p-2 rounded-md border bg-muted/10 text-xs"
                  >
                    <div class="flex items-center gap-2">
                      <Badge variant="secondary" class="text-[10px] uppercase">{{ agg.function }}</Badge>
                      <span class="font-mono text-muted-foreground">{{ agg.field }}</span>
                    </div>
                    <Trash2 
                      class="w-3.5 h-3.5 cursor-pointer text-muted-foreground hover:text-destructive transition-colors" 
                      @click="removeAggregation(idx)" 
                    />
                  </div>
                  <div v-if="!(config.aggregations?.length)" class="text-center py-4 text-xs text-muted-foreground">
                    暂无聚合配置
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <!-- Tab 3: Windowing -->
          <TabsContent value="window" class="mt-0 space-y-4">
            <div class="space-y-4">
              <div class="space-y-2">
                <Label>窗口类型 (Window Type)</Label>
                <Select v-model="windowType">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无窗口 (Global)</SelectItem>
                    <SelectItem value="tumbling">滚动窗口 (Tumbling)</SelectItem>
                    <SelectItem value="sliding">滑动窗口 (Sliding)</SelectItem>
                    <SelectItem value="session">会话窗口 (Session)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <template v-if="windowType !== 'none'">
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label>窗口大小 (Size)</Label>
                    <div class="relative">
                      <Input 
                        type="number" 
                        :model-value="config.window_size" 
                        @update:model-value="(v) => updateConfig('window_size', parseInt(v as string))"
                        placeholder="60"
                      />
                      <span class="absolute right-3 top-2.5 text-xs text-muted-foreground">秒</span>
                    </div>
                  </div>
                  
                  <div class="space-y-2" v-if="windowType === 'sliding'">
                    <Label>滑动步长 (Slide)</Label>
                    <div class="relative">
                      <Input 
                        type="number" 
                        :model-value="config.window_slide" 
                        @update:model-value="(v) => updateConfig('window_slide', parseInt(v as string))"
                        placeholder="10"
                      />
                      <span class="absolute right-3 top-2.5 text-xs text-muted-foreground">秒</span>
                    </div>
                  </div>
                </div>

                <div class="space-y-2">
                  <Label>时间戳字段 (Timestamp Field)</Label>
                  <Input 
                    :model-value="config.timestamp_field ?? 'timestamp'" 
                    @update:model-value="(v) => updateConfig('timestamp_field', v)"
                    placeholder="默认为处理时间 (Processing Time)"
                  />
                </div>
                
                <div class="flex items-center justify-between pt-2 border-t mt-2">
                  <div class="space-y-0.5">
                    <Label class="text-xs">允许迟到数据</Label>
                    <p class="text-[10px] text-muted-foreground">处理窗口关闭后到达的数据</p>
                  </div>
                  <Switch 
                    :checked="config.allow_late_data ?? false" 
                    @update:checked="(v) => updateConfig('allow_late_data', v)" 
                  />
                </div>
              </template>
              
              <div v-else class="p-4 rounded-md bg-muted text-xs text-muted-foreground text-center">
                全量聚合模式：对流数据将持续累积状态，对批数据将一次性计算所有结果。
              </div>
            </div>
          </TabsContent>
        </div>
      </ScrollArea>

      <!-- Footer Validation -->
      <div v-if="validationErrors.length" class="p-3 border-t bg-destructive/10 text-destructive text-xs">
        <div class="flex items-center gap-2 font-medium mb-1">
          <AlertCircle class="w-4 h-4" />
          配置错误
        </div>
        <ul class="list-disc list-inside pl-1 opacity-90">
          <li v-for="err in validationErrors" :key="err">{{ err }}</li>
        </ul>
      </div>
    </Tabs>
  </div>
</template>
