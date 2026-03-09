<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { llmApi, type Model } from '../../api/llm';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Plus, 
  Trash2, 
  Network, 
  Settings, 
  Braces, 
  BrainCircuit, 
  Link,
  Users,
  AlertCircle
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const availableModels = ref<Model[]>([]);
const activeTab = ref('ontology');

// --- Helpers ---
const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

const config = computed(() => node.value?.data?.config || {});

// --- Lifecycle ---
onMounted(async () => {
  try {
    const res = await llmApi.listModels();
    availableModels.value = res.filter(m => m.is_active && m.model_type !== 'embedding');
  } catch (e) {
    console.error('Failed to fetch LLM models', e);
  }
});

// --- Ontology Management ---

// Entity Types
const newEntityType = ref('');
const addEntityType = () => {
  const val = newEntityType.value.trim();
  if (!val) return;
  const current = config.value.entity_types || [];
  if (!current.includes(val)) {
    updateConfig('entity_types', [...current, val]);
  }
  newEntityType.value = '';
};
const removeEntityType = (index: number) => {
  const current = [...(config.value.entity_types || [])];
  current.splice(index, 1);
  updateConfig('entity_types', current);
};

// Relation Types
const newRelationType = ref('');
const addRelationType = () => {
  const val = newRelationType.value.trim();
  if (!val) return;
  const current = config.value.relation_types || [];
  if (!current.includes(val)) {
    updateConfig('relation_types', [...current, val]);
  }
  newRelationType.value = '';
};
const removeRelationType = (index: number) => {
  const current = [...(config.value.relation_types || [])];
  current.splice(index, 1);
  updateConfig('relation_types', current);
};

// Properties Extraction
const newProperty = ref('');
const addProperty = () => {
  const val = newProperty.value.trim();
  if (!val) return;
  const current = config.value.properties_to_extract || [];
  if (!current.includes(val)) {
    updateConfig('properties_to_extract', [...current, val]);
  }
  newProperty.value = '';
};
const removeProperty = (index: number) => {
  const current = [...(config.value.properties_to_extract || [])];
  current.splice(index, 1);
  updateConfig('properties_to_extract', current);
};

// --- Validation ---
const validationErrors = computed(() => {
  const errors: string[] = [];
  if (!config.value.model_id) errors.push('请选择提取模型');
  if (!config.value.entity_types?.length) errors.push('请至少定义一种实体类型');
  return errors;
});
</script>

<template>
  <div class="flex flex-col w-full min-h-[600px] bg-background/50 border rounded-lg overflow-hidden">
    <!-- Header / Model Select -->
    <div class="p-4 border-b bg-muted/20 space-y-3">
      <div class="space-y-1">
        <Label>提取模型 (Extraction Model)</Label>
        <Select 
          :model-value="config.model_id"
          @update:model-value="(v) => updateConfig('model_id', v)"
        >
          <SelectTrigger>
            <SelectValue placeholder="选择大语言模型..." />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem v-for="m in availableModels" :key="m.model_id" :value="m.model_id">
                {{ m.name }} ({{ m.provider }})
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>
    </div>

    <!-- Main Config Tabs -->
    <Tabs v-model="activeTab" class="flex-1 flex flex-col min-h-0">
      <div class="px-4 pt-2 border-b bg-background">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="ontology" class="flex items-center gap-2">
            <Network class="w-3.5 h-3.5" />
            本体定义
          </TabsTrigger>
          <TabsTrigger value="extraction" class="flex items-center gap-2">
            <BrainCircuit class="w-3.5 h-3.5" />
            抽取策略
          </TabsTrigger>
          <TabsTrigger value="advanced" class="flex items-center gap-2">
            <Settings class="w-3.5 h-3.5" />
            高级配置
          </TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea class="flex-1">
        <div class="p-4 space-y-6">
          
          <!-- Tab 1: Ontology (Schema) -->
          <TabsContent value="ontology" class="mt-0 space-y-6">
            <!-- Entities -->
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium flex items-center gap-2">
                  <Users class="w-4 h-4 text-primary" />
                  实体类型 (Entities)
                </CardTitle>
                <CardDescription class="text-xs">
                  定义需要从文本中识别的对象类型，如“Person”, “Organization”
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-3">
                <div class="flex gap-2">
                  <Input 
                    v-model="newEntityType" 
                    placeholder="输入实体类型并回车..." 
                    class="h-8 text-xs" 
                    @keyup.enter="addEntityType" 
                  />
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addEntityType">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>
                <div class="flex flex-wrap gap-2 min-h-[2rem]">
                  <Badge 
                    v-for="(type, idx) in (config.entity_types || [])" 
                    :key="idx"
                    variant="outline"
                    class="bg-background pr-1 gap-1 group hover:border-destructive/50 transition-colors"
                  >
                    {{ type }}
                    <Trash2 
                      class="w-3 h-3 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors" 
                      @click="removeEntityType(Number(idx))" 
                    />
                  </Badge>
                  <span v-if="!(config.entity_types?.length)" class="text-xs text-muted-foreground italic">
                    暂无实体类型
                  </span>
                </div>
              </CardContent>
            </Card>

            <!-- Relations -->
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium flex items-center gap-2">
                  <Link class="w-4 h-4 text-primary" />
                  关系类型 (Relations)
                </CardTitle>
                <CardDescription class="text-xs">
                  定义实体之间的连接关系，如“WORKS_FOR”, “LOCATED_IN”
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-3">
                <div class="flex gap-2">
                  <Input 
                    v-model="newRelationType" 
                    placeholder="输入关系类型并回车..." 
                    class="h-8 text-xs" 
                    @keyup.enter="addRelationType" 
                  />
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addRelationType">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>
                <div class="flex flex-wrap gap-2 min-h-[2rem]">
                  <Badge 
                    v-for="(type, idx) in (config.relation_types || [])" 
                    :key="idx"
                    variant="outline"
                    class="bg-background pr-1 gap-1 group hover:border-destructive/50 transition-colors"
                  >
                    {{ type }}
                    <Trash2 
                      class="w-3 h-3 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors" 
                      @click="removeRelationType(Number(idx))" 
                    />
                  </Badge>
                  <span v-if="!(config.relation_types?.length)" class="text-xs text-muted-foreground italic">
                    暂无关系类型
                  </span>
                </div>
              </CardContent>
            </Card>

             <!-- Properties -->
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium flex items-center gap-2">
                  <Braces class="w-4 h-4 text-primary" />
                  属性提取 (Properties)
                </CardTitle>
                <CardDescription class="text-xs">
                  定义需要为实体提取的特定属性字段，如“age”, “title”
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-3">
                <div class="flex gap-2">
                  <Input 
                    v-model="newProperty" 
                    placeholder="输入属性名称并回车..." 
                    class="h-8 text-xs" 
                    @keyup.enter="addProperty" 
                  />
                  <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addProperty">
                    <Plus class="w-4 h-4" />
                  </Button>
                </div>
                <div class="flex flex-wrap gap-2 min-h-[2rem]">
                   <Badge 
                    v-for="(prop, idx) in (config.properties_to_extract || [])" 
                    :key="idx"
                    variant="outline"
                    class="bg-background pr-1 gap-1 group hover:border-destructive/50 transition-colors"
                  >
                    {{ prop }}
                    <Trash2 
                      class="w-3 h-3 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors" 
                      @click="removeProperty(Number(idx))" 
                    />
                  </Badge>
                  <span v-if="!(config.properties_to_extract?.length)" class="text-xs text-muted-foreground italic">
                    暂无指定属性 (默认提取所有相关)
                  </span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <!-- Tab 2: Extraction Strategy -->
          <TabsContent value="extraction" class="mt-0 space-y-4">
            <div class="space-y-4 border rounded-md p-4 bg-background">
              <div class="flex items-center justify-between">
                <div class="space-y-0.5">
                  <Label class="text-sm">指代消解 (Coreference Resolution)</Label>
                  <p class="text-xs text-muted-foreground">自动解析代词（如"他"、"它"）所指代的实体</p>
                </div>
                <Switch 
                  :checked="config.coref_enabled ?? false" 
                  @update:checked="(v) => updateConfig('coref_enabled', v)" 
                />
              </div>
              
              <div class="flex items-center justify-between pt-4 border-t">
                <div class="space-y-0.5">
                  <Label class="text-sm">实体对齐 (Entity Resolution)</Label>
                  <p class="text-xs text-muted-foreground">合并具有相似名称的实体（如 "Google" 和 "Google Inc."）</p>
                </div>
                <Switch 
                  :checked="config.entity_resolution_enabled ?? false" 
                  @update:checked="(v) => updateConfig('entity_resolution_enabled', v)" 
                />
              </div>

              <div class="flex items-center justify-between pt-4 border-t">
                <div class="space-y-0.5">
                  <Label class="text-sm">严格模式 (Strict Schema)</Label>
                  <p class="text-xs text-muted-foreground">仅提取在本体中明确定义的实体和关系类型</p>
                </div>
                <Switch 
                  :checked="config.strict_mode ?? true" 
                  @update:checked="(v) => updateConfig('strict_mode', v)" 
                />
              </div>
            </div>

            <div class="space-y-2">
              <Label>最大递归深度 (Max Recursion Depth)</Label>
              <div class="pt-2 px-2">
                 <Select 
                    :model-value="config.max_depth?.toString() ?? '1'"
                    @update:model-value="(v) => updateConfig('max_depth', parseInt(v))"
                  >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">0 (仅顶层)</SelectItem>
                    <SelectItem value="1">1 (直接关联)</SelectItem>
                    <SelectItem value="2">2 (二级关联)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          <!-- Tab 3: Advanced / Prompt -->
          <TabsContent value="advanced" class="mt-0 space-y-4">
            <div class="space-y-2">
              <Label>系统提示词 (System Prompt Override)</Label>
              <p class="text-xs text-muted-foreground">自定义用于指导 LLM 进行提取的提示词。保留为空以使用默认策略。</p>
              <Textarea 
                placeholder="你是一个知识图谱提取专家..." 
                class="min-h-[200px] font-mono text-xs leading-relaxed"
                :model-value="config.custom_prompt"
                @update:model-value="(v) => updateConfig('custom_prompt', v)"
              />
            </div>

            <div class="space-y-2">
              <Label>示例 (Few-shot Examples)</Label>
              <p class="text-xs text-muted-foreground">提供 JSON 格式的示例以提高提取准确性。</p>
              <Textarea 
                placeholder='[{"text": "Apple released the iPhone.", "entities": [...]}]' 
                class="min-h-[150px] font-mono text-xs"
                :model-value="config.few_shot_examples"
                @update:model-value="(v) => updateConfig('few_shot_examples', v)"
              />
            </div>
          </TabsContent>
        </div>
      </ScrollArea>
      
      <!-- Footer Validation -->
      <div v-if="validationErrors.length" class="p-3 border-t bg-destructive/10 text-destructive text-xs">
        <div class="flex items-center gap-2 font-medium mb-1">
          <AlertCircle class="w-4 h-4" />
          配置不完整
        </div>
        <ul class="list-disc list-inside pl-1 opacity-90">
          <li v-for="err in validationErrors" :key="err">{{ err }}</li>
        </ul>
      </div>
    </Tabs>
  </div>
</template>
