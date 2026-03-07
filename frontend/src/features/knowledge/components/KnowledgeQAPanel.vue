<template>
    <div v-show="visible" class="w-[400px] flex flex-col pl-4 bg-white dark:bg-slate-900 relative transition-all duration-300 h-full border-l border-slate-100 dark:border-slate-800">
        
        <!-- Header for Chat -->
        <div class="py-3 border-b border-slate-100 dark:border-slate-800 flex flex-col bg-white dark:bg-slate-900 shrink-0 pr-2 transition-colors">
            <div class="flex justify-between items-center mb-2">
                <h3 class="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                    <span class="w-1 h-4 bg-blue-600 dark:bg-blue-500 rounded-full"></span>
                    知识问答
                </h3>
                <div class="flex items-center gap-2">
                    <button 
                        @click="toggleHistoryPanel"
                        class="p-1.5 text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
                        title="历史会话"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </button>
                    <button 
                        @click="confirmClearChatHistory" 
                        class="p-1.5 text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                        title="开启新会话"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    </button>
                    <button 
                        @click="$emit('close')"
                        class="p-1.5 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded transition-colors"
                        title="收起"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- History Panel (Overlay) -->
        <div v-if="showHistoryPanel" class="absolute inset-0 bg-white dark:bg-slate-900 z-20 flex flex-col animate-fade-in-up">
            <div class="flex items-center justify-between p-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                <h4 class="text-sm font-medium text-slate-700 dark:text-slate-300">会话历史</h4>
                <button @click="showHistoryPanel = false" class="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <div class="flex-1 overflow-y-auto p-2 space-y-2 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700">
                <div v-if="sessionsLoading" class="flex justify-center py-4">
                    <div class="w-5 h-5 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin"></div>
                </div>
                <div v-else-if="sessions.length === 0" class="text-center text-xs text-slate-400 dark:text-slate-600 py-8">
                    暂无历史会话
                </div>
                <div 
                    v-for="session in sessions" 
                    :key="session.session_id"
                    class="p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:border-blue-200 dark:hover:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer transition-all group relative"
                    :class="{'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800': session.session_id === currentSessionId}"
                    @click="switchSession(session.session_id)"
                >
                    <div class="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1 line-clamp-1 pr-6">
                        {{ session.preview || '新会话' }}
                    </div>
                    <div class="flex items-center justify-between text-[10px] text-slate-400 dark:text-slate-500">
                        <span>{{ formatDate(session.last_active) }}</span>
                        <span>{{ session.message_count }} 条对话</span>
                    </div>
                    <button 
                        @click.stop="deleteSession(session.session_id)"
                        class="absolute top-2 right-2 p-1 text-slate-300 dark:text-slate-600 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- Messages Area -->
        <div class="flex-1 overflow-y-auto space-y-6 pr-2 mb-4 pt-4 relative scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700" ref="chatContainer">
            <!-- Empty State -->
            <div v-if="chatMessages.length === 0" class="h-full flex flex-col items-center justify-center text-center px-6">
                <div class="w-16 h-16 bg-blue-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center mb-4 shadow-sm border border-transparent dark:border-slate-700">
                    <svg class="w-8 h-8 text-blue-500 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                </div>
                <h3 class="text-base font-medium text-slate-800 dark:text-slate-200 mb-2">问答助手</h3>
                <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-6">
                    您可以问我任何知识中心内容的问题，我会结合知识图谱为您解答。
                </p>
                
                <!-- Mode Cards -->
                <div class="grid grid-cols-2 gap-2 w-full">
                    <div 
                        v-for="card in modeCards" 
                        :key="card.id"
                        class="p-3 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-white dark:hover:bg-slate-700/80 hover:border-blue-200 dark:hover:border-blue-700 hover:shadow-sm transition-all text-left group"
                    >
                        <div class="flex items-center gap-2 mb-2">
                            <span class="w-6 h-6 rounded-lg bg-white dark:bg-slate-900 flex items-center justify-center text-blue-500 dark:text-blue-400 border border-slate-100 dark:border-slate-700 group-hover:border-blue-100 dark:group-hover:border-blue-800">
                                <component :is="card.icon" class="w-3.5 h-3.5" />
                            </span>
                            <span class="text-xs font-medium text-slate-700 dark:text-slate-300">{{ card.title }}</span>
                        </div>
                        <div class="space-y-1">
                            <div 
                                v-for="(ex, idx) in card.examples" 
                                :key="idx"
                                @click="handleSuggestion(ex)"
                                class="text-[10px] text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-300 cursor-pointer truncate flex items-center gap-1"
                                title="点击填入"
                            >
                                <span class="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-600 group-hover:bg-blue-300 dark:group-hover:bg-blue-500"></span>
                                {{ ex }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Messages -->
            <div v-for="(msg, index) in chatMessages" :key="index" class="flex flex-col gap-2 group animate-fade-in-up">
                <!-- User Message -->
                <div v-if="msg.role === 'user'" class="flex justify-end">
                    <div class="px-4 py-2.5 bg-blue-600 text-white rounded-2xl rounded-tr-sm text-sm shadow-sm max-w-[90%] leading-relaxed">
                        {{ msg.content }}
                    </div>
                </div>
                
                <!-- Assistant Message -->
                <div v-else class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0 mt-1">
                        <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <div class="flex flex-col gap-2 max-w-[95%] w-full overflow-hidden">
                        
                        <!-- 1. Process Nodes (Collapsible) -->
                        <div v-if="msg.steps && msg.steps.length > 0" class="border border-slate-100 dark:border-slate-700 rounded-lg overflow-hidden mb-2 bg-slate-50 dark:bg-slate-800/50 w-full">
                            <button 
                                @click="toggleProcess(msg._id || index)"
                                class="w-full flex items-center justify-between px-3 py-2 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            >
                                <div class="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                                    <svg class="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                    <span>思考过程 ({{ msg.steps.length }} 步)</span>
                                </div>
                                <svg 
                                    class="w-3 h-3 text-slate-400 dark:text-slate-500 transition-transform duration-200"
                                    :class="isProcessExpanded(msg._id || index) ? 'rotate-180' : ''"
                                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                >
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            <div v-show="isProcessExpanded(msg._id || index)" class="bg-white dark:bg-slate-900 px-3 py-2 border-t border-slate-100 dark:border-slate-700">
                                <div class="space-y-2">
                                    <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="flex gap-2">
                                        <div class="flex flex-col items-center pt-1">
                                            <div class="w-1.5 h-1.5 rounded-full bg-blue-400 dark:bg-blue-500"></div>
                                            <div v-if="sIdx < msg.steps.length - 1" class="w-px h-full bg-slate-200 dark:bg-slate-700 my-0.5"></div>
                                        </div>
                                        <div class="pb-1 min-w-0 flex-1">
                                            <div class="text-[11px] text-slate-500 dark:text-slate-400 break-words whitespace-pre-wrap font-mono">
                                                {{ step.content }}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 2. Content / Data View -->
                        <div class="flex flex-col w-full">
                            <!-- View Switcher Toolbar (Only if SQL exists) -->
                            <div v-if="msg.sql_query" class="flex items-center justify-between mb-2">
                                <div class="text-xs text-slate-400 font-medium">查询结果</div>
                                <div class="flex bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg">
                                    <button 
                                        @click="setMsgViewMode(msg._id || index, 'table')"
                                        :class="getMsgViewMode(msg._id || index) === 'table' ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                                        class="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all"
                                    >
                                        表格视图
                                    </button>
                                    <button 
                                        @click="setMsgViewMode(msg._id || index, 'sql')"
                                        :class="getMsgViewMode(msg._id || index) === 'sql' ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                                        class="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all"
                                    >
                                        SQL查询
                                    </button>
                                </div>
                            </div>

                            <!-- Loading State -->
                            <div v-if="!msg.content && !msg.data_content && !msg.error_message && chatLoading && msg === chatMessages[chatMessages.length - 1]" class="p-3 bg-slate-50 dark:bg-slate-800 rounded-2xl rounded-tl-sm border border-slate-100 dark:border-slate-700 w-fit">
                                <div class="flex items-center gap-1">
                                    <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                                    <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                                    <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                                </div>
                            </div>

                            <!-- Main Content Area -->
                            <div v-else class="bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-2xl rounded-tl-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
                                
                                <!-- SQL View -->
                                <div v-if="getMsgViewMode(msg._id || index) === 'sql' && msg.sql_query" class="relative group/sql p-3">
                                    <pre class="text-xs text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto font-mono p-2"><code>{{ msg.sql_query }}</code></pre>
                                    <button @click="copySql(msg.sql_query)" class="absolute top-4 right-4 p-1 rounded bg-white dark:bg-slate-800 shadow border text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 opacity-0 group-hover/sql:opacity-100 transition-opacity">
                                        <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M8 16H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2m-6 4h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                                    </button>
                                </div>

                                <!-- Table / Text View -->
                                <div 
                                    v-show="getMsgViewMode(msg._id || index) === 'table'"
                                    class="p-3 text-sm leading-relaxed markdown-content"
                                    :class="{ 'no-sources': !msg.sources || msg.sources.length === 0 }"
                                    v-html="renderMarkdown(msg.content, msg.sources && msg.sources.length > 0)"
                                    @click="handleCitationClick($event, msg)"
                                ></div>

                                <!-- Chart View -->
                                <div v-if="msg.chart_config" class="border-t border-slate-100 dark:border-slate-700 p-3 bg-white dark:bg-slate-900">
                                    <div class="flex items-center gap-2 mb-2">
                                        <svg class="w-3.5 h-3.5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
                                        <span class="text-xs font-bold text-slate-700 dark:text-slate-300">可视化图表</span>
                                    </div>
                                    <div class="h-64 w-full bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-100 dark:border-slate-700">
                                        <ChartFrame :option="processChartOption(msg.chart_config)" />
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Sources -->
                        <div v-if="msg.sources && msg.sources.length > 0" class="flex flex-col gap-2 mt-1 pl-1">
                            <div class="text-[10px] text-slate-400 dark:text-slate-500 font-medium flex justify-between items-center">
                                <span>参考来源</span>
                                <span v-if="scope === 'global'" class="text-[9px] bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 dark:text-slate-400">文档视图</span>
                                <span v-else class="text-[9px] bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 dark:text-slate-400">详情视图</span>
                            </div>
                            
                            <!-- Case 1: Global Scope - Show Document Cards -->
                            <div v-if="scope === 'global'" class="flex flex-col gap-2">
                                <div 
                                    v-for="(doc, idx) in getUniqueDocs(msg.sources)" 
                                    :key="idx"
                                    class="flex items-center gap-3 p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer group"
                                    :title="doc.filename"
                                >
                                    <div class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center text-blue-500 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors">
                                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                    </div>
                                    <div class="flex flex-col overflow-hidden">
                                        <span class="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">{{ doc.filename || '未知文档' }}</span>
                                        <span class="text-[10px] text-slate-400 dark:text-slate-500">相关度: {{ Math.round(doc.score * 100) }}%</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Case 2: Doc Scope - Show Entities and Chunks -->
                            <div v-else class="flex flex-col gap-3">
                                <!-- Entities -->
                                <div v-if="getEntities(msg.sources).length > 0" class="flex flex-wrap gap-1.5">
                                    <div 
                                        v-for="(src, idx) in getEntities(msg.sources)" 
                                        :key="idx"
                                        @click="locateCitationInGraph(src)"
                                        class="px-2 py-1 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded text-[10px] text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 hover:border-indigo-200 dark:hover:border-indigo-700 transition-colors cursor-pointer flex items-center gap-1"
                                        :title="src.content"
                                    >
                                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                        <span class="font-medium">{{ src.title }}</span>
                                    </div>
                                </div>

                                <!-- Chunks -->
                                <div class="grid grid-cols-1 gap-2">
                                    <div 
                                        v-for="(src, idx) in getChunks(msg.sources).slice(0, 3)" 
                                        :key="idx"
                                        @click="locateCitationInGraph(src)"
                                        class="p-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[11px] text-slate-600 dark:text-slate-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer relative group"
                                    >
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="px-1.5 py-0.5 rounded bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 text-[9px] font-mono">
                                                #{{ idx + 1 }}
                                            </span>
                                            <span class="text-[9px] text-slate-400 dark:text-slate-500 truncate flex-1">{{ src.title }}</span>
                                        </div>
                                        <div class="line-clamp-2 leading-relaxed opacity-80 group-hover:opacity-100">
                                            {{ src.content }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Loading State -->
            <div v-if="chatLoading && (chatMessages.length === 0 || chatMessages[chatMessages.length - 1].role !== 'assistant')" class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0 mt-1">
                    <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                </div>
                <div class="flex items-center gap-1 p-3 bg-slate-50 dark:bg-slate-800 rounded-2xl rounded-tl-sm w-fit">
                    <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                    <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        </div>

        <!-- Input Area -->
        <div class="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
            <div class="relative">
                <input 
                    v-model="chatInput" 
                    @keyup.enter="sendChatMessage"
                    type="text" 
                    placeholder="输入问题..." 
                    class="w-full pl-4 pr-12 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all placeholder:text-slate-400 dark:placeholder:text-slate-500 dark:text-slate-200"
                    :disabled="chatLoading"
                >
                <button 
                    @click="sendChatMessage"
                    class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm group"
                    :disabled="chatLoading || !chatInput.trim()"
                >
                    <svg class="w-4 h-4 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                </button>
            </div>
            <div class="text-[10px] text-center text-slate-300 dark:text-slate-600 mt-2 pb-1">
                由混合检索引擎提供支持 (BM25 + Vector + Graph)
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, nextTick, createVNode, onMounted } from 'vue';
import axios from 'axios';
import { message, Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';
import { marked } from 'marked';
import ChartFrame from '@/features/analytics/components/ChartFrame.vue';
import { useChartOptimizer } from '@/features/analytics/composables/useChartOptimizer';
import { 
    SparklesIcon, 
    DocumentTextIcon, 
    ShareIcon, 
    TableCellsIcon 
} from '@heroicons/vue/24/outline';
import * as echarts from 'echarts';

// Props
const props = defineProps<{
    visible: boolean;
    docId?: number | string | null;
    scope: string;
    nodes: any;
}>();

// Emits
const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'locate-node', nodeId: string): void;
}>();

const api = axios.create({ baseURL: '/api/v1' });

// Setup Markdown Renderer
const renderer = new marked.Renderer();
renderer.code = ({ text, lang }) => {
    const code = text;
    const language = lang;
    if (language === 'echarts') {
        const id = 'chart-' + Math.random().toString(36).substr(2, 9);
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) {
                try {
                    let jsonStr = code.trim();
                    if (jsonStr.startsWith('{')) {
                        const option = JSON.parse(jsonStr);
                        const chart = echarts.init(el);
                        chart.setOption(option);
                        new ResizeObserver(() => {
                            chart.resize();
                        }).observe(el);
                    }
                } catch (e) {
                    console.error('ECharts render error:', e);
                    el.innerHTML = `<div class="p-2 text-xs text-red-400 bg-red-50 rounded">图表数据解析失败</div>`;
                }
            }
        }, 50);
        return `<div id="${id}" style="width: 100%; height: 240px; margin: 0.5rem 0;"></div>`;
    }
    return `<pre><code class="language-${language}">${code}</code></pre>`;
};
renderer.text = ({ text }) => text;
marked.use({ renderer: renderer, breaks: true, gfm: true });

interface ChatMessage {
    _id?: string;
    role: string;
    content: string;
    steps?: { content: string; step: number }[];
    sources?: any[];
    sql_query?: string;
    data_content?: string;
    chart_config?: any;
    error_message?: string;
}

// State
const chatMessages = ref<ChatMessage[]>([]);
const chatInput = ref('');
const chatLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);
const currentSessionId = ref<string | null>(null);
const showHistoryPanel = ref(false);
const sessions = ref<any[]>([]);
const sessionsLoading = ref(false);

const expandedProcess = ref(new Set());
const msgViewModes = reactive<Record<string, string>>({});

// Methods
const generateUUID = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

const isProcessExpanded = (id: any) => expandedProcess.value.has(id);
const toggleProcess = (id: any) => {
    if (expandedProcess.value.has(id)) {
        expandedProcess.value.delete(id);
    } else {
        expandedProcess.value.add(id);
    }
};

const getMsgViewMode = (id: any) => msgViewModes[id] || 'table';
const setMsgViewMode = (id: any, mode: string) => {
    msgViewModes[id] = mode;
};

const copySql = (sql: string) => {
    if (!sql) return;
    navigator.clipboard.writeText(sql).then(() => {
        message.success('SQL 已复制');
    });
};

const { optimizeOption } = useChartOptimizer();
const processChartOption = (rawOption: any) => optimizeOption(rawOption);

const modeCards = [
    {
        id: 'auto',
        title: '智能问答',
        icon: SparklesIcon,
        desc: '自动识别意图，智能路由引擎',
        examples: ['分析这份文档的核心观点', '梳理关键实体关系']
    },
    {
        id: 'rag',
        title: '知识检索',
        icon: DocumentTextIcon,
        desc: '基于文档内容的精确问答',
        examples: ['什么是切片技术？', '文档中提到了哪些标准？']
    },
    {
        id: 'kg',
        title: '图谱分析',
        icon: ShareIcon,
        desc: '可视化实体关系与结构',
        examples: ['展示5G网络的关系图', '查看核心节点的关联']
    },
    {
        id: 'data',
        title: '数据洞察',
        icon: TableCellsIcon,
        desc: '统计数据查询与报表生成',
        examples: ['统计各省份基站数量', '查询本月订单总额']
    }
];

const toggleHistoryPanel = () => {
    showHistoryPanel.value = !showHistoryPanel.value;
    if (showHistoryPanel.value) {
        fetchSessions();
    }
};

const fetchSessions = async () => {
    const targetDocId = props.docId || 0;
    sessionsLoading.value = true;
    try {
        const res = await api.get(`/knowledge/${targetDocId}/qa/sessions`);
        sessions.value = res.data;
    } catch (e) {
        message.error("获取会话列表失败");
    } finally {
        sessionsLoading.value = false;
    }
};

const switchSession = async (sid: string) => {
    currentSessionId.value = sid;
    showHistoryPanel.value = false;
    await fetchChatHistory(props.docId || 0);
};

const deleteSession = async (sid: string) => {
    Modal.confirm({
        title: '删除会话',
        content: '确定要删除该会话及其所有记录吗？',
        onOk: async () => {
            try {
                await api.delete(`/knowledge/chat/sessions/${sid}`);
                message.success('已删除');
                if (currentSessionId.value === sid) {
                    currentSessionId.value = null;
                    chatMessages.value = [];
                }
                fetchSessions();
            } catch (e) {
                message.error('删除失败');
            }
        }
    });
};

const formatDate = (ts: number) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric' });
};

const fetchChatHistory = async (docId: number | string) => {
    if (docId === null || docId === undefined) return;
    if (!currentSessionId.value) {
        chatMessages.value = [];
        return;
    }

    try {
        const params: any = {};
        if (currentSessionId.value) {
            params.session_id = currentSessionId.value;
        }
        const res = await api.get(`/knowledge/${docId}/qa/history`, { params });
        chatMessages.value = res.data;
        setTimeout(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }, 100);
    } catch (e) {
        console.error('Failed to fetch chat history:', e);
    }
};

const handleSuggestion = (text: string) => {
    if (chatLoading.value) return;
    chatInput.value = text;
};

const sendChatMessage = async () => {
    if (chatLoading.value) return;
    if (!chatInput.value.trim()) return;
    
    const query = chatInput.value;
    
    if (!currentSessionId.value) {
        currentSessionId.value = generateUUID();
    }

    chatMessages.value.push({ role: 'user', content: query });
    chatInput.value = '';
    chatLoading.value = true;
    
    setTimeout(() => {
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }, 100);
    
    try {
        const history = chatMessages.value.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`);
        
        const payload = { 
            query, 
            history,
            scope: props.docId ? props.scope : 'global',
            mode: 'auto',
            session_id: currentSessionId.value
        };
        
        const url = props.docId 
            ? `/api/v1/knowledge/${props.docId}/qa` 
            : `/api/v1/knowledge/qa`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const assistantMsg = reactive<{
            _id: string;
            role: string;
            content: string;
            sources: any[];
            steps: { content: string; step: number }[];
            sql_query: string;
            data_content: string;
            chart_config: any;
        }>({ 
            _id: `msg_${Date.now()}_assistant`,
            role: 'assistant', 
            content: '', 
            sources: [],
            steps: [], 
            sql_query: '',
            data_content: '',
            chart_config: null
        });
        chatMessages.value.push(assistantMsg);

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        if (reader) {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);
                        if (data.type) {
                            switch (data.type) {
                                case 'text':
                                    assistantMsg.content += data.content;
                                    break;
                                case 'process':
                                    assistantMsg.steps.push({
                                        content: data.content,
                                        step: data.step || assistantMsg.steps.length + 1
                                    });
                                    if (assistantMsg.steps.length === 1) {
                                        expandedProcess.value.add(assistantMsg._id);
                                    }
                                    break;
                                case 'sql':
                                    assistantMsg.sql_query = data.content;
                                    setMsgViewMode(assistantMsg._id, 'sql');
                                    break;
                                case 'data':
                                    assistantMsg.data_content = data.content;
                                    assistantMsg.content += '\n' + data.content;
                                    setMsgViewMode(assistantMsg._id, 'table');
                                    break;
                                case 'chart':
                                    assistantMsg.chart_config = data.content;
                                    break;
                                case 'sources':
                                    assistantMsg.sources = data.content;
                                    break;
                                case 'error':
                                    assistantMsg.content += `\n[Error: ${data.content}]`;
                                    break;
                            }
                        } else {
                            assistantMsg.content += JSON.stringify(data);
                        }
                    } catch (e) {
                        assistantMsg.content += line + '\n';
                    }
                }
                if (chatContainer.value) {
                    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
                }
            }
        }
        
        if (buffer.trim()) {
             try {
                 const data = JSON.parse(buffer);
                 if (data.type === 'text') assistantMsg.content += data.content;
             } catch (e) {
                 assistantMsg.content += buffer;
             }
        }
        
        if (chatMessages.value.length <= 2 && showHistoryPanel.value) {
            fetchSessions();
        }
        
    } catch (e: any) {
        console.error(e);
        if (chatMessages.value.length === 0 || chatMessages.value[chatMessages.value.length - 1].role === 'user') {
             chatMessages.value.push({ 
                role: 'assistant', 
                content: `[Error: ${e.message}]`,
                sources: []
            });
        } else {
             const lastMsg = chatMessages.value[chatMessages.value.length - 1];
             lastMsg.content += `\n[Error: ${e.message}]`;
        }
    } finally {
        chatLoading.value = false;
        setTimeout(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }, 100);
    }
};

const confirmClearChatHistory = () => {
    Modal.confirm({
        title: '开启新会话？',
        icon: createVNode(ExclamationCircleOutlined),
        content: '这将开启一个新的空白会话，旧的记录将保留在历史中。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                currentSessionId.value = generateUUID();
                chatMessages.value = [];
                message.success('新会话已开启');
                fetchSessions(); 
            } catch (e: any) {
                message.error('操作失败：' + (e.message));
            }
        }
    });
};

const renderMarkdown = (content: string, hasStructuredSources = false) => {
    if (!content) return '';
    try {
        let inputText = (content || '').trim();
        let thinkHtml = '';
        const thinkStart = inputText.indexOf('<think>');
        if (thinkStart !== -1) {
            const thinkEnd = inputText.indexOf('</think>');
            let thinkContent = '';
            let isPartial = false;
            
            if (thinkEnd !== -1) {
                thinkContent = inputText.substring(thinkStart + 7, thinkEnd);
                inputText = inputText.substring(0, thinkStart) + inputText.substring(thinkEnd + 8);
            } else {
                thinkContent = inputText.substring(thinkStart + 7);
                inputText = inputText.substring(0, thinkStart); 
                isPartial = true;
            }

            if (thinkContent || isPartial) {
                let parsedThink = marked.parse(thinkContent || '正在检索思考中...');
                const parsedThinkStr = typeof parsedThink === 'string' ? parsedThink : '';
                const sanitizedThink = (parsedThinkStr || '').replace(/\[object\s+Object\]/gi, '').trim();
                thinkHtml = `
                <details class="mb-3 bg-amber-50/50 rounded-lg border border-amber-100 overflow-hidden group" ${isPartial ? 'open' : ''}>
                    <summary class="px-3 py-1.5 text-xs font-medium text-amber-600/70 cursor-pointer hover:bg-amber-50 flex items-center gap-2 select-none transition-colors">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                        思考过程
                    </summary>
                    <div class="px-3 py-2 text-xs text-slate-600 border-t border-amber-100/50 bg-white/50 leading-relaxed">
                        ${sanitizedThink || '正在检索思考中...'}
                    </div>
                </details>`;
            }
        }

        inputText = inputText.replace(/^(\s*)\*\*([^*]+)\*\*([:：])/gm, '$1**$2** $3');
        inputText = inputText.replace(/\[\[Entity:\s*(.*?)\]\]/g, '<span class="entity-citation" data-entity="$1" title="点击在图谱中定位">$1</span>');
        inputText = inputText.replace(/doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?/gi, '');
        
        if (hasStructuredSources) {
            const refHeaderPattern = /\n+\s*(?:#+\s*)?(?:\*\*)?(References|Sources|参考来源|知识来源|引用|引用文献|Reference Document List)(:|\：)?(?:\*\*)?\s*(\n+|$)/gi;
            inputText = inputText.split(refHeaderPattern)[0];
        }
        
        const echartsRegex = /:::\s*echarts\s*([\s\S]*?):::/g;
        inputText = inputText.replace(echartsRegex, (match, jsonContent) => {
            return `\n\`\`\`echarts\n${jsonContent.trim()}\n\`\`\`\n`;
        });
        
        if (inputText.includes('__SOURCES__')) {
            inputText = inputText.split('__SOURCES__')[0];
        }
        
        inputText = inputText.replace(/^data: /gm, '');
        inputText = inputText.replace(/^event: .*$/gm, '');

        inputText = inputText.replace(/\[+[\s\t]*(?:Source:[\s\t]*)?(\d+)[\s\t]*\]+/gi, '[$1]');
        inputText = inputText.replace(/\n{3,}/g, '\n\n').trim();
        if (hasStructuredSources) {
            inputText = inputText.replace(/\[(\d+)\]/g, (match, num) => {
                return `<span class="citation-icon" data-idx="${parseInt(num)-1}" title="点击在图谱中定位">${match}</span>`;
            });
        } else {
            inputText = inputText.replace(/\[(\d+)\]/g, (match) => {
                return `<span class="citation-index-disabled" title="暂无引用来源">${match}</span>`;
            });
        }
        
        const answerHtml = marked.parse(inputText);
        return thinkHtml + answerHtml;
    } catch (e) {
        console.error('Markdown parse error:', e);
        return content;
    }
};

const handleCitationClick = (e: MouseEvent, msg: any) => {
    const citationTarget = (e.target as HTMLElement).closest('.citation-icon');
    if (citationTarget) {
        e.stopPropagation();
        const idx = parseInt(citationTarget.getAttribute('data-idx') || '-1');
        
        if (idx < 0) return;

        if (!msg.sources || msg.sources.length === 0) {
            Modal.warning({ title: '引用数据缺失', content: '当前回答暂无引用来源。', okText: '关闭' });
            return;
        }

        if (!msg.sources[idx]) return;

        const source = msg.sources[idx];
        if (source.source === 'graph') {
             locateCitationInGraph(source);
        } else if (source.source === 'vector') {
             Modal.info({
                title: `参考来源 [${idx + 1}]`,
                icon: createVNode(InfoCircleOutlined),
                width: 600,
                content: createVNode('div', { class: 'space-y-3' }, [
                    createVNode('div', { class: 'text-xs text-slate-500 flex items-center gap-2 pb-2 border-b border-slate-100' }, [
                        createVNode('span', { class: 'bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100' }, '文档片段'),
                        createVNode('span', { class: 'font-medium truncate max-w-[300px]' }, source.title || source.filename),
                        createVNode('span', { class: 'ml-auto' }, `相关度: ${Math.round(source.score * 100)}%`)
                    ]),
                    createVNode('div', { class: 'p-3 bg-slate-50 rounded-lg text-sm text-slate-700 leading-relaxed max-h-[400px] overflow-y-auto font-mono whitespace-pre-wrap' }, source.content)
                ]),
                maskClosable: true,
                okText: '关闭'
             });
        } else {
             Modal.info({
                title: `参考来源 [${idx + 1}]`,
                content: JSON.stringify(source, null, 2),
                maskClosable: true,
                okText: '关闭'
             });
        }
        return;
    }

    const entityTarget = (e.target as HTMLElement).closest('.entity-citation');
    if (entityTarget) {
        e.stopPropagation();
        const entityName = entityTarget.getAttribute('data-entity');
        if (entityName) {
            locateCitationInGraph({ title: entityName, source: 'graph' });
        }
    }
};

const locateCitationInGraph = (source: any) => {
    if (!source) return;
    
    // Check if we have nodes available to search
    if (!props.nodes || Object.keys(props.nodes).length === 0) {
        // If no nodes, we can't really verify existence, but maybe we should emit anyway and let the parent decide?
        // But the requirement says "only retain QA logic".
        // The original logic checked graphNodes.value.
        // We will emit 'locate-node' and let the parent/viewer handle the focus logic.
        // BUT, to give feedback "Not found", we need the nodes.
        message.info('当前无可见图谱数据');
        return;
    }

    if (source.source === 'graph') {
        const entityName = source.title; 
        const matchingNodeId = Object.keys(props.nodes).find(id => {
            const node = props.nodes[id];
            return (node.name === entityName) || (id === entityName);
        });
        if (matchingNodeId) {
            emit('locate-node', matchingNodeId);
            return;
        }
    }
    
    // Vector source fallback logic
    const content = source.content || '';
    const matchingNodeIds = Object.keys(props.nodes).filter(id => {
        const node = props.nodes[id];
        const name = node.name || id;
        return content.includes(name);
    });
    if (matchingNodeIds.length > 0) {
        emit('locate-node', matchingNodeIds[0]);
    } else {
        message.info('未在当前可见图谱中找到相关实体');
    }
};

const getUniqueDocs = (sources: any[]) => {
    if (!sources) return [];
    const docs = new Map();
    sources.forEach(s => {
        if (s.source === 'vector' && s.filename) {
            if (!docs.has(s.filename)) {
                docs.set(s.filename, {
                    filename: s.filename,
                    doc_id: s.doc_id,
                    score: s.score
                });
            } else {
                const existing = docs.get(s.filename);
                if (s.score > existing.score) {
                    existing.score = s.score;
                }
            }
        }
    });
    return Array.from(docs.values()).sort((a: any, b: any) => b.score - a.score);
};

const getChunks = (sources: any[]) => {
    return (sources || []).filter(s => s.source === 'vector');
};

const getEntities = (sources: any[]) => {
    return (sources || []).filter(s => s.source === 'graph');
};

defineExpose({
    renderMarkdown,
    handleCitationClick,
    locateCitationInGraph,
    sendChatMessage
});

onMounted(() => {
    fetchSessions();
});

watch(() => props.visible, (newVal) => {
    if (newVal) {
        // Scroll to bottom when shown
        setTimeout(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }, 100);
    }
});
</script>

<style scoped>
/* Scrollbar Styles */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
}
:hover::-webkit-scrollbar-thumb {
  background: #e5e6eb;
}
::-webkit-scrollbar-thumb:hover {
  background: #c9cdd4;
}

.animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.markdown-content :deep(p) {
    margin-bottom: 0.75rem;
    line-height: 1.6;
}
.markdown-content :deep(p:last-child) {
    margin-bottom: 0;
}
.markdown-content :deep(ul), .markdown-content :deep(ol) {
    padding-left: 1.5rem;
    margin-bottom: 0.75rem;
}
.markdown-content :deep(li) {
    margin-bottom: 0.4rem;
}
.markdown-content :deep(strong) {
    font-weight: 600;
    color: #1e293b;
}
.markdown-content :deep(.entity-citation) {
    color: #2563eb;
    background-color: #eff6ff;
    padding: 0px 4px;
    border-radius: 4px;
    border-bottom: 1px dashed #3b82f6;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}
.markdown-content :deep(.entity-citation:hover) {
    background-color: #dbeafe;
    border-bottom-style: solid;
}
.markdown-content :deep(.citation-icon) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    background-color: #f1f5f9;
    color: #3b82f6;
    border: 1px solid #dbeafe;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin: 0 2px;
    padding: 0 3px;
    cursor: pointer;
    vertical-align: super;
    transition: all 0.2s;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.markdown-content :deep(.citation-icon:hover) {
    background-color: #3b82f6;
    border-color: #3b82f6;
    color: white;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}
.markdown-content.no-sources :deep(.citation-icon) {
    pointer-events: none;
    opacity: 0.5;
    cursor: default;
}
.markdown-content :deep(.citation-index-disabled) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    background-color: #f8fafc;
    color: #94a3b8;
    border: 1px dashed #e2e8f0;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin: 0 2px;
    padding: 0 3px;
    vertical-align: super;
}

/* Table Styles (Matched with SmartDataQuery) */
.markdown-content :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
    font-size: 13px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    display: table; /* Ensure table display */
}
.markdown-content :deep(thead) {
    background-color: #f8fafc;
}
.markdown-content :deep(th), .markdown-content :deep(td) {
    border: 1px solid #e2e8f0;
    padding: 10px 14px;
    text-align: left;
}
.markdown-content :deep(th) {
    background-color: #f8fafc;
    font-weight: 600;
    color: #475569;
}
.markdown-content :deep(tr:nth-child(even)) {
    background-color: #fcfcfc;
}
.markdown-content :deep(tr:hover) {
    background-color: #f1f5f9;
}
.markdown-content :deep(pre) {
    background: #f1f5f9;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid #e2e8f0;
}
.markdown-content :deep(code) {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    color: #475569;
}
</style>
