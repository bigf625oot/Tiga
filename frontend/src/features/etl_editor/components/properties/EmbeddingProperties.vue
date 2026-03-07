<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { llmApi, type Model } from '../../api/llm';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  FileText, 
  Scissors, 
  Database, 
  AlertCircle, 
  CheckCircle2, 
  Eye, 
  Settings2,
  FileType,
  Layers
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const availableModels = ref<Model[]>([]);
const activeTab = ref('chunking');

// Default Preview Text
const defaultPreviewText = `人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的“容器”。

人工智能可以对人的意识、思维的信息过程的模拟。人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。`;

const previewText = ref(defaultPreviewText);
const previewChunks = ref<string[]>([]);

const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

// --- Computed Config Helpers ---
const config = computed(() => node.value?.data?.config || {});

const chunkStrategy = computed({
  get: () => config.value.chunk_strategy || 'recursive',
  set: (v) => updateConfig('chunk_strategy', v)
});

const chunkSize = computed({
  get: () => config.value.chunk_size ?? 500,
  set: (v) => updateConfig('chunk_size', v)
});

const chunkOverlap = computed({
  get: () => config.value.chunk_overlap ?? 50,
  set: (v) => updateConfig('chunk_overlap', v)
});

// --- Validation ---
const validationErrors = computed(() => {
  const errors: string[] = [];
  if (chunkSize.value <= 0) errors.push('分块大小必须大于 0');
  if (chunkOverlap.value >= chunkSize.value) errors.push('重叠度必须小于分块大小');
  if (!config.value.model_id) errors.push('请选择嵌入模型');
  return errors;
});

// --- Simulation Logic for Preview ---
const generatePreview = () => {
  const text = previewText.value;
  const size = chunkSize.value;
  const overlap = chunkOverlap.value;
  const strategy = chunkStrategy.value;
  
  if (!text || size <= 0 || overlap >= size) {
    previewChunks.value = [];
    return;
  }

  const chunks: string[] = [];
  
  if (strategy === 'fixed') {
    let start = 0;
    while (start < text.length) {
      const end = Math.min(start + size, text.length);
      chunks.push(text.slice(start, end));
      start += (size - overlap);
    }
  } else if (strategy === 'recursive') {
    // Simple simulation of recursive splitting by newlines then spaces
    const separators = ['\n\n', '\n', '。', '！', '!', '；', ';', ' '];
    // This is a simplified mock. Real recursive splitting is complex.
    // We'll just simulate paragraph splitting for visual feedback
    const paragraphs = text.split('\n').filter(p => p.trim());
    let currentChunk = '';
    
    paragraphs.forEach(p => {
      if (currentChunk.length + p.length > size) {
        if (currentChunk) chunks.push(currentChunk);
        currentChunk = p;
      } else {
        currentChunk += (currentChunk ? '\n' : '') + p;
      }
    });
    if (currentChunk) chunks.push(currentChunk);
  } else {
    // Semantic placeholder
    chunks.push(text); // No split preview for semantic in frontend only
  }
  
  previewChunks.value = chunks;
};

watch([chunkSize, chunkOverlap, chunkStrategy, previewText], generatePreview, { immediate: true });

onMounted(async () => {
  try {
    const res = await llmApi.listModels();
    availableModels.value = res.filter(m => m.is_active && (m.model_type === 'embedding' || m.model_type === 'multimodal'));
  } catch (e) {
    console.error('Failed to fetch embedding models', e);
  }
  generatePreview();
});
</script>

<template>
  <div class="flex flex-col w-full min-h-[600px] bg-background/50 border rounded-lg overflow-hidden">
    <Tabs v-model="activeTab" class="w-full flex flex-col h-full">
      <div class="px-4 pt-2 border-b bg-muted/20 shrink-0">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="parsing" class="flex items-center gap-2">
            <FileType class="w-3.5 h-3.5" />
            解析
          </TabsTrigger>
          <TabsTrigger value="chunking" class="flex items-center gap-2">
            <Scissors class="w-3.5 h-3.5" />
            分块
          </TabsTrigger>
          <TabsTrigger value="embedding" class="flex items-center gap-2">
            <Database class="w-3.5 h-3.5" />
            向量
          </TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea class="flex-1">
        <div class="p-4 space-y-6">
          
          <!-- Tab 1: Document Parsing -->
          <TabsContent value="parsing" class="space-y-4 mt-0">
            <Card>
              <CardHeader class="pb-3">
                <CardTitle class="text-sm font-medium flex items-center gap-2">
                  <FileText class="w-4 h-4 text-blue-500" />
                  文档格式支持
                </CardTitle>
                <CardDescription class="text-xs">
                  配置文档解析器的行为和支持的文件类型
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label class="text-xs">结构化文件</Label>
                    <div class="flex flex-col gap-2">
                      <div class="flex items-center space-x-2">
                        <Switch :checked="config.parse_pdf ?? true" @update:checked="(v) => updateConfig('parse_pdf', v)" />
                        <span class="text-xs">PDF (.pdf)</span>
                      </div>
                      <div class="flex items-center space-x-2">
                        <Switch :checked="config.parse_word ?? true" @update:checked="(v) => updateConfig('parse_word', v)" />
                        <span class="text-xs">Word (.docx)</span>
                      </div>
                    </div>
                  </div>
                  <div class="space-y-2">
                    <Label class="text-xs">纯文本/标记</Label>
                    <div class="flex flex-col gap-2">
                      <div class="flex items-center space-x-2">
                        <Switch :checked="config.parse_md ?? true" @update:checked="(v) => updateConfig('parse_md', v)" />
                        <span class="text-xs">Markdown (.md)</span>
                      </div>
                      <div class="flex items-center space-x-2">
                        <Switch :checked="config.parse_txt ?? true" @update:checked="(v) => updateConfig('parse_txt', v)" />
                        <span class="text-xs">Text (.txt)</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="pt-4 border-t">
                  <div class="flex items-center justify-between">
                    <div class="space-y-0.5">
                      <Label class="text-xs font-medium">智能结构识别</Label>
                      <p class="text-[10px] text-muted-foreground">自动提取标题、段落层级和表格结构</p>
                    </div>
                    <Switch :checked="config.extract_structure ?? true" @update:checked="(v) => updateConfig('extract_structure', v)" />
                  </div>
                </div>
                
                <div class="flex items-center justify-between">
                  <div class="space-y-0.5">
                    <Label class="text-xs font-medium">OCR 增强</Label>
                    <p class="text-[10px] text-muted-foreground">对扫描件图片进行文字识别 (较慢)</p>
                  </div>
                  <Switch :checked="config.ocr_enabled ?? false" @update:checked="(v) => updateConfig('ocr_enabled', v)" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <!-- Tab 2: Intelligent Chunking -->
          <TabsContent value="chunking" class="space-y-4 mt-0">
            <!-- Strategy Selection -->
            <div class="space-y-2">
              <Label>分块策略 (Strategy)</Label>
              <Select v-model="chunkStrategy">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fixed">固定长度 (Fixed Size)</SelectItem>
                  <SelectItem value="recursive">递归字符 (Recursive Character)</SelectItem>
                  <SelectItem value="semantic">语义分割 (Semantic)</SelectItem>
                  <SelectItem value="markdown">Markdown 结构化</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Parameters -->
            <div class="space-y-4 border rounded-md p-3 bg-muted/20">
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <Label class="text-xs">分块大小 (Chunk Size)</Label>
                  <span class="text-xs font-mono bg-background px-1.5 rounded border">{{ chunkSize }}</span>
                </div>
                <Slider 
                  :model-value="[chunkSize]"
                  :max="2000" :min="50" :step="10"
                  @update:model-value="(v) => chunkSize = v?.[0] || 500"
                />
              </div>

              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <Label class="text-xs">重叠度 (Overlap)</Label>
                  <span class="text-xs font-mono bg-background px-1.5 rounded border">{{ chunkOverlap }}</span>
                </div>
                <Slider 
                  :model-value="[chunkOverlap]"
                  :max="500" :min="0" :step="10"
                  @update:model-value="(v) => chunkOverlap = v?.[0] || 0"
                />
              </div>

              <div v-if="chunkStrategy === 'semantic'" class="space-y-3 pt-2 border-t">
                <div class="flex justify-between items-center">
                  <Label class="text-xs">相似度阈值 (Threshold)</Label>
                  <span class="text-xs font-mono bg-background px-1.5 rounded border">{{ config.semantic_threshold ?? 0.8 }}</span>
                </div>
                <Slider 
                  :model-value="[config.semantic_threshold ?? 0.8]"
                  :max="1" :min="0.1" :step="0.05"
                  @update:model-value="(v) => updateConfig('semantic_threshold', v?.[0])"
                />
              </div>
            </div>

            <!-- Validation Status -->
            <div v-if="validationErrors.length > 0" class="p-3 bg-destructive/10 text-destructive rounded-md text-xs space-y-1">
              <div class="flex items-center gap-1.5 font-medium">
                <AlertCircle class="w-3.5 h-3.5" />
                配置错误
              </div>
              <ul class="list-disc list-inside opacity-90">
                <li v-for="err in validationErrors" :key="err">{{ err }}</li>
              </ul>
            </div>

            <!-- Visualization Preview -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label class="flex items-center gap-1.5">
                  <Eye class="w-3.5 h-3.5 text-primary" />
                  分块效果预览
                </Label>
                <Badge variant="outline" class="text-[10px] font-normal">
                  预计生成 {{ previewChunks.length }} 个块
                </Badge>
              </div>
              
              <div class="border rounded-md overflow-hidden bg-background">
                <div class="p-2 border-b bg-muted/30">
                  <Textarea 
                    v-model="previewText" 
                    class="min-h-[80px] text-xs font-mono border-0 focus-visible:ring-0 bg-transparent p-0 resize-none"
                    placeholder="输入测试文本以预览分块效果..."
                  />
                </div>
                <div class="p-2 max-h-[200px] overflow-y-auto bg-muted/10 space-y-2">
                  <div 
                    v-for="(chunk, idx) in previewChunks" 
                    :key="idx"
                    class="text-xs p-2 rounded border border-l-4 transition-all hover:shadow-sm"
                    :class="[
                      idx % 2 === 0 ? 'bg-blue-50/50 border-l-blue-500 border-blue-100' : 'bg-green-50/50 border-l-green-500 border-green-100'
                    ]"
                  >
                    <div class="flex justify-between text-[10px] text-muted-foreground mb-1">
                      <span>Chunk #{{ idx + 1 }}</span>
                      <span>{{ chunk.length }} chars</span>
                    </div>
                    <p class="whitespace-pre-wrap leading-relaxed">{{ chunk }}</p>
                  </div>
                  <div v-if="previewChunks.length === 0" class="text-center py-4 text-xs text-muted-foreground">
                    无预览结果，请检查分块参数
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <!-- Tab 3: Vector Embedding -->
          <TabsContent value="embedding" class="space-y-6 mt-0">
            <div class="space-y-4">
              <div class="space-y-2">
                <Label>选择模型 (Model)</Label>
                <Select 
                  :model-value="node.data?.config?.model_id"
                  @update:model-value="(v) => updateConfig('model_id', v)"
                >
                  <SelectTrigger class="h-10">
                    <SelectValue placeholder="选择嵌入模型..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem v-for="m in availableModels" :key="m.model_id" :value="m.model_id">
                        <div class="flex flex-col text-left">
                          <span class="font-medium">{{ m.name }}</span>
                          <span class="text-[10px] text-muted-foreground">{{ m.provider }}</span>
                        </div>
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label>向量维度</Label>
                  <Input 
                    type="number" 
                    :model-value="node.data?.config?.dimension ?? 1536"
                    @update:model-value="(v) => updateConfig('dimension', parseInt(v as string))"
                  />
                </div>
                <div class="space-y-2">
                  <Label>批处理大小</Label>
                  <Input 
                    type="number" 
                    :model-value="node.data?.config?.batch_size ?? 32"
                    @update:model-value="(v) => updateConfig('batch_size', parseInt(v as string))"
                  />
                </div>
              </div>

              <div class="space-y-3 pt-4 border-t">
                <div class="flex items-center justify-between">
                  <div class="space-y-0.5">
                    <Label class="text-xs">L2 归一化 (Normalization)</Label>
                    <p class="text-[10px] text-muted-foreground">将向量模长缩放为 1，推荐开启</p>
                  </div>
                  <Switch :checked="config.normalize ?? true" @update:checked="(v) => updateConfig('normalize', v)" />
                </div>
                
                <div class="flex items-center justify-between">
                  <div class="space-y-0.5">
                    <Label class="text-xs">添加元数据 (Metadata)</Label>
                    <p class="text-[10px] text-muted-foreground">将来源、页码等信息写入向量元数据</p>
                  </div>
                  <Switch :checked="config.add_metadata ?? true" @update:checked="(v) => updateConfig('add_metadata', v)" />
                </div>
              </div>
            </div>

            <div class="p-3 rounded-md bg-green-50 text-green-700 text-xs flex items-start gap-2" v-if="!validationErrors.length && config.model_id">
              <CheckCircle2 class="w-4 h-4 mt-0.5" />
              <div>
                <p class="font-medium">配置有效</p>
                <p class="opacity-90">已准备好处理向量化任务</p>
              </div>
            </div>
          </TabsContent>
        </div>
      </ScrollArea>
    </Tabs>
  </div>
</template>
