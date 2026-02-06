<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header Banner -->
    <div class="px-10 pt-12 pb-6">
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">音视频库</h2>
          <p class="text-[#86868B] text-lg font-medium">管理和分析您的媒体资源。</p>
        </div>
        <div class="flex gap-3">
          <button 
            @click="triggerUpload" 
            class="bg-[#0071e3] text-white px-5 py-2.5 rounded-full hover:bg-[#0077ED] transition-all shadow-sm hover:shadow-md font-medium flex items-center gap-2 active:scale-95 text-sm"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
            上传
          </button>
          <input type="file" ref="fileInput" class="hidden" accept="audio/*,video/*" @change="handleFileUpload">
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto px-10 pb-10 custom-scrollbar">
      
      <div v-if="loading" class="text-center py-32 text-[#86868B]">
        <svg class="animate-spin h-8 w-8 mx-auto mb-4 text-[#0071e3] opacity-80" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <span class="text-sm font-medium">加载中...</span>
      </div>

      <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center py-40 text-[#86868B]">
        <div class="w-20 h-20 bg-slate-50 rounded-[24px] flex items-center justify-center mb-6 border border-slate-100">
            <svg class="w-10 h-10 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
        </div>
        <span class="text-lg font-semibold text-[#1D1D1F]">暂无内容</span>
        <p class="text-sm mt-2 opacity-80">您的音视频库是空的</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-8">
        <!-- Card -->
        <div v-for="file in files" :key="file.id" class="bg-white rounded-[24px] shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-500 flex flex-col group overflow-hidden relative border border-slate-200">
            <!-- Icon/Thumbnail Area -->
            <div class="aspect-video bg-[#F5F5F7] flex items-center justify-center relative overflow-hidden group-hover:bg-[#E8E8ED] transition-colors duration-500">
                 <!-- Play Button Overlay -->
                 <div class="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center backdrop-blur-[2px] cursor-pointer z-10" @click="playMedia(file)">
                    <div class="w-12 h-12 bg-white/90 backdrop-blur-md rounded-full flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 transition-transform duration-300 text-[#1D1D1F]">
                        <svg class="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </div>
                 </div>

                 <div v-if="file.is_folder" class="w-20 h-20 text-[#FFD60A]">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                 </div>
                 <div v-else class="w-20 h-20 transition-transform duration-500 group-hover:scale-105">
                    <img v-if="file.filename.toLowerCase().endsWith('.mp3')" src="/MP3.svg" class="w-full h-full" alt="MP3" />
                    <img v-else src="/MP4.svg" class="w-full h-full" alt="MP4" />
                 </div>
                 
                 <!-- Status Badge -->
                 <div class="absolute top-3 right-3 z-20">
                    <span v-if="file.asr_status === 'completed'" class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/80 backdrop-blur-md text-[#34C759] shadow-sm border border-black/5">
                        已转写
                    </span>
                    <span v-else-if="file.asr_status === 'processing'" class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/80 backdrop-blur-md text-[#0071e3] shadow-sm border border-black/5">
                        <svg class="animate-spin -ml-0.5 mr-1 h-2.5 w-2.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        转写中
                    </span>
                 </div>
            </div>

            <!-- Content Area -->
            <div class="p-5 flex-1 flex flex-col">
                <div class="mb-2">
                    <h4 class="font-semibold text-[#1D1D1F] text-[15px] line-clamp-1 leading-snug mb-1" :title="file.filename">{{ file.filename }}</h4>
                    <div class="flex items-center gap-2 text-sm text-[#86868B] font-medium">
                        <span class="font-din tracking-wide">{{ formatDuration(file.duration) }}</span>
                        <span>•</span>
                        <span class="font-din tracking-wide">{{ formatDate(file.created_at) }}</span>
                    </div>
                </div>

                <!-- Actions (Visible on Hover) -->
                <div class="mt-auto pt-4 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-y-2 group-hover:translate-y-0">
                    <div class="flex gap-1">
                        <button @click="openRenameModal(file)" class="p-1.5 text-[#86868B] hover:text-[#0071e3] hover:bg-blue-50 rounded-lg transition-colors" title="重命名">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        </button>
                        <a-popconfirm
                            title="确定要删除吗?"
                            ok-text="确认"
                            cancel-text="取消"
                            @confirm="deleteFile(file.id)"
                        >
                            <button class="p-1.5 text-[#86868B] hover:text-[#FF3B30] hover:bg-red-50 rounded-lg transition-colors" title="删除">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                            </button>
                        </a-popconfirm>
                    </div>

                    <button 
                        @click="parseToGraph(file)" 
                        class="text-sm font-semibold text-[#0071e3] hover:text-[#0077ED] hover:bg-blue-50 px-2.5 py-1.5 rounded-full transition-colors flex items-center gap-1"
                        v-if="file.asr_status === 'completed'"
                    >
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        解析图谱
                    </button>
                </div>
            </div>
        </div>
      </div>
    </div>

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

    <!-- Player Modal -->
    <a-modal
        v-model:open="playerVisible"
        :title="currentPlayingFile?.filename"
        :footer="null"
        width="800px"
        destroyOnClose
        @cancel="closePlayer"
        :bodyStyle="{ padding: '0' }"
    >
        <div class="bg-black flex items-center justify-center rounded-b-lg overflow-hidden" style="min-height: 400px;">
            <video 
                v-if="currentPlayingFile && isVideo(currentPlayingFile.filename)"
                :src="playUrl" 
                controls 
                autoplay
                class="w-full h-full max-h-[600px]"
            ></video>
            <div v-else-if="currentPlayingFile" class="w-full p-10 flex flex-col items-center justify-center">
                <div class="w-32 h-32 rounded-full bg-slate-800 flex items-center justify-center mb-8 animate-pulse-slow">
                    <svg class="w-16 h-16 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
                </div>
                <audio 
                    :src="playUrl" 
                    controls 
                    autoplay
                    class="w-full max-w-md"
                ></audio>
            </div>
            <div v-else class="text-white">加载中...</div>
        </div>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';

// Reuse the axios instance logic or create new
const api = axios.create({
    baseURL: '/api/v1'
});

const files = ref([]);
const loading = ref(false);
const fileInput = ref(null);
const renameModalVisible = ref(false);
const renameValue = ref('');
const itemToRename = ref(null);

// Player State
const playerVisible = ref(false);
const playUrl = ref('');
const currentPlayingFile = ref(null);

const fetchFiles = async () => {
    loading.value = true;
    try {
        const res = await api.get('/recordings/');
        // Filter out folders if we only want media files, or keep them. 
        // For Media Library, usually we just show files. But let's keep it consistent.
        // The user asked for "Audio/Video Library", maybe folders are less relevant here 
        // unless we implement folder navigation. For now, let's show all.
        files.value = res.data;
    } catch (e) {
        message.error("获取列表失败");
    } finally {
        loading.value = false;
    }
};

const triggerUpload = () => {
    fileInput.value.click();
};

const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Get duration (approximate for now or use helper)
    const duration = await getMediaDuration(file);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('duration', duration);
    
    try {
        message.loading({ content: '上传中...', key: 'upload' });
        await api.post('/recordings/upload', formData);
        message.success({ content: '上传成功，正在后台转写', key: 'upload' });
        fetchFiles();
    } catch (e) {
        message.error({ content: '上传失败', key: 'upload' });
    } finally {
        e.target.value = ''; // Reset input
    }
};

const getMediaDuration = (file) => {
    return new Promise((resolve) => {
        const url = URL.createObjectURL(file);
        const element = file.type.startsWith('video') ? document.createElement('video') : document.createElement('audio');
        element.src = url;
        element.addEventListener('loadedmetadata', () => {
            const durationMs = Math.floor(element.duration * 1000);
            URL.revokeObjectURL(url);
            resolve(durationMs);
        });
        element.addEventListener('error', () => {
             URL.revokeObjectURL(url);
             resolve(0);
        });
    });
};

const deleteFile = async (id) => {
    try {
        await api.delete(`/recordings/${id}`);
        message.success("删除成功");
        fetchFiles();
    } catch (e) {
        message.error("删除失败");
    }
};

const openRenameModal = (file) => {
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
        fetchFiles();
    } catch (e) {
        message.error("重命名失败");
    }
};

const playMedia = async (file) => {
    if (file.is_folder) return;
    
    currentPlayingFile.value = file;
    playerVisible.value = true;
    playUrl.value = ''; // Reset
    
    try {
        const res = await api.get(`/recordings/${file.id}`);
        if (res.data.play_url) {
            playUrl.value = res.data.play_url;
        } else {
            message.error("无法获取播放地址");
            playerVisible.value = false;
        }
    } catch (e) {
        message.error("获取播放信息失败");
        playerVisible.value = false;
    }
};

const closePlayer = () => {
    playerVisible.value = false;
    playUrl.value = '';
    currentPlayingFile.value = null;
};

const isVideo = (filename) => {
    return /\.(mp4|mov|avi|webm|mkv)$/i.test(filename);
};

const parseToGraph = async (file) => {
    if (!file.transcription_text) {
        // Fetch details to get transcription if missing in list
        try {
            const res = await api.get(`/recordings/${file.id}`);
            file.transcription_text = res.data.transcription_text;
        } catch(e) {
            message.error("获取转写内容失败");
            return;
        }
    }

    if (!file.transcription_text) {
        message.warning("该文件暂无转写内容，无法生成图谱");
        return;
    }

    // Upload as text file to Knowledge Base
    const blob = new Blob([file.transcription_text], { type: 'text/plain' });
    const textFile = new File([blob], `${file.filename}.txt`, { type: 'text/plain' });
    const formData = new FormData();
    formData.append('file', textFile);

    try {
        message.loading({ content: '正在提交图谱构建任务...', key: 'graph' });
        await api.post('/knowledge/upload', formData);
        message.success({ content: '已提交至知识库，图谱构建中', key: 'graph' });
    } catch (e) {
        message.error({ content: '提交失败: ' + (e.response?.data?.detail || e.message), key: 'graph' });
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD');
};

const formatDuration = (ms) => {
    if (!ms) return '00:00';
    const totalSec = Math.floor(ms / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
};

onMounted(() => {
    fetchFiles();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #CBD5E0;
}

@keyframes pulse-slow {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}
.animate-pulse-slow {
  animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>