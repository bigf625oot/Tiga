<template>
  <div class="max-w-[1600px] mx-auto p-6 h-[calc(100vh-20px)] animate-fade-in-up flex gap-6">
    
    <!-- Left Sidebar: Steps Navigation -->
    <div class="w-72 bg-white rounded-2xl border border-slate-100 shadow-sm flex flex-col overflow-hidden shrink-0 h-full">
        <div class="p-6 border-b border-slate-50">
            <h2 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-blue-600 rounded-full"></span>
                指标提取
            </h2>
            <p class="text-xs text-slate-400 mt-2">五步完成智能化数据提取</p>
        </div>
        
        <div class="flex-1 overflow-y-auto py-4 custom-scrollbar">
            <div v-for="step in 5" :key="step" 
                class="relative px-6 py-4 cursor-pointer transition-all group flex items-start gap-4"
                :class="currentStep === step ? 'bg-blue-50/50' : 'hover:bg-slate-50'"
                @click="canJumpTo(step) && (currentStep = step)"
            >
                <!-- Connecting Line -->
                <div v-if="step < 5" class="absolute left-[39px] top-10 bottom-[-20px] w-0.5 bg-slate-100 group-last:hidden"></div>

                <!-- Step Number/Icon -->
                <div 
                    class="relative z-10 w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs font-din transition-all duration-300 border-2 shrink-0"
                    :class="[
                        currentStep === step ? 'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-600/30' : 
                        currentStep > step ? 'bg-blue-600 border-blue-600 text-white' : 
                        'bg-white border-slate-200 text-slate-400 group-hover:border-blue-300'
                    ]"
                >
                    <svg v-if="currentStep > step" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                    <span v-else>{{ step }}</span>
                </div>

                <!-- Step Text -->
                <div class="flex-1 pt-1">
                    <h4 class="font-bold text-sm transition-colors" :class="currentStep === step ? 'text-slate-800' : 'text-slate-500'">
                        {{ ['数据源选择', '选择指标', '模型配置', '参数设置', '提取结果'][step-1] }}
                    </h4>
                    <p class="text-xs text-slate-400 mt-1 line-clamp-1">
                        {{ ['录音/知识库/文档', '设定提取目标', '选择AI模型', '输出格式配置', '查看与导出'][step-1] }}
                    </p>
                </div>

                <!-- Active Indicator -->
                <div v-if="currentStep === step" class="absolute left-0 top-0 bottom-0 w-1 bg-blue-600 rounded-r"></div>
            </div>
        </div>
    </div>

    <!-- Right Content Area -->
    <div class="flex-1 bg-white rounded-2xl border border-slate-100 shadow-sm flex flex-col overflow-hidden h-full relative">
        
        <!-- Step 1: Data Source Selection -->
        <div v-if="currentStep === 1" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar p-8">
            <div class="max-w-4xl mx-auto">
                <div class="mb-8">
                    <h3 class="text-2xl font-bold text-slate-800">选择数据来源</h3>
                    <p class="text-slate-500 mt-1">支持从多种渠道导入数据进行分析</p>
                </div>
                
                <!-- Compact Cards -->
                <div class="grid grid-cols-3 gap-4 mb-8">
                    <div 
                        @click="sourceType = 'recording'"
                        class="p-4 rounded-xl border transition-all cursor-pointer flex items-center gap-4 hover:shadow-md h-24 relative overflow-hidden group bg-white"
                        :class="sourceType === 'recording' ? 'border-blue-500 ring-2 ring-blue-500/10 bg-blue-50/10' : 'border-slate-200 hover:border-blue-300'"
                    >
                        <div class="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <span class="block font-bold text-slate-700 text-base">录音文件</span>
                            <span class="block text-xs text-slate-400 mt-1 truncate">从录音记录中提取</span>
                        </div>
                        <div class="w-4 h-4 rounded-full border-2 flex items-center justify-center" :class="sourceType === 'recording' ? 'border-blue-500' : 'border-slate-300'">
                             <div v-if="sourceType === 'recording'" class="w-2 h-2 rounded-full bg-blue-500"></div>
                        </div>
                    </div>

                    <div 
                        @click="sourceType = 'kb'"
                        class="p-4 rounded-xl border transition-all cursor-pointer flex items-center gap-4 hover:shadow-md h-24 relative overflow-hidden group bg-white"
                        :class="sourceType === 'kb' ? 'border-amber-500 ring-2 ring-amber-500/10 bg-amber-50/10' : 'border-slate-200 hover:border-amber-300'"
                    >
                        <div class="w-12 h-12 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <span class="block font-bold text-slate-700 text-base">知识库</span>
                            <span class="block text-xs text-slate-400 mt-1 truncate">引用现有知识资产</span>
                        </div>
                        <div class="w-4 h-4 rounded-full border-2 flex items-center justify-center" :class="sourceType === 'kb' ? 'border-amber-500' : 'border-slate-300'">
                             <div v-if="sourceType === 'kb'" class="w-2 h-2 rounded-full bg-amber-500"></div>
                        </div>
                    </div>

                    <div 
                        @click="sourceType = 'upload'"
                        class="p-4 rounded-xl border transition-all cursor-pointer flex items-center gap-4 hover:shadow-md h-24 relative overflow-hidden group bg-white"
                        :class="sourceType === 'upload' ? 'border-purple-500 ring-2 ring-purple-500/10 bg-purple-50/10' : 'border-slate-200 hover:border-purple-300'"
                    >
                        <div class="w-12 h-12 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <span class="block font-bold text-slate-700 text-base">本地上传</span>
                            <span class="block text-xs text-slate-400 mt-1 truncate">PDF/Word/TXT</span>
                        </div>
                        <div class="w-4 h-4 rounded-full border-2 flex items-center justify-center" :class="sourceType === 'upload' ? 'border-purple-500' : 'border-slate-300'">
                             <div v-if="sourceType === 'upload'" class="w-2 h-2 rounded-full bg-purple-500"></div>
                        </div>
                    </div>
                </div>
                
                <!-- File Selection Logic -->
                <div class="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm transition-all duration-300">
                    <div v-if="sourceType === 'recording'" class="w-full">
                        <label class="block text-sm font-bold text-slate-700 mb-3 ml-1">选择已转写文件</label>
                        <a-select
                            v-model:value="selectedFileId"
                            show-search
                            placeholder="-- 请选择或搜索文件 --"
                            option-filter-prop="label"
                            class="w-full"
                            size="large"
                            @change="handleFileChange"
                            :options="files.map(f => ({ label: `${f.filename} (${f.duration}s)`, value: f.id }))"
                        >
                            <template #suffixIcon>
                                <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                            </template>
                        </a-select>
                    </div>

                    <div v-else-if="sourceType === 'kb'" class="w-full">
                         <label class="block text-sm font-bold text-slate-700 mb-3 ml-1">选择知识库文件</label>
                         <a-select
                            v-model:value="selectedKbFileId"
                            show-search
                            placeholder="-- 请选择或搜索知识库文件 --"
                            option-filter-prop="label"
                            class="w-full"
                            size="large"
                            @change="handleKbFileChange"
                            :options="kbFiles.map(f => ({ label: `${f.filename} (${(f.file_size/1024).toFixed(1)} KB)`, value: f.id }))"
                        >
                             <template #suffixIcon>
                                <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                            </template>
                        </a-select>
                    </div>

                    <div v-else class="w-full">
                         <div 
                            @click="triggerDocUpload"
                            class="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50/30 transition-all group bg-slate-50 hover:bg-white"
                        >
                            <input type="file" ref="docInput" class="hidden" accept=".pdf,.docx,.doc,.txt" @change="handleDocUpload">
                            <div v-if="uploading">
                                <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-3" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                <span class="text-slate-500 font-medium">正在解析文档内容...</span>
                            </div>
                            <div v-else class="flex flex-col items-center">
                                <div class="w-12 h-12 bg-white border border-slate-200 shadow-sm rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300">
                                    <svg class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                </div>
                                <p class="text-base font-bold text-slate-700 group-hover:text-blue-600 transition-colors">点击上传或拖拽文件</p>
                                <p class="text-xs text-slate-400 mt-1">PDF, Word, TXT (Max 20MB)</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Preview -->
                <div class="mt-6 transition-all duration-500 ease-in-out" :class="textContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'">
                    <label class="block text-sm font-bold text-slate-700 mb-2 ml-1 flex justify-between items-center">
                        文本预览
                        <span v-if="textContent" class="text-xs font-normal text-slate-400 bg-white border border-slate-200 px-2 py-1 rounded-md">{{ (textContent.length / 1000).toFixed(1) }}k 字符</span>
                    </label>
                    <div class="relative group">
                        <textarea 
                            v-model="textContent" 
                            readonly
                            rows="10" 
                            class="w-full px-5 py-4 border border-slate-200 rounded-xl bg-slate-50 text-slate-600 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all custom-scrollbar shadow-inner"
                            :placeholder="sourceType === 'recording' ? '选择文件后显示内容...' : '上传文档后显示内容...'"
                        ></textarea>
                        <div v-if="textContent && textContent.length > 30000" class="absolute bottom-4 right-4 bg-amber-50 text-amber-700 px-3 py-1 rounded-lg text-xs font-medium border border-amber-100 shadow-sm flex items-center gap-1">
                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                            超长文档
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 2: Indicator Selection -->
        <div v-if="currentStep === 2" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar flex flex-col p-6">
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h3 class="text-2xl font-bold text-slate-800">选择需要提取的指标</h3>
                    <p class="text-slate-500 text-sm mt-1">从指标库中选择或创建新指标</p>
                </div>
                <div class="flex gap-3">
                    <div class="relative">
                        <input 
                            v-model="indicatorSearch" 
                            type="text" 
                            placeholder="搜索指标名称..." 
                            class="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all bg-white shadow-sm"
                        >
                        <svg class="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    </div>
                    <button 
                        @click="openIndicatorModal()" 
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-all shadow-md shadow-blue-600/20 active:scale-95 flex items-center gap-2"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                        新建
                    </button>
                </div>
            </div>

            <div class="flex-1 overflow-hidden border border-slate-200 rounded-xl bg-white flex flex-col shadow-sm">
                <!-- Table Header -->
                <div class="bg-slate-50 border-b border-slate-200 grid grid-cols-12 gap-4 px-6 py-3 font-semibold text-slate-600 text-xs uppercase tracking-wider sticky top-0 z-10">
                    <div class="col-span-1 flex items-center justify-center">
                        <div class="relative flex items-center">
                             <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" class="peer h-4 w-4 cursor-pointer appearance-none rounded border border-slate-300 bg-white transition-all checked:border-blue-500 checked:bg-blue-500 hover:border-blue-400">
                             <svg class="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 transition-opacity peer-checked:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                        </div>
                    </div>
                    <div class="col-span-3">指标名称</div>
                    <div class="col-span-2">分组</div>
                    <div class="col-span-2">别名</div>
                    <div class="col-span-3">描述</div>
                    <div class="col-span-1 text-center">操作</div>
                </div>

                <!-- Table Body -->
                <div class="overflow-y-auto custom-scrollbar flex-1">
                    <div 
                        v-for="indicator in filteredIndicators" 
                        :key="indicator.id" 
                        class="grid grid-cols-12 gap-4 px-6 py-3 border-b border-slate-100 items-center hover:bg-blue-50/30 transition-colors cursor-pointer group text-sm"
                        :class="isSelected(indicator) ? 'bg-blue-50/40' : ''"
                        @click="toggleSelection(indicator)"
                    >
                        <div class="col-span-1 flex items-center justify-center" @click.stop>
                            <div class="relative flex items-center">
                                <input type="checkbox" :checked="isSelected(indicator)" @change="toggleSelection(indicator)" class="peer h-4 w-4 cursor-pointer appearance-none rounded border border-slate-300 bg-white transition-all checked:border-blue-500 checked:bg-blue-500 hover:border-blue-400">
                                <svg class="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 transition-opacity peer-checked:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                            </div>
                        </div>
                        <div class="col-span-3 font-medium text-slate-800 group-hover:text-blue-700 transition-colors">{{ indicator.name }}</div>
                        <div class="col-span-2">
                            <span class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs border border-slate-200">{{ indicator.group }}</span>
                        </div>
                        <div class="col-span-2 text-slate-500">{{ indicator.alias || '-' }}</div>
                        <div class="col-span-3 text-slate-500 truncate" :title="indicator.description">{{ indicator.description || '-' }}</div>
                        <div class="col-span-1 text-center" @click.stop>
                            <button @click="openIndicatorModal(indicator)" class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-all">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4 flex justify-between items-center px-2">
                <div class="text-sm text-slate-500">
                    <span class="font-medium text-slate-700">{{ filteredIndicators.length }}</span> 个指标可用
                </div>
                <div class="text-sm font-medium" :class="selectedIndicators.length > 0 ? 'text-blue-600' : 'text-slate-400'">
                    已选择 {{ selectedIndicators.length }} 个指标
                </div>
            </div>
        </div>

        <!-- Step 3: Model Configuration -->
        <div v-if="currentStep === 3" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar p-8">
            <div class="max-w-4xl mx-auto">
                <div class="mb-8">
                    <h3 class="text-2xl font-bold text-slate-800">配置 AI 模型</h3>
                    <p class="text-slate-500 mt-1">选择最适合当前任务的大语言模型</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div 
                        v-for="model in availableModels" 
                        :key="model.id"
                        @click="selectedModel = model.id"
                        class="p-6 border rounded-xl cursor-pointer transition-all hover:shadow-lg relative overflow-hidden group bg-white"
                        :class="selectedModel === model.id ? 'border-blue-500 ring-1 ring-blue-500 bg-blue-50/5' : 'border-slate-200 hover:border-blue-300'"
                    >
                        <div class="flex justify-between items-start mb-4">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                                    {{ model.icon || '🤖' }}
                                </div>
                                <div>
                                    <h4 class="font-bold text-slate-800">{{ model.name }}</h4>
                                    <span class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-500 font-medium">{{ model.context_window }}</span>
                                </div>
                            </div>
                            <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors" :class="selectedModel === model.id ? 'border-blue-500 bg-blue-500 text-white' : 'border-slate-300 text-transparent'">
                                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                            </div>
                        </div>
                        
                        <p class="text-sm text-slate-600 mb-6 min-h-[40px]">{{ model.description }}</p>
                        
                        <div class="space-y-3 bg-slate-50/50 rounded-lg p-3">
                            <div class="flex items-center justify-between text-xs">
                                <span class="text-slate-500 font-medium">推理能力</span>
                                <div class="flex gap-1">
                                    <div v-for="i in 5" :key="i" class="w-6 h-1 rounded-full transition-all" :class="i <= model.reasoning_score ? (selectedModel === model.id ? 'bg-blue-500' : 'bg-slate-400') : 'bg-slate-200'"></div>
                                </div>
                            </div>
                            <div class="flex items-center justify-between text-xs">
                                <span class="text-slate-500 font-medium">响应速度</span>
                                <div class="flex gap-1">
                                    <div v-for="i in 5" :key="i" class="w-6 h-1 rounded-full transition-all" :class="i <= (6-model.reasoning_score) ? (selectedModel === model.id ? 'bg-green-500' : 'bg-slate-400') : 'bg-slate-200'"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 4: Extraction Config -->
        <div v-if="currentStep === 4" class="flex-1 overflow-y-auto animate-fade-in custom-scrollbar p-8">
            <div class="max-w-3xl mx-auto">
                <div class="mb-8">
                    <h3 class="text-2xl font-bold text-slate-800">提取参数配置</h3>
                    <p class="text-slate-500 mt-1">自定义输出格式和处理规则</p>
                </div>
                
                <div class="space-y-6">
                    <!-- Output Format -->
                    <div class="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                        <label class="block text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            输出格式
                        </label>
                        <div class="grid grid-cols-3 gap-4">
                            <label v-for="fmt in ['JSON', 'CSV', 'Markdown Table']" :key="fmt" class="cursor-pointer">
                                <input type="radio" v-model="outputFormat" :value="fmt" class="hidden peer">
                                <div class="p-3 border border-slate-200 rounded-lg text-center hover:border-blue-300 peer-checked:border-blue-500 peer-checked:bg-blue-50 peer-checked:text-blue-700 transition-all text-sm font-bold">
                                    {{ fmt }}
                                </div>
                            </label>
                        </div>
                    </div>

                    <!-- Extraction Mode -->
                    <div class="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                        <label class="block text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                            提取模式
                        </label>
                        <div class="space-y-3">
                            <label class="flex p-4 border border-slate-200 rounded-lg cursor-pointer hover:border-blue-300 transition-all" :class="extractionMode === 'Multi' ? 'border-blue-500 bg-blue-50/30 ring-1 ring-blue-500' : ''">
                                <div class="flex items-start gap-3">
                                    <div class="mt-0.5 w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0" :class="extractionMode === 'Multi' ? 'border-blue-500 bg-blue-500' : 'border-slate-300'">
                                        <div class="w-1.5 h-1.5 rounded-full bg-white" v-if="extractionMode === 'Multi'"></div>
                                    </div>
                                    <div>
                                        <span class="block font-bold text-slate-800 text-sm">全面提取 (Multi)</span>
                                        <span class="block text-xs text-slate-500 mt-0.5">提取所有符合条件的数据点</span>
                                    </div>
                                </div>
                                <input type="radio" v-model="extractionMode" value="Multi" class="hidden">
                            </label>
                            <label class="flex p-4 border border-slate-200 rounded-lg cursor-pointer hover:border-blue-300 transition-all" :class="extractionMode === 'Single' ? 'border-blue-500 bg-blue-50/30 ring-1 ring-blue-500' : ''">
                                <div class="flex items-start gap-3">
                                    <div class="mt-0.5 w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0" :class="extractionMode === 'Single' ? 'border-blue-500 bg-blue-500' : 'border-slate-300'">
                                        <div class="w-1.5 h-1.5 rounded-full bg-white" v-if="extractionMode === 'Single'"></div>
                                    </div>
                                    <div>
                                        <span class="block font-bold text-slate-800 text-sm">精准提取 (Single)</span>
                                        <span class="block text-xs text-slate-500 mt-0.5">仅提取最佳匹配的唯一值</span>
                                    </div>
                                </div>
                                <input type="radio" v-model="extractionMode" value="Single" class="hidden">
                            </label>
                        </div>
                    </div>

                    <!-- Advanced Options -->
                    <div class="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                        <label class="block text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
                            高级选项
                        </label>
                        <div class="flex gap-8">
                            <label class="flex items-center gap-2 cursor-pointer group">
                                <div class="relative">
                                    <input type="checkbox" v-model="liteMode" class="sr-only peer">
                                    <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                                </div>
                                <span class="text-sm font-medium text-slate-700">节省 Token</span>
                            </label>
                            <label class="flex items-center gap-2 cursor-pointer group">
                                <div class="relative">
                                    <input type="checkbox" v-model="handleExceptions" class="sr-only peer">
                                    <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                                </div>
                                <span class="text-sm font-medium text-slate-700">异常值标记</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 5: Results -->
        <div v-if="currentStep === 5" class="flex-1 p-0 overflow-hidden flex flex-col animate-fade-in relative">
            <div v-if="extracting" class="absolute inset-0 z-20 bg-white/95 backdrop-blur-sm flex flex-col items-center justify-center">
                <div class="relative">
                    <div class="w-20 h-20 border-4 border-blue-100 rounded-full animate-spin"></div>
                    <div class="absolute top-0 left-0 w-20 h-20 border-4 border-t-blue-600 rounded-full animate-spin"></div>
                    <div class="absolute inset-0 flex items-center justify-center">
                        <span class="text-2xl animate-pulse">🤖</span>
                    </div>
                </div>
                <h3 class="text-lg font-bold text-slate-800 mt-6 mb-2">AI 深度分析中...</h3>
                <p class="text-slate-500 animate-pulse text-sm">正在提取 {{ selectedIndicators.length }} 个关键指标</p>
            </div>

            <div class="p-4 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm shrink-0">
                <div>
                    <h3 class="text-lg font-bold text-slate-800">提取结果概览</h3>
                    <p class="text-xs text-slate-500 mt-0.5">共发现 {{ results.length }} 个数据点</p>
                </div>
                <div class="flex gap-2">
                    <button class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:text-blue-600 hover:border-blue-200 transition-all shadow-sm flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                        导出Excel
                    </button>
                    <button class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors shadow-md shadow-blue-600/20 flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        生成报告
                    </button>
                </div>
            </div>

            <div class="flex-1 overflow-auto p-6 custom-scrollbar bg-slate-50/50">
                <div v-if="results.length > 0" class="grid grid-cols-1 gap-4">
                    <div v-for="(res, idx) in results" :key="idx" class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group">
                        <div class="bg-slate-50 px-5 py-3 border-b border-slate-100 flex justify-between items-center">
                            <div class="flex items-center gap-3">
                                <span class="w-1.5 h-6 rounded-full" :class="res.status === 'success' ? 'bg-green-500' : 'bg-red-500'"></span>
                                <span class="font-bold text-slate-800 text-sm">{{ res.indicator_name }}</span>
                            </div>
                            <span class="text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1" :class="res.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
                                <span class="w-1 h-1 rounded-full" :class="res.status === 'success' ? 'bg-green-600' : 'bg-red-600'"></span>
                                {{ res.status === 'success' ? '成功' : '失败' }}
                            </span>
                        </div>
                        <div class="p-5 overflow-x-auto bg-white">
                            <pre class="text-xs font-mono text-slate-600 whitespace-pre-wrap leading-relaxed">{{ res.content }}</pre>
                        </div>
                    </div>
                </div>
                <div v-else-if="!extracting" class="h-full flex flex-col items-center justify-center text-slate-400">
                    <div class="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                         <svg class="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                    </div>
                    <p class="text-base font-medium text-slate-500">暂无结果</p>
                    <p class="text-xs mt-1">请配置参数并开始提取</p>
                </div>
            </div>
        </div>

        <!-- Footer Buttons (Fixed at bottom right) -->
        <div class="p-4 border-t border-slate-100 bg-white flex justify-between items-center shrink-0 z-20">
             <button 
                @click="currentStep--" 
                :disabled="currentStep === 1 || extracting"
                class="px-6 py-2.5 rounded-lg font-bold transition-all flex items-center gap-2 text-sm"
                :class="currentStep === 1 ? 'text-slate-300 cursor-not-allowed' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
             >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                上一步
             </button>
             
             <div class="flex gap-3">
                 <button 
                    v-if="currentStep < 5"
                    @click="nextStep"
                    :disabled="!canProceed"
                    class="px-8 py-2.5 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 shadow-md shadow-blue-600/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transition-all hover:scale-105 active:scale-95 flex items-center gap-2 text-sm"
                 >
                    {{ currentStep === 4 ? '开始提取' : '下一步' }}
                    <svg v-if="currentStep < 4" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                    <svg v-if="currentStep === 4" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                 </button>
                 <button 
                    v-if="currentStep === 5"
                    @click="reset"
                    class="px-6 py-2.5 bg-slate-100 text-slate-700 rounded-lg font-bold hover:bg-slate-200 transition-all flex items-center gap-2 text-sm"
                 >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    重新开始
                 </button>
             </div>
        </div>
    </div>

    <!-- Indicator Modal -->
    <a-modal
        v-model:open="showIndicatorModal"
        :title="null"
        :footer="null"
        width="800px"
        destroyOnClose
        centered
        :maskClosable="false"
        class="custom-modal"
    >
        <div class="relative">
             <div class="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-t-lg"></div>
             <div class="p-6">
                <h3 class="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <span class="w-1 h-6 bg-blue-600 rounded-full"></span>
                    {{ editingIndicator ? '编辑指标' : '新建指标' }}
                </h3>
                <IndicatorForm 
                    :initialData="editingIndicator" 
                    :isEdit="!!editingIndicator"
                    @submit="handleIndicatorSubmit"
                    @cancel="showIndicatorModal = false"
                />
            </div>
        </div>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, defineAsyncComponent } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue';

const IndicatorForm = defineAsyncComponent(() => import('./IndicatorForm.vue'));

const api = axios.create({ baseURL: '/api/v1' });

const props = defineProps({
    prefilledIndicator: Object
});

// State
const currentStep = ref(1);
const extracting = ref(false);
const results = ref([]);

// Step 1: Data Source
const sourceType = ref('recording');
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
        message.error('获取内容失败');
    }
};

const handleKbFileChange = async () => {
    if (!selectedKbFileId.value) return;
    try {
        const res = await api.get(`/knowledge/${selectedKbFileId.value}/content`);
        textContent.value = res.data.content || "无内容";
    } catch (e) {
        message.error('获取内容失败');
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
        message.success('解析成功');
    } catch (e) {
        message.error('解析失败');
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
            message.success('更新成功');
        } else {
            await api.post('/indicators/', payload);
            message.success('创建成功');
        }
        showIndicatorModal.value = false;
        fetchIndicators();
    } catch (e) {
        message.error('保存失败');
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
        message.success('提取任务完成');
    } catch (e) {
        message.error('提取过程发生错误');
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