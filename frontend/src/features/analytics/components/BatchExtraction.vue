<template>
  <div class="max-w-[1600px] mx-auto p-6 h-[calc(100vh-20px)] animate-fade-in-up flex gap-6">
    
    <!-- Left Sidebar: Steps Navigation -->
    <div class="w-72 bg-white rounded-lg border border-border shadow-sm flex flex-col overflow-hidden shrink-0 h-full">
        <div class="p-6 border-b border-slate-50">
            <h2 class="text-xl font-semibold text-slate-800 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-purple-600 rounded-full"></span>
                批量提取
            </h2>
            <p class="text-xs text-muted-foreground mt-2">支持多文档并发处理与分析</p>
        </div>
        
        <div class="flex-1 overflow-y-auto py-4 custom-scrollbar">
            <div v-for="step in 5" :key="step" 
                class="relative px-6 py-4 cursor-pointer transition-all group flex items-start gap-4"
                :class="currentStep === step ? 'bg-purple-50/50' : 'hover:bg-muted/50'"
                @click="canJumpTo(step) && (currentStep = step)"
            >
                <!-- Connecting Line -->
                <div v-if="step < 5" class="absolute left-[39px] top-10 bottom-[-20px] w-0.5 bg-muted group-last:hidden"></div>

                <!-- Step Number/Icon -->
                <div 
                    class="relative z-10 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-xs font-din transition-all duration-300 border-2 shrink-0"
                    :class="[
                        currentStep === step ? 'bg-purple-600 border-purple-600 text-white shadow-lg shadow-purple-600/30' : 
                        currentStep > step ? 'bg-purple-600 border-purple-600 text-white' : 
                        'bg-white border-slate-200 text-muted-foreground group-hover:border-purple-300'
                    ]"
                >
                    <svg v-if="currentStep > step" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                    <span v-else>{{ step }}</span>
                </div>

                <!-- Step Text -->
                <div class="flex-1 pt-1">
                    <h4 class="font-semibold text-sm transition-colors" :class="currentStep === step ? 'text-slate-800' : 'text-muted-foreground'">
                        {{ ['文档导入', '指标选择', '模型配置', '任务参数', '批量结果'][step-1] }}
                    </h4>
                    <p class="text-xs text-muted-foreground mt-1 line-clamp-1">
                        {{ ['批量上传文档', '选择指标体系', '配置处理模型', '输出与错误处理', '查看任务进度'][step-1] }}
                    </p>
                </div>

                <!-- Active Indicator -->
                <div v-if="currentStep === step" class="absolute left-0 top-0 bottom-0 w-1 bg-purple-600 rounded-r"></div>
            </div>
        </div>
    </div>

    <!-- Right Content Area -->
    <div class="flex-1 bg-white rounded-lg border border-border shadow-sm flex flex-col overflow-hidden h-full relative">
        
        <!-- Step 1: Batch File Upload -->
        <div v-if="currentStep === 1" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar p-8">
            <div class="max-w-5xl mx-auto">
                <div class="mb-8 text-center">
                    <h3 class="text-2xl font-semibold text-slate-800">批量导入文档</h3>
                    <p class="text-muted-foreground mt-1">拖拽文件到下方区域，支持多选上传 (Max 100)</p>
                </div>
                
                <div 
                    @click="triggerBatchUpload"
                    class="border-2 border-dashed border-slate-300 rounded-lg p-12 text-center cursor-pointer hover:border-purple-500 hover:bg-purple-50/20 transition-all group mb-8 bg-muted/50 relative overflow-hidden"
                >
                    <input type="file" ref="fileInput" class="hidden" multiple accept=".pdf,.docx,.doc,.txt" @change="handleBatchUpload">
                    <div class="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none"></div>
                    
                    <div class="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 border border-border">
                        <svg class="w-8 h-8 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"/></svg>
                    </div>
                    <p class="text-lg font-semibold text-slate-700 group-hover:text-purple-600 transition-colors">点击选择或拖拽多个文件</p>
                    <p class="text-sm text-muted-foreground mt-2">支持 PDF, Word, TXT 格式</p>
                </div>

                <div v-if="files.length > 0" class="space-y-4 animate-fade-in">
                    <div class="flex justify-between items-center px-1">
                        <h4 class="font-semibold text-slate-700 flex items-center gap-2">
                            已添加文件 
                            <span class="px-2 py-0.5 bg-muted text-slate-600 rounded-md text-xs">{{ files.length }}</span>
                        </h4>
                        <button @click="files = []" class="text-xs text-red-500 hover:text-red-700 font-medium hover:bg-red-50 px-2 py-1 rounded transition-colors">清空列表</button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div v-for="(file, index) in files" :key="index" class="bg-white border border-slate-200 rounded-lg p-4 flex justify-between items-center group hover:shadow-md hover:border-purple-200 transition-all">
                            <div class="flex items-center gap-4 overflow-hidden">
                                <div class="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0 text-muted-foreground font-semibold text-xs uppercase">
                                    {{ file.name.split('.').pop() }}
                                </div>
                                <div class="overflow-hidden">
                                    <p class="text-sm font-medium text-slate-700 truncate" :title="file.name">{{ file.name }}</p>
                                    <p class="text-xs text-muted-foreground">{{ (file.size / 1024).toFixed(1) }} KB</p>
                                </div>
                            </div>
                            <button @click="removeFile(index)" class="text-slate-300 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 2: Indicator Selection (Reused logic) -->
        <div v-if="currentStep === 2" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar flex flex-col p-6">
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h3 class="text-2xl font-semibold text-slate-800">选择指标体系</h3>
                    <p class="text-muted-foreground text-sm mt-1">选择需要批量提取的指标集合</p>
                </div>
                <div class="flex gap-4">
                    <div class="relative">
                        <input 
                            v-model="indicatorSearch" 
                            type="text" 
                            placeholder="搜索指标..." 
                            class="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all bg-white shadow-sm"
                        >
                        <svg class="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    </div>
                </div>
            </div>

            <div class="flex-1 overflow-hidden border border-slate-200 rounded-lg bg-white flex flex-col shadow-sm">
                <div class="bg-muted/50 border-b border-slate-200 grid grid-cols-12 gap-4 px-6 p-4 font-semibold text-slate-600 text-xs uppercase tracking-wider sticky top-0 z-10">
                    <div class="col-span-1 flex items-center justify-center">
                        <div class="relative flex items-center">
                             <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" class="peer h-4 w-4 cursor-pointer appearance-none rounded border border-slate-300 bg-white transition-all checked:border-purple-500 checked:bg-purple-500 hover:border-purple-400">
                             <svg class="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 transition-opacity peer-checked:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                        </div>
                    </div>
                    <div class="col-span-3">指标名称</div>
                    <div class="col-span-2">分组</div>
                    <div class="col-span-6">描述</div>
                </div>
                <div class="overflow-y-auto custom-scrollbar flex-1">
                    <div 
                        v-for="indicator in filteredIndicators" 
                        :key="indicator.id" 
                        class="grid grid-cols-12 gap-4 px-6 p-4 border-b border-border items-center hover:bg-purple-50/30 transition-colors cursor-pointer group text-sm"
                        :class="isSelected(indicator) ? 'bg-purple-50/40' : ''"
                        @click="toggleSelection(indicator)"
                    >
                        <div class="col-span-1 flex items-center justify-center" @click.stop>
                            <div class="relative flex items-center">
                                <input type="checkbox" :checked="isSelected(indicator)" @change="toggleSelection(indicator)" class="peer h-4 w-4 cursor-pointer appearance-none rounded border border-slate-300 bg-white transition-all checked:border-purple-500 checked:bg-purple-500 hover:border-purple-400">
                                <svg class="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 transition-opacity peer-checked:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                            </div>
                        </div>
                        <div class="col-span-3 font-medium text-slate-800 group-hover:text-purple-700 transition-colors">{{ indicator.name }}</div>
                        <div class="col-span-2">
                            <span class="px-2 py-0.5 bg-muted text-slate-600 rounded text-xs border border-slate-200">{{ indicator.group }}</span>
                        </div>
                        <div class="col-span-6 text-muted-foreground truncate" :title="indicator.description">{{ indicator.description || '-' }}</div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4 flex justify-between items-center px-2">
                <div class="text-sm text-muted-foreground">
                    <span class="font-medium text-slate-700">{{ filteredIndicators.length }}</span> 个指标可用
                </div>
                <div class="text-sm font-medium" :class="selectedIndicators.length > 0 ? 'text-purple-600' : 'text-muted-foreground'">
                    已选择 {{ selectedIndicators.length }} 个指标
                </div>
            </div>
        </div>

        <!-- Step 3: Model Configuration -->
        <div v-if="currentStep === 3" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar p-8">
            <div class="max-w-5xl mx-auto">
                <div class="mb-8">
                    <h3 class="text-2xl font-semibold text-slate-800">配置处理模型</h3>
                    <p class="text-muted-foreground mt-1">建议选择长上下文模型以应对批量任务</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                     <div 
                        v-for="model in availableModels" 
                        :key="model.id"
                        @click="selectedModel = model.id"
                        class="p-6 border rounded-lg cursor-pointer transition-all hover:shadow-lg relative overflow-hidden group bg-white"
                        :class="selectedModel === model.id ? 'border-purple-500 ring-1 ring-purple-500 bg-purple-50/5' : 'border-slate-200 hover:border-purple-300'"
                    >
                        <div class="flex justify-between items-start mb-4">
                            <div class="w-10 h-10 rounded-lg bg-white border border-border flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                                {{ model.icon || '🤖' }}
                            </div>
                            <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors" :class="selectedModel === model.id ? 'border-purple-500 bg-purple-500 text-white' : 'border-slate-300 text-transparent'">
                                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                            </div>
                        </div>
                        <h4 class="font-semibold text-slate-800 mb-1">{{ model.name }}</h4>
                        <div class="flex items-center gap-2 mb-4">
                            <span class="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground font-medium">{{ model.context_window }}</span>
                        </div>
                        <p class="text-sm text-slate-600">{{ model.description }}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 4: Extraction Config -->
        <div v-if="currentStep === 4" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar p-8">
            <div class="max-w-3xl mx-auto">
                <div class="mb-8">
                    <h3 class="text-2xl font-semibold text-slate-800">批量任务配置</h3>
                    <p class="text-muted-foreground mt-1">设置输出和错误处理策略</p>
                </div>
                
                <div class="space-y-6">
                    <div class="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
                        <label class="block text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            输出格式
                        </label>
                        <div class="grid grid-cols-3 gap-4">
                            <label v-for="fmt in ['Excel', 'JSON', 'CSV']" :key="fmt" class="cursor-pointer">
                                <input type="radio" v-model="outputFormat" :value="fmt" class="hidden peer">
                                <div class="p-4 border border-slate-200 rounded-lg text-center hover:border-purple-300 peer-checked:border-purple-500 peer-checked:bg-purple-50 peer-checked:text-purple-700 transition-all text-sm font-semibold">
                                    {{ fmt }}
                                </div>
                            </label>
                        </div>
                    </div>

                    <div class="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
                        <label class="block text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                            错误处理
                        </label>
                        <div class="space-y-3">
                            <label class="flex items-center gap-2 cursor-pointer group">
                                <div class="relative">
                                    <input type="checkbox" v-model="skipErrors" class="sr-only peer">
                                    <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
                                </div>
                                <span class="text-sm font-medium text-slate-700">跳过处理失败的文档继续执行</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 5: Results -->
        <div v-if="currentStep === 5" class="flex-1 p-0 overflow-hidden flex flex-col animate-fade-in relative bg-muted/50/50">
            <div class="p-4 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm shrink-0">
                <div class="flex items-center gap-6">
                    <div>
                        <h3 class="text-lg font-semibold text-slate-800">批量任务状态</h3>
                        <p class="text-xs text-muted-foreground mt-0.5" v-if="isRunning">预计剩余时间: {{ estimatedTimeRemaining }}</p>
                    </div>
                    <div class="flex items-center gap-4">
                        <div class="w-32 h-2 bg-muted rounded-full overflow-hidden">
                            <div class="h-full bg-purple-600 transition-all duration-500" :style="{ width: progressPercent + '%' }"></div>
                        </div>
                        <span class="font-din font-semibold text-slate-700 text-lg">{{ progressPercent }}%</span>
                        <span class="text-xs text-muted-foreground">({{ completedCount }}/{{ totalTasks }})</span>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button 
                        @click="togglePause" 
                        class="p-4 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium transition-all shadow-sm flex items-center gap-1.5"
                        :class="isPaused ? 'text-green-600 border-green-200 hover:bg-green-50' : 'text-amber-600 border-amber-200 hover:bg-amber-50'"
                    >
                        <svg v-if="isPaused" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                        <svg v-else class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                        {{ isPaused ? '继续' : '暂停' }}
                    </button>
                    <button class="p-4 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700 transition-colors shadow-md shadow-purple-600/20 flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        汇总报告
                    </button>
                </div>
            </div>

            <div class="flex-1 overflow-auto p-6 custom-scrollbar">
                <div class="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                    <table class="w-full text-left border-collapse">
                        <thead class="bg-muted/50 border-b border-slate-200">
                            <tr>
                                <th class="p-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-6">文件名</th>
                                <th class="p-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">状态</th>
                                <th class="p-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">耗时</th>
                                <th class="p-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">提取指标数</th>
                                <th class="p-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider pr-6 text-right">操作</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="(task, idx) in batchTasks" :key="idx" class="hover:bg-muted/50/80 transition-colors group">
                                <td class="p-4 pl-6 font-medium text-slate-700 flex items-center gap-4">
                                    <div class="w-8 h-8 rounded bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground uppercase">
                                        {{ task.fileName.split('.').pop() }}
                                    </div>
                                    <span class="text-sm truncate max-w-[200px]" :title="task.fileName">{{ task.fileName }}</span>
                                </td>
                                <td class="p-4">
                                    <span class="px-2 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1.5 w-fit border"
                                        :class="{
                                            'bg-muted/50 text-muted-foreground border-border': task.status === 'pending',
                                            'bg-primary/10 text-primary border-blue-100': task.status === 'processing',
                                            'bg-green-50 text-green-600 border-green-100': task.status === 'completed',
                                            'bg-red-50 text-red-600 border-red-100': task.status === 'failed',
                                            'bg-amber-50 text-amber-600 border-amber-100': task.status === 'paused'
                                        }"
                                    >
                                        <span v-if="task.status === 'processing'" class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                                        <span v-else class="w-1.5 h-1.5 rounded-full" :class="{
                                            'bg-slate-400': task.status === 'pending',
                                            'bg-green-500': task.status === 'completed',
                                            'bg-red-500': task.status === 'failed',
                                            'bg-amber-500': task.status === 'paused'
                                        }"></span>
                                        {{ getStatusText(task.status) }}
                                    </span>
                                </td>
                                <td class="p-4 text-xs font-din text-slate-600">{{ task.duration ? task.duration + 's' : '-' }}</td>
                                <td class="p-4 text-xs font-din text-slate-600">
                                    <span v-if="task.indicatorCount > 0" class="px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded text-xs font-semibold">{{ task.indicatorCount }}</span>
                                    <span v-else>-</span>
                                </td>
                                <td class="p-4 pr-6 text-right">
                                    <button v-if="task.status === 'completed'" class="text-purple-600 hover:text-purple-800 text-xs font-semibold hover:underline">查看</button>
                                    <button v-if="task.status === 'failed'" class="text-red-600 hover:text-red-800 text-xs font-semibold hover:underline">重试</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Footer Buttons -->
        <div class="p-4 border-t border-border bg-white flex justify-between items-center shrink-0 z-20">
             <button 
                @click="currentStep--" 
                :disabled="currentStep === 1 || isRunning"
                class="px-6 py-2.5 rounded-lg font-semibold transition-all flex items-center gap-2 text-sm"
                :class="currentStep === 1 ? 'text-slate-300 cursor-not-allowed' : 'text-slate-600 hover:bg-muted hover:text-slate-900'"
             >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                上一步
             </button>
             
             <div class="flex gap-4">
                 <button 
                    v-if="currentStep < 5"
                    @click="nextStep"
                    :disabled="!canProceed"
                    class="px-8 py-2.5 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 shadow-md shadow-purple-600/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transition-all hover:scale-105 active:scale-95 flex items-center gap-2 text-sm"
                 >
                    {{ currentStep === 4 ? '开始批量提取' : '下一步' }}
                    <svg v-if="currentStep < 4" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                    <svg v-if="currentStep === 4" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                 </button>
                 <button 
                    v-if="currentStep === 5"
                    @click="reset"
                    class="px-6 py-2.5 bg-muted text-slate-700 rounded-lg font-semibold hover:bg-slate-200 transition-all flex items-center gap-2 text-sm"
                 >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
                    新建批量任务
                 </button>
             </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue';

const api = axios.create({ baseURL: '/api/v1' });

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
        message.warning('最多支持 100 个文件');
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
        message.success('批量任务完成');
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

onMounted(() => {
    fetchIndicators();
});
</script>

<style scoped>
.font-din {
    font-family: 'DIN Alternate', 'Roboto', sans-serif;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 4px;
}

.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: #cbd5e1;
}

.bg-grid-pattern {
    background-image: radial-gradient(currentColor 1px, transparent 1px);
    background-size: 20px 20px;
}

@keyframes fade-in-up {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in-up {
    animation: fade-in-up 0.4s ease-out;
}
</style>