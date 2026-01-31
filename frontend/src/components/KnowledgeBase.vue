<template>
  <div class="h-full flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden frame664">
    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col p-6 gap-4">
        
        <!-- Header / Tabs -->
        <div class="flex flex-col gap-6">
            <h2 class="text-xl font-bold text-[#171717]">知识库</h2>
            
            <div class="flex items-center gap-8 border-b border-slate-100 pb-0">
                <div 
                    class="cursor-pointer pb-2 text-base font-medium transition-colors relative"
                    :class="activeTab === 'shared' ? 'text-[#171717]' : 'text-[#858b9b]'"
                    @click="activeTab = 'shared'"
                >
                    共享
                    <div v-if="activeTab === 'shared'" class="absolute bottom-0 left-0 w-full h-0.5 bg-[#171717]"></div>
                </div>
                <div 
                    class="cursor-pointer pb-2 text-base font-medium transition-colors relative"
                    :class="activeTab === 'personal' ? 'text-[#171717]' : 'text-[#858b9b]'"
                    @click="activeTab = 'personal'"
                >
                    个人
                    <div v-if="activeTab === 'personal'" class="absolute bottom-0 left-0 w-full h-0.5 bg-[#171717]"></div>
                </div>
            </div>
        </div>

        <!-- Toolbar -->
        <div class="flex justify-between items-center mt-2">
            <!-- Left: Search and File Count/Title -->
            <div class="flex items-center gap-4 flex-1">
                 <span class="text-base font-medium text-[#2a2f3c]">全部文件</span>
                 <div class="flex items-center gap-2 px-3 py-1.5 border border-[#c9cdd4] rounded-lg bg-white w-[330px]">
                     <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                     <input type="text" placeholder="请输入名称或关键词进行搜索" class="flex-1 text-sm outline-none text-[#2a2f3c] placeholder-[#bcc1cd]">
                 </div>
            </div>

            <!-- Right: Actions -->
            <div class="flex items-center gap-3">
                 <input 
                    type="file" 
                    ref="fileInput" 
                    class="hidden" 
                    @change="handleFileUpload" 
                    accept=".pdf,.txt,.md,.doc,.docx"
                >
                <button 
                    @click="$refs.fileInput.click()"
                    class="flex items-center gap-1 px-4 py-1.5 bg-[#171717] text-white rounded-xl text-sm hover:bg-slate-800 transition-colors"
                    :disabled="uploading"
                >
                    <span v-if="uploading">上传中...</span>
                    <span v-else>上传文件</span>
                </button>
                <button class="flex items-center gap-1 px-4 py-1.5 border border-[#c9cdd4] text-[#2a2f3c] rounded-xl text-sm hover:bg-slate-50 transition-colors">
                    新建文件夹
                </button>
            </div>
        </div>

        <!-- Format Hint -->
        <div class="bg-[#f7f7f7] rounded-lg px-3 py-2 flex items-center gap-2 text-[11px]">
            <span class="text-[#2a2f3c]">支持格式：</span>
            <span class="text-[#ff7300]">PDF, DOC, DOCX, XLS, XLSX 格式文件</span>
            <span class="text-[#2a2f3c]">大小限制： 请确保文件小于</span>
            <span class="text-[#ff7300]">100MB</span>
        </div>

        <!-- File List Table -->
        <div class="flex-1 overflow-auto mt-2">
            <Loading v-if="loading" type="skeleton-list" />
            <div v-else class="min-w-full">
                <!-- Table Header -->
                <div class="flex items-center bg-[#f9f9fa] h-[38px] rounded px-3 text-xs font-medium text-[#2a2f3c]">
                    <div class="flex-1 flex items-center gap-2 relative">
                        <span>文件名称</span>
                        <div class="flex flex-col gap-0.5">
                             <svg class="w-2 h-1 text-slate-400" fill="none" viewBox="0 0 10 5" stroke="currentColor"><path d="M5 0L10 5H0L5 0Z" fill="currentColor"/></svg>
                             <svg class="w-2 h-1 text-slate-400" fill="none" viewBox="0 0 10 5" stroke="currentColor"><path d="M5 5L0 0H10L5 5Z" fill="currentColor"/></svg>
                        </div>
                        <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
                    </div>
                    <div class="w-[100px] px-3 relative">
                        <span>大小</span>
                        <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
                    </div>
                    <div class="w-[180px] px-3 relative">
                        <span>上传/创建时间</span>
                        <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
                    </div>
                    <div class="w-[180px] px-3 relative flex items-center gap-2">
                        <span>解析方式</span>
                        <svg class="w-3 h-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
                    </div>
                    <div class="w-[100px] px-3">
                        <span>操作</span>
                    </div>
                </div>

                <!-- Table Body -->
                <div class="flex flex-col">
                    <div v-if="files.length === 0 && !uploading" class="py-12 flex flex-col items-center justify-center text-slate-400 text-sm">
                        暂无文件
                    </div>
                    
                    <div 
                        v-for="file in files" 
                        :key="file.id" 
                        class="flex items-center border-b border-slate-50 hover:bg-[#eeeeee] transition-colors py-2 px-3 text-sm text-[#2a2f3c]"
                    >
                        <!-- Name -->
                        <div class="flex-1 flex items-center gap-2 overflow-hidden">
                             <!-- File Icon Placeholder -->
                             <div class="w-6 h-6 flex items-center justify-center bg-white border border-[#bcc1cd] rounded">
                                 <svg class="w-3 h-3 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                             </div>
                             <span class="truncate">{{ file.filename }}</span>
                        </div>
                        
                        <!-- Size -->
                        <div class="w-[100px] px-3 text-slate-500">
                            {{ formatSize(file.file_size) }}
                        </div>
                        
                        <!-- Time -->
                        <div class="w-[180px] px-3 text-slate-500">
                            {{ formatDate(file.created_at) }}
                        </div>
                        
                        <!-- Status -->
                        <div class="w-[180px] px-3">
                            <!-- Progress Bar for active states -->
                            <div v-if="['uploading', 'indexing'].includes(file.status)" class="w-full pr-4">
                                <div class="flex justify-between items-center mb-1.5">
                                    <span class="text-xs text-blue-600 font-medium">
                                        {{ file.status === 'uploading' ? '上传中' : '解析中' }}
                                    </span>
                                    <span class="text-[10px] text-slate-400">进行中</span>
                                </div>
                                <div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                     <div class="h-full bg-blue-500 rounded-full w-full relative overflow-hidden">
                                         <div class="absolute inset-0 bg-white/30 w-full h-full animate-shimmer"></div>
                                     </div>
                                </div>
                            </div>
                            
                            <!-- Standard Badge for other states -->
                            <div v-else class="flex items-center gap-2 px-2 py-1 bg-slate-100 rounded border border-slate-200 w-fit">
                                <span class="w-2 h-2 rounded-full" 
                                    :class="{
                                        'bg-green-500': file.status === 'indexed',
                                        'bg-red-500': file.status === 'failed'
                                    }"
                                ></span>
                                <span class="text-xs">
                                    {{ file.status === 'indexed' ? '智能解析' : '解析失败' }}
                                </span>
                            </div>
                        </div>
                        
                        <!-- Actions -->
                        <div class="w-[100px] px-3 flex items-center gap-3">
                            <button 
                                v-if="file.status === 'indexed'"
                                @click="viewGraph(file)" 
                                class="text-slate-400 hover:text-blue-600" 
                                title="查看知识图谱"
                            >
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path></svg>
                            </button>
                            <button @click="deleteFile(file.id)" class="text-slate-400 hover:text-red-600" title="删除文件">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Graph Modal -->
        <a-modal
            v-model:open="graphVisible"
            width="95%"
            :style="{ top: '20px' }"
            :footer="null"
            destroyOnClose
            class="graph-modal"
        >
            <template #title>
                <span :title="currentGraphTitle" class="cursor-help">
                    {{ currentGraphTitle.length > 20 ? currentGraphTitle.slice(0, 20) + '...' : currentGraphTitle }}
                </span>
            </template>
            <div class="flex h-[80vh] overflow-hidden">
                <!-- Left: Graph -->
                <div class="flex-1 border-r border-slate-200 pr-4 relative">
                    <div v-if="graphLoading" class="h-full flex flex-col items-center justify-center p-8 gap-4">
                        <!-- Skeleton for Graph -->
                        <div class="w-full h-full bg-slate-50 rounded-xl animate-pulse relative overflow-hidden">
                            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
                                <div class="w-16 h-16 rounded-full bg-slate-200 mb-4"></div>
                                <div class="w-32 h-4 bg-slate-200 rounded"></div>
                            </div>
                            <!-- Random Nodes -->
                            <div class="absolute top-1/4 left-1/4 w-12 h-12 rounded-full bg-slate-200"></div>
                            <div class="absolute bottom-1/4 right-1/4 w-10 h-10 rounded-full bg-slate-200"></div>
                            <div class="absolute top-1/3 right-1/3 w-8 h-8 rounded-full bg-slate-200"></div>
                        </div>
                    </div>
                    <GraphViewer v-else :nodes="graphNodes" :edges="graphEdges" />
                </div>

                <!-- Right: Chat -->
                <div class="w-[400px] flex flex-col pl-4 bg-white relative">
                    
                    <!-- Messages Area -->
                    <div class="flex-1 overflow-y-auto space-y-6 pr-2 mb-4 pt-4" ref="chatContainer">
                        <!-- Empty State -->
                        <div v-if="chatMessages.length === 0" class="h-full flex flex-col items-center justify-center text-center px-6">
                            <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
                                <svg class="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                            </div>
                            <h3 class="text-base font-medium text-slate-800 mb-2">文档问答助手</h3>
                            <p class="text-sm text-slate-500 leading-relaxed">
                                我已阅读完当前文档，您可以问我任何关于文档内容的问题，我会结合知识图谱为您解答。
                            </p>
                            <div class="mt-8 grid grid-cols-1 gap-2 w-full">
                                <div class="px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs rounded-lg cursor-pointer transition-colors border border-slate-100 text-left" @click="chatInput = '这份文档主要讲了什么？'; sendChatMessage()">
                                    这份文档主要讲了什么？
                                </div>
                                <div class="px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs rounded-lg cursor-pointer transition-colors border border-slate-100 text-left" @click="chatInput = '有哪些关键实体和关系？'; sendChatMessage()">
                                    有哪些关键实体和关系？
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
                                <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-1">
                                    <svg class="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                                <div class="flex flex-col gap-2 max-w-[90%]">
                                    <div class="p-3 bg-slate-50 text-slate-800 rounded-2xl rounded-tl-sm text-sm leading-relaxed border border-slate-100">
                                        {{ msg.content }}
                                    </div>
                                    
                                    <!-- Sources -->
                                    <div v-if="msg.sources && msg.sources.length > 0" class="flex flex-col gap-1 mt-1">
                                        <div class="text-[10px] text-slate-400 font-medium uppercase tracking-wider pl-1">参考来源</div>
                                        <div class="flex flex-wrap gap-1.5">
                                            <div v-for="(src, idx) in msg.sources.slice(0, 3)" :key="idx" 
                                                class="px-2 py-1 bg-white border border-slate-200 rounded text-[10px] text-slate-500 truncate max-w-[200px] hover:bg-slate-50 hover:border-slate-300 transition-colors cursor-help"
                                                :title="src.content"
                                            >
                                                <span class="font-bold text-blue-500 mr-1">{{ src.source.toUpperCase() }}</span>
                                                {{ src.content.slice(0, 15) }}...
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Loading State -->
                        <div v-if="chatLoading" class="flex gap-3">
                            <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-1">
                                <svg class="w-4 h-4 text-indigo-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <div class="flex items-center gap-1 p-3 bg-slate-50 rounded-2xl rounded-tl-sm w-fit">
                                <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                                <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                                <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Input Area -->
                    <div class="mt-auto pt-4 border-t border-slate-100 bg-white">
                        <div class="relative">
                            <input 
                                v-model="chatInput" 
                                @keyup.enter="sendChatMessage"
                                type="text" 
                                placeholder="输入问题..." 
                                class="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all placeholder:text-slate-400"
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
                        <div class="text-[10px] text-center text-slate-300 mt-2 pb-1">
                            由混合检索引擎提供支持 (BM25 + Vector + Graph)
                        </div>
                    </div>
                </div>
            </div>
        </a-modal>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, createVNode } from 'vue';
import axios from 'axios';
import { message, Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import Loading from './common/Loading.vue';
import GraphViewer from './common/GraphViewer.vue';

const files = ref([]);
const uploading = ref(false);
const loading = ref(true);
const activeTab = ref('personal'); // shared | personal
const api = axios.create({ baseURL: '/api/v1' }); // Use relative path
let pollTimer = null;

// Graph State
const graphVisible = ref(false);
const graphNodes = ref({});
const graphEdges = ref({});
const currentGraphTitle = ref('');
const graphLoading = ref(false);
const currentDocId = ref(null);

// Chat State
const chatMessages = ref([]);
const chatInput = ref('');
const chatLoading = ref(false);
const chatContainer = ref(null);

const viewGraph = async (file) => {
    currentGraphTitle.value = file.filename;
    currentDocId.value = file.id;
    graphVisible.value = true;
    graphLoading.value = true;
    graphNodes.value = {};
    graphEdges.value = {};
    
    // Reset Chat
    chatMessages.value = [];
    chatInput.value = '';
    
    try {
        const res = await api.get(`/knowledge/${file.id}/graph`);
        if (res.data) {
            graphNodes.value = res.data.nodes || {};
            graphEdges.value = res.data.edges || {};
        }
    } catch (e) {
        console.error(e);
        message.error("获取图谱数据失败: " + (e.response?.data?.detail || e.message));
        // Mock data for demo if failed (optional, but good for user experience during dev)
        // In real prod, maybe show empty state
    } finally {
        graphLoading.value = false;
    }
};

const sendChatMessage = async () => {
    if (!chatInput.value.trim() || !currentDocId.value) return;
    
    const query = chatInput.value;
    chatMessages.value.push({ role: 'user', content: query });
    chatInput.value = '';
    chatLoading.value = true;
    
    // Auto scroll to bottom
    setTimeout(() => {
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }, 100);
    
    try {
        const res = await api.post(`/knowledge/${currentDocId.value}/qa`, { query });
        chatMessages.value.push({ 
            role: 'assistant', 
            content: res.data.answer,
            sources: res.data.sources 
        });
    } catch (e) {
        console.error(e);
        chatMessages.value.push({ role: 'assistant', content: "Error: " + (e.response?.data?.detail || e.message) });
    } finally {
        chatLoading.value = false;
        setTimeout(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }, 100);
    }
};

const fetchFiles = async () => {

    try {
        const res = await api.get('/knowledge/list');
        files.value = res.data;
        
        // Check if we need to poll (if any file is in transient state)
        const hasPending = files.value.some(f => ['uploading', 'uploaded', 'indexing'].includes(f.status));
        if (hasPending) {
            startPolling();
        } else {
            stopPolling();
        }
    } catch (e) {
        console.error(e);
        stopPolling();
    } finally {
        loading.value = false;
    }
};

const startPolling = () => {
    if (pollTimer) return;
    pollTimer = setInterval(fetchFiles, 3000);
};

const stopPolling = () => {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
};

const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    uploading.value = true;
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        await api.post('/knowledge/upload', formData);
        message.success("上传成功，正在索引中...");
        fetchFiles();
    } catch (e) {
        message.error("上传失败：" + (e.response?.data?.detail || e.message));
    } finally {
        uploading.value = false;
        e.target.value = ''; 
    }
};

const deleteFile = (id) => {
    Modal.confirm({
        title: '确定要删除此文件吗？',
        icon: createVNode(ExclamationCircleOutlined),
        content: '删除后将无法恢复，请谨慎操作。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                await api.delete(`/knowledge/${id}`);
                message.success("删除成功");
                fetchFiles();
            } catch (e) {
                message.error("删除失败");
            }
        }
    });
};

const formatSize = (bytes) => {
    if (!bytes && bytes !== 0) return '0 B';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    // Format: YYYY-MM-DD HH:mm:ss
    const d = new Date(dateStr);
    return d.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-');
};

onMounted(fetchFiles);
onUnmounted(stopPolling);
</script>

<style scoped>
/* Custom Scrollbar for file list */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #e5e6eb;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #c9cdd4;
}

.animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.animate-shimmer {
    animation: shimmer 1.5s infinite;
}

:deep(.graph-modal .ant-modal-title) {
    font-size: 14px;
    color: #4b5563;
    cursor: help;
}
</style>