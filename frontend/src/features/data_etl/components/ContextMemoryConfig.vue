<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/toast/use-toast';
import { systemConfigApi, type ContextMemoryConfig } from '@/features/data_etl/api';

const { toast } = useToast();

const isLoading = ref(false);
const isSaving = ref(false);

const config = reactive<ContextMemoryConfig>({
  version: 1,
  context: {
    history_limit: 10,
    compression_threshold: 3000,
    enable_graph_memory: true,
    graph_hop_depth: 1,
  },
  memory: {
    enable_session_kb: true,
    embedding_model_id: 'text-embedding-3-small',
    memory_extraction_interval: 10,
  },
});

const applyConfig = (data: ContextMemoryConfig) => {
  config.version = data.version;
  config.context.history_limit = data.context.history_limit ?? 10;
  config.context.compression_threshold = data.context.compression_threshold ?? 3000;
  config.context.enable_graph_memory = data.context.enable_graph_memory ?? true;
  config.context.graph_hop_depth = data.context.graph_hop_depth ?? 1;
  
  config.memory.enable_session_kb = data.memory.enable_session_kb ?? true;
  config.memory.embedding_model_id = data.memory.embedding_model_id ?? 'text-embedding-3-small';
  config.memory.memory_extraction_interval = data.memory.memory_extraction_interval ?? 10;
};

const loadConfig = async () => {
  isLoading.value = true;
  try {
    const data = await systemConfigApi.getContextMemory();
    applyConfig(data);
  } catch (e: any) {
    toast({
      title: '加载失败',
      description: e?.message || '无法加载上下文与记忆配置',
      variant: 'destructive',
    });
  } finally {
    isLoading.value = false;
  }
};

const saveConfig = async () => {
  if (!Number.isFinite(config.context.history_limit) || config.context.history_limit < 0) {
    toast({ title: '参数错误', description: '历史条数必须是非负数', variant: 'destructive' });
    return;
  }
  if (!Number.isFinite(config.context.compression_threshold) || config.context.compression_threshold < 0) {
    toast({ title: '参数错误', description: '压缩阈值必须是非负数', variant: 'destructive' });
    return;
  }
  if (!config.memory.embedding_model_id?.trim()) {
    toast({ title: '参数错误', description: 'Embedding 模型ID不能为空', variant: 'destructive' });
    return;
  }

  isSaving.value = true;
  try {
    const saved = await systemConfigApi.updateContextMemory({
      version: config.version,
      context: { ...config.context },
      memory: { ...config.memory },
    });
    applyConfig(saved);
    toast({ title: '保存成功', description: '上下文与记忆配置已更新' });
  } catch (e: any) {
    toast({
      title: '保存失败',
      description: e?.response?.data?.detail || e?.message || '无法保存配置',
      variant: 'destructive',
    });
  } finally {
    isSaving.value = false;
  }
};

const resetConfig = async () => {
  isSaving.value = true;
  try {
    const data = await systemConfigApi.resetContextMemory();
    applyConfig(data);
    toast({ title: '已恢复默认', description: '上下文与记忆配置已恢复默认值' });
  } catch (e: any) {
    toast({
      title: '恢复失败',
      description: e?.response?.data?.detail || e?.message || '无法恢复默认配置',
      variant: 'destructive',
    });
  } finally {
    isSaving.value = false;
  }
};

onMounted(loadConfig);
</script>

<template>
  <div class="space-y-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">短期工作记忆</CardTitle>
        <CardDescription class="dark:text-slate-400">控制直接注入大模型上下文的历史消息窗口</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">保留历史轮数 (history_limit)</Label>
            <p class="text-xs text-muted-foreground mb-2">建议保留最近 5-15 轮，保持上下文精简，避免干扰</p>
            <Input
              type="number"
              min="0"
              step="1"
              :model-value="config.context.history_limit"
              :disabled="isLoading || isSaving"
              @update:modelValue="(v) => (config.context.history_limit = Number(v))"
            />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">旧压缩阈值 (tokens) <span class="text-orange-500 text-xs ml-1">已废弃</span></Label>
            <p class="text-xs text-muted-foreground mb-2">因引入图谱记忆，基于 Token 的暴力截断不再作为首选策略</p>
            <Input
              type="number"
              min="0"
              step="100"
              :model-value="config.context.compression_threshold"
              :disabled="isLoading || isSaving"
              @update:modelValue="(v) => (config.context.compression_threshold = Number(v))"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">长期图谱记忆</CardTitle>
        <CardDescription class="dark:text-slate-400">基于GraphRAG自动从历史对话中提取实体与关系，形成无限记忆网络</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-800">
          <div class="space-y-0.5">
            <Label class="text-base dark:text-slate-200">启用图谱记忆网络</Label>
            <p class="text-sm text-muted-foreground dark:text-slate-400">开启后，后台将自动分析对话提取知识图谱，并在新对话时通过 query_subgraph 动态召回</p>
          </div>
          <Switch
            :checked="config.context.enable_graph_memory"
            :disabled="isLoading || isSaving"
            @update:checked="(val) => (config.context.enable_graph_memory = val)"
          />
        </div>

        <div class="grid grid-cols-2 gap-6" v-if="config.context.enable_graph_memory">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">记忆提取频率 (消息数)</Label>
            <p class="text-xs text-muted-foreground mb-2">每累积多少条消息触发一次 LightRAG 实体提取</p>
            <Input
              type="number"
              min="1"
              max="100"
              step="1"
              :model-value="config.memory.memory_extraction_interval"
              :disabled="isLoading || isSaving"
              @update:modelValue="(v) => (config.memory.memory_extraction_interval = Number(v))"
            />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">图谱联想深度 (Hop-Depth)</Label>
            <p class="text-xs text-muted-foreground mb-2">召回记忆时向外扩展的层数（建议 1-2 跳）</p>
            <Input
              type="number"
              min="1"
              max="3"
              step="1"
              :model-value="config.context.graph_hop_depth"
              :disabled="isLoading || isSaving"
              @update:modelValue="(v) => (config.context.graph_hop_depth = Number(v))"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">会话知识库</CardTitle>
        <CardDescription class="dark:text-slate-400">控制用户上传文件时的向量化处理策略</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-800">
          <div class="space-y-0.5">
            <Label class="text-base dark:text-slate-200">启用会话知识库 (Session KB)</Label>
            <p class="text-sm text-muted-foreground dark:text-slate-400">用于文件知识注入与检索增强；关闭后仍可解析文件内容但不做向量化</p>
          </div>
          <Switch
            :checked="config.memory.enable_session_kb"
            :disabled="isLoading || isSaving"
            @update:checked="(val) => (config.memory.enable_session_kb = val)"
          />
        </div>

        <div class="space-y-2">
          <Label class="dark:text-slate-200">Embedding 模型ID</Label>
          <Input
            placeholder="text-embedding-3-small"
            :model-value="config.memory.embedding_model_id"
            :disabled="isLoading || isSaving"
            @update:modelValue="(v) => (config.memory.embedding_model_id = String(v))"
          />
        </div>

        <div class="pt-2 flex justify-end gap-2">
          <Button variant="secondary" :disabled="isLoading || isSaving" @click="resetConfig">恢复默认</Button>
          <Button :disabled="isLoading || isSaving" @click="saveConfig">保存配置</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
