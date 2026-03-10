
<template>
  <div class="h-full flex flex-col bg-white dark:bg-zinc-950 transition-colors duration-300">
    <!-- Compact Header -->
    <div class="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-white/95 dark:bg-zinc-950/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-zinc-950/60">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold text-zinc-900 dark:text-zinc-50 tracking-tight">知识库</h2>
        <div class="h-4 w-[1px] bg-zinc-200 dark:bg-zinc-800"></div>
        <Tabs :model-value="activeTab" @update:model-value="(val) => activeTab = val" class="w-[200px]">
          <TabsList class="grid w-full grid-cols-2 h-9">
            <TabsTrigger value="shared" class="text-xs">共享</TabsTrigger>
            <TabsTrigger value="personal" class="text-xs">个人</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      
      <!-- Right Side Actions -->
      <div class="flex items-center gap-2">
         <div class="relative w-64">
            <Search class="absolute left-2 top-2.5 h-4 w-4 text-zinc-500 dark:text-zinc-400" />
            <Input 
              placeholder="搜索文件..." 
              class="pl-8 h-9 text-sm bg-zinc-50 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 focus-visible:ring-1 focus-visible:ring-zinc-400 dark:focus-visible:ring-zinc-600" 
            />
         </div>
         <Button variant="outline" size="sm" class="h-9" @click="viewGlobalGraph" title="查看全局知识图谱">
            <Share2 class="w-4 h-4 mr-2" />
            全局图谱
         </Button>
      </div>
    </div>

    <!-- Toolbar & Breadcrumbs -->
    <div class="px-6 py-3 flex items-center justify-between bg-zinc-50/50 dark:bg-zinc-900/20 border-b border-zinc-200 dark:border-zinc-800">
       <!-- Left: Breadcrumbs -->
       <div class="flex items-center gap-1 text-sm text-zinc-600 dark:text-zinc-400">
          <div v-for="(crumb, index) in breadcrumbs" :key="index" class="flex items-center">
             <span 
                class="cursor-pointer hover:text-zinc-900 dark:hover:text-zinc-50 transition-colors px-1 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800"
                :class="index === breadcrumbs.length - 1 ? 'font-semibold text-zinc-900 dark:text-zinc-50' : ''"
                @click="navigateToBreadcrumb(index)"
             >
                {{ crumb.name }}
             </span>
             <span v-if="index < breadcrumbs.length - 1" class="text-zinc-400 dark:text-zinc-600 mx-1">/</span>
          </div>
       </div>

       <!-- Right: File Actions -->
       <div class="flex items-center gap-2">
            <div v-if="selectedFiles.length > 0" class="flex items-center gap-2 mr-4 bg-zinc-100 dark:bg-zinc-800 px-3 py-1 rounded-md">
                <span class="text-xs text-zinc-500 dark:text-zinc-400">已选 {{ selectedFiles.length }} 项</span>
                <div class="h-3 w-[1px] bg-zinc-300 dark:bg-zinc-600 mx-1"></div>
                <button @click="openMoveModal" class="text-xs text-zinc-700 dark:text-zinc-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium">移动</button>
                <button @click="confirmBatchDelete" class="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium ml-2">删除</button>
            </div>

            <input 
                type="file" 
                ref="fileInput" 
                class="hidden" 
                @change="handleFileUpload" 
                accept=".pdf,.txt,.md,.doc,.docx"
            >
            <Button size="sm" @click="$refs.fileInput.click()" :disabled="uploading" class="h-8">
                <UploadCloud class="w-4 h-4 mr-2" />
                <span v-if="uploading">上传中...</span>
                <span v-else>上传文件</span>
            </Button>
            <Button variant="outline" size="sm" @click="openNewFolder" class="h-8">
                <FolderPlus class="w-4 h-4 mr-2" />
                新建文件夹
            </Button>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger as-child>
                  <Button variant="ghost" size="icon" class="h-8 w-8 text-zinc-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20" @click="confirmCleanVector" :disabled="cleaningVector">
                    <Trash2 class="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>清空向量库</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
       </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-hidden p-6 bg-white dark:bg-zinc-950">
      <div 
          class="h-full flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-sm bg-white dark:bg-zinc-900"
      >
        <!-- Table Header -->
        <div class="flex items-center bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-200 dark:border-zinc-800 h-10 px-4 text-xs font-medium text-zinc-500 dark:text-zinc-400">
            <div class="w-[40px] flex justify-center">
                <Checkbox :checked="allSelected" :indeterminate="indeterminate" @update:checked="toggleSelectAll" />
            </div>
            <div class="flex-1 pl-2">文件名称</div>
            <div class="w-[100px]">大小</div>
            <div class="w-[180px]">上传/创建时间</div>
            <div class="w-[140px]">状态</div>
            <div class="w-[100px] text-right pr-4">操作</div>
        </div>

        <!-- File List -->
        <div class="flex-1 overflow-y-auto scroll-container" ref="scrollContainer" @scroll="onScroll">
            <div class="flex flex-col min-w-full">
                <div v-if="loading && files.length === 0" class="p-8 space-y-4">
                    <Skeleton class="h-12 w-full" v-for="i in 5" :key="i" />
                </div>
                
                <div v-else-if="files.length === 0 && !uploading" class="flex flex-col items-center justify-center py-20 text-zinc-400 dark:text-zinc-600">
                    <FolderOpen class="w-12 h-12 mb-3 opacity-20" />
                    <p class="text-sm">暂无文件</p>
                </div>
                
                <div 
                    v-for="file in files" 
                    :key="file.id" 
                    class="group flex items-center border-b border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors py-3 px-4 text-sm text-zinc-700 dark:text-zinc-200"
                >
                    <!-- Checkbox -->
                    <div class="w-[40px] flex justify-center" @click.stop>
                        <Checkbox :checked="selectedFiles.includes(file.id)" @update:checked="() => toggleSelect(file.id)" />
                    </div>

                    <!-- Name -->
                    <div 
                        class="flex-1 flex items-center gap-3 overflow-hidden cursor-pointer pl-2"
                        @click="file.is_folder ? openFolder(file) : null"
                    >
                         <!-- File Icon -->
                         <div class="w-8 h-8 flex items-center justify-center flex-shrink-0 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
                             <Folder v-if="file.is_folder" class="w-5 h-5 text-blue-500 dark:text-blue-400" fill="currentColor" />
                             <img v-else :src="getFileIcon(file.filename)" class="w-5 h-5 object-contain opacity-80" alt="icon" />
                         </div>
                         <div class="flex flex-col overflow-hidden">
                            <span class="truncate font-medium group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{{ file.filename }}</span>
                            <span v-if="!file.is_folder" class="text-[10px] text-zinc-400 dark:text-zinc-500 truncate">{{ file.id }}</span>
                         </div>
                    </div>
                    
                    <!-- Size -->
                    <div class="w-[100px] text-zinc-500 dark:text-zinc-400 text-xs font-mono">
                        {{ file.is_folder ? '-' : formatSize(file.file_size) }}
                    </div>
                    
                    <!-- Time -->
                    <div class="w-[180px] text-zinc-500 dark:text-zinc-400 text-xs">
                        {{ file.is_folder ? '-' : formatDate(file.created_at) }}
                    </div>
                    
                    <!-- Status -->
                    <div class="w-[140px]">
                        <template v-if="!file.is_folder">
                            <!-- Progress Bar for active states -->
                            <div v-if="['上传中', '解析中'].includes(file.status_text)" class="w-full pr-4">
                                <div class="flex justify-between items-center mb-1.5">
                                    <span class="text-[10px] text-blue-600 dark:text-blue-400 font-medium">
                                        {{ file.status_text }}
                                    </span>
                                    <span class="text-[10px] text-zinc-400">
                                        {{ file.progress || 0 }}%
                                    </span>
                                </div>
                                <Progress :model-value="file.progress || 0" class="h-1.5" />
                            </div>
                            
                            <!-- Standard Badge for other states -->
                            <Badge 
                                v-else 
                                variant="outline" 
                                class="font-normal text-xs"
                                :class="{
                                    'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-900': file.status_text === '已完成',
                                    'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900': file.status_text === '失败',
                                    'bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700': !['已完成', '失败'].includes(file.status_text)
                                }"
                            >
                                {{ file.status_text || '未知' }}
                            </Badge>
                        </template>
                        <span v-else class="text-zinc-400">-</span>
                    </div>
                    
                    <!-- Actions -->
                    <div class="w-[100px] flex items-center justify-end gap-2 pr-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button 
                            v-if="!file.is_folder && file.status_text === '已完成'"
                            variant="ghost" 
                            size="icon" 
                            class="h-8 w-8 text-zinc-500 hover:text-blue-600 dark:text-zinc-400 dark:hover:text-blue-400" 
                            @click="viewGraph(file)" 
                            title="查看知识图谱"
                        >
                            <Share2 class="w-4 h-4" />
                        </Button>
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            class="h-8 w-8 text-zinc-500 hover:text-red-600 hover:bg-red-50 dark:text-zinc-400 dark:hover:text-red-400 dark:hover:bg-red-900/20" 
                            @click="confirmDelete(file.id)" 
                            title="删除文件"
                        >
                            <Trash2 class="w-4 h-4" />
                        </Button>
                    </div>
                </div>
                
                <!-- Load More Spinner -->
                <div v-if="loadingMore" class="py-4 flex justify-center text-zinc-400 text-xs">
                    <Loader2 class="w-4 h-4 animate-spin mr-2" />
                    加载中...
                </div>
            </div>
        </div>
      </div>
    </div>

    <!-- Graph Modal -->
    <Dialog v-model:open="graphVisible">
        <DialogContent class="max-w-[95vw] w-[95vw] h-[90vh] p-0 overflow-hidden flex flex-col gap-0 dark:bg-zinc-900 dark:border-zinc-800">
            <DialogHeader class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex-shrink-0">
                <DialogTitle class="flex items-center gap-2 text-base">
                    <Share2 class="w-4 h-4 text-blue-500" />
                    <span class="truncate max-w-[600px]" :title="currentGraphTitle">{{ currentGraphTitle }}</span>
                </DialogTitle>
            </DialogHeader>
            <div class="flex-1 overflow-hidden relative">
                <KnowledgeGraphView :doc-id="currentDocId" :initial-scope="currentDocId ? 'doc' : 'global'" />
            </div>
        </DialogContent>
    </Dialog>

    <!-- New Folder Modal -->
    <Dialog v-model:open="newFolderVisible">
        <DialogContent class="sm:max-w-[425px] dark:bg-zinc-900 dark:border-zinc-800">
            <DialogHeader>
                <DialogTitle>新建文件夹</DialogTitle>
                <DialogDescription>
                    请输入新文件夹的名称。
                </DialogDescription>
            </DialogHeader>
            <div class="grid gap-4 py-4">
                <div class="grid gap-2">
                    <Label htmlFor="name" class="text-right">名称</Label>
                    <Input id="name" v-model="newFolderName" class="col-span-3" placeholder="我的文件夹" @keyup.enter="createFolder" />
                </div>
            </div>
            <DialogFooter>
                <Button variant="outline" @click="newFolderVisible = false">取消</Button>
                <Button @click="createFolder" :disabled="creatingFolder">
                    <Loader2 v-if="creatingFolder" class="w-4 h-4 mr-2 animate-spin" />
                    创建
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>

    <!-- Move Modal -->
    <Dialog v-model:open="moveModalVisible">
        <DialogContent class="sm:max-w-[425px] dark:bg-zinc-900 dark:border-zinc-800">
            <DialogHeader>
                <DialogTitle>移动到...</DialogTitle>
                <DialogDescription>
                    选择目标文件夹。
                </DialogDescription>
            </DialogHeader>
            <div class="py-4">
                <ScrollArea class="h-[300px] w-full border border-zinc-200 dark:border-zinc-800 rounded-md p-2">
                     <div 
                        v-for="folder in availableFolders" 
                        :key="folder.value"
                        class="px-3 py-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer flex items-center gap-3 transition-colors text-sm"
                        :class="{'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400': targetFolderId === folder.value}"
                        @click="targetFolderId = folder.value"
                     >
                         <Folder class="w-4 h-4 text-blue-400" fill="currentColor" />
                         <span>{{ folder.label }}</span>
                     </div>
                </ScrollArea>
            </div>
            <DialogFooter>
                <Button variant="outline" @click="moveModalVisible = false">取消</Button>
                <Button @click="confirmMove" :disabled="moving">
                    <Loader2 v-if="moving" class="w-4 h-4 mr-2 animate-spin" />
                    确认移动
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>

    <!-- Alert Dialogs -->
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

    <AlertDialog :open="batchDeleteConfirmOpen" @update:open="val => batchDeleteConfirmOpen = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确定要删除选中的 {{ selectedFiles.length }} 个项目吗？</AlertDialogTitle>
          <AlertDialogDescription>
            删除后可联系管理员恢复。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="batchDeleteConfirmOpen = false">取消</AlertDialogCancel>
          <AlertDialogAction @click="executeBatchDelete" class="bg-red-600 hover:bg-red-700 focus:ring-red-600">删除</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog :open="cleanVectorConfirmOpen" @update:open="val => cleanVectorConfirmOpen = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确定要清空向量库吗？</AlertDialogTitle>
          <AlertDialogDescription>
            此操作将删除向量库持久化数据并按当前模型重建，不影响图谱与已上传文件。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="cleanVectorConfirmOpen = false">取消</AlertDialogCancel>
          <AlertDialogAction @click="executeCleanVector" class="bg-red-600 hover:bg-red-700 focus:ring-red-600">清空并重建</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, createVNode, watch, computed } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue'; // Keep for global toast messages
import { 
    Search, 
    Share2, 
    UploadCloud, 
    FolderPlus, 
    Trash2, 
    Folder, 
    FolderOpen, 
    Loader2 
} from 'lucide-vue-next';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
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
import { Label } from '@/components/ui/label';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

import KnowledgeGraphView from './KnowledgeGraphView.vue';

const files = ref([]);
const uploading = ref(false);
const loading = ref(true);
const loadingMore = ref(false);
const page = ref(1);
const pageSize = 20;
const hasMore = ref(true);
const scrollContainer = ref(null);

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

// Folder State
const currentFolderId = ref(null);
const breadcrumbs = ref([{ id: null, name: '根目录' }]);

// Selection State
const selectedFiles = ref([]);
const allSelected = computed(() => {
    return files.value.length > 0 && selectedFiles.value.length === files.value.length;
});
const indeterminate = computed(() => {
    return selectedFiles.value.length > 0 && selectedFiles.value.length < files.value.length;
});

// Move State
const moveModalVisible = ref(false);
const targetFolderId = ref(null);
const moving = ref(false);
const availableFolders = ref([]); // For simple selection

// Graph State
const graphVisible = ref(false);
const currentGraphTitle = ref('');
const currentDocId = ref(null);

// Confirmation Dialog State
const deleteConfirmOpen = ref(false);
const batchDeleteConfirmOpen = ref(false);
const cleanVectorConfirmOpen = ref(false);
const itemToDelete = ref(null);

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

const fetchFiles = async (reset = false) => {
    if (reset) {
        page.value = 1;
        files.value = [];
        hasMore.value = true;
        loading.value = true;
    } else {
        if (!hasMore.value || loadingMore.value) return;
        loadingMore.value = true;
    }

    try {
        const params = {
            page: page.value,
            page_size: pageSize
        };
        if (currentFolderId.value) {
            params.parent_id = currentFolderId.value;
        }
        const res = await api.get('/knowledge/list', { params });
        const newFiles = res.data;
        
        if (newFiles.length < pageSize) {
            hasMore.value = false;
        }
        
        if (reset) {
            files.value = newFiles;
            selectedFiles.value = [];
        } else {
            files.value = [...files.value, ...newFiles];
        }
        
        page.value++;
        
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
        loadingMore.value = false;
    }
};

const onScroll = () => {
    if (!scrollContainer.value) return;
    const { scrollTop, clientHeight, scrollHeight } = scrollContainer.value;
    if (scrollTop + clientHeight >= scrollHeight - 20) {
        fetchFiles(false);
    }
};

const openFolder = (folder) => {
    currentFolderId.value = folder.id;
    breadcrumbs.value.push({ id: folder.id, name: folder.filename });
    fetchFiles(true);
};

const navigateToBreadcrumb = (index) => {
    const target = breadcrumbs.value[index];
    currentFolderId.value = target.id;
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1);
    fetchFiles(true);
};

const toggleSelectAll = () => {
    if (allSelected.value) {
        selectedFiles.value = [];
    } else {
        selectedFiles.value = files.value.map(f => f.id);
    }
};

const toggleSelect = (id) => {
    const index = selectedFiles.value.indexOf(id);
    if (index > -1) {
        selectedFiles.value.splice(index, 1);
    } else {
        selectedFiles.value.push(id);
    }
};

const confirmBatchDelete = () => {
    if (selectedFiles.value.length === 0) return;
    batchDeleteConfirmOpen.value = true;
};

const executeBatchDelete = async () => {
    try {
        await api.post('/knowledge/batch_delete', { item_ids: selectedFiles.value });
        message.success("批量删除成功");
        fetchFiles(true);
    } catch (e) {
        message.error("删除失败：" + (e.response?.data?.detail || e.message));
    } finally {
        batchDeleteConfirmOpen.value = false;
    }
};

const openMoveModal = async () => {
    if (selectedFiles.value.length === 0) return;
    
    try {
        const res = await api.get('/knowledge/list', { params: { parent_id: null, page: 1, page_size: 100 } });
        availableFolders.value = res.data.filter(f => f.is_folder).map(f => ({ label: f.filename, value: f.id }));
        // Add "Root" option
        availableFolders.value.unshift({ label: '根目录', value: null });
        
        targetFolderId.value = null;
        moveModalVisible.value = true;
    } catch (e) {
        message.error("无法加载文件夹列表");
    }
};

const confirmMove = async () => {
    moving.value = true;
    try {
        await api.post('/knowledge/move', { 
            target_parent_id: targetFolderId.value,
            item_ids: selectedFiles.value 
        });
        message.success("移动成功");
        moveModalVisible.value = false;
        fetchFiles(true);
    } catch (e) {
        message.error("移动失败：" + (e.response?.data?.detail || e.message));
    } finally {
        moving.value = false;
    }
};

const startPolling = () => {
    if (pollTimer) return;
    pollTimer = setInterval(() => fetchFiles(true), 3000); 
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
    cleanVectorConfirmOpen.value = true;
};

const executeCleanVector = async () => {
    cleaningVector.value = true;
    try {
        await api.post('/knowledge/vector/clean');
        message.success('向量库已清空并重建');
        fetchFiles(true);
    } catch (e) {
        message.error('清理失败：' + (e.response?.data?.detail || e.message));
    } finally {
        cleaningVector.value = false;
        cleanVectorConfirmOpen.value = false;
    }
};

const createFolder = async () => {
    const name = newFolderName.value.trim();
    if (!name) {
        message.warning('请输入文件夹名称');
        return;
    }
    creatingFolder.value = true;
    try {
        await api.post('/knowledge/folder', { name, parent_id: currentFolderId.value });
        message.success('文件夹已创建');
        newFolderVisible.value = false;
        resetNewFolder();
        fetchFiles(true);
    } catch (err) {
        message.error('创建失败：' + (err.response?.data?.detail || err.message));
    } finally {
        creatingFolder.value = false;
    }
};

const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    uploading.value = true;
    const formData = new FormData();
    formData.append('file', file);
    if (currentFolderId.value) {
        formData.append('parent_id', currentFolderId.value);
    }
    
    try {
        await api.post('/knowledge/upload', formData);
        message.success("上传成功，正在索引中...");
        fetchFiles(true);
    } catch (e) {
        message.error("上传失败：" + (e.response?.data?.detail || e.message));
    } finally {
        uploading.value = false;
        e.target.value = ''; 
    }
};

const confirmDelete = (id) => {
    itemToDelete.value = id;
    deleteConfirmOpen.value = true;
};

const executeDelete = async () => {
    if (!itemToDelete.value) return;
    try {
        await api.delete(`/knowledge/${itemToDelete.value}`);
        message.success("删除成功");
        fetchFiles(true);
    } catch (e) {
        message.error("删除失败");
    } finally {
        deleteConfirmOpen.value = false;
        itemToDelete.value = null;
    }
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
.scroll-container::-webkit-scrollbar {
  width: 6px;
  background: transparent;
  opacity: 0;
  transition: opacity 0.3s;
}
.scroll-container::-webkit-scrollbar-track {
  background: transparent;
}
.scroll-container::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
}
.scroll-container:hover::-webkit-scrollbar-thumb {
  background: #c9cdd4;
}
.scroll-container::-webkit-scrollbar-thumb:hover {
  background: #aab0b9;
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
