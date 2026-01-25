<template>
  <div class="h-full flex bg-slate-50 overflow-hidden rounded-2xl shadow-sm border border-slate-200">
    <!-- Sidebar: Sessions -->
    <div class="w-64 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
        <div class="p-4 border-b border-slate-100">
            <button 
                @click="createNewSession" 
                class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl flex items-center justify-center gap-2 transition-colors shadow-sm shadow-blue-200 font-medium text-sm"
            >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                <span>新建对话</span>
            </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
            <div v-if="sessions.length === 0" class="text-center text-slate-400 text-xs py-8">
                暂无历史对话
            </div>
            <div 
                v-for="session in sessions" 
                :key="session.id"
                @click="selectSession(session)"
                class="group px-3 py-3 rounded-xl cursor-pointer flex items-center justify-between transition-all duration-200"
                :class="currentSessionId === session.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50 text-slate-600'"
            >
                <div class="flex items-center gap-3 overflow-hidden">
                    <svg class="w-4 h-4 flex-shrink-0" :class="currentSessionId === session.id ? 'text-blue-500' : 'text-slate-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                    <span class="text-sm truncate">{{ session.title || '新对话' }}</span>
                </div>
                <button 
                    @click.stop="deleteSession(session.id)"
                    class="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 rounded transition-opacity"
                >
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
        </div>
    </div>

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-white relative">
        
        <!-- Header (Only show when chatting) -->
        <div v-if="messages.length > 0" class="px-6 py-3 border-b border-slate-100 flex justify-between items-center bg-white/80 backdrop-blur-sm z-10">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
                    <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                <div>
                    <h2 class="font-bold text-slate-800 text-sm">
                        {{ currentSession?.title || '智能问答助手' }}
                    </h2>
                    <div class="flex items-center gap-1 text-xs text-slate-500" v-if="currentAgent">
                        <span>当前智能体:</span>
                        <span class="font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">{{ currentAgent.name }}</span>
                        <span v-if="localStrictMode" class="ml-2 px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">严格检索</span>
                    </div>
                </div>
            </div>
            
            <!-- Agent Selector -->
            <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500">选择智能体:</span>
                <select 
                    v-model="selectedAgentId" 
                    @change="handleAgentChange"
                    class="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none min-w-[150px]"
                    :disabled="isLoading || messages.length > 0"
                >
                    <option value="">默认问答助手</option>
                    <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                        {{ agent.name }}
                    </option>
                </select>
            </div>
        </div>

        <div v-if="messages.length > 0 && userScripts.length" class="px-6 py-3 border-b border-slate-100 bg-white">
            <div class="max-w-4xl mx-auto">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-xs font-medium text-slate-700">用户剧本</div>
                    <div class="text-[11px] text-slate-400">点击剧本快速填充到输入框</div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div v-for="s in userScripts" :key="s.id" class="p-3 border rounded-lg bg-slate-50 hover:bg-slate-100 cursor-pointer"
                         @click="input = s.content">
                        <div class="text-sm font-medium text-slate-700 truncate">{{ s.title }}</div>
                        <div class="text-[11px] text-slate-500 mt-1 line-clamp-3">{{ s.content }}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Welcome / Empty State (Design Implementation) -->
        <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center p-8 bg-white">
             <div class="frame1321317936">
                <p class="text-heading">今天想说什么</p>
                <div class="frame367 relative group transition-all focus-within:ring-2 focus-within:ring-blue-100">
                    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 mb-2 w-full overflow-x-auto">
                        <div v-for="(att, idx) in selectedAttachments" :key="idx" class="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100 flex-shrink-0">
                            <component :is="att.type === 'local' ? PaperClipOutlined : FileTextOutlined" />
                            <span class="max-w-[120px] truncate" :title="att.name">{{ att.name }}</span>
                            <DeleteOutlined class="cursor-pointer hover:text-red-500 ml-1" @click="removeAttachment(idx)" />
                        </div>
                    </div>
                    <textarea 
                        v-model="input" 
                        @keydown.enter.prevent="sendMessage"
                        class="text2 w-full flex-1 resize-none outline-none bg-transparent placeholder-slate-300" 
                        placeholder="描述您需要帮助的内容..."
                    ></textarea>
                    
                    <div class="frame374 absolute bottom-3 right-3 left-3 flex justify-between items-center">
                         <div class="frame1321315582 cursor-pointer hover:bg-slate-50 rounded-lg p-1 transition-colors" @click="openAttachmentModal">
                            <div class="frame flex items-center gap-2">
                                <svg class="icons w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
                                <p class="text3 text-slate-500 text-xs m-0">附件</p>
                            </div>
                         </div>
                         
                         <div class="flex items-center gap-4">
                             <!-- Agent Selector Pill -->
                             <div class="agent-selector-container">
                                <svg class="selector-icon w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                <a-select 
                                    v-model:value="selectedAgentId" 
                                    @change="handleAgentChange"
                                    class="agent-select-custom"
                                    :bordered="false"
                                    popupClassName="agent-dropdown-custom"
                                    :listHeight="200"
                                >
                                    <template #suffixIcon>
                                         <svg class="w-3 h-3 text-slate-400 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </template>
                                    <a-select-option value="">默认助手</a-select-option>
                                    <a-select-option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</a-select-option>
                                </a-select>
                             </div>
                             
                             <div class="frame1321315581 flex items-center gap-2">
                                <button @click="sendMessage" class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-md transition-all active:scale-95" :disabled="!input.trim()">
                                    <svg class="icons3 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"></path></svg>
                                </button>
                             </div>
                         </div>
                    </div>
                </div>

                <div class="frame1 mt-8">
                    <div v-if="userScriptsLoading" class="text-xs text-slate-500">正在加载用户剧本...</div>
                    <div v-else-if="userScriptsError" class="text-xs text-red-500">{{ userScriptsError }}</div>
                    <template v-else>
                        <div 
                            v-for="s in userScripts" 
                            :key="s.id" 
                            class="frame3 cursor-pointer hover:bg-slate-50 transition-colors gap-2" 
                            @click="sendQuickMessage(s.content)"
                        >
                            <svg class="icons4 w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
                            <p class="text4 m-0">{{ s.title }}</p>
                        </div>
                    </template>
                </div>
             </div>
        </div>

        <!-- Messages List (Standard Chat) -->
        <div v-else class="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" 
                 :class="['flex gap-4 max-w-4xl mx-auto', msg.role === 'user' ? 'flex-row-reverse' : '']">
                <!-- Avatar -->
                <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                     :class="msg.role === 'user' ? 'bg-blue-600' : 'bg-white border border-slate-200'">
                     <span v-if="msg.role === 'user'" class="text-white text-xs font-bold">Me</span>
                     <svg v-else class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                
                <!-- Content -->
                <div :class="['rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed max-w-[85%]', 
                              msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white border border-slate-100 text-slate-700 rounded-tl-sm']">
                    <div v-if="msg.role === 'assistant'">
                        <!-- Thinking Block -->
                        <div v-if="msg.reasoning || (msg.meta_data && msg.meta_data.reasoning)" 
                             class="mb-3 p-3 bg-slate-50 border-l-4 border-indigo-200 rounded text-xs text-slate-500 font-mono whitespace-pre-wrap">
                            <div class="flex items-center gap-1 mb-1 text-indigo-400 font-semibold uppercase tracking-wider">
                                <svg class="w-3 h-3 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                                Thinking Process
                            </div>
                            {{ msg.reasoning || msg.meta_data.reasoning }}
                        </div>
                        
                        <!-- Amis Renderer (for Charts) -->
                        <div v-if="isAmisJSON(msg.content)" class="amis-container my-2 border border-slate-200 rounded-lg overflow-hidden">
                            <div :id="'amis-' + index"></div>
                        </div>
                        
                        <!-- Markdown Content -->
                        <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                        <div v-if="msg.meta_data && (msg.meta_data.structured_references || msg.meta_data.references)" class="mt-3 p-3 bg-slate-50 rounded border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div class="font-medium text-slate-700">参考资料</div>
                                <div class="flex items-center gap-2">
                                    <select v-model="viewMode" class="text-xs bg-white border border-slate-300 rounded px-2 py-1">
                                        <option value="table">表格</option>
                                        <option value="cards">卡片</option>
                                    </select>
                                    <select v-if="viewMode==='cards'" v-model="cardsLayout" class="text-xs bg-white border border-slate-300 rounded px-2 py-1">
                                        <option value="grid">网格</option>
                                        <option value="masonry">瀑布流</option>
                                    </select>
                                </div>
                            </div>
                            <ReferencesTable v-if="viewMode==='table'" :items="structuredRefs(msg)" :loading="false" />
                            <ReferencesCards v-else :items="structuredRefs(msg)" :loading="false" :mode="cardsLayout" />
                        </div>
                        <div v-if="localDebugMode && msg.meta_data && msg.meta_data.filtered_out && msg.meta_data.filtered_out.length" class="mt-2 p-2 bg-slate-100 text-[11px] text-slate-500 rounded">
                            <div class="mb-1">已过滤结果</div>
                            <ul class="space-y-1">
                                <li v-for="(f, fidx) in msg.meta_data.filtered_out" :key="fidx">{{ f.title }} · {{ f.score }}</li>
                            </ul>
                        </div>
                    </div>
                    <div v-else>{{ msg.content }}</div>
                </div>
            </div>

            <!-- Loading Indicator -->
            <div v-if="isLoading && !isStreaming" class="flex gap-4 max-w-4xl mx-auto">
                 <div class="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 shadow-sm">
                     <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path></svg>
                 </div>
                 <div class="bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm flex items-center gap-2">
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></span>
                 </div>
            </div>
        </div>

        <!-- Input Area (Bottom - Only show when chatting) -->
        <div class="p-4 bg-white border-t border-slate-100 z-10" v-if="currentSessionId && messages.length > 0">
            <div class="max-w-4xl mx-auto relative">
                <div class="mb-2 flex items-center gap-3 text-[11px] text-slate-600">
                    <label class="flex items-center gap-2">
                        <input type="checkbox" v-model="localStrictMode" />
                        <span>仅检索绑定文档</span>
                    </label>
                    <label class="flex items-center gap-1">
                        <span>噪声阈值</span>
                        <input type="number" v-model.number="localThreshold" step="0.01" min="0" max="1" class="w-16 bg-slate-50 border border-slate-200 rounded px-2 py-0.5" />
                    </label>
                    <label class="flex items-center gap-2">
                        <input type="checkbox" v-model="localDebugMode" />
                        <span>调试模式</span>
                    </label>
                    <label class="flex items-center gap-1">
                        <span>A/B</span>
                        <select v-model="localABVariant" class="bg-slate-50 border border-slate-200 rounded px-2 py-0.5">
                            <option value="A">A</option>
                            <option value="B">B</option>
                        </select>
                    </label>
                </div>
                <textarea 
                  v-model="input" 
                  @keydown.enter.prevent="sendMessage"
                  rows="1"
                  placeholder="输入您的问题，按 Enter 发送..." 
                  class="w-full pl-4 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none resize-none text-sm text-slate-700 placeholder-slate-400 transition-all shadow-inner"
                  :disabled="isLoading"
                  style="min-height: 52px; max-height: 120px;"
                  @input="adjustHeight"
                ></textarea>
                <button 
                  @click="sendMessage"
                  class="absolute right-2 bottom-2 p-2 rounded-lg transition-all duration-200"
                  :class="input.trim() && !isLoading ? 'bg-blue-600 text-white shadow-lg shadow-blue-200 hover:bg-blue-700' : 'bg-slate-200 text-slate-400 cursor-not-allowed'"
                  :disabled="isLoading || !input.trim()"
                >
                    <svg class="w-5 h-5 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
                </button>
            </div>
            <p class="text-center text-[10px] text-slate-400 mt-2">内容由 AI 生成，仅供参考</p>
        </div>
    </div>
    <!-- Attachment Modal -->
    <a-modal
        v-model:open="attachmentModalVisible"
        title="选择附件"
        width="600px"
        @ok="handleAttachmentOk"
        destroyOnClose
    >
        <a-tabs v-model:activeKey="activeAttachmentTab" @change="handleAttachmentTabChange">
            <!-- Local File Tab -->
            <a-tab-pane key="local" tab="本地文件">
                <a-upload-dragger
                    name="file"
                    :multiple="true"
                    :showUploadList="false"
                    :beforeUpload="handleLocalUpload"
                >
                    <p class="ant-upload-drag-icon">
                        <InboxOutlined />
                    </p>
                    <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p class="ant-upload-hint">
                        支持 PDF, DOCX, PPTX, XLSX, TXT 格式，最大 50MB
                    </p>
                </a-upload-dragger>
                
                <!-- Local File List -->
                <div v-if="localFileList.length > 0" class="mt-4 max-h-40 overflow-y-auto space-y-2">
                    <div v-for="file in localFileList" :key="file.uid" class="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100">
                        <div class="flex items-center gap-2 truncate">
                            <PaperClipOutlined class="text-slate-400" />
                            <span class="text-sm text-slate-700 truncate max-w-[300px]">{{ file.name }}</span>
                            <span class="text-xs text-slate-400">({{ (file.size / 1024).toFixed(1) }} KB)</span>
                        </div>
                        <DeleteOutlined class="text-slate-400 hover:text-red-500 cursor-pointer" @click="removeLocalFile(file)" />
                    </div>
                </div>
            </a-tab-pane>
            
            <!-- Knowledge Base Tab -->
            <a-tab-pane key="knowledge" tab="知识库文档">
                <div class="flex flex-col gap-3 h-[400px]">
                    <div class="flex gap-2">
                        <a-input v-model:value="knowledgeSearchKeyword" placeholder="搜索文档名称..." allowClear>
                            <template #prefix><SearchOutlined /></template>
                        </a-input>
                        <a-button type="primary" :loading="knowledgeLoading" @click="fetchKnowledgeDocs">刷新</a-button>
                    </div>
                    
                    <a-table
                        :dataSource="filteredKnowledgeDocs"
                        :columns="knowledgeColumns"
                        :rowKey="record => record.id"
                        :rowSelection="{ selectedRowKeys: selectedKnowledgeRowKeys, onChange: onKnowledgeSelectChange }"
                        :pagination="{ pageSize: 50, size: 'small' }"
                        :scroll="{ y: 300 }"
                        size="small"
                        :loading="knowledgeLoading"
                    />
                </div>
            </a-tab-pane>
        </a-tabs>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed, watch, createVNode } from 'vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Modal, message } from 'ant-design-vue';
import ReferencesTable from './ReferencesTable.vue';
import ReferencesCards from './ReferencesCards.vue';
import { ExclamationCircleOutlined, PaperClipOutlined, FileTextOutlined, DeleteOutlined, InboxOutlined, SearchOutlined } from '@ant-design/icons-vue';

const input = ref('');
const messages = ref([]);
const sessions = ref([]);
const agents = ref([]);
const currentSessionId = ref(null);
const selectedAgentId = ref('');
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);

const currentSession = computed(() => sessions.value.find(s => s.id === currentSessionId.value));
const currentAgent = computed(() => agents.value.find(a => a.id === selectedAgentId.value));

onMounted(() => {
    fetchAgents();
    fetchSessions();
    fetchUserScripts(selectedAgentId.value);
});
const localStrictMode = ref(false);
const localThreshold = ref(0.85);
const localDebugMode = ref(false);
const localABVariant = ref('A');
const viewMode = ref('table');
const cardsLayout = ref('grid');
const structuredRefs = (msg) => {
    const sr = msg.meta_data?.structured_references || [];
    if (sr.length) return sr;
    const refs = msg.meta_data?.references || [];
    return refs.map((r, i) => ({
        id: i + 1,
        title: r.title || '',
        createTime: '',
        coverImage: r.url || '',
        summary: r.preview || '',
        tags: []
    }));
};
const userScripts = ref([]);
const userScriptsLoading = ref(false);
const userScriptsError = ref('');
const fetchUserScripts = async (aid) => {
    userScriptsError.value = '';
    userScriptsLoading.value = true;
    if (!aid) { userScripts.value = []; userScriptsLoading.value = false; return; }
    try {
        const res = await fetch(`/api/v1/user_scripts?agent_id=${aid}`);
        if (res.ok) {
            userScripts.value = await res.json();
        } else {
            userScriptsError.value = '请求失败';
            userScripts.value = [];
        }
    } catch (e) {
        userScriptsError.value = '加载失败';
        userScripts.value = [];
    } finally {
        userScriptsLoading.value = false;
    }
};
watch(selectedAgentId, (nv) => fetchUserScripts(nv));

const adjustHeight = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
};

const sendQuickMessage = (text) => {
    input.value = text;
    sendMessage();
};

// --- Attachment Logic ---
const attachmentModalVisible = ref(false);
const activeAttachmentTab = ref('local');
const localFileList = ref([]);
const knowledgeDocs = ref([]);
const selectedKnowledgeRowKeys = ref([]);
const knowledgeSearchKeyword = ref('');
const knowledgeLoading = ref(false);
const selectedAttachments = ref([]); // Final confirmed attachments

const knowledgeColumns = [
    { title: '文档名称', dataIndex: 'filename', key: 'filename', sorter: (a, b) => a.filename.localeCompare(b.filename) },
    { title: '大小', dataIndex: 'file_size', key: 'file_size', customRender: ({ text }) => (text / 1024).toFixed(2) + ' KB', sorter: (a, b) => a.file_size - b.file_size },
    { title: '修改时间', dataIndex: 'updated_at', key: 'updated_at', sorter: (a, b) => new Date(a.updated_at) - new Date(b.updated_at) }
];

const openAttachmentModal = () => {
    attachmentModalVisible.value = true;
    if (activeAttachmentTab.value === 'knowledge') {
        fetchKnowledgeDocs();
    }
};

const handleAttachmentTabChange = (key) => {
    activeAttachmentTab.value = key;
    if (key === 'knowledge' && knowledgeDocs.value.length === 0) {
        fetchKnowledgeDocs();
    }
};

const handleLocalUpload = (file) => {
    // Check size (50MB)
    const isLt50M = file.size / 1024 / 1024 < 50;
    if (!isLt50M) {
        message.error('文件大小不能超过 50MB!');
        return false; // Stop upload
    }
    // Check type
    const acceptedTypes = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt'];
    const fileExt = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!acceptedTypes.includes(fileExt)) {
        message.error('不支持的文件类型! 仅支持 PDF/DOCX/PPTX/XLSX/TXT');
        return false;
    }
    
    // Add to local list manually since we prevent default upload
    localFileList.value = [...localFileList.value, file];
    return false; // Prevent auto upload
};

const removeLocalFile = (file) => {
    const index = localFileList.value.indexOf(file);
    const newFileList = localFileList.value.slice();
    newFileList.splice(index, 1);
    localFileList.value = newFileList;
};

const fetchKnowledgeDocs = async () => {
    knowledgeLoading.value = true;
    try {
        const res = await fetch('/api/v1/knowledge/list');
        if (res.ok) {
            let docs = await res.json();
            // Filter by current agent if agent has bindings
            if (currentAgent.value && currentAgent.value.knowledge_config && currentAgent.value.knowledge_config.document_ids) {
                const boundIds = currentAgent.value.knowledge_config.document_ids;
                if (boundIds.length > 0) {
                   docs = docs.filter(d => boundIds.includes(d.id));
                }
            }
            knowledgeDocs.value = docs;
        } else {
            message.error('获取知识库文档失败');
        }
    } catch (e) {
        console.error(e);
        message.error('获取知识库文档出错');
    } finally {
        knowledgeLoading.value = false;
    }
};

const filteredKnowledgeDocs = computed(() => {
    if (!knowledgeSearchKeyword.value) return knowledgeDocs.value;
    const kw = knowledgeSearchKeyword.value.toLowerCase();
    return knowledgeDocs.value.filter(d => d.filename.toLowerCase().includes(kw));
});

const onKnowledgeSelectChange = (selectedKeys) => {
    selectedKnowledgeRowKeys.value = selectedKeys;
};

const handleAttachmentOk = () => {
    // Merge local and knowledge attachments
    const localAtts = localFileList.value.map(f => ({ type: 'local', name: f.name, size: f.size, file: f }));
    const knowledgeAtts = knowledgeDocs.value
        .filter(d => selectedKnowledgeRowKeys.value.includes(d.id))
        .map(d => ({ type: 'knowledge', name: d.filename, size: d.file_size, id: d.id, file: null }));
    
    selectedAttachments.value = [...localAtts, ...knowledgeAtts];
    attachmentModalVisible.value = false;
    message.success(`已选择 ${selectedAttachments.value.length} 个附件`);
};

const removeAttachment = (index) => {
    selectedAttachments.value.splice(index, 1);
};

// API Helpers
const fetchAgents = async () => {
    try {
        const res = await fetch('/api/v1/agents/');
        if (res.ok) {
            agents.value = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch agents", e);
    }
};

const fetchSessions = async () => {
    try {
        const res = await fetch('/api/v1/chat/sessions');
        if (res.ok) {
            sessions.value = await res.json();
            // Select first session if exists and none selected
            if (sessions.value.length > 0 && !currentSessionId.value) {
                selectSession(sessions.value[0]);
            }
        }
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    }
};

const selectSession = async (session) => {
    currentSessionId.value = session.id;
    selectedAgentId.value = session.agent_id || '';
    
    // Fetch details (messages)
    try {
        const res = await fetch(`/api/v1/chat/sessions/${session.id}`);
        if (res.ok) {
            const data = await res.json();
            messages.value = data.messages || [];
            scrollToBottom();
            
            // Render Amis charts if any
            nextTick(() => {
                messages.value.forEach((msg, idx) => {
                    if (msg.role === 'assistant' && isAmisJSON(msg.content)) {
                        renderAmis(idx, msg.content);
                    }
                });
            });
        }
    } catch (e) {
        console.error("Failed to fetch session details", e);
    }
};

const createNewSession = async () => {
    try {
        const res = await fetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                title: '新对话',
                agent_id: selectedAgentId.value || null 
            })
        });
        if (res.ok) {
            const newSession = await res.json();
            sessions.value.unshift(newSession);
            selectSession(newSession);
        }
    } catch (e) {
        console.error("Failed to create session", e);
    }
};

const deleteSession = (id) => {
    Modal.confirm({
        title: '确定要删除此对话吗？',
        icon: createVNode(ExclamationCircleOutlined),
        content: '删除后将无法恢复，请谨慎操作。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                const res = await fetch(`/api/v1/chat/sessions/${id}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    sessions.value = sessions.value.filter(s => s.id !== id);
                    if (currentSessionId.value === id) {
                        currentSessionId.value = null;
                        messages.value = [];
                        // If there are other sessions, select the first one
                        if (sessions.value.length > 0) {
                            selectSession(sessions.value[0]);
                        } else {
                            // Reset agent selection if no sessions left
                            selectedAgentId.value = '';
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to delete session", e);
            }
        }
    });
};

const handleAgentChange = async () => {
    // If we have an empty session selected, update its agent immediately
    if (messages.value.length === 0 && currentSessionId.value) {
        try {
            console.log("Updating session agent:", currentSessionId.value, selectedAgentId.value);
            const res = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: selectedAgentId.value || null })
            });
            if (!res.ok) throw new Error(res.statusText);
            
            // Update local session list if needed (though agent_id isn't displayed in list usually)
            const sess = sessions.value.find(s => s.id === currentSessionId.value);
            if (sess) sess.agent_id = selectedAgentId.value;
        } catch (e) {
            console.error("Failed to update session agent", e);
        }
    }
};

const sendMessage = async () => {
    if (!input.value.trim() || isLoading.value) return;
    
    isLoading.value = true;
    
    // Prepare attachments (Upload local files)
    let attachmentIds = [];
    if (selectedAttachments.value.length > 0) {
        const localFiles = selectedAttachments.value.filter(a => a.type === 'local');
        const knowledgeFiles = selectedAttachments.value.filter(a => a.type === 'knowledge');
        
        // Add existing knowledge IDs
        knowledgeFiles.forEach(att => attachmentIds.push(att.id));
        
        // Upload local files
        for (const att of localFiles) {
            const formData = new FormData();
            formData.append('file', att.file);
            try {
                const res = await fetch('/api/v1/knowledge/upload', {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    const doc = await res.json();
                    attachmentIds.push(doc.id);
                } else {
                    message.error(`附件上传失败: ${att.name}`);
                }
            } catch (e) {
                console.error(e);
                message.error(`附件上传出错: ${att.name}`);
            }
        }
    }
    
    // Auto-create session if none exists
    if (!currentSessionId.value) {
        try {
            const res = await fetch('/api/v1/chat/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    title: input.value.slice(0, 20) || '新对话',
                    agent_id: selectedAgentId.value || null 
                })
            });
            if (res.ok) {
                const newSession = await res.json();
                sessions.value.unshift(newSession);
                currentSessionId.value = newSession.id;
            } else {
                throw new Error("Failed to create session");
            }
        } catch (e) {
            console.error(e);
            isLoading.value = false;
            return;
        }
    }
    
    const userMsg = input.value;
    input.value = '';
    selectedAttachments.value = []; // Clear attachments UI
    const textarea = document.querySelector('textarea');
    if (textarea) textarea.style.height = 'auto';

    messages.value.push({ role: 'user', content: userMsg });
    isStreaming.value = false;
    
    scrollToBottom();
    
    try {
        const response = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: userMsg, 
                strict_mode: localStrictMode.value, 
                threshold: localThreshold.value, 
                debug: localDebugMode.value, 
                ab_variant: localABVariant.value,
                attachments: attachmentIds 
            })
        });
        
        if (!response.ok) throw new Error(response.statusText);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        messages.value.push({ role: 'assistant', content: '', reasoning: '' });
        const assistantMsg = messages.value[messages.value.length - 1];
        const assistantMsgIndex = messages.value.length - 1;
        
        isStreaming.value = true;
        
        let fullBuffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            fullBuffer += chunk;
            
            // Streaming parse logic
            const thinkStart = fullBuffer.indexOf('<think>');
            
            if (thinkStart !== -1) {
                const thinkEnd = fullBuffer.indexOf('</think>');
                if (thinkEnd !== -1) {
                    assistantMsg.reasoning = fullBuffer.substring(thinkStart + 7, thinkEnd).trim();
                    const beforeThink = fullBuffer.substring(0, thinkStart);
                    const afterThink = fullBuffer.substring(thinkEnd + 8);
                    assistantMsg.content = (beforeThink + afterThink).trim();
                } else {
                    assistantMsg.reasoning = fullBuffer.substring(thinkStart + 7);
                    assistantMsg.content = fullBuffer.substring(0, thinkStart);
                }
            } else {
                assistantMsg.content = fullBuffer;
            }
            
            scrollToBottom();
        }
        
        if (isAmisJSON(assistantMsg.content)) {
            nextTick(() => renderAmis(assistantMsgIndex, assistantMsg.content));
        }
        
    } catch (e) {
        console.error(e);
        messages.value.push({ role: 'assistant', content: "Error: " + e.message });
    } finally {
        isLoading.value = false;
        isStreaming.value = false;
        scrollToBottom();
    }
};

const scrollToBottom = () => {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
    });
};

const renderMarkdown = (text) => {
    try {
        let html = marked.parse(text || '');
        html = html.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, open, formula) => {
            try { return katex.renderToString(formula, { displayMode: true }); } catch { return match; }
        });
        html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try { return katex.renderToString(formula, { displayMode: false }); } catch { return match; }
        });
        return html;
    } catch (e) {
        return text;
    }
};

const isAmisJSON = (text) => {
    if (!text || !text.trim().startsWith('```json')) return false;
    return text.includes('"type": "page"') || text.includes('"type": "chart"');
};

const renderAmis = (index, content) => {
    const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
    if (jsonMatch && jsonMatch[1]) {
        try {
            const schema = JSON.parse(jsonMatch[1]);
            const container = document.getElementById('amis-' + index);
            if (container && window.amis) {
                window.amis.embed(container, schema);
            }
        } catch (e) {
            console.error("Amis render error", e);
        }
    }
};

</script>

<style scoped>
/* Frame 1321317936 Styles */
.frame1321317936 {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 800px;
  row-gap: 24px;
}

.text-heading {
  padding: 24px 0;
  width: 100%;
  text-align: center;
  line-height: 36px;
  color: #2a2f3c;
  font-family: "PingFang SC", sans-serif;
  font-size: 28px;
  font-weight: 500;
}

.frame367 {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  align-self: stretch;
  justify-content: space-between;
  border: 1px solid #e5e6eb;
  border-radius: 16px;
  box-shadow: 0px 4px 24px 0px #bfcded33;
  background: #ffffff;
  padding: 16px;
  height: 140px;
}

.text2 {
  font-size: 15px;
  line-height: 1.6;
  color: #1e293b;
}

.frame1 {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.frame3 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  /* column-gap: 8px; */
  border-radius: 100px;
  padding: 8px 16px;
  background: #f8fafc;
  border: 1px solid transparent;
}
.frame3:hover {
    border-color: #e2e8f0;
    background: #f1f5f9;
}

.text4 {
  line-height: 18px;
  color: #2a2f3c;
  font-size: 12px;
}

.markdown-body {
    font-size: 14px;
    line-height: 1.6;
    color: #334155;
}
/* Typography */
.markdown-body p { margin-bottom: 0.75em; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body strong { font-weight: 600; color: #1e293b; }
.markdown-body em { font-style: italic; }
/* Headings */
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
    font-weight: 600;
    color: #0f172a;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    line-height: 1.3;
}
.markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3em; }
.markdown-body h2 { font-size: 1.3em; }
.markdown-body h3 { font-size: 1.1em; }
/* Lists */
.markdown-body ul, .markdown-body ol { padding-left: 1.5em; margin-bottom: 0.75em; }
.markdown-body ul { list-style-type: disc; }
.markdown-body ol { list-style-type: decimal; }
/* Code */
.markdown-body pre { background: #f1f5f9; padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 1em; border: 1px solid #e2e8f0; }
.markdown-body code { font-family: monospace; background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-size: 0.9em; }

/* Agent Select Styles */
.agent-selector-container {
    position: relative;
    display: flex;
    align-items: center;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 9999px;
    padding: 2px 4px;
    transition: all 0.3s ease;
}
.agent-selector-container:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.selector-icon {
    margin-left: 8px;
    pointer-events: none;
    z-index: 1;
}
.agent-select-custom {
    width: 100px;
}
.agent-select-custom :deep(.ant-select-selector) {
    padding-left: 8px !important;
    height: 32px !important;
    display: flex;
    align-items: center;
    background-color: transparent !important;
}
.agent-select-custom :deep(.ant-select-selection-item) {
    font-size: 12px;
    font-weight: 500;
    color: #334155;
    line-height: 32px;
}
</style>
<style>
/* Global Dropdown Styles */
.agent-dropdown-custom .ant-select-item {
    font-size: 12px;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 4px;
}
.agent-dropdown-custom .ant-select-item-option-selected {
    background-color: #eff6ff !important;
    color: #2563eb !important;
    font-weight: 500;
}
</style>
