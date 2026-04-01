<script setup lang="ts">
import { reactive, ref, computed, watch } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/toast/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { HelpCircle, Plus, Trash2, Users, Link, Braces, AlertCircle, CheckCircle2, Undo2, RotateCcw, LayoutGrid, Network, Database, ArrowRight, BookOpen, GitMerge, BrainCircuit } from 'lucide-vue-next';
import KnowledgeGraphPreview from './KnowledgeGraphPreview.vue';

const { toast } = useToast();

const defaultConfig = {
  entityTypes: ['人物', '组织', '地点', '产品', '事件'],
  relationTypes: ['工作于', '位于', '创立', '收购', '生产', '参与'],
  propertiesToExtract: ['名称', '描述', '日期', '类型'],
  extractionModel: 'gpt-4o',
  corefEnabled: true,
  entityResolutionEnabled: true,
  strictMode: true,
  maxDepth: '1',
  customPrompt: '',
  fewShotExamples: '',
  ontology: {
    classes: [
      { id: 'c1', name: 'Person', label: '人物', desc: '自然人实体' },
      { id: 'c2', name: 'Company', label: '公司', desc: '企业组织' },
      { id: 'c3', name: 'Product', label: '产品', desc: '商业产品' }
    ],
    relations: [
      { id: 'r1', source: 'c1', target: 'c2', name: 'FOUNDER_OF', label: '创立', desc: '人物创立公司' },
      { id: 'r2', source: 'c2', target: 'c3', name: 'PRODUCES', label: '生产', desc: '公司生产产品' },
      { id: 'r3', source: 'c1', target: 'c2', name: 'WORKS_FOR', label: '工作于', desc: '雇佣关系' }
    ],
    rules: [
      { id: 'ru1', content: '如果 [人物] 创立 [公司]，则推导 [人物] 工作于 [公司]' }
    ]
  }
};

const config = reactive({ ...defaultConfig });

const isDirty = ref(false);
const isSaving = ref(false);
const pendingDelete = ref<{ type: string; index: number } | null>(null);
const showResetConfirm = ref(false);
const activeTab = ref('ontology');

const configSnapshot = JSON.stringify(config);

watch(config, () => {
  isDirty.value = JSON.stringify(config) !== configSnapshot;
}, { deep: true });

const extractionModelOptions = [
  { value: 'gpt-4o', label: 'GPT-4o (OpenAI)', desc: '速度快，效果好' },
  { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet', desc: '长文本理解强' },
  { value: 'qwen-max', label: 'Qwen Max (阿里云)', desc: '中文优化' },
  { value: 'deepseek-chat', label: 'DeepSeek Chat', desc: '性价比高' }
];

const maxDepthOptions = [
  { value: '0', label: '0 - 仅提取顶层实体', desc: '不追踪关联关系' },
  { value: '1', label: '1 - 直接关联关系', desc: '提取实体及其直接关联' },
  { value: '2', label: '2 - 二级关联关系', desc: '深度追溯，完整图谱' }
];

const extractionModelLabel = computed(() => {
  return extractionModelOptions.find(o => o.value === config.extractionModel)?.label || '请选择模型';
});

const maxDepthLabel = computed(() => {
  return maxDepthOptions.find(o => o.value === config.maxDepth)?.label || '请选择深度';
});

const newEntityType = ref('');
const addEntityType = () => {
  const val = newEntityType.value.trim();
  if (!val) {
    toast({ title: '请输入实体类型', variant: 'destructive' });
    return;
  }
  if (config.entityTypes.includes(val)) {
    toast({ title: '该实体类型已存在', variant: 'destructive' });
    return;
  }
  config.entityTypes.push(val);
  newEntityType.value = '';
  toast({ title: '已添加', description: `实体类型「${val}」已添加` });
};
const removeEntityType = (index: number) => {
  pendingDelete.value = { type: 'entity', index };
};

const newRelationType = ref('');
const addRelationType = () => {
  const val = newRelationType.value.trim();
  if (!val) {
    toast({ title: '请输入关系类型', variant: 'destructive' });
    return;
  }
  if (config.relationTypes.includes(val)) {
    toast({ title: '该关系类型已存在', variant: 'destructive' });
    return;
  }
  config.relationTypes.push(val);
  newRelationType.value = '';
  toast({ title: '已添加', description: `关系类型「${val}」已添加` });
};
const removeRelationType = (index: number) => {
  pendingDelete.value = { type: 'relation', index };
};

const newProperty = ref('');
const addProperty = () => {
  const val = newProperty.value.trim();
  if (!val) {
    toast({ title: '请输入属性名称', variant: 'destructive' });
    return;
  }
  if (config.propertiesToExtract.includes(val)) {
    toast({ title: '该属性已存在', variant: 'destructive' });
    return;
  }
  config.propertiesToExtract.push(val);
  newProperty.value = '';
  toast({ title: '已添加', description: `属性「${val}」已添加` });
};
const removeProperty = (index: number) => {
  pendingDelete.value = { type: 'property', index };
};

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substring(2);

const newOntClass = reactive({ label: '', desc: '' });
const addOntClass = () => {
  const val = newOntClass.label.trim();
  if (!val) {
    toast({ title: '请输入实体类名称', variant: 'destructive' });
    return;
  }
  if (config.ontology.classes.some(c => c.label === val)) {
    toast({ title: '该实体类已存在', variant: 'destructive' });
    return;
  }
  config.ontology.classes.push({
    id: generateId(),
    name: val,
    label: val,
    desc: newOntClass.desc.trim()
  });
  newOntClass.label = '';
  newOntClass.desc = '';
  toast({ title: '已添加', description: `实体类「${val}」已添加` });
};
const removeOntClass = (index: number) => pendingDelete.value = { type: 'ontClass', index };

const newOntRel = reactive({ source: '', target: '', label: '' });
const addOntRel = () => {
  if (!newOntRel.source || !newOntRel.target || !newOntRel.label.trim()) {
    toast({ title: '请完善关系信息（起点、终点、关系名称）', variant: 'destructive' });
    return;
  }
  const val = newOntRel.label.trim();
  config.ontology.relations.push({
    id: generateId(),
    source: newOntRel.source,
    target: newOntRel.target,
    name: val,
    label: val,
    desc: ''
  });
  newOntRel.label = '';
  toast({ title: '已添加', description: `关系「${val}」已添加` });
};
const removeOntRel = (index: number) => pendingDelete.value = { type: 'ontRel', index };

const newOntRule = ref('');
const addOntRule = () => {
  const val = newOntRule.value.trim();
  if (!val) {
    toast({ title: '请输入规则内容', variant: 'destructive' });
    return;
  }
  config.ontology.rules.push({
    id: generateId(),
    content: val
  });
  newOntRule.value = '';
  toast({ title: '已添加业务规则' });
};
const removeOntRule = (index: number) => pendingDelete.value = { type: 'ontRule', index };

const confirmDelete = () => {
  if (!pendingDelete.value) return;
  const { type, index } = pendingDelete.value;
  let deleted = '';
  if (type === 'entity') {
    deleted = config.entityTypes[index];
    config.entityTypes.splice(index, 1);
  } else if (type === 'relation') {
    deleted = config.relationTypes[index];
    config.relationTypes.splice(index, 1);
  } else if (type === 'property') {
    deleted = config.propertiesToExtract[index];
    config.propertiesToExtract.splice(index, 1);
  } else if (type === 'ontClass') {
    deleted = config.ontology.classes[index].label;
    // Remove associated relations
    const classId = config.ontology.classes[index].id;
    config.ontology.relations = config.ontology.relations.filter(r => r.source !== classId && r.target !== classId);
    config.ontology.classes.splice(index, 1);
  } else if (type === 'ontRel') {
    deleted = config.ontology.relations[index].label;
    config.ontology.relations.splice(index, 1);
  } else if (type === 'ontRule') {
    deleted = '规则';
    config.ontology.rules.splice(index, 1);
  }
  toast({ title: '已删除', description: `「${deleted}」已移除` });
  pendingDelete.value = null;
};

const cancelDelete = () => {
  pendingDelete.value = null;
};

const saveConfig = async () => {
  isSaving.value = true;
  await new Promise(resolve => setTimeout(resolve, 800));
  isSaving.value = false;
  isDirty.value = false;
  Object.assign(defaultConfig, JSON.parse(JSON.stringify(config)));
  toast({
    title: '保存成功',
    description: '知识图谱配置已更新',
    class: 'border-green-500'
  });
};

const resetConfig = () => {
  Object.assign(config, JSON.parse(JSON.stringify(defaultConfig)));
  isDirty.value = false;
  showResetConfirm.value = false;
  toast({ title: '已重置', description: '配置已恢复为上次保存状态' });
};

const requestReset = () => {
  if (isDirty.value) {
    showResetConfirm.value = true;
  } else {
    resetConfig();
  }
};
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold dark:text-slate-50">知识图谱配置</h2>
        <p class="text-sm text-muted-foreground dark:text-slate-400">配置实体、关系和提取策略</p>
      </div>
      <div class="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          @click="requestReset"
          :disabled="isSaving"
          class="dark:bg-slate-900 dark:border-slate-700"
        >
          <RotateCcw class="w-4 h-4 mr-2" />
          重置
        </Button>
        <Button
          @click="saveConfig"
          :disabled="!isDirty || isSaving"
          :class="{ 'opacity-50 cursor-not-allowed': !isDirty || isSaving }"
        >
          <CheckCircle2 v-if="!isSaving" class="w-4 h-4 mr-2" />
          <span v-if="isSaving">保存中...</span>
          <span v-else>保存配置</span>
        </Button>
      </div>
    </div>

    <div v-if="isDirty" class="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
      <AlertCircle class="w-4 h-4 text-amber-500" />
      <span class="text-sm text-amber-500">您有未保存的更改</span>
    </div>

    <Dialog :open="!!pendingDelete" @update:open="(v) => !v && cancelDelete()">
      <DialogContent class="dark:bg-slate-950">
        <DialogHeader>
          <DialogTitle class="dark:text-slate-50">确认删除</DialogTitle>
          <DialogDescription class="dark:text-slate-400">
            确定要删除此项目吗？此操作可以撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="cancelDelete">取消</Button>
          <Button variant="destructive" @click="confirmDelete">确认删除</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog :open="showResetConfirm" @update:open="(v) => !v && (showResetConfirm = false)">
      <DialogContent class="dark:bg-slate-950">
        <DialogHeader>
          <DialogTitle class="dark:text-slate-50">放弃更改？</DialogTitle>
          <DialogDescription class="dark:text-slate-400">
            您有未保存的更改。确定要放弃这些更改并重置吗？
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="showResetConfirm = false">继续编辑</Button>
          <Button variant="destructive" @click="resetConfig">放弃更改</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="mb-4 grid w-full md:w-[480px] grid-cols-3">
        <TabsTrigger value="ontology" class="flex items-center gap-2">
          <Database class="w-4 h-4" />
          本体建模
        </TabsTrigger>
        <TabsTrigger value="config" class="flex  items-center gap-2">
          <LayoutGrid class="w-4 h-4" />
          配置表单
        </TabsTrigger>
        <TabsTrigger value="preview" class="flex items-center gap-2">
          <Network class="w-4 h-4" />
          图谱预览
        </TabsTrigger>
      </TabsList>

      <TabsContent value="ontology" class="space-y-6">
        <Card class="dark:bg-slate-950 dark:border-slate-800">
          <CardHeader>
            <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-sm font-bold">
              <Database class="w-5 h-5" />
              概念/实体类
            </CardTitle>
            <CardDescription class="dark:text-slate-400">
              定义业务领域中的核心概念（如：客户、订单、商品）
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex gap-2">
              <Input
                v-model="newOntClass.label"
                placeholder="概念名称（如：客户）"
                class="h-10 w-1/3 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
                @keyup.enter="addOntClass"
              />
              <Input
                v-model="newOntClass.desc"
                placeholder="描述（可选）"
                class="h-10 flex-1 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
                @keyup.enter="addOntClass"
              />
              <Button size="default" variant="secondary" class="h-10 px-4" @click="addOntClass">
                <Plus class="w-4 h-4 mr-1" />
                添加
              </Button>
            </div>
            <div class="flex flex-wrap gap-2 min-h-[3rem] p-3 border rounded-lg dark:border-slate-800 bg-muted/10">
              <div
                v-for="(cls, idx) in config.ontology.classes"
                :key="cls.id"
                class="flex items-center gap-2 px-3 py-2 bg-background border rounded-md shadow-sm dark:bg-slate-900 dark:border-slate-700 group hover:border-destructive/50 transition-all"
              >
                <div class="flex flex-col">
                  <span class="text-sm font-medium dark:text-slate-200">{{ cls.label }}</span>
                  <span v-if="cls.desc" class="text-xs text-muted-foreground">{{ cls.desc }}</span>
                </div>
                <Trash2
                  class="w-4 h-4 ml-2 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors"
                  @click.stop="removeOntClass(idx)"
                />
              </div>
              <div v-if="!config.ontology.classes.length" class="w-full flex flex-col items-center justify-center py-4 text-muted-foreground">
                <Database class="w-8 h-8 mb-2 opacity-20" />
                <span class="text-sm">暂无概念类，请添加</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="dark:bg-slate-950 dark:border-slate-800">
          <CardHeader>
            <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-sm font-bold">
              <Link class="w-5 h-5" />
              关联关系
            </CardTitle>
            <CardDescription class="dark:text-slate-400">
              定义概念之间的业务联系（如：客户 [购买] 订单）
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center gap-2">
              <Select v-model="newOntRel.source">
                <SelectTrigger class="h-10 flex-1 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                  <SelectValue placeholder="选择起点概念" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="cls in config.ontology.classes" :key="cls.id" :value="cls.id">{{ cls.label }}</SelectItem>
                </SelectContent>
              </Select>
              <ArrowRight class="w-4 h-4 text-muted-foreground shrink-0" />
              <Input
                v-model="newOntRel.label"
                placeholder="关系名称（如：购买）"
                class="h-10 flex-1 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
                @keyup.enter="addOntRel"
              />
              <ArrowRight class="w-4 h-4 text-muted-foreground shrink-0" />
              <Select v-model="newOntRel.target">
                <SelectTrigger class="h-10 flex-1 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                  <SelectValue placeholder="选择终点概念" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="cls in config.ontology.classes" :key="cls.id" :value="cls.id">{{ cls.label }}</SelectItem>
                </SelectContent>
              </Select>
              <Button size="default" variant="secondary" class="h-10 px-4" @click="addOntRel">
                <Plus class="w-4 h-4 mr-1" />
                添加
              </Button>
            </div>
            
            <div class="space-y-2 min-h-[3rem] p-3 border rounded-lg dark:border-slate-800 bg-muted/10">
              <div
                v-for="(rel, idx) in config.ontology.relations"
                :key="rel.id"
                class="flex items-center justify-between p-3 bg-background border rounded-md shadow-sm dark:bg-slate-900 dark:border-slate-700 group hover:border-destructive/50 transition-all"
              >
                <div class="flex items-center gap-3">
                  <Badge variant="outline" class="bg-blue-500/10 text-blue-600 border-blue-500/20">
                    {{ config.ontology.classes.find(c => c.id === rel.source)?.label || '未知' }}
                  </Badge>
                  <div class="flex items-center gap-1 text-muted-foreground">
                    <span class="w-4 border-t border-dashed"></span>
                    <span class="text-sm font-medium dark:text-slate-300">{{ rel.label }}</span>
                    <span class="w-4 border-t border-dashed"></span>
                    <ArrowRight class="w-3.5 h-3.5" />
                  </div>
                  <Badge variant="outline" class="bg-purple-500/10 text-purple-600 border-purple-500/20">
                    {{ config.ontology.classes.find(c => c.id === rel.target)?.label || '未知' }}
                  </Badge>
                </div>
                <Button variant="ghost" size="icon" class="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop="removeOntRel(idx)">
                  <Trash2 class="w-4 h-4 text-destructive" />
                </Button>
              </div>
              <div v-if="!config.ontology.relations.length" class="w-full flex flex-col items-center justify-center py-4 text-muted-foreground">
                <Link class="w-8 h-8 mb-2 opacity-20" />
                <span class="text-sm">暂无关联关系，请添加</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="dark:bg-slate-950 dark:border-slate-800">
          <CardHeader>
            <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-sm font-bold">
              <BrainCircuit class="w-5 h-5" />
              推理规则
            </CardTitle>
            <CardDescription class="dark:text-slate-400">
              设置业务逻辑规则，让AI自动推导出隐式关系（如：如果A是B的子公司，且B属于C集团，则A属于C集团）
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex gap-2">
              <Input
                v-model="newOntRule"
                placeholder="使用自然语言描述业务规则..."
                class="h-10 flex-1 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
                @keyup.enter="addOntRule"
              />
              <Button size="default" variant="secondary" class="h-10 px-4" @click="addOntRule">
                <Plus class="w-4 h-4 mr-1" />
                添加
              </Button>
            </div>
            
            <div class="space-y-2 min-h-[3rem] p-3 border rounded-lg dark:border-slate-800 bg-muted/10">
              <div
                v-for="(rule, idx) in config.ontology.rules"
                :key="rule.id"
                class="flex items-start justify-between p-3 bg-background border rounded-md shadow-sm dark:bg-slate-900 dark:border-slate-700 group hover:border-destructive/50 transition-all"
              >
                <div class="flex items-start gap-2 pt-0.5">
                  <GitMerge class="w-4 h-4 mt-0.5 text-amber-500 shrink-0" />
                  <span class="text-sm dark:text-slate-200">{{ rule.content }}</span>
                </div>
                <Button variant="ghost" size="icon" class="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" @click.stop="removeOntRule(idx)">
                  <Trash2 class="w-4 h-4 text-destructive" />
                </Button>
              </div>
              <div v-if="!config.ontology.rules.length" class="w-full flex flex-col items-center justify-center py-4 text-muted-foreground">
                <BrainCircuit class="w-8 h-8 mb-2 opacity-20" />
                <span class="text-sm">暂无推理规则，请添加</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="config" class="space-y-6">
        <Card class="dark:bg-slate-950 dark:border-slate-800">
          <CardHeader>
            <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-lg font-bold">
              实体类型
            </CardTitle>
            <CardDescription class="dark:text-slate-400">
              定义要提取的实体种类，如人物、公司、地点等
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex gap-2">
              <Input
                v-model="newEntityType"
                placeholder="输入实体类型名称..."
                class="h-10 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
                @keyup.enter="addEntityType"
                maxlength="50"
              />
              <Button size="default" variant="secondary" class="h-10 px-4" @click="addEntityType">
                <Plus class="w-4 h-4 mr-1" />
                添加
              </Button>
            </div>
            <div class="flex flex-wrap gap-2 min-h-[3rem] p-3 border rounded-lg dark:border-slate-800 bg-muted/10">
              <Badge
                v-for="(type, idx) in config.entityTypes"
                :key="idx"
                variant="outline"
                class="px-3 py-1.5 text-sm bg-blue-500/10 border-blue-500/20 text-blue-600 dark:text-blue-400 pr-2 gap-2 group hover:border-destructive/50 transition-all cursor-pointer"
              >
            {{ type }}
            <Trash2
              class="w-3.5 h-3.5 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors"
              @click.stop="removeEntityType(idx)"
            />
          </Badge>
          <span v-if="!config.entityTypes.length" class="text-sm text-muted-foreground italic py-1">
            暂无实体类型，请添加
          </span>
        </div>
        <p class="text-xs text-muted-foreground">提示：实体类型用于识别文本中的关键名词，如"人名"、"公司名"、"地点"等</p>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-lg font-bold">
          关系类型
        </CardTitle>
        <CardDescription class="dark:text-slate-400">
          定义实体之间的关系，如"工作于"、"位于"、"创立"等
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="flex gap-2">
          <Input
            v-model="newRelationType"
            placeholder="输入关系类型名称..."
            class="h-10 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
            @keyup.enter="addRelationType"
            maxlength="50"
          />
          <Button size="default" variant="secondary" class="h-10 px-4" @click="addRelationType">
            <Plus class="w-4 h-4 mr-1" />
            添加
          </Button>
        </div>
        <div class="flex flex-wrap gap-2 min-h-[3rem] p-3 border rounded-lg dark:border-slate-800 bg-muted/10">
          <Badge
            v-for="(type, idx) in config.relationTypes"
            :key="idx"
            variant="outline"
            class="px-3 py-1.5 text-sm bg-purple-500/10 border-purple-500/20 text-purple-600 dark:text-purple-400 pr-2 gap-2 group hover:border-destructive/50 transition-all cursor-pointer"
          >
            {{ type }}
            <Trash2
              class="w-3.5 h-3.5 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors"
              @click.stop="removeRelationType(idx)"
            />
          </Badge>
          <span v-if="!config.relationTypes.length" class="text-sm text-muted-foreground italic py-1">
            暂无关系类型，请添加
          </span>
        </div>
        <p class="text-xs text-muted-foreground">提示：关系类型描述实体之间的关联，如"张三分工作于阿里巴巴"中的"工作于"</p>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-lg font-bold">
          属性字段
        </CardTitle>
        <CardDescription class="dark:text-slate-400">
          指定要从实体中提取的附加信息
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="flex gap-2">
          <Input
            v-model="newProperty"
            placeholder="输入属性名称..."
            class="h-10 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
            @keyup.enter="addProperty"
            maxlength="50"
          />
          <Button size="default" variant="secondary" class="h-10 px-4" @click="addProperty">
            <Plus class="w-4 h-4 mr-1" />
            添加
          </Button>
        </div>
        <div class="flex flex-wrap gap-2 min-h-[3rem] p-3 border rounded-lg dark:border-slate-800 bg-muted/10">
          <Badge
            v-for="(prop, idx) in config.propertiesToExtract"
            :key="idx"
            variant="outline"
            class="px-3 py-1.5 text-sm bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400 pr-2 gap-2 group hover:border-destructive/50 transition-all cursor-pointer"
          >
            {{ prop }}
            <Trash2
              class="w-3.5 h-3.5 cursor-pointer text-muted-foreground group-hover:text-destructive transition-colors"
              @click.stop="removeProperty(idx)"
            />
          </Badge>
          <span v-if="!config.propertiesToExtract.length" class="text-sm text-muted-foreground italic py-1">
            暂无属性，保留为空将提取所有属性
          </span>
        </div>
        <p class="text-xs text-muted-foreground">提示：属性是实体的特征信息，如"姓名"、"成立时间"、"地址"等</p>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-lg font-bold">
          抽取策略
        </CardTitle>
        <CardDescription class="dark:text-slate-400">配置AI模型提取知识图谱时的行为</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Label class="dark:text-slate-200">AI模型</Label>
              <Popover>
                <PopoverTrigger as-child>
                  <Button variant="ghost" size="icon" class="w-5 h-5 p-0">
                    <HelpCircle class="w-4 h-4 text-muted-foreground" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="dark:bg-slate-950 dark:border-slate-800 w-80">
                  <p class="text-sm dark:text-slate-300">选择用于从文本中提取知识图谱的AI模型。不同模型在速度、成本和效果上有差异。</p>
                </PopoverContent>
              </Popover>
            </div>
            <Select v-model="config.extractionModel">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 h-10">
                <SelectValue>{{ extractionModelLabel }}</SelectValue>
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem v-for="opt in extractionModelOptions" :key="opt.value" :value="opt.value" class="dark:text-slate-200">
                  <div class="flex flex-col">
                    <span>{{ opt.label }}</span>
                    <span class="text-xs text-muted-foreground">{{ opt.desc }}</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Label class="dark:text-slate-200">关系追溯深度</Label>
              <Popover>
                <PopoverTrigger as-child>
                  <Button variant="ghost" size="icon" class="w-5 h-5 p-0">
                    <HelpCircle class="w-4 h-4 text-muted-foreground" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="dark:bg-slate-950 dark:border-slate-800 w-80">
                  <p class="text-sm dark:text-slate-300">指定从初始实体出发，追溯关联实体的最大层数。深度越大，图谱越完整但处理时间越长。</p>
                </PopoverContent>
              </Popover>
            </div>
            <Select v-model="config.maxDepth">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 h-10">
                <SelectValue>{{ maxDepthLabel }}</SelectValue>
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem v-for="opt in maxDepthOptions" :key="opt.value" :value="opt.value" class="dark:text-slate-200">
                  <div class="flex flex-col">
                    <span>{{ opt.label }}</span>
                    <span class="text-xs text-muted-foreground">{{ opt.desc }}</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div class="space-y-4 rounded-lg border p-5 dark:border-slate-800 bg-muted/5">
          <div class="flex items-center justify-between">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <Label class="text-base font-medium dark:text-slate-200">智能指代消解</Label>
                <Popover>
                  <PopoverTrigger as-child>
                    <Button variant="ghost" size="icon" class="w-5 h-5 p-0">
                      <HelpCircle class="w-4 h-4 text-muted-foreground" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent class="dark:bg-slate-950 dark:border-slate-800 w-80">
                    <p class="text-sm dark:text-slate-300">开启后，AI会自动将"他"、"它"、"这个公司"等代词替换为实际对应的实体名称。</p>
                  </PopoverContent>
                </Popover>
              </div>
              <p class="text-sm text-muted-foreground dark:text-slate-400">自动识别代词指向的具体实体</p>
            </div>
            <Switch :checked="config.corefEnabled" @update:checked="(v) => config.corefEnabled = v" />
          </div>

          <div class="flex items-center justify-between pt-4 border-t dark:border-slate-800">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <Label class="text-base font-medium dark:text-slate-200">智能实体对齐</Label>
                <Popover>
                  <PopoverTrigger as-child>
                    <Button variant="ghost" size="icon" class="w-5 h-5 p-0">
                      <HelpCircle class="w-4 h-4 text-muted-foreground" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent class="dark:bg-slate-950 dark:border-slate-800 w-80">
                    <p class="text-sm dark:text-slate-300">自动识别不同表述的同一实体，如"Google"和"Google Inc."、"腾讯"和"腾讯公司"。</p>
                  </PopoverContent>
                </Popover>
              </div>
              <p class="text-sm text-muted-foreground dark:text-slate-400">合并相似名称的重复实体</p>
            </div>
            <Switch :checked="config.entityResolutionEnabled" @update:checked="(v) => config.entityResolutionEnabled = v" />
          </div>

          <div class="flex items-center justify-between pt-4 border-t dark:border-slate-800">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <Label class="text-base font-medium dark:text-slate-200">严格模式</Label>
                <Popover>
                  <PopoverTrigger as-child>
                    <Button variant="ghost" size="icon" class="w-5 h-5 p-0">
                      <HelpCircle class="w-4 h-4 text-muted-foreground" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent class="dark:bg-slate-950 dark:border-slate-800 w-80">
                    <p class="text-sm dark:text-slate-300">开启后，AI仅提取在上方"实体类型"和"关系类型"中明确定义的内容，避免提取无关信息。</p>
                  </PopoverContent>
                </Popover>
              </div>
              <p class="text-sm text-muted-foreground dark:text-slate-400">仅提取已定义的实体和关系</p>
            </div>
            <Switch :checked="config.strictMode" @update:checked="(v) => config.strictMode = v" />
          </div>
        </div>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 flex items-center gap-2 text-lg font-bold">
          高级配置
        </CardTitle>
        <CardDescription class="dark:text-slate-400">自定义AI提示词和示例（如无特殊需求建议保持默认）</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <Label class="dark:text-slate-200">系统提示词</Label>
            <Badge variant="outline" class="text-xs bg-amber-500/10 text-amber-500 border-amber-500/20">可选</Badge>
          </div>
          <p class="text-sm text-muted-foreground dark:text-slate-400">自定义AI提取图谱时的指导说明。留空使用系统默认提示词。</p>
          <Textarea
            v-model="config.customPrompt"
            placeholder="例如：你是一个专业的知识图谱提取专家，请从文本中提取结构化的实体和关系..."
            class="min-h-[120px] font-mono text-sm dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
          />
        </div>

        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <Label class="dark:text-slate-200">本体建模</Label>
            <Badge variant="outline" class="text-xs bg-amber-500/10 text-amber-500 border-amber-500/20">可选</Badge>
          </div>
          <p class="text-sm text-muted-foreground dark:text-slate-400">提供JSON格式的示例，帮助AI更准确地理解您的提取需求。</p>
          <Textarea
            v-model="config.fewShotExamples"
            placeholder='[
  {
    "ontology": {
      "classes": ["Person", "Company", "Product"],
      "relations": [
        {"type": "FOUNDER_OF", "domain": "Person", "range": "Company"},
        {"type": "PRODUCES", "domain": "Company", "range": "Product"}
      ],
      "rules": [
        "如果 A FOUNDER_OF(创立) B，则可推导出 A WORKS_FOR(工作于) B"
      ]
    },
    "text": "乔布斯创立了苹果公司，苹果公司生产了iPhone。",
    "result": {
      "entities": [
        {"type": "Person", "name": "乔布斯"},
        {"type": "Company", "name": "苹果公司"},
        {"type": "Product", "name": "iPhone"}
      ],
      "relations": [
        {"type": "FOUNDER_OF", "from": "乔布斯", "to": "苹果公司"},
        {"type": "WORKS_FOR", "from": "乔布斯", "to": "苹果公司", "inferred": true},
        {"type": "PRODUCES", "from": "苹果公司", "to": "iPhone"}
      ]
    }
  }
]'
            class="min-h-[200px] font-mono text-sm dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200"
          />
        </div>

        <div class="pt-4 flex justify-end gap-3">
          <Button variant="outline" @click="requestReset" class="dark:bg-slate-900 dark:border-slate-700">
            <RotateCcw class="w-4 h-4 mr-2" />
            重置
          </Button>
          <Button @click="saveConfig" :disabled="!isDirty || isSaving">
            <CheckCircle2 v-if="!isSaving" class="w-4 h-4 mr-2" />
            {{ isSaving ? '保存中...' : '保存配置' }}
          </Button>
        </div>
      </CardContent>
    </Card>
      </TabsContent>

      <TabsContent value="preview" class="h-full">
        <KnowledgeGraphPreview
          v-if="activeTab === 'preview'"
          :entity-types="config.entityTypes"
          :relation-types="config.relationTypes"
        />
      </TabsContent>
    </Tabs>
  </div>
</template>
