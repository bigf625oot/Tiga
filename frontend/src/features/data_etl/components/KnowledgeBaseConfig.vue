<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { 
  Library, Plus, Search, FolderOpen, FileText, Users, Shield, 
  Settings, Save, Trash2, Edit3, Check, X, AlertCircle,
  ChevronRight, MoreVertical, Upload, Download, Copy, Eye
} from 'lucide-vue-next';

const { toast } = useToast();

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  fileCount: number;
  folderCount: number;
  status: 'active' | 'inactive';
}

interface KnowledgeFile {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size?: string;
  children?: KnowledgeFile[];
  createdAt: string;
  authorizedRoles: string[];
  authorizedUsers: string[];
}

interface Role {
  id: string;
  name: string;
}

interface User {
  id: string;
  name: string;
  avatar?: string;
}

const mockKnowledgeBases: KnowledgeBase[] = [
  { id: '1', name: '产品知识库', description: '公司产品相关文档和技术规格', createdAt: '2024-01-15', updatedAt: '2024-03-10', fileCount: 156, folderCount: 12, status: 'active' },
  { id: '2', name: '客服知识库', description: '客服常见问题解答和操作指南', createdAt: '2024-02-01', updatedAt: '2024-03-12', fileCount: 89, folderCount: 5, status: 'active' },
  { id: '3', name: '培训资料库', description: '新员工培训材料和教程', createdAt: '2024-02-20', updatedAt: '2024-03-08', fileCount: 45, folderCount: 8, status: 'inactive' },
];

const mockRoles: Role[] = [
  { id: 'r1', name: '管理员' },
  { id: 'r2', name: '产品经理' },
  { id: 'r3', name: '客服专员' },
  { id: 'r4', name: '普通员工' },
];

const mockUsers: User[] = [
  { id: 'u1', name: '张三' },
  { id: 'u2', name: '李四' },
  { id: 'u3', name: '王五' },
];

const mockFiles: KnowledgeFile[] = [
  { 
    id: 'f1', name: '产品手册', type: 'folder', createdAt: '2024-01-15', authorizedRoles: ['r1', 'r2'], authorizedUsers: [],
    children: [
      { id: 'f1-1', name: '产品介绍.pdf', type: 'file', size: '2.3MB', createdAt: '2024-01-16', authorizedRoles: [], authorizedUsers: [] },
      { id: 'f1-2', name: '技术规格.docx', type: 'file', size: '1.1MB', createdAt: '2024-01-17', authorizedRoles: [], authorizedUsers: [] },
    ]
  },
  { id: 'f2', name: '常见问题', type: 'folder', createdAt: '2024-01-20', authorizedRoles: ['r3'], authorizedUsers: [],
    children: [
      { id: 'f2-1', name: 'FAQ.pdf', type: 'file', size: '856KB', createdAt: '2024-01-21', authorizedRoles: [], authorizedUsers: [] },
    ]
  },
  { id: 'f3', name: '更新日志.txt', type: 'file', size: '12KB', createdAt: '2024-02-01', authorizedRoles: [], authorizedUsers: [] },
];

const knowledgeBases = ref<KnowledgeBase[]>(mockKnowledgeBases);
const activeKnowledgeBaseId = ref<string | null>(null);
const activeTab = ref('info');
const searchQuery = ref('');
const hasUnsavedChanges = ref(false);

const config = reactive({
  enableRAG: true,
  enableKG: true,
  chunkSize: 512,
  embeddingModel: 'text-embedding-3-small',
  retrievalStrategy: 'hybrid',
  maxFileSize: 100,
  allowedFileTypes: ['.pdf', '.docx', '.txt', '.md'],
});

const isAddDialogOpen = ref(false);
const isDeleteDialogOpen = ref(false);
const isEditMode = ref(false);
const editingFileId = ref<string | null>(null);
const itemToDelete = ref<{ id: string; type: 'base' | 'file' | 'folder' } | null>(null);

const newKnowledgeBase = reactive({
  name: '',
  description: '',
  status: 'active' as 'active' | 'inactive',
});

const editForm = reactive({
  name: '',
  description: '',
  status: 'active' as 'active' | 'inactive',
});

const expandedFolders = ref<Set<string>>(new Set(['f1', 'f2']));
const selectedFiles = ref<Set<string>>(new Set());
const currentFiles = ref<KnowledgeFile[]>(mockFiles);

const activeKnowledgeBase = computed(() => {
  return knowledgeBases.value.find(kb => kb.id === activeKnowledgeBaseId.value);
});

const filteredKnowledgeBases = computed(() => {
  if (!searchQuery.value) return knowledgeBases.value;
  const query = searchQuery.value.toLowerCase();
  return knowledgeBases.value.filter(kb => 
    kb.name.toLowerCase().includes(query) || 
    kb.description.toLowerCase().includes(query)
  );
});

const selectedFilesList = computed(() => {
  return currentFiles.value.filter(f => selectedFiles.value.has(f.id));
});

const toggleFolder = (folderId: string) => {
  if (expandedFolders.value.has(folderId)) {
    expandedFolders.value.delete(folderId);
  } else {
    expandedFolders.value.add(folderId);
  }
};

const selectKnowledgeBase = (id: string) => {
  if (hasUnsavedChanges.value) {
    toast({
      title: '无法切换',
      description: '您有未保存的更改，请先保存或撤销后再切换。',
      variant: 'destructive',
    });
    return;
  }
  activeKnowledgeBaseId.value = id;
  resetEditForm();
};

const resetEditForm = () => {
  if (activeKnowledgeBase.value) {
    editForm.name = activeKnowledgeBase.value.name;
    editForm.description = activeKnowledgeBase.value.description;
    editForm.status = activeKnowledgeBase.value.status;
  }
  isEditMode.value = false;
};

const saveEdit = () => {
  if (!editForm.name.trim()) {
    toast({
      title: '验证失败',
      description: '知识库名称不能为空',
      variant: 'destructive',
    });
    return;
  }
  
  const kb = knowledgeBases.value.find(k => k.id === activeKnowledgeBaseId.value);
  if (kb) {
    kb.name = editForm.name;
    kb.description = editForm.description;
    kb.status = editForm.status;
    kb.updatedAt = new Date().toISOString().split('T')[0];
    hasUnsavedChanges.value = false;
    isEditMode.value = false;
    toast({
      title: '保存成功',
      description: '知识库信息已更新',
    });
  }
};

const handleAddKnowledgeBase = () => {
  if (!newKnowledgeBase.name.trim()) {
    toast({
      title: '验证失败',
      description: '知识库名称不能为空',
      variant: 'destructive',
    });
    return;
  }

  const newKB: KnowledgeBase = {
    id: Date.now().toString(),
    name: newKnowledgeBase.name,
    description: newKnowledgeBase.description,
    createdAt: new Date().toISOString().split('T')[0],
    updatedAt: new Date().toISOString().split('T')[0],
    fileCount: 0,
    folderCount: 0,
    status: newKnowledgeBase.status,
  };

  knowledgeBases.value.unshift(newKB);
  activeKnowledgeBaseId.value = newKB.id;
  
  Object.assign(newKnowledgeBase, { name: '', description: '', status: 'active' });
  isAddDialogOpen.value = false;
  
  toast({
    title: '创建成功',
    description: `知识库"${newKB.name}"已创建`,
  });
};

const confirmDelete = (item: { id: string; type: 'base' | 'file' | 'folder' }) => {
  itemToDelete.value = item;
  isDeleteDialogOpen.value = true;
};

const handleDelete = () => {
  if (!itemToDelete.value) return;

  if (itemToDelete.value.type === 'base') {
    const kb = knowledgeBases.value.find(k => k.id === itemToDelete.value!.id);
    knowledgeBases.value = knowledgeBases.value.filter(k => k.id !== itemToDelete.value!.id);
    if (activeKnowledgeBaseId.value === itemToDelete.value.id) {
      activeKnowledgeBaseId.value = knowledgeBases.value[0]?.id || null;
    }
    toast({
      title: '删除成功',
      description: `知识库"${kb?.name}"已删除`,
    });
  }

  itemToDelete.value = null;
  isDeleteDialogOpen.value = false;
};

const saveConfig = () => {
  toast({
    title: '保存成功',
    description: '知识库配置已更新',
  });
  hasUnsavedChanges.value = false;
};

const discardChanges = () => {
  hasUnsavedChanges.value = false;
  resetEditForm();
  toast({
    title: '已撤销',
    description: '所有未保存的更改已撤销',
  });
};

const toggleFileSelection = (fileId: string) => {
  if (selectedFiles.value.has(fileId)) {
    selectedFiles.value.delete(fileId);
  } else {
    selectedFiles.value.add(fileId);
  }
};

const toggleFileAuthorization = (fileId: string, type: 'role' | 'user', id: string, authorized: boolean) => {
  const file = findFileById(fileId);
  if (!file) return;
  
  if (type === 'role') {
    if (authorized) {
      file.authorizedRoles = file.authorizedRoles.filter(r => r !== id);
    } else {
      file.authorizedRoles.push(id);
    }
  } else {
    if (authorized) {
      file.authorizedUsers = file.authorizedUsers.filter(u => u !== id);
    } else {
      file.authorizedUsers.push(id);
    }
  }
  hasUnsavedChanges.value = true;
};

const findFileById = (id: string): KnowledgeFile | null => {
  for (const file of currentFiles.value) {
    if (file.id === id) return file;
    if (file.children) {
      const found = file.children.find(c => c.id === id);
      if (found) return found;
    }
  }
  return null;
};

const toggleKnowledgeBaseAuthorization = (type: 'role' | 'user', id: string, authorized: boolean) => {
  const kb = knowledgeBases.value.find(k => k.id === activeKnowledgeBaseId.value);
  if (!kb) return;
  hasUnsavedChanges.value = true;
};

const getFileIcon = (type: 'file' | 'folder') => {
  return type === 'folder' ? FolderOpen : FileText;
};

const formatFileSize = (size?: string) => {
  return size || '-';
};

const getStatusBadge = (status: 'active' | 'inactive') => {
  return status === 'active' 
    ? { label: '启用', class: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' }
    : { label: '停用', class: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' };
};
</script>

<template>
  <div class="flex h-full min-h-[600px] gap-6">
    <!-- Left Panel: Knowledge Base List -->
    <Card class="w-80 flex flex-col dark:bg-slate-950 dark:border-slate-800">
      <CardHeader class="pb-4">
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="text-lg flex items-center gap-2">
              <Library class="w-5 h-5" />
              知识库
            </CardTitle>
            <CardDescription class="mt-1">管理知识库与文档</CardDescription>
          </div>
          <Dialog v-model:open="isAddDialogOpen">
            <DialogTrigger as-child>
              <Button variant="outline" size="icon" :disabled="hasUnsavedChanges">
                <Plus class="w-4 h-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>新建知识库</DialogTitle>
                <DialogDescription>创建一个新的知识库，用于存储和管理文档。</DialogDescription>
              </DialogHeader>
              <div class="space-y-4 py-4">
                <div class="space-y-2">
                  <Label>知识库名称 <span class="text-destructive">*</span></Label>
                  <Input v-model="newKnowledgeBase.name" placeholder="例如：产品知识库" />
                </div>
                <div class="space-y-2">
                  <Label>描述</Label>
                  <Input v-model="newKnowledgeBase.description" placeholder="简要描述知识库的用途" />
                </div>
                <div class="flex items-center justify-between p-3 border rounded-lg">
                  <div class="space-y-0.5">
                    <Label class="text-base">启用状态</Label>
                    <p class="text-sm text-muted-foreground">知识库创建后是否立即启用</p>
                  </div>
                  <Switch v-model="newKnowledgeBase.status" :checked="newKnowledgeBase.status === 'active'" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" @click="isAddDialogOpen = false">取消</Button>
                <Button @click="handleAddKnowledgeBase">创建</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        
        <!-- Search -->
        <div class="relative mt-4">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            v-model="searchQuery"
            placeholder="搜索知识库..." 
            class="pl-9"
          />
        </div>
      </CardHeader>

      <CardContent class="flex-1 overflow-hidden p-0">
        <ScrollArea class="h-[calc(100vh-18rem)]">
          <div class="px-4 pb-4 space-y-2">
            <div v-if="filteredKnowledgeBases.length === 0" class="text-center py-8 text-muted-foreground">
              <Library class="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p class="text-sm">未找到知识库</p>
              <Button variant="link" class="mt-2" @click="isAddDialogOpen = true">
                创建第一个知识库
              </Button>
            </div>

            <div 
              v-for="kb in filteredKnowledgeBases" 
              :key="kb.id"
              @click="selectKnowledgeBase(kb.id)"
              class="group relative p-3 rounded-lg border cursor-pointer transition-colors"
              :class="[
                activeKnowledgeBaseId === kb.id 
                  ? 'bg-primary/10 border-primary/50 dark:bg-primary/20 dark:border-primary/50' 
                  : 'hover:bg-muted dark:hover:bg-slate-900 border-transparent dark:border-transparent'
              ]"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-medium text-sm truncate dark:text-slate-200">{{ kb.name }}</span>
                    <Badge :class="getStatusBadge(kb.status).class" class="text-[10px] px-1.5 py-0 h-4">
                      {{ getStatusBadge(kb.status).label }}
                    </Badge>
                  </div>
                  <div class="text-xs text-muted-foreground dark:text-slate-400 truncate mb-2">
                    {{ kb.description || '暂无描述' }}
                  </div>
                  <div class="flex items-center gap-3 text-xs text-muted-foreground/70">
                    <span class="flex items-center gap-1">
                      <FolderOpen class="w-3 h-3" />
                      {{ kb.folderCount }}
                    </span>
                    <span class="flex items-center gap-1">
                      <FileText class="w-3 h-3" />
                      {{ kb.fileCount }}
                    </span>
                  </div>
                </div>
                <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                  <Popover>
                    <PopoverTrigger as-child>
                      <Button variant="ghost" size="icon" class="h-8 w-8" @click.stop>
                        <MoreVertical class="w-4 h-4" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent class="w-40 p-1" align="end">
                      <Button 
                        variant="ghost" 
                        class="w-full justify-start text-sm h-9 text-destructive"
                        @click.stop="confirmDelete({ id: kb.id, type: 'base' })"
                      >
                        <Trash2 class="w-4 h-4 mr-2" />
                        删除
                      </Button>
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>

    <!-- Right Panel: Details -->
    <Card class="flex-1 flex flex-col dark:bg-slate-950 dark:border-slate-800">
      <!-- Empty State -->
      <div v-if="!activeKnowledgeBase" class="flex-1 flex items-center justify-center">
        <div class="text-center text-muted-foreground">
          <Library class="w-16 h-16 mx-auto mb-4 opacity-30" />
          <p class="text-lg font-medium mb-2">选择知识库</p>
          <p class="text-sm">从左侧列表选择一个知识库进行管理</p>
        </div>
      </div>

      <!-- Content -->
      <template v-else>
        <CardHeader class="pb-4 border-b">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <Library class="w-5 h-5 text-primary" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span v-if="!isEditMode" class="font-semibold">{{ activeKnowledgeBase.name }}</span>
                  <Input 
                    v-else 
                    v-model="editForm.name" 
                    class="h-8 w-64 font-semibold"
                    @change="hasUnsavedChanges = true"
                  />
                  <Badge :class="getStatusBadge(activeKnowledgeBase.status).class" class="text-[10px]">
                    {{ getStatusBadge(activeKnowledgeBase.status).label }}
                  </Badge>
                  <Badge v-if="hasUnsavedChanges" variant="destructive" class="flex items-center gap-1">
                    <AlertCircle class="w-3 h-3" /> 未保存
                  </Badge>
                </div>
                <p class="text-sm text-muted-foreground mt-0.5">
                  <span v-if="!isEditMode">{{ activeKnowledgeBase.description || '暂无描述' }}</span>
                  <Input 
                    v-else 
                    v-model="editForm.description" 
                    class="h-7 w-80 text-sm mt-1"
                    @change="hasUnsavedChanges = true"
                  />
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <template v-if="isEditMode">
                <Button variant="outline" @click="discardChanges">
                  <X class="w-4 h-4 mr-2" />
                  取消
                </Button>
                <Button @click="saveEdit">
                  <Check class="w-4 h-4 mr-2" />
                  保存
                </Button>
              </template>
              <template v-else>
                <Button variant="outline" @click="isEditMode = true">
                  <Edit3 class="w-4 h-4 mr-2" />
                  编辑
                </Button>
                <Button :disabled="!hasUnsavedChanges" @click="saveConfig">
                  <Save class="w-4 h-4 mr-2" />
                  保存配置
                </Button>
              </template>
            </div>
          </div>
        </CardHeader>

        <CardContent class="flex-1 p-0 flex flex-col min-h-0">
          <Tabs v-model="activeTab" class="flex-1 flex flex-col">
            <div class="px-6 pt-4 border-b">
              <TabsList class="w-full justify-start h-auto p-0 bg-transparent gap-6">
                <TabsTrigger 
                  value="info"
                  class="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-3 pt-2 font-medium"
                >
                  <FileText class="w-4 h-4 mr-2" />
                  文件管理
                </TabsTrigger>
                <TabsTrigger 
                  value="permission"
                  class="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-3 pt-2 font-medium"
                >
                  <Shield class="w-4 h-4 mr-2" />
                  权限管理
                </TabsTrigger>
                <TabsTrigger 
                  value="config"
                  class="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-3 pt-2 font-medium"
                >
                  <Settings class="w-4 h-4 mr-2" />
                  配置
                </TabsTrigger>
              </TabsList>
            </div>

            <!-- File Management Tab -->
            <TabsContent value="info" class="m-0 flex-1 flex flex-col">
              <ScrollArea class="flex-1 h-[calc(100vh-20rem)]">
                <div class="p-6">
                  <!-- Toolbar -->
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Upload class="w-4 h-4 mr-2" />
                        上传文件
                      </Button>
                      <Button variant="outline" size="sm">
                        <FolderOpen class="w-4 h-4 mr-2" />
                        新建文件夹
                      </Button>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-muted-foreground">
                      <span v-if="selectedFiles.size > 0">
                        已选择 {{ selectedFiles.size }} 项
                      </span>
                      <Button 
                        v-if="selectedFiles.size > 0" 
                        variant="ghost" 
                        size="sm"
                        @click="selectedFiles.clear()"
                      >
                        清除选择
                      </Button>
                    </div>
                  </div>

                  <!-- File Tree -->
                  <div class="border rounded-lg overflow-hidden">
                    <div class="bg-muted/50 dark:bg-slate-900 px-4 py-3 flex items-center text-sm font-medium dark:text-slate-200">
                      <Checkbox 
                        class="mr-3" 
                        :checked="selectedFiles.size === currentFiles.length && currentFiles.length > 0"
                        @update:checked="(val) => { if (val) currentFiles.forEach(f => selectedFiles.add(f.id)); else selectedFiles.clear(); }"
                      />
                      <span class="flex-1">名称</span>
                      <span class="w-24 text-right">大小</span>
                      <span class="w-32 text-center">授权</span>
                      <span class="w-16 text-center">操作</span>
                    </div>
                    
                    <div class="divide-y dark:divide-slate-800">
                      <div v-for="item in currentFiles" :key="item.id" class="dark:hover:bg-slate-900/50 transition-colors">
                        <!-- Folder -->
                        <div v-if="item.type === 'folder'" class="flex items-center px-4 py-3">
                          <Checkbox 
                            class="mr-3" 
                            :checked="selectedFiles.has(item.id)"
                            @update:checked="toggleFileSelection(item.id)"
                          />
                          <button 
                            @click="toggleFolder(item.id)"
                            class="flex items-center gap-2 flex-1 hover:text-primary transition-colors"
                          >
                            <ChevronRight 
                              class="w-4 h-4 transition-transform"
                              :class="{ 'rotate-90': expandedFolders.has(item.id) }"
                            />
                            <FolderOpen class="w-5 h-5 text-primary" />
                            <span class="font-medium">{{ item.name }}</span>
                            <Badge variant="secondary" class="text-[10px] ml-2">
                              {{ item.children?.length || 0 }} 项
                            </Badge>
                          </button>
                          <span class="w-24 text-sm text-muted-foreground">-</span>
                          <div class="w-32 flex justify-center">
                            <Popover>
                              <PopoverTrigger as-child>
                                <Button variant="ghost" size="sm" class="h-7 px-2">
                                  <Shield class="w-4 h-4 mr-1" />
                                  {{ item.authorizedRoles.length }} 角色
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent class="w-64 p-3">
                                <div class="space-y-3">
                                  <div class="text-sm font-medium">授权角色</div>
                                  <div class="space-y-2">
                                    <label 
                                      v-for="role in mockRoles" 
                                      :key="role.id"
                                      class="flex items-center gap-2 cursor-pointer"
                                    >
                                      <Checkbox 
                                        :checked="item.authorizedRoles.includes(role.id)"
                                        @update:checked="(val) => toggleFileAuthorization(item.id, 'role', role.id, val)"
                                      />
                                      <span class="text-sm">{{ role.name }}</span>
                                    </label>
                                  </div>
                                </div>
                              </PopoverContent>
                            </Popover>
                          </div>
                          <div class="w-16 flex justify-center">
                            <Popover>
                              <PopoverTrigger as-child>
                                <Button variant="ghost" size="icon" class="h-8 w-8">
                                  <MoreVertical class="w-4 h-4" />
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent class="w-40 p-1" align="end">
                                <Button variant="ghost" class="w-full justify-start text-sm h-9">
                                  <Upload class="w-4 h-4 mr-2" />
                                  上传
                                </Button>
                                <Button variant="ghost" class="w-full justify-start text-sm h-9">
                                  <FolderOpen class="w-4 h-4 mr-2" />
                                  新建子文件夹
                                </Button>
                                <Separator class="my-1" />
                                <Button 
                                  variant="ghost" 
                                  class="w-full justify-start text-sm h-9 text-destructive"
                                  @click="confirmDelete({ id: item.id, type: 'folder' })"
                                >
                                  <Trash2 class="w-4 h-4 mr-2" />
                                  删除
                                </Button>
                              </PopoverContent>
                            </Popover>
                          </div>
                        </div>

                        <!-- Folder Children -->
                        <div v-if="item.type === 'folder' && expandedFolders.has(item.id)" class="ml-8 bg-muted/30 dark:bg-slate-900/30">
                          <div 
                            v-for="child in item.children" 
                            :key="child.id"
                            class="flex items-center px-4 py-2.5 border-t dark:border-slate-800"
                          >
                            <Checkbox 
                              class="mr-3" 
                              :checked="selectedFiles.has(child.id)"
                              @update:checked="toggleFileSelection(child.id)"
                            />
                            <component :is="getFileIcon(child.type)" class="w-4 h-4 mr-2 text-muted-foreground" />
                            <span class="flex-1 text-sm">{{ child.name }}</span>
                            <span class="w-24 text-sm text-muted-foreground">{{ formatFileSize(child.size) }}</span>
                            <div class="w-32 flex justify-center">
                              <Popover>
                                <PopoverTrigger as-child>
                                  <Button variant="ghost" size="sm" class="h-7 px-2">
                                    <Shield class="w-4 h-4 mr-1" />
                                    {{ child.authorizedRoles.length + child.authorizedUsers.length }}
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent class="w-64 p-3">
                                  <div class="space-y-3">
                                    <div class="text-sm font-medium">授权角色</div>
                                    <div class="space-y-2">
                                      <label 
                                        v-for="role in mockRoles" 
                                        :key="role.id"
                                        class="flex items-center gap-2 cursor-pointer"
                                      >
                                        <Checkbox 
                                          :checked="child.authorizedRoles.includes(role.id)"
                                          @update:checked="(val) => toggleFileAuthorization(child.id, 'role', role.id, val)"
                                        />
                                        <span class="text-sm">{{ role.name }}</span>
                                      </label>
                                    </div>
                                  </div>
                                </PopoverContent>
                              </Popover>
                            </div>
                            <div class="w-16 flex justify-center">
                              <Button variant="ghost" size="icon" class="h-8 w-8">
                                <MoreVertical class="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>

                        <!-- File -->
                        <div v-else class="flex items-center px-4 py-3">
                          <Checkbox 
                            class="mr-3" 
                            :checked="selectedFiles.has(item.id)"
                            @update:checked="toggleFileSelection(item.id)"
                          />
                          <component :is="getFileIcon(item.type)" class="w-5 h-5 mr-2 text-muted-foreground" />
                          <span class="flex-1 text-sm">{{ item.name }}</span>
                          <span class="w-24 text-sm text-muted-foreground">{{ formatFileSize(item.size) }}</span>
                          <div class="w-32 flex justify-center">
                            <Popover>
                              <PopoverTrigger as-child>
                                <Button variant="ghost" size="sm" class="h-7 px-2">
                                  <Shield class="w-4 h-4 mr-1" />
                                  {{ item.authorizedRoles.length + item.authorizedUsers.length }}
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent class="w-64 p-3">
                                <div class="space-y-3">
                                  <div class="text-sm font-medium">授权角色</div>
                                  <div class="space-y-2">
                                    <label 
                                      v-for="role in mockRoles" 
                                      :key="role.id"
                                      class="flex items-center gap-2 cursor-pointer"
                                    >
                                      <Checkbox 
                                        :checked="item.authorizedRoles.includes(role.id)"
                                        @update:checked="(val) => toggleFileAuthorization(item.id, 'role', role.id, val)"
                                      />
                                      <span class="text-sm">{{ role.name }}</span>
                                    </label>
                                  </div>
                                </div>
                              </PopoverContent>
                            </Popover>
                          </div>
                          <div class="w-16 flex justify-center">
                            <Popover>
                              <PopoverTrigger as-child>
                                <Button variant="ghost" size="icon" class="h-8 w-8">
                                  <MoreVertical class="w-4 h-4" />
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent class="w-40 p-1" align="end">
                                <Button variant="ghost" class="w-full justify-start text-sm h-9">
                                  <Eye class="w-4 h-4 mr-2" />
                                  预览
                                </Button>
                                <Button variant="ghost" class="w-full justify-start text-sm h-9">
                                  <Download class="w-4 h-4 mr-2" />
                                  下载
                                </Button>
                                <Button variant="ghost" class="w-full justify-start text-sm h-9">
                                  <Copy class="w-4 h-4 mr-2" />
                                  复制
                                </Button>
                                <Separator class="my-1" />
                                <Button 
                                  variant="ghost" 
                                  class="w-full justify-start text-sm h-9 text-destructive"
                                  @click="confirmDelete({ id: item.id, type: 'file' })"
                                >
                                  <Trash2 class="w-4 h-4 mr-2" />
                                  删除
                                </Button>
                              </PopoverContent>
                            </Popover>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            <!-- Permission Management Tab -->
            <TabsContent value="permission" class="m-0 flex-1 flex flex-col">
              <ScrollArea class="flex-1 h-[calc(100vh-20rem)]">
                <div class="p-6">
                  <div class="grid grid-cols-2 gap-6">
                    <!-- Role Authorization -->
                    <Card class="dark:bg-slate-900/50 dark:border-slate-800">
                      <CardHeader class="pb-4">
                        <CardTitle class="text-base flex items-center gap-2">
                          <Users class="w-5 h-5" />
                          角色授权
                        </CardTitle>
                        <CardDescription>设置哪些角色可以访问此知识库</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div class="space-y-3">
                          <label 
                            v-for="role in mockRoles" 
                            :key="role.id"
                            class="flex items-center gap-3 p-3 rounded-lg border dark:border-slate-700 hover:bg-muted/50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                          >
                            <Checkbox 
                              :checked="false"
                              @update:checked="(val) => toggleKnowledgeBaseAuthorization('role', role.id, val)"
                            />
                            <div class="flex-1">
                              <div class="font-medium text-sm">{{ role.name }}</div>
                              <div class="text-xs text-muted-foreground">访问和管理知识库内容</div>
                            </div>
                            <Badge variant="secondary" class="text-[10px]">
                              <Check class="w-3 h-3 mr-1" />
                              已授权
                            </Badge>
                          </label>
                        </div>
                      </CardContent>
                    </Card>

                    <!-- User Authorization -->
                    <Card class="dark:bg-slate-900/50 dark:border-slate-800">
                      <CardHeader class="pb-4">
                        <CardTitle class="text-base flex items-center gap-2">
                          <Shield class="w-5 h-5" />
                          用户授权
                        </CardTitle>
                        <CardDescription>单独授权特定用户访问此知识库</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div class="space-y-3">
                          <div v-for="user in mockUsers" :key="user.id" class="flex items-center gap-3 p-3 rounded-lg border dark:border-slate-700 hover:bg-muted/50 dark:hover:bg-slate-800/50 transition-colors">
                            <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-primary text-sm font-medium">
                              {{ user.name.charAt(0) }}
                            </div>
                            <div class="flex-1">
                              <div class="font-medium text-sm">{{ user.name }}</div>
                              <div class="text-xs text-muted-foreground">ID: {{ user.id }}</div>
                            </div>
                            <Checkbox 
                              :checked="false"
                              @update:checked="(val) => toggleKnowledgeBaseAuthorization('user', user.id, val)"
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <!-- Batch Authorization -->
                  <Card class="mt-6 dark:bg-slate-900/50 dark:border-slate-800">
                    <CardHeader class="pb-4">
                      <CardTitle class="text-base flex items-center gap-2">
                        <Shield class="w-5 h-5" />
                        批量授权
                      </CardTitle>
                      <CardDescription>对知识库下的特定文件或文件夹进行授权</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div v-if="selectedFiles.size === 0" class="text-center py-8 text-muted-foreground">
                        <FileText class="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p class="text-sm">请先在"文件管理"中选择要授权的文件</p>
                      </div>
                      <div v-else class="space-y-4">
                        <div class="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                          <Check class="w-4 h-4 text-green-500" />
                          已选择 {{ selectedFiles.size }} 个文件/文件夹
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-3">
                            <Label class="text-sm font-medium">授权角色</Label>
                            <div class="space-y-2">
                              <label 
                                v-for="role in mockRoles" 
                                :key="role.id"
                                class="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-muted/50"
                              >
                                <Checkbox :checked="false" />
                                <span class="text-sm">{{ role.name }}</span>
                              </label>
                            </div>
                          </div>
                          <div class="space-y-3">
                            <Label class="text-sm font-medium">授权用户</Label>
                            <div class="space-y-2">
                              <label 
                                v-for="user in mockUsers" 
                                :key="user.id"
                                class="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-muted/50"
                              >
                                <Checkbox :checked="false" />
                                <span class="text-sm">{{ user.name }}</span>
                              </label>
                            </div>
                          </div>
                        </div>
                        <div class="flex justify-end">
                          <Button @click="hasUnsavedChanges = true">
                            <Save class="w-4 h-4 mr-2" />
                            批量保存授权
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </ScrollArea>
            </TabsContent>

            <!-- Configuration Tab -->
            <TabsContent value="config" class="m-0 flex-1 flex flex-col">
              <ScrollArea class="flex-1 h-[calc(100vh-20rem)]">
                <div class="p-6 space-y-6">
                  <!-- Retrieval Settings -->
                  <Card class="dark:bg-slate-900/50 dark:border-slate-800">
                    <CardHeader class="pb-4">
                      <CardTitle class="text-base flex items-center gap-2">
                        <Settings class="w-5 h-5" />
                        检索功能
                      </CardTitle>
                      <CardDescription>配置知识库的检索策略和功能开关</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-6">
                      <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-700">
                        <div class="space-y-0.5">
                          <Label class="text-base dark:text-slate-200">启用 RAG 检索</Label>
                          <p class="text-sm text-muted-foreground">开启基于向量的知识检索增强生成</p>
                        </div>
                        <Switch 
                          :checked="config.enableRAG" 
                          @update:checked="(val) => { config.enableRAG = val; hasUnsavedChanges = true; }" 
                        />
                      </div>

                      <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-700">
                        <div class="space-y-0.5">
                          <Label class="text-base dark:text-slate-200">启用知识图谱</Label>
                          <p class="text-sm text-muted-foreground">开启结构化知识图谱检索</p>
                        </div>
                        <Switch 
                          :checked="config.enableKG" 
                          @update:checked="(val) => { config.enableKG = val; hasUnsavedChanges = true; }" 
                        />
                      </div>

                      <Separator />

                      <div class="grid grid-cols-2 gap-6">
                        <div class="space-y-3">
                          <Label class="dark:text-slate-200">检索策略</Label>
                          <Select 
                            v-model="config.retrievalStrategy"
                            @update:modelValue="hasUnsavedChanges = true"
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectItem value="hybrid">混合检索</SelectItem>
                                <SelectItem value="vector">向量检索</SelectItem>
                                <SelectItem value="keyword">关键词检索</SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                          <p class="text-sm text-muted-foreground">
                            混合检索结合向量和关键词提供更准确的检索结果
                          </p>
                        </div>

                        <div class="space-y-3">
                          <Label class="dark:text-slate-200">Embedding 模型</Label>
                          <Select 
                            v-model="config.embeddingModel"
                            @update:modelValue="hasUnsavedChanges = true"
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectItem value="text-embedding-3-small">text-embedding-3-small</SelectItem>
                                <SelectItem value="text-embedding-3-large">text-embedding-3-large</SelectItem>
                                <SelectItem value="text-embedding-ada-002">text-embedding-ada-002</SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                          <p class="text-sm text-muted-foreground">
                            用于将文本转换为向量表示的模型
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <!-- Document Processing -->
                  <Card class="dark:bg-slate-900/50 dark:border-slate-800">
                    <CardHeader class="pb-4">
                      <CardTitle class="text-base flex items-center gap-2">
                        <FileText class="w-5 h-5" />
                        文档处理
                      </CardTitle>
                      <CardDescription>配置文档入库时的处理参数</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-6">
                      <div class="grid grid-cols-2 gap-6">
                        <div class="space-y-3">
                          <Label class="dark:text-slate-200">文档切分大小</Label>
                          <div class="flex items-center gap-4">
                            <Input 
                              v-model.number="config.chunkSize"
                              type="number"
                              class="w-32"
                              @change="hasUnsavedChanges = true"
                            />
                            <span class="text-sm text-muted-foreground">tokens</span>
                          </div>
                          <p class="text-sm text-muted-foreground">
                            单个文档块的最大token数，建议512-1024
                          </p>
                        </div>

                        <div class="space-y-3">
                          <Label class="dark:text-slate-200">最大文件大小</Label>
                          <div class="flex items-center gap-4">
                            <Input 
                              v-model.number="config.maxFileSize"
                              type="number"
                              class="w-32"
                              @change="hasUnsavedChanges = true"
                            />
                            <span class="text-sm text-muted-foreground">MB</span>
                          </div>
                          <p class="text-sm text-muted-foreground">
                            超过此大小的文件将被拒绝上传
                          </p>
                        </div>
                      </div>

                      <div class="space-y-3">
                        <Label class="dark:text-slate-200">允许的文件类型</Label>
                        <div class="flex flex-wrap gap-2">
                          <Badge 
                            v-for="type in config.allowedFileTypes" 
                            :key="type"
                            variant="outline"
                            class="px-3 py-1 cursor-pointer hover:bg-destructive/10 hover:text-destructive hover:border-destructive transition-colors"
                            @click="hasUnsavedChanges = true"
                          >
                            {{ type }}
                          </Badge>
                          <Button variant="outline" size="sm" class="h-6 px-2">
                            <Plus class="w-3 h-3 mr-1" />
                            添加
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div class="flex justify-end gap-3">
                    <Button variant="outline" @click="discardChanges" :disabled="!hasUnsavedChanges">
                      <X class="w-4 h-4 mr-2" />
                      放弃更改
                    </Button>
                    <Button @click="saveConfig" :disabled="!hasUnsavedChanges">
                      <Save class="w-4 h-4 mr-2" />
                      保存配置
                    </Button>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </template>
    </Card>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            确定要删除这个{{ itemToDelete?.type === 'base' ? '知识库' : itemToDelete?.type === 'folder' ? '文件夹' : '文件' }}吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">取消</Button>
          <Button variant="destructive" @click="handleDelete">
            <Trash2 class="w-4 h-4 mr-2" />
            删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
