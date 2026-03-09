<template>
  <div class="h-[calc(100vh-20px)] p-6 flex gap-6 max-w-[1600px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
    
    <!-- Left Sidebar: Steps Navigation -->
    <Card class="w-72 flex flex-col shrink-0 h-full border-r">
        <CardHeader class="pb-4 border-b">
            <CardTitle class="flex items-center gap-2 text-xl">
                <span class="w-1.5 h-6 bg-primary rounded-full"></span>
                指标提取
            </CardTitle>
            <CardDescription>五步完成智能化数据提取</CardDescription>
        </CardHeader>
        
        <ScrollArea class="flex-1">
            <div class="p-4 space-y-1">
                <div v-for="(step, index) in steps" :key="index" 
                    class="relative px-4 py-3 cursor-pointer transition-all rounded-lg flex items-start gap-3 group"
                    :class="currentStep === index + 1 ? 'bg-primary/10' : 'hover:bg-muted'"
                    @click="canJumpTo(index + 1) && (currentStep = index + 1)"
                >
                    <!-- Connecting Line -->
                    <div v-if="index < 4" class="absolute left-[27px] top-10 bottom-[-10px] w-px bg-border group-last:hidden"></div>

                    <!-- Step Number/Icon -->
                    <div 
                        class="relative z-10 w-6 h-6 rounded-full flex items-center justify-center font-semibold text-[10px] transition-all duration-300 border shrink-0"
                        :class="[
                            currentStep === index + 1 ? 'bg-primary border-primary text-primary-foreground shadow-md shadow-primary/20' : 
                            currentStep > index + 1 ? 'bg-primary border-primary text-primary-foreground' : 
                            'bg-background border-muted-foreground/30 text-muted-foreground group-hover:border-primary/50'
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
                    <div v-if="currentStep === index + 1" class="absolute left-0 top-2 bottom-2 w-1 bg-primary rounded-r"></div>
                </div>
            </div>
        </ScrollArea>
    </Card>

    <!-- Right Content Area -->
    <Card class="flex-1 flex flex-col overflow-hidden h-full shadow-sm">
        
        <!-- Step 1: Data Source Selection -->
        <ScrollArea v-if="currentStep === 1" class="flex-1">
            <div class="p-8 max-w-4xl mx-auto space-y-8">
                <div>
                    <h3 class="text-2xl font-semibold tracking-tight">选择数据来源</h3>
                    <p class="text-muted-foreground mt-1">支持从多种渠道导入数据进行分析</p>
                </div>
                
                <!-- Source Type Cards -->
                <div class="grid grid-cols-3 gap-4">
                    <div 
                        v-for="type in sourceTypes" 
                        :key="type.value"
                        @click="sourceType = type.value"
                        class="p-4 rounded-xl border transition-all cursor-pointer flex items-center gap-4 hover:shadow-md h-24 relative overflow-hidden group bg-card"
                        :class="sourceType === type.value ? 'border-primary ring-1 ring-primary/20 bg-primary/5' : 'hover:border-primary/50'"
                    >
                        <div class="w-12 h-12 rounded-lg flex items-center justify-center shrink-0 transition-transform group-hover:scale-110" :class="type.iconBg">
                            <component :is="type.icon" class="w-6 h-6" :class="type.iconColor" />
                        </div>
                        <div class="flex-1 min-w-0">
                            <span class="block font-semibold text-base">{{ type.label }}</span>
                            <span class="block text-xs text-muted-foreground mt-1 truncate">{{ type.desc }}</span>
                        </div>
                        <div class="absolute top-3 right-3 w-4 h-4 rounded-full border flex items-center justify-center" :class="sourceType === type.value ? 'border-primary' : 'border-muted-foreground/30'">
                             <div v-if="sourceType === type.value" class="w-2 h-2 rounded-full bg-primary"></div>
                        </div>
                    </div>
                </div>
                
                <!-- File Selection Logic -->
                <Card class="p-6 transition-all duration-300">
                    <div v-if="sourceType === 'recording'" class="space-y-4">
                        <Label>选择已转写文件</Label>
                        <Select v-model="selectedFileId" @update:modelValue="handleFileChange">
                            <SelectTrigger class="w-full h-11">
                                <SelectValue placeholder="-- 请选择或搜索文件 --" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem v-for="f in files" :key="f.id" :value="f.id">
                                    {{ f.filename }} ({{ f.duration }}s)
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div v-else-if="sourceType === 'kb'" class="space-y-4">
                         <Label>选择知识库文件</Label>
                         <Select v-model="selectedKbFileId" @update:modelValue="handleKbFileChange">
                            <SelectTrigger class="w-full h-11">
                                <SelectValue placeholder="-- 请选择或搜索知识库文件 --" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem v-for="f in kbFiles" :key="f.id" :value="f.id">
                                    {{ f.filename }} ({{ (f.file_size/1024).toFixed(1) }} KB)
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div v-else class="w-full">
                         <div 
                            @click="triggerDocUpload"
                            class="border-2 border-dashed border-muted-foreground/25 rounded-xl p-8 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all group bg-muted/30"
                        >
                            <input type="file" ref="docInput" class="hidden" accept=".pdf,.docx,.doc,.txt" @change="handleDocUpload">
                            <div v-if="uploading" class="flex flex-col items-center gap-3">
                                <Loader2 class="h-8 w-8 animate-spin text-primary" />
                                <span class="text-muted-foreground font-medium">正在解析文档内容...</span>
                            </div>
                            <div v-else class="flex flex-col items-center gap-3">
                                <div class="w-12 h-12 bg-background border shadow-sm rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                    <UploadCloud class="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <p class="text-base font-semibold group-hover:text-primary transition-colors">点击上传或拖拽文件</p>
                                    <p class="text-xs text-muted-foreground mt-1">PDF, Word, TXT (Max 20MB)</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>

                <!-- Preview -->
                <div class="space-y-3 transition-all duration-500 ease-in-out" :class="textContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'">
                    <div class="flex justify-between items-center">
                        <Label>文本预览</Label>
                        <Badge variant="outline" v-if="textContent" class="font-mono text-xs">
                            {{ (textContent.length / 1000).toFixed(1) }}k 字符
                        </Badge>
                    </div>
                    <div class="relative group">
                        <Textarea 
                            v-model="textContent" 
                            readonly
                            rows="10" 
                            class="font-mono text-xs resize-none bg-muted/30 focus-visible:ring-primary/20"
                            :placeholder="sourceType === 'recording' ? '选择文件后显示内容...' : '上传文档后显示内容...'"
                        />
                        <Badge v-if="textContent && textContent.length > 30000" variant="warning" class="absolute bottom-4 right-4 gap-1 shadow-sm">
                            <AlertTriangle class="w-3 h-3" />
                            超长文档
                        </Badge>
                    </div>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 2: Indicator Selection -->
        <ScrollArea v-if="currentStep === 2" class="flex-1">
            <div class="p-6 flex flex-col h-full space-y-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-2xl font-semibold tracking-tight">选择需要提取的指标</h3>
                        <p class="text-muted-foreground text-sm mt-1">从指标库中选择或创建新指标</p>
                    </div>
                    <div class="flex gap-3">
                        <div class="relative">
                            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input 
                                v-model="indicatorSearch" 
                                type="text" 
                                placeholder="搜索指标名称..." 
                                class="pl-9 w-64 bg-background"
                            />
                        </div>
                        <Button @click="openIndicatorModal()" class="gap-2 shadow-sm">
                            <Plus class="w-4 h-4" />
                            新建
                        </Button>
                    </div>
                </div>

                <div class="rounded-md border bg-card flex-1 flex flex-col overflow-hidden">
                    <Table>
                        <TableHeader class="bg-muted/50 sticky top-0 z-10">
                            <TableRow>
                                <TableHead class="w-[50px] text-center">
                                    <Checkbox :checked="isAllSelected" @update:checked="toggleSelectAll" />
                                </TableHead>
                                <TableHead class="w-[200px]">指标名称</TableHead>
                                <TableHead class="w-[120px]">分组</TableHead>
                                <TableHead class="w-[120px]">别名</TableHead>
                                <TableHead>描述</TableHead>
                                <TableHead class="w-[80px] text-center">操作</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody class="overflow-y-auto">
                            <TableRow 
                                v-for="indicator in filteredIndicators" 
                                :key="indicator.id" 
                                class="cursor-pointer hover:bg-muted/50"
                                :class="isSelected(indicator) ? 'bg-primary/5' : ''"
                                @click="toggleSelection(indicator)"
                            >
                                <TableCell class="text-center" @click.stop>
                                    <Checkbox :checked="isSelected(indicator)" @update:checked="toggleSelection(indicator)" />
                                </TableCell>
                                <TableCell class="font-medium text-foreground">{{ indicator.name }}</TableCell>
                                <TableCell>
                                    <Badge variant="secondary" class="font-normal">{{ indicator.group }}</Badge>
                                </TableCell>
                                <TableCell class="text-muted-foreground">{{ indicator.alias || '-' }}</TableCell>
                                <TableCell class="text-muted-foreground truncate max-w-[300px]" :title="indicator.description">{{ indicator.description || '-' }}</TableCell>
                                <TableCell class="text-center" @click.stop>
                                    <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-primary" @click="openIndicatorModal(indicator)">
                                        <Edit2 class="w-4 h-4" />
                                    </Button>
                                </TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </div>
                
                <div class="flex justify-between items-center px-2">
                    <span class="text-sm text-muted-foreground">
                        共 {{ filteredIndicators.length }} 个指标
                    </span>
                    <span class="text-sm font-medium" :class="selectedIndicators.length > 0 ? 'text-primary' : 'text-muted-foreground'">
                        已选择 {{ selectedIndicators.length }} 个指标
                    </span>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 3: Model Configuration -->
        <ScrollArea v-if="currentStep === 3" class="flex-1">
            <div class="p-8 max-w-4xl mx-auto space-y-8">
                <div>
                    <h3 class="text-2xl font-semibold tracking-tight">配置 AI 模型</h3>
                    <p class="text-muted-foreground mt-1">选择最适合当前任务的大语言模型</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div 
                        v-for="model in availableModels" 
                        :key="model.id"
                        @click="selectedModel = model.id"
                        class="p-6 border rounded-xl cursor-pointer transition-all hover:shadow-lg relative overflow-hidden group bg-card"
                        :class="selectedModel === model.id ? 'border-primary ring-1 ring-primary bg-primary/5' : 'hover:border-primary/50'"
                    >
                        <div class="flex justify-between items-start mb-4">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded-lg bg-muted/50 border flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                                    {{ model.icon || '🤖' }}
                                </div>
                                <div>
                                    <h4 class="font-semibold">{{ model.name }}</h4>
                                    <Badge variant="secondary" class="text-[10px] px-1.5 h-5">{{ model.context_window }}</Badge>
                                </div>
                            </div>
                            <div class="w-5 h-5 rounded-full border flex items-center justify-center transition-colors" :class="selectedModel === model.id ? 'border-primary bg-primary text-primary-foreground' : 'border-muted-foreground/30'">
                                <Check v-if="selectedModel === model.id" class="w-3 h-3" />
                            </div>
                        </div>
                        
                        <p class="text-sm text-muted-foreground mb-6 min-h-[40px] leading-relaxed">{{ model.description }}</p>
                        
                        <div class="space-y-3 bg-muted/30 rounded-lg p-4">
                            <div class="flex items-center justify-between text-xs">
                                <span class="text-muted-foreground font-medium">推理能力</span>
                                <div class="flex gap-1">
                                    <div v-for="i in 5" :key="i" class="w-6 h-1 rounded-full transition-all" :class="i <= model.reasoning_score ? (selectedModel === model.id ? 'bg-primary' : 'bg-muted-foreground/40') : 'bg-muted'"></div>
                                </div>
                            </div>
                            <div class="flex items-center justify-between text-xs">
                                <span class="text-muted-foreground font-medium">响应速度</span>
                                <div class="flex gap-1">
                                    <div v-for="i in 5" :key="i" class="w-6 h-1 rounded-full transition-all" :class="i <= (6-model.reasoning_score) ? (selectedModel === model.id ? 'bg-green-500' : 'bg-muted-foreground/40') : 'bg-muted'"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 4: Extraction Config -->
        <ScrollArea v-if="currentStep === 4" class="flex-1">
            <div class="p-8 max-w-3xl mx-auto space-y-8">
                <div>
                    <h3 class="text-2xl font-semibold tracking-tight">提取参数配置</h3>
                    <p class="text-muted-foreground mt-1">自定义输出格式和处理规则</p>
                </div>
                
                <div class="space-y-6">
                    <!-- Output Format -->
                    <Card class="p-6 space-y-4">
                        <Label class="text-base flex items-center gap-2">
                            <FileText class="w-4 h-4 text-primary" />
                            输出格式
                        </Label>
                        <RadioGroup v-model="outputFormat" class="grid grid-cols-3 gap-4">
                            <div v-for="fmt in ['JSON', 'CSV', 'Markdown Table']" :key="fmt">
                                <RadioGroupItem :value="fmt" :id="fmt" class="peer sr-only" />
                                <Label
                                    :for="fmt"
                                    class="flex items-center justify-center p-4 rounded-lg border-2 border-muted bg-popover hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:text-primary peer-data-[state=checked]:bg-primary/5 cursor-pointer transition-all"
                                >
                                    {{ fmt }}
                                </Label>
                            </div>
                        </RadioGroup>
                    </Card>

                    <!-- Extraction Mode -->
                    <Card class="p-6 space-y-4">
                        <Label class="text-base flex items-center gap-2">
                            <Settings2 class="w-4 h-4 text-purple-500" />
                            提取模式
                        </Label>
                        <RadioGroup v-model="extractionMode" class="space-y-3">
                            <div class="flex items-center space-x-2 p-4 rounded-lg border hover:bg-accent transition-all cursor-pointer" :class="extractionMode === 'Multi' ? 'border-primary bg-primary/5' : ''">
                                <RadioGroupItem value="Multi" id="multi" />
                                <Label for="multi" class="flex-1 cursor-pointer">
                                    <span class="block font-semibold">全面提取 (Multi)</span>
                                    <span class="block text-xs text-muted-foreground mt-0.5">提取所有符合条件的数据点</span>
                                </Label>
                            </div>
                            <div class="flex items-center space-x-2 p-4 rounded-lg border hover:bg-accent transition-all cursor-pointer" :class="extractionMode === 'Single' ? 'border-primary bg-primary/5' : ''">
                                <RadioGroupItem value="Single" id="single" />
                                <Label for="single" class="flex-1 cursor-pointer">
                                    <span class="block font-semibold">精准提取 (Single)</span>
                                    <span class="block text-xs text-muted-foreground mt-0.5">仅提取最佳匹配的唯一值</span>
                                </Label>
                            </div>
                        </RadioGroup>
                    </Card>

                    <!-- Advanced Options -->
                    <Card class="p-6 space-y-4">
                        <Label class="text-base flex items-center gap-2">
                            <SlidersHorizontal class="w-4 h-4 text-amber-500" />
                            高级选项
                        </Label>
                        <div class="flex gap-8">
                            <div class="flex items-center space-x-2">
                                <Switch id="lite-mode" v-model:checked="liteMode" />
                                <Label for="lite-mode">节省 Token</Label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <Switch id="handle-exceptions" v-model:checked="handleExceptions" />
                                <Label for="handle-exceptions">异常值标记</Label>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </ScrollArea>

        <!-- Step 5: Results -->
        <div v-if="currentStep === 5" class="flex-1 flex flex-col relative h-full">
            <div v-if="extracting" class="absolute inset-0 z-20 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center animate-in fade-in">
                <div class="relative mb-6">
                    <div class="w-20 h-20 border-4 border-primary/20 rounded-full animate-spin"></div>
                    <div class="absolute top-0 left-0 w-20 h-20 border-4 border-t-primary rounded-full animate-spin"></div>
                    <div class="absolute inset-0 flex items-center justify-center">
                        <Bot class="w-8 h-8 text-primary animate-pulse" />
                    </div>
                </div>
                <h3 class="text-lg font-semibold mt-2">AI 深度分析中...</h3>
                <p class="text-muted-foreground animate-pulse text-sm">正在提取 {{ selectedIndicators.length }} 个关键指标</p>
            </div>

            <div class="p-4 border-b flex justify-between items-center bg-card shadow-sm shrink-0">
                <div>
                    <h3 class="text-lg font-semibold">提取结果概览</h3>
                    <p class="text-xs text-muted-foreground mt-0.5">共发现 {{ results.length }} 个数据点</p>
                </div>
                <div class="flex gap-2">
                    <Button variant="outline" size="sm" class="gap-1.5">
                        <Download class="w-3.5 h-3.5" />
                        导出Excel
                    </Button>
                    <Button size="sm" class="gap-1.5 shadow-sm">
                        <FileText class="w-3.5 h-3.5" />
                        生成报告
                    </Button>
                </div>
            </div>

            <ScrollArea class="flex-1 bg-muted/20">
                <div class="p-6">
                    <div v-if="results.length > 0" class="grid grid-cols-1 gap-4">
                        <Card v-for="(res, idx) in results" :key="idx" class="overflow-hidden transition-all hover:shadow-md">
                            <div class="bg-muted/30 px-6 py-3 border-b flex justify-between items-center">
                                <div class="flex items-center gap-3">
                                    <span class="w-1.5 h-5 rounded-full" :class="res.status === 'success' ? 'bg-green-500' : 'bg-destructive'"></span>
                                    <span class="font-semibold text-sm">{{ res.indicator_name }}</span>
                                </div>
                                <Badge :variant="res.status === 'success' ? 'default' : 'destructive'" class="text-xs gap-1">
                                    <CheckCircle2 v-if="res.status === 'success'" class="w-3 h-3" />
                                    <XCircle v-else class="w-3 h-3" />
                                    {{ res.status === 'success' ? '成功' : '失败' }}
                                </Badge>
                            </div>
                            <div class="p-6 bg-card">
                                <pre class="text-xs font-mono text-muted-foreground whitespace-pre-wrap leading-relaxed">{{ res.content }}</pre>
                            </div>
                        </Card>
                    </div>
                    <div v-else-if="!extracting" class="h-[400px] flex flex-col items-center justify-center text-muted-foreground">
                        <div class="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mb-4">
                            <ClipboardList class="w-8 h-8 text-muted-foreground/50" />
                        </div>
                        <p class="text-base font-medium">暂无结果</p>
                        <p class="text-xs mt-1">请配置参数并开始提取</p>
                    </div>
                </div>
            </ScrollArea>
        </div>

        <!-- Footer Buttons -->
        <div class="p-4 border-t bg-card flex justify-between items-center shrink-0 z-10">
             <Button 
                variant="ghost" 
                @click="currentStep--" 
                :disabled="currentStep === 1 || extracting"
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
                    class="px-8 shadow-lg shadow-primary/20 gap-2"
                 >
                    {{ currentStep === 4 ? '开始提取' : '下一步' }}
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
                    重新开始
                 </Button>
             </div>
        </div>
    </Card>

    <!-- Indicator Modal -->
    <Dialog v-model:open="showIndicatorModal">
        <DialogContent class="sm:max-w-[800px] p-0 overflow-hidden">
            <div class="h-1.5 bg-gradient-to-r from-blue-500 to-indigo-600"></div>
            <div class="p-6">
                <DialogHeader class="mb-6">
                    <DialogTitle class="flex items-center gap-2 text-xl">
                        <span class="w-1 h-6 bg-primary rounded-full"></span>
                        {{ editingIndicator ? '编辑指标' : '新建指标' }}
                    </DialogTitle>
                </DialogHeader>
                <IndicatorForm 
                    :initialData="editingIndicator" 
                    :isEdit="!!editingIndicator"
                    @submit="handleIndicatorSubmit"
                    @cancel="showIndicatorModal = false"
                />
            </div>
        </DialogContent>
    </Dialog>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, defineAsyncComponent } from 'vue';
import axios from 'axios';
import { useToast } from '@/components/ui/toast/use-toast';
import { 
    Check, Mic, Database, UploadCloud, AlertTriangle, Search, Plus, 
    Edit2, FileText, Settings2, SlidersHorizontal, Bot, Download, 
    CheckCircle2, XCircle, ClipboardList, ChevronLeft, ChevronRight, 
    Play, RotateCcw, Loader2
} from 'lucide-vue-next';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

const IndicatorForm = defineAsyncComponent(() => import('./IndicatorForm.vue'));

const api = axios.create({ baseURL: '/api/v1' });
const { toast } = useToast();

const props = defineProps({
    prefilledIndicator: Object
});

// State
const currentStep = ref(1);
const extracting = ref(false);
const results = ref([]);

const steps = [
    { title: '数据源选择', description: '录音/知识库/文档' },
    { title: '选择指标', description: '设定提取目标' },
    { title: '模型配置', description: '选择AI模型' },
    { title: '参数设置', description: '输出格式配置' },
    { title: '提取结果', description: '查看与导出' }
];

// Step 1: Data Source
const sourceType = ref('recording');
const sourceTypes = [
    { value: 'recording', label: '录音文件', desc: '从录音记录中提取', icon: Mic, iconBg: 'bg-blue-100 dark:bg-blue-900/20', iconColor: 'text-blue-600 dark:text-blue-400' },
    { value: 'kb', label: '知识库', desc: '引用现有知识资产', icon: Database, iconBg: 'bg-amber-100 dark:bg-amber-900/20', iconColor: 'text-amber-600 dark:text-amber-400' },
    { value: 'upload', label: '本地上传', desc: 'PDF/Word/TXT', icon: UploadCloud, iconBg: 'bg-purple-100 dark:bg-purple-900/20', iconColor: 'text-purple-600 dark:text-purple-400' }
];

const files = ref([]);
const kbFiles = ref([]);
const selectedFileId = ref(null);
const selectedKbFileId = ref(null);
const uploading = ref(false);
const textContent = ref('');
const docInput = ref(null);

// Step 2: Indicators
const indicators = ref([]);
const selectedIndicators = ref([]);
const indicatorSearch = ref('');
const showIndicatorModal = ref(false);
const editingIndicator = ref(null);

// Step 3: Model
const availableModels = ref([
    { id: 'qwen-plus', name: 'Qwen Plus', description: '均衡型模型，在速度和性能之间保持良好的平衡，适合大多数通用提取任务。', context_window: '32k', reasoning_score: 4, icon: '🚀' },
    { id: 'qwen-max', name: 'Qwen Max', description: '最强推理能力，擅长处理复杂的逻辑分析和深层次的语义理解。', context_window: '32k', reasoning_score: 5, icon: '🧠' },
    { id: 'qwen-long', name: 'Qwen Long', description: '超长上下文支持，专为长文档和海量数据分析设计，可一次性处理整本书籍。', context_window: '200k', reasoning_score: 3, icon: '📜' },
    { id: 'qwen-turbo', name: 'Qwen Turbo', description: '极速响应，低成本，适合简单的提取任务和实时性要求高的场景。', context_window: '32k', reasoning_score: 3, icon: '⚡' },
]);
const selectedModel = ref('qwen-plus');

// Step 4: Config
const outputFormat = ref('JSON');
const extractionMode = ref('Multi');
const liteMode = ref(false);
const handleExceptions = ref(true);

// Computed
const canProceed = computed(() => {
    if (currentStep.value === 1) return !!textContent.value;
    if (currentStep.value === 2) return selectedIndicators.value.length > 0;
    if (currentStep.value === 3) return !!selectedModel.value;
    return true;
});

const canJumpTo = (step) => {
    if (step === 1) return true;
    if (step === 2) return !!textContent.value;
    if (step === 3) return !!textContent.value && selectedIndicators.value.length > 0;
    if (step === 4) return !!textContent.value && selectedIndicators.value.length > 0 && !!selectedModel.value;
    return false;
}

const filteredIndicators = computed(() => {
    if (!indicatorSearch.value) return indicators.value;
    const kw = indicatorSearch.value.toLowerCase();
    return indicators.value.filter(i => 
        i.name.toLowerCase().includes(kw) || 
        (i.group && i.group.toLowerCase().includes(kw))
    );
});

const isAllSelected = computed(() => {
    return filteredIndicators.value.length > 0 && 
           filteredIndicators.value.every(i => selectedIndicators.value.some(s => s.id === i.id));
});

// Methods
const nextStep = async () => {
    if (currentStep.value === 4) {
        currentStep.value = 5;
        await startExtraction();
    } else {
        currentStep.value++;
    }
};

const reset = () => {
    currentStep.value = 1;
    results.value = [];
    selectedIndicators.value = [];
    textContent.value = '';
};

// Data Source Logic
const fetchFiles = async () => {
    try {
        const [recRes, kbRes] = await Promise.all([
            api.get('/recordings/'),
            api.get('/knowledge/list')
        ]);
        files.value = recRes.data.filter(f => !f.is_folder && f.asr_status === 'completed');
        kbFiles.value = kbRes.data;
    } catch (e) {
        console.error(e);
    }
};

const handleFileChange = async () => {
    if (!selectedFileId.value) return;
    try {
        const res = await api.get(`/recordings/${selectedFileId.value}`);
        textContent.value = res.data.transcription_text || "无转写内容";
    } catch (e) {
        toast({ title: '获取内容失败', variant: 'destructive' });
    }
};

const handleKbFileChange = async () => {
    if (!selectedKbFileId.value) return;
    try {
        const res = await api.get(`/knowledge/${selectedKbFileId.value}/content`);
        textContent.value = res.data.content || "无内容";
    } catch (e) {
        toast({ title: '获取内容失败', variant: 'destructive' });
    }
};

const triggerDocUpload = () => docInput.value.click();

const handleDocUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    uploading.value = true;
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await api.post('/metrics/parse_doc', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        textContent.value = res.data.text || '';
        toast({ title: '解析成功' });
    } catch (e) {
        toast({ title: '解析失败', variant: 'destructive' });
    } finally {
        uploading.value = false;
        e.target.value = '';
    }
};

// Indicator Logic
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
        // Deselect all visible
        const visibleIds = filteredIndicators.value.map(i => i.id);
        selectedIndicators.value = selectedIndicators.value.filter(i => !visibleIds.includes(i.id));
    } else {
        // Select all visible
        const newItems = filteredIndicators.value.filter(i => !isSelected(i));
        selectedIndicators.value.push(...newItems);
    }
};

const openIndicatorModal = (indicator = null) => {
    editingIndicator.value = indicator ? { ...indicator } : null;
    showIndicatorModal.value = true;
};

const handleIndicatorSubmit = async (payload) => {
    try {
        if (editingIndicator.value) {
            await api.patch(`/indicators/${editingIndicator.value.id}`, payload);
            toast({ title: '更新成功' });
        } else {
            await api.post('/indicators/', payload);
            toast({ title: '创建成功' });
        }
        showIndicatorModal.value = false;
        fetchIndicators();
    } catch (e) {
        toast({ title: '保存失败', variant: 'destructive' });
    }
};

// Extraction Logic
const startExtraction = async () => {
    extracting.value = true;
    results.value = [];
    
    try {
        // Process sequentially or parallel
        // For simplicity and stability, sequential
        for (const indicator of selectedIndicators.value) {
            try {
                const res = await api.post('/metrics/extract', {
                    indicator_name: indicator.name,
                    definition: indicator.description, // Use description as definition
                    text_content: textContent.value,
                    aliases: indicator.alias,
                    output_format: outputFormat.value,
                    language: 'CN', // Could be configurable
                    extraction_mode: extractionMode.value,
                    model: selectedModel.value,
                    advanced_options: indicator.advanced_options // Pass advanced options
                });
                
                results.value.push({
                    indicator_name: indicator.name,
                    status: 'success',
                    content: res.data.content
                });
            } catch (err) {
                results.value.push({
                    indicator_name: indicator.name,
                    status: 'error',
                    content: '提取失败: ' + (err.response?.data?.detail || err.message)
                });
            }
        }
        toast({ title: '提取任务完成' });
    } catch (e) {
        toast({ title: '提取过程发生错误', variant: 'destructive' });
    } finally {
        extracting.value = false;
    }
};

onMounted(() => {
    fetchFiles();
    fetchIndicators();
    if (props.prefilledIndicator) {
        selectedIndicators.value.push(props.prefilledIndicator);
        currentStep.value = 1; // Start from beginning but with indicator selected
    }
});
</script>
