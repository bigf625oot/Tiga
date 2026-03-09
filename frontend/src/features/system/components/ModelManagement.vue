<template>
  <div class="container mx-auto py-6 max-w-7xl animate-in fade-in duration-500">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
      <div>
        <h2 class="text-2xl font-bold tracking-tight">模型管理</h2>
        <p class="text-muted-foreground text-sm mt-1">配置和管理您的 LLM 模型接口，支持多种主流模型服务商。</p>
      </div>
      <Button @click="openCreateModal" class="shadow-sm">
        <Plus class="mr-2 h-4 w-4" />
        添加模型
      </Button>
    </div>

    <!-- Main Content -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
      <!-- Loading State -->
      <div v-if="loading" class="p-8 flex justify-center items-center">
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <!-- Empty State -->
      <div v-else-if="models.length === 0" class="flex flex-col items-center justify-center p-12 text-center">
        <div class="bg-muted/50 p-4 rounded-full mb-4">
          <Bot class="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 class="text-lg font-semibold">暂无模型</h3>
        <p class="text-muted-foreground text-sm max-w-sm mt-2 mb-6">
          您还没有配置任何模型。添加一个模型以开始使用智能功能。
        </p>
        <Button variant="outline" @click="openCreateModal">
          <Plus class="mr-2 h-4 w-4" />
          立即添加
        </Button>
      </div>

      <!-- Data Table -->
      <Table v-else>
        <TableHeader>
          <TableRow>
            <TableHead class="w-[200px]">名称</TableHead>
            <TableHead>提供商</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>模型 ID</TableHead>
            <TableHead>状态</TableHead>
            <TableHead class="hidden md:table-cell">创建时间</TableHead>
            <TableHead class="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="model in models" :key="model.id" class="group">
            <TableCell class="font-medium">
              <div class="flex items-center gap-2">
                <div class="p-1.5 rounded-md bg-primary/10 text-primary">
                  <Bot class="h-4 w-4" />
                </div>
                <span>{{ model.name }}</span>
              </div>
            </TableCell>
            <TableCell>
              <Badge variant="outline" class="capitalize">
                {{ model.provider }}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge :variant="getModelTypeVariant(model.model_type)" class="capitalize">
                {{ getModelTypeLabel(model.model_type) }}
              </Badge>
            </TableCell>
            <TableCell class="font-mono text-xs text-muted-foreground">
              {{ model.model_id }}
            </TableCell>
            <TableCell>
              <div class="flex items-center gap-2">
                <Switch 
                  :checked="model.is_active" 
                  @update:checked="(val) => handleStatusChange(model, val)"
                  :disabled="model.statusLoading"
                />
                <span class="text-xs text-muted-foreground w-8">
                  {{ model.is_active ? '启用' : '禁用' }}
                </span>
              </div>
            </TableCell>
            <TableCell class="hidden md:table-cell text-muted-foreground text-xs">
              {{ formatDate(model.created_at) }}
            </TableCell>
            <TableCell class="text-right">
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button variant="ghost" size="icon" class="h-8 w-8">
                    <MoreHorizontal class="h-4 w-4" />
                    <span class="sr-only">打开菜单</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>操作</DropdownMenuLabel>
                  <DropdownMenuItem @click="openEditModal(model)">
                    <Edit2 class="mr-2 h-4 w-4" />
                    编辑
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem @click="confirmDelete(model)" class="text-destructive focus:text-destructive">
                    <Trash2 class="mr-2 h-4 w-4" />
                    删除
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
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
                  <SelectValue placeholder="选择提供商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="aliyun">Aliyun (通义千问)</SelectItem>
                  <SelectItem value="deepseek">DeepSeek</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                  <SelectItem value="google">Google</SelectItem>
                  <SelectItem value="local">Local (Ollama/vLLM)</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
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

          <div class="flex items-center justify-between rounded-lg border p-4">
            <div class="space-y-0.5">
              <Label class="text-base">启用状态</Label>
              <p class="text-xs text-muted-foreground">控制该模型是否在应用中可用</p>
            </div>
            <Switch v-model:checked="formState.is_active" />
          </div>

          <!-- Connection Test -->
          <div v-if="testResult" class="rounded-lg border p-3 text-sm flex items-start gap-3 animate-in fade-in slide-in-from-top-2" :class="testResult.success ? 'bg-green-50 text-green-700 border-green-200' : 'bg-destructive/10 text-destructive border-destructive/20'">
            <CheckCircle2 v-if="testResult.success" class="h-5 w-5 flex-shrink-0" />
            <XCircle v-else class="h-5 w-5 flex-shrink-0" />
            <span class="break-all">{{ testResult.message }}</span>
          </div>

        </div>

        <SheetFooter class="flex-col sm:flex-row gap-2">
          <Button variant="outline" type="button" @click="handleTestConnection" :disabled="testing" class="w-full sm:w-auto">
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
import { 
  Loader2, Plus, Bot, MoreHorizontal, Edit2, Trash2, 
  Eye, EyeOff, Network, CheckCircle2, XCircle 
} from 'lucide-vue-next';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetFooter,
} from '@/components/ui/sheet';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
const testing = ref(false);
const isEdit = ref(false);
const isCustomModel = ref(false);
const showApiKey = ref(false);
const testResult = ref(null);

const deleteDialogOpen = ref(false);
const deleteLoading = ref(false);
const modelToDelete = ref(null);

const formState = reactive({
    id: null,
    name: '',
    provider: 'openai',
    model_id: '',
    model_type: 'text',
    api_key: '',
    base_url: '',
    is_active: true
});

const providerConfig = {
    openai: {
        baseUrl: 'https://api.openai.com/v1',
        models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'dall-e-3', 'text-embedding-3-small', 'text-embedding-3-large']
    },
    aliyun: {
        baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        models: ['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-vl-max', 'qwen-vl-plus', 'wanx-v1']
    },
    deepseek: {
        baseUrl: 'https://api.deepseek.com',
        models: ['deepseek-chat', 'deepseek-reasoner', 'deepseek-embed']
    },
    anthropic: {
        baseUrl: 'https://api.anthropic.com/v1',
        models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
    },
    google: {
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
        models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro-vision']
    },
    local: {
        baseUrl: 'http://localhost:11434/v1',
        models: ['llama3', 'mistral', 'qwen2']
    },
    other: {
        baseUrl: '',
        models: []
    }
};

const currentModelOptions = ref([]);

// Methods
const fetchModels = async () => {
    loading.value = true;
    try {
        const res = await api.get('/llm/models');
        models.value = res.data.map(m => ({ ...m, statusLoading: false }));
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

const handleProviderChange = (val) => {
    const config = providerConfig[val];
    if (config) {
        formState.base_url = config.baseUrl;
        currentModelOptions.value = config.models.map(m => ({ value: m, label: m }));
        
        // Logic to reset or keep model_id
        if (config.models.length > 0) {
            // If current model_id is not in the new list, reset to first available
            if (!config.models.includes(formState.model_id)) {
                formState.model_id = config.models[0];
            }
            isCustomModel.value = false;
        } else {
            // If no predefined models, switch to custom input
            isCustomModel.value = true;
            if (!formState.model_id) formState.model_id = '';
        }
        
        if (val === 'local' || val === 'other') {
            isCustomModel.value = true;
        }
    } else {
        currentModelOptions.value = [];
        isCustomModel.value = true;
    }
};

const toggleCustomModel = () => {
    isCustomModel.value = !isCustomModel.value;
    if (!isCustomModel.value && currentModelOptions.value.length > 0) {
        // Switching back to list, ensure valid selection
        if (!currentModelOptions.value.find(o => o.value === formState.model_id)) {
            formState.model_id = currentModelOptions.value[0].value;
        }
    }
};

const openCreateModal = () => {
    isEdit.value = false;
    testResult.value = null;
    Object.assign(formState, {
        id: null,
        name: '',
        provider: 'openai',
        model_id: '',
        model_type: 'text',
        api_key: '',
        base_url: '',
        is_active: true
    });
    // Trigger provider change to set defaults
    handleProviderChange('openai');
    sheetOpen.value = true;
};

const openEditModal = (record) => {
    isEdit.value = true;
    testResult.value = null;
    
    // Set provider first to populate options
    const config = providerConfig[record.provider];
    if (config) {
        currentModelOptions.value = config.models.map(m => ({ value: m, label: m }));
        const isInList = config.models.includes(record.model_id);
        isCustomModel.value = !isInList;
        if (record.provider === 'local' || record.provider === 'other') isCustomModel.value = true;
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

const handleTestConnection = async () => {
    if (!formState.provider || !formState.model_id) {
        toast({
            title: "参数缺失",
            description: "请先填写提供商和模型 ID",
            variant: "destructive"
        });
        return;
    }
    
    testing.value = true;
    testResult.value = null;
    try {
        const res = await api.post('/llm/models/test', {
            provider: formState.provider,
            model_id: formState.model_id,
            api_key: formState.api_key,
            base_url: formState.base_url
        });
        
        if (res.data.success) {
            testResult.value = { success: true, message: res.data.message || '连接测试成功！' };
            toast({
                title: "测试成功",
                description: "模型连接正常。",
                variant: "default", // shadcn toast typically uses 'default' or 'destructive'
                class: "bg-green-500 text-white border-none"
            });
        } else {
            testResult.value = { success: false, message: res.data.message || '连接测试失败' };
            toast({
                title: "测试失败",
                description: res.data.message,
                variant: "destructive"
            });
        }
    } catch (e) {
        const errMsg = e.response?.data?.detail || e.message;
        testResult.value = { success: false, message: '请求失败: ' + errMsg };
        toast({
            title: "连接错误",
            description: errMsg,
            variant: "destructive"
        });
    } finally {
        testing.value = false;
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

const handleStatusChange = async (model, checked) => {
    model.statusLoading = true;
    try {
        // Optimistic update
        const originalStatus = model.is_active;
        model.is_active = checked;
        
        await api.put(`/llm/models/${model.id}`, { is_active: checked });
        toast({
            description: `模型已${checked ? '启用' : '禁用'}`
        });
    } catch (e) {
        model.is_active = !checked; // revert
        toast({
            title: "更新失败",
            description: "无法修改状态",
            variant: "destructive"
        });
    } finally {
        model.statusLoading = false;
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm');
};

const getModelTypeLabel = (type) => {
    const map = {
        'text': '文本',
        'embedding': '嵌入',
        'multimodal': '多模态',
        'image': '图像',
        'video': '视频'
    };
    return map[type] || type;
};

const getModelTypeVariant = (type) => {
    switch (type) {
        case 'text': return 'secondary';
        case 'embedding': return 'outline';
        case 'multimodal': return 'default'; // purple-ish in custom themes often
        case 'image': return 'outline';
        case 'video': return 'outline';
        default: return 'secondary';
    }
};

onMounted(() => {
    fetchModels();
});
</script>
