<script setup lang="ts">
import { reactive, ref } from 'vue';
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
import { useToast } from '@/components/ui/toast/use-toast';
import { Eye, EyeOff } from 'lucide-vue-next';

const { toast } = useToast();

const config = reactive({
  defaultProvider: 'openai',
  defaultModel: 'gpt-3.5-turbo',
  openaiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  deepseekKey: '',
  tavilyKey: '',
  firecrawlKey: '',
  e2bKey: ''
});

const showKeys = reactive<Record<string, boolean>>({
  openai: false,
  deepseek: false,
  tavily: false,
  firecrawl: false,
  e2b: false
});

const saveConfig = () => {
  toast({
    title: '保存成功',
    description: '模型与工具集成配置已更新',
  });
};
</script>

<template>
  <div class="space-y-6">
    <!-- 默认 LLM 配置 -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">全局默认大模型配置</CardTitle>
        <CardDescription class="dark:text-slate-400">设置系统默认使用的模型供应商及模型ID</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">默认提供商 (Provider)</Label>
            <Select v-model="config.defaultProvider">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择提供商" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="openai" class="dark:text-slate-200">OpenAI</SelectItem>
                <SelectItem value="deepseek" class="dark:text-slate-200">DeepSeek</SelectItem>
                <SelectItem value="aliyun" class="dark:text-slate-200">阿里云 (DashScope)</SelectItem>
                <SelectItem value="anthropic" class="dark:text-slate-200">Anthropic (Claude)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">默认模型 ID</Label>
            <Input v-model="config.defaultModel" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 模型 API Key 配置 -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">大模型 API Keys</CardTitle>
        <CardDescription class="dark:text-slate-400">配置各模型供应商的访问密钥</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="space-y-2">
          <Label class="dark:text-slate-200">OpenAI API Key</Label>
          <div class="relative">
            <Input :type="showKeys.openai ? 'text' : 'password'" v-model="config.openaiKey" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 pr-10" />
            <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground" @click="showKeys.openai = !showKeys.openai">
              <Eye v-if="!showKeys.openai" class="h-4 w-4" />
              <EyeOff v-else class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div class="space-y-2">
          <Label class="dark:text-slate-200">DeepSeek API Key</Label>
          <div class="relative">
            <Input :type="showKeys.deepseek ? 'text' : 'password'" v-model="config.deepseekKey" placeholder="sk-..." class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 pr-10" />
            <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground" @click="showKeys.deepseek = !showKeys.deepseek">
              <Eye v-if="!showKeys.deepseek" class="h-4 w-4" />
              <EyeOff v-else class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 第三方工具配置 -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">常用插件与工具密钥</CardTitle>
        <CardDescription class="dark:text-slate-400">配置搜索、沙箱等第三方工具的访问密钥</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">Tavily Search API Key</Label>
            <div class="relative">
              <Input :type="showKeys.tavily ? 'text' : 'password'" v-model="config.tavilyKey" placeholder="tvly-..." class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 pr-10" />
              <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground" @click="showKeys.tavily = !showKeys.tavily">
                <Eye v-if="!showKeys.tavily" class="h-4 w-4" />
                <EyeOff v-else class="h-4 w-4" />
              </Button>
            </div>
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">FireCrawl API Key</Label>
            <div class="relative">
              <Input :type="showKeys.firecrawl ? 'text' : 'password'" v-model="config.firecrawlKey" placeholder="fc-..." class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 pr-10" />
              <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground" @click="showKeys.firecrawl = !showKeys.firecrawl">
                <Eye v-if="!showKeys.firecrawl" class="h-4 w-4" />
                <EyeOff v-else class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <div class="space-y-2">
          <Label class="dark:text-slate-200 text-lg font-bold">Sandbox API Key</Label>
          <div class="relative">
            <Input :type="showKeys.e2b ? 'text' : 'password'" v-model="config.e2bKey" placeholder="e2b_..." class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 pr-10" />
            <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground" @click="showKeys.e2b = !showKeys.e2b">
              <Eye v-if="!showKeys.e2b" class="h-4 w-4" />
              <EyeOff v-else class="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <div class="pt-4 flex justify-end">
          <Button @click="saveConfig">保存配置</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>