<template>
  <div class="h-full flex flex-col bg-background text-foreground transition-colors duration-300">
    <!-- Header Banner -->
    <div class="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">音视频库</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-muted-foreground text-xs truncate max-w-xl">
            管理和分析您的媒体资源。
          </p>
        </div>
        <div class="flex gap-2">
           <Button 
            @click="triggerUpload" 
            size="sm"
            class="h-9"
          >
            <Upload class="w-4 h-4 mr-2" />
            上传
          </Button>
          <input type="file" ref="fileInput" class="hidden" accept="audio/*,video/*" @change="handleFileUpload">
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
      
      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        <div v-for="i in 10" :key="i" class="bg-card rounded-xl border border-border overflow-hidden h-[280px]">
            <Skeleton class="h-[157px] w-full" />
            <div class="p-4 space-y-3">
                 <Skeleton class="h-4 w-3/4" />
                 <Skeleton class="h-3 w-1/2" />
            </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <div class="w-20 h-20 bg-muted/50 rounded-2xl flex items-center justify-center mb-6 border border-border">
            <Film class="w-10 h-10 opacity-40" />
        </div>
        <span class="text-lg font-semibold text-foreground">暂无内容</span>
        <p class="text-sm mt-2 opacity-80">您的音视频库是空的</p>
      </div>

      <!-- File Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        <div v-for="file in files" :key="file.id" class="bg-card rounded-xl shadow-sm hover:shadow-md transition-all duration-300 flex flex-col group overflow-hidden relative border border-border">
            <!-- Thumbnail -->
            <div class="aspect-video bg-muted/30 flex items-center justify-center relative overflow-hidden group-hover:bg-muted/50 transition-colors">
                 <!-- Play Overlay -->
                 <div class="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center backdrop-blur-[1px] cursor-pointer z-10" @click="playMedia(file)">
                    <div class="w-10 h-10 bg-background/90 backdrop-blur-md rounded-full flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 transition-transform duration-300 text-foreground">
                        <Play class="w-4 h-4 ml-0.5 fill-current" />
                    </div>
                 </div>

                 <!-- Icon -->
                 <div v-if="file.is_folder" class="w-16 h-16 text-yellow-400">
                    <Folder class="w-full h-full fill-current" />
                 </div>
                 <div v-else class="w-20 h-20 transition-transform duration-500 group-hover:scale-105">
                    <img v-if="file.filename.toLowerCase().endsWith('.mp3')" src="/MP3.svg" class="w-full h-full" alt="MP3" />
                    <img v-else src="/MP4.svg" class="w-full h-full" alt="MP4" />
                 </div>
                 
                 <!-- Status Badge -->
                 <div class="absolute top-2 right-2 z-20">
                    <Badge v-if="file.asr_status === 'completed'" variant="secondary" class="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-transparent text-[10px] px-1.5 h-5">
                        已转写
                    </Badge>
                     <Badge v-else-if="file.asr_status === 'processing'" variant="secondary" class="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-transparent text-[10px] px-1.5 h-5 flex gap-1">
                        <Loader2 class="w-3 h-3 animate-spin" />
                        转写中
                    </Badge>
                 </div>
            </div>

            <!-- Content -->
            <div class="p-4 flex-1 flex flex-col">
                <div class="mb-2">
                    <h4 class="font-medium text-sm line-clamp-1 mb-1" :title="file.filename">{{ file.filename }}</h4>
                    <div class="flex items-center gap-2 text-xs text-muted-foreground">
                        <span class="font-mono">{{ formatDuration(file.duration) }}</span>
                        <span>•</span>
                        <span>{{ formatDate(file.created_at) }}</span>
                    </div>
                </div>

                <!-- Actions -->
                <div class="mt-auto pt-2 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div class="flex gap-1">
                        <Button variant="ghost" size="icon" class="h-7 w-7" @click="openRenameModal(file)" title="重命名">
                            <Edit2 class="w-3.5 h-3.5 text-muted-foreground" />
                        </Button>
                        <Button variant="ghost" size="icon" class="h-7 w-7 hover:text-destructive" @click="confirmDelete(file)" title="删除">
                            <Trash2 class="w-3.5 h-3.5" />
                        </Button>
                    </div>

                    <Button 
                        v-if="file.asr_status === 'completed'"
                        variant="ghost" 
                        size="sm" 
                        class="h-7 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 px-2"
                        @click="parseToGraph(file)"
                    >
                        <Share2 class="w-3.5 h-3.5 mr-1" />
                        解析图谱
                    </Button>
                </div>
            </div>
        </div>
      </div>
    </div>

    <!-- Rename Dialog -->
    <Dialog v-model:open="renameModalVisible">
        <DialogContent class="sm:max-w-[425px]">
            <DialogHeader>
                <DialogTitle>重命名</DialogTitle>
                <DialogDescription>请输入新的文件名称。</DialogDescription>
            </DialogHeader>
            <div class="py-4">
                <Input 
                    v-model="renameValue" 
                    placeholder="请输入新名称" 
                    @keydown.enter="handleRename"
                    autofocus
                />
            </div>
            <DialogFooter>
                <Button variant="outline" @click="renameModalVisible = false">取消</Button>
                <Button @click="handleRename">确认</Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>

    <!-- Player Dialog -->
    <Dialog v-model:open="playerVisible">
        <DialogContent class="sm:max-w-[800px] p-0 overflow-hidden bg-black border-zinc-800">
             <DialogHeader class="px-4 py-3 bg-zinc-900/50 border-b border-zinc-800 absolute top-0 left-0 right-0 z-10">
                <DialogTitle class="text-zinc-100 text-sm font-normal">{{ currentPlayingFile?.filename }}</DialogTitle>
            </DialogHeader>
            <div class="flex items-center justify-center min-h-[400px] bg-black pt-10">
                <video 
                    v-if="currentPlayingFile && isVideo(currentPlayingFile.filename)"
                    :src="playUrl" 
                    controls 
                    autoplay
                    class="w-full h-full max-h-[600px]"
                ></video>
                <div v-else-if="currentPlayingFile" class="w-full p-10 flex flex-col items-center justify-center">
                     <div class="w-32 h-32 rounded-full bg-zinc-800 flex items-center justify-center mb-8 animate-pulse">
                        <Music class="w-16 h-16 text-zinc-500" />
                     </div>
                     <audio 
                        :src="playUrl" 
                        controls 
                        autoplay
                        class="w-full max-w-md"
                    ></audio>
                </div>
            </div>
        </DialogContent>
    </Dialog>

    <!-- Delete Confirmation -->
    <AlertDialog :open="deleteConfirmOpen" @update:open="val => deleteConfirmOpen = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确定要删除此文件吗？</AlertDialogTitle>
          <AlertDialogDescription>
            此操作将永久删除该文件，无法恢复。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="deleteConfirmOpen = false">取消</AlertDialogCancel>
          <AlertDialogAction @click="executeDelete" class="bg-red-600 hover:bg-red-700 focus:ring-red-600">删除</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';
import { 
    Upload, 
    Film, 
    Play, 
    Folder, 
    Music, 
    Video, 
    Loader2, 
    Edit2, 
    Trash2, 
    Share2 
} from 'lucide-vue-next';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

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

// Delete State
const deleteConfirmOpen = ref(false);
const itemToDelete = ref(null);

const fetchFiles = async () => {
    loading.value = true;
    try {
        const res = await api.get('/recordings/');
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

const confirmDelete = (file) => {
    itemToDelete.value = file;
    deleteConfirmOpen.value = true;
};

const executeDelete = async () => {
    if (!itemToDelete.value) return;
    try {
        await api.delete(`/recordings/${itemToDelete.value.id}`);
        message.success("删除成功");
        fetchFiles();
    } catch (e) {
        message.error("删除失败");
    } finally {
        deleteConfirmOpen.value = false;
        itemToDelete.value = null;
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
</style>