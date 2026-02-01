<template>
  <div class="h-full flex bg-slate-50 overflow-hidden shadow-sm relative bg-animated">
    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-white relative">
        
        <!-- Header (Only show when chatting) -->
        <div v-if="messages.length > 0" class="px-6 py-3 border-b border-figma-border flex justify-between items-center bg-white/80 backdrop-blur-sm z-10">
            <div class="flex items-center gap-3 group">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M13.0556 4.81815H2.94445C2.51489 4.81815 2.16667 5.19803 2.16667 5.66663V14.1515C2.16667 14.6201 2.51489 15 2.94445 15H13.0556C13.4851 15 13.8333 14.6201 13.8333 14.1515V5.66663C13.8333 5.19803 13.4851 4.81815 13.0556 4.81815Z" stroke="white" stroke-width="1.3"/>
                        <path d="M8.00001 4.81818V1.92899L5.66667 1" stroke="white" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div>
                    <h2 class="font-bold text-figma-text text-[14px] m-0 leading-tight">
                        {{ currentSession?.title || '新任务' }}
                    </h2>
                    <div class="flex items-center gap-1 text-[11px] text-figma-notation" v-if="currentAgent">
                        <span>当前智能体:</span>
                        <span class="font-medium text-blue-600">{{ currentAgent.name }}</span>
                    </div>
                </div>
                <button 
                    v-if="currentSessionId"
                    class="p-1 text-figma-disable hover:text-red-500 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                    @click="deleteSession(currentSessionId)"
                    title="删除对话"
                >
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            
            
        </div>

        

        <!-- Welcome / Empty State (Design Implementation) -->
        <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center p-4 md:p-8 bg-white overflow-y-auto relative bg-animated">
             <div class="w-full max-w-[800px] flex flex-col items-center gap-8 md:gap-12">
                <div class="flex flex-col items-center gap-4">
                    <!-- Robot Avatar from Figma 114_14502 -->
                    <div class="w-[94px] h-[94px] flex items-center justify-center mb-2">
                        <img src="/bot.svg" alt="Robot" class="w-full h-full object-contain" />
                    </div>
                    <h1 class="text-[24px] md:text-[28px] text-[#2A2F3C] text-center m-0 leading-tight" style="font-family: 'Alibaba PuHuiTi','PingFang SC','Microsoft YaHei',sans-serif; font-weight:115;">让我们创造点厉害的东西！</h1>
                </div>
                
                <div class="w-full flex flex-col gap-10">
                    <!-- Input Area (Simplified) -->
                    <div class="relative flex flex-col">
                        <div class="flex flex-col gap-2">
                            <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 mb-2 w-full overflow-x-auto custom-scrollbar pb-1">
                                <div v-for="(att, idx) in selectedAttachments" :key="idx" class="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100 flex-shrink-0">
                                    <component :is="att.type === 'local' ? PaperClipOutlined : FileTextOutlined" />
                                    <span class="max-w-[120px] truncate" :title="att.name">{{ att.name }}</span>
                                    <DeleteOutlined class="cursor-pointer hover:text-red-500 ml-1" @click="removeAttachment(idx)" />
                                </div>
                            </div>
                            <textarea 
                                v-model="input" 
                                @keydown="onInputKeydown"
                                class="textarea-modern pr-10 pb-12"
                                placeholder="描述您需要帮助的内容..."
                                :disabled="isLoading"
                                style="height: 140px;"
                            ></textarea>
                        </div>
                        
                        <!-- Footer Area (Embedded inside textarea container) -->
                        <div class="absolute bottom-2 left-2 right-2 flex justify-between items-center h-8">
                             <!-- Left: Attachment -->
                             <button @click="openAttachmentModal" class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-figma-hover transition-colors text-figma-notation border border-[#F2F3F5]">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M13.8933 7.41333L7.78667 13.52C6.33333 15.0267 3.93333 15.0267 2.48 13.52C1.02667 12.0667 1.02667 9.66667 2.48 8.21333L8.58667 2.10667C9.54667 1.14667 11.1467 1.14667 12.1067 2.10667C13.0667 3.06667 13.0667 4.66667 12.1067 5.62667L6 11.7333C5.52 12.2133 4.72 12.2133 4.24 11.7333C3.76 11.2533 3.76 10.4533 4.24 9.97333L9.81333 4.4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                             </button>
                             
                             <!-- Right: Agent Selector & Send Button -->
                             <div class="flex items-center gap-3">
                                 <!-- Agent Selector (Fidelity Implementation) -->
                                 <div class="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-figma-hover cursor-pointer transition-all group border border-transparent hover:border-figma-border relative" @click="agentSelectOpen = true">
                                    <!-- Gradient Icon BG -->
                                    <div class="w-5 h-5 rounded-[6px] flex items-center justify-center overflow-hidden bg-gradient-to-br  flex-shrink-0">
                                        <img v-if="currentAgent && currentAgent.icon_url" :src="currentAgent.icon_url" alt="" class="w-3 h-3 object-contain" />
                                        <img v-else src="/tiga.svg" alt="" class="w-4 h-4 object-contain" />
                                    </div>
                                    <a-select 
                                        v-model:value="selectedAgentId" 
                                        @change="handleAgentChange"
                                        class="agent-select-figma"
                                        :bordered="false"
                                        size="small"
                                        popupClassName="agent-dropdown-custom"
                                        v-model:open="agentSelectOpen"
                                        @update:open="val => agentSelectOpen = val"
                                        @dropdownVisibleChange="val => agentSelectOpen = val"
                                        :getPopupContainer="getPopupContainerForSelect"
                                        :dropdownMatchSelectWidth="false"
                                    >
                                        <a-select-option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</a-select-option>
                                    </a-select>
                                    <!-- Custom Chevron -->
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#858B9B" stroke-width="2.5" class="ml-1 group-hover:stroke-figma-text transition-colors"><path d="M6 9l6 6 6-6"/></svg>
                                 </div>

                                 <!-- Send Button (Circle Blue) -->
                                 <button 
                                    @click="sendMessage" 
                                    class="w-8 h-8 flex items-center justify-center rounded-[24px] transition-all active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed"
                                    :class="input.trim() ? 'bg-gradient-to-r from-[#0056E8] to-[#387BFF] text-white shadow-lg shadow-blue-200 hover:brightness-110' : 'bg-[#E5E6EB] text-[#BCC1CD] shadow-none'"
                                    :disabled="!input.trim() || isLoading"
                                 >
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M8 13V3M8 3L4 7M8 3L12 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                 </button>
                             </div>
                        </div>
                    </div>

                    <!-- Scripts Section (Frame 1321318130) -->
                    <div v-if="userScripts.length > 0" class="flex flex-col gap-3 px-1">
                        <span class="text-[13px] font-medium text-[#495363] px-3">剧本</span>
                        <div class="flex flex-wrap gap-3 overflow-x-auto pb-2 custom-scrollbar">
                            <div 
                                v-for="s in userScripts" 
                                :key="s.id" 
                                class="flex items-center gap-2 px-4 py-2 bg-white hover:bg-figma-hover transition-all cursor-pointer rounded-full border border-[#F2F3F5] group shadow-sm flex-shrink-0" 
                                @click="sendQuickMessage(s.content)"
                            >
                                <div class="w-4 h-4 flex items-center justify-center text-[#858B9B] group-hover:text-figma-text">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M6 2H4.66667C3.19391 2 2 3.19391 2 4.66667V11.3333C2 12.8061 3.19391 14 4.66667 14H11.3333C12.8061 14 14 12.8061 14 11.3333V4.66667C14 3.19391 12.8061 2 11.3333 2H10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M6 1V3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M10 1V3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M5 7H11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M5 10H9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                </div>
                                <span class="text-[12px] text-[#858B9B] group-hover:text-figma-text whitespace-nowrap">{{ s.title }}</span>
                            </div>
                        </div>
                    </div>
                </div>
             </div>
        </div>

        <!-- Messages List (Standard Chat) -->
        <div v-else class="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" 
                 :class="['flex gap-4 max-w-4xl mx-auto', msg.role === 'user' ? 'flex-row-reverse' : '']">
                <!-- Avatar -->
                <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm overflow-hidden"
                     :class="msg.role === 'user' ? 'bg-blue-600 border-2 border-white' : 'border border-slate-200'">
                     <img v-if="msg.role === 'user'" src="https://api.dicebear.com/7.x/notionists/svg?seed=Admin" alt="user avatar" class="w-full h-full object-cover" />
                     <img v-else-if="currentAgent && currentAgent.icon_url" :src="currentAgent.icon_url" alt="agent avatar" class="w-full h-full object-cover" />
                     <img v-else src="/tiga.svg" alt="agent avatar" class="w-full h-full object-cover" />
                </div>
                
                <!-- Content -->
                <div :class="[msg.role === 'user' ? 'bubble-user' : 'bubble-assistant']">
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
        <div class="p-4 bg-white z-10" v-if="currentSessionId && messages.length > 0">
            <div class="max-w-4xl mx-auto relative">
                <div class="relative">
                  <textarea 
                    v-model="input" 
                    @keydown="onInputKeydown"
                    rows="1"
                    placeholder="输入您的问题，按 Enter 发送..." 
                    class="textarea-modern pr-10"
                    :disabled="isLoading"
                    style="min-height: 52px; max-height: 120px;"
                    @input="adjustHeight"
                  ></textarea>
                  <button 
                    @click="sendMessage"
                    class="absolute right-3 top-1/2 -translate-y-1/2 transition-all duration-200"
                    :class="input.trim() && !isLoading ? 'text-blue-600 hover:text-blue-700' : 'text-slate-400 cursor-not-allowed'"
                    :disabled="isLoading || !input.trim()"
                  >
                      <svg class="w-5 h-5 mx-auto transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
                  </button>
                </div>
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

const props = defineProps({
    sessionId: {
        type: String,
        default: null
    }
});
const emit = defineEmits(['refresh-sessions']);
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Modal, message } from 'ant-design-vue';
import ReferencesTable from './ReferencesTable.vue';
import ReferencesCards from './ReferencesCards.vue';
import { ExclamationCircleOutlined, PaperClipOutlined, FileTextOutlined, DeleteOutlined, InboxOutlined, SearchOutlined } from '@ant-design/icons-vue';

const input = ref('');
const messages = ref([]);
const currentSession = ref(null);
const agents = ref([]);
const currentSessionId = ref(props.sessionId);
const selectedAgentId = ref('');
const agentSelectOpen = ref(false);
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);

const currentAgent = computed(() => agents.value.find(a => a.id === selectedAgentId.value));

const getPopupContainerForSelect = () => {
    if (typeof window !== 'undefined' && window.document && window.document.body) {
        return window.document.body;
    }
    return undefined;
};

const getDefaultAgentId = (list) => {
    let saved = '';
    try {
        saved = localStorage.getItem('defaultAgentId') || '';
    } catch {}
    if (saved && list.some(a => a.id === saved)) return saved;
    const generic = list.find(a => a.name && (a.name === '通用' || a.name.includes('通用')));
    if (generic) return generic.id;
    return list.length ? list[0].id : '';
};

onMounted(() => {
    fetchAgents();
    if (currentSessionId.value) {
        fetchSessionDetails(currentSessionId.value);
    }
    fetchUserScripts(selectedAgentId.value);
    nextTick(() => {
        const ta = document.querySelector('textarea');
        if (ta) ta.focus();
    });
});

watch(() => props.sessionId, (newId) => {
    currentSessionId.value = newId;
    if (newId) {
        fetchSessionDetails(newId);
    } else {
        currentSession.value = null;
        messages.value = [];
    }
});
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
watch(selectedAgentId, (nv) => {
    fetchUserScripts(nv);
    try {
        if (nv) localStorage.setItem('defaultAgentId', nv);
    } catch {}
});

const adjustHeight = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
};

const onInputKeydown = (e) => {
    if (e.key === 'Enter') {
        if (e.shiftKey) return;
        e.preventDefault();
        sendMessage();
    }
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
            const data = await res.json();
            agents.value = data;
            if (!selectedAgentId.value && data.length > 0) {
                const did = getDefaultAgentId(data);
                selectedAgentId.value = did;
                fetchUserScripts(did);
            }
        }
    } catch (e) {
        console.error("Failed to fetch agents", e);
    }
};

const fetchSessionDetails = async (id) => {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${id}`);
        if (res.ok) {
            const data = await res.json();
            currentSession.value = data;
            selectedAgentId.value = data.agent_id || '';
            messages.value = data.messages || [];
            scrollToBottom();
            if (!selectedAgentId.value && agents.value.length > 0) {
                selectedAgentId.value = getDefaultAgentId(agents.value);
            }
            
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

// No createNewSession here, handled by App.vue

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
                    emit('refresh-sessions'); // Notify App.vue
                    if (currentSessionId.value === id) {
                        currentSessionId.value = null;
                        currentSession.value = null;
                        messages.value = [];
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
            
            if (currentSession.value) {
                currentSession.value.agent_id = selectedAgentId.value;
            }
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
    
    // Push user message to UI immediately
    const userMsg = input.value;
    input.value = '';
    selectedAttachments.value = []; // Clear attachments UI
    const textarea = document.querySelector('textarea');
    if (textarea) textarea.style.height = 'auto';
    messages.value.push({ role: 'user', content: userMsg });
    isStreaming.value = false;
    scrollToBottom();
    
    // Auto-create session if none exists
    if (!currentSessionId.value) {
        try {
            const res = await fetch('/api/v1/chat/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    title: (userMsg && userMsg.slice(0, 20)) || '新对话',
                    agent_id: selectedAgentId.value || null 
                })
            });
            if (res.ok) {
                const newSession = await res.json();
                emit('refresh-sessions');
                currentSessionId.value = newSession.id;
                currentSession.value = newSession;
            } else {
                throw new Error("Failed to create session");
            }
        } catch (e) {
            console.error(e);
            messages.value.push({ role: 'assistant', content: "Error: 会话创建失败" });
            isLoading.value = false;
            return;
        }
    }
    
    try {
        const response = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: userMsg, 
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

        // [Feature] Support in-text entity citations: [[Entity: Name]]
        inputText = inputText.replace(/\[\[Entity:\s*(.*?)\]\]/g, '<span class="entity-citation" data-entity="$1">$1</span>');

        // [Fix] Handle multi-layered brackets like [[[1]]], [[ [1] ]], or [[Source: 1]]
        // Consolidate all citation patterns into a single unified format [n]
        inputText = inputText.replace(/\[+[\s\t]*(?:Source:[\s\t]*)?(\d+)[\s\t]*\]+/gi, '[$1]');

        // Final rendering of citations [n] as superscripts
        inputText = inputText.replace(/\[(\d+)\]/g, '<sup class="chunk-citation" data-id="$1">[$1]</sup>');

        let html = marked.parse(inputText);
        html = html.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, open, formula) => {
            try { return katex.renderToString(formula, { displayMode: true }); } catch { return match; }
        });
        html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try { return katex.renderToString(formula, { displayMode: false }); } catch { return match; }
        });
        html = html.replace(/<p>\s*<\/p>/g, '');
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
.custom-scrollbar::-webkit-scrollbar {
  height: 4px;
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e5e6eb;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #bcc1cd;
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

/* Citations Styling */
:deep(.entity-citation) {
    color: #2563eb;
    background-color: #eff6ff;
    padding: 0px 4px;
    border-radius: 4px;
    border-bottom: 1px dashed #3b82f6;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}
:deep(.entity-citation:hover) {
    background-color: #dbeafe;
    border-bottom-style: solid;
}

:deep(.chunk-citation) {
    color: #6366f1;
    font-weight: bold;
    cursor: help;
    margin-left: 2px;
    padding: 0 2px;
}
:deep(.chunk-citation:hover) {
    text-decoration: underline;
}

/* Agent Select Figma Styles */
:deep(.agent-select-figma .ant-select-selector) {
    padding: 0 !important;
    height: 24px !important;
    line-height: 24px !important;
}
:deep(.agent-select-figma .ant-select-selection-item) {
    font-size: 12px !important;
    color: #000000 !important;
    font-weight: 400 !important;
    padding-inline-end: 4px !important;
}
:deep(.agent-select-figma .ant-select-arrow) {
    display: none !important;
}

.bubble-user {
    max-width: 85%;
    padding: 10px 12px;
    border-radius: 14px 14px 4px 14px;
    background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
    color: #ffffff;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.18);
    font-size: 12px;
    line-height: 1.6;
}
.bubble-assistant {
    max-width: 85%;
    padding: 10px 12px;
    border-radius: 14px 14px 14px 4px;
    background: #ffffff;
    border: 1px solid #e6eaf2;
    color: #334155;
    box-shadow: 0 6px 18px rgba(191, 205, 237, 0.25);
    font-size: 12px;
    line-height: 1.6;
}
/* Ensure markdown spacing doesn't inflate bubble height */
.bubble-assistant .markdown-body,
.bubble-user .markdown-body {
    font-size: inherit;
    line-height: inherit;
}
.bubble-assistant .markdown-body p,
.bubble-user .markdown-body p {
    margin: 0;
}
.bubble-assistant .markdown-body p:empty,
.bubble-user .markdown-body p:empty {
    display: none;
}

.absolute.w-\[7px\].h-\[3px\].bg-blue-500.rounded-full {
    display: none !important;
}
.bg-animated::before {
    content: "";
    position: absolute;
    inset: -20%;
    background:
      radial-gradient(circle at 20% 20%, rgba(0,86,232,0.40), transparent 60%),
      radial-gradient(circle at 80% 30%, rgba(56,123,255,0.38), transparent 55%),
      radial-gradient(circle at 30% 80%, rgba(16,185,129,0.26), transparent 55%);
    filter: blur(24px);
    animation: none;
    display: none;
    pointer-events: none;
    z-index: 0;
    transform: translate3d(0,0,0);
}
@keyframes bgFloat {
    0% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-6px) rotate(180deg); }
    100% { transform: translateY(0) rotate(360deg); }
}

/* Hollow Tiga word in background */
.bg-animated::after {
    content: "Tiga";
    position: absolute;
    left: 50%;
    top: 42%;
    transform: translate(-50%, -50%) rotate(-8deg);
    font-family: 'Alibaba PuHuiTi','PingFang SC','Microsoft YaHei',sans-serif;
    font-weight: 700;
    font-size: clamp(140px, 26vw, 380px);
    letter-spacing: 0.06em;
    color: transparent;
    -webkit-text-stroke: 0.8px rgba(0,86,232,0.18);
    text-stroke: 0.8px rgba(0,86,232,0.18);
    opacity: 0.12;
    pointer-events: none;
    z-index: 0;
}
 
.textarea-modern {
    width: 100%;
    padding: 12px 14px;
    background: #ffffff;
    border: 1px solid #E6EAF2;
    border-radius: 14px;
    color: #334155;
    font-size: 14px;
    line-height: 1.6;
    transition: border-color .2s ease, box-shadow .2s ease, background .2s ease;
}
.textarea-modern::placeholder {
    color: #9AA4B2;
}
.textarea-modern:focus {
    outline: none;
    border-color: #60A5FA;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.25);
}
.textarea-modern:disabled {
    background: #F7F7FA;
    color: #A0AEC0;
    cursor: not-allowed;
}
</style>
<style>
/* Global Dropdown Styles */
.agent-dropdown-custom .ant-select-item {
    font-size: 13px;
    padding: 8px 12px;
}
.agent-dropdown-custom .ant-select-item-option-selected {
    background-color: #F2F3F5 !important;
    color: #171717 !important;
    font-weight: 500;
}
</style>
<style>
/* Alibaba PuHuiTi Webfont (CDN) */
@font-face {
    font-family: 'Alibaba PuHuiTi';
    font-weight: 300;
    font-style: normal;
    font-display: swap;
    src: url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-45-Light/AlibabaPuHuiTi-2-45-Light.woff2') format('woff2'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-45-Light/AlibabaPuHuiTi-2-45-Light.woff') format('woff'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-45-Light/AlibabaPuHuiTi-2-45-Light.ttf') format('truetype');
}
@font-face {
    font-family: 'Alibaba PuHuiTi';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-55-Regular/AlibabaPuHuiTi-2-55-Regular.woff2') format('woff2'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-55-Regular/AlibabaPuHuiTi-2-55-Regular.woff') format('woff'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-55-Regular/AlibabaPuHuiTi-2-55-Regular.ttf') format('truetype');
}
@font-face {
    font-family: 'Alibaba PuHuiTi';
    font-weight: 500;
    font-style: normal;
    font-display: swap;
    src: url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-65-Medium/AlibabaPuHuiTi-2-65-Medium.woff2') format('woff2'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-65-Medium/AlibabaPuHuiTi-2-65-Medium.woff') format('woff'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-65-Medium/AlibabaPuHuiTi-2-65-Medium.ttf') format('truetype');
}
@font-face {
    font-family: 'Alibaba PuHuiTi';
    font-weight: 600;
    font-style: normal;
    font-display: swap;
    src: url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-75-SemiBold/AlibabaPuHuiTi-2-75-SemiBold.woff2') format('woff2'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-75-SemiBold/AlibabaPuHuiTi-2-75-SemiBold.woff') format('woff'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-75-SemiBold/AlibabaPuHuiTi-2-75-SemiBold.ttf') format('truetype');
}
@font-face {
    font-family: 'Alibaba PuHuiTi';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-85-Bold/AlibabaPuHuiTi-2-85-Bold.woff2') format('woff2'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-85-Bold/AlibabaPuHuiTi-2-85-Bold.woff') format('woff'),
         url('https://puhuiti.oss-cn-hangzhou.aliyuncs.com/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-85-Bold/AlibabaPuHuiTi-2-85-Bold.ttf') format('truetype');
}
</style>
