
<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header -->
    <div class="px-10 pt-12 pb-6">
      <div class="flex flex-col gap-6">
        <div>
          <h2 class="text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">知识库</h2>
          <p class="text-[#86868B] text-lg font-medium">企业级知识沉淀与管理。</p>
        </div>

        <div class="flex items-center gap-8 pb-0">
                <div 
                    class="cursor-pointer pb-2 text-base font-medium transition-colors relative"
                    :class="activeTab === 'shared' ? 'text-[#0056e8]' : 'text-[#858b9b]'"
                    @click="activeTab = 'shared'"
                >
                    共享
                    <div v-if="activeTab === 'shared'" class="absolute bottom-0 left-0 w-full h-0.5 bg-[#0056e8]"></div>
                </div>
                <div 
                    class="cursor-pointer pb-2 text-base font-medium transition-colors relative"
                    :class="activeTab === 'personal' ? 'text-[#0056e8]' : 'text-[#858b9b]'"
                    @click="activeTab = 'personal'"
                >
                    个人
                    <div v-if="activeTab === 'personal'" class="absolute bottom-0 left-0 w-full h-0.5 bg-[#0056e8]"></div>
                </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-hidden px-10 pb-10 bg-white">
      <div class="h-full flex flex-col">

        <!-- Toolbar -->
        <div class="flex justify-between items-center mb-4">
            <!-- Left: Search and File Count/Title -->
            <div class="flex items-center gap-4 flex-1">
                 <span class="text-base font-medium text-[#2a2f3c] cursor-pointer hover:text-blue-600 transition-colors" @click="viewGlobalGraph" title="查看全局知识图谱">全部文件</span>
                 <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white w-[330px]">
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
                <button 
                    @click="openNewFolder"
                    class="flex items-center gap-1 px-4 py-1.5 border border-[#c9cdd4] text-[#2a2f3c] rounded-xl text-sm hover:bg-slate-50 transition-colors"
                >
                    新建文件夹
                </button>
                <button 
                    @click="confirmCleanVector"
                    class="flex items-center gap-1 px-4 py-1.5 border border-red-300 text-red-600 rounded-xl text-sm hover:bg-red-50 transition-colors"
                    :disabled="cleaningVector"
                    title="清空向量库（不影响图谱与文件）"
                >
                    <span v-if="cleaningVector">清理中...</span>
                    <span v-else>清空向量库</span>
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
                <div class="flex items-center bg-[#f9f9fa] h-[38px] rounded px-3 text-[14px] font-medium text-[#2a2f3c]">
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
                    <div v-if="files.length === 0 && !uploading" class="py-12 flex flex-col items-center justify-center text-slate-400 text-[14px]">
                        暂无文件
                    </div>
                    
                    <div 
                        v-for="file in files" 
                        :key="file.id" 
                        class="flex items-center border-b border-slate-50 hover:bg-[#eeeeee] transition-colors py-2 px-3 text-[14px] text-[#2a2f3c]"
                    >
                        <!-- Name -->
                        <div class="flex-1 flex items-center gap-2 overflow-hidden">
                             <!-- File Icon -->
                             <div class="w-6 h-6 flex items-center justify-center flex-shrink-0">
                                 <img :src="getFileIcon(file.filename)" class="w-full h-full object-contain" alt="icon" />
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
                            <div v-if="['上传中', '解析中'].includes(file.status_text)" class="w-full pr-4">
                                <div class="flex justify-between items-center mb-1.5">
                                    <span class="text-xs text-blue-600 font-medium">
                                        {{ file.status_text }}
                                    </span>
                                    <span class="text-[10px] text-slate-400">
                                        <template v-if="file.progress !== null && file.progress !== undefined">
                                            {{ file.progress }}%
                                        </template>
                                        <template v-else>进行中</template>
                                    </span>
                                </div>
                                <div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                     <div 
                                        class="h-full bg-blue-500 rounded-full relative overflow-hidden"
                                        :style="{ width: (file.progress !== null && file.progress !== undefined) ? (file.progress + '%') : '100%' }"
                                     >
                                         <div class="absolute inset-0 bg-white/30 w-full h-full animate-shimmer"></div>
                                     </div>
                                </div>
                            </div>
                            
                            <!-- Standard Badge for other states -->
                            <div v-else class="flex items-center gap-2 px-2 py-1 bg-slate-100 rounded border border-slate-200 w-fit">
                                <span class="w-2 h-2 rounded-full" 
                                    :class="{
                                        'bg-green-500': file.status_text === '已完成',
                                        'bg-red-500': file.status_text === '失败'
                                    }"
                                ></span>
                                <span class="text-xs">
                                    {{ file.status_text || '未知' }}
                                </span>
                            </div>
                        </div>
                        
                        <!-- Actions -->
                        <div class="w-[100px] px-3 flex items-center gap-3">
                            <button 
                                v-if="file.status_text === '已完成'"
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
                <div class="flex items-center gap-2">
                  <span :title="currentGraphTitle" class="cursor-help text-[#171717]">
                      {{ currentGraphTitle.length > 20 ? currentGraphTitle.slice(0, 20) + '...' : currentGraphTitle }}
                  </span>
                </div>
            </template>
            <div class="h-[80vh]">
                <KnowledgeGraphView :doc-id="currentDocId" :initial-scope="currentDocId ? 'doc' : 'global'" />
            </div>
        </a-modal>

        <!-- New Folder Modal -->
        <a-modal
            v-model:open="newFolderVisible"
            title="新建文件夹"
            :confirmLoading="creatingFolder"
            @ok="createFolder"
            @cancel="resetNewFolder"
            destroyOnClose
        >
            <div class="flex flex-col gap-2">
                <label class="text-sm text-slate-600">文件夹名称</label>
                <input 
                    v-model="newFolderName"
                    type="text" 
                    placeholder="请输入文件夹名称" 
                    class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all placeholder:text-slate-400"
                />
            </div>
        </a-modal>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, createVNode, watch, computed } from 'vue';
import axios from 'axios';
import { message, Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { marked } from 'marked';
import { Loading } from '@/shared/components/atoms/Loading';
import KnowledgeGraphView from './KnowledgeGraphView.vue';

const files = ref([]);
const uploading = ref(false);
const loading = ref(true);
const activeTab = ref('personal'); // shared | personal
const api = axios.create({ baseURL: '/api/v1' }); // Use relative path
api.interceptors.request.use((config) => {
  const id = Math.random().toString(36).slice(2, 10);
  config.headers['X-Trace-Id'] = id;
  const started = Date.now();
  config.__trace = { id, started };
  if ((config.url || '').includes('/knowledge')) {
    console.info('[KB][REQ]', id, config.method?.toUpperCase(), config.url, { params: config.params, data: config.data });
    console.time(`[KB][${id}]`);
  }
  return config;
});
api.interceptors.response.use((res) => {
  const trace = res.config.__trace;
  if ((res.config.url || '').includes('/knowledge')) {
    const ms = Date.now() - (trace?.started || Date.now());
    console.timeEnd(`[KB][${trace?.id}]`);
    console.info('[KB][RES]', trace?.id, res.status, res.config.url, `${ms}ms`, { keys: res.data ? Object.keys(res.data) : [] });
  }
  return res;
}, (err) => {
  const cfg = err.config || {};
  const trace = cfg.__trace;
  if ((cfg.url || '').includes('/knowledge')) {
    console.timeEnd(`[KB][${trace?.id}]`);
    console.error('[KB][ERR]', trace?.id, cfg.method?.toUpperCase(), cfg.url, err.response?.status, err.message, err.response?.data);
  }
  return Promise.reject(err);
});
let pollTimer = null;
const cleaningVector = ref(false);

// Graph State
const graphVisible = ref(false);
const currentGraphTitle = ref('');
const currentDocId = ref(null);

const viewGraph = (file) => {
    currentGraphTitle.value = file.filename;
    currentDocId.value = file.id;
    graphVisible.value = true;
};

const viewGlobalGraph = () => {
    currentGraphTitle.value = "全局知识图谱";
    currentDocId.value = null; // null means global scope
    graphVisible.value = true;
};

const fetchFiles = async () => {

    try {
        const res = await api.get('/knowledge/list');
        files.value = res.data;
        
        // Check if we need to poll (if any file is in transient state)
        const hasPending = files.value.some(f => ['上传中', '已上传', '解析中'].includes(f.status_text));
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

// New Folder
const newFolderVisible = ref(false);
const newFolderName = ref('');
const creatingFolder = ref(false);

const resetNewFolder = () => {
    newFolderName.value = '';
    creatingFolder.value = false;
};

const openNewFolder = () => {
    newFolderVisible.value = true;
    message.info('请输入文件夹名称');
};

const confirmCleanVector = () => {
    Modal.confirm({
        title: '确定要清空向量库吗？',
        icon: createVNode(ExclamationCircleOutlined),
        content: '此操作将删除向量库持久化数据并按当前模型重建，不影响图谱与已上传文件。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            cleaningVector.value = true;
            try {
                await api.post('/knowledge/vector/clean');
                message.success('向量库已清空并重建');
                fetchFiles();
            } catch (e) {
                message.error('清理失败：' + (e.response?.data?.detail || e.message));
            } finally {
                cleaningVector.value = false;
            }
        }
    });
};
const createFolder = async () => {
    const name = newFolderName.value.trim();
    if (!name) {
        message.warning('请输入文件夹名称');
        return;
    }
    creatingFolder.value = true;
    const payloads = [
        { url: '/knowledge/folders', body: { name } },
        { url: '/knowledge/folder', body: { name } },
        { url: '/knowledge/create_folder', body: { name } },
        { url: '/knowledge', body: { name, is_folder: true } }
    ];
    let created = false;
    for (const { url, body } of payloads) {
        try {
            const res = await api.post(url, body);
            if (res.status >= 200 && res.status < 300) {
                created = true;
                break;
            }
        } catch (err) {
            const status = err.response?.status;
            if (status === 405 || status === 404) {
                continue;
            } else {
                message.error('创建失败：' + (err.response?.data?.detail || err.message));
                creatingFolder.value = false;
                return;
            }
        }
    }
    if (created) {
        message.success('文件夹已创建');
        newFolderVisible.value = false;
        resetNewFolder();
        fetchFiles();
    } else {
        message.error('创建失败：接口不可用');
        creatingFolder.value = false;
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

const getFileIcon = (filename) => {
    if (!filename) return '/default.svg';
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'pdf') return '/PDF.svg';
    if (ext === 'doc' || ext === 'docx') return '/docx .svg'; // Note: filename in public is 'docx .svg'
    if (ext === 'txt') return '/txt.svg';
    // Add more mappings if needed
    return '/default.svg';
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
</style>
