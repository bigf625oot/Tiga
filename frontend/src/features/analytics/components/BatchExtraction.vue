<template>
  <div class="h-[calc(100vh-20px)] p-6 flex gap-6 max-w-[1600px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
    
    <!-- Left Sidebar: Steps Navigation -->
    <Card class="w-72 flex flex-col shrink-0 h-full border-r">
        <CardHeader class="pb-4 border-b">
            <CardTitle class="flex items-center gap-2 text-xl">
                <span class="w-1.5 h-6 bg-purple-600 rounded-full"></span>
                批量提取
            </CardTitle>
            <CardDescription>支持多文档并发处理与分析</CardDescription>
        </CardHeader>
        
        <ScrollArea class="flex-1">
            <div class="p-4 space-y-1">
                <div v-for="(step, index) in steps" :key="index" 
                    class="relative px-4 py-3 cursor-pointer transition-all rounded-lg flex items-start gap-3 group"
                    :class="currentStep === index + 1 ? 'bg-purple-50 dark:bg-purple-900/20' : 'hover:bg-muted'"
                    @click="canJumpTo(index + 1) && (currentStep = index + 1)"
                >
                    <!-- Connecting Line -->
                    <div v-if="index < 4" class="absolute left-[27px] top-10 bottom-[-10px] w-px bg-border group-last:hidden"></div>

                    <!-- Step Number/Icon -->
                    <div 
                        class="relative z-10 w-6 h-6 rounded-full flex items-center justify-center font-semibold text-[10px] transition-all duration-300 border shrink-0"
                        :class="[
                            currentStep === index + 1 ? 'bg-purple-600 border-purple-600 text-white shadow-md shadow-purple-600/20' : 
                            currentStep > index + 1 ? 'bg-purple-600 border-purple-600 text-white' : 
                            'bg-background border-muted-foreground/30 text-muted-foreground group-hover:border-purple-600/50'
                        ]"
                    >
                        <Check v-if="currentStep > index + 1" class="w-3.5 h-3.5" />
                        <span v-else>{{ index + 1 }}</span>
                    </div>

                    <!-- Step Text -->
                    <div class="flex-1 pt-0.5">
                        <h4 class="font-medium text-sm transition-colors" :class="currentStep === index + 1 ? 'text-foreground' : 'text-muted-foreground'">
                            {{ step.title }}
                        </h4>
                        <p class="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                            {{ step.description }}
                        </p>
                    </div>

                    <!-- Active Indicator -->
                    <div v-if="currentStep === index + 1" class="absolute left-0 top-2 bottom-2 w-1 bg-purple-600 rounded-r"></div>
                </div>
            </div>
        </ScrollArea>
    </Card>

    <!-- Right Content Area -->
    <Card class="flex-1 flex flex-col overflow-hidden h-full shadow-sm">
        
        <!-- Step 1: Batch File Upload -->
        <ScrollArea v-if="currentStep === 1" class="flex-1">
            <div class="p-8 max-w-5xl mx-auto space-y-8">
                <div class="text-center">
                    <h3 class="text-2xl font-semibold tracking-tight">批量导入文档</h3>
                    <p class="text-muted-foreground mt-1">拖拽文件到下方区域，支持多选上传 (Max 100)</p>
                </div>
                
                <div 
                    @click="triggerBatchUpload"
                    class="border-2 border-dashed border-muted-foreground/25 rounded-xl p-12 text-center cursor-pointer hover:border-purple-500 hover:bg-purple-50/10 dark:hover:bg-purple-900/10 transition-all group bg-muted/30 relative overflow-hidden"
                >
                    <input type="file" ref="fileInput" class="hidden" multiple accept=".pdf,.docx,.doc,.txt" @change="handleBatchUpload">
                    
                    <div class="w-16 h-16 bg-background rounded-full shadow-sm flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 border">
                        <UploadCloud class="w-8 h-8 text-purple-500" />
                    </div>
                    <p class="text-lg font-semibold group-hover:text-purple-600 transition-colors">点击选择或拖拽多个文件</p>
                    <p class="text-sm text-muted-foreground mt-2">支持 PDF, Word, TXT 格式</p>
                </div>

                <div v-if="files.length > 0" class="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                    <div class="flex justify-between items-center px-1">
                        <h4 class="font-semibold flex items-center gap-2">
                            已添加文件 
                            <Badge variant="secondary" class="text-xs">{{ files.length }}</Badge>
                        </h4>
                        <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive hover:bg-destructive/10 h-8" @click="files = []">清空列表</Button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div v-for="(file, index) in files" :key="index" class="bg-card border rounded-lg p-4 flex justify-between items-center group hover:shadow-md hover:border-purple-200 transition-all">
                            <div class="flex items-center gap-4 overflow-hidden">
                                <div class="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0 text-muted-foreground font-semibold text-xs uppercase">
                                    {{ file.name.split('.').pop() }}
                                </div>
                                <div class="overflow-hidden">
                                    <p class="text-sm font-medium truncate" :title="file.name">{{ file.name }}</p>
                                    <p class="text-xs text-muted-foreground">{{ (file.size / 1024).toFixed(1) }} KB</p>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100" @click="removeFile(index)">
                                <Trash2 class="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 2: Indicator Selection -->
        <ScrollArea v-if="currentStep === 2" class="flex-1">
            <div class="p-6 flex flex-col h-full space-y-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-2xl font-semibold tracking-tight">选择指标体系</h3>
                        <p class="text-muted-foreground text-sm mt-1">选择需要批量提取的指标集合</p>
                    </div>
                    <div class="relative">
                        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input 
                            v-model="indicatorSearch" 
                            type="text" 
                            placeholder="搜索指标..." 
                            class="pl-9 w-64 bg-background focus-visible:ring-purple-500/20"
                        />
                    </div>
                </div>

                <div class="rounded-md border bg-card flex-1 flex flex-col overflow-hidden">
                    <Table>
                        <TableHeader class="bg-muted/50 sticky top-0 z-10">
                            <TableRow>
                                <TableHead class="w-[50px] text-center">
                                    <Checkbox :checked="isAllSelected" @update:checked="toggleSelectAll" class="data-[state=checked]:bg-purple-600 data-[state=checked]:border-purple-600" />
                                </TableHead>
                                <TableHead class="w-[200px]">指标名称</TableHead>
                                <TableHead class="w-[120px]">分组</TableHead>
                                <TableHead>描述</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody class="overflow-y-auto">
                            <TableRow 
                                v-for="indicator in filteredIndicators" 
                                :key="indicator.id" 
                                class="cursor-pointer hover:bg-purple-50/30 dark:hover:bg-purple-900/20"
                                :class="isSelected(indicator) ? 'bg-purple-50/40 dark:bg-purple-900/30' : ''"
                                @click="toggleSelection(indicator)"
                            >
                                <TableCell class="text-center" @click.stop>
                                    <Checkbox :checked="isSelected(indicator)" @update:checked="toggleSelection(indicator)" class="data-[state=checked]:bg-purple-600 data-[state=checked]:border-purple-600" />
                                </TableCell>
                                <TableCell class="font-medium text-foreground">{{ indicator.name }}</TableCell>
                                <TableCell>
                                    <Badge variant="secondary" class="font-normal">{{ indicator.group }}</Badge>
                                </TableCell>
                                <TableCell class="text-muted-foreground truncate max-w-[400px]" :title="indicator.description">{{ indicator.description || '-' }}</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </div>
                
                <div class="flex justify-between items-center px-2">
                    <span class="text-sm text-muted-foreground">
                        共 {{ filteredIndicators.length }} 个指标
                    </span>
                    <span class="text-sm font-medium" :class="selectedIndicators.length > 0 ? 'text-purple-600' : 'text-muted-foreground'">
                        已选择 {{ selectedIndicators.length }} 个指标
                    </span>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 3: Model Configuration -->
        <ScrollArea v-if="currentStep === 3" class="flex-1">
            <div class="p-8 max-w-5xl mx-auto space-y-8">
                <div>
                    <h3 class="text-2xl font-semibold tracking-tight">配置处理模型</h3>
                    <p class="text-muted-foreground mt-1">建议选择长上下文模型以应对批量任务</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                     <div 
                        v-for="model in availableModels" 
                        :key="model.id"
                        @click="selectedModel = model.id"
                        class="p-6 border rounded-xl cursor-pointer transition-all hover:shadow-lg relative overflow-hidden group bg-card"
                        :class="selectedModel === model.id ? 'border-purple-500 ring-1 ring-purple-500 bg-purple-50/5 dark:bg-purple-900/10' : 'hover:border-purple-300'"
                    >
                        <div class="flex justify-between items-start mb-4">
                            <div class="w-10 h-10 rounded-lg bg-background border flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                                {{ model.icon || '🤖' }}
                            </div>
                            <div class="w-5 h-5 rounded-full border flex items-center justify-center transition-colors" :class="selectedModel === model.id ? 'border-purple-500 bg-purple-500 text-white' : 'border-muted-foreground/30'">
                                <Check v-if="selectedModel === model.id" class="w-3 h-3" />
                            </div>
                        </div>
                        <h4 class="font-semibold mb-1">{{ model.name }}</h4>
                        <div class="flex items-center gap-2 mb-4">
                            <Badge variant="secondary" class="text-[10px] px-1.5 h-5">{{ model.context_window }}</Badge>
                        </div>
                        <p class="text-sm text-muted-foreground leading-relaxed">{{ model.description }}</p>
                    </div>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 4: Extraction Config -->
        <ScrollArea v-if="currentStep === 4" class="flex-1">
            <div class="p-8 max-w-3xl mx-auto space-y-8">
                <div>
                    <h3 class="text-2xl font-semibold tracking-tight">批量任务配置</h3>
                    <p class="text-muted-foreground mt-1">设置输出和错误处理策略</p>
                </div>
                
                <div class="space-y-6">
                    <!-- Output Format -->
                    <Card class="p-6 space-y-4">
                        <Label class="text-base flex items-center gap-2">
                            <FileText class="w-4 h-4 text-purple-500" />
                            输出格式
                        </Label>
                        <RadioGroup v-model="outputFormat" class="grid grid-cols-3 gap-4">
                            <div v-for="fmt in ['Excel', 'JSON', 'CSV']" :key="fmt">
                                <RadioGroupItem :value="fmt" :id="fmt" class="peer sr-only" />
                                <Label
                                    :for="fmt"
                                    class="flex items-center justify-center p-4 rounded-lg border-2 border-muted bg-popover hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-purple-500 peer-data-[state=checked]:text-purple-700 peer-data-[state=checked]:bg-purple-50 dark:peer-data-[state=checked]:bg-purple-900/20 cursor-pointer transition-all"
                                >
                                    {{ fmt }}
                                </Label>
                            </div>
                        </RadioGroup>
                    </Card>

                    <!-- Error Handling -->
                    <Card class="p-6 space-y-4">
                        <Label class="text-base flex items-center gap-2">
                            <AlertTriangle class="w-4 h-4 text-amber-500" />
                            错误处理
                        </Label>
                        <div class="flex items-center space-x-2">
                            <Switch id="skip-errors" v-model:checked="skipErrors" class="data-[state=checked]:bg-purple-600" />
                            <Label for="skip-errors">跳过处理失败的文档继续执行</Label>
                        </div>
                    </Card>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 5: Results -->
        <div v-if="currentStep === 5" class="flex-1 flex flex-col relative h-full bg-muted/20">
            <div class="p-4 border-b flex justify-between items-center bg-card shadow-sm shrink-0">
                <div class="flex items-center gap-6">
                    <div>
                        <h3 class="text-lg font-semibold">批量任务状态</h3>
                        <p class="text-xs text-muted-foreground mt-0.5" v-if="isRunning">预计剩余时间: {{ estimatedTimeRemaining }}</p>
                    </div>
                    <div class="flex items-center gap-4">
                        <div class="w-48 h-2 bg-muted rounded-full overflow-hidden">
                            <div class="h-full bg-purple-600 transition-all duration-500" :style="{ width: progressPercent + '%' }"></div>
                        </div>
                        <span class="font-mono font-semibold text-lg">{{ progressPercent }}%</span>
                        <span class="text-xs text-muted-foreground">({{ completedCount }}/{{ totalTasks }})</span>
                    </div>
                </div>
                <div class="flex gap-2">
                    <Button 
                        @click="togglePause" 
                        variant="outline" 
                        size="sm"
                        class="gap-1.5"
                        :class="isPaused ? 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20' : 'text-amber-600 hover:text-amber-700 hover:bg-amber-50 dark:hover:bg-amber-900/20'"
                    >
                        <Play v-if="isPaused" class="w-3.5 h-3.5 fill-current" />
                        <Pause v-else class="w-3.5 h-3.5 fill-current" />
                        {{ isPaused ? '继续' : '暂停' }}
                    </Button>
                    <Button size="sm" class="gap-1.5 bg-purple-600 hover:bg-purple-700 shadow-sm">
                        <FileText class="w-3.5 h-3.5" />
                        汇总报告
                    </Button>
                </div>
            </div>

            <ScrollArea class="flex-1">
                <div class="p-6">
                    <div class="bg-card rounded-md border shadow-sm overflow-hidden">
                        <Table>
                            <TableHeader class="bg-muted/50">
                                <TableRow>
                                    <TableHead class="pl-6">文件名</TableHead>
                                    <TableHead>状态</TableHead>
                                    <TableHead>耗时</TableHead>
                                    <TableHead>提取指标数</TableHead>
                                    <TableHead class="text-right pr-6">操作</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <TableRow v-for="(task, idx) in batchTasks" :key="idx" class="hover:bg-muted/50">
                                    <TableCell class="pl-6 font-medium flex items-center gap-3">
                                        <div class="w-8 h-8 rounded bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground uppercase">
                                            {{ task.fileName.split('.').pop() }}
                                        </div>
                                        <span class="truncate max-w-[200px]" :title="task.fileName">{{ task.fileName }}</span>
                                    </TableCell>
                                    <TableCell>
                                        <Badge :variant="getStatusVariant(task.status)" class="font-normal gap-1.5">
                                            <span v-if="task.status === 'processing'" class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                                            {{ getStatusText(task.status) }}
                                        </Badge>
                                    </TableCell>
                                    <TableCell class="font-mono text-xs text-muted-foreground">{{ task.duration ? task.duration + 's' : '-' }}</TableCell>
                                    <TableCell>
                                        <Badge variant="secondary" v-if="task.indicatorCount > 0">{{ task.indicatorCount }}</Badge>
                                        <span v-else class="text-muted-foreground text-xs">-</span>
                                    </TableCell>
                                    <TableCell class="text-right pr-6">
                                        <Button v-if="task.status === 'completed'" variant="link" size="sm" class="h-auto p-0 text-purple-600">查看</Button>
                                        <Button v-if="task.status === 'failed'" variant="link" size="sm" class="h-auto p-0 text-destructive">重试</Button>
                                    </TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </ScrollArea>
        </div>

        <!-- Footer Buttons -->
        <div class="p-4 border-t bg-card flex justify-between items-center shrink-0 z-10">
             <Button 
                variant="ghost" 
                @click="currentStep--" 
                :disabled="currentStep === 1 || isRunning"
                class="gap-2"
             >
                <ChevronLeft class="w-4 h-4" />
                上一步
             </Button>
             
             <div class="flex gap-4">
                 <Button 
                    v-if="currentStep < 5"
                    @click="nextStep"
                    :disabled="!canProceed"
                    class="px-8 shadow-lg shadow-purple-600/20 gap-2 bg-purple-600 hover:bg-purple-700"
                 >
                    {{ currentStep === 4 ? '开始批量提取' : '下一步' }}
                    <ChevronRight v-if="currentStep < 4" class="w-4 h-4" />
                    <Play v-if="currentStep === 4" class="w-4 h-4" />
                 </Button>
                 <Button 
                    v-if="currentStep === 5"
                    variant="secondary"
                    @click="reset"
                    class="gap-2"
                 >
                    <RotateCcw class="w-4 h-4" />
                    新建批量任务
                 </Button>
             </div>
        </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useToast } from '@/components/ui/toast/use-toast';
import { 
    Check, UploadCloud, Search, CheckCircle2, XCircle, ChevronLeft, ChevronRight, 
    Play, Pause, RotateCcw, Trash2, FileText, AlertTriangle
} from 'lucide-vue-next';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';

const api = axios.create({ baseURL: '/api/v1' });
const { toast } = useToast();

// State
const currentStep = ref(1);
const files = ref([]);
const fileInput = ref(null);
const indicators = ref([]);
const selectedIndicators = ref([]);
const indicatorSearch = ref('');
const availableModels = ref([
    { id: 'qwen-plus', name: 'Qwen Plus', description: '均衡型模型，在速度和性能之间保持平衡', context_window: '32k', icon: '🚀' },
    { id: 'qwen-max', name: 'Qwen Max', description: '最强推理能力，适合复杂逻辑分析', context_window: '32k', icon: '🧠' },
    { id: 'qwen-long', name: 'Qwen Long', description: '超长上下文，适合长文档批量处理', context_window: '200k', icon: '📜' }
]);
const selectedModel = ref('qwen-plus');
const outputFormat = ref('Excel');
const skipErrors = ref(true);

const steps = [
    { title: '文档导入', description: '批量上传文档' },
    { title: '指标选择', description: '选择指标体系' },
    { title: '模型配置', description: '配置处理模型' },
    { title: '任务参数', description: '输出与错误处理' },
    { title: '批量结果', description: '查看任务进度' }
];

// Batch Execution State
const batchTasks = ref([]);
const isRunning = ref(false);
const isPaused = ref(false);

// Computed
const canProceed = computed(() => {
    if (currentStep.value === 1) return files.value.length > 0;
    if (currentStep.value === 2) return selectedIndicators.value.length > 0;
    if (currentStep.value === 3) return !!selectedModel.value;
    return true;
});

const canJumpTo = (step) => {
    if (step === 1) return true;
    if (step === 2) return files.value.length > 0;
    if (step === 3) return files.value.length > 0 && selectedIndicators.value.length > 0;
    if (step === 4) return files.value.length > 0 && selectedIndicators.value.length > 0 && !!selectedModel.value;
    return false;
}

const filteredIndicators = computed(() => {
    if (!indicatorSearch.value) return indicators.value;
    const kw = indicatorSearch.value.toLowerCase();
    return indicators.value.filter(i => i.name.toLowerCase().includes(kw));
});

const isAllSelected = computed(() => {
    return filteredIndicators.value.length > 0 && 
           filteredIndicators.value.every(i => selectedIndicators.value.some(s => s.id === i.id));
});

const totalTasks = computed(() => batchTasks.value.length);
const completedCount = computed(() => batchTasks.value.filter(t => ['completed', 'failed'].includes(t.status)).length);
const progressPercent = computed(() => totalTasks.value ? Math.round((completedCount.value / totalTasks.value) * 100) : 0);
const estimatedTimeRemaining = computed(() => {
    if (!isRunning.value || completedCount.value === 0) return '-';
    // Mock calculation
    const remaining = totalTasks.value - completedCount.value;
    const avgTime = 2; // seconds
    const totalSeconds = remaining * avgTime;
    return totalSeconds > 60 ? `${Math.ceil(totalSeconds/60)} 分钟` : `${totalSeconds} 秒`;
});

// Methods
const triggerBatchUpload = () => fileInput.value.click();

const handleBatchUpload = (e) => {
    const newFiles = Array.from(e.target.files);
    if (newFiles.length + files.value.length > 100) {
        toast({ title: '最多支持 100 个文件', variant: 'warning' });
        return;
    }
    files.value.push(...newFiles);
    e.target.value = '';
};

const removeFile = (index) => {
    files.value.splice(index, 1);
};

const fetchIndicators = async () => {
    try {
        const res = await api.get('/indicators/', { params: { limit: 1000 } });
        indicators.value = res.data;
    } catch (e) {
        console.error(e);
    }
};

const isSelected = (indicator) => selectedIndicators.value.some(i => i.id === indicator.id);

const toggleSelection = (indicator) => {
    if (isSelected(indicator)) {
        selectedIndicators.value = selectedIndicators.value.filter(i => i.id !== indicator.id);
    } else {
        selectedIndicators.value.push(indicator);
    }
};

const toggleSelectAll = () => {
    if (isAllSelected.value) {
        const visibleIds = filteredIndicators.value.map(i => i.id);
        selectedIndicators.value = selectedIndicators.value.filter(i => !visibleIds.includes(i.id));
    } else {
        const newItems = filteredIndicators.value.filter(i => !isSelected(i));
        selectedIndicators.value.push(...newItems);
    }
};

const nextStep = async () => {
    if (currentStep.value === 4) {
        currentStep.value = 5;
        await startBatchProcessing();
    } else {
        currentStep.value++;
    }
};

const reset = () => {
    currentStep.value = 1;
    files.value = [];
    selectedIndicators.value = [];
    batchTasks.value = [];
    isRunning.value = false;
};

const startBatchProcessing = async () => {
    // Initialize tasks
    batchTasks.value = files.value.map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        file: file,
        fileName: file.name,
        status: 'pending',
        duration: 0,
        indicatorCount: 0
    }));
    
    isRunning.value = true;
    processQueue();
};

const processQueue = async () => {
    if (!isRunning.value || isPaused.value) return;
    
    // Simple queue: find next pending
    const task = batchTasks.value.find(t => t.status === 'pending');
    if (!task) {
        isRunning.value = false;
        toast({ title: '批量任务完成' });
        return;
    }
    
    task.status = 'processing';
    const startTime = Date.now();
    
    try {
        // 1. Upload/Parse File
        const formData = new FormData();
        formData.append('file', task.file);
        const parseRes = await api.post('/metrics/parse_doc', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        const textContent = parseRes.data.text;
        
        // 2. Extract Indicators (Loop)
        let extractedCount = 0;
        for (const indicator of selectedIndicators.value) {
            await api.post('/metrics/extract', {
                indicator_name: indicator.name,
                definition: indicator.description,
                text_content: textContent,
                model: selectedModel.value,
                extraction_mode: 'Multi', // Default for batch
                advanced_options: indicator.advanced_options
            });
            extractedCount++;
        }
        
        task.status = 'completed';
        task.indicatorCount = extractedCount;
    } catch (e) {
        task.status = 'failed';
        if (!skipErrors.value) {
            isPaused.value = true; // Pause on error if configured
        }
    } finally {
        task.duration = ((Date.now() - startTime) / 1000).toFixed(1);
        processQueue(); // Next
    }
};

const togglePause = () => {
    isPaused.value = !isPaused.value;
    if (!isPaused.value) processQueue();
};

const getStatusText = (status) => {
    const map = {
        pending: '等待中',
        processing: '处理中',
        completed: '已完成',
        failed: '失败',
        paused: '已暂停'
    };
    return map[status] || status;
};

const getStatusVariant = (status) => {
    const map = {
        pending: 'secondary',
        processing: 'default',
        completed: 'success', // Assuming custom variant or use default/outline
        failed: 'destructive',
        paused: 'warning' // Assuming custom variant
    };
    // Map to available badge variants: default, secondary, destructive, outline
    if (status === 'completed') return 'outline'; // Or styled with class
    if (status === 'paused') return 'secondary';
    return map[status] || 'outline';
};

onMounted(() => {
    fetchIndicators();
});
</script>
