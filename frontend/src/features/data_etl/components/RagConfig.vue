<script setup lang="ts">
import { reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();

const config = reactive({
  chunkStrategy: 'semantic',
  chunkSize: 1200,
  chunkOverlap: 120,
  semanticThreshold: 0.8,
  rerankEnabled: false,
  rerankModel: 'cross-encoder/ms-marco-MiniLM-L-6-v2',
  ocrEnabled: false,
  docParseBackends: 'docling,pymupdf,pdfplumber,pypdf,ocr',
  contextTokensLimit: 6000
});

const saveConfig = () => {
  toast({
    title: '保存成功',
    description: '知识库与 RAG 策略配置已更新',
  });
};
</script>

<template>
  <div class="space-y-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">切分与解析策略</CardTitle>
        <CardDescription class="dark:text-slate-400">配置文档入库时的解析和切分参数</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">切分策略 (Chunk Strategy)</Label>
            <Select v-model="config.chunkStrategy">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择策略" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="fixed" class="dark:text-slate-200">固定长度 (Fixed Size)</SelectItem>
                <SelectItem value="recursive" class="dark:text-slate-200">递归字符 (Recursive Character)</SelectItem>
                <SelectItem value="semantic" class="dark:text-slate-200">语义分割 (Semantic)</SelectItem>
                <SelectItem value="markdown" class="dark:text-slate-200">Markdown 结构化</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">PDF 解析引擎</Label>
            <Input v-model="config.docParseBackends" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">块大小 (Chunk Size)</Label>
            <Input type="number" v-model.number="config.chunkSize" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">块重叠 (Chunk Overlap)</Label>
            <Input type="number" v-model.number="config.chunkOverlap" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2" v-if="config.chunkStrategy === 'semantic'">
            <Label class="dark:text-slate-200">相似度阈值 (Threshold)</Label>
            <Input type="number" step="0.05" min="0.1" max="1" v-model.number="config.semanticThreshold" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2 flex flex-col justify-end pb-2" :class="{'col-start-1': config.chunkStrategy === 'semantic'}">
            <div class="flex items-center space-x-2">
              <Switch id="ocr-enabled" :checked="config.ocrEnabled" @update:checked="(val) => config.ocrEnabled = val" />
              <Label htmlFor="ocr-enabled" class="cursor-pointer dark:text-slate-200">开启 OCR 增强</Label>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">检索与重排配置</CardTitle>
        <CardDescription class="dark:text-slate-400">配置 RAG 召回时的排序与上下文限制</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2 flex flex-col justify-center">
            <div class="flex items-center space-x-2">
              <Switch id="rerank-enabled" :checked="config.rerankEnabled" @update:checked="(val) => config.rerankEnabled = val" />
              <Label htmlFor="rerank-enabled" class="cursor-pointer dark:text-slate-200">开启 Rerank 重排</Label>
            </div>
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">上下文 Token 限制</Label>
            <Input type="number" v-model.number="config.contextTokensLimit" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="space-y-2" v-if="config.rerankEnabled">
          <Label class="dark:text-slate-200">重排模型 (Rerank Model)</Label>
          <Input v-model="config.rerankModel" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
        </div>

        <div class="pt-4 flex justify-end">
          <Button @click="saveConfig">保存配置</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>