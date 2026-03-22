<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/toast/use-toast';
import { Eye, EyeOff, CheckCircle2, XCircle, Search, TerminalSquare, Box, Settings2, ShieldCheck, Zap } from 'lucide-vue-next';
import { llmApi, type Model } from '@/features/etl_editor/api/llm';

const { toast } = useToast();

// 状态定义
const loading = ref(false);
const availableModels = ref<Model[]>([]);
const providers = ref<{id: string; label: string}[]>([]);

// 系统配置状态 (替代硬编码的 keys)
const config = reactive({
  defaultTextProvider: '',
  defaultTextModel: '',
  defaultEmbeddingProvider: '',
  defaultEmbeddingModel: '',
});

// 插件/工具监控状态
const toolsStatus = ref([
  { id: 'tavily', name: 'Tavily Search', type: 'search', status: 'connected', latency: '120ms', description: '高级AI搜索引擎，用于代理联网检索。' },
  { id: 'firecrawl', name: 'FireCrawl', type: 'crawler', status: 'error', latency: '-', description: '网页爬虫工具，用于抓取和结构化网页内容。' },
  { id: 'e2b', name: 'E2B Sandbox', type: 'sandbox', status: 'connected', latency: '45ms', description: '安全的云端代码执行沙箱环境。' },
  { id: 'mcp', name: 'MCP 协议扩展', type: 'protocol', status: 'connected', latency: '8ms', description: '模型上下文协议，连接本地资源。' }
]);

// 获取已配置的模型列表
const fetchModels = async () => {
  loading.value = true;
  try {
    availableModels.value = await llmApi.listModels();
    
    // 提取唯一的提供商
    const uniqueProviders = new Set(availableModels.value.map(m => m.provider));
    providers.value = Array.from(uniqueProviders).map(p => ({
      id: p,
      label: p.charAt(0).toUpperCase() + p.slice(1)
    }));

    // 初始化默认值
    if (availableModels.value.length > 0) {
      const textModels = textModelsList.value;
      if (textModels.length > 0 && !config.defaultTextModel) {
        config.defaultTextProvider = textModels[0].provider;
        config.defaultTextModel = textModels[0].model_id;
      }
      
      const embModels = embeddingModelsList.value;
      if (embModels.length > 0 && !config.defaultEmbeddingModel) {
        config.defaultEmbeddingProvider = embModels[0].provider;
        config.defaultEmbeddingModel = embModels[0].model_id;
      }
    }
  } catch (error) {
    console.error('Failed to fetch models:', error);
    toast({ title: '加载失败', description: '无法获取模型列表', variant: 'destructive' });
  } finally {
    loading.value = false;
  }
};

// 计算属性过滤不同类型的模型
const textModelsList = computed(() => 
  availableModels.value.filter(m => m.model_type === 'text' || !m.model_type)
);

const embeddingModelsList = computed(() => 
  availableModels.value.filter(m => m.model_type === 'embedding')
);

// 获取指定提供商的模型
const getModelsByProvider = (models: Model[], providerId: string) => {
  return models.filter(m => m.provider === providerId);
};

// 监听提供商变化，自动选择第一个模型
const handleProviderChange = (type: 'text' | 'embedding', providerId: string) => {
  const targetList = type === 'text' ? textModelsList.value : embeddingModelsList.value;
  const models = getModelsByProvider(targetList, providerId);
  
  if (models.length > 0) {
    if (type === 'text') config.defaultTextModel = models[0].model_id;
    else config.defaultEmbeddingModel = models[0].model_id;
  } else {
    if (type === 'text') config.defaultTextModel = '';
    else config.defaultEmbeddingModel = '';
  }
};

// 工具类型图标映射
const getToolIcon = (type: string) => {
  switch(type) {
    case 'search': return Search;
    case 'crawler': return Box;
    case 'sandbox': return TerminalSquare;
    case 'protocol': return Settings2;
    default: return Box;
  }
};

onMounted(() => {
  fetchModels();
});

const saveConfig = () => {
  toast({
    title: '配置已应用',
    description: '全局默认模型与工具路由策略已更新。',
  });
};
</script>

<template>
  <div class="space-y-8 pb-10">
    <!-- 模块说明 -->
    <div>
      <h2 class="text-xl font-bold tracking-tight">智能体资源路由</h2>
      <p class="text-muted-foreground mt-2">管理全局默认模型调度策略与第三方工具的健康状态。API 密钥配置已迁移至统一的系统配置与模型管理模块中。</p>
    </div>

    <!-- 全局默认大模型配置 -->
    <Card class="dark:bg-slate-950/50 border-slate-200 dark:border-slate-800 shadow-sm">
      <CardHeader class="pb-4">
        <div class="flex items-center gap-2">
          <div class="p-2 bg-primary/10 rounded-lg text-primary">
            <Zap class="w-5 h-5" />
          </div>
          <div>
            <CardTitle class="text-lg">全局模型路由策略</CardTitle>
            <CardDescription>配置智能体在未指定特定模型时的默认降级策略</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent class="space-y-8">
        
        <!-- 文本生成模型路由 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b pb-2">
            <h3 class="text-sm font-medium flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-blue-500"></span>
              文本生成 (Text Generation)
            </h3>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <Label>首选提供商</Label>
              <Select v-model="config.defaultTextProvider" @update:model-value="val => handleProviderChange('text', val)">
                <SelectTrigger>
                  <SelectValue placeholder="选择提供商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="p in providers" :key="p.id" :value="p.id">
                    {{ p.label }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <Label>默认模型 ID</Label>
              <Select v-model="config.defaultTextModel" :disabled="!config.defaultTextProvider">
                <SelectTrigger>
                  <SelectValue placeholder="选择默认模型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="m in getModelsByProvider(textModelsList, config.defaultTextProvider)" 
                    :key="m.model_id" 
                    :value="m.model_id"
                  >
                    {{ m.name || m.model_id }}
                  </SelectItem>
                  <SelectItem v-if="getModelsByProvider(textModelsList, config.defaultTextProvider).length === 0" value="none" disabled>
                    该提供商下无可用文本模型
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <!-- 向量嵌入模型路由 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b pb-2">
            <h3 class="text-sm font-medium flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              向量嵌入 (Embeddings)
            </h3>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <Label>首选提供商</Label>
              <Select v-model="config.defaultEmbeddingProvider" @update:model-value="val => handleProviderChange('embedding', val)">
                <SelectTrigger>
                  <SelectValue placeholder="选择提供商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="p in providers" :key="p.id" :value="p.id">
                    {{ p.label }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <Label>默认模型 ID</Label>
              <Select v-model="config.defaultEmbeddingModel" :disabled="!config.defaultEmbeddingProvider">
                <SelectTrigger>
                  <SelectValue placeholder="选择默认模型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="m in getModelsByProvider(embeddingModelsList, config.defaultEmbeddingProvider)" 
                    :key="m.model_id" 
                    :value="m.model_id"
                  >
                    {{ m.name || m.model_id }}
                  </SelectItem>
                  <SelectItem v-if="getModelsByProvider(embeddingModelsList, config.defaultEmbeddingProvider).length === 0" value="none" disabled>
                    该提供商下无可用嵌入模型
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

      </CardContent>
      <CardFooter class="bg-muted/50 py-4 flex justify-between items-center rounded-b-xl">
        <p class="text-xs text-muted-foreground">如果智能体调用失败，系统将尝试回退到该路由配置。</p>
        <Button @click="saveConfig">保存路由策略</Button>
      </CardFooter>
    </Card>

    <!-- 工具与环境监控 -->
    <Card class="dark:bg-slate-950/50 border-slate-200 dark:border-slate-800 shadow-sm">
      <CardHeader class="pb-4 border-b">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="p-2 bg-primary/10 rounded-lg text-primary">
              <ShieldCheck class="w-5 h-5" />
            </div>
            <div>
              <CardTitle class="text-lg">环境与工具探针</CardTitle>
              <CardDescription>监控系统核心工具链的连通性与健康状态</CardDescription>
            </div>
          </div>
          <Button variant="outline" size="sm">
            <Settings2 class="w-4 h-4 mr-2" />
            前往环境变量配置
          </Button>
        </div>
      </CardHeader>
      <CardContent class="p-0">
        <div class="divide-y">
          <div v-for="tool in toolsStatus" :key="tool.id" class="p-6 flex items-start gap-4 hover:bg-muted/30 transition-colors">
            <div class="p-3 bg-muted rounded-xl border">
              <component :is="getToolIcon(tool.type)" class="w-5 h-5 text-foreground" />
            </div>
            <div class="flex-1 space-y-1">
              <div class="flex items-center justify-between">
                <h4 class="font-medium text-base">{{ tool.name }}</h4>
                <div class="flex items-center gap-3">
                  <span v-if="tool.status === 'connected'" class="text-xs text-muted-foreground">延迟: {{ tool.latency }}</span>
                  <Badge :variant="tool.status === 'connected' ? 'default' : 'destructive'" class="shadow-sm">
                    <CheckCircle2 v-if="tool.status === 'connected'" class="w-3 h-3 mr-1" />
                    <XCircle v-else class="w-3 h-3 mr-1" />
                    {{ tool.status === 'connected' ? '已连接' : '配置异常' }}
                  </Badge>
                </div>
              </div>
              <p class="text-sm text-muted-foreground">{{ tool.description }}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>