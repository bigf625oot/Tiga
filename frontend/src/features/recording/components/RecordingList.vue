<template>
    <div class="h-full flex flex-col bg-white font-sans">
        <!-- Header & Filters -->
        <div class="flex flex-col gap-6 px-8 pt-8 pb-4">
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <h1 class="text-2xl font-bold text-slate-900 tracking-tight">录音纪要</h1>
                    <span class="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs font-medium border border-slate-200">{{ files.length }} 个文件</span>
                </div>
                <div class="flex gap-3">
                     <div class="relative group">
                        <input 
                            type="text" 
                            placeholder="搜索录音标题或内容..." 
                            class="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm w-72 transition-all focus:w-80 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 shadow-sm placeholder:text-slate-400"
                        >
                        <svg class="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 group-focus-within:text-blue-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                     </div>
                </div>
            </div>
            
            <!-- Tags / Filters -->
            <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                <button class="px-5 py-2 rounded-full bg-slate-900 text-white text-sm font-medium shadow-md shadow-slate-900/10 transition-all hover:translate-y-px active:translate-y-0">全部</button>
                <button class="px-5 py-2 rounded-full bg-white border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300 transition-all shadow-sm">最近7天</button>
                <button class="px-5 py-2 rounded-full bg-white border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300 transition-all shadow-sm">我的项目</button>
                <button class="px-5 py-2 rounded-full bg-white border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300 transition-all shadow-sm flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/></svg>
                    星标
                </button>
            </div>
        </div>

        <!-- Content Area -->
        <div class="flex-1 overflow-y-auto px-8 pb-32">
            <!-- Loading State -->
            <div v-if="loading" class="flex flex-col items-center justify-center h-64 text-slate-400">
                <svg class="animate-spin h-8 w-8 mb-3 text-blue-600" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span class="text-sm font-medium">加载数据中...</span>
            </div>

            <!-- Empty State (Optimized) -->
            <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-slate-300 animate-[fadeIn_0.5s_ease-out]">
                <div class="relative w-64 h-64 mb-6">
                     <!-- Custom SVG Illustration -->
                    <svg viewBox="0 0 400 300" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full drop-shadow-xl">
                        <rect x="100" y="60" width="200" height="180" rx="16" fill="white" stroke="#E2E8F0" stroke-width="2"/>
                        <rect x="120" y="90" width="160" height="12" rx="6" fill="#F1F5F9"/>
                        <rect x="120" y="120" width="100" height="12" rx="6" fill="#F1F5F9"/>
                        <rect x="120" y="150" width="140" height="12" rx="6" fill="#F1F5F9"/>
                        <circle cx="280" cy="220" r="30" fill="#3B82F6" fill-opacity="0.1"/>
                        <path d="M280 210V230M270 220H290" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                        <!-- Floating Elements -->
                        <g class="animate-[bounce_3s_infinite]">
                             <circle cx="80" cy="100" r="12" fill="#F87171" fill-opacity="0.2"/>
                        </g>
                         <g class="animate-[bounce_4s_infinite]">
                             <circle cx="320" cy="80" r="8" fill="#3B82F6" fill-opacity="0.2"/>
                        </g>
                    </svg>
                </div>
                <h3 class="text-xl font-bold text-slate-800 mb-3">暂无录音记录</h3>
                <p class="text-slate-500 max-w-sm text-center leading-relaxed mb-8">
                    您可以点击下方按钮开始新的录音，或导入现有的音频文件生成智能纪要。
                </p>
                <div class="flex gap-4">
                    <button @click="openRecorder" class="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium shadow-lg shadow-blue-600/30 hover:bg-blue-700 hover:-translate-y-0.5 transition-all flex items-center gap-2">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
                        开始录音
                    </button>
                    <button @click="triggerUpload" class="px-6 py-2.5 bg-white text-slate-700 border border-slate-200 rounded-xl font-medium hover:bg-slate-50 hover:border-slate-300 transition-all flex items-center gap-2">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                        导入音频
                    </button>
                </div>
            </div>

            <!-- Card Grid -->
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                <!-- Folder Navigation -->
                <div v-if="currentFolderId" @click="goUp" class="group relative bg-white rounded-2xl p-6 border-2 border-dashed border-slate-200 hover:border-blue-500 hover:bg-blue-50/30 transition-all cursor-pointer flex flex-col items-center justify-center min-h-[200px]">
                    <div class="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-sm">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
                    </div>
                    <span class="font-bold text-slate-700 group-hover:text-blue-600 transition-colors">返回上一级</span>
                </div>

                <!-- File Cards -->
                <div v-for="file in files" :key="file.id" 
                    class="group relative bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_12px_24px_rgba(0,0,0,0.08)] hover:border-blue-500/20 hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col justify-between min-h-[200px]"
                    @click="handleItemClick(file)"
                >
                    <!-- Card Header -->
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex items-center gap-3.5 overflow-hidden">
                             <div :class="[
                                'w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border',
                                file.is_folder ? 'bg-amber-50 text-amber-500 border-amber-100' : 'bg-blue-50 text-blue-600 border-blue-100'
                            ]">
                                <svg v-if="file.is_folder" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                                <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                            </div>
                            <div class="flex flex-col overflow-hidden">
                                <h3 class="font-bold text-slate-800 truncate text-base mb-1 group-hover:text-blue-600 transition-colors" :title="file.filename">{{ file.filename }}</h3>
                                <span class="text-xs text-slate-500 font-medium">{{ formatDate(file.created_at) }}</span>
                            </div>
                        </div>
                        
                        <!-- More Actions (Hover) -->
                        <div class="opacity-0 group-hover:opacity-100 transition-all absolute top-4 right-4 flex gap-1 bg-white shadow-sm border border-slate-100 rounded-lg p-1" @click.stop>
                             <button class="w-8 h-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-slate-50 hover:text-blue-600 transition-all" title="重命名" @click="openRenameModal(file)">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            </button>
                            <a-popconfirm title="确定要删除吗?" ok-text="确认" cancel-text="取消" @confirm="deleteRecording(file.id)">
                                <button class="w-8 h-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-red-50 hover:text-red-500 transition-all" title="删除">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                </button>
                            </a-popconfirm>
                        </div>
                    </div>

                    <!-- Waveform Placeholder / Status -->
                    <div v-if="!file.is_folder" class="flex-1 flex items-center justify-center my-3 relative bg-slate-50 rounded-xl overflow-hidden group-hover:bg-blue-50/50 transition-colors border border-slate-100/50">
                        <!-- Static Waveform Visual -->
                        <div class="flex items-center gap-1 h-10 opacity-40 group-hover:opacity-60 transition-opacity">
                             <div v-for="i in 24" :key="i" 
                                class="w-1 bg-blue-500 rounded-full transition-all duration-300"
                                :style="{ height: (20 + Math.random() * 80) + '%', opacity: 0.3 + Math.random() * 0.7 }"
                             ></div>
                        </div>
                        
                        <!-- Play Overlay -->
                        <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-90 group-hover:scale-100 bg-white/10 backdrop-blur-[1px]">
                            <div class="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-lg shadow-blue-600/30 hover:scale-110 transition-transform">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                            </div>
                        </div>
                    </div>
                    <div v-else class="flex-1"></div>

                    <!-- Card Footer -->
                    <div class="flex justify-between items-center mt-2 pt-3 border-t border-slate-50">
                        <span v-if="!file.is_folder" class="text-xs font-bold font-din text-slate-500 bg-slate-100 px-2 py-1 rounded-md">{{ formatDuration(file.duration) }}</span>
                        <span v-else class="text-xs text-slate-400 font-medium">文件夹</span>

                        <!-- Status Badge -->
                         <div v-if="!file.is_folder" class="flex items-center gap-1.5">
                            <div v-if="file.summary_status === 'completed'" class="flex items-center gap-1.5 text-[11px] font-bold text-green-600 bg-green-50 px-2.5 py-1 rounded-full border border-green-100">
                                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                已完成
                            </div>
                             <div v-else-if="file.summary_status === 'processing'" class="flex items-center gap-1.5 text-[11px] font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
                                <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                                处理中
                            </div>
                            <div v-else-if="file.summary_status === 'failed'" class="flex items-center gap-1.5 text-[11px] font-bold text-red-600 bg-red-50 px-2.5 py-1 rounded-full border border-red-100">
                                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                                失败
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Global Floating Action Button (FAB) - Fixed Color Classes -->
        <div class="absolute bottom-10 right-10 z-50">
            <a-dropdown :trigger="['click']" placement="topRight">
                <button class="w-16 h-16 rounded-full bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/40 hover:scale-105 active:scale-95 transition-all flex items-center justify-center group ring-4 ring-white/30 backdrop-blur-sm">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="group-hover:rotate-90 transition-transform duration-300"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                </button>
                <template #overlay>
                    <a-menu class="!rounded-2xl !p-2 !min-w-[180px] !shadow-xl !border !border-slate-100">
                        <a-menu-item key="record" @click="openRecorder" class="!rounded-xl !mb-1 !py-3">
                            <div class="flex items-center gap-3">
                                <div class="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg></div>
                                <span class="font-bold text-slate-700">发起录音</span>
                            </div>
                        </a-menu-item>
                        <a-menu-item key="upload" @click="triggerUpload" class="!rounded-xl !mb-1 !py-3">
                            <div class="flex items-center gap-3">
                                <div class="w-9 h-9 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg></div>
                                <span class="font-bold text-slate-700">导入音频</span>
                            </div>
                        </a-menu-item>
                        <a-menu-item key="folder" @click="createFolder" class="!rounded-xl !py-3">
                            <div class="flex items-center gap-3">
                                <div class="w-9 h-9 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg></div>
                                <span class="font-bold text-slate-700">新建文件夹</span>
                            </div>
                        </a-menu-item>
                    </a-menu>
                </template>
            </a-dropdown>
        </div>

        <!-- Hidden Input -->
        <input type="file" ref="fileInput" class="hidden" accept="audio/*" @change="handleFileUpload">

        <!-- Modals (Keep existing) -->
        <a-modal v-model:open="createFolderModalVisible" title="新建文件夹" @ok="handleCreateFolderConfirm" centered :bodyStyle="{padding: '24px'}">
            <a-input v-model:value="newFolderName" placeholder="请输入文件夹名称" :status="folderNameError ? 'error' : ''" @pressEnter="handleCreateFolderConfirm" auto-focus class="!rounded-lg !py-2" />
            <div v-if="folderNameError" class="text-red-500 text-xs mt-1">{{ folderNameError }}</div>
        </a-modal>

        <a-modal v-model:open="renameModalVisible" title="重命名" @ok="handleRename" centered :bodyStyle="{padding: '24px'}">
            <a-input v-model:value="renameValue" placeholder="请输入新名称" @pressEnter="handleRename" auto-focus class="!rounded-lg !py-2" />
        </a-modal>

        <!-- Recorder Component -->
        <Recorder v-if="showRecorder" @close="showRecorder = false" @finish="handleFinish" />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';
import Recorder from './Recorder.vue';

// Define emits
const emit = defineEmits(['view-detail']);

// Setup Axios
const api = axios.create({
    baseURL: '/api/v1'
});

const showRecorder = ref(false);
const files = ref<any[]>([]);
const loading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

// Folder Logic
const currentFolderId = ref<string | null>(null);
const currentFolderName = ref('');
const createFolderModalVisible = ref(false);
const renameModalVisible = ref(false);
const newFolderName = ref('');
const folderNameError = ref('');
const itemToRename = ref<any>(null);
const renameValue = ref('');

const fetchRecordings = async () => {
    loading.value = true;
    try {
        const params: any = {};
        if (currentFolderId.value) params.parent_id = currentFolderId.value;
        const res = await api.get('/recordings/', { params });
        files.value = res.data;
    } catch (e) {
        message.error("获取列表失败");
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const handleItemClick = (file: any) => {
    if (file.is_folder) {
        currentFolderId.value = file.id;
        currentFolderName.value = file.filename;
        fetchRecordings();
    } else {
        viewDetail(file);
    }
};

const goUp = () => {
    currentFolderId.value = null; 
    currentFolderName.value = '';
    fetchRecordings();
};

const createFolder = () => {
    newFolderName.value = '';
    folderNameError.value = '';
    createFolderModalVisible.value = true;
};

const handleCreateFolderConfirm = async () => {
    const name = newFolderName.value.trim();
    if (!name) {
        folderNameError.value = "文件夹名称不能为空";
        return;
    }
    const isDuplicate = files.value.some(f => f.filename === name && f.is_folder);
    if (isDuplicate) {
        folderNameError.value = "该文件夹已存在";
        return;
    }
    try {
        await api.post('/recordings/folder', null, { params: { name, parent_id: currentFolderId.value } });
        message.success("文件夹创建成功");
        createFolderModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        message.error("创建失败");
    }
};

const openRenameModal = (file: any) => {
    itemToRename.value = file;
    renameValue.value = file.filename;
    renameModalVisible.value = true;
};

const handleRename = async () => {
    if (!itemToRename.value || !renameValue.value.trim()) return;
    try {
        await api.put(`/recordings/${itemToRename.value.id}/rename`, null, { 
            params: { name: renameValue.value.trim() } 
        });
        message.success("重命名成功");
        renameModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        message.error("重命名失败");
    }
};

const deleteRecording = async (id: string) => {
    try {
        await api.delete(`/recordings/${id}`);
        message.success("删除成功");
        fetchRecordings();
    } catch (e) {
        message.error("删除失败");
    }
};

const openRecorder = () => {
  showRecorder.value = true;
};

const handleFinish = async (recordData: any) => {
    await uploadFileToBackend(recordData.blob, recordData.fileName, recordData.duration);
};

const triggerUpload = () => {
    fileInput.value?.click();
};

const handleFileUpload = async (e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
        const duration = await getAudioDuration(file);
        await uploadFileToBackend(file, file.name, duration);
    }
};

const getAudioDuration = (file: File) => {
    return new Promise<number>((resolve) => {
        const url = URL.createObjectURL(file);
        const audio = new Audio(url);
        audio.addEventListener('loadedmetadata', () => {
            const durationMs = Math.floor(audio.duration * 1000);
            URL.revokeObjectURL(url);
            resolve(durationMs);
        });
        audio.addEventListener('error', () => {
             URL.revokeObjectURL(url);
             resolve(0);
        });
    });
};

const uploadFileToBackend = async (fileBlob: Blob, fileName: string, duration: number) => {
    const formData = new FormData();
    formData.append('file', fileBlob, fileName); 
    formData.append('duration', duration.toString());
    if (currentFolderId.value) {
        formData.append('parent_id', currentFolderId.value);
    }

    try {
        message.loading({ content: '上传处理中...', key: 'upload' });
        await api.post('/recordings/upload', formData);
        message.success({ content: '上传成功', key: 'upload' });
        fetchRecordings();
    } catch (e) {
        message.error({ content: '上传失败', key: 'upload' });
        console.error(e);
    }
};

const viewDetail = (file: any) => {
    emit('view-detail', file);
};

const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD'); // Shortened for card
};

const formatDuration = (ms: number) => {
    const durationSec = Math.floor(ms / 1000);
    const min = Math.floor(durationSec / 60);
    const sec = durationSec % 60;
    return (min > 0 ? min + ":" : "0:") + (sec < 10 ? "0" + sec : sec);
};

onMounted(() => {
    fetchRecordings();
});
</script>

<style scoped>
/* Hide scrollbar for horizontal tag list */
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>