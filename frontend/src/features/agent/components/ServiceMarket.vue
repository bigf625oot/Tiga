<template>
  <div class="h-full flex bg-white">
    <!-- Inner Sidebar -->
    <div class="w-56 bg-white border-r border-slate-100 flex flex-col flex-shrink-0">
      <div class="p-4">
        <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          工具市场
        </h2>
        <p class="text-xs text-slate-500 mt-1">发现并集成强大的AI能力</p>
      </div>

      <div class="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        <div 
          v-for="item in menuItems" 
          :key="item.id"
          @click="activeCategory = item.id"
          class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm font-medium"
          :class="activeCategory === item.id ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'"
        >
          <span>{{ item.label }}</span>
          <span v-if="item.count" class="ml-auto text-xs bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded-full">{{ item.count }}</span>
        </div>
      </div>

      <!-- User Custom Link -->
      <div class="p-4 border-t border-slate-100">
        <button 
          @click="showCreateToolModal = true"
          class="flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600 transition-colors w-full"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>创建工具</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden" @click="activeMenuId = null">
      <!-- Header -->
      <div class="px-8 py-5 bg-white border-b border-slate-100 flex items-center justify-between flex-shrink-0">
        <div class="flex items-center gap-4">
          <div class="relative">
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索工具、插件或技能..." 
              class="pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm w-80 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none transition-all"
            />
            <svg class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          
          <!-- Filter Tags -->
          <div class="flex gap-2">
            <button 
              v-for="tag in [{id: 'all', label: '全部'}, {id: 'hot', label: '热门'}, {id: 'new', label: '最新'}, {id: 'official', label: '官方'}]" 
              :key="tag.id"
              class="px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
              :class="activeFilter === tag.id ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              @click="activeFilter = tag.id"
            >
              {{ tag.label }}
            </button>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button @click="refreshData" class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors" title="刷新">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <!-- Skeleton Loader -->
        <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div v-for="n in 8" :key="n" class="border border-slate-100 rounded-xl p-5 bg-white h-[220px] flex flex-col animate-pulse">
            <!-- ... skeleton content ... -->
          </div>
        </div>

        <div v-else-if="filteredItems.length === 0" class="flex flex-col items-center justify-center h-64 text-slate-400">
          <svg class="w-16 h-16 mb-4 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p>未找到相关服务</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div 
            v-for="item in filteredItems" 
            :key="item.id" 
            class="group bg-white border border-gray-200 rounded-xl hover:shadow-lg transition-all duration-200 flex flex-col h-[230px] relative"
          >
            <div class="p-4 flex flex-col h-full">
              <!-- Header: Icon + Title + Menu -->
              <div class="flex gap-3 mb-2">
                <!-- Icon -->
                <img v-if="item.iconUrl" :src="item.iconUrl" class="w-12 h-12 object-contain flex-shrink-0" />
                <div v-else class="w-12 h-12 flex-shrink-0 flex items-center justify-center text-base text-gray-400 bg-gray-50 rounded-lg">{{ item.icon }}</div>
                
                <!-- Title & Tags Area -->
                <div class="flex-1 min-w-0">
                  <div class="flex justify-between items-start">
                    <h3 class="font-bold text-gray-800 text-sm leading-tight truncate pr-1" :title="item.name">{{ item.name }}</h3>
                    
                    <!-- Menu Trigger -->
                    <div v-if="!item.is_official" class="relative flex-shrink-0 -mt-1 -mr-1">
                      <button 
                        @click.stop="toggleMenu(item.id)"
                        class="p-1 text-gray-300 hover:text-gray-600 hover:bg-gray-50 rounded transition-colors"
                        :class="{'text-gray-600 bg-gray-50': activeMenuId === item.id}"
                      >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                      </button>
                      
                      <!-- Dropdown Menu -->
                      <div 
                        v-if="activeMenuId === item.id"
                        class="absolute right-0 top-full mt-1 w-24 bg-white border border-gray-200 rounded-lg shadow-xl z-20 py-1"
                        @click.stop
                      >
                        <button 
                          @click="openEditModal(item); activeMenuId = null"
                          class="w-full text-left px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors"
                        >
                          编辑
                        </button>
                        <button 
                          @click="deleteTool(item); activeMenuId = null"
                          class="w-full text-left px-3 py-1.5 text-xs text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Tags (Below Title) -->
                  <div class="flex items-center gap-1.5 mt-1">
                    <span class="px-1.5 py-px rounded text-[10px] font-medium border" 
                      :class="item.type === 'mcp' ? 'bg-purple-50 text-purple-600 border-purple-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'">
                      {{ item.type === 'mcp' ? 'MCP' : 'Skill' }}
                    </span>
                    <span v-if="item.is_official" class="px-1.5 py-px rounded text-[10px] font-medium bg-blue-50 text-blue-600 border border-blue-100">
                      官方
                    </span>
                  </div>
                </div>
              </div>

              <!-- Description -->
              <p class="text-xs text-gray-500 leading-relaxed line-clamp-3 mb-3 flex-1" :title="item.description">
                {{ item.description || '暂无描述' }}
              </p>

              <!-- Footer -->
              <div class="mt-auto pt-3 border-t border-gray-50 flex flex-col gap-2">
                <div class="text-[10px] text-gray-400">
                  <span class="truncate max-w-[120px]">@{{ item.author }}</span>
                </div>

                <div class="flex items-center justify-between">
                  <div class="text-[10px] text-gray-400">
                    <span v-if="item.downloads">{{ item.downloads }}k</span>
                    <span v-else>v{{ item.version }}</span>
                  </div>

                  <button 
                    @click.stop="handleInstall(item)"
                    class="px-2.5 py-1 text-xs rounded transition-colors border"
                    :class="item.installed 
                      ? 'bg-gray-50 text-gray-400 border-transparent cursor-default' 
                      : 'bg-white border-gray-200 text-gray-700 hover:text-blue-600 hover:border-blue-200 hover:shadow-sm'"
                    :disabled="item.installed || item.isInstalling"
                  >
                    <div class="flex items-center gap-1">
                      <svg v-if="item.isInstalling" class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>{{ item.installed ? '已安装' : (item.isInstalling ? '安装中' : '获取') }}</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Create/Edit Tool Modal -->
  <div v-if="showCreateToolModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-all" @click="closeModal">
    <div class="bg-white rounded-xl shadow-2xl w-[640px] max-w-[95vw] max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200" @click.stop>
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <div>
          <h3 class="text-lg font-bold text-slate-800">{{ isEditing ? '编辑工具' : '创建新工具' }}</h3>
          <p class="text-xs text-slate-500 mt-0.5">{{ isEditing ? '修改已有的 AI 助手工具配置' : '配置并发布你的 AI 助手工具' }}</p>
        </div>
        <button @click="closeModal" class="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-100 transition-colors">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div class="space-y-6">
          <!-- Tool Type Selection -->
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-slate-700">
              工具类型 <span class="text-red-500">*</span>
            </label>
            <div class="grid grid-cols-2 gap-4">
              <div 
                @click="newToolForm.type = 'skill'"
                class="relative p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-3"
                :class="newToolForm.type === 'skill' ? 'border-blue-500 bg-blue-50/50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
              >
                <div class="p-2 rounded-lg" :class="newToolForm.type === 'skill' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                </div>
                <div>
                  <div class="font-medium text-slate-800">Agent Skill</div>
                  <div class="text-xs text-slate-500 mt-1 leading-relaxed">基于自然语言指令的轻量级技能，适用于文本处理和逻辑分析。</div>
                </div>
                <div v-if="newToolForm.type === 'skill'" class="absolute top-3 right-3 text-blue-500">
                  <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>

              <div 
                @click="newToolForm.type = 'mcp'"
                class="relative p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-3"
                :class="newToolForm.type === 'mcp' ? 'border-purple-500 bg-purple-50/50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
              >
                <div class="p-2 rounded-lg" :class="newToolForm.type === 'mcp' ? 'bg-purple-100 text-purple-600' : 'bg-slate-100 text-slate-500'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <div class="font-medium text-slate-800">MCP Server</div>
                  <div class="text-xs text-slate-500 mt-1 leading-relaxed">标准化的模型上下文协议服务，支持复杂工具调用和资源访问。</div>
                </div>
                <div v-if="newToolForm.type === 'mcp'" class="absolute top-3 right-3 text-purple-500">
                  <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Basic Info Grid -->
          <div class="grid grid-cols-2 gap-5">
            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700">
                名称 <span class="text-red-500">*</span>
              </label>
              <input 
                v-model="newToolForm.name" 
                type="text" 
                placeholder="例如：codemap" 
                class="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400 text-sm" 
              />
            </div>
            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700">
                版本 <span class="text-red-500">*</span>
              </label>
              <input 
                v-model="newToolForm.version" 
                type="text" 
                placeholder="1.0.0" 
                class="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400 text-sm" 
              />
            </div>
          </div>

          <!-- Category or MCP Type -->
          <div class="grid gap-5" :class="newToolForm.type === 'mcp' ? 'grid-cols-2' : 'grid-cols-1'">
            <div v-if="newToolForm.type === 'mcp'" class="space-y-2">
              <label class="block text-sm font-medium text-slate-700">MCP 类型</label>
              <div class="relative">
                <select v-model="newToolForm.mcp_type" class="w-full pl-4 pr-10 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all text-sm appearance-none cursor-pointer">
                  <option value="stdio">STDIO (Standard Input/Output)</option>
                  <option value="sse">SSE (Server-Sent Events)</option>
                </select>
                <div class="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-slate-500">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700">分类</label>
              <div class="relative">
                <select v-model="newToolForm.category" class="w-full pl-4 pr-10 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all text-sm appearance-none cursor-pointer">
                  <option value="" disabled selected>请选择分类...</option>
                  <option v-for="cat in menuItems.filter(c => c.id !== 'all')" :key="cat.id" :value="cat.id">
                    {{ cat.label }}
                  </option>
                </select>
                <div class="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-slate-500">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <label class="block text-sm font-medium text-slate-700">描述</label>
            <textarea 
              v-model="newToolForm.description" 
              rows="3" 
              placeholder="简要描述该工具的功能、用途及特点..." 
              class="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none text-sm placeholder:text-slate-400"
            ></textarea>
          </div>

          <!-- Skill Specific: File Upload & Instructions -->
          <div v-if="newToolForm.type === 'skill'" class="space-y-5">
            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700">导入配置 (可选)</label>
              <div class="group bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-blue-500 hover:bg-blue-50/30 transition-all cursor-pointer relative">
                <input type="file" @change="handleFileUpload" accept=".zip,.skill" class="absolute inset-0 opacity-0 cursor-pointer z-10" />
                <div class="space-y-3 pointer-events-none">
                  <div class="w-12 h-12 mx-auto rounded-full bg-slate-200 group-hover:bg-blue-100 group-hover:text-blue-600 flex items-center justify-center transition-colors text-slate-400">
                    <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div class="text-sm text-slate-600">
                    <span class="font-semibold text-blue-600">点击上传</span> 或将文件拖拽到此处
                  </div>
                  <p class="text-xs text-slate-400">支持 .zip 或 .skill 格式文件，将自动解析 SKILL.md</p>
                </div>
              </div>
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700">
                指令内容 <span class="text-red-500">*</span>
              </label>
              <div class="relative">
                <textarea 
                  v-model="newToolForm.content" 
                  rows="8" 
                  placeholder="当这个 Skill 被触发时，你希望模型遵循哪些规则或信息..." 
                  class="w-full px-4 py-3 font-mono text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-y placeholder:text-slate-400"
                ></textarea>
                <div class="absolute right-3 top-3 text-xs text-slate-400 bg-white/80 px-2 py-1 rounded backdrop-blur-sm border border-slate-100">
                  Markdown
                </div>
              </div>
              <p class="text-xs text-slate-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                建议包含命令、使用场景、输出解释及示例
              </p>
            </div>
          </div>

          <!-- MCP Specific: Config -->
          <div v-else class="space-y-2">
            <label class="block text-sm font-medium text-slate-700">
              MCP 配置 <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <textarea 
                v-model="newToolForm.mcp_config" 
                rows="6" 
                class="w-full px-4 py-3 font-mono text-sm bg-slate-900 text-slate-50 border border-slate-800 rounded-lg focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all resize-y"
                spellcheck="false"
              ></textarea>
              <div class="absolute right-3 top-3 text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded border border-slate-700">
                JSON
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-between items-center">
        <div class="text-xs text-slate-400">
          <span v-if="newToolForm.type === 'skill'">带 <span class="text-red-400">*</span> 为必填项</span>
        </div>
        <div class="flex gap-3">
          <button 
            @click="closeModal" 
            class="px-5 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 rounded-lg transition-colors shadow-sm"
          >
            取消
          </button>
          <button 
            @click="createTool" 
            :disabled="isSubmitting" 
            class="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded-lg shadow-sm hover:shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg v-if="isSubmitting" class="animate-spin -ml-1 mr-1 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isSubmitting ? '处理中...' : (isEditing ? '保存修改' : '确认创建') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import JSZip from 'jszip';

const menuItems = ref([]);

const activeCategory = ref('all');
const searchQuery = ref('');
const activeFilter = ref('all'); // all, hot, new, official
const isLoading = ref(false);
const showCreateToolModal = ref(false);
const isEditing = ref(false);
const editingId = ref(null);
const activeMenuId = ref(null);

// Local storage for installed tools
const getStoredInstalled = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem('installed_tools') || '[]'));
  } catch {
    return new Set();
  }
};
const installedTools = ref(getStoredInstalled());

const mcpItems = ref([]);
const skills = ref([]);
const isSubmitting = ref(false);

const handleInstall = async (item) => {
  if (item.installed || item.isInstalling) return;
  
  item.isInstalling = true;
  // Simulate network request
  await new Promise(resolve => setTimeout(resolve, 800));
  
  item.installed = true;
  item.isInstalling = false;
  
  installedTools.value.add(item.id);
  localStorage.setItem('installed_tools', JSON.stringify([...installedTools.value]));
};

const newToolForm = reactive({
  name: '',
  type: 'skill', // 'skill' or 'mcp'
  scope: 'global', // 'global' or 'project'
  version: '1.0.0',
  description: '',
  content: '',
  mcp_type: 'stdio',
  mcp_config: '{\n  "command": "python",\n  "args": ["server.py"]\n}',
  category: '' // default category
});

const closeModal = () => {
  showCreateToolModal.value = false;
  setTimeout(() => {
    resetForm();
  }, 200); // Wait for animation
};

const resetForm = () => {
  isEditing.value = false;
  editingId.value = null;
  newToolForm.name = '';
  newToolForm.type = 'skill';
  newToolForm.version = '1.0.0';
  newToolForm.description = '';
  newToolForm.content = '';
  newToolForm.mcp_type = 'stdio';
  newToolForm.mcp_config = '{\n  "command": "python",\n  "args": ["server.py"]\n}';
  newToolForm.category = '';
};

const toggleMenu = (id) => {
  if (activeMenuId.value === id) {
    activeMenuId.value = null;
  } else {
    activeMenuId.value = id;
  }
};

const openEditModal = (item) => {
  isEditing.value = true;
  editingId.value = item.id;
  
  newToolForm.type = item.type;
  newToolForm.name = item.name;
  newToolForm.version = item.version || '1.0.0';
  newToolForm.description = item.description || '';
  newToolForm.category = item.category || '';
  
  if (item.type === 'skill') {
    newToolForm.content = item.content || '';
    newToolForm.scope = item.meta_data?.scope || 'global';
  } else {
    newToolForm.mcp_type = item.type_code || 'stdio'; // Assuming item has type_code or we map from type
    // Backend returns 'type' as 'stdio' or 'sse' in MCPServer model, 
    // but in frontend item.type is overwritten to 'mcp'.
    // We need to check the original data or store it.
    // In fetchMcpServers, we spread ...item, so original type should be there but overwritten by type: 'mcp'.
    // We should fix fetchMcpServers to preserve original type.
    
    // Let's assume we fix fetchMcpServers below to store original type in mcp_type
    newToolForm.mcp_type = item.mcp_type || 'stdio';
    newToolForm.mcp_config = JSON.stringify(item.config || {}, null, 2);
  }
  
  showCreateToolModal.value = true;
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // Reset input value to allow re-uploading the same file if needed
  event.target.value = '';

  if (!file.name.endsWith('.zip') && !file.name.endsWith('.skill')) {
    alert("不支持的文件格式，请上传 .zip 或 .skill 文件");
    return;
  }

  try {
    const zip = await JSZip.loadAsync(file);
    
    const files = Object.keys(zip.files);
    
    // Helper to find file by name pattern, preferring shallowest path (root level first)
    const findFile = (pattern) => {
      const matches = files.filter(path => pattern.test(path) && !zip.files[path].dir);
      if (matches.length === 0) return null;
      // Sort by path depth (number of slashes), then by length to prefer shorter names
      matches.sort((a, b) => {
        const depthA = (a.match(/\//g) || []).length;
        const depthB = (b.match(/\//g) || []).length;
        if (depthA !== depthB) return depthA - depthB;
        return a.length - b.length;
      });
      return matches[0];
    };

    // Find SKILL.md (case insensitive, any depth)
    const skillMdPath = findFile(/(^|\/)skill\.md$/i);
    
    if (skillMdPath) {
      const content = await zip.file(skillMdPath).async("string");
      newToolForm.content = content;
      alert(`配置导入成功！已加载 ${skillMdPath}`);
    } else {
      alert("在压缩包中未找到 SKILL.md 文件。");
    }
    
    // Optional: Try to find metadata (manifest.json or package.json)
    const manifestPath = findFile(/(^|\/)(manifest\.json|package\.json)$/i);
    if (manifestPath) {
      try {
        const manifestStr = await zip.file(manifestPath).async("string");
        const manifest = JSON.parse(manifestStr);
        if (manifest.name) newToolForm.name = manifest.name;
        if (manifest.version) newToolForm.version = manifest.version;
        if (manifest.description) newToolForm.description = manifest.description;
      } catch (e) {
        console.warn("Failed to parse manifest", e);
      }
    }

  } catch (e) {
    console.error("Error reading file", e);
    alert("解析文件失败，请确认文件格式正确且未损坏");
  }
};

const fetchCategories = async () => {
  try {
    const res = await fetch('/api/v1/service-categories/');
    if (res.ok) {
      const data = await res.json();
      // Add 'All' category at the beginning manually if it's not from backend, 
      // or rely on backend. User said "Only 2 categories", but for UX "All" is usually implied as default view.
      // Let's stick to backend data. If backend returns only MCP and Skills, we might want to add 'All' locally for aggregation.
      menuItems.value = [{ id: 'all', label: '全部推荐' }, ...data.map(d => ({ id: d.slug, label: d.label }))];
      
      // Ensure 'all' is selected by default if not set
      if (!activeCategory.value) activeCategory.value = 'all';
    }
  } catch (e) {
    console.error("Failed to fetch categories", e);
  }
};

const buildQueryParams = () => {
  const params = new URLSearchParams();
  if (searchQuery.value) params.append('q', searchQuery.value);
  if (activeCategory.value && activeCategory.value !== 'all' && activeCategory.value !== 'mcp' && activeCategory.value !== 'skills') {
    params.append('category', activeCategory.value);
  }
  if (activeFilter.value !== 'all') {
    params.append('filter', activeFilter.value);
  }
  return params.toString();
};

const fetchMcpServers = async () => {
  // If category is 'skills', don't fetch MCP
  if (activeCategory.value === 'skills') {
    mcpItems.value = [];
    return;
  }
  
  try {
    const query = buildQueryParams();
    const res = await fetch(`/api/v1/mcp/?${query}`);
    if (res.ok) {
      const data = await res.json();
      mcpItems.value = data.map(item => ({
        ...item,
        type: 'mcp',
        mcp_type: item.type, // Preserve original type (stdio/sse)
        author: item.author || 'User Configured',
        iconUrl: '/tools/mcp.svg',
        bgColor: 'bg-purple-50',
        installed: installedTools.value.has(item.id),
        downloads: item.downloads || 0,
        is_official: item.is_official
      }));
    }
  } catch (e) {
    console.error("Failed to fetch MCP servers", e);
  }
};

const fetchSkills = async () => {
  // If category is 'mcp', don't fetch Skills
  if (activeCategory.value === 'mcp') {
    skills.value = [];
    return;
  }

  try {
    const query = buildQueryParams();
    const res = await fetch(`/api/v1/skills/?${query}`);
    if (res.ok) {
      const data = await res.json();
      skills.value = data.map(s => ({
        ...s,
        type: 'skill',
        author: s.author || 'System', 
        iconUrl: '/tools/skill.svg',
        bgColor: 'bg-green-50',
        installed: installedTools.value.has(s.id),
        downloads: s.downloads || 0,
        is_official: s.is_official
      }));
    }
  } catch (e) {
    console.error("Failed to fetch skills", e);
  }
};

const refreshData = async () => {
  isLoading.value = true;
  await Promise.all([fetchSkills(), fetchMcpServers()]);
  isLoading.value = false;
};

// Watchers to trigger refresh when filters change
import { watch } from 'vue';
watch([activeCategory, activeFilter], () => {
  refreshData();
});

// Debounced search
let searchTimeout;
watch(searchQuery, () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    refreshData();
  }, 500);
});

const createTool = async () => {
  // Basic validation
  if (!newToolForm.name) {
    alert("请输入工具名称");
    return;
  }
  if (!newToolForm.version) {
    alert("请输入版本号");
    return;
  }
  
  if (newToolForm.type === 'skill' && !newToolForm.content) {
    alert("请输入技能指令内容");
    return;
  }

  isSubmitting.value = true;
  
  try {
    let url = '';
    let body = {};
    
    // Common fields
    const common = {
      name: newToolForm.name,
      description: newToolForm.description,
      category: newToolForm.category
    };
    
    if (newToolForm.type === 'skill') {
      url = isEditing.value ? `/api/v1/skills/${editingId.value}` : '/api/v1/skills/';
      body = {
        ...common,
        version: newToolForm.version,
        content: newToolForm.content,
        is_active: true,
        meta_data: { scope: newToolForm.scope }
      };
    } else {
      url = isEditing.value ? `/api/v1/mcp/${editingId.value}` : '/api/v1/mcp/';
      let config = {};
      try {
        config = JSON.parse(newToolForm.mcp_config);
      } catch (e) {
        alert("Invalid JSON in Config");
        isSubmitting.value = false;
        return;
      }
      body = {
        ...common,
        type: newToolForm.mcp_type,
        config: config,
        version: newToolForm.version,
        is_active: true
      };
    }
    
    const res = await fetch(url, {
      method: isEditing.value ? 'PUT' : 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    
    if (res.ok) {
      closeModal();
      refreshData();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Failed to save'}`);
    }
  } catch (e) {
    console.error(e);
    alert("Network Error");
  } finally {
    isSubmitting.value = false;
  }
};

const deleteTool = async (item) => {
  if (!confirm(`Are you sure you want to delete ${item.name}?`)) return;
  
  try {
    const url = item.type === 'skill' 
      ? `/api/v1/skills/${item.id}` 
      : `/api/v1/mcp/${item.id}`;
      
    const res = await fetch(url, { method: 'DELETE' });
    if (res.ok) {
      refreshData();
    } else {
      alert("Failed to delete");
    }
  } catch (e) {
    console.error(e);
    alert("Network Error");
  }
};

const filteredItems = computed(() => {
  // Client-side merging only, filtering is done server-side
  return [...mcpItems.value, ...skills.value];
});

onMounted(async () => {
  await fetchCategories();
  refreshData();
});
</script>
