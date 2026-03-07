<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { llmApi, type Model } from '../../api/llm';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);
const availableModels = ref<Model[]>([]);

const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

onMounted(async () => {
  try {
    const res = await llmApi.listModels();
    availableModels.value = res.filter(m => m.is_active);
  } catch (e) {
    console.error('Failed to fetch models', e);
  }
});
</script>

<template>
  <div class="space-y-4">
    <!-- Model Selection -->
    <div class="space-y-2">
      <Label>模型 (Model)</Label>
      <Select 
        :model-value="node.data?.config?.model"
        @update:model-value="(v) => updateConfig('model', v)"
      >
        <SelectTrigger>
          <SelectValue placeholder="Select a model" />
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

    <!-- Prompt Template -->
    <div class="space-y-2">
      <Label>提示模板 (Prompt Template)</Label>
      <textarea 
        placeholder="你是一个意图识别助手..." 
        class="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono text-xs"
        :value="node.data?.config?.prompt_template"
        @input="(e) => updateConfig('prompt_template', (e.target as HTMLTextAreaElement).value)"
      />
      <p class="text-xs text-muted-foreground" v-pre>使用 {{text}} 作为输入变量占位符。</p>
    </div>

    <!-- Few-shot Examples -->
    <div class="space-y-2">
      <Label>示例 (Few-shot Examples)</Label>
      <textarea 
        placeholder='[{"input": "退款", "intent": "refund"}]' 
        class="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono text-xs"
        :value="node.data?.config?.few_shot_examples"
        @input="(e) => updateConfig('few_shot_examples', (e.target as HTMLTextAreaElement).value)"
      />
    </div>

    <!-- Output Schema -->
    <div class="space-y-2">
      <Label>输出约束 (JSON Schema)</Label>
      <textarea 
        placeholder='{"type": "object", "properties": {"intent": {"type": "string"}}}' 
        class="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono text-xs"
        :value="node.data?.config?.output_schema"
        @input="(e) => updateConfig('output_schema', (e.target as HTMLTextAreaElement).value)"
      />
    </div>

    <!-- Advanced Parameters -->
    <Accordion type="single" collapsible class="w-full">
      <AccordionItem value="advanced">
        <AccordionTrigger>高级参数 (Advanced)</AccordionTrigger>
        <AccordionContent class="space-y-4 pt-2">
          <div class="space-y-2">
            <div class="flex justify-between">
              <Label>温度 (Temperature)</Label>
              <span class="text-xs text-muted-foreground">{{ node.data?.config?.temperature ?? 0.7 }}</span>
            </div>
            <Slider 
              :model-value="[node.data?.config?.temperature ?? 0.7]"
              :max="2" :step="0.1"
              @update:model-value="(v) => updateConfig('temperature', v?.[0])"
            />
          </div>

          <div class="space-y-2">
             <div class="flex justify-between">
              <Label>Top P</Label>
              <span class="text-xs text-muted-foreground">{{ node.data?.config?.top_p ?? 1.0 }}</span>
            </div>
            <Slider 
              :model-value="[node.data?.config?.top_p ?? 1.0]"
              :max="1" :step="0.05"
              @update:model-value="(v) => updateConfig('top_p', v?.[0])"
            />
          </div>

          <div class="space-y-2">
            <Label>最大 Token (Max Tokens)</Label>
            <Input 
              type="number" 
              :model-value="node.data?.config?.max_tokens ?? 1024"
              @update:model-value="(v) => updateConfig('max_tokens', parseInt(v as string))"
            />
          </div>

          <div class="space-y-2">
            <Label>超时时间 (Timeout ms)</Label>
             <Input 
              type="number" 
              :model-value="node.data?.config?.timeout ?? 3000"
              @update:model-value="(v) => updateConfig('timeout', parseInt(v as string))"
            />
          </div>

          <div class="flex items-center justify-between space-x-2">
            <Label>启用 A/B 测试 (A/B Testing)</Label>
            <Switch 
              :checked="node.data?.config?.ab_testing_enabled ?? false"
              @update:checked="(v) => updateConfig('ab_testing_enabled', v)"
            />
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  </div>
</template>
