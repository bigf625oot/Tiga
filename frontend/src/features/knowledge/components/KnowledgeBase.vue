
<template>
  <div class="h-full flex flex-col bg-background overflow-hidden transition-colors duration-300">
    <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold tracking-tight text-foreground">知识库</h2>
        <div class="h-4 w-px bg-border"></div>
        <p class="text-xs text-muted-foreground m-0 truncate max-w-xl">管理和组织您的知识文档。</p>
      </div>
      <div class="flex items-center gap-2">
        <Button v-if="activeTab === 'personal'" size="sm" class="h-9 shadow-sm" @click="$refs.fileInput.click()" :disabled="uploading">
          <UploadCloud class="w-4 h-4 mr-2" />
          <span v-if="uploading">上传中...</span>
          <span v-else>上传文件</span>
        </Button>
        <div v-else class="h-9 w-9"></div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden bg-muted/10">
        <!-- Filter & Search Bar -->
        <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b flex-shrink-0">
            <!-- Left: Empty placeholder to balance flex layout -->
            <div class="hidden md:block w-full md:w-64"></div>

            <!-- Center: View Tabs -->
            <div class="flex items-center justify-center flex-1">
                <Tabs :model-value="activeTab" @update:model-value="(val) => activeTab = val" class="w-[200px]">
                    <TabsList class="grid w-full grid-cols-2 h-9 bg-muted/80 p-1 rounded-lg border border-border/50 items-center">
                        <TabsTrigger value="shared" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">共享空间</TabsTrigger>
                        <TabsTrigger value="personal" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">个人空间</TabsTrigger>
                    </TabsList>
                </Tabs>
            </div>

            <!-- Right: Actions -->
            <div class="flex items-center gap-3 w-full md:w-auto justify-end">
                <div class="relative w-full md:w-64 group">
                    <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    <Input 
                        v-model="searchQuery"
                        placeholder="搜索文件..." 
                        class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50" 
                    />
                    <button v-if="searchQuery" @click="searchQuery = ''" class="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors" aria-label="清空搜索">
                      <X class="h-4 w-4" />
                    </button>
                </div>
                
                <div class="h-4 w-px bg-border hidden md:block mx-1"></div>

                <!-- Secondary Actions -->
                <div class="flex items-center gap-2">
                    <Button v-if="activeTab === 'personal'" variant="outline" size="sm" @click="openNewFolder" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
                        <FolderPlus class="w-3.5 h-3.5" />
                        新建文件夹
                    </Button>
                    <Button variant="outline" size="sm" @click="viewGlobalGraph" title="查看全局知识图谱" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
                        <Share2 class="w-3.5 h-3.5" />
                        全局图谱
                    </Button>
                    <TooltipProvider v-if="activeTab === 'personal'">
                        <Tooltip>
                            <TooltipTrigger as-child>
                                <Button variant="ghost" size="icon" class="h-9 w-9 text-muted-foreground hover:text-destructive hover:bg-destructive/10 shadow-sm transition-all hover:scale-105 active:scale-95 flex-shrink-0" @click="confirmCleanVector" :disabled="cleaningVector">
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
        </div>

        <!-- Toolbar (Breadcrumbs & Batch Actions) -->
        <div class="px-6 py-2 flex items-center justify-between bg-muted/30 border-b border-border flex-shrink-0 min-h-[40px]">
           <!-- Left: Breadcrumbs -->
           <div class="flex items-center gap-1 text-sm text-muted-foreground">
              <div v-for="(crumb, index) in breadcrumbs" :key="index" class="flex items-center">
                 <span 
                    class="cursor-pointer hover:text-foreground transition-colors px-2 py-1 rounded hover:bg-muted"
                    :class="index === breadcrumbs.length - 1 ? 'font-semibold text-foreground' : ''"
                    @click="navigateToBreadcrumb(index)"
                 >
                    {{ crumb.name }}
                 </span>
                 <span v-if="index < breadcrumbs.length - 1" class="text-muted-foreground/50 mx-1">/</span>
              </div>
           </div>

           <!-- Right: Batch Actions -->
           <div class="flex items-center gap-2">
                <div v-if="selectedFiles.length > 0 && activeTab === 'personal'" class="flex items-center gap-2 mr-4 bg-muted px-3 py-1 rounded-md">
                    <span class="text-xs text-muted-foreground">已选 {{ selectedFiles.length }} 项</span>
                    <div class="h-3 w-[1px] bg-border mx-1"></div>
                    <button @click="openMoveModal" class="text-xs font-medium text-foreground hover:text-primary transition-colors">移动</button>
                    <button @click="confirmBatchDelete" class="text-xs font-medium text-destructive hover:text-destructive/80 transition-colors ml-2">删除</button>
                </div>
                <div v-else-if="selectedFiles.length > 0" class="text-xs text-muted-foreground mr-4">
                     已选 {{ selectedFiles.length }} 项 (只读)
                </div>

                <input 
                    type="file" 
                    ref="fileInput" 
                    class="hidden" 
                    @change="handleFileUpload" 
                    accept=".pdf,.txt,.md,.doc,.docx"
                >
                <div class="text-xs text-muted-foreground whitespace-nowrap">共 {{ files.length }} 个文件</div>
           </div>
        </div>

        <div class="flex-1 overflow-hidden p-6 bg-transparent">
          <div class="h-full flex flex-col gap-4">
            <div v-if="searchQuery" class="flex items-center gap-2">
              <h3 class="text-lg font-semibold tracking-tight text-foreground">搜索结果</h3>
              <span class="text-sm text-muted-foreground">({{ files.length }})</span>
            </div>

            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2" @click.stop>
                <Checkbox :checked="allSelected" :indeterminate="indeterminate" @update:checked="toggleSelectAll" :disabled="activeTab === 'shared'" aria-label="全选" />
                <span class="text-xs text-muted-foreground">全选</span>
              </div>
            </div>

            <div class="flex-1 overflow-y-auto scroll-container" ref="scrollContainer" @scroll="onScroll">
              <div v-if="loading && files.length === 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start p-1">
                <div v-for="i in 8" :key="i" class="bg-card rounded-xl border border-border/60 overflow-hidden h-[190px] p-5 space-y-3">
                  <div class="flex items-center gap-4">
                    <Skeleton class="h-12 w-12 rounded-xl" />
                    <div class="flex-1 space-y-2">
                      <Skeleton class="h-4 w-3/4" />
                      <Skeleton class="h-3 w-1/2" />
                    </div>
                  </div>
                  <Skeleton class="h-3 w-full" />
                  <Skeleton class="h-3 w-5/6" />
                </div>
              </div>

              <div v-else-if="files.length === 0 && !uploading" class="flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto">
                <div class="w-12 h-12 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
                  <Search v-if="searchQuery" class="w-10 h-10 text-muted-foreground/50" />
                  <!-- <FolderOpen v-else class="w-10 h-10 text-muted-foreground/50" /> -->
                  <img src="/Placeholder/null_file.svg" alt="Placeholder" class="w-full h-full object-cover" />
                </div>
                <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">{{ searchQuery ? '未找到相关文件' : '暂无文件' }}</h3>
                <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">{{ searchQuery ? '请尝试更换关键词搜索，或清空筛选条件。' : (activeTab === 'personal' ? '当前目录暂无文件，您可以上传文件或新建文件夹开始整理。' : '共享空间暂无可用文件。') }}</p>
                <div v-if="!searchQuery && activeTab === 'personal'" class="flex items-center gap-3">
                  <Button @click="$refs.fileInput.click()" class="px-8 shadow-sm hover:scale-105 transition-transform" :disabled="uploading">
                    <UploadCloud class="w-4 h-4 mr-2" />
                    上传文件
                  </Button>
                  <Button variant="outline" @click="openNewFolder" class="px-8 shadow-sm hover:scale-105 transition-transform">
                    <FolderPlus class="w-4 h-4 mr-2" />
                    新建文件夹
                  </Button>
                </div>
              </div>

              <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start p-1">
                <KnowledgeItemCard
                  v-for="file in files"
                  :key="file.id"
                  :item="file"
                  :selected="selectedFiles.includes(file.id)"
                  :readonly="activeTab === 'shared'"
                  :icon-src="file.is_folder ? '' : getFileIcon(file.filename)"
                  :size-text="file.is_folder ? '-' : formatSize(file.file_size)"
                  :created-at-text="file.is_folder ? '-' : formatDate(file.created_at)"
                  @toggleSelect="toggleSelect(file.id)"
                  @openFolder="openFolder(file)"
                  @viewGraph="viewGraph(file)"
                  @move="openMoveForItem(file)"
                  @retry="retryFile(file)"
                  @delete="confirmDelete(file.id)"
                />
                <template v-if="loadingMore">
                  <div v-for="i in 4" :key="'skel-more-'+i" class="bg-card rounded-xl border border-border/60 overflow-hidden h-[190px] p-5 space-y-3">
                    <div class="flex items-center gap-4">
                      <Skeleton class="h-12 w-12 rounded-xl" />
                      <div class="flex-1 space-y-2">
                        <Skeleton class="h-4 w-3/4" />
                        <Skeleton class="h-3 w-1/2" />
                      </div>
                    </div>
                    <Skeleton class="h-3 w-full" />
                    <Skeleton class="h-3 w-5/6" />
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
    </div>

    <!-- Graph Modal -->
    <Dialog v-model:open="graphVisible">
        <DialogContent class="max-w-[95vw] w-[95vw] h-[90vh] p-0 overflow-hidden flex flex-col gap-0 bg-background border-border">
            <DialogHeader class="px-6 py-4 border-b border-border flex-shrink-0">
                <DialogTitle class="flex items-center gap-2 text-base text-foreground">
                    <Share2 class="w-4 h-4 text-primary" />
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
        <DialogContent class="sm:max-w-[425px] bg-background border-border">
            <DialogHeader>
                <DialogTitle class="text-foreground">新建文件夹</DialogTitle>
                <DialogDescription class="text-muted-foreground">
                    请输入新文件夹的名称。
                </DialogDescription>
            </DialogHeader>
            <div class="grid gap-4 py-4">
                <div class="grid gap-2">
                    <Label htmlFor="name" class="text-right text-foreground">名称</Label>
                    <Input id="name" v-model="newFolderName" class="col-span-3 bg-background border-input" placeholder="我的文件夹" @keyup.enter="createFolder" />
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
        <DialogContent class="sm:max-w-[425px] bg-background border-border">
            <DialogHeader>
                <DialogTitle class="text-foreground">移动到...</DialogTitle>
                <DialogDescription class="text-muted-foreground">
                    选择目标文件夹。
                </DialogDescription>
            </DialogHeader>
            <div class="py-4">
                <ScrollArea class="h-[300px] w-full border border-border rounded-md p-2">
                     <div 
                        v-for="folder in availableFolders" 
                        :key="folder.value"
                        class="px-3 py-2 rounded-md hover:bg-muted cursor-pointer flex items-center gap-3 transition-colors text-sm text-foreground"
                        :class="{'bg-primary/10 text-primary': targetFolderId === folder.value}"
                        @click="targetFolderId = folder.value"
                     >
                         <Folder class="w-4 h-4 text-primary" fill="currentColor" />
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
          <AlertDialogAction @click="executeDelete" class="bg-destructive hover:bg-destructive/90 focus:ring-destructive">删除</AlertDialogAction>
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
          <AlertDialogAction @click="executeBatchDelete" class="bg-destructive hover:bg-destructive/90 focus:ring-destructive">删除</AlertDialogAction>
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
          <AlertDialogAction @click="executeCleanVector" class="bg-destructive hover:bg-destructive/90 focus:ring-destructive">清空并重建</AlertDialogAction>
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
    X,
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
import { Skeleton } from '@/components/ui/skeleton';
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
import KnowledgeItemCard from './KnowledgeItemCard.vue';

const files = ref([]);
const uploading = ref(false);
const loading = ref(true);
const loadingMore = ref(false);
const page = ref(1);
const pageSize = 20;
const hasMore = ref(true);
const scrollContainer = ref(null);

const activeTab = ref('personal'); // shared | personal
const searchQuery = ref('');
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
let searchTimer = null;
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

const fetchFiles = async (reset = false, silent = false) => {
    let currentFetchPage = 1;
    let currentFetchPageSize = pageSize;

    if (reset) {
        if (!silent) {
            page.value = 1;
            files.value = [];
            hasMore.value = true;
            loading.value = true;
        } else {
            currentFetchPageSize = Math.max(pageSize, (page.value - 1) * pageSize);
        }
    } else {
        if (!hasMore.value || loadingMore.value) return;
        loadingMore.value = true;
        currentFetchPage = page.value;
    }

    try {
        const params = {
            page: currentFetchPage,
            page_size: currentFetchPageSize
        };
        if (searchQuery.value && searchQuery.value.trim()) {
            params.keyword = searchQuery.value.trim();
        }
        if (currentFolderId.value) {
            params.parent_id = currentFolderId.value;
        }
        const res = await api.get('/knowledge/list', { params });
        const newFiles = res.data;
        
        if (reset) {
            if (!silent) {
                if (newFiles.length < pageSize) hasMore.value = false;
            } else {
                if (newFiles.length < currentFetchPageSize) hasMore.value = false;
            }
        } else {
            if (newFiles.length < pageSize) {
                hasMore.value = false;
            }
        }
        
        if (reset) {
            files.value = newFiles;
            if (!silent) {
                selectedFiles.value = [];
            } else {
                selectedFiles.value = selectedFiles.value.filter(id => newFiles.some(f => f.id === id));
            }
        } else {
            files.value = [...files.value, ...newFiles];
        }
        
        if (!reset) {
            page.value++;
        } else if (!silent) {
            page.value = 2;
        }
        
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
        if (!silent) loading.value = false;
        loadingMore.value = false;
    }
};

watch(searchQuery, () => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        if (scrollContainer.value) scrollContainer.value.scrollTop = 0;
        fetchFiles(true);
    }, 300);
});

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

const retryFile = async (file) => {
    try {
        message.loading({ content: '正在提交重试请求...', key: 'retry' });
        await api.post(`/knowledge/${file.id}/retry`);
        message.success({ content: '重试已触发', key: 'retry' });
        fetchFiles(true);
    } catch (e) {
        console.error("Retry failed:", e);
        message.error({ content: '重试失败: ' + (e.response?.data?.detail || e.message), key: 'retry' });
    }
};

const confirmBatchDelete = () => {
    if (selectedFiles.value.length === 0) return;
    batchDeleteConfirmOpen.value = true;
};

const openMoveForItem = (file) => {
    if (activeTab.value !== 'personal') return;
    selectedFiles.value = [file.id];
    openMoveModal();
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
    pollTimer = setInterval(() => fetchFiles(true, true), 3000); 
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
onUnmounted(() => {
    stopPolling();
    if (searchTimer) clearTimeout(searchTimer);
});
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
