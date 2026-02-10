<template>
    <div class="h-full flex flex-col">
        <div class="grid grid-cols-2 gap-6 mb-12 max-w-[840px]">
            <!-- Start Recording Card -->
            <div @click="openRecorder" class="relative group overflow-hidden bg-white rounded-[24px] p-8 border border-slate-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] hover:shadow-[0_20px_40px_rgba(59,130,246,0.1)] hover:border-blue-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col items-center justify-center gap-4 h-[200px]">
                <div class="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-110 group-hover:shadow-blue-500/40 transition-all duration-300 ring-4 ring-blue-50/50">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                </div>
                <div class="relative flex flex-col items-center gap-1.5">
                    <span class="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors tracking-tight">发起录音速记</span>
                </div>
            </div>

            <!-- Upload Audio Card -->
            <div @click="triggerUpload" class="relative group overflow-hidden bg-white rounded-[24px] p-8 border border-slate-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] hover:shadow-[0_20px_40px_rgba(59,130,246,0.1)] hover:border-blue-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col items-center justify-center gap-4 h-[200px]">
                <div class="relative w-16 h-16 rounded-2xl bg-white border border-slate-100 flex items-center justify-center shadow-sm group-hover:border-blue-200 group-hover:scale-110 transition-all duration-300">
                     <svg class="relative z-10 text-blue-500" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                </div>
                <div class="relative flex flex-col items-center gap-1.5">
                    <span class="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors tracking-tight">上传本地音频</span>
                </div>
                <input type="file" ref="fileInput" class="hidden" accept="audio/*" @change="handleFileUpload">
            </div>
        </div>

        <!-- File List -->
        <div class="w-full">
            <div class="flex justify-between items-center mb-3 px-2">
                <div class="flex items-center gap-3">
                    <button v-if="currentFolderId" @click="goUp" class="text-slate-500 hover:text-blue-600 flex items-center justify-center w-8 h-8 rounded-lg hover:bg-slate-100 transition-colors">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    </button>
                    <div class="h-4 w-px bg-slate-200" v-if="currentFolderId"></div>
                    <h2 class="text-base font-bold text-slate-800 leading-none mb-0">{{ currentFolderId ? currentFolderName : '全部文件' }}</h2>
                </div>
                <button @click="createFolder" class="text-sm bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 font-medium">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>
                    新建文件夹
                </button>
            </div>

            <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div class="grid grid-cols-12 gap-4 px-6 py-3.5 bg-slate-50 border-b border-slate-200 text-sm font-bold text-slate-500 uppercase tracking-wider">
                    <div class="col-span-4 pl-2">文件名称</div>
                    <div class="col-span-1 text-center">时长</div>
                    <div class="col-span-3 text-center">处理流水线 (上传-转写-摘要)</div>
                    <div class="col-span-2 text-center">创建时间</div>
                    <div class="col-span-2 text-center">操作</div>
                </div>
                
                <div v-if="loading" class="text-center py-12 text-slate-400">
                    <svg class="animate-spin h-8 w-8 mx-auto mb-3 text-blue-500 opacity-50" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span class="text-sm font-medium">加载数据中...</span>
                </div>
                <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center py-20 text-slate-300 bg-white">
                    <div class="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 border border-slate-100">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-50"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
                    </div>
                    <span class="text-sm font-medium text-slate-400">暂无文件</span>
                </div>
                
                <div v-else class="divide-y divide-slate-50">
                    <div v-for="file in files" :key="file.id" class="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-slate-50 transition-all items-center group bg-white">
                        <!-- Name -->
                        <div class="col-span-4 flex items-center gap-3 overflow-hidden">
                            <div v-if="file.is_folder" class="w-9 h-9 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center flex-shrink-0 border border-amber-100 shadow-sm">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                            </div>
                            <div v-else class="w-9 h-9 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center flex-shrink-0 border border-blue-100 shadow-sm">
                                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                            </div>
                            <span class="text-sm font-medium text-slate-700 truncate cursor-pointer hover:text-blue-600 transition-colors" @click="handleItemClick(file)">{{ file.filename }}</span>
                        </div>
                        
                        <!-- Duration -->
                        <div class="col-span-1 text-center text-sm text-slate-500 font-din font-medium">{{ file.is_folder ? '-' : formatDuration(file.duration) }}</div>
                        
                        <!-- Pipeline Status -->
                        <div class="col-span-3 flex items-center justify-center gap-2">
                            <span v-if="file.is_folder" class="text-slate-300">-</span>
                            <template v-else>
                                <!-- Upload -->
                                <div class="relative group/tooltip">
                                    <div class="w-5 h-5 rounded-full flex items-center justify-center border transition-all" :class="[getStatusStyle(file.upload_status).bg, getStatusStyle(file.upload_status).text, getStatusStyle(file.upload_status).border]">
                                        <svg v-if="file.upload_status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        <svg v-else-if="file.upload_status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
                                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                                    </div>
                                    <!-- Tooltip -->
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">上传</div>
                                </div>
                                <!-- Arrow -->
                                <svg class="w-2.5 h-2.5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                                
                                <!-- ASR -->
                                <div class="relative group/tooltip">
                                    <div class="w-5 h-5 rounded-full flex items-center justify-center border transition-all" :class="[getStatusStyle(file.asr_status).bg, getStatusStyle(file.asr_status).text, getStatusStyle(file.asr_status).border]">
                                        <svg v-if="file.asr_status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        <svg v-else-if="file.asr_status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
                                    </div>
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">转写</div>
                                </div>
                                <!-- Arrow -->
                                <svg class="w-2.5 h-2.5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                                
                                <!-- Summary -->
                                <div class="relative group/tooltip">
                                    <div class="w-5 h-5 rounded-full flex items-center justify-center border transition-all" :class="[getStatusStyle(file.summary_status).bg, getStatusStyle(file.summary_status).text, getStatusStyle(file.summary_status).border]">
                                        <svg v-if="file.summary_status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        <svg v-else-if="file.summary_status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                                    </div>
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">摘要</div>
                                </div>
                            </template>
                        </div>
                        
                        <!-- Time -->
                        <div class="col-span-2 text-center text-sm text-slate-400 font-din">{{ formatDate(file.created_at) }}</div>
                        
                        <!-- Actions -->
                        <div class="col-span-2 flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button v-if="!file.is_folder" class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-blue-50 hover:text-blue-600 transition-all" title="查看详情" @click="viewDetail(file)">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            </button>
                            <button class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-blue-50 hover:text-blue-600 transition-all" title="重命名" @click="openRenameModal(file)">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            </button>
                            <a-popconfirm
                                title="确定要删除吗?"
                                ok-text="确认"
                                cancel-text="取消"
                                @confirm="deleteRecording(file.id)"
                            >
                                <button class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-red-50 hover:text-red-500 transition-all" title="删除">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                </button>
                            </a-popconfirm>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Folder Modal -->
        <a-modal v-model:open="createFolderModalVisible" title="新建文件夹" @ok="handleCreateFolderConfirm">
            <div class="py-4">
                <a-input 
                    v-model:value="newFolderName" 
                    placeholder="请输入文件夹名称" 
                    :status="folderNameError ? 'error' : ''"
                    @pressEnter="handleCreateFolderConfirm"
                    auto-focus
                />
                <div v-if="folderNameError" class="text-red-500 text-xs mt-1">{{ folderNameError }}</div>
            </div>
        </a-modal>

        <!-- Move Modal -->
        <a-modal v-model:open="moveModalVisible" title="移动到文件夹" @ok="handleMove">
            <div class="py-4">
                <p class="mb-2 text-gray-500">选择目标文件夹：</p>
                <a-select v-model:value="selectedTargetFolder" style="width: 100%">
                    <a-select-option :value="null">根目录 (Root)</a-select-option>
                    <a-select-option v-for="folder in availableFolders" :key="folder.id" :value="folder.id">{{ folder.filename }}</a-select-option>
                </a-select>
            </div>
        </a-modal>

        <!-- Rename Modal -->
        <a-modal v-model:open="renameModalVisible" title="重命名" @ok="handleRename">
            <div class="py-4">
                <a-input 
                    v-model:value="renameValue" 
                    placeholder="请输入新名称" 
                    @pressEnter="handleRename"
                    auto-focus
                />
            </div>
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
const moveModalVisible = ref(false);
const createFolderModalVisible = ref(false);
const renameModalVisible = ref(false);
const newFolderName = ref('');
const folderNameError = ref('');
const itemToMove = ref<any>(null);
const itemToRename = ref<any>(null);
const renameValue = ref('');
const selectedTargetFolder = ref<string | null>(null);
const availableFolders = ref<any[]>([]);

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

const openMoveModal = async (file: any) => {
    itemToMove.value = file;
    selectedTargetFolder.value = null;
    moveModalVisible.value = true;
    try {
        const res = await api.get('/recordings/', { params: { limit: 1000 } });
        availableFolders.value = res.data.filter((f: any) => f.is_folder && f.id !== file.id);
    } catch(e) {}
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

const handleMove = async () => {
    if (!itemToMove.value) return;
    try {
        await api.put(`/recordings/${itemToMove.value.id}/move`, null, { 
            params: { target_parent_id: selectedTargetFolder.value } 
        });
        message.success("移动成功");
        moveModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        message.error("移动失败");
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

const deleteRecording = async (id: string) => {
    try {
        await api.delete(`/recordings/${id}`);
        message.success("删除成功");
        fetchRecordings();
    } catch (e) {
        message.error("删除失败");
    }
};

const viewDetail = (file: any) => {
    emit('view-detail', file);
};

const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

const formatDuration = (ms: number) => {
    const durationSec = Math.floor(ms / 1000);
    const min = Math.floor(durationSec / 60);
    const sec = durationSec % 60;
    return (min > 0 ? min + "分" : "") + sec + "秒";
};

const statusConfig: any = {
    completed: { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200', icon: 'check' },
    processing: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200', icon: 'loader' },
    failed: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200', icon: 'x' },
    pending: { bg: 'bg-slate-50', text: 'text-slate-300', border: 'border-slate-200', icon: 'minus' }
};

const getStatusStyle = (status: string) => {
    return statusConfig[status] || statusConfig.pending;
};

onMounted(() => {
    fetchRecordings();
});
</script>
