<template>
    <div class="h-full flex flex-col bg-white overflow-y-auto p-8">
        <div class="max-w-[1200px] mx-auto w-full flex flex-col gap-8">
            <h2 class="text-xl font-bold text-[#171717]">智能体</h2>

            <Loading v-if="isLoading" type="skeleton-card" />

            <template v-else>
                <!-- Section: My Agents -->
                <div class="flex flex-col gap-6">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-semibold text-[#171717]">我的智能体</span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        <!-- Create Card -->
                        <div 
                            @click="openCreateModal"
                            class="bg-[#f9fafb] rounded-2xl h-[160px] flex items-center justify-center cursor-pointer hover:shadow-md transition-all group"
                        >
                            <div class="flex items-center gap-4">
                                <div class="w-[54px] h-[54px] rounded-full bg-white flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform">
                                    <svg class="w-6 h-6 text-[#171717]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                </div>
                                <span class="text-sm font-medium text-[#171717]">创建智能体</span>
                            </div>
                        </div>

                        <!-- User Agents -->
                        <div 
                            v-for="agent in myAgents" 
                            :key="agent.id"
                            class="bg-[#f9fafb] rounded-2xl p-4 h-[160px] flex flex-col justify-between hover:shadow-md transition-all relative group cursor-pointer"
                            @click="editAgent(agent)"
                        >
                            <div class="flex items-start justify-between">
                                <div class="flex items-center gap-3">
                                    <div class="w-10 h-10 rounded-full bg-white flex items-center justify-center text-lg font-bold text-[#171717] shadow-sm overflow-hidden border border-slate-100">
                                        <img v-if="isImageIcon(agent.icon)" :src="agent.icon" class="w-full h-full object-cover" />
                                        <component v-else :is="agent.iconComponent" class="w-5 h-5 text-slate-700" />
                                    </div>
                                    <span class="font-medium text-[#171717] truncate max-w-[120px]">{{ agent.name }}</span>
                                </div>
                                <!-- Delete Action -->
                                <button 
                                    @click.stop="deleteAgent(agent)" 
                                    class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-500 transition-opacity"
                                >
                                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                </button>
                            </div>
                            <p class="text-xs text-[#858b9b] line-clamp-2 leading-relaxed">
                                {{ agent.description || '暂无描述...' }}
                            </p>
                        </div>

                        <!-- Empty State (Only shown when myAgents is empty) -->
                        <div v-if="myAgents.length === 0" class="col-span-full py-8 flex flex-col items-center justify-center text-center">
                            <div class="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                                <svg class="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                            </div>
                            <p class="text-slate-500 text-sm font-medium">暂无智能体</p>
                            <p class="text-slate-400 text-xs mt-1">点击上方“创建智能体”开始构建您的专属AI助手</p>
                        </div>
                    </div>
                </div>

                <!-- Section: Discover -->
                <div class="flex flex-col gap-6">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-semibold text-[#171717]">发现</span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        <div 
                            v-for="(agent, index) in discoverAgents" 
                            :key="index"
                            class="bg-[#f9fafb] rounded-2xl p-4 h-[160px] flex flex-col justify-between hover:shadow-md transition-all cursor-pointer relative group"
                            @click="editAgent(agent)"
                        >
                            <div class="flex items-start justify-between">
                                <div class="flex items-center gap-3">
                                    <div 
                                        class="w-[46px] h-[46px] rounded-[20px] flex items-center justify-center shadow-sm border border-slate-100 overflow-hidden"
                                        :class="agent.is_template ? 'bg-transparent' : 'bg-white'"
                                    >
                                        <img src="/tiga.svg" class="w-8 h-8 object-contain" />
                                    </div>
                                    <span class="font-medium text-[#171717]">{{ agent.name }}</span>
                                </div>
                                <!-- Delete Action -->
                                <button 
                                    @click.stop="deleteAgent(agent)" 
                                    class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-500 transition-opacity"
                                >
                                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                </button>
                            </div>
                            <p class="text-xs text-[#858b9b] line-clamp-2 leading-relaxed mt-2">
                                {{ agent.description }}
                            </p>
                        </div>
                    </div>
                </div>
            </template>

        </div>

        <!-- Create/Edit Modal (Reused Logic) -->
        <div v-if="showModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-end">
            <div class="w-[600px] h-full bg-white shadow-2xl flex flex-col animate-slide-in-right">
                <!-- Modal Header -->
                <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-white">
                    <h3 class="text-lg font-bold text-slate-800">{{ isEditing ? '编辑智能体' : '新建智能体' }}</h3>
                    <button @click="closeModal" class="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>

                <!-- Modal Body -->
                <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
                    
                    <!-- Basic Info -->
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                        <div class="flex items-center gap-2 mb-3 text-slate-800 font-medium">
                            <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                            智能体基础信息
                        </div>
                        <div class="space-y-3">
                            <div>
                                <label class="block text-xs font-medium text-slate-500 mb-1">智能体名称</label>
                                <input v-model="form.name" type="text" class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="请输入智能体名称">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-slate-500 mb-1">智能体简介</label>
                                <textarea v-model="form.description" rows="2" class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none" placeholder="请描述智能体的功能和用途..."></textarea>
                            </div>
                            
                            <!-- Icon Upload -->
                            <div>
                                <label class="block text-xs font-medium text-slate-500 mb-1">智能体图标</label>
                                <div class="flex items-center gap-4">
                                    <div 
                                        class="w-12 h-12 rounded-xl border border-slate-200 flex items-center justify-center overflow-hidden bg-slate-50 relative group cursor-pointer"
                                        @click="triggerIconUpload"
                                    >
                                        <img v-if="isImageIcon(form.icon)" :src="form.icon" class="w-full h-full object-cover" />
                                        <img v-else-if="!form.icon" src="/tiga.svg" class="w-6 h-6 object-contain" />
                                        <component v-else :is="getIconComponent(form.icon)" class="w-6 h-6 text-slate-400" />
                                        
                                        <!-- Hover Overlay -->
                                        <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                        </div>
                                    </div>
                                    <div class="flex-1">
                                        <div class="text-xs text-slate-500 mb-1">建议尺寸 128x128px，支持 PNG, JPG</div>
                                        <button @click="triggerIconUpload" class="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-50 text-slate-600 transition-colors">
                                            上传图片
                                        </button>
                                        <input type="file" ref="iconInput" class="hidden" accept="image/*" @change="handleIconUpload">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- System Prompt -->
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-2 cursor-pointer" @click="toggleSection('prompt')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                                系统提示 (System Prompt)
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.prompt ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.prompt" class="space-y-2">
                             <textarea v-model="form.system_prompt" rows="5" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono text-slate-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="You are a helpful assistant..."></textarea>
                        </div>
                    </div>

                    <!-- Model Selection -->
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-2 cursor-pointer" @click="toggleSection('model')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                模型配置
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.model ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.model" class="space-y-3">
                            <!-- Custom Dropdown Trigger -->
                            <div class="relative">
                                <div 
                                    @click.stop="showModelDropdown = !showModelDropdown"
                                    class="relative z-20 w-full px-3 py-2 border border-slate-300 rounded-lg bg-white flex items-center justify-between cursor-pointer hover:border-blue-400 transition-all text-sm group"
                                    :class="{'ring-2 ring-blue-100 border-blue-400': showModelDropdown}"
                                >
                                    <div class="flex items-center gap-2">
                                        <div v-if="getSelectedModel()" class="w-2 h-2 rounded-full bg-green-500"></div>
                                        <span :class="form.model_config.model_id ? 'text-slate-700 font-medium' : 'text-slate-400'">
                                            {{ getSelectedModel()?.name || '不选择模型 (使用默认)' }}
                                        </span>
                                        <span v-if="getSelectedModel()" class="text-xs text-slate-400 ml-1">
                                            ({{ getSelectedModel()?.provider }})
                                        </span>
                                    </div>
                                    <svg class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-transform duration-200" :class="{'rotate-180': showModelDropdown}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                </div>

                                <!-- Invisible Overlay -->
                                <div v-if="showModelDropdown" class="fixed inset-0 z-10 cursor-default" @click="showModelDropdown = false"></div>

                                <!-- Dropdown Menu -->
                                <div v-if="showModelDropdown" class="absolute z-30 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl max-h-64 overflow-y-auto py-2 animate-fade-in-up origin-top">
                                    <div 
                                        @click="selectModel(null)"
                                        class="px-4 py-3 text-sm hover:bg-slate-50 cursor-pointer text-slate-500 border-b border-slate-100 flex items-center gap-2 transition-colors"
                                    >
                                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                        <span>不选择模型</span>
                                    </div>
                                    
                                    <div 
                                        v-for="m in availableModels" 
                                        :key="m.model_id" 
                                        @click="selectModel(m)"
                                        class="px-4 py-3 text-sm hover:bg-blue-50 cursor-pointer flex justify-between items-center group transition-colors border-b border-slate-50 last:border-0"
                                        :class="form.model_config.model_id === m.model_id ? 'bg-blue-50/60' : ''"
                                    >
                                        <div class="flex flex-col">
                                            <span class="font-medium" :class="form.model_config.model_id === m.model_id ? 'text-blue-600' : 'text-slate-700'">{{ m.name }}</span>
                                            <span class="text-xs text-slate-400 mt-0.5">{{ m.provider }} · {{ m.model_type }}</span>
                                        </div>
                                        <svg v-if="form.model_config.model_id === m.model_id" class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                    </div>
                                </div>
                            </div>
                             <div class="flex items-center justify-between">
                                 <span class="text-sm text-slate-600">启用推理模式 (Reasoning)</span>
                                 <button 
                                    @click="form.model_config.reasoning = !form.model_config.reasoning"
                                    class="w-10 h-5 rounded-full transition-colors relative"
                                    :class="form.model_config.reasoning ? 'bg-blue-600' : 'bg-slate-200'"
                                 >
                                    <span class="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform" :class="form.model_config.reasoning ? 'translate-x-5' : ''"></span>
                                 </button>
                             </div>
                        </div>
                    </div>
                    
                    <!-- Knowledge Base Selection -->
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-2 cursor-pointer" @click="toggleSection('knowledge')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                                知识库配置
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.knowledge ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.knowledge" class="space-y-2">
                            <div v-if="knowledgeBases.length === 0" class="text-xs text-slate-400 py-2">暂无可用知识库</div>
                            <div class="flex items-center justify-between px-3 py-2 border border-slate-200 rounded-lg">
                                <span class="text-sm text-slate-700">仅检索绑定文档</span>
                                <button 
                                    @click="form.knowledge_config.strict_only = !form.knowledge_config.strict_only"
                                    class="w-8 h-4 rounded-full transition-colors relative"
                                    :class="form.knowledge_config.strict_only ? 'bg-blue-600' : 'bg-slate-200'"
                                >
                                    <span class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform" :class="form.knowledge_config.strict_only ? 'translate-x-4' : ''"></span>
                                </button>
                            </div>
                            <div v-for="kb in knowledgeBases" :key="kb.id" class="flex items-center gap-3 p-2 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50">
                                <input type="checkbox" :value="kb.id" v-model="form.knowledge_config.document_ids" class="rounded text-blue-600 focus:ring-blue-500">
                                <div class="flex-1">
                                    <div class="text-sm font-medium text-slate-700">{{ kb.filename }}</div>
                                    <div class="text-xs text-slate-400">{{ formatSize(kb.file_size) }}</div>
                                </div>
                            </div>
                            <div class="text-[10px] text-slate-500 px-1">严格模式将只在绑定文档内检索；关闭时可在全局知识库中召回，低置信度结果将按阈值过滤。</div>
                        </div>
                    </div>

                    <!-- Tools Selection -->
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-2 cursor-pointer" @click="toggleSection('tools')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                                默认工具
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.tools ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.tools" class="space-y-2">
                            <label class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                                <input type="checkbox" value="duckduckgo" v-model="form.tools_config" class="rounded text-blue-600 focus:ring-blue-500">
                                <div>
                                    <div class="text-sm font-medium text-slate-700">DuckDuckGo Search</div>
                                    <div class="text-xs text-slate-400">网络搜索工具，支持实时信息检索</div>
                                </div>
                            </label>
                            <label class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                                <input type="checkbox" value="calculator" v-model="form.tools_config" class="rounded text-blue-600 focus:ring-blue-500">
                                <div>
                                    <div class="text-sm font-medium text-slate-700">Calculator</div>
                                    <div class="text-xs text-slate-400">数学计算工具，支持复杂运算</div>
                                </div>
                            </label>
                            <label class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                                <input type="checkbox" value="n8n" v-model="form.tools_config" class="rounded text-blue-600 focus:ring-blue-500">
                                <div>
                                    <div class="text-sm font-medium text-slate-700">N8N Workflow</div>
                                    <div class="text-xs text-slate-400">工作流自动化，连接外部服务</div>
                                </div>
                            </label>

                            <!-- Selected Market Skills -->
                            <div v-if="form.tools_config.some(t => typeof t === 'object')" class="border-t border-slate-100 pt-2 mt-2">
                                <label class="block text-xs font-medium text-slate-500 mb-2">已添加的技能组件</label>
                                <div class="space-y-2">
                                    <div v-for="(tool, idx) in form.tools_config.filter(t => typeof t === 'object')" :key="idx" class="flex items-center justify-between p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm group">
                                        <div class="flex items-center gap-2">
                                            <svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                            <span class="font-medium text-slate-700">{{ tool.name }}</span>
                                            <span class="text-xs text-slate-400 bg-white px-1.5 rounded border border-slate-100">v{{ tool.version || '1.0' }}</span>
                                        </div>
                                        <button @click="removeSkill(tool)" class="text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <button @click="openToolSelector('skill')" class="w-full py-1.5 border border-dashed border-blue-300 rounded-lg text-blue-600 hover:bg-blue-50 transition-colors text-sm flex items-center justify-center gap-1 mt-2">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                                添加更多技能
                            </button>
                        </div>
                    </div>

                    <!-- MCP Config -->
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-2 cursor-pointer" @click="toggleSection('mcp')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                MCP 服务配置
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.mcp ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.mcp" class="space-y-3">
                            <div v-if="form.mcp_config.length === 0" class="text-center py-4 bg-slate-50 rounded-lg border border-dashed border-slate-200">
                                <p class="text-xs text-slate-400">暂未配置 MCP 服务</p>
                            </div>
                            <div v-for="(mcp, idx) in form.mcp_config" :key="idx" class="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-all group">
                                <!-- Header: Name & Actions -->
                                <div class="bg-slate-50/80 px-4 py-2.5 border-b border-slate-100 flex items-center justify-between">
                                    <div class="flex items-center gap-3 flex-1">
                                        <div class="flex items-center justify-center w-6 h-6 rounded-md" :class="mcp.type === 'sse' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'">
                                            <svg v-if="mcp.type === 'sse'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                            <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                                        </div>
                                        <input 
                                            v-model="mcp.name" 
                                            class="bg-transparent font-semibold text-sm text-slate-700 focus:outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 px-2 py-0.5 rounded transition-all w-48 placeholder-slate-400" 
                                            placeholder="服务名称 (e.g. filesystem)"
                                        >
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <select v-model="mcp.type" class="text-xs bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-600 focus:border-blue-500 outline-none cursor-pointer">
                                            <option value="stdio">stdio</option>
                                            <option value="sse">sse</option>
                                        </select>
                                        <button 
                                            @click="removeMcp(idx)" 
                                            class="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                                            title="移除服务"
                                        >
                                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                        </button>
                                    </div>
                                </div>

                                <!-- Body: Config -->
                                <div class="p-4 space-y-3">
                                    <div class="space-y-1">
                                        <div class="flex justify-between">
                                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Command / URL</label>
                                        </div>
                                        <div class="relative">
                                            <input 
                                                v-model="mcp.command" 
                                                class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono text-slate-600 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" 
                                                placeholder="输入命令或 SSE URL..."
                                            >
                                        </div>
                                    </div>
                                    
                                    <div class="space-y-1">
                                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Arguments (JSON Array)</label>
                                        <textarea 
                                            v-model="mcp.args" 
                                            rows="1" 
                                            class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono text-slate-600 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none" 
                                            placeholder="['--arg1', 'value']"
                                        ></textarea>
                                    </div>
                                </div>

                                <!-- Footer: Tools Action -->
                                <div class="px-4 py-2 bg-slate-50/50 border-t border-slate-100 flex justify-between items-center">
                                    <div class="flex items-center gap-1.5">
                                        <div class="w-1.5 h-1.5 rounded-full bg-slate-300"></div>
                                        <span class="text-[10px] text-slate-400">尚未连接验证</span>
                                    </div>
                                    <button 
                                        @click="viewMcpTools(mcp)" 
                                        class="text-xs font-medium text-teal-600 hover:text-teal-700 hover:bg-teal-50 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
                                        title="连接并查看工具"
                                    >
                                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                                        查看工具列表
                                    </button>
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <button @click="addMcp" class="flex-1 py-1.5 border border-dashed border-slate-300 rounded-lg text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm flex items-center justify-center gap-1">
                                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    手动添加
                                </button>
                                <button @click="openToolSelector('mcp')" class="flex-1 py-1.5 border border-dashed border-purple-300 rounded-lg text-purple-600 hover:bg-purple-50 transition-colors text-sm flex items-center justify-center gap-1">
                                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                                    从市场选择
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-pink-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                                用户剧本
                            </div>
                        </div>
                        <UserScriptsEditor v-if="activeAgentId" :agentId="activeAgentId" />
                        <div v-else class="text-center py-6 text-slate-400 text-sm bg-slate-50 rounded-lg border border-dashed border-slate-200">
                            请先保存智能体，再配置用户剧本
                        </div>
                    </div>
                </div>

                <!-- Modal Footer -->
                <div class="px-6 py-4 border-t border-slate-200 bg-white flex justify-between items-center">
                    <div class="flex gap-2">
                        <button @click="exportConfig" class="px-3 py-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg text-sm transition-colors flex items-center gap-1" title="导出配置">
                             <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                             导出
                        </button>
                        <button @click="triggerImport" class="px-3 py-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg text-sm transition-colors flex items-center gap-1" title="导入配置">
                             <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                             导入
                        </button>
                        <input type="file" ref="importInput" class="hidden" accept=".json" @change="handleImportConfig">
                    </div>
                    <div class="flex gap-3">
                        <button @click="closeModal" class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors">取消</button>
                        <button @click="saveAgent" class="px-6 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm" :disabled="isSaving">
                            <span v-if="isSaving">保存中...</span>
                            <span v-else>保存配置</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tools List Modal -->
        <div v-if="showToolsModal" class="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
            <div class="bg-white rounded-xl shadow-2xl w-[600px] max-w-[90vw] max-h-[80vh] flex flex-col overflow-hidden" @click.stop>
                <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                    <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2">
                        <svg class="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                        {{ currentMcpName }} 工具列表
                    </h3>
                    <button @click="showToolsModal = false" class="text-slate-400 hover:text-slate-600"><svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
                </div>
                
                <div class="flex-1 overflow-y-auto p-6 bg-slate-50/30 custom-scrollbar">
                    <div v-if="isFetchingTools" class="flex flex-col items-center justify-center py-10 gap-3">
                        <div class="animate-spin w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full"></div>
                        <span class="text-slate-500 text-sm">正在连接 MCP 服务获取工具...</span>
                    </div>
                    <div v-else-if="currentMcpTools.length === 0" class="text-center py-10 text-slate-400 flex flex-col items-center gap-2">
                        <svg class="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>
                        <span>该服务暂未提供任何工具或连接失败</span>
                    </div>
                    <div v-else class="space-y-4">
                        <div v-for="(tool, idx) in currentMcpTools" :key="idx" class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                            <div class="flex items-start justify-between mb-2">
                                <div class="font-bold text-slate-700 font-mono text-sm bg-slate-100 px-2 py-0.5 rounded">{{ tool.name }}</div>
                            </div>
                            <p class="text-sm text-slate-600 mb-3">{{ tool.description || '暂无描述' }}</p>
                            
                            <div v-if="tool.inputSchema" class="bg-slate-50 rounded-lg p-3 border border-slate-100">
                                <div class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Input Schema</div>
                                <pre class="text-xs text-slate-600 font-mono whitespace-pre-wrap overflow-x-auto">{{ JSON.stringify(tool.inputSchema, null, 2) }}</pre>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="p-4 border-t border-slate-100 bg-white flex justify-end">
                    <button @click="showToolsModal = false" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-sm font-medium transition-colors">关闭</button>
                </div>
            </div>
        </div>

        <!-- Tool Selector Modal -->
        <div v-if="showToolSelector" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
            <div class="bg-white rounded-xl shadow-2xl w-[800px] max-w-[95vw] max-h-[85vh] flex flex-col overflow-hidden" @click.stop>
                <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                    <h3 class="text-lg font-bold text-slate-800">选择组件</h3>
                    <button @click="showToolSelector = false" class="text-slate-400 hover:text-slate-600"><svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
                </div>
                
                <div class="flex border-b border-slate-100">
                    <button 
                        v-for="tab in ['mcp', 'skill']" 
                        :key="tab"
                        @click="activeToolTab = tab"
                        class="px-6 py-3 text-sm font-medium border-b-2 transition-colors capitalize"
                        :class="activeToolTab === tab ? 'border-blue-500 text-blue-600 bg-blue-50/50' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'"
                    >
                        {{ tab === 'mcp' ? 'MCP Servers' : 'Agent Skills' }}
                    </button>
                </div>

                <div class="flex-1 overflow-y-auto p-6 bg-slate-50/30 custom-scrollbar">
                    <div v-if="isLoadingTools" class="flex justify-center py-10"><div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div></div>
                    <div v-else-if="filteredMarketTools.length === 0" class="text-center py-10 text-slate-400">暂无可用组件</div>
                    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div v-for="tool in filteredMarketTools" :key="tool.id" class="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-all flex flex-col">
                            <div class="flex justify-between items-start mb-2">
                                <div class="flex items-center gap-2">
                                    <span class="p-1.5 rounded-md" :class="tool.type === 'mcp' ? 'bg-purple-100 text-purple-600' : 'bg-green-100 text-green-600'">
                                        <svg v-if="tool.type === 'mcp'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"></path></svg>
                                        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                    </span>
                                    <span class="font-bold text-slate-700 truncate" :title="tool.name">{{ tool.name }}</span>
                                </div>
                                <span class="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">v{{ tool.version }}</span>
                            </div>
                            <p class="text-xs text-slate-500 mb-4 line-clamp-2 flex-1">{{ tool.description || 'No description' }}</p>
                            
                            <!-- Compatibility & Action -->
                            <div class="mt-auto flex items-center justify-between pt-3 border-t border-slate-50">
                                <div v-if="!checkCompatibility(tool)" class="text-xs text-amber-500 flex items-center gap-1" title="版本可能不兼容">
                                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                    版本风险
                                </div>
                                <div v-else class="text-xs text-green-500 flex items-center gap-1">
                                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                    兼容
                                </div>

                                <button 
                                    @click="selectToolFromMarket(tool)"
                                    class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1"
                                    :class="isToolSelected(tool) || (tool.is_active === false) ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-blue-50 text-blue-600 hover:bg-blue-100'"
                                    :disabled="isToolSelected(tool) || (tool.is_active === false)"
                                    :title="(tool.is_active === false) ? '工具未配置或不可用' : ''"
                                >
                                    {{ isToolSelected(tool) ? '已添加' : ((tool.is_active === false) ? '不可用' : '添加') }}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, h, createVNode } from 'vue';
import Loading from '@/shared/components/atoms/Loading/Loading.vue';
import { Modal, message } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import UserScriptsEditor from './UserScriptsEditor.vue';

// Helper to create simple SVG icons without runtime compiler dependency
const createIcon = (d) => ({
    render: () => h('svg', {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '1.5',
        stroke: 'currentColor'
    }, [
        h('path', {
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            d: d
        })
    ])
});

// Icons
const GlobeAltIcon = createIcon('M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S12 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S12 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418');
const ChartBarIcon = createIcon('M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z');
const DocumentTextIcon = createIcon('M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z');
const BookOpenIcon = createIcon('M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25');
const LightBulbIcon = createIcon('M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 2.625v1.068a1.5 1.5 0 01-1.5 1.5h-1.5a1.5 1.5 0 01-1.5-1.5v-1.068a25.509 25.509 0 013 0zm-6-2.25a9 9 0 1118 0 9 9 0 01-18 0z');
const PresentationChartLineIcon = createIcon('M3.75 3v11.25A2.25 2.25 0 006 14.25h12a2.25 2.25 0 002.25-2.25V3M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 14.25h-2.25m-7.5 0h2.25m-2.25 0v5.25m0 0h2.25m-2.25 0h-2.25');

const myAgents = ref([]);
const discoverAgents = ref([]);
const availableModels = ref([]);
const knowledgeBases = ref([]);
const showModal = ref(false);
const isEditing = ref(false);
const isSaving = ref(false);
const isLoading = ref(true);

// Tools Viewer
const showToolsModal = ref(false);
const currentMcpTools = ref([]);
const isFetchingTools = ref(false);
const currentMcpName = ref('');

// Tool Selector & Import/Export
const showToolSelector = ref(false);
const activeToolTab = ref('mcp');
const marketTools = ref([]); // Stores fetched MCPs and Skills
const isLoadingTools = ref(false);
const importInput = ref(null);

// Icon Upload & Model Dropdown
const iconInput = ref(null);
const showModelDropdown = ref(false);

const availableIcons = {
    'globe': GlobeAltIcon,
    'chart': ChartBarIcon,
    'book': BookOpenIcon,
    'document': DocumentTextIcon,
    'presentation': PresentationChartLineIcon,
    'lightbulb': LightBulbIcon
};

const getIconComponent = (iconName) => {
    return availableIcons[iconName] || GlobeAltIcon;
};

const isImageIcon = (icon) => {
    if (!icon || typeof icon !== 'string') return false;
    const value = icon.trim();
    if (!value) return false;
    if (value.startsWith('data:image')) return true;
    if (value.startsWith('blob:')) return true;
    if (/^https?:\/\//i.test(value)) return true;
    if (value.startsWith('/') || value.startsWith('./') || value.startsWith('../')) return true;
    return /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i.test(value);
};

const triggerIconUpload = () => {
    iconInput.value.click();
};

const handleIconUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check size (e.g., < 100KB)
    if (file.size > 100 * 1024) {
        message.warning("图标文件过大，建议小于 100KB");
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        form.value.icon = e.target.result;
    };
    reader.readAsDataURL(file);
};

const getSelectedModel = () => {
    if (!form.value.model_config.model_id) return null;
    return availableModels.value.find(m => m.model_id === form.value.model_config.model_id);
};

const selectModel = (model) => {
    form.value.model_config.model_id = model ? model.model_id : '';
    showModelDropdown.value = false;
};

const sections = ref({
    prompt: true,
    model: true,
    tools: false,
    mcp: false,
    skills: false,
    knowledge: false
});

const defaultSkillsConfig = {
    environment: { type: 'local', image: 'python:3.9-slim' },
    python: { enabled: false, safe_mode: true, allowed_modules: [] },
    filesystem: { enabled: false, base_dir: '/tmp', allow_write: false },
    browser: { enabled: false, headless: true, search_engine: 'duckduckgo' }
};

const buildAgentPayload = (agentLike) => {
    const payload = {
        name: agentLike?.name || '',
        description: agentLike?.description || '',
        icon: agentLike?.icon || 'globe',
        system_prompt: agentLike?.system_prompt || '',
        model_config: agentLike?.model_config || { model_id: '', reasoning: false },
        tools_config: Array.isArray(agentLike?.tools_config) ? agentLike.tools_config : [],
        mcp_config: Array.isArray(agentLike?.mcp_config) ? agentLike.mcp_config : [],
        skills_config: agentLike?.skills_config || defaultSkillsConfig,
        knowledge_config: agentLike?.knowledge_config || { document_ids: [], strict_only: false }
    };

    if (agentLike?.id) payload.id = agentLike.id;
    if (typeof agentLike?.is_template === 'boolean') payload.is_template = agentLike.is_template;
    if (typeof agentLike?.is_active === 'boolean') payload.is_active = agentLike.is_active;

    return payload;
};

const form = ref({
    id: null,
    name: '',
    description: '',
    icon: '/tiga.svg',
    system_prompt: '',
    model_config: { model_id: '', reasoning: false },
    tools_config: [],
    mcp_config: [],
    skills_config: defaultSkillsConfig,
    knowledge_config: { document_ids: [] }
});

const activeAgentId = computed(() => form.value.id || '');

onMounted(() => {
    fetchAgents();
    fetchModels();
    fetchKnowledgeBases();
});

const fetchAgents = async () => {
    isLoading.value = true;
    try {
        const res = await fetch('/api/v1/agents/');
        if (res.ok) {
            const allAgents = await res.json();
            myAgents.value = allAgents.filter(a => !a.is_template);
            discoverAgents.value = allAgents.filter(a => a.is_template);
            
            // Map icon strings to components for discover agents if needed
            discoverAgents.value.forEach(agent => {
                const gradients = [
                    'linear-gradient(140.57deg, #ff9ba2 17.28%, #f56a79 91.19%)',
                    'linear-gradient(180deg, #a7c0ff 0%, #6892fd 100%)',
                    'linear-gradient(180deg, #73f1bb 0%, #49dd9d 100%)',
                    'linear-gradient(180deg, #ffc56e 0%, #ffb153 100%)',
                    'linear-gradient(135.82deg, #d194ff 0%, #8a8eff 93.32%)',
                    'linear-gradient(132.83deg, #46c3ff 14.35%, #47aafd 84.99%)'
                ];
                agent.gradient = gradients[agent.name.length % gradients.length];
                // Map icon string to component using the availableIcons map
                agent.iconComponent = availableIcons[agent.icon] || GlobeAltIcon;
            });
            
            // Also map icons for myAgents to ensure they display correctly if they have icon strings
            myAgents.value.forEach(agent => {
                 agent.iconComponent = availableIcons[agent.icon] || GlobeAltIcon;
            });
        }
    } catch (e) {
        console.error("Failed to fetch agents", e);
    } finally {
        isLoading.value = false;
    }
};

const fetchKnowledgeBases = async () => {
    try {
        const res = await fetch('/api/v1/knowledge/list');
        if (res.ok) {
            knowledgeBases.value = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch knowledge bases", e);
    }
};

const fetchModels = async () => {
    try {
        const res = await fetch('/api/v1/llm/models');
        if (res.ok) {
            const allModels = await res.json();
            availableModels.value = allModels.filter(m => m.is_active);
        }
    } catch (e) {
        console.error("Failed to fetch models", e);
    }
};

const openCreateModal = () => {
    isEditing.value = false;
    form.value = {
        id: null,
        name: '',
        description: '',
        icon: 'globe',
        system_prompt: '',
        model_config: { model_id: '', reasoning: false },
        tools_config: [],
        mcp_config: [],
        skills_config: defaultSkillsConfig,
        knowledge_config: { document_ids: [], strict_only: false }
    };
    showModal.value = true;
};

const editAgent = (agent) => {
    isEditing.value = true;
    form.value = buildAgentPayload(agent);
    showModal.value = true;
};

const deleteAgent = (agent) => {
    Modal.confirm({
        title: `确定要删除智能体 "${agent.name}" 吗？`,
        icon: createVNode(ExclamationCircleOutlined),
        content: '删除后将无法恢复，请谨慎操作。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                const res = await fetch(`/api/v1/agents/${agent.id}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    fetchAgents();
                    message.success("删除成功");
                }
            } catch (e) {
                message.error("删除失败");
            }
        }
    });
};

const closeModal = () => {
    showModal.value = false;
};

const toggleSection = (section) => {
    sections.value[section] = !sections.value[section];
};

const addMcp = () => {
    form.value.mcp_config.push({
        name: '',
        type: 'stdio',
        command: '',
        args: '[]'
    });
};

const removeMcp = (index) => {
    form.value.mcp_config.splice(index, 1);
};

const viewMcpTools = async (mcp) => {
    currentMcpName.value = mcp.name || 'Unknown MCP';
    currentMcpTools.value = [];
    showToolsModal.value = true;
    isFetchingTools.value = true;
    
    try {
        // Parse args
        let parsedArgs = [];
        try {
            parsedArgs = JSON.parse(mcp.args || '[]');
        } catch (e) {
            console.warn("Failed to parse args", e);
            parsedArgs = [];
        }
        
        const config = {
            type: mcp.type,
            command: mcp.command,
            args: parsedArgs,
            env: {}
        };
        
        const res = await fetch('/api/v1/mcp/fetch_tools', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        if (res.ok) {
            currentMcpTools.value = await res.json();
        } else {
            const err = await res.json();
            message.error("获取工具失败: " + (err.detail || 'Unknown error'));
        }
    } catch (e) {
        console.error("Failed to fetch MCP tools", e);
        message.error("连接 MCP 服务失败");
    } finally {
        isFetchingTools.value = false;
    }
};

const removeSkill = (tool) => {
    const index = form.value.tools_config.findIndex(t => t === tool || (typeof t === 'object' && t.name === tool.name));
    if (index > -1) {
        form.value.tools_config.splice(index, 1);
    }
};

const formatSize = (bytes) => {
    if (!bytes && bytes !== 0) return '0 B';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// --- Tool Selector Logic ---

const openToolSelector = (tab = 'mcp') => {
    activeToolTab.value = tab;
    showToolSelector.value = true;
    fetchMarketTools();
};

const fetchMarketTools = async () => {
    if (marketTools.value.length > 0) return; // Cache simple
    isLoadingTools.value = true;
    try {
        const [mcpRes, skillRes] = await Promise.all([
            fetch('/api/v1/mcp/'),
            fetch('/api/v1/skills/')
        ]);
        
        const mcps = mcpRes.ok ? await mcpRes.json() : [];
        const skills = skillRes.ok ? await skillRes.json() : [];
        
        marketTools.value = [
            ...mcps.map(m => ({ ...m, type: 'mcp' })),
            ...skills.map(s => ({ ...s, type: 'skill' }))
        ];
    } catch (e) {
        console.error("Failed to fetch tools", e);
        message.error("获取组件列表失败");
    } finally {
        isLoadingTools.value = false;
    }
};

const filteredMarketTools = computed(() => {
    return marketTools.value.filter(t => t.type === activeToolTab.value);
});

const checkCompatibility = (tool) => {
    // Mock Logic: If tool version starts with '2.', warn (assume agent supports v1)
    if (tool.version && tool.version.startsWith('2.')) return false;
    return true;
};

const isToolSelected = (tool) => {
    if (tool.type === 'mcp') {
        // Check mcp_config (array of objects)
        // We check by name or ID if available. 
        // form.mcp_config items have 'name', 'type', 'command'.
        // tool from market has 'name', 'config' (json), etc.
        return form.value.mcp_config.some(m => m.name === tool.name);
    } else {
        // Check tools_config (array of strings or objects)
        return form.value.tools_config.some(t => {
            if (typeof t === 'string') return t === tool.name;
            return t.id === tool.id || t.name === tool.name;
        });
    }
};

const selectToolFromMarket = (tool) => {
    if (tool.type === 'mcp') {
        // Add to mcp_config
        // Default to stdio/python if config missing, or parse tool.config
        let config = {
            name: tool.name,
            type: tool.mcp_type || 'stdio', // tool.mcp_type might come from backend
            command: 'python',
            args: '[]'
        };
        
        // Try to use tool's stored config
        if (tool.config) {
            // tool.config is object (from backend model)
            config = {
                ...config,
                ...tool.config,
                name: tool.name // Ensure name match
            };
            // Ensure args is string for textarea
            if (Array.isArray(config.args)) {
                config.args = JSON.stringify(config.args);
            }
        }
        
        form.value.mcp_config.push(config);
        message.success(`已添加 MCP 服务: ${tool.name}`);
    } else {
        // Add to tools_config
        // Store as object to preserve details
        form.value.tools_config.push({
            type: 'skill',
            id: tool.id,
            name: tool.name,
            content: tool.content,
            version: tool.version
        });
        message.success(`已添加技能: ${tool.name}`);
    }
};

// --- Import/Export Logic ---

const exportConfig = () => {
    const dataStr = JSON.stringify(form.value, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-${form.value.name || 'config'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success("配置已导出");
};

const triggerImport = () => {
    importInput.value.click();
};

const handleImportConfig = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            // Simple validation
            if (!data.name && !data.model_config) {
                throw new Error("Invalid config format");
            }
            
            // Merge or Replace? Replace is safer for "Import"
            form.value = { ...form.value, ...data };
            
            // Ensure ID is null if we want to create new, or keep it if updating?
            // Usually import implies overwriting settings. 
            // If importing to "Create New", ID should be null. 
            // If "Edit", maybe keep ID?
            // Let's assume user wants to apply settings. 
            // If isEditing, keep ID. If not, keep ID null.
            if (!isEditing.value) {
                form.value.id = null;
            } else {
                form.value.id = activeAgentId.value; // Restore ID
            }
            
            message.success("配置已导入");
        } catch (err) {
            console.error(err);
            message.error("导入失败: 配置文件格式错误");
        }
    };
    reader.readAsText(file);
    event.target.value = ''; // Reset
};

const saveAgent = async () => {
    if (!form.value.name) {
        alert("请输入智能体名称");
        return;
    }
    
    isSaving.value = true;
    try {
        const url = isEditing.value 
            ? `/api/v1/agents/${form.value.id}`
            : '/api/v1/agents/';
        
        const method = isEditing.value ? 'PUT' : 'POST';

        const payload = buildAgentPayload(form.value);
        
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            closeModal();
            fetchAgents();
        } else {
            const err = await res.json();
            alert("保存失败: " + JSON.stringify(err));
        }
    } catch (e) {
        alert("保存错误: " + e.message);
    } finally {
        isSaving.value = false;
    }
};
</script>

<style scoped>
@keyframes slide-in-right {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
.animate-slide-in-right {
    animation: slide-in-right 0.3s ease-out forwards;
}
</style>
