<template>
  <div class="h-full flex flex-col bg-background font-sans">
    <!-- Header & Actions -->
    <div class="flex flex-col gap-6 px-8 pt-8 pb-4">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-4">
          <h1 class="text-2xl font-semibold tracking-tight">指标管理</h1>
          <Badge variant="secondary" class="px-2.5 py-0.5 text-xs font-medium">
            {{ total }} 个指标
          </Badge>
        </div>
        <div class="flex gap-4">
          <div class="relative w-72 transition-all focus-within:w-80">
            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              @keyup.enter="fetchIndicators"
              type="text"
              placeholder="搜索指标名称或分组..."
              class="pl-9 bg-background"
            />
          </div>
          <Button variant="outline" @click="openImportDialog" class="gap-2">
            <Upload class="w-4 h-4" />
            批量导入
          </Button>
          <Button variant="outline" class="gap-2 text-amber-600 hover:text-amber-700 bg-amber-50 hover:bg-amber-100 border-amber-200" @click="openBatchPromptDialog">
            <Sparkles class="w-4 h-4" />
            生成 Prompt
          </Button>
          <Button @click="openDialog('create')" class="gap-2 shadow-lg shadow-primary/20">
            <Plus class="w-4 h-4" />
            添加指标
          </Button>
        </div>
      </div>
      
      <!-- Quick Filters -->
      <ScrollArea class="w-full whitespace-nowrap pb-2">
        <div class="flex w-max space-x-2 p-1">
          <Button
            variant="ghost"
            size="sm"
            @click="filterGroup = ''"
            :class="!filterGroup ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'bg-background hover:bg-muted text-muted-foreground'"
            class="rounded-full px-4 font-normal"
          >
            全部
          </Button>
          <Button
            v-for="group in uniqueGroups"
            :key="group"
            variant="ghost"
            size="sm"
            @click="filterGroup = group"
            :class="filterGroup === group ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'bg-background hover:bg-muted text-muted-foreground'"
            class="rounded-full px-4 font-normal"
          >
            {{ group }}
          </Button>
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-y-auto px-8 pb-32">
      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center h-64 text-muted-foreground gap-4">
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
        <span class="text-sm font-medium">加载数据中...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredIndicators.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-muted-foreground animate-in fade-in zoom-in duration-300">
        <div class="relative w-48 h-48 mb-6 opacity-80 bg-muted/30 rounded-full flex items-center justify-center">
            <FileText class="w-24 h-24 text-muted-foreground/50" />
        </div>
        <h3 class="text-lg font-semibold text-foreground mb-2">暂无相关指标</h3>
        <p class="text-muted-foreground text-sm mb-6">点击上方按钮添加您的第一个业务指标</p>
        <Button @click="openDialog('create')" size="lg" class="shadow-lg shadow-primary/20">
          立即添加
        </Button>
      </div>

      <!-- Card Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <Card v-for="item in filteredIndicators" :key="item.id" class="group hover:shadow-lg hover:border-primary/50 transition-all duration-300 flex flex-col justify-between h-[240px] relative">
          <CardHeader class="p-6 pb-2 space-y-0">
            <div class="flex justify-between items-start mb-2">
              <Badge variant="secondary" class="truncate max-w-[120px] font-normal">
                {{ item.group }}
              </Badge>
              
              <!-- Actions Dropdown -->
              <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute right-4 top-4">
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground">
                      <MoreHorizontal class="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-40">
                    <DropdownMenuItem @click="openDialog('edit', item)">
                      <Edit class="mr-2 h-4 w-4" />
                      编辑
                    </DropdownMenuItem>
                    <DropdownMenuItem @click="handleExtract(item)">
                      <Play class="mr-2 h-4 w-4" />
                      提取
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem @click="handleDelete(item)" class="text-destructive focus:text-destructive">
                      <Trash2 class="mr-2 h-4 w-4" />
                      删除
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
            
            <CardTitle class="text-lg font-semibold truncate" :title="item.name">{{ item.name }}</CardTitle>
            <div class="text-xs text-muted-foreground mt-1 truncate flex items-center gap-1.5 h-5">
              <template v-if="item.alias">
                <span class="w-1 h-1 rounded-full bg-muted-foreground/50"></span>
                {{ item.alias }}
              </template>
            </div>
          </CardHeader>
          
          <CardContent class="px-6 py-2 flex-1">
            <p class="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
              {{ item.description || '暂无描述信息...' }}
            </p>
          </CardContent>

          <CardFooter class="p-4 pt-0 mt-auto border-t bg-muted/10 flex items-center justify-between">
            <span class="text-xs font-medium text-muted-foreground flex items-center gap-1.5 mt-4">
              <Calendar class="w-3.5 h-3.5" />
              {{ formatDate(item.created_at) }}
            </span>
            <Button 
                variant="ghost" 
                size="sm"
                @click="handleExtract(item)"
                class="text-xs font-semibold text-primary hover:text-primary hover:bg-primary/10 -mr-2 mt-4 gap-1 group/btn"
            >
                去提取
                <ArrowRight class="w-3 h-3 transition-transform group-hover/btn:translate-x-0.5" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog v-model:open="dialogVisible">
      <DialogContent class="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ dialogType === 'create' ? '添加指标' : '编辑指标' }}</DialogTitle>
          <DialogDescription>
            {{ dialogType === 'create' ? '填写下方信息以创建新的业务指标。' : '修改指标信息，点击保存以更新。' }}
          </DialogDescription>
        </DialogHeader>
        <div class="py-4">
          <IndicatorForm 
            :initialData="selectedIndicator" 
            :isEdit="dialogType === 'edit'"
            @submit="handleFormSubmit"
            @cancel="dialogVisible = false"
          />
        </div>
      </DialogContent>
    </Dialog>

    <!-- Import Dialog -->
    <Dialog v-model:open="importDialogVisible">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>批量导入指标</DialogTitle>
          <DialogDescription>
            请上传 CSV 或 Excel 文件。必填表头：指标分组 (Group), 指标名称 (Name), 指标描述 (Description)。
          </DialogDescription>
        </DialogHeader>
        
        <div class="py-4 space-y-4">
          <div class="bg-primary/5 border border-primary/20 rounded-lg p-4 text-sm text-primary flex gap-2">
            <Info class="w-5 h-5 flex-shrink-0" />
            <div class="leading-relaxed">
              支持 .csv, .xlsx, .xls 格式。请确保文件编码为 UTF-8。
            </div>
          </div>
          
          <div 
            class="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all group" 
            @click="triggerFileInput"
          >
            <input type="file" ref="fileInput" class="hidden" accept=".csv,.xlsx,.xls" @change="handleImportFile">
            <div class="w-12 h-12 rounded-full bg-muted group-hover:bg-primary/20 flex items-center justify-center m-4 transition-colors">
              <UploadCloud class="w-6 h-6 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <p class="text-sm font-medium text-foreground">点击上传或拖拽文件到此处</p>
            <p class="text-xs text-muted-foreground mt-1">支持最大 10MB 文件</p>
          </div>

          <div v-if="importing || importResult" class="mt-4 space-y-2">
            <div v-if="importing" class="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div class="bg-primary h-2 rounded-full transition-all duration-300" :style="{ width: importProgress + '%' }"></div>
            </div>
            <div v-if="importResult" class="bg-muted/50 p-4 rounded-lg border text-sm">
              <div class="flex gap-4 mb-2">
                <span class="text-green-600 font-semibold flex items-center gap-1"><CheckCircle2 class="w-4 h-4"/> 成功: {{ importResult.success }}</span>
                <span class="text-destructive font-semibold flex items-center gap-1"><XCircle class="w-4 h-4"/> 失败: {{ importResult.failed }}</span>
              </div>
              <ScrollArea v-if="importResult.errors.length > 0" class="h-32 w-full rounded border border-destructive/20 bg-destructive/5 p-2">
                <div v-for="(err, idx) in importResult.errors" :key="idx" class="text-xs text-destructive mb-1">{{ err }}</div>
              </ScrollArea>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <!-- Batch Prompt Dialog -->
    <Dialog v-model:open="batchPromptDialogVisible">
      <DialogContent class="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>批量生成 Prompt</DialogTitle>
          <DialogDescription>
            该功能将根据当前列表中的所有指标（受搜索条件影响），自动生成一份完整的指标提取 Prompt 模板。
          </DialogDescription>
        </DialogHeader>

        <div class="bg-muted/30 p-4 rounded-lg border h-[400px] overflow-hidden font-mono text-sm">
           <ScrollArea class="h-full w-full">
                <div v-if="generatingPrompt" class="flex flex-col items-center justify-center h-full text-muted-foreground gap-2 mt-32">
                    <Loader2 class="h-8 w-8 animate-spin text-amber-500" />
                    <span>正在生成 Prompt...</span>
                </div>
                <div v-else class="whitespace-pre-wrap select-text text-foreground">{{ generatedPrompt || '点击下方按钮开始生成...' }}</div>
           </ScrollArea>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="batchPromptDialogVisible = false">关闭</Button>
          <Button @click="generateBatchPrompt" :disabled="generatingPrompt">
            {{ generatingPrompt ? '生成中...' : '开始生成' }}
          </Button>
          <Button v-if="generatedPrompt" variant="secondary" @click="copyPrompt" class="gap-2">
            <Copy class="w-4 h-4" />
            复制内容
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Delete Confirmation -->
    <AlertDialog v-model:open="deleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除指标 "{{ indicatorToDelete?.name }}" 吗？此操作无法撤销。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="deleteDialogOpen = false">取消</AlertDialogCancel>
          <AlertDialogAction @click="confirmDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">删除</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineAsyncComponent } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import { 
    Search, Plus, Upload, Sparkles, MoreHorizontal, Edit, Play, 
    Trash2, FileText, Loader2, Calendar, ArrowRight, Info, 
    UploadCloud, CheckCircle2, XCircle, Copy
} from 'lucide-vue-next';

// UI Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/toast/use-toast';

const IndicatorForm = defineAsyncComponent(() => import('./IndicatorForm.vue'));

const emit = defineEmits(['navigate-to-extraction']);
const { toast } = useToast();

const api = axios.create({ baseURL: '/api/v1' });

// State
const indicators = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const filterGroup = ref('');
const total = ref(0);

// Import State
const importDialogVisible = ref(false);
const importing = ref(false);
const importProgress = ref(0);
const importResult = ref(null);
const fileInput = ref(null);

// Batch Prompt State
const batchPromptDialogVisible = ref(false);
const generatingPrompt = ref(false);
const generatedPrompt = ref('');

// Delete State
const deleteDialogOpen = ref(false);
const indicatorToDelete = ref(null);

// Computed
const uniqueGroups = computed(() => {
    const groups = new Set(indicators.value.map(i => i.group).filter(Boolean));
    return Array.from(groups);
});

const filteredIndicators = computed(() => {
    return indicators.value.filter(item => {
        const matchesSearch = !searchQuery.value || 
            item.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
            (item.group && item.group.toLowerCase().includes(searchQuery.value.toLowerCase()));
        
        const matchesGroup = !filterGroup.value || item.group === filterGroup.value;
        
        return matchesSearch && matchesGroup;
    });
});

// Dialog State
const dialogVisible = ref(false);
const dialogType = ref('create');
const submitting = ref(false);

const selectedIndicator = ref(null);

// Methods
const fetchIndicators = async () => {
  loading.value = true;
  try {
    const res = await api.get('/indicators/', { params: { limit: 1000 } });
    indicators.value = res.data;
    total.value = res.data.length;
  } catch (e) {
    toast({
        title: "获取指标列表失败",
        description: e.message,
        variant: "destructive"
    });
  } finally {
    loading.value = false;
  }
};

const formatDate = (date) => dayjs(date).format('YYYY-MM-DD');

const openDialog = (type, row = null) => {
  dialogType.value = type;
  if (type === 'edit' && row) {
    selectedIndicator.value = { ...row };
  } else {
    selectedIndicator.value = null;
  }
  dialogVisible.value = true;
};

const handleFormSubmit = async (payload) => {
  submitting.value = true;
  try {
    if (dialogType.value === 'create') {
      await api.post('/indicators/', payload);
      toast({ title: "添加成功" });
      // Reset filters to ensure new item is visible
      searchQuery.value = '';
      filterGroup.value = '';
    } else {
      await api.patch(`/indicators/${selectedIndicator.value.id}`, payload);
      toast({ title: "更新成功" });
    }
    dialogVisible.value = false;
    fetchIndicators();
  } catch (e) {
    console.error(e);
    toast({
        title: "操作失败",
        description: e.response?.data?.detail || e.message,
        variant: "destructive"
    });
  } finally {
    submitting.value = false;
  }
};

const handleDelete = (row) => {
    indicatorToDelete.value = row;
    deleteDialogOpen.value = true;
};

const confirmDelete = async () => {
    if (!indicatorToDelete.value) return;
    try {
        await api.delete(`/indicators/${indicatorToDelete.value.id}`);
        toast({ title: "删除成功" });
        fetchIndicators();
    } catch (e) {
        toast({
            title: "删除失败",
            description: e.message,
            variant: "destructive"
        });
    } finally {
        deleteDialogOpen.value = false;
        indicatorToDelete.value = null;
    }
};

const handleExtract = (row) => {
  emit('navigate-to-extraction', row);
};

// Import Logic
const openImportDialog = () => {
    importDialogVisible.value = true;
    importResult.value = null;
    importProgress.value = 0;
};

const triggerFileInput = () => {
    fileInput.value.click();
};

const handleImportFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    importing.value = true;
    importProgress.value = 20;
    importResult.value = null;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Mock progress
        const timer = setInterval(() => {
            if (importProgress.value < 90) importProgress.value += 10;
        }, 200);
        
        const res = await api.post('/indicators/import', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        clearInterval(timer);
        importProgress.value = 100;
        importResult.value = res.data;
        
        if (res.data.failed === 0) {
            toast({ title: `成功导入 ${res.data.success} 条数据` });
            setTimeout(() => {
                importDialogVisible.value = false;
                fetchIndicators();
            }, 1500);
        } else {
            toast({ 
                title: "导入完成", 
                description: `成功: ${res.data.success}, 失败: ${res.data.failed}`,
                variant: "warning" 
            });
            fetchIndicators();
        }
    } catch (e) {
        toast({
            title: "导入失败",
            description: e.response?.data?.detail || e.message,
            variant: "destructive"
        });
        importProgress.value = 0;
    } finally {
        importing.value = false;
        e.target.value = ''; // Reset input
    }
};

// Batch Prompt Logic
const openBatchPromptDialog = () => {
    batchPromptDialogVisible.value = true;
    generatedPrompt.value = '';
};

const generateBatchPrompt = async () => {
    generatingPrompt.value = true;
    try {
        if (filteredIndicators.value.length === 0) {
            generatedPrompt.value = "当前没有指标数据，无法生成 Prompt。";
            return;
        }

        const batchRes = await api.post('/metrics/batch_generate_prompts', {
            indicators: filteredIndicators.value,
            output_format: "JSON",
            language: "CN",
            extraction_mode: "Multi"
        });
        
        const results = batchRes.data;
        let finalOutput = "";
        
        results.forEach((item, index) => {
            finalOutput += `### ${index + 1}. ${item.indicator_name}\n`;
            finalOutput += `\`\`\`\n${item.prompt}\n\`\`\`\n\n`;
            finalOutput += `--------------------------------------------------\n\n`;
        });

        generatedPrompt.value = finalOutput;
    } catch (e) {
        toast({
            title: "生成失败",
            description: e.message,
            variant: "destructive"
        });
        console.error(e);
    } finally {
        generatingPrompt.value = false;
    }
};

const copyPrompt = async () => {
    if (!generatedPrompt.value) return;
    try {
        await navigator.clipboard.writeText(generatedPrompt.value);
        toast({ title: "已复制到剪贴板" });
    } catch (err) {
        toast({ title: "复制失败", variant: "destructive" });
    }
};

onMounted(() => {
  fetchIndicators();
});
</script>