<template>
    <div class="h-full flex flex-col bg-background font-sans">
        <!-- Header & Filters -->
        <div class="flex flex-col gap-6 px-8 pt-8 pb-4 border-b border-border/40">
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <h1 class="text-2xl font-semibold text-foreground tracking-tight">录音纪要</h1>
                    <Badge variant="secondary" class="font-normal">{{ files.length }} 个文件</Badge>
                </div>
                <div class="flex gap-4">
                    <div class="relative w-72 transition-all focus-within:w-80">
                        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input 
                          type="text" 
                          placeholder="搜索录音标题或内容..." 
                          class="pl-9 bg-background"
                          v-model="searchQuery"
                        />
                    </div>
                </div>
            </div>
            
            <!-- Tags / Filters -->
            <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                <Button variant="default" size="sm" class="rounded-full shadow-md">全部</Button>
                <Button variant="outline" size="sm" class="rounded-full bg-background border-border text-muted-foreground hover:text-foreground">最近7天</Button>
                <Button variant="outline" size="sm" class="rounded-full bg-background border-border text-muted-foreground hover:text-foreground">我的项目</Button>
                <Button variant="outline" size="sm" class="rounded-full bg-background border-border text-muted-foreground hover:text-foreground gap-1.5">
                    <Star class="w-3.5 h-3.5" />
                    星标
                </Button>
            </div>
        </div>

        <!-- Content Area -->
        <div class="flex-1 overflow-y-auto px-8 py-6">
            <!-- Loading State -->
            <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                <div v-for="i in 8" :key="i" class="flex flex-col space-y-3">
                    <Skeleton class="h-[200px] w-full rounded-xl" />
                    <div class="space-y-2">
                        <Skeleton class="h-4 w-3/4" />
                        <Skeleton class="h-3 w-1/2" />
                    </div>
                </div>
            </div>

            <!-- Empty State -->
            <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-muted-foreground animate-in fade-in zoom-in duration-500">
                <div class="relative w-64 h-64 mb-6 opacity-80 hover:opacity-100 transition-opacity">
                     <!-- Custom SVG Illustration -->
                    <svg viewBox="0 0 400 300" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full drop-shadow-2xl">
                        <rect x="100" y="60" width="200" height="180" rx="16" class="fill-card stroke-border" stroke-width="2"/>
                        <rect x="120" y="90" width="160" height="12" rx="6" class="fill-muted"/>
                        <rect x="120" y="120" width="100" height="12" rx="6" class="fill-muted"/>
                        <rect x="120" y="150" width="140" height="12" rx="6" class="fill-muted"/>
                        <circle cx="280" cy="220" r="30" class="fill-primary/10"/>
                        <path d="M280 210V230M270 220H290" class="stroke-primary" stroke-width="3" stroke-linecap="round"/>
                        <!-- Floating Elements -->
                        <g class="animate-bounce" style="animation-duration: 3s;">
                             <circle cx="80" cy="100" r="12" class="fill-destructive/20"/>
                        </g>
                         <g class="animate-bounce" style="animation-duration: 4s;">
                             <circle cx="320" cy="80" r="8" class="fill-blue-500/20"/>
                        </g>
                    </svg>
                </div>
                <h3 class="text-xl font-semibold text-foreground mb-2">暂无录音记录</h3>
                <p class="text-muted-foreground max-w-sm text-center leading-relaxed mb-8">
                    您可以点击下方按钮开始新的录音，或导入现有的音频文件生成智能纪要。
                </p>
                <div class="flex gap-4">
                    <Button @click="openRecorder" size="lg" class="shadow-lg shadow-primary/20 gap-2">
                        <Mic class="w-5 h-5" />
                        开始录音
                    </Button>
                    <Button @click="triggerUpload" variant="outline" size="lg" class="gap-2">
                        <Upload class="w-5 h-5" />
                        导入音频
                    </Button>
                </div>
            </div>

            <!-- Card Grid -->
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-24">
                <!-- Folder Navigation -->
                <Card 
                    v-if="currentFolderId" 
                    @click="goUp" 
                    class="group cursor-pointer border-dashed border-2 hover:border-primary/50 hover:bg-muted/50 transition-all flex flex-col items-center justify-center min-h-[200px]"
                >
                    <div class="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-sm">
                        <CornerUpLeft class="w-7 h-7" />
                    </div>
                    <span class="font-semibold text-foreground group-hover:text-primary transition-colors">返回上一级</span>
                </Card>

                <!-- File Cards -->
                <Card 
                    v-for="file in filteredFiles" 
                    :key="file.id" 
                    class="group relative hover:shadow-lg hover:border-primary/20 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
                    @click="handleItemClick(file)"
                >
                    <!-- Card Header -->
                    <div class="p-6 pb-2 flex justify-between items-start">
                        <div class="flex items-center gap-4 overflow-hidden">
                             <div :class="[
                                'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border transition-colors',
                                file.is_folder ? 'bg-amber-50 text-amber-500 border-amber-100 dark:bg-amber-950/30 dark:border-amber-900/50' : 'bg-primary/10 text-primary border-primary/10'
                            ]">
                                <Folder v-if="file.is_folder" class="w-6 h-6 fill-current" />
                                <FileAudio v-else class="w-6 h-6" />
                            </div>
                            <div class="flex flex-col overflow-hidden">
                                <h3 class="font-semibold text-foreground truncate text-base mb-1 group-hover:text-primary transition-colors" :title="file.filename">{{ file.filename }}</h3>
                                <span class="text-xs text-muted-foreground font-medium">{{ formatDate(file.created_at) }}</span>
                            </div>
                        </div>
                        
                        <!-- More Actions -->
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute top-4 right-4" @click.stop>
                            <DropdownMenu>
                                <DropdownMenuTrigger as-child>
                                    <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted">
                                        <MoreVertical class="h-4 w-4 text-muted-foreground" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" class="w-40">
                                    <DropdownMenuItem @click="openRenameModal(file)">
                                        <Edit2 class="mr-2 h-4 w-4" />
                                        <span>重命名</span>
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem @click="confirmDelete(file)" class="text-destructive focus:text-destructive">
                                        <Trash2 class="mr-2 h-4 w-4" />
                                        <span>删除</span>
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    </div>

                    <!-- Waveform Placeholder / Status -->
                    <div v-if="!file.is_folder" class="flex-1 px-6 py-2 flex items-center justify-center relative">
                        <div class="w-full h-16 bg-muted/30 rounded-lg overflow-hidden flex items-center justify-center gap-1 group-hover:bg-primary/5 transition-colors border border-transparent group-hover:border-primary/10">
                            <!-- Static Waveform Visual -->
                             <div v-for="i in 24" :key="i" 
                                class="w-1 bg-primary/40 rounded-full transition-all duration-500 group-hover:bg-primary/60"
                                :style="{ height: (20 + Math.random() * 60) + '%', opacity: 0.3 + Math.random() * 0.7 }"
                             ></div>
                        </div>
                        
                        <!-- Play Overlay -->
                        <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-90 group-hover:scale-100">
                            <div class="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-lg shadow-primary/30 hover:scale-110 transition-transform">
                                <Play class="w-5 h-5 ml-0.5" />
                            </div>
                        </div>
                    </div>
                    <div v-else class="flex-1"></div>

                    <!-- Card Footer -->
                    <div class="px-6 py-4 border-t border-border/40 flex justify-between items-center bg-muted/20">
                        <span v-if="!file.is_folder" class="text-xs font-mono font-medium text-muted-foreground bg-background px-2 py-0.5 rounded border border-border/50 shadow-sm">{{ formatDuration(file.duration) }}</span>
                        <span v-else class="text-xs text-muted-foreground font-medium">文件夹</span>

                        <!-- Status Badge -->
                         <div v-if="!file.is_folder" class="flex items-center">
                            <Badge v-if="file.summary_status === 'completed'" variant="secondary" class="bg-green-50 text-green-700 hover:bg-green-100 border-green-200 gap-1.5 pl-1.5 pr-2.5">
                                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                已完成
                            </Badge>
                             <Badge v-else-if="file.summary_status === 'processing'" variant="secondary" class="bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200 gap-1.5 pl-1.5 pr-2.5">
                                <Loader2 class="w-3 h-3 animate-spin text-blue-500" />
                                处理中
                            </Badge>
                            <Badge v-else-if="file.summary_status === 'failed'" variant="destructive" class="gap-1.5 pl-1.5 pr-2.5">
                                <AlertCircle class="w-3 h-3" />
                                失败
                            </Badge>
                        </div>
                    </div>
                </Card>
            </div>
        </div>

        <!-- Global Floating Action Button (FAB) -->
        <div class="absolute bottom-10 right-10 z-50">
            <DropdownMenu>
                <DropdownMenuTrigger as-child>
                    <Button size="icon" class="w-14 h-14 rounded-full shadow-xl shadow-primary/30 hover:scale-105 active:scale-95 transition-all ring-4 ring-background">
                        <Plus class="w-7 h-7" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="w-48 p-2" side="top">
                    <DropdownMenuItem @click="openRecorder" class="py-3 px-3 cursor-pointer">
                        <div class="w-8 h-8 rounded-md bg-primary/10 text-primary flex items-center justify-center mr-3">
                            <Mic class="w-4 h-4" />
                        </div>
                        <span class="font-medium">发起录音</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem @click="triggerUpload" class="py-3 px-3 cursor-pointer">
                        <div class="w-8 h-8 rounded-md bg-purple-50 text-purple-600 flex items-center justify-center mr-3">
                            <Upload class="w-4 h-4" />
                        </div>
                        <span class="font-medium">导入音频</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem @click="createFolder" class="py-3 px-3 cursor-pointer">
                        <div class="w-8 h-8 rounded-md bg-amber-50 text-amber-600 flex items-center justify-center mr-3">
                            <FolderPlus class="w-4 h-4" />
                        </div>
                        <span class="font-medium">新建文件夹</span>
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>

        <!-- Hidden Input -->
        <input type="file" ref="fileInput" class="hidden" accept="audio/*" @change="handleFileUpload">

        <!-- Modals -->
        <Dialog v-model:open="createFolderModalVisible">
            <DialogContent class="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>新建文件夹</DialogTitle>
                    <DialogDescription>
                        请输入文件夹名称，创建后可用于归档录音文件。
                    </DialogDescription>
                </DialogHeader>
                <div class="grid gap-4 py-4">
                    <div class="grid gap-2">
                        <Input 
                            id="name" 
                            v-model="newFolderName" 
                            placeholder="文件夹名称" 
                            @keyup.enter="handleCreateFolderConfirm"
                            :class="{'border-destructive': folderNameError}"
                            autofocus
                        />
                        <span v-if="folderNameError" class="text-xs text-destructive">{{ folderNameError }}</span>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" @click="createFolderModalVisible = false">取消</Button>
                    <Button type="submit" @click="handleCreateFolderConfirm">创建</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>

        <Dialog v-model:open="renameModalVisible">
            <DialogContent class="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>重命名</DialogTitle>
                </DialogHeader>
                <div class="grid gap-4 py-4">
                    <Input 
                        v-model="renameValue" 
                        placeholder="请输入新名称" 
                        @keyup.enter="handleRename"
                        autofocus
                    />
                </div>
                <DialogFooter>
                    <Button variant="outline" @click="renameModalVisible = false">取消</Button>
                    <Button type="submit" @click="handleRename">保存</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>

        <AlertDialog v-model:open="deleteAlertVisible">
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>确认删除?</AlertDialogTitle>
                    <AlertDialogDescription>
                        此操作无法撤销。这将永久删除该文件/文件夹及其所有内容。
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>取消</AlertDialogCancel>
                    <AlertDialogAction @click="handleDeleteConfirm" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">确认删除</AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>

        <!-- Recorder Component -->
        <Recorder v-if="showRecorder" @close="showRecorder = false" @finish="handleFinish" />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import Recorder from './Recorder.vue';
import { useToast } from '@/components/ui/toast/use-toast';
import { 
    Search, Star, Mic, Upload, Folder, FileAudio, MoreVertical, 
    Edit2, Trash2, Play, Plus, FolderPlus, CornerUpLeft, Loader2, AlertCircle
} from 'lucide-vue-next';

// Shadcn UI Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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

// Define emits
const emit = defineEmits(['view-detail']);

// Setup Axios
const api = axios.create({
    baseURL: '/api/v1'
});

const { toast } = useToast();

const showRecorder = ref(false);
const files = ref<any[]>([]);
const loading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const searchQuery = ref('');

// Folder Logic
const currentFolderId = ref<string | null>(null);
const currentFolderName = ref('');
const createFolderModalVisible = ref(false);
const renameModalVisible = ref(false);
const deleteAlertVisible = ref(false);
const itemToDelete = ref<string | null>(null);

const newFolderName = ref('');
const folderNameError = ref('');
const itemToRename = ref<any>(null);
const renameValue = ref('');

// Computed
const filteredFiles = computed(() => {
    if (!searchQuery.value) return files.value;
    const query = searchQuery.value.toLowerCase();
    return files.value.filter(f => f.filename.toLowerCase().includes(query));
});

const fetchRecordings = async () => {
    loading.value = true;
    try {
        const params: any = {};
        if (currentFolderId.value) params.parent_id = currentFolderId.value;
        const res = await api.get('/recordings/', { params });
        files.value = res.data;
    } catch (e) {
        toast({
            variant: "destructive",
            title: "获取列表失败",
            description: "请检查网络连接或稍后重试"
        });
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
        toast({ title: "文件夹创建成功" });
        createFolderModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        toast({ variant: "destructive", title: "创建失败" });
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
        toast({ title: "重命名成功" });
        renameModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        toast({ variant: "destructive", title: "重命名失败" });
    }
};

const confirmDelete = (file: any) => {
    itemToDelete.value = file.id;
    deleteAlertVisible.value = true;
};

const handleDeleteConfirm = async () => {
    if (!itemToDelete.value) return;
    try {
        await api.delete(`/recordings/${itemToDelete.value}`);
        toast({ title: "删除成功" });
        fetchRecordings();
    } catch (e) {
        toast({ variant: "destructive", title: "删除失败" });
    } finally {
        deleteAlertVisible.value = false;
        itemToDelete.value = null;
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
        toast({ title: "上传处理中...", description: "请稍候" });
        await api.post('/recordings/upload', formData);
        toast({ title: "上传成功" });
        fetchRecordings();
    } catch (e) {
        toast({ variant: "destructive", title: "上传失败" });
        console.error(e);
    }
};

const viewDetail = (file: any) => {
    emit('view-detail', file);
};

const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD'); 
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
