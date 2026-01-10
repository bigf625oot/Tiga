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
                                        <img v-if="isBase64Icon(agent.icon)" :src="agent.icon" class="w-full h-full object-cover" />
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
                            <p class="text-slate-400 text-xs mt-1">点击上方“创建智能体”开始构建您的专属 AI 助手</p>
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
                                        v-if="agent.is_template"
                                        class="w-[46px] h-[46px] rounded-[20px] flex items-center justify-center shadow-sm text-white"
                                        :style="{ background: agent.gradient }"
                                    >
                                        <component :is="agent.iconComponent || agent.icon" class="w-6 h-6" />
                                    </div>
                                    <div 
                                        v-else
                                        class="w-[46px] h-[46px] rounded-[20px] flex items-center justify-center shadow-sm border border-slate-100 bg-white overflow-hidden"
                                    >
                                        <img v-if="isBase64Icon(agent.icon)" :src="agent.icon" class="w-full h-full object-cover" />
                                        <component v-else :is="agent.iconComponent || agent.icon" class="w-6 h-6 text-slate-700" />
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
                <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
                    
                    <!-- Basic Info -->
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <div class="flex items-center gap-2 mb-4 text-slate-800 font-medium">
                            <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                            智能体基础信息
                        </div>
                        <div class="space-y-4">
                            <div>
                                <label class="block text-xs font-medium text-slate-500 mb-1">智能体名称</label>
                                <input v-model="form.name" type="text" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="请输入智能体名称">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-slate-500 mb-1">智能体简介</label>
                                <textarea v-model="form.description" rows="3" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none" placeholder="请描述智能体的功能和用途..."></textarea>
                            </div>
                            
                            <!-- Icon Upload -->
                            <div>
                                <label class="block text-xs font-medium text-slate-500 mb-2">智能体图标</label>
                                <div class="flex items-center gap-4">
                                    <div 
                                        class="w-16 h-16 rounded-2xl border border-slate-200 flex items-center justify-center overflow-hidden bg-slate-50 relative group cursor-pointer"
                                        @click="triggerIconUpload"
                                    >
                                        <img v-if="isBase64Icon(form.icon)" :src="form.icon" class="w-full h-full object-cover" />
                                        <component v-else :is="getIconComponent(form.icon)" class="w-8 h-8 text-slate-400" />
                                        
                                        <!-- Hover Overlay -->
                                        <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                        </div>
                                    </div>
                                    <div class="flex-1">
                                        <div class="text-xs text-slate-500 mb-2">建议尺寸 128x128px，支持 PNG, JPG</div>
                                        <button @click="triggerIconUpload" class="text-xs px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors">
                                            上传图片
                                        </button>
                                        <input type="file" ref="iconInput" class="hidden" accept="image/*" @change="handleIconUpload">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- System Prompt -->
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-4 cursor-pointer" @click="toggleSection('prompt')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                                系统提示 (System Prompt)
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.prompt ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.prompt" class="space-y-3">
                             <textarea v-model="form.system_prompt" rows="6" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono text-slate-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="You are a helpful assistant..."></textarea>
                        </div>
                    </div>

                    <!-- Model Selection -->
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-4 cursor-pointer" @click="toggleSection('model')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                模型配置
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.model ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.model" class="space-y-4">
                            <!-- Custom Dropdown Trigger -->
                            <div class="relative">
                                <div 
                                    @click.stop="showModelDropdown = !showModelDropdown"
                                    class="relative z-20 w-full px-4 py-3 border border-slate-300 rounded-lg bg-white flex items-center justify-between cursor-pointer hover:border-blue-400 transition-all text-sm group"
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
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-4 cursor-pointer" @click="toggleSection('knowledge')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                                知识库配置
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.knowledge ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.knowledge" class="space-y-3">
                            <div v-if="knowledgeBases.length === 0" class="text-xs text-slate-400 py-2">暂无可用知识库</div>
                            <div v-for="kb in knowledgeBases" :key="kb.id" class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50">
                                <input type="checkbox" :value="kb.id" v-model="form.knowledge_config.document_ids" class="rounded text-blue-600 focus:ring-blue-500">
                                <div class="flex-1">
                                    <div class="text-sm font-medium text-slate-700">{{ kb.filename }}</div>
                                    <div class="text-xs text-slate-400">{{ formatSize(kb.file_size) }}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tools Selection -->
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-4 cursor-pointer" @click="toggleSection('tools')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                                默认工具
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.tools ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.tools" class="space-y-3">
                            <label class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50">
                                <input type="checkbox" value="duckduckgo" v-model="form.tools_config" class="rounded text-blue-600 focus:ring-blue-500">
                                <span class="text-sm font-medium text-slate-700">DuckDuckGo Search</span>
                            </label>
                            <label class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50">
                                <input type="checkbox" value="calculator" v-model="form.tools_config" class="rounded text-blue-600 focus:ring-blue-500">
                                <span class="text-sm font-medium text-slate-700">Calculator</span>
                            </label>
                            <label class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50">
                                <input type="checkbox" value="n8n" v-model="form.tools_config" class="rounded text-blue-600 focus:ring-blue-500">
                                <span class="text-sm font-medium text-slate-700">N8N Workflow</span>
                            </label>
                        </div>
                    </div>

                    <!-- MCP Config -->
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                         <div class="flex items-center justify-between mb-4 cursor-pointer" @click="toggleSection('mcp')">
                            <div class="flex items-center gap-2 text-slate-800 font-medium">
                                <svg class="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                MCP 服务配置
                            </div>
                            <svg class="w-4 h-4 text-slate-400 transform transition-transform" :class="sections.mcp ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        <div v-show="sections.mcp" class="space-y-4">
                            <div v-for="(mcp, idx) in form.mcp_config" :key="idx" class="p-3 bg-slate-50 border border-slate-200 rounded-lg relative group">
                                <button @click="removeMcp(idx)" class="absolute top-2 right-2 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                </button>
                                <div class="space-y-2">
                                    <input v-model="mcp.name" class="w-full bg-transparent border-b border-slate-200 text-sm py-1 focus:border-blue-500 outline-none" placeholder="服务名称 (e.g. filesystem)">
                                    <div class="flex gap-2">
                                        <select v-model="mcp.type" class="bg-white border border-slate-200 rounded text-xs px-2 py-1 outline-none">
                                            <option value="stdio">stdio</option>
                                            <option value="sse">sse</option>
                                        </select>
                                        <input v-model="mcp.command" class="flex-1 bg-white border border-slate-200 rounded text-xs px-2 py-1 outline-none" placeholder="命令 / URL">
                                    </div>
                                    <textarea v-model="mcp.args" rows="1" class="w-full bg-white border border-slate-200 rounded text-xs px-2 py-1 outline-none resize-none" placeholder="参数 (JSON array, e.g. ['arg1', 'arg2'])"></textarea>
                                </div>
                            </div>
                            <button @click="addMcp" class="w-full py-2 border border-dashed border-slate-300 rounded-lg text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm flex items-center justify-center gap-1">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                添加 MCP 服务
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Modal Footer -->
                <div class="px-6 py-4 border-t border-slate-200 bg-white flex justify-end gap-3">
                    <button @click="closeModal" class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors">取消</button>
                    <button @click="saveAgent" class="px-6 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm" :disabled="isSaving">
                        <span v-if="isSaving">保存中...</span>
                        <span v-else>保存配置</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, h, createVNode } from 'vue';
import Loading from './common/Loading.vue';
import { Modal, message } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';

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

const isBase64Icon = (icon) => {
    return icon && icon.startsWith('data:image');
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

const form = ref({
    id: null,
    name: '',
    description: '',
    icon: 'globe',
    system_prompt: '',
    model_config: { model_id: '', reasoning: false },
    tools_config: [],
    mcp_config: [],
    skills_config: {
        environment: { type: 'local', image: 'python:3.9-slim' },
        python: { enabled: false, safe_mode: true, allowed_modules: [] },
        filesystem: { enabled: false, base_dir: '/tmp', allow_write: false },
        browser: { enabled: false, headless: true, search_engine: 'duckduckgo' }
    },
    knowledge_config: { document_ids: [] }
});

onMounted(() => {
    fetchAgents();
    fetchModels();
    fetchKnowledgeBases();
});

const fetchAgents = async () => {
    isLoading.value = true;
    try {
        const res = await fetch('http://localhost:8000/api/v1/agents/');
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
        const res = await fetch('http://localhost:8000/api/v1/knowledge/list');
        if (res.ok) {
            knowledgeBases.value = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch knowledge bases", e);
    }
};

const fetchModels = async () => {
    try {
        const res = await fetch('http://localhost:8000/api/v1/llm/models');
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
        skills_config: {
            environment: { type: 'local', image: 'python:3.9-slim' },
            python: { enabled: false, safe_mode: true, allowed_modules: [] },
            filesystem: { enabled: false, base_dir: '/tmp', allow_write: false },
            browser: { enabled: false, headless: true, search_engine: 'duckduckgo' }
        },
        knowledge_config: { document_ids: [] }
    };
    showModal.value = true;
};

const editAgent = (agent) => {
    isEditing.value = true;
    form.value = JSON.parse(JSON.stringify(agent));
    // Ensure nested objects exist
    if (!form.value.model_config) form.value.model_config = { model_id: '', reasoning: false };
    if (!form.value.tools_config) form.value.tools_config = [];
    if (!form.value.mcp_config) form.value.mcp_config = [];
    if (!form.value.knowledge_config) form.value.knowledge_config = { document_ids: [] };
    
    if (!form.value.skills_config) form.value.skills_config = {
        environment: { type: 'local', image: 'python:3.9-slim' },
        python: { enabled: false, safe_mode: true, allowed_modules: [] },
        filesystem: { enabled: false, base_dir: '/tmp', allow_write: false },
        browser: { enabled: false, headless: true, search_engine: 'duckduckgo' }
    };
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
                const res = await fetch(`http://localhost:8000/api/v1/agents/${agent.id}`, {
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

const formatSize = (bytes) => {
    if (!bytes && bytes !== 0) return '0 B';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const saveAgent = async () => {
    if (!form.value.name) {
        alert("请输入智能体名称");
        return;
    }
    
    isSaving.value = true;
    try {
        const url = isEditing.value 
            ? `http://localhost:8000/api/v1/agents/${form.value.id}`
            : 'http://localhost:8000/api/v1/agents/';
        
        const method = isEditing.value ? 'PUT' : 'POST';
        
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form.value)
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