<script setup lang="ts">
import { ref } from 'vue';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Eye, EyeOff, Activity, DollarSign, Database, Cpu } from 'lucide-vue-next';

const temperature = ref([0.7]);
const showKey = ref(false);
const apiKey = ref('sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');

const embeddingStats = [
  { label: '向量维度', value: '3072', icon: Activity, color: 'text-blue-500 dark:text-blue-400' },
  { label: '本月消耗', value: '1.04M', unit: 'tokens', icon: Database, color: 'text-blue-500 dark:text-blue-400' },
  { label: '预估费用', value: '$13.52', icon: DollarSign, color: 'text-green-500 dark:text-green-400' },
];

const llmStats = [
  { label: '上下文长度', value: '128K', icon: Cpu, color: 'text-purple-500 dark:text-purple-400' },
  { label: '本月消耗', value: '3.69M', unit: 'tokens', icon: Database, color: 'text-purple-500 dark:text-purple-400' },
  { label: '预估费用', value: '$110.70', icon: DollarSign, color: 'text-green-500 dark:text-green-400' },
];
</script>

<template>
  <div class="space-y-6">
    <!-- Embedding Model Card -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div class="space-y-1">
            <CardTitle class="flex items-center gap-2 dark:text-slate-50">
              Embedding Model
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            </CardTitle>
            <CardDescription class="dark:text-slate-400">向量化模型配置</CardDescription>
          </div>
          <Badge variant="outline" class="bg-green-50 text-green-700 border-green-200 gap-1 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
            <Activity class="w-3 h-3" />
            已连接
          </Badge>
        </div>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">选择模型</Label>
            <Select default-value="large">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择模型" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="large" class="dark:text-slate-200 dark:focus:bg-slate-800">text-embedding-3-large (3072d)</SelectItem>
                <SelectItem value="small" class="dark:text-slate-200 dark:focus:bg-slate-800">text-embedding-3-small (1536d)</SelectItem>
                <SelectItem value="ada" class="dark:text-slate-200 dark:focus:bg-slate-800">text-embedding-ada-002 (1536d)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label class="dark:text-slate-200">API Key</Label>
            <div class="relative">
              <Input 
                :type="showKey ? 'text' : 'password'" 
                v-model="apiKey" 
                readonly 
                class="pr-10 font-mono dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" 
              />
              <Button
                variant="ghost"
                size="icon"
                class="absolute right-0 top-0 h-full px-3 hover:bg-transparent dark:hover:bg-transparent"
                @click="showKey = !showKey"
              >
                <component :is="showKey ? EyeOff : Eye" class="w-4 h-4 text-muted-foreground dark:text-slate-400" />
              </Button>
            </div>
          </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-3 gap-4">
          <div 
            v-for="(stat, index) in embeddingStats" 
            :key="index"
            class="p-4 rounded-lg border bg-muted/50 flex flex-col justify-between group hover:border-primary/20 transition-colors dark:bg-slate-900/50 dark:border-slate-800"
          >
            <div>
              <p class="text-xs text-muted-foreground font-medium mb-1 dark:text-slate-400">{{ stat.label }}</p>
              <div class="text-xl font-bold tracking-tight dark:text-slate-100">
                {{ stat.value }}
                <span v-if="stat.unit" class="text-xs font-normal text-muted-foreground dark:text-slate-500">{{ stat.unit }}</span>
              </div>
            </div>
            <component :is="stat.icon" class="w-8 h-8 self-end opacity-10 group-hover:opacity-20 transition-opacity" :class="stat.color" />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- RAG LLM Card -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div class="space-y-1">
            <CardTitle class="flex items-center gap-2 dark:text-slate-50">
              RAG LLM
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            </CardTitle>
            <CardDescription class="dark:text-slate-400">大语言模型配置</CardDescription>
          </div>
          <Badge variant="outline" class="bg-green-50 text-green-700 border-green-200 gap-1 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
            <Activity class="w-3 h-3" />
            已连接
          </Badge>
        </div>
      </CardHeader>
      <CardContent class="space-y-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">选择模型</Label>
            <Select default-value="gpt4-turbo">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择模型" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="gpt4-turbo" class="dark:text-slate-200 dark:focus:bg-slate-800">GPT-4 Turbo (128K context)</SelectItem>
                <SelectItem value="gpt4o" class="dark:text-slate-200 dark:focus:bg-slate-800">GPT-4o</SelectItem>
                <SelectItem value="claude-3-5" class="dark:text-slate-200 dark:focus:bg-slate-800">Claude 3.5 Sonnet</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <Label class="dark:text-slate-200">Temperature</Label>
              <span class="text-xs font-mono bg-muted px-2 py-0.5 rounded text-muted-foreground dark:bg-slate-900 dark:text-slate-400">{{ temperature[0] }}</span>
            </div>
            <Slider
              v-model="temperature"
              :max="1"
              :step="0.1"
              class="w-full"
            />
            <div class="flex justify-between text-[10px] text-muted-foreground uppercase tracking-wider font-medium dark:text-slate-500">
              <span>Precise</span>
              <span>Balanced</span>
              <span>Creative</span>
            </div>
          </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-3 gap-4">
          <div 
            v-for="(stat, index) in llmStats" 
            :key="index"
            class="p-4 rounded-lg border bg-muted/50 flex flex-col justify-between group hover:border-primary/20 transition-colors dark:bg-slate-900/50 dark:border-slate-800"
          >
            <div>
              <p class="text-xs text-muted-foreground font-medium mb-1 dark:text-slate-400">{{ stat.label }}</p>
              <div class="text-xl font-bold tracking-tight dark:text-slate-100">
                {{ stat.value }}
                <span v-if="stat.unit" class="text-xs font-normal text-muted-foreground dark:text-slate-500">{{ stat.unit }}</span>
              </div>
            </div>
            <component :is="stat.icon" class="w-8 h-8 self-end opacity-10 group-hover:opacity-20 transition-opacity" :class="stat.color" />
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
