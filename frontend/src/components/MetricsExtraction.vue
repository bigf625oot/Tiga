<template>
  <div class="max-w-[1400px] mx-auto p-4 flex flex-col lg:flex-row gap-6 h-[calc(100vh-140px)]">
    <!-- Left Panel: Definition & Preview -->
    <div class="w-full lg:w-1/3 flex flex-col gap-5 h-full pr-2 overflow-y-auto">
        
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm shrink-0">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <span class="w-1 h-5 bg-blue-600 rounded-full"></span>
                指标定义
            </h3>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">指标名称</label>
                    <input v-model="form.indicator_name" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="例如：营业收入">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">指标别名 (可选)</label>
                    <input v-model="form.aliases" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="例如：营收, 销售额">
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">指标定义</label>
                    <textarea v-model="form.definition" rows="4" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none resize-none text-sm" placeholder="详细描述该指标的定义、计算方式或口径..."></textarea>
                    
                    <div class="mt-3 flex justify-between items-center">
                        <label class="flex items-center gap-2 cursor-pointer select-none">
                            <input type="checkbox" v-model="form.lite_mode" class="rounded text-blue-600 focus:ring-blue-500 border-slate-300">
                            <span class="text-xs text-slate-600">节省 Token 模式</span>
                        </label>
                        <button 
                            @click="showAdvancedModal = true" 
                            class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium transition-colors"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                            高级条件设置
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Prompt Preview Block -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex-1 flex flex-col min-h-[300px]">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-bold text-slate-800 flex items-center gap-2">
                    <span class="w-1 h-5 bg-indigo-500 rounded-full"></span>
                    Prompt 预览
                </h3>
                <button 
                    @click="showPromptModal = true" 
                    class="text-slate-400 hover:text-blue-600 p-1.5 hover:bg-slate-100 rounded-lg transition-all"
                    title="最大化预览"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
                </button>
            </div>
            <div class="flex-1 relative">
                <textarea 
                    readonly 
                    :value="promptPreview"
                    class="w-full h-full absolute inset-0 p-3 border border-slate-300 rounded-lg bg-slate-50 text-xs font-mono text-slate-600 resize-none outline-none focus:ring-2 focus:ring-blue-200"
                    placeholder="完善指标定义后自动生成 Prompt 预览..."
                ></textarea>
            </div>
        </div>

    </div>

    <!-- Right Panel: Wizard Steps -->
    <div class="w-full lg:w-2/3 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        
        <!-- Steps Header -->
        <div class="p-6 border-b border-slate-100">
             <div class="flex items-center justify-between">
                 <div v-for="step in 4" :key="step" class="flex flex-col items-center relative z-10 w-1/4">
                     <div 
                        class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm font-din transition-all duration-300 border-2"
                        :class="currentStep >= step ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-slate-300 text-slate-400'"
                     >
                        {{ step }}
                     </div>
                     <span class="text-xs mt-2 font-medium" :class="currentStep >= step ? 'text-blue-600' : 'text-slate-400'">
                        {{ ['数据来源', '模型设置', '提取配置', '提取结果'][step-1] }}
                     </span>
                 </div>
             </div>
        </div>

        <!-- Step Content Area -->
        <div class="flex-1 p-6 overflow-y-auto relative">
            
            <!-- Step 1: Data Source -->
            <div v-if="currentStep === 1" class="space-y-6 animate-fade-in">
                <h3 class="text-lg font-bold text-slate-800">选择数据来源</h3>
                
                <div class="flex bg-slate-100 p-1 rounded-lg w-fit">
                    <button 
                        @click="sourceType = 'recording'"
                        class="px-4 py-2 text-sm font-medium rounded-md transition-all"
                        :class="sourceType === 'recording' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                    >
                        选择录音文件
                    </button>
                    <button 
                        @click="sourceType = 'upload'"
                        class="px-4 py-2 text-sm font-medium rounded-md transition-all"
                        :class="sourceType === 'upload' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                    >
                        上传文档
                    </button>
                </div>
                
                <div v-if="sourceType === 'recording'" class="space-y-4">
                    <label class="block text-sm font-medium text-slate-700">选择已转写文件</label>
                    <div class="relative">
                        <!-- Invisible Overlay for closing -->
                        <div v-if="showFileDropdown" class="fixed inset-0 z-10 cursor-default" @click="showFileDropdown = false"></div>
                        
                        <!-- Trigger -->
                        <div 
                            @click="showFileDropdown = !showFileDropdown"
                            class="relative z-20 w-full px-4 py-3 border border-slate-300 rounded-lg bg-white flex items-center justify-between cursor-pointer hover:border-blue-400 transition-all text-sm group"
                            :class="{'ring-2 ring-blue-100 border-blue-400': showFileDropdown}"
                        >
                            <span :class="selectedFileId ? 'text-slate-700 font-medium' : 'text-slate-400'">
                                {{ selectedFileName || '-- 请选择已转写的文件 --' }}
                            </span>
                            
                            <div class="flex items-center gap-2">
                                <button 
                                    v-if="selectedFileId" 
                                    @click.stop="clearFileSelection"
                                    class="p-1 rounded-full hover:bg-slate-100 text-slate-400 hover:text-red-500 transition-colors z-30"
                                    title="清除选择"
                                >
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                </button>
                                <svg class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-transform duration-200" :class="{'rotate-180': showFileDropdown}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>
                        
                        <!-- Dropdown Menu -->
                        <div 
                            v-if="showFileDropdown" 
                            class="absolute z-30 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl max-h-64 overflow-y-auto py-2 animate-fade-in-up origin-top"
                        >
                            <div 
                                @click="clearFileSelection"
                                class="px-4 py-3 text-sm hover:bg-slate-50 cursor-pointer text-slate-500 border-b border-slate-100 flex items-center gap-2 transition-colors"
                            >
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>
                                <span>不选择任何文件</span>
                            </div>
                            
                            <div v-if="files.length === 0" class="px-4 py-8 text-center flex flex-col items-center text-slate-400">
                                <svg class="w-8 h-8 mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                <span class="text-xs">暂无可用文件</span>
                            </div>
                            <div 
                                v-for="file in files" 
                                :key="file.id"
                                @click="selectFile(file)"
                                class="px-4 py-3 text-sm hover:bg-blue-50 cursor-pointer flex justify-between items-center group transition-colors border-b border-slate-50 last:border-0"
                                :class="selectedFileId === file.id ? 'bg-blue-50/60' : ''"
                            >
                                <div class="flex flex-col overflow-hidden mr-3">
                                    <span class="truncate font-medium" :class="selectedFileId === file.id ? 'text-blue-600' : 'text-slate-700'">{{ file.filename }}</span>
                                    <span class="text-xs text-slate-400 mt-0.5 font-din">{{ formatDate(file.created_at) }}</span>
                                </div>
                                <span class="text-xs font-din px-2 py-1 bg-slate-100 rounded text-slate-500 group-hover:bg-white group-hover:text-blue-500 transition-colors whitespace-nowrap">{{ file.duration }}s</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div v-else class="space-y-4">
                    <label class="block text-sm font-medium text-slate-700">上传本地文档</label>
                    <div 
                        @click="triggerDocUpload"
                        class="border-2 border-dashed border-slate-200 rounded-xl p-10 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 transition-all group"
                    >
                        <input type="file" ref="docInput" class="hidden" accept=".pdf,.docx,.doc,.txt" @change="handleDocUpload">
                        <div v-if="uploading">
                            <svg class="animate-spin h-8 w-8 text-blue-500 mx-auto mb-3" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            <span class="text-slate-500">正在解析...</span>
                        </div>
                        <div v-else>
                            <svg class="w-10 h-10 text-slate-300 group-hover:text-blue-400 mx-auto mb-3 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
                            <p class="text-slate-600 font-medium">点击上传 PDF/Word/TXT</p>
                        </div>
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-2">文本预览</label>
                    <textarea 
                        v-model="form.text_content" 
                        rows="8" 
                        class="w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 text-slate-600 text-xs resize-none font-mono focus:bg-white focus:ring-2 focus:ring-blue-200 outline-none transition-all"
                        :placeholder="sourceType === 'recording' ? '选择文件后显示...' : '上传文档后显示...'"
                    ></textarea>
                    
                    <!-- Long Text Warning -->
                    <div v-if="form.text_content && form.text_content.length > 30000" class="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm flex items-start gap-3 animate-fade-in">
                        <svg class="w-5 h-5 shrink-0 mt-0.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        <div>
                            <p class="font-bold text-amber-900">检测到超长文档 (<span class="font-din">{{ (form.text_content.length / 1000).toFixed(1) }}</span>k 字符)</p>
                            <p class="mt-1 text-xs text-amber-700 leading-relaxed">
                                文档长度超过单次处理建议阈值。为确保提取完整性：<br>
                                1. 建议在下一步选择 <strong>Qwen-Long</strong> 模型（支持超长上下文）。<br>
                                2. 如果选择其他模型，系统将自动启用<strong>分块并行处理 (Map-Reduce)</strong>，这可能会消耗更多时间并产生多个结果片段。
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Step 2: Model Settings -->
            <div v-if="currentStep === 2" class="space-y-6 animate-fade-in">
                <h3 class="text-lg font-bold text-slate-800">选择大模型</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div 
                        v-for="model in ['qwen-plus', 'qwen-max', 'qwen-turbo', 'qwen-long']" 
                        :key="model"
                        @click="form.model = model"
                        class="p-4 border rounded-xl cursor-pointer transition-all hover:shadow-md"
                        :class="form.model === model ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-slate-200 hover:border-blue-300'"
                    >
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-bold text-slate-800">{{ model }}</span>
                            <div v-if="form.model === model" class="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center">
                                <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                            </div>
                        </div>
                        <p class="text-xs text-slate-500">
                            {{ model === 'qwen-plus' ? '均衡推荐，性价比高' : 
                               model === 'qwen-max' ? '最强性能，适合复杂逻辑' : 
                               model === 'qwen-turbo' ? '极速响应，成本最低' : '适合超长文本处理' }}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Step 3: Extraction Config -->
            <div v-if="currentStep === 3" class="space-y-6 animate-fade-in">
                <h3 class="text-lg font-bold text-slate-800">文档提取设置</h3>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">输出格式 (Output Format)</label>
                        <div class="relative">
                            <div v-if="showFormatDropdown" class="fixed inset-0 z-10 cursor-default" @click="showFormatDropdown = false"></div>
                            
                            <div 
                                @click="showFormatDropdown = !showFormatDropdown"
                                class="relative z-20 w-full px-4 py-3 border border-slate-300 rounded-lg bg-white flex items-center justify-between cursor-pointer hover:border-blue-400 transition-all text-sm group"
                                :class="{'ring-2 ring-blue-100 border-blue-400': showFormatDropdown}"
                            >
                                <span class="text-slate-700 font-medium">{{ form.output_format }}</span>
                                <svg class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-transform duration-200" :class="{'rotate-180': showFormatDropdown}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            
                            <div v-if="showFormatDropdown" class="absolute z-30 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl py-2 animate-fade-in-up origin-top">
                                <div 
                                    v-for="fmt in ['JSON', 'CSV', 'Markdown Table']" 
                                    :key="fmt"
                                    @click="selectFormat(fmt)"
                                    class="px-4 py-2.5 text-sm hover:bg-blue-50 cursor-pointer flex justify-between items-center group transition-colors"
                                    :class="form.output_format === fmt ? 'bg-blue-50 text-blue-600 font-medium' : 'text-slate-700'"
                                >
                                    <span>{{ fmt }}</span>
                                    <svg v-if="form.output_format === fmt" class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">提取模式 (Extraction Mode)</label>
                        <div class="flex gap-4">
                            <label class="flex-1 p-4 border rounded-lg cursor-pointer transition-all" :class="form.extraction_mode === 'Multi' ? 'border-blue-500 bg-blue-50' : 'border-slate-200'">
                                <div class="flex items-center gap-2 mb-1">
                                    <input type="radio" v-model="form.extraction_mode" value="Multi" class="text-blue-600">
                                    <span class="font-bold text-slate-800">全部提取 (Multi)</span>
                                </div>
                                <p class="text-xs text-slate-500 pl-6">提取所有符合条件的数据点</p>
                            </label>
                            <label class="flex-1 p-4 border rounded-lg cursor-pointer transition-all" :class="form.extraction_mode === 'Single' ? 'border-blue-500 bg-blue-50' : 'border-slate-200'">
                                <div class="flex items-center gap-2 mb-1">
                                    <input type="radio" v-model="form.extraction_mode" value="Single" class="text-blue-600">
                                    <span class="font-bold text-slate-800">仅提取最佳 (Single)</span>
                                </div>
                                <p class="text-xs text-slate-500 pl-6">只提取最新或最匹配的一条</p>
                            </label>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Prompt 语言 (Language)</label>
                        <div class="flex gap-4">
                             <label class="flex items-center gap-2 cursor-pointer">
                                <input type="radio" v-model="form.language" value="CN" class="text-blue-600">
                                <span class="text-sm">中文 (Chinese)</span>
                            </label>
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input type="radio" v-model="form.language" value="EN" class="text-blue-600">
                                <span class="text-sm">英文 (English)</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Step 4: Results -->
            <div v-if="currentStep === 4" class="h-full flex flex-col animate-fade-in">
                <div class="flex justify-between items-center mb-4">
                     <h3 class="text-lg font-bold text-slate-800">提取结果</h3>
                     <div class="flex items-center gap-3">
                         <span class="text-xs px-2 py-1 bg-slate-100 rounded text-slate-500">{{ form.model }}</span>
                         <div class="flex bg-slate-100 p-1 rounded-lg">
                            <button @click="viewMode = 'json'" class="px-3 py-1 text-xs rounded-md transition-all" :class="viewMode === 'json' ? 'bg-white shadow text-blue-600' : 'text-slate-500'">JSON</button>
                            <button @click="viewMode = 'table'" class="px-3 py-1 text-xs rounded-md transition-all" :class="viewMode === 'table' ? 'bg-white shadow text-blue-600' : 'text-slate-500'">表格</button>
                            <button @click="viewMode = 'tree'" class="px-3 py-1 text-xs rounded-md transition-all" :class="viewMode === 'tree' ? 'bg-white shadow text-blue-600' : 'text-slate-500'">树状</button>
                         </div>
                     </div>
                </div>
                
                <div class="flex-1 overflow-auto border border-slate-200 rounded-xl bg-slate-50 relative p-4">
                    <div v-if="!result && !extracting" class="absolute inset-0 flex flex-col items-center justify-center text-slate-300">
                        <svg class="w-12 h-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        <span>点击下方“开始提取”查看结果</span>
                    </div>
                    
                    <div v-if="extracting" class="absolute inset-0 flex flex-col items-center justify-center bg-white/90 z-10">
                        <div class="w-16 h-16 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                        <p class="text-blue-600 font-bold animate-pulse">AI 正在思考中...</p>
                        <p class="text-xs text-slate-400 mt-2">使用模型: {{ form.model }}</p>
                    </div>

                    <div v-if="result">
                         <!-- JSON View -->
                        <pre v-if="viewMode === 'json'" class="whitespace-pre-wrap text-slate-700 font-mono text-sm">{{ result }}</pre>
                        
                        <!-- Table View -->
                        <div v-else-if="viewMode === 'table'" class="overflow-auto">
                            <table v-if="parsedResult && Array.isArray(parsedResult)" class="w-full text-sm border-collapse bg-white">
                                <thead class="bg-slate-100">
                                    <tr><th v-for="k in Object.keys(parsedResult[0]||{})" :key="k" class="p-2 border text-left">{{k}}</th></tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(row, i) in parsedResult" :key="i"><td v-for="k in Object.keys(parsedResult[0]||{})" :key="k" class="p-2 border">{{row[k]}}</td></tr>
                                </tbody>
                            </table>
                            <table v-else-if="parsedResult" class="w-full text-sm border-collapse bg-white">
                                <tbody>
                                    <tr v-for="(v, k) in parsedResult" :key="k"><td class="p-2 border bg-slate-50 font-bold w-1/3">{{k}}</td><td class="p-2 border">{{v}}</td></tr>
                                </tbody>
                            </table>
                            <div v-else class="text-center py-10 text-slate-400">无法解析表格数据</div>
                        </div>

                        <!-- Tree View -->
                        <pre v-else-if="viewMode === 'tree'" class="text-sm font-mono text-slate-700">{{ parsedResult ? JSON.stringify(parsedResult, null, 4) : '无法解析' }}</pre>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer Buttons -->
        <div class="p-6 border-t border-slate-100 bg-slate-50 flex justify-between items-center">
             <button 
                @click="currentStep--" 
                :disabled="currentStep === 1 || extracting"
                class="px-6 py-2 rounded-lg font-medium transition-all"
                :class="currentStep === 1 ? 'text-slate-300 cursor-not-allowed' : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'"
             >
                上一步
             </button>
             
             <button 
                v-if="currentStep < 3"
                @click="currentStep++"
                class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 shadow-lg shadow-blue-600/20"
             >
                下一步
             </button>
             
             <button 
                v-if="currentStep === 3"
                @click="handleExtractAndNext"
                :disabled="!form.text_content || !form.indicator_name"
                class="px-8 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 shadow-lg shadow-green-600/20 disabled:opacity-50 disabled:cursor-not-allowed"
             >
                开始智能提取
             </button>
             
             <button 
                v-if="currentStep === 4"
                @click="handleExtract"
                :disabled="extracting"
                class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2"
             >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                重新提取
             </button>
        </div>
    </div>
  </div>

  <!-- Prompt Preview Modal -->
  <div v-if="showPromptModal" class="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col animate-fade-in-up">
        <!-- Header -->
        <div class="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
            <div>
                <h3 class="text-lg font-bold text-slate-800">Prompt 完整预览</h3>
                <p class="text-sm text-slate-500 mt-1">这是发送给大模型的最终指令内容</p>
            </div>
            <div class="flex items-center gap-3">
                <button @click="copyPrompt" class="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 hover:text-blue-600 transition-colors flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                    复制内容
                </button>
                <button @click="showPromptModal = false" class="text-slate-400 hover:text-slate-600 p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
        </div>
        
        <!-- Body -->
        <div class="flex-1 p-0 overflow-hidden relative bg-white">
            <textarea 
                readonly 
                v-model="promptPreview"
                class="w-full h-full p-6 bg-white text-slate-700 font-mono text-sm leading-relaxed resize-none outline-none border-none focus:ring-0"
            ></textarea>
        </div>
    </div>
  </div>

  <!-- Advanced Options Modal -->
  <div v-if="showAdvancedModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm transition-all">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col animate-fade-in-up">
        <!-- Header -->
        <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
            <div>
                <h3 class="text-lg font-bold text-slate-800">高级指标约束条件</h3>
                <p class="text-sm text-slate-500 mt-1">完善这些信息有助于 AI 更精准地提取数据</p>
            </div>
            <button @click="showAdvancedModal = false" class="text-slate-400 hover:text-slate-600 p-2 hover:bg-slate-100 rounded-full transition-colors">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        
        <!-- Body -->
        <div class="p-6 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Left Column -->
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">相关术语 (关联术语)</label>
                    <input v-model="advancedOptions.related_terms" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="例如：EBITDA, 净利润">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">技术特征</label>
                    <textarea v-model="advancedOptions.technical_features" rows="3" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none resize-none text-sm" placeholder="物理意义、测量方法、影响因素、工程应用等..."></textarea>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">计算公式</label>
                    <input v-model="advancedOptions.formula" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="例如：营业利润 = 营业收入 - 营业成本...">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">典型格式</label>
                    <input v-model="advancedOptions.typical_format" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="例如：百分比(%), 金额(万元)...">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">常见位置</label>
                    <input v-model="advancedOptions.common_location" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="表格中 / 段落描述 / 图注说明...">
                </div>
            </div>
            
            <!-- Right Column -->
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">文档范围</label>
                    <input v-model="advancedOptions.doc_scope" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="指定章节或全文，例如：财务报表附注...">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">默认值</label>
                    <input v-model="advancedOptions.default_value" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="若未找到时的默认填充值...">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">取值范围</label>
                    <input v-model="advancedOptions.value_range" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="单值 / 范围值 / 系列值...">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">参考范围值</label>
                    <input v-model="advancedOptions.reference_range" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-200 outline-none text-sm" placeholder="合理的数值范围，例如：0-100%...">
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="p-6 border-t border-slate-100 flex justify-end bg-slate-50 rounded-b-xl">
            <button @click="showAdvancedModal = false" class="px-6 py-2 bg-white border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 mr-3 font-medium transition-colors">取消</button>
            <button @click="showAdvancedModal = false" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 shadow-lg shadow-blue-600/20 transition-all active:scale-95">确认保存</button>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1' 
});

const files = ref([]);
const loadingFiles = ref(false);
const selectedFileId = ref(null);
const extracting = ref(false);
const result = ref('');

// Upload related
const sourceType = ref('recording'); // 'recording' | 'upload'
const uploading = ref(false);
const docInput = ref(null);

const form = reactive({
    indicator_name: '',
    aliases: '',
    definition: '',
    text_content: '',
    output_format: 'JSON',
    language: 'CN',
    extraction_mode: 'Multi',
    model: 'qwen-plus',
    lite_mode: false
});

const advancedOptions = reactive({
    related_terms: '',
    technical_features: '',
    formula: '',
    typical_format: '',
    common_location: '',
    doc_scope: '',
    default_value: '',
    value_range: '',
    reference_range: ''
});

const showAdvancedModal = ref(false);
const showPromptModal = ref(false);
const showFileDropdown = ref(false);
const showFormatDropdown = ref(false);
const viewMode = ref('json'); // 'json', 'table', 'tree'
const currentStep = ref(1);
const promptPreview = ref('');
let previewTimeout = null;

const selectedFileName = computed(() => {
    if (!selectedFileId.value) return null;
    const file = files.value.find(f => f.id === selectedFileId.value);
    return file ? `${file.filename} (${file.duration}s)` : null;
});

const selectFile = (file) => {
    selectedFileId.value = file.id;
    handleFileChange();
    showFileDropdown.value = false;
};

const clearFileSelection = () => {
    selectedFileId.value = null;
    form.text_content = '';
    showFileDropdown.value = false;
};

const selectFormat = (format) => {
    form.output_format = format;
    showFormatDropdown.value = false;
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm');
};

const copyPrompt = () => {
    if (!promptPreview.value) return;
    navigator.clipboard.writeText(promptPreview.value);
    message.success("Prompt 已复制到剪贴板");
};

const fetchPromptPreview = async () => {
    // Only fetch if minimal fields are present
    if (!form.indicator_name) return;
    
    try {
        const res = await api.post('/metrics/preview_prompt', {
            indicator_name: form.indicator_name,
            definition: form.definition,
            output_format: form.output_format,
            language: form.language,
            lite_mode: form.lite_mode,
            aliases: form.aliases,
            extraction_mode: form.extraction_mode,
            advanced_options: advancedOptions
        });
        promptPreview.value = res.data.prompt;
    } catch (e) {
        console.error(e);
    }
};

watch(
    () => [form.indicator_name, form.definition, form.aliases, form.lite_mode, form.language, form.output_format, form.extraction_mode, advancedOptions], 
    () => { 
        if (previewTimeout) clearTimeout(previewTimeout);
        previewTimeout = setTimeout(fetchPromptPreview, 500);
    }, 
    { deep: true }
);

const parsedResult = computed(() => {
    try {
        if (!result.value) return null;
        let str = result.value.trim();
        // Remove markdown code blocks if present
        if (str.startsWith('```')) {
            str = str.replace(/^```(json)?\s*/i, '').replace(/\s*```$/, '');
        }
        return JSON.parse(str);
    } catch (e) {
        return null;
    }
});

watch(sourceType, () => {
    form.text_content = '';
    selectedFileId.value = null;
    // Reset file input if exists
    if (docInput.value) {
        docInput.value.value = '';
    }
});

onMounted(async () => {
    loadingFiles.value = true;
    try {
        const res = await api.get('/recordings/');
        // Filter only files with successful transcription
        files.value = res.data.filter(f => !f.is_folder && f.asr_status === 'completed');
    } catch (e) {
        console.error(e);
    } finally {
        loadingFiles.value = false;
    }
});

const handleFileChange = async () => {
    if (!selectedFileId.value) {
        form.text_content = '';
        return;
    }
    
    // Find file content locally if available, or fetch detail
    // The list API usually doesn't return full text. We might need to fetch detail.
    try {
        const res = await api.get(`/recordings/${selectedFileId.value}`);
        form.text_content = res.data.transcription_text || "无转写内容";
    } catch (e) {
        message.error("获取文件内容失败");
    }
};

const triggerDocUpload = () => {
    if (uploading.value) return;
    docInput.value.click();
};

const handleDocUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    uploading.value = true;
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await api.post('/metrics/parse_doc', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        
        if (res.data.text) {
            form.text_content = res.data.text;
            message.success(`已加载文档: ${res.data.filename}`);
        } else {
            message.warning("解析成功但没有提取到文本");
        }
    } catch (e) {
        console.error(e);
        message.error(e.response?.data?.detail || "文档解析失败");
    } finally {
        uploading.value = false;
        // Reset input value to allow re-uploading same file
        event.target.value = '';
    }
};

const handleExtractAndNext = async () => {
    currentStep.value = 4;
    await handleExtract();
};

const handleExtract = async () => {
    extracting.value = true;
    result.value = '';
    
    try {
        const res = await api.post('/metrics/extract', {
            indicator_name: form.indicator_name,
            definition: form.definition,
            text_content: form.text_content,
            aliases: form.aliases,
            output_format: form.output_format,
            language: form.language,
            extraction_mode: form.extraction_mode,
            advanced_options: advancedOptions,
            model: form.model
        });
        
        if (res.data.status === 'success') {
            result.value = res.data.content;
            message.success("提取完成");
        } else {
            result.value = res.data.content; // Show error message
            message.error("提取遇到问题");
        }
    } catch (e) {
        message.error("请求失败");
        console.error(e);
    } finally {
        extracting.value = false;
    }
};
</script>
