<template>
  <div class="h-full flex bg-background overflow-hidden">
    <!-- Categories Sidebar -->
    <div 
      class="bg-card border-r flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20"
      :class="isSidebarCollapsed ? 'w-[60px]' : 'w-96'"
    >
      <!-- Sidebar Header -->
      <div class="p-4 flex items-center justify-between border-b h-16">
        <div class="flex items-center gap-3 overflow-hidden whitespace-nowrap" :class="{'opacity-0 w-0': isSidebarCollapsed}">
          <div class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary shadow-sm flex-shrink-0">
            <LayoutGrid class="w-4 h-4" />
          </div>
          <span class="font-semibold tracking-tight">模型分类</span>
        </div>
        
        <Button 
          variant="ghost" 
          size="icon" 
          class="h-8 w-8 ml-auto text-muted-foreground"
          @click="isSidebarCollapsed = !isSidebarCollapsed"
          :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
        >
          <ChevronLeft v-if="!isSidebarCollapsed" class="w-4 h-4" />
          <ChevronRight v-else class="w-4 h-4" />
        </Button>
      </div>

      <!-- Categories List -->
      <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
        <!-- 全部模型卡片单独占一行 -->
        <div class="mb-4">
          <Button
            v-if="providerCategories.length > 0"
            :variant="activeCategory === providerCategories[0].id ? 'secondary' : 'outline'"
            class="w-full justify-start gap-3 px-4 relative h-14 border rounded-xl shadow-sm transition-all hover:shadow-md"
            :class="[
              isSidebarCollapsed ? 'justify-center px-0' : '',
              activeCategory === providerCategories[0].id ? 'border-primary/50 bg-primary/10 ring-1 ring-primary/20' : 'border-border/60 hover:border-primary/30 bg-muted/10'
            ]"
            @click="activeCategory = providerCategories[0].id"
            :title="isSidebarCollapsed ? providerCategories[0].label : ''"
          >
            <component :is="providerCategories[0].icon" class="w-4 h-4 flex-shrink-0 text-primary" />
            
            <span 
              class="truncate transition-all duration-300 capitalize text-sm font-semibold"
              :class="isSidebarCollapsed ? 'w-0 opacity-0 hidden' : 'w-auto opacity-100'"
            >
              {{ providerCategories[0].label }}
            </span>
            
            <Badge 
              v-if="providerCategories[0].count !== undefined && !isSidebarCollapsed" 
              variant="secondary" 
              class="ml-auto text-xs h-6 px-2 min-w-[24px] flex items-center justify-center bg-background border shadow-sm"
            >
              {{ providerCategories[0].count }}
            </Badge>
          </Button>
        </div>

        <!-- 其他提供商网格 -->
        <div class="grid grid-cols-2 gap-4" :class="{'grid-cols-1': isSidebarCollapsed}">
          <Button
            v-for="item in providerCategories.slice(1)" 
            :key="item.id"
            :variant="activeCategory === item.id ? 'secondary' : 'outline'"
            class="w-full justify-start gap-3 px-3 relative h-14 border rounded-xl transition-all hover:shadow-md bg-card"
            :class="[
              isSidebarCollapsed ? 'justify-center px-0' : '',
              activeCategory === item.id ? 'border-primary/50 bg-primary/5 ring-1 ring-primary/20' : 'border-border/60 hover:border-primary/30'
            ]"
            @click="activeCategory = item.id"
            :title="isSidebarCollapsed ? item.label : ''"
          >
            <div v-if="item.initials" class="relative w-6 h-6 flex-shrink-0 flex items-center justify-center">
              <img 
                v-if="!logoErrors[item.id]"
                :src="getProviderLogo(item.id)" 
                class="w-5 h-5 object-contain"
                alt="logo"
                @error="handleLogoError(item.id)"
              />
              <!-- Initials Avatar Fallback -->
              <div 
                v-else
                class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border shadow-sm transition-all"
                :class="activeCategory === item.id 
                  ? 'bg-primary text-primary-foreground border-primary' 
                  : 'bg-muted/50 text-muted-foreground border-border group-hover:border-primary/50 group-hover:text-foreground'"
              >
                {{ item.initials }}
              </div>
            </div>
            <component v-else :is="item.icon" class="w-4 h-4 flex-shrink-0" />
            
            <span 
              class="truncate transition-all duration-300 capitalize text-sm font-medium"
              :class="isSidebarCollapsed ? 'w-0 opacity-0 hidden' : 'w-auto opacity-100'"
            >
              {{ item.label }}
            </span>
            
            <Badge 
              v-if="item.count !== undefined && !isSidebarCollapsed" 
              variant="secondary" 
              class="ml-auto text-xs h-6 px-2 min-w-[24px] flex items-center justify-center bg-muted/60"
            >
              {{ item.count }}
            </Badge>
          </Button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative bg-muted/10">
      <!-- Header Area -->
      <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">模型管理</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-xs text-muted-foreground m-0">
            配置和管理您的 LLM 模型接口，支持多种主流模型服务商。
          </p>
        </div>
      </div>

      <!-- Search & Filter Bar -->
      <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
        <!-- Left: Empty placeholder to balance flex layout -->
        <div class="hidden md:block w-full md:w-64"></div>
        
        <!-- Center: View Tabs -->
        <div class="flex items-center justify-center flex-1">
            <Tabs v-model="activeType" class="w-[300px]">
              <TabsList class="grid w-full grid-cols-4 h-9 bg-muted/80 p-1 rounded-lg border border-border/50 items-center">
                <TabsTrigger value="all" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">全部</TabsTrigger>
                <TabsTrigger value="text" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">文本</TabsTrigger>
                <TabsTrigger value="embedding" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">嵌入</TabsTrigger>
                <TabsTrigger value="image" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">图像</TabsTrigger>
              </TabsList>
            </Tabs>
        </div>

        <!-- Right: Actions -->
        <div class="flex items-center gap-3 w-full md:w-auto justify-end">
            <div class="relative w-full md:w-64 group">
               <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
               <Input 
                 v-model="searchQuery"
                 type="text" 
                 placeholder="搜索模型名称或ID..." 
                 class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50"
               />
               <button v-if="searchQuery" @click="searchQuery = ''"
                   class="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors">
                   <X class="h-4 w-4" />
               </button>
            </div>

            <div class="h-4 w-px bg-border hidden md:block mx-1"></div>

            <Button @click="handleRefresh" variant="outline" size="icon" :disabled="loading" class="h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95 flex-shrink-0" title="刷新列表">
              <RefreshCw class="w-4 h-4 text-muted-foreground" :class="{'animate-spin': loading}" />
            </Button>

            <Button @click="openCreateModal" size="sm" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
              <Plus class="w-3.5 h-3.5" />
              添加模型
            </Button>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar flex flex-col">
        <!-- Skeleton Loader -->
        <div v-if="loading && models.length === 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="n in 8" :key="n" class="border rounded-xl p-4 bg-card h-[180px] flex flex-col space-y-3 shadow-sm">
            <div class="flex gap-3">
              <Skeleton class="h-10 w-10 rounded-lg" />
              <div class="space-y-2 flex-1 pt-1">
                <Skeleton class="h-4 w-1/2" />
                <Skeleton class="h-3 w-1/4" />
              </div>
            </div>
            <div class="space-y-2 flex-1 pt-2">
              <Skeleton class="h-3 w-full" />
              <Skeleton class="h-3 w-5/6" />
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredModels.length === 0" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto text-muted-foreground animate-in fade-in duration-500">
          <div class="w-12 h-12 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
            <img src="/Placeholder/null.svg" alt="暂无内容" class="h-full w-full object-cover" />
          </div>
          <h3 class="text-xl font-semibold text-foreground mb-2">未找到相关模型</h3>
          <p class="text-sm max-w-sm text-center leading-relaxed mb-8 text-muted-foreground">
            我们找不到与您搜索条件匹配的模型。请尝试调整关键词或筛选条件，或者创建一个新模型。
          </p>
          <div class="flex gap-4">
            <Button variant="outline" @click="searchQuery = ''; activeType = 'all'; activeCategory = 'all'">
              清除筛选
            </Button>
            <Button @click="openCreateModal">
              <Plus class="w-4 h-4 mr-2" />
              创建模型
            </Button>
          </div>
        </div>

        <!-- Model Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-20 animate-in fade-in zoom-in duration-300">
          <ModelCard 
            v-for="model in filteredModels" 
            :key="model.id" 
            :item="model"
            :testing-id="testingId"
            @edit="openEditModal"
            @delete="confirmDelete"
            @toggle-status="handleToggleStatus"
            @test="handleTestConnection"
          />
        </div>
      </div>
    </div>

    <!-- Create/Edit Sheet -->
    <Sheet v-model:open="sheetOpen">
      <SheetContent class="sm:max-w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{{ isEdit ? '编辑模型' : '添加模型' }}</SheetTitle>
          <SheetDescription>
            配置模型的连接参数。带 <span class="text-destructive">*</span> 为必填项。
          </SheetDescription>
        </SheetHeader>
        
        <div class="grid gap-6 py-6">
          <!-- Basic Info -->
          <div class="grid gap-2">
            <Label for="name">模型名称 <span class="text-destructive">*</span></Label>
            <Input id="name" v-model="formState.name" placeholder="例如: GPT-4o 助手" />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="grid gap-2">
              <Label for="provider">提供商 <span class="text-destructive">*</span></Label>
              <Select v-model="formState.provider" @update:modelValue="handleProviderChange">
                <SelectTrigger>
                  <div v-if="formState.provider && providerConfig[formState.provider]" class="flex items-center gap-2">
                    <img 
                      v-if="!logoErrors[formState.provider]"
                      :src="getProviderLogo(formState.provider)" 
                      class="w-4 h-4 object-contain"
                      alt="logo"
                      @error="handleLogoError(formState.provider)"
                    />
                    <span>{{ providerConfig[formState.provider].label || formState.provider }}</span>
                  </div>
                  <SelectValue v-else placeholder="选择提供商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="(config, key) in providerConfig" :key="key" :value="key">
                    <div class="flex items-center gap-2">
                      <img 
                        v-if="!logoErrors[key]"
                        :src="getProviderLogo(key)" 
                        class="w-4 h-4 object-contain"
                        alt="logo"
                        @error="handleLogoError(key)"
                      />
                      <span>{{ config.label || key }}</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="grid gap-2">
              <Label for="type">模型类型 <span class="text-destructive">*</span></Label>
              <Select v-model="formState.model_type">
                <SelectTrigger>
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">文本 (Text)</SelectItem>
                  <SelectItem value="embedding">嵌入 (Embedding)</SelectItem>
                  <SelectItem value="multimodal">多模态 (Multimodal)</SelectItem>
                  <SelectItem value="image">图像生成 (Image)</SelectItem>
                  <SelectItem value="video">视频生成 (Video)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="grid gap-2">
            <div class="flex items-center justify-between">
              <Label for="model_id">模型 ID <span class="text-destructive">*</span></Label>
              <Button 
                variant="link" 
                size="sm" 
                class="h-auto p-0 text-xs" 
                @click="toggleCustomModel"
              >
                {{ isCustomModel ? '从列表选择' : '手动输入' }}
              </Button>
            </div>
            
            <div v-if="!isCustomModel && currentModelOptions.length > 0">
              <Select v-model="formState.model_id">
                <SelectTrigger>
                  <SelectValue placeholder="选择模型 ID" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="opt in currentModelOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Input 
              v-else 
              id="model_id" 
              v-model="formState.model_id" 
              placeholder="输入模型 ID，例如: gpt-4-turbo" 
            />
          </div>

          <div class="grid gap-2">
            <Label for="api_key">API Key</Label>
            <div class="relative">
              <Input 
                id="api_key" 
                :type="showApiKey ? 'text' : 'password'" 
                v-model="formState.api_key" 
                placeholder="sk-..." 
                class="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                @click="showApiKey = !showApiKey"
              >
                <Eye v-if="!showApiKey" class="h-4 w-4 text-muted-foreground" />
                <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
              </Button>
            </div>
          </div>

          <div class="grid gap-2">
            <Label for="base_url">Base URL</Label>
            <Input id="base_url" v-model="formState.base_url" placeholder="可选，例如: https://api.openai.com/v1" />
            <p class="text-[10px] text-muted-foreground">如果不填写，将使用提供商的默认地址。</p>
          </div>

          <!-- Advanced Settings -->
          <Accordion type="single" collapsible class="w-full border rounded-lg bg-muted/20">
            <AccordionItem value="advanced" class="border-0">
              <AccordionTrigger class="px-4 py-2 text-sm hover:no-underline hover:bg-muted/40 rounded-t-lg">
                <div class="flex items-center gap-2">
                   <Sliders class="w-4 h-4 text-muted-foreground" />
                   高级配置 (Advanced)
                </div>
              </AccordionTrigger>
              <AccordionContent class="px-4 py-4 space-y-4 border-t bg-card/50 rounded-b-lg">
                  
                  <!-- Token Limits -->
                  <div class="grid grid-cols-2 gap-4">
                      <div class="grid gap-2">
                          <Label class="text-xs">上下文长度 (Context Length)</Label>
                          <Input type="number" v-model.number="formState.context_length" placeholder="4096" />
                      </div>
                      <div class="grid gap-2">
                          <Label class="text-xs">最大输出 (Max Output)</Label>
                          <Input type="number" v-model.number="formState.max_output_tokens" placeholder="2048" />
                      </div>
                  </div>

                  <!-- Capabilities -->
                  <div class="space-y-2">
                      <Label class="text-xs font-medium">模型能力</Label>
                      <div class="grid grid-cols-2 gap-3">
                          <div class="flex items-center space-x-2 border p-2 rounded bg-background">
                              <Switch id="vision" v-model:checked="formState.supports_vision" />
                              <Label for="vision" class="text-xs cursor-pointer">视觉识别 (Vision)</Label>
                          </div>
                          <div class="flex items-center space-x-2 border p-2 rounded bg-background">
                              <Switch id="tools" v-model:checked="formState.supports_tools" />
                              <Label for="tools" class="text-xs cursor-pointer">函数调用 (Tools)</Label>
                          </div>
                          <div class="flex items-center space-x-2 border p-2 rounded bg-background">
                              <Switch id="json" v-model:checked="formState.supports_json_mode" />
                              <Label for="json" class="text-xs cursor-pointer">JSON 模式</Label>
                          </div>
                      </div>
                  </div>

                  <!-- Inference Params -->
                  <div class="grid grid-cols-2 gap-4 pt-2">
                      <div class="grid gap-2">
                          <Label class="text-xs">温度 (Temperature)</Label>
                          <Input type="number" step="0.1" min="0" max="2" v-model.number="formState.temperature" />
                      </div>
                      <div class="grid gap-2">
                          <Label class="text-xs">Top P</Label>
                          <Input type="number" step="0.1" min="0" max="1" v-model.number="formState.top_p" />
                      </div>
                  </div>
                  
                  <!-- Pricing -->
                  <div class="space-y-2 pt-2 border-t border-dashed">
                      <Label class="text-xs font-medium">成本定价 (每 1k Tokens)</Label>
                      <div class="grid grid-cols-2 gap-4">
                        <div class="grid gap-2">
                            <Label class="text-[10px] text-muted-foreground">输入价格 ($)</Label>
                            <Input type="number" step="0.000001" v-model.number="formState.input_token_price" />
                        </div>
                        <div class="grid gap-2">
                            <Label class="text-[10px] text-muted-foreground">输出价格 ($)</Label>
                            <Input type="number" step="0.000001" v-model.number="formState.output_token_price" />
                        </div>
                      </div>
                  </div>

              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <div class="flex items-center justify-between rounded-lg border p-4">
            <div class="space-y-0.5">
              <Label class="text-base">启用状态</Label>
              <p class="text-xs text-muted-foreground">控制该模型是否在应用中可用</p>
            </div>
            <Switch v-model:checked="formState.is_active" />
          </div>

          <!-- Connection Test Result inside Modal -->
          <div v-if="testResult" class="rounded-lg border p-3 text-sm flex items-start gap-3 animate-in fade-in slide-in-from-top-2" :class="testResult.success ? 'bg-green-50 text-green-700 border-green-200' : 'bg-destructive/10 text-destructive border-destructive/20'">
            <CheckCircle2 v-if="testResult.success" class="h-5 w-5 flex-shrink-0" />
            <XCircle v-else class="h-5 w-5 flex-shrink-0" />
            <span class="break-all">{{ testResult.message }}</span>
          </div>

        </div>

        <SheetFooter class="flex-col sm:flex-row gap-2">
          <Button variant="outline" type="button" @click="handleTestFormConnection" :disabled="testing" class="w-full sm:w-auto">
            <Loader2 v-if="testing" class="mr-2 h-4 w-4 animate-spin" />
            <Network v-else class="mr-2 h-4 w-4" />
            测试连接
          </Button>
          <Button type="submit" @click="handleSubmit" :disabled="submitting" class="w-full sm:w-auto">
            <Loader2 v-if="submitting" class="mr-2 h-4 w-4 animate-spin" />
            {{ isEdit ? '保存更改' : '创建模型' }}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>

    <!-- Delete Confirmation Dialog -->
    <AlertDialog v-model:open="deleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除模型?</AlertDialogTitle>
          <AlertDialogDescription>
            此操作不可撤销。这将永久删除模型 "{{ modelToDelete?.name }}" 及其配置信息。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="modelToDelete = null">取消</AlertDialogCancel>
          <AlertDialogAction @click="handleDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
            <Loader2 v-if="deleteLoading" class="mr-2 h-4 w-4 animate-spin" />
            删除
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <Toaster />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import ModelCard from './ModelCard.vue';
import { 
  Loader2, Plus, Bot, MoreHorizontal, Edit2, Trash2, 
  Eye, EyeOff, Network, CheckCircle2, XCircle, X,
  LayoutGrid, ChevronLeft, ChevronRight, RefreshCw, Search,
  Zap, Box, Brain, Globe, Cpu, Sliders
} from 'lucide-vue-next';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetFooter,
} from '@/components/ui/sheet';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/components/ui/toast/use-toast';
import { Toaster } from '@/components/ui/toast';

const { toast } = useToast();

const api = axios.create({
    baseURL: '/api/v1'
});

// State
const models = ref([]);
const loading = ref(false);
const sheetOpen = ref(false);
const submitting = ref(false);
const testing = ref(false); // For modal test
const testingId = ref(null); // For card test
const isEdit = ref(false);
const isCustomModel = ref(false);
const showApiKey = ref(false);
const testResult = ref(null);

const deleteDialogOpen = ref(false);
const deleteLoading = ref(false);
const modelToDelete = ref(null);

// Sidebar & Filter State
const isSidebarCollapsed = ref(false);
const activeCategory = ref('all');
const activeType = ref('all');
const searchQuery = ref('');

const logoErrors = ref({});
const handleLogoError = (id) => {
    logoErrors.value[id] = true;
};

const getProviderLogo = (provider) => {
    if (!provider) return '';
    const providerMap = {
        'openai': 'openai',
        'anthropic': 'anthropic',
        'google': 'google',
        'gemini': 'gemini',
        'aliyun': 'qwen',
        'dashscope': 'qwen',
        'deepseek': 'deepseek',
        'claude': 'claude',
        'aws': 'aws',
        'bedrock': 'bedrock',
        'azure': 'azureai',
        'mistral': 'mistral',
        'groq': 'groq',
        'xai': 'xai',
        'cohere': 'cohere',
        'perplexity': 'perplexity',
        'together': 'together',
        'openrouter': 'openrouter',
        'nvidia': 'nvidia',
        'ollama': 'ollama',
        'fireworks': 'fireworks',
        'nebius': 'nebius',
        'vertexai': 'vertexai'
    };
    const key = provider.toLowerCase();
    const logoName = providerMap[key] || key;
    return `/flags/llm/${logoName}.svg`;
};

const isAdvancedMode = ref(false);

const formState = reactive({
    id: null,
    name: '',
    provider: '',
    model_id: '',
    model_type: 'text',
    api_key: '',
    base_url: '',
    
    // Advanced Params
    context_length: 4096,
    max_output_tokens: 2048,
    temperature: 0.7,
    top_p: 1.0,
    supports_vision: false,
    supports_tools: true,
    supports_json_mode: true,
    
    input_token_price: 0.0,
    output_token_price: 0.0,
    
    is_active: true
});

const providerConfig = ref({});

const currentModelOptions = ref([]);

// Computed Properties
const providerCategories = computed(() => {
    const counts = {};
    models.value.forEach(m => {
        counts[m.provider] = (counts[m.provider] || 0) + 1;
    });

    const categories = [
        { id: 'all', label: '全部模型', icon: LayoutGrid, count: models.value.length },
    ];
    
    // Add dynamic categories from providerConfig
    Object.keys(providerConfig.value).forEach(key => {
        const config = providerConfig.value[key];
  
        categories.push({
            id: key,
            label: config.label || key,
            initials: (config.label || key).substring(0, 1).toUpperCase(),
            // country: config.country, // Backend doesn't provide country yet, maybe map it locally or skip
            count: counts[key] || 0
        });
    });
    
    // Always add "Other" if there are models with unknown providers
    const knownProviders = Object.keys(providerConfig.value);
    const otherCount = models.value.filter(m => !knownProviders.includes(m.provider)).length;
    
    if (otherCount > 0) {
        categories.push({ id: 'other', label: '其他', initials: 'O', count: otherCount });
    }

    return categories;
});

const filteredModels = computed(() => {
    return models.value.filter(model => {
        // Search Filter
        if (searchQuery.value) {
            const query = searchQuery.value.toLowerCase();
            const matchesName = model.name.toLowerCase().includes(query);
            const matchesId = model.model_id.toLowerCase().includes(query);
            if (!matchesName && !matchesId) return false;
        }

        // Category (Provider) Filter
        if (activeCategory.value !== 'all') {
            if (model.provider !== activeCategory.value) return false;
        }

        // Type Filter
        if (activeType.value !== 'all') {
            if (model.model_type !== activeType.value) return false;
        }

        return true;
    });
});

// Methods
const fetchProviders = async () => {
    try {
        const res = await api.get('/llm/providers');
        providerConfig.value = res.data;
    } catch (e) {
        console.error("Failed to fetch providers", e);
    }
};

const fetchModels = async (forceRefresh = false) => {
    loading.value = true;
    try {
        const params = forceRefresh ? { _t: Date.now() } : {};
        const res = await api.get('/llm/models', { params });
        models.value = res.data;
    } catch (e) {
        toast({
            title: "获取失败",
            description: "无法加载模型列表，请稍后重试。",
            variant: "destructive"
        });
    } finally {
        loading.value = false;
    }
};

const handleRefresh = async () => {
    loading.value = true;
    models.value = [];
    await new Promise(resolve => setTimeout(resolve, 300));
    await fetchModels(true);
    toast({ title: '刷新成功', description: '模型数据已更新' });
};

const handleProviderChange = (val) => {
    const config = providerConfig.value[val];
    if (config) {
        formState.base_url = config.baseUrl || '';
        currentModelOptions.value = (config.models || []).map(m => ({ value: m, label: m }));
        
        if (config.models && config.models.length > 0) {
            if (!config.models.includes(formState.model_id)) {
                formState.model_id = config.models[0];
            }
            isCustomModel.value = false;
        } else {
            isCustomModel.value = true;
            if (!formState.model_id) formState.model_id = '';
        }
    } else {
        currentModelOptions.value = [];
        isCustomModel.value = true;
    }
};

const toggleCustomModel = () => {
    isCustomModel.value = !isCustomModel.value;
    if (!isCustomModel.value && currentModelOptions.value.length > 0) {
        if (!currentModelOptions.value.find(o => o.value === formState.model_id)) {
            formState.model_id = currentModelOptions.value[0].value;
        }
    }
};

const openCreateModal = () => {
    isEdit.value = false;
    isAdvancedMode.value = false;
    testResult.value = null;
    const defaultProvider = Object.keys(providerConfig.value)[0] || '';
    Object.assign(formState, {
        id: null,
        name: '',
        provider: defaultProvider,
        model_id: '',
        model_type: 'text',
        api_key: '',
        base_url: '',
        context_length: 4096,
        max_output_tokens: 2048,
        temperature: 0.7,
        top_p: 1.0,
        supports_vision: false,
        supports_tools: true,
        supports_json_mode: true,
        input_token_price: 0.0,
        output_token_price: 0.0,
        is_active: true
    });
    handleProviderChange(defaultProvider);
    sheetOpen.value = true;
};

const openEditModal = (record) => {
    isEdit.value = true;
    isAdvancedMode.value = false; // Reset unless user expands it
    testResult.value = null;
    
    const config = providerConfig.value[record.provider];
    if (config) {
        currentModelOptions.value = (config.models || []).map(m => ({ value: m, label: m }));
        const isInList = config.models && config.models.includes(record.model_id);
        isCustomModel.value = !isInList;
    } else {
        currentModelOptions.value = [];
        isCustomModel.value = true;
    }

    Object.assign(formState, {
        id: record.id,
        name: record.name,
        provider: record.provider,
        model_id: record.model_id,
        model_type: record.model_type || 'text',
        api_key: record.api_key,
        base_url: record.base_url,
        
        // Map new fields
        context_length: record.context_length ?? 4096,
        max_output_tokens: record.max_output_tokens ?? 2048,
        temperature: record.temperature ?? 0.7,
        top_p: record.top_p ?? 1.0,
        supports_vision: record.supports_vision ?? false,
        supports_tools: record.supports_tools ?? true,
        supports_json_mode: record.supports_json_mode ?? true,
        input_token_price: record.input_token_price ?? 0.0,
        output_token_price: record.output_token_price ?? 0.0,
        
        is_active: record.is_active
    });
    sheetOpen.value = true;
};

const handleSubmit = async () => {
    if (!formState.name || !formState.model_id) {
        toast({
            title: "表单错误",
            description: "请填写所有必填项 (名称, 提供商, 模型 ID)",
            variant: "destructive"
        });
        return;
    }

    submitting.value = true;
    try {
        if (isEdit.value) {
            await api.put(`/llm/models/${formState.id}`, formState);
            toast({
                title: "更新成功",
                description: `模型 "${formState.name}" 已更新。`
            });
        } else {
            await api.post('/llm/models', formState);
            toast({
                title: "创建成功",
                description: `模型 "${formState.name}" 已创建。`
            });
        }
        sheetOpen.value = false;
        fetchModels();
    } catch (e) {
        toast({
            title: "操作失败",
            description: e.response?.data?.detail || e.message || "请求失败",
            variant: "destructive"
        });
    } finally {
        submitting.value = false;
    }
};

const handleTestFormConnection = async () => {
    if (!formState.provider || !formState.model_id) {
        toast({ title: "参数缺失", description: "请先填写提供商和模型 ID", variant: "destructive" });
        return;
    }
    testing.value = true;
    testResult.value = null;
    await performTest(formState, (result) => {
        testResult.value = result;
    });
    testing.value = false;
};

const handleTestConnection = async (model) => {
    testingId.value = model.id;
    await performTest(model, () => {});
    testingId.value = null;
};

const performTest = async (modelData, callback) => {
    try {
        const res = await api.post('/llm/models/test', {
            provider: modelData.provider,
            model_id: modelData.model_id,
            api_key: modelData.api_key,
            base_url: modelData.base_url
        });
        
        if (res.data.success) {
            callback({ success: true, message: res.data.message || '连接测试成功！' });
            toast({
                title: "测试成功",
                description: `${modelData.name || '模型'} 连接正常。`,
                class: "bg-green-500 text-white border-none"
            });
        } else {
            callback({ success: false, message: res.data.message || '连接测试失败' });
            toast({
                title: "测试失败",
                description: res.data.message,
                variant: "destructive"
            });
        }
    } catch (e) {
        const errMsg = e.response?.data?.detail || e.message;
        callback({ success: false, message: '请求失败: ' + errMsg });
        toast({
            title: "连接错误",
            description: errMsg,
            variant: "destructive"
        });
    }
};

const confirmDelete = (model) => {
    modelToDelete.value = model;
    deleteDialogOpen.value = true;
};

const handleDelete = async () => {
    if (!modelToDelete.value) return;
    deleteLoading.value = true;
    try {
        await api.delete(`/llm/models/${modelToDelete.value.id}`);
        toast({
            title: "删除成功",
            description: "模型已删除。"
        });
        fetchModels();
    } catch (e) {
        toast({
            title: "删除失败",
            description: "无法删除该模型，请稍后重试。",
            variant: "destructive"
        });
    } finally {
        deleteLoading.value = false;
        deleteDialogOpen.value = false;
        modelToDelete.value = null;
    }
};

const handleToggleStatus = async (model) => {
    try {
        const newStatus = !model.is_active;
        await api.put(`/llm/models/${model.id}`, { is_active: newStatus });
        model.is_active = newStatus; // Update local state
        toast({
            description: `模型已${newStatus ? '启用' : '禁用'}`
        });
    } catch (e) {
        toast({
            title: "更新失败",
            description: "无法修改状态",
            variant: "destructive"
        });
    }
};

onMounted(() => {
    fetchProviders();
    fetchModels();
});
</script>
