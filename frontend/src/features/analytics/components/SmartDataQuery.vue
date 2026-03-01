<template>
  <div class="h-full flex bg-white overflow-hidden">
    <!-- Sidebar -->
    <div class="bg-white flex flex-col flex-shrink-0 overflow-hidden" :style="{ width: leftWidth + 'px' }">
        <!-- Toggle -->
        <div class="p-4">
          <div class="inline-flex p-1 bg-slate-100 rounded-lg">
            <button
              @click="leftTab = 'sessions'"
              :class="leftTab === 'sessions' ? 'bg-white shadow text-slate-900' : 'text-slate-600'"
              class="px-3 py-1.5 text-xs rounded-md transition-colors"
              aria-label="会话"
            >会话</button>
            <button
              @click="leftTab = 'config'"
              :class="leftTab === 'config' ? 'bg-white shadow text-slate-900' : 'text-slate-600'"
              class="px-3 py-1.5 text-xs rounded-md transition-colors"
              aria-label="数据库配置"
            >数据库配置</button>
          </div>
        </div>
        
        <!-- Sessions Panel -->
        <div v-show="leftTab === 'sessions'" class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <div class="flex items-center gap-2 mb-3 sticky top-0 bg-white z-10 pb-2">
            <a-input v-model:value="sessionSearch" placeholder="搜索会话..." allowClear />
            <button 
              @click="handleCreateSession"
              class="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors flex items-center justify-center"
              title="新建会话"
              aria-label="新建会话"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M12 5v14M5 12h14" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
              </svg>
            </button>
          </div>
          <div class="text-[11px] text-slate-500 mb-2">共 {{ filteredSessions.length }} 个会话</div>
          <div class="space-y-1">
            <div
              v-for="s in filteredSessions"
              :key="s.id"
              @click="selectSession(s.id)"
              class="group px-3 py-2 rounded-lg cursor-pointer transition-all"
              :class="[activeSessionId === s.id ? 'bg-blue-50' : 'hover:bg-slate-50']"
            >
              <div class="flex items-center justify-between">
                <div class="text-sm font-medium text-slate-800 truncate">
                  <span v-if="s.is_pinned" class="text-amber-600 mr-1">★</span>{{ s.title || '未命名会话' }}
                  <span v-if="s.is_archived" class="ml-2 text-[10px] text-slate-500">已归档</span>
                </div>
                <div class="opacity-0 group-hover:opacity-100 transition-opacity text-[11px] text-blue-600 flex gap-2">
                  <a @click.stop="handleRenameSession(s)">重命名</a>
                  <a @click.stop="togglePin(s)">{{ s.is_pinned ? '取消置顶' : '置顶' }}</a>
                  <a @click.stop="toggleArchive(s)">{{ s.is_archived ? '取消归档' : '归档' }}</a>
                  <a class="text-red-500" @click.stop="handleDeleteSession(s)">删除</a>
                </div>
              </div>
              <div class="mt-0.5 flex items-center text-[11px] text-slate-500">
                <span class="truncate">{{ s.last_message_preview || '暂无消息' }}</span>
                <span class="ml-auto flex-none pl-2 text-slate-400">{{ formatRelative(s.updated_at || s.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Config Panel -->
        <div v-show="leftTab === 'config'" class="p-6 overflow-y-auto custom-scrollbar">
        <h2 class="text-lg font-bold mb-6 flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
            数据库配置
        </h2>
        
        <a-form 
            ref="formRef"
            :model="config" 
            :rules="rules"
            layout="vertical" 
            class="space-y-4"
        >
            <a-form-item label="数据库类型" name="type">
                <a-select v-model:value="config.type" @change="handleTypeChange">
                    <a-select-option value="sqlite">SQLite</a-select-option>
                    <a-select-option value="postgresql">PostgreSQL</a-select-option>
                    <a-select-option value="mysql">MySQL</a-select-option>
                </a-select>
            </a-form-item>
            
            <template v-if="config.type === 'sqlite'">
                <a-form-item label="文件路径" name="path" help="请输入SQLite数据库文件的绝对路径">
                    <a-input v-model:value="config.path" placeholder="e.g. C:/data/app.db" />
                </a-form-item>
            </template>
            
            <template v-else>
                <div class="grid grid-cols-3 gap-3">
                    <div class="col-span-2">
                        <a-form-item label="主机地址" name="host">
                            <a-input v-model:value="config.host" placeholder="localhost" />
                        </a-form-item>
                    </div>
                    <div>
                        <a-form-item label="端口" name="port">
                            <a-input-number v-model:value="config.port" class="w-full" :controls="false" />
                        </a-form-item>
                    </div>
                </div>
                
                <a-form-item label="用户名" name="user">
                    <a-input v-model:value="config.user" placeholder="root" />
                </a-form-item>
                
                <a-form-item label="密码" name="password">
                    <a-input-password v-model:value="config.password" placeholder="请输入密码" />
                </a-form-item>

                <!-- Advanced Options Toggle -->
                <div class="pt-2">
                    <div 
                        @click="showAdvanced = !showAdvanced" 
                        class="flex items-center gap-1 text-xs text-blue-600 cursor-pointer hover:text-blue-700 select-none font-medium"
                    >
                        <span>更多连接配置</span>
                        <svg class="w-3 h-3 transition-transform duration-200" :class="showAdvanced ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </div>
                    
                    <div v-show="showAdvanced" class="mt-4 space-y-4 p-4 bg-slate-50 rounded-xl animate-in fade-in slide-in-from-top-2 duration-200">
                        <a-form-item label="数据库名称" name="database">
                            <a-input v-model:value="config.database" placeholder="选填，默认连接postgres/mysql" />
                        </a-form-item>
                        
                        <div class="grid grid-cols-2 gap-3">
                            <a-form-item label="连接超时 (秒)" name="timeout">
                                <a-input-number v-model:value="config.timeout" class="w-full" :min="1" />
                            </a-form-item>
                            
                            <a-form-item label="连接池大小" name="pool_size">
                                <a-input-number v-model:value="config.pool_size" class="w-full" :min="1" />
                            </a-form-item>
                        </div>
                        
                        <a-form-item v-if="config.type === 'mysql'" label="字符集" name="charset">
                            <a-select v-model:value="config.charset">
                                <a-select-option value="utf8mb4">utf8mb4</a-select-option>
                                <a-select-option value="utf8">utf8</a-select-option>
                                <a-select-option value="latin1">latin1</a-select-option>
                            </a-select>
                        </a-form-item>
                        
                        <a-form-item v-if="config.type === 'postgresql'" label="SSL 模式" name="ssl_mode">
                            <a-select v-model:value="config.ssl_mode">
                                <a-select-option value="disable">Disable</a-select-option>
                                <a-select-option value="require">Require</a-select-option>
                                <a-select-option value="verify-ca">Verify CA</a-select-option>
                                <a-select-option value="verify-full">Verify Full</a-select-option>
                            </a-select>
                        </a-form-item>
                    </div>
                </div>
            </template>
            
            <div class="flex flex-col gap-3 pt-4 mt-4">
                <a-button @click="testConnection" :loading="testing" class="w-full" :disabled="connecting">
                    <template #icon>
                        <svg class="w-4 h-4 mr-2 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    </template>
                    测试连接
                </a-button>
                
                <a-button type="primary" @click="saveAndConnect" :loading="connecting" class="w-full h-10 font-medium bg-blue-600" :disabled="testing">
                    保存配置并连接
                </a-button>
            </div>
        </a-form>
        
        <!-- Status Messages -->
        <div v-if="testResult" class="mt-4 p-3 rounded-lg text-xs flex items-start gap-2" :class="testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
            <component :is="testResult.success ? 'CheckCircleOutlined' : 'CloseCircleOutlined'" class="mt-0.5" />
            <span class="break-all">{{ testResult.message }}</span>
        </div>
        
        <div class="mt-8 p-4 bg-blue-50 text-blue-700 text-xs rounded-xl leading-relaxed">
            <p class="font-bold mb-2 flex items-center gap-1">
                <InfoCircleOutlined /> 使用提示
            </p>
            <p>连接成功后，您可以直接使用自然语言查询数据。</p>
            <p class="mt-2 font-medium">示例指令：</p>
            <ul class="list-disc pl-4 mt-1 space-y-1 text-blue-600">
                <li>"查询最近10笔销售记录"</li>
                <li>"统计各类目的销售总额"</li>
                <li>"绘制月度销售趋势图"</li>
            </ul>
        </div>
        </div>
    </div>
    
    <!-- Resize Handle -->
    <div 
      class="w-1 hover:bg-slate-200 cursor-col-resize flex-shrink-0 border-r border-slate-200"
      :class="isResizing ? 'bg-slate-200' : 'bg-transparent'"
      @mousedown="startResizing"
      title="拖拽调整侧栏宽度"
      aria-label="拖拽调整侧栏宽度"
    ></div>
      
    <!-- Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-white relative">
        <div class="px-6 py-3 flex items-center gap-3 sticky top-0 bg-white/90 backdrop-blur z-10">
            <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold text-slate-800 truncate">{{ currentSession?.title || '未命名会话' }}</div>
                <div class="text-[11px] text-slate-500 truncate">
                    <span v-if="currentSession" :title="formatAbsolute(currentSession.updated_at || currentSession.created_at)">
                        最近活跃：{{ formatRelative(currentSession.updated_at || currentSession.created_at) }}
                    </span>
                    <span v-else>未选择会话</span>
                </div>
            </div>
            <div v-if="currentSession" class="flex items-center gap-2 text-[11px]">
                <a @click="handleRenameSession(currentSession)" class="text-blue-600">重命名</a>
                <a @click="togglePin(currentSession)" class="text-blue-600">{{ currentSession.is_pinned ? '取消置顶' : '置顶' }}</a>
                <a @click="toggleArchive(currentSession)" class="text-blue-600">{{ currentSession.is_archived ? '取消归档' : '归档' }}</a>
                <a @click="handleDeleteSession(currentSession)" class="text-red-500">删除</a>
            </div>
        </div>
        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6" ref="messagesContainer">
             <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400">
                <div class="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-sm mb-6">
                    <svg class="w-10 h-10 text-blue-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                </div>
                <h3 class="text-lg font-semibold text-slate-700 mb-2">智能问数助手</h3>
                <p class="text-sm max-w-xs text-center leading-relaxed">配置数据库并开始提问，我会自动为您生成 SQL 查询并可视化结果。</p>
             </div>
             
            <div v-for="(msg, index) in messages" :key="msg._id || index" 
                 :class="['flex gap-4 max-w-4xl mx-auto', msg.role === 'user' ? 'flex-row-reverse' : '']">
                <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                     :class="msg.role === 'user' ? 'bg-blue-600' : 'bg-white'">
                     <span v-if="msg.role === 'user'" class="text-white text-xs font-bold">Me</span>
                     <svg v-else class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                <div :class="['rounded-2xl shadow-sm text-sm leading-relaxed max-w-[90%] overflow-hidden', 
                              msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm px-5 py-3.5' : 'bg-white text-slate-700 rounded-tl-sm w-full border border-slate-100']">
                    <div v-if="msg.role === 'assistant'" class="flex flex-col">
                        <!-- 1. Process Nodes (Collapsible) -->
                        <div class="border-b border-slate-100">
                            <button 
                                @click="toggleProcess(msg._id)"
                                class="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 hover:bg-slate-100 transition-colors"
                            >
                                <div class="flex items-center gap-2 text-xs font-medium text-slate-600">
                                    <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                    <span>思考过程</span>
                                </div>
                                <svg 
                                    class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200"
                                    :class="isProcessExpanded(msg._id) ? 'rotate-180' : ''"
                                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                >
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            <div v-show="isProcessExpanded(msg._id)" class="bg-slate-50 px-4 py-3 border-t border-slate-100 animate-in slide-in-from-top-1">
                                <div class="space-y-3">
                                    <div v-for="(step, sIdx) in (msg.steps || [])" :key="step.step" class="flex gap-3">
                                        <div class="flex flex-col items-center">
                                            <div class="w-2 h-2 rounded-full mt-1.5" 
                                                 :class="sIdx === (msg.steps || []).length - 1 && isStreaming ? 'bg-blue-500 animate-pulse' : 'bg-blue-500'"></div>
                                            <div v-if="sIdx < (msg.steps || []).length - 1" class="w-0.5 h-full bg-slate-200 my-1"></div>
                                        </div>
                                        <div class="pb-2 min-w-0 flex-1">
                                            <div class="text-xs font-medium text-slate-700 flex justify-between">
                                                <span>步骤 {{ step.step }}</span>
                                                <span class="text-slate-400 font-normal">{{ formatRelative(step.timestamp) }}</span>
                                            </div>
                                            <div class="text-[11px] text-slate-500 mt-0.5 break-words whitespace-pre-wrap font-mono bg-white border border-slate-200 p-2 rounded shadow-sm" 
                                                 v-if="step.content && step.content.trim()">
                                                {{ step.content.trim() }}
                                            </div>
                                        </div>
                                    </div>
                                    <div v-if="(!msg.steps || msg.steps.length === 0) && isStreaming" class="text-xs text-slate-400 italic px-2">
                                        正在初始化流程...
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 2. Content Area with View Switcher -->
                        <div class="p-4">
                            <!-- Loading Skeleton -->
                            <div v-if="isStreaming && !msg.content && !msg.error_message" class="space-y-6 animate-pulse p-4">
                                <!-- Table Skeleton -->
                                <div class="space-y-4">
                                    <div class="h-4 bg-slate-200 rounded w-1/4"></div>
                                    <div class="border border-slate-200 rounded-lg overflow-hidden">
                                        <div class="h-10 bg-slate-100 border-b border-slate-200"></div>
                                        <div class="p-4 space-y-3">
                                            <div class="h-3 bg-slate-100 rounded w-full"></div>
                                            <div class="h-3 bg-slate-100 rounded w-full"></div>
                                            <div class="h-3 bg-slate-100 rounded w-3/4"></div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Chart Skeleton -->
                                <div class="space-y-4">
                                    <div class="h-4 bg-slate-200 rounded w-1/5"></div>
                                    <div class="h-64 bg-slate-50 rounded-xl border border-slate-200"></div>
                                </div>
                            </div>

                            <!-- Toolbar -->
                            <div class="flex items-center justify-between mb-3" v-if="msg.sql_query && (msg.content || !isStreaming)">
                                <div class="text-xs text-slate-400 font-medium">查询结果</div>
                                <div class="flex bg-slate-100 p-0.5 rounded-lg">
                                    <button 
                                        @click="setMsgViewMode(msg._id, 'table')"
                                        :class="getMsgViewMode(msg._id) === 'table' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                                        class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all"
                                    >
                                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7-8v8m14-8v8M5 21h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
                                        表格视图
                                    </button>
                                    <button 
                                        @click="setMsgViewMode(msg._id, 'sql')"
                                        :class="getMsgViewMode(msg._id) === 'sql' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                                        class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all"
                                    >
                                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                                        SQL查询
                                    </button>
                                </div>
                            </div>

                            <!-- View Content -->
                            <div class="min-h-[60px]">
                                <!-- Table View (Markdown) -->
                                <div v-show="getMsgViewMode(msg._id) === 'table'" class="markdown-body" v-html="renderMarkdown(getMessageText(msg.content))"></div>
                                
                                <!-- SQL View -->
                                <div v-show="getMsgViewMode(msg._id) === 'sql'" class="relative group/sql">
                                    <pre class="p-3 text-xs text-slate-800 bg-slate-50 rounded-lg border border-slate-200 overflow-x-auto font-mono"><code>{{ msg.sql_query }}</code></pre>
                                    <button
                                      @click="copySql(msg.sql_query)"
                                      class="absolute top-2 right-2 p-1.5 rounded-md bg-white shadow-sm border border-slate-200 text-slate-500 opacity-0 group-hover/sql:opacity-100 transition-opacity hover:text-blue-600"
                                      title="复制 SQL"
                                    >
                                      <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M8 16H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2m-6 4h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                                    </button>
                                </div>
                            </div>

                            <!-- 3. Chart Content (Bottom) -->
                            <div v-if="msg.chart_config || getMessageChart(msg.content)" class="mt-5 pt-5 border-t border-slate-100">
                                <div class="flex items-center gap-2 mb-3">
                                    <svg class="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
                                    <span class="text-xs font-bold text-slate-700">可视化图表</span>
                                </div>
                                <div class="h-80 w-full bg-white rounded-xl p-4 border border-slate-100 shadow-sm hover:shadow-md transition-shadow duration-200">
                                    <v-chart class="chart" :option="processChartOption(msg.chart_config || getMessageChart(msg.content))" autoresize />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-else>{{ msg.content }}</div>
                </div>
            </div>
            
            <!-- Loading -->
            <div v-if="isLoading && !isStreaming" class="flex gap-4 max-w-4xl mx-auto">
                 <div class="w-8 h-8 rounded-full bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                     <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                 </div>
                 <div class="bg-white rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm flex items-center gap-2">
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></span>
                 </div>
            </div>
        </div>
        
        <!-- Input -->
        <div class="p-4 bg-white z-10">
            <div class="max-w-4xl mx-auto">
                <div class="relative">
                    <textarea 
                      v-model="input" 
                      @keydown.enter.exact.prevent="sendMessage"
                      @input="autoResize"
                      ref="textareaRef"
                      rows="3"
                      placeholder="输入您的问题..."
                      class="w-full pl-4 pr-28 py-3.5 bg-transparent border border-slate-200 rounded-xl outline-none resize-none text-sm text-slate-700 placeholder-slate-400 transition-all max-h-48 overflow-y-auto focus:border-blue-400"
                      :disabled="isLoading"
                    ></textarea>
                    <div class="absolute right-2 bottom-2 flex items-center gap-2">
                        <button 
                          @click="sendMessage"
                          class="p-2 rounded-lg transition-all duration-200"
                          :class="input.trim() && !isLoading ? 'text-blue-600 hover:text-blue-700 hover:bg-blue-50' : 'text-slate-300 cursor-not-allowed'"
                          :disabled="isLoading || !input.trim()"
                          aria-label="发送"
                        >
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path d="M22 2 11 13" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                              <path d="M22 2 15 22 11 13 2 9 22 2" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <!-- Icon Toolbar -->
                <div class="flex items-center justify-between mt-2">

                    <div class="text-[10px] text-slate-400">
                      <span>{{ input.length }}/2000</span>
                    </div>
                </div>
                <p class="text-center text-[10px] text-slate-400 mt-2">智能问数 ·Tiga AI驱动</p>
            </div>
        </div>
    </div>
  </div>

  <a-modal 
    v-model:open="createModalOpen" 
    title="新建会话"
    :confirmLoading="createLoading"
    @ok="confirmCreateSession"
    @cancel="closeCreateModal"
    destroyOnClose
  >
    <a-input v-model:value="createForm.title" placeholder="请输入会话标题" />
  </a-modal>

  <a-modal 
    v-model:open="renameModalOpen" 
    title="重命名会话"
    :confirmLoading="renameLoading"
    @ok="confirmRenameSession"
    @cancel="closeRenameModal"
    destroyOnClose
  >
    <a-input v-model:value="renameForm.title" placeholder="请输入新标题" />
  </a-modal>

  <a-modal
    v-model:open="deleteModalOpen"
    title="删除会话"
    okType="danger"
    :okText="'删除'"
    :confirmLoading="deleteLoading"
    @ok="confirmDeleteSession"
    @cancel="closeDeleteModal"
    destroyOnClose
  >
    <div class="text-slate-600 text-sm">确定要删除该会话吗？此操作不可恢复。</div>
  </a-modal>
</template>

<script setup>
import { ref, nextTick, onMounted, reactive, computed } from 'vue';
import { message } from 'ant-design-vue';
import { marked } from 'marked';
import { CheckCircleOutlined, CloseCircleOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';
import VChart from 'vue-echarts';
import 'echarts';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';
import 'dayjs/locale/zh-cn';

// Session panel state
const leftTab = ref('sessions'); // 'sessions' | 'config'
const sessions = ref([]);
const sessionSearch = ref('');
const activeSessionId = ref(null);
const sessionsLoading = ref(false);
const expandedProcess = ref(new Set());
const msgViewModes = reactive({});

dayjs.extend(relativeTime);
dayjs.extend(utc);
dayjs.locale('zh-cn');

const formRef = ref();
const config = ref({
    type: 'sqlite',
    path: '',
    host: 'localhost',
    port: 5432,
    database: '',
    user: '',
    password: '',
    timeout: 30,
    pool_size: 5,
    charset: 'utf8mb4',
    ssl_mode: 'disable'
});

const showAdvanced = ref(false);
const testing = ref(false);
const connecting = ref(false);
const testResult = ref(null);
const input = ref('');
const messages = ref([]);
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);
const currentController = ref(null);
const textareaRef = ref(null);

const autoResize = () => {
    const el = textareaRef.value;
    if (!el) return;
    el.style.height = 'auto';
    const max = 192; // 48 * 4 = 192px => max-h-48
    const next = Math.min(el.scrollHeight, max);
    el.style.height = next + 'px';
};

// Toolbar state & helpers
const templatesOpen = ref(false);
const templates = [
    { name: '统计最近7日销售总额', content: '统计最近7天的销售总额，并按天汇总后画折线图' },
    { name: '品类销售排行Top5', content: '按品类统计销售额，取Top5并绘制柱状图' },
    { name: '大客户贡献度', content: '统计按客户维度的销售额，按降序排序并展示前10名' }
];
const clearInput = () => { input.value = ''; autoResize(); };
const insertTemplate = (text) => {
    const cur = input.value || '';
    input.value = cur ? (cur.endsWith('\n') ? cur + text : cur + '\n' + text) : text;
    autoResize();
    templatesOpen.value = false;
};

// Resizable left pane
const leftWidth = ref(384); // default 24rem
const isResizing = ref(false);
const startX = ref(0);
const startWidth = ref(leftWidth.value);
const MIN_LEFT = 280;
const MAX_LEFT = 640;
const clamp = (v, min, max) => Math.min(Math.max(v, min), max);
const onMouseMove = (e) => {
    const dx = e.clientX - startX.value;
    leftWidth.value = clamp(startWidth.value + dx, MIN_LEFT, MAX_LEFT);
};
const stopResizing = () => {
    if (!isResizing.value) return;
    isResizing.value = false;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', stopResizing);
    try { document.body.style.userSelect = ''; } catch {}
};
const startResizing = (e) => {
    isResizing.value = true;
    startX.value = e.clientX;
    startWidth.value = leftWidth.value;
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', stopResizing);
    try { document.body.style.userSelect = 'none'; } catch {}
};

const createModalOpen = ref(false);
const createLoading = ref(false);
const createForm = reactive({ title: '新的会话' });
const renameModalOpen = ref(false);
const renameLoading = ref(false);
const renameForm = reactive({ title: '' });
const deleteModalOpen = ref(false);
const deleteLoading = ref(false);
const targetSession = ref(null);

const rules = computed(() => {
    const baseRules = {
        type: [{ required: true, message: '请选择数据库类型' }],
        database: [{ required: false }]
    };

    if (config.value.type === 'sqlite') {
        return {
            ...baseRules,
            path: [{ required: true, message: '请输入文件路径', trigger: 'blur' }]
        };
    } else {
        return {
            ...baseRules,
            host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
            port: [{ required: true, message: '请输入端口号' }],
            user: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
        };
    }
});

const formatRelative = (ts) => {
    try {
        if (!ts) return '';
        return dayjs.utc(ts).local().fromNow();
    } catch {
        return '';
    }
};

const formatAbsolute = (ts) => {
    try {
        if (!ts) return '';
        return dayjs.utc(ts).local().format('YYYY-MM-DD HH:mm:ss');
    } catch {
        return '';
    }
};

const isProcessExpanded = (id) => expandedProcess.value.has(id);
const toggleProcess = (id) => {
    if (expandedProcess.value.has(id)) {
        expandedProcess.value.delete(id);
    } else {
        expandedProcess.value.add(id);
    }
};

const getMsgViewMode = (id) => msgViewModes[id] || 'table';
const setMsgViewMode = (id, mode) => {
    msgViewModes[id] = mode;
};

const handleTypeChange = (val) => {
    // Set default ports
    if (val === 'postgresql') config.value.port = 5432;
    if (val === 'mysql') config.value.port = 3306;
    if (val === 'sqlite') config.value.port = null;
    testResult.value = null;
};

const fetchConfig = async () => {
    try {
        const res = await fetch('/api/v1/data_query/config');
        if (res.ok) {
            const data = await res.json();
            if (Object.keys(data).length > 0) {
                config.value = { ...config.value, ...data };
            }
        }
    } catch (e) {
        console.error("Failed to load config", e);
    }
};

const testConnection = async () => {
    testResult.value = null;
    try {
        await formRef.value.validate();
    } catch (error) {
        return;
    }
    
    testing.value = true;
    try {
        const res = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (res.ok) {
            testResult.value = { success: true, message: '连接测试成功！' };
            message.success('连接测试成功');
        } else {
            const err = await res.json();
            testResult.value = { success: false, message: '连接失败: ' + (err.detail || '未知错误') };
            message.error('连接测试失败');
        }
    } catch (e) {
        testResult.value = { success: false, message: '网络错误: ' + e.message };
        message.error('连接测试失败');
    } finally {
        testing.value = false;
    }
};

const saveAndConnect = async () => {
    try {
        await formRef.value.validate();
    } catch (error) {
        return;
    }
    
    connecting.value = true;
    testResult.value = null;
    
    // 1. Connect
    try {
        const connRes = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (!connRes.ok) {
            const err = await connRes.json();
            throw new Error(err.detail || '连接失败');
        }
        
        // 2. Save Config
        const saveRes = await fetch('/api/v1/data_query/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (!saveRes.ok) {
            message.warning('连接成功，但配置保存失败');
        } else {
            message.success('配置已保存并连接成功');
        }
        
        testResult.value = { success: true, message: '已连接并就绪' };
        
    } catch (e) {
        testResult.value = { success: false, message: e.message };
        message.error(e.message);
    } finally {
        connecting.value = false;
    }
};

// ---- Session helpers ----
const fetchSessions = async () => {
    sessionsLoading.value = true;
    try {
        const res = await fetch('/api/v1/data_query/sessions?status=active&limit=100&offset=0&user_id=default_user');
        if (res.ok) {
            const data = await res.json();
            sessions.value = Array.isArray(data.items) ? data.items : [];
        }
    } catch (e) {
        console.error('Failed to fetch sessions', e);
    } finally {
        sessionsLoading.value = false;
    }
};

const filteredSessions = computed(() => {
    const q = (sessionSearch.value || '').toLowerCase();
    const base = sessions.value.slice().filter(s =>
        !q ||
        (s.title || '').toLowerCase().includes(q) ||
        (s.last_message_preview || '').toLowerCase().includes(q)
    );
    // Sort: pinned first, then by recent activity (updated_at -> created_at)
    base.sort((a, b) => {
        if (a.is_pinned !== b.is_pinned) {
            return b.is_pinned ? 1 : -1; // true first
        }
        const ta = Date.parse(a?.updated_at || a?.created_at || 0) || 0;
        const tb = Date.parse(b?.updated_at || b?.created_at || 0) || 0;
        return tb - ta; // recent first
    });
    return base;
});

const handleCreateSession = async () => {
    createLoading.value = true;
    try {
        const res = await fetch('/api/v1/data_query/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: '新的会话', user_id: 'default_user' })
        });
        if (!res.ok) throw new Error('创建失败');
        let created = null;
        try { created = await res.json(); } catch {}
        if (created && created.id) {
            sessions.value.unshift(created);
            activeSessionId.value = created.id;
            messages.value = []; // Clear messages for new session
            await loadSessionMessages(created.id);
        }
        message.success('已创建会话');
        leftTab.value = 'sessions';
    } catch (e) {
        message.error(e.message || '创建失败');
    } finally {
        createLoading.value = false;
    }
};
const closeCreateModal = () => { createModalOpen.value = false; };
const confirmCreateSession = async () => {
    // Deprecated
};

const handleRenameSession = (s) => {
    targetSession.value = s;
    renameForm.title = s.title || '未命名会话';
    renameModalOpen.value = true;
};
const closeRenameModal = () => { renameModalOpen.value = false; targetSession.value = null; };
const confirmRenameSession = async () => {
    if (!targetSession.value) return;
    const newTitle = (renameForm.title || '').trim();
    if (!newTitle) {
        message.warning('请输入新标题');
        return;
    }
    renameLoading.value = true;
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${targetSession.value.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        if (!res.ok) throw new Error('重命名失败');
        const updated = await res.json();
        const idx = sessions.value.findIndex(it => it.id === targetSession.value.id);
        if (idx >= 0) sessions.value[idx] = updated;
        message.success('已重命名');
        renameModalOpen.value = false;
        targetSession.value = null;
    } catch (e) {
        message.error(e.message || '重命名失败');
    } finally {
        renameLoading.value = false;
    }
};

const togglePin = async (s) => {
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${s.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_pinned: !s.is_pinned })
        });
        if (!res.ok) throw new Error('操作失败');
        const updated = await res.json();
        const idx = sessions.value.findIndex(it => it.id === s.id);
        if (idx >= 0) sessions.value[idx] = updated;
        message.success(updated.is_pinned ? '已置顶' : '已取消置顶');
    } catch (e) {
        message.error(e.message || '操作失败');
    }
};

const toggleArchive = async (s) => {
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${s.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_archived: !s.is_archived })
        });
        if (!res.ok) throw new Error('操作失败');
        const updated = await res.json();
        const idx = sessions.value.findIndex(it => it.id === s.id);
        if (idx >= 0) sessions.value[idx] = updated;
        message.success(updated.is_archived ? '已归档' : '已取消归档');
    } catch (e) {
        message.error(e.message || '操作失败');
    }
};

const handleDeleteSession = (s) => {
    targetSession.value = s;
    deleteModalOpen.value = true;
};
const closeDeleteModal = () => { deleteModalOpen.value = false; targetSession.value = null; };
const confirmDeleteSession = async () => {
    if (!targetSession.value) return;
    deleteLoading.value = true;
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${targetSession.value.id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('删除失败');
        sessions.value = sessions.value.filter(it => it.id !== targetSession.value.id);
        if (activeSessionId.value === targetSession.value.id) {
            activeSessionId.value = null;
            messages.value = [];
        }
        message.success('已删除');
        deleteModalOpen.value = false;
        targetSession.value = null;
    } catch (e) {
        message.error(e.message || '删除失败');
    } finally {
        deleteLoading.value = false;
    }
};

const loadSessionMessages = async (id) => {
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${id}/messages`);
        if (!res.ok) throw new Error('加载消息失败');
        const data = await res.json();
        const items = Array.isArray(data.items) ? data.items : [];
        messages.value = items.map(m => ({
            _id: m.id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: m.role,
            content: m.content || '',
            sql_query: m.sql_query || null,
            chart_config: m.chart_config || null
        }));
        await nextTick();
        scrollToBottom();
    } catch (e) {
        console.error(e);
        message.error(e.message || '加载消息失败');
    }
};

const selectSession = async (id) => {
    activeSessionId.value = id;
    await loadSessionMessages(id);
};

const currentSession = computed(() => {
    if (!activeSessionId.value) return null;
    return sessions.value.find(s => s.id === activeSessionId.value) || null;
});

const sendMessage = async () => {
    if (!input.value.trim() || isLoading.value) return;
    const userMsg = input.value;
    input.value = '';
    if (textareaRef.value) {
        textareaRef.value.style.height = 'auto';
    }
    messages.value.push({ _id: `msg_${Date.now()}_user`, role: 'user', content: userMsg });
    isLoading.value = true;
    scrollToBottom();
    
    // Add placeholder for assistant response
    messages.value.push({ 
        _id: `msg_${Date.now()}_assistant`, 
        role: 'assistant', 
        content: '',
        steps: [],
        currentStep: 0
    });
    const assistantMsg = messages.value[messages.value.length - 1];

    try {
        // Auto create session if not selected
        if (!activeSessionId.value) {
            try {
                const title = userMsg.slice(0, 20);
                const resCreate = await fetch('/api/v1/data_query/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, user_id: 'default_user' })
                });
                if (resCreate && resCreate.ok) {
                    let created = null;
                    try { created = await resCreate.json(); } catch {}
                    if (created && created.id) {
                        sessions.value.unshift(created);
                        activeSessionId.value = created.id;
                    }
                }
            } catch (_) { /* non-blocking */ }
        }
        currentController.value = new AbortController();
        const response = await fetch('/api/v1/data_query/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userMsg, session_id: activeSessionId.value || null }),
            signal: currentController.value.signal
        });
        
        if (!response.ok) throw new Error(response.statusText);
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        isStreaming.value = true;
        
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the last incomplete line
            
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const stepData = JSON.parse(line);
                     if (stepData.step && stepData.content) {
                        stepData.timestamp = Date.now();
                        assistantMsg.steps.push(stepData);
                        assistantMsg.currentStep = stepData.step;
                        
                        // Only append to display content if it is data or chart or error
                        if (['data', 'chart', 'error'].includes(stepData.type)) {
                             assistantMsg.content += stepData.content;
                        }
                        
                        if (stepData.type === 'sql') {
                            const sqlMatch = stepData.content.match(/```sql\n([\s\S]*?)\n```/);
                            if (sqlMatch && sqlMatch[1]) {
                                assistantMsg.sql_query = sqlMatch[1].trim();
                            } else {
                                // If regex fails, assume it's just the SQL (or handle as is)
                                // But service sends ```sql...
                                assistantMsg.sql_query = stepData.content.replace(/```sql|```/g, '').trim();
                            }
                        }
                    }
                } catch (e) {
                    console.warn('Failed to parse step JSON', e);
                    // Fallback: treat as raw text if JSON parse fails (though backend should be consistent)
                    // assistantMsg.content += line + '\n';
                }
            }
            scrollToBottom();
        }
        
        // Process remaining buffer
         if (buffer.trim()) {
             try {
                 const stepData = JSON.parse(buffer);
                 if (stepData.step && stepData.content) {
                    stepData.timestamp = Date.now();
                    assistantMsg.steps.push(stepData);
                    assistantMsg.currentStep = stepData.step;
                    
                    if (['data', 'chart', 'error'].includes(stepData.type)) {
                         assistantMsg.content += stepData.content;
                    }
                    if (stepData.type === 'sql') {
                        assistantMsg.sql_query = stepData.content.replace(/```sql|```/g, '').trim();
                    }
                }
             } catch (e) {
                  // ignore or append as text
             }
         }
        
    } catch (e) {
        if (!assistantMsg.content) {
             assistantMsg.content = 'Error: ' + e.message;
        } else {
             assistantMsg.content += '\n\n[System Error]: ' + e.message;
        }
    } finally {
        isLoading.value = false;
        isStreaming.value = false;
        currentController.value = null;
        scrollToBottom();
    }
};

const stopStreaming = () => {
    try {
        if (currentController.value) {
            currentController.value.abort();
        }
    } catch {}
};

const scrollToBottom = () => {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
    });
};

const getMessageText = (content) => {
    if (!content) return '';
    // Remove the ::: echarts ... ::: block
    return content.replace(/::: echarts[\s\S]*?:::/, '').trim();
};

const getMessageChart = (content) => {
    if (!content) return null;
    const match = content.match(/::: echarts([\s\S]*?):::/);
    if (match && match[1]) {
        try {
            return JSON.parse(match[1].trim());
        } catch (e) {
            console.error('Failed to parse chart JSON', e);
            return null;
        }
    }
    return null;
};

const processChartOption = (rawOption) => {
    if (!rawOption) return {};
    // Clone option to avoid mutating the original
    const option = JSON.parse(JSON.stringify(rawOption));
    
    // 1. Color Palette (Modern, soft colors)
    option.color = [
        '#6366f1', '#3b82f6', '#0ea5e9', '#06b6d4', 
        '#14b8a6', '#10b981', '#84cc16', '#f59e0b', 
        '#f97316', '#ef4444', '#ec4899', '#8b5cf6'
    ];
    
    // 2. Grid (Ensure labels are visible)
    if (!option.grid) {
        option.grid = {
            top: '15%',
            bottom: '12%',
            left: '3%',
            right: '4%',
            containLabel: true
        };
    } else {
        option.grid.containLabel = true;
        option.grid.bottom = '12%'; // Ensure space for legend
    }
    
    // 3. Legend (Bottom, centered)
    if (option.legend) {
        option.legend.type = 'scroll'; // Allow scrolling if too many items
        option.legend.bottom = 0;
        option.legend.left = 'center';
        option.legend.orient = 'horizontal';
        option.legend.itemWidth = 10;
        option.legend.itemHeight = 10;
        option.legend.textStyle = {
            color: '#64748b',
            fontSize: 11
        };
        // Remove legend padding/border if any
        delete option.legend.padding;
        delete option.legend.borderWidth;
    }
    
    // 4. Tooltip (Modern style)
    if (!option.tooltip) {
        option.tooltip = {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        };
    }
    // Force tooltip style
    option.tooltip.backgroundColor = 'rgba(255, 255, 255, 0.95)';
    option.tooltip.borderColor = '#e2e8f0';
    option.tooltip.textStyle = { color: '#1e293b', fontSize: 12 };
    option.tooltip.padding = [8, 12];
    option.tooltip.extraCssText = 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border-radius: 8px;';

    // 5. Title (Top center, subtle)
    if (option.title) {
        const titleStyle = { color: '#1e293b', fontSize: 14, fontWeight: 600 };
        const subtextStyle = { color: '#64748b', fontSize: 11 };
        
        const applyTitleStyle = (t) => {
             if (!t.textStyle) t.textStyle = titleStyle;
             else Object.assign(t.textStyle, titleStyle);
             
             if (!t.subtextStyle) t.subtextStyle = subtextStyle;
             else Object.assign(t.subtextStyle, subtextStyle);
             
             // Only set default position if not specified
             if (t.left === undefined && t.right === undefined && t.top === undefined && t.bottom === undefined) {
                 t.left = 'center';
                 t.top = 10;
             }
        };

        if (Array.isArray(option.title)) {
             option.title.forEach(applyTitleStyle);
        } else {
             applyTitleStyle(option.title);
        }
    }
    
    // 6. Series specific tweaks
    if (option.series) {
        option.series.forEach(s => {
            // Bar charts: Rounded corners
            if (s.type === 'bar') {
                if (!s.itemStyle) s.itemStyle = {};
                s.itemStyle.borderRadius = [4, 4, 0, 0];
                s.barMaxWidth = 40;
            }
            // Line charts: Smooth curve, symbol style
            if (s.type === 'line') {
                s.smooth = true;
                s.symbol = 'circle';
                s.symbolSize = 6;
                if (!s.lineStyle) s.lineStyle = {};
                s.lineStyle.width = 3;
            }
            // Pie charts: Donut style, centered
            if (s.type === 'pie') {
                // Use a safer, smaller layout to avoid overlap
                s.center = ['50%', '55%']; 
                // Smaller radius to ensure labels have room
                if (!s.radius) s.radius = ['40%', '60%']; 
                s.avoidLabelOverlap = true;
                
                if (!s.label) s.label = {};
                // s.label.show = true;
                // s.label.formatter = '{b}: {c} ({d}%)';
                
                if (!s.itemStyle) s.itemStyle = {};
                s.itemStyle.borderRadius = 5;
                s.itemStyle.borderColor = '#fff';
                s.itemStyle.borderWidth = 2;
            }
        });
    }

    return option;
};

const renderMarkdown = (text) => {
    try {
        let inputText = (text || '').trim();
        
        // [Cleanup] Remove raw document references like doc#3:xxxx...
        inputText = inputText.replace(/doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?/gi, '');
        
        // [Cleanup] Remove the trailing "References" or "Sources" section aggressively
        const refHeaderPattern = /\n+\s*(?:#+\s*)?(?:\*\*)?(References|Sources|参考来源|引用|引用文献|Reference Document List)(:|\：)?(\*\*)?\s*(\n+|$)/gi;
        inputText = inputText.split(refHeaderPattern)[0];

        // [Cleanup] Also remove any trailing lines that look like [n] or [n] something
        let lines = inputText.split('\n');
        while (lines.length > 0 && (/^\s*\[\d+\]\s*.*$/.test(lines[lines.length - 1]) || !lines[lines.length - 1].trim())) {
            lines.pop();
        }
        inputText = lines.join('\n');

        // [Cleanup] Trim multiple newlines
        inputText = inputText.replace(/\n{3,}/g, '\n\n');

        // [Fix] Handle cases where bold text at the start of a line (possibly indented) 
        // is followed by a colon, which can break some Markdown parsers (like marked).
        inputText = inputText.replace(/^(\s*)\*\*([^*]+)\*\*([:：])/gm, '$1**$2** $3');

        // [Fix] Handle multi-layered brackets like [[[1]]], [[ [1] ]], or [[Source: 1]]
        // Consolidate all citation patterns into a single unified format [n]
        inputText = inputText.replace(/\[+[\s\t]*(?:Source:[\s\t]*)?(\d+)[\s\t]*\]+/gi, '[$1]');

        return marked.parse(inputText);
    } catch (e) {
        console.error('Markdown parse error:', e);
        return text || '';
    }
};

onMounted(() => {
    fetchConfig();
    fetchSessions();
    nextTick(() => autoResize());
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.chart {
    height: 100%;
    width: 100%;
}

/* Markdown Styles */
.markdown-body :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
    font-size: 13px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
    border: 1px solid #e2e8f0;
    padding: 10px 14px;
}
.markdown-body :deep(th) {
    background-color: #f8fafc;
    font-weight: 600;
    text-align: left;
    color: #475569;
}
.markdown-body :deep(tr:nth-child(even)) {
    background-color: #fcfcfc;
}
.markdown-body :deep(tr:hover) {
    background-color: #f1f5f9;
}
.markdown-body :deep(pre) {
    background: #f1f5f9;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid #e2e8f0;
}
.markdown-body :deep(code) {
    font-family: 'Hack', monospace;
    font-size: 12px;
}
</style>
