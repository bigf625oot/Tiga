<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
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
  ChevronRight, MoreVertical, Upload, Download, Copy, Eye, Loader2
} from 'lucide-vue-next';
import { knowledgeBaseService } from '../services/knowledgeBaseService';
import type { KnowledgeBase, KnowledgeFile, KnowledgeBaseConfig, KnowledgeBasePermission } from '../api';

const { toast } = useToast();

interface Role {
  id: string;
  name: string;
}

interface User {
  id: string;
  name: string;
  avatar?: string;
}

const knowledgeBases = ref<KnowledgeBase[]>([]);
const activeKnowledgeBaseId = ref<string | null>(null);
const activeTab = ref('info');
const searchQuery = ref('');
const hasUnsavedChanges = ref(false);
const isLoading = ref(false);
const filesLoading = ref(false);

const roles = ref<Role[]>([]);
const users = ref<User[]>([]);

const config = reactive<KnowledgeBaseConfig>({
  enable_rag: true,
  enable_kg: true,
  chunk_size: 512,
  embedding_model: 'text-embedding-3-small',
  retrieval_strategy: 'hybrid',
  max_file_size: 100,
  allowed_file_types: ['.pdf', '.docx', '.txt', '.md'],
});

const kbPermissions = reactive<KnowledgeBasePermission>({
  roles: [],
  users: [],
});

const isAddDialogOpen = ref(false);
const isDeleteDialogOpen = ref(false);
const isRenameDialogOpen = ref(false);
const isEditMode = ref(false);
const editingFileId = ref<string | null>(null);
const itemToDelete = ref<{ id: string; type: 'base' | 'file' | 'folder' } | null>(null);
const renamingFileId = ref<string | null>(null);
const renameLoading = ref(false);

const renameForm = reactive({
  name: '',
});

watch(isRenameDialogOpen, (open) => {
  if (!open) {
    renamingFileId.value = null;
    renameForm.name = '';
  }
});

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

const expandedFolders = ref<Set<string>>(new Set());
const selectedFiles = ref<Set<string>>(new Set());
const currentFiles = ref<KnowledgeFile[]>([]);

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

const fetchKnowledgeBases = async () => {
  isLoading.value = true;
  try {
    knowledgeBases.value = await knowledgeBaseService.getKnowledgeBases();
  } catch (error) {
    toast({
      title: '加载失败',
      description: '知识库列表加载失败',
      variant: 'destructive',
    });
  } finally {
    isLoading.value = false;
  }
};

const fetchFiles = async (kbId: string) => {
  filesLoading.value = true;
  try {
    currentFiles.value = await knowledgeBaseService.getFiles(kbId);
    expandedFolders.value.clear();
    currentFiles.value.forEach(f => {
      if (f.type === 'folder') {
        expandedFolders.value.add(f.id);
      }
    });
  } catch (error) {
    toast({
      title: '加载失败',
      description: '文件列表加载失败',
      variant: 'destructive',
    });
  } finally {
    filesLoading.value = false;
  }
};

const fetchConfig = async (kbId: string) => {
  try {
    const data = await knowledgeBaseService.getConfig(kbId);
    Object.assign(config, data);
  } catch (error) {
    console.error('Failed to load config');
  }
};

const fetchPermissions = async (kbId: string) => {
  try {
    const data = await knowledgeBaseService.getPermissions(kbId);
    Object.assign(kbPermissions, data);
  } catch (error) {
    console.error('Failed to load permissions');
  }
};

onMounted(async () => {
  await fetchKnowledgeBases();
  try {
    const [rolesData, usersData] = await Promise.all([
      fetch('/api/v1/users/roles').then(r => r.json()),
      fetch('/api/v1/users?page_size=100').then(r => r.json()),
    ]);
    roles.value = rolesData;
    users.value = usersData.items || [];
  } catch (error) {
    console.error('Failed to load roles/users');
  }
});

watch(activeKnowledgeBaseId, async (newId) => {
  if (newId) {
    await Promise.all([
      fetchFiles(newId),
      fetchConfig(newId),
      fetchPermissions(newId),
    ]);
  }
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

const saveEdit = async () => {
  if (!editForm.name.trim()) {
    toast({
      title: '验证失败',
      description: '知识库名称不能为空',
      variant: 'destructive',
    });
    return;
  }

  try {
    const updated = await knowledgeBaseService.updateKnowledgeBase(activeKnowledgeBaseId.value!, {
      name: editForm.name,
      description: editForm.description,
      status: editForm.status,
    });
    const index = knowledgeBases.value.findIndex(k => k.id === activeKnowledgeBaseId.value);
    if (index !== -1) {
      knowledgeBases.value[index] = updated;
    }
    hasUnsavedChanges.value = false;
    isEditMode.value = false;
    toast({
      title: '保存成功',
      description: '知识库信息已更新',
    });
  } catch (error) {
    toast({
      title: '保存失败',
      description: '知识库信息更新失败',
      variant: 'destructive',
    });
  }
};

const handleAddKnowledgeBase = async () => {
  if (!newKnowledgeBase.name.trim()) {
    toast({
      title: '验证失败',
      description: '知识库名称不能为空',
      variant: 'destructive',
    });
    return;
  }

  try {
    const newKB = await knowledgeBaseService.createKnowledgeBase({
      name: newKnowledgeBase.name,
      description: newKnowledgeBase.description,
      status: newKnowledgeBase.status,
    });

    knowledgeBases.value.unshift(newKB);
    activeKnowledgeBaseId.value = newKB.id;

    Object.assign(newKnowledgeBase, { name: '', description: '', status: 'active' });
    isAddDialogOpen.value = false;

    toast({
      title: '创建成功',
      description: `知识库"${newKB.name}"已创建`,
    });
  } catch (error) {
    toast({
      title: '创建失败',
      description: '知识库创建失败',
      variant: 'destructive',
    });
  }
};

const confirmDelete = (item: { id: string; type: 'base' | 'file' | 'folder' }) => {
  itemToDelete.value = item;
  isDeleteDialogOpen.value = true;
};

const openRenameDialog = (fileId: string) => {
  const file = findFileById(fileId);
  if (!file || file.type !== 'folder') return;
  renamingFileId.value = fileId;
  renameForm.name = file.name;
  isRenameDialogOpen.value = true;
};

const handleRename = async () => {
  if (!activeKnowledgeBaseId.value || !renamingFileId.value) return;
  const name = renameForm.name.trim();
  if (!name) {
    toast({
      title: '验证失败',
      description: '文件夹名称不能为空',
      variant: 'destructive',
    });
    return;
  }

  const file = findFileById(renamingFileId.value);
  if (file && file.name === name) {
    isRenameDialogOpen.value = false;
    renamingFileId.value = null;
    return;
  }

  renameLoading.value = true;
  try {
    const updated = await knowledgeBaseService.renameFile(activeKnowledgeBaseId.value, renamingFileId.value, name);
    const target = findFileById(updated.id);
    if (target) target.name = updated.name;
    toast({ title: '重命名成功' });
    isRenameDialogOpen.value = false;
    renamingFileId.value = null;
  } catch (error) {
    toast({
      title: '重命名失败',
      description: '文件夹重命名失败',
      variant: 'destructive',
    });
  } finally {
    renameLoading.value = false;
  }
};

const handleDelete = async () => {
  if (!itemToDelete.value) return;

  try {
    if (itemToDelete.value.type === 'base') {
      await knowledgeBaseService.deleteKnowledgeBase(itemToDelete.value.id);
      const kb = knowledgeBases.value.find(k => k.id === itemToDelete.value!.id);
      knowledgeBases.value = knowledgeBases.value.filter(k => k.id !== itemToDelete.value!.id);
      if (activeKnowledgeBaseId.value === itemToDelete.value.id) {
        activeKnowledgeBaseId.value = knowledgeBases.value[0]?.id || null;
      }
      toast({
        title: '删除成功',
        description: `知识库"${kb?.name}"已删除`,
      });
    } else if (itemToDelete.value.type === 'file' || itemToDelete.value.type === 'folder') {
      await knowledgeBaseService.deleteFile(activeKnowledgeBaseId.value!, itemToDelete.value.id);
      await fetchFiles(activeKnowledgeBaseId.value!);
      toast({
        title: '删除成功',
        description: `${itemToDelete.value.type === 'folder' ? '文件夹' : '文件'}已删除`,
      });
    }
  } catch (error) {
    toast({
      title: '删除失败',
      description: '删除操作失败',
      variant: 'destructive',
    });
  }

  itemToDelete.value = null;
  isDeleteDialogOpen.value = false;
};

const saveConfig = async () => {
  if (!activeKnowledgeBaseId.value) return;

  try {
    await knowledgeBaseService.updateConfig(activeKnowledgeBaseId.value, { ...config });
    await knowledgeBaseService.updatePermissions(activeKnowledgeBaseId.value, { ...kbPermissions });
    toast({
      title: '保存成功',
      description: '知识库配置已更新',
    });
    hasUnsavedChanges.value = false;
  } catch (error) {
    toast({
      title: '保存失败',
      description: '配置保存失败',
      variant: 'destructive',
    });
  }
};

const discardChanges = () => {
  hasUnsavedChanges.value = false;
  if (activeKnowledgeBaseId.value) {
    fetchConfig(activeKnowledgeBaseId.value);
    fetchPermissions(activeKnowledgeBaseId.value);
  }
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

const toggleFileAuthorization = async (fileId: string, type: 'role' | 'user', id: string, authorized: boolean) => {
  const file = findFileById(fileId);
  if (!file) return;

  if (type === 'role') {
    if (authorized) {
      file.authorized_roles = file.authorized_roles.filter(r => r !== id);
    } else {
      file.authorized_roles.push(id);
    }
  } else {
    if (authorized) {
      file.authorized_users = file.authorized_users.filter(u => u !== id);
    } else {
      file.authorized_users.push(id);
    }
  }

  try {
    await knowledgeBaseService.updateFile(activeKnowledgeBaseId.value!, fileId, {
      authorized_roles: file.authorized_roles,
      authorized_users: file.authorized_users,
    });
  } catch (error) {
    toast({
      title: '授权失败',
      description: '文件授权更新失败',
      variant: 'destructive',
    });
  }
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
  if (type === 'role') {
    if (authorized) {
      kbPermissions.roles = kbPermissions.roles.filter(r => r !== id);
    } else {
      kbPermissions.roles.push(id);
    }
  } else {
    if (authorized) {
      kbPermissions.users = kbPermissions.users.filter(u => u !== id);
    } else {
      kbPermissions.users.push(id);
    }
  }
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

const handleCreateFolder = async () => {
  if (!activeKnowledgeBaseId.value) return;
  try {
    const created = await knowledgeBaseService.createFolder(activeKnowledgeBaseId.value, '新建文件夹');
    await fetchFiles(activeKnowledgeBaseId.value);
    toast({ title: '文件夹创建成功' });
    openRenameDialog(created.id);
  } catch (error) {
    toast({ title: '文件夹创建失败', variant: 'destructive' });
  }
};

const handleCreateSubFolder = async (parentId: string) => {
  if (!activeKnowledgeBaseId.value) return;
  try {
    const created = await knowledgeBaseService.createFolder(activeKnowledgeBaseId.value, '新建子文件夹', parentId);
    await fetchFiles(activeKnowledgeBaseId.value);
    expandedFolders.value.add(parentId);
    toast({ title: '子文件夹创建成功' });
    openRenameDialog(created.id);
  } catch (error) {
    toast({ title: '子文件夹创建失败', variant: 'destructive' });
  }
};

const handleUploadFile = async (parentId?: string) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = config.allowed_file_types.join(',');
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file && activeKnowledgeBaseId.value) {
      try {
        await knowledgeBaseService.uploadFile(activeKnowledgeBaseId.value, file, parentId);
        await fetchFiles(activeKnowledgeBaseId.value);
        if (parentId) {
          expandedFolders.value.add(parentId);
        }
        toast({ title: '文件上传成功' });
      } catch (error) {
        toast({ title: '文件上传失败', variant: 'destructive' });
      }
    }
  };
  input.click();
};
</script>

<template>
  <div class="flex h-full min-h-[600px] gap-6">
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
            <div v-if="isLoading" class="flex items-center justify-center h-[calc(100vh-20rem)]">
              <Loader2 class="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
            <div v-else-if="filteredKnowledgeBases.length === 0" class="flex flex-col items-center justify-center h-[calc(100vh-20rem)] text-muted-foreground">
              <img src="/public/Placeholder/null_file.svg" class="w-12 h-12 mb-3 opacity-50" />
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
                      {{ kb.folder_count }}
                    </span>
                    <span class="flex items-center gap-1">
                      <FileText class="w-3 h-3" />
                      {{ kb.file_count }}
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

    <Card class="flex-1 flex flex-col dark:bg-slate-950 dark:border-slate-800">
      <div v-if="!activeKnowledgeBase" class="flex-1 flex items-center justify-center">
        <div class="text-center text-muted-foreground">
          <img src="/public/Placeholder/null_file.svg" class="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p class="text-lg font-medium mb-2">选择知识库</p>
          <p class="text-sm">从左侧列表选择一个知识库进行管理</p>
        </div>
      </div>

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

            <TabsContent value="info" class="m-0 flex-1 flex flex-col">
              <ScrollArea class="flex-1 h-[calc(100vh-20rem)]">
                <div class="p-6">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2">
                      <Button variant="outline" size="sm" @click="handleUploadFile">
                        <Upload class="w-4 h-4 mr-2" />
                        上传文件
                      </Button>
                      <Button variant="outline" size="sm" @click="handleCreateFolder">
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

                  <div v-if="filesLoading" class="flex items-center justify-center py-8">
                    <Loader2 class="w-6 h-6 animate-spin text-muted-foreground" />
                  </div>
                  <div v-else-if="currentFiles.length === 0" class="text-center py-8 text-muted-foreground">
                    <FileText class="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p class="text-sm">暂无文件</p>
                  </div>
                  <div v-else class="border rounded-lg overflow-hidden">
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
                            <span class="text-sm font-medium">{{ item.name }}</span>
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
                                  {{ item.authorized_roles.length }} 角色
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent class="w-64 p-3">
                                <div class="space-y-3">
                                  <div class="text-sm font-medium">授权角色</div>
                                  <div class="space-y-2">
                                    <label
                                      v-for="role in roles"
                                      :key="role.id"
                                      class="flex items-center gap-2 cursor-pointer"
                                    >
                                      <Checkbox
                                        :checked="item.authorized_roles.includes(role.id)"
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
                                <Button variant="ghost" class="w-full justify-start text-sm h-9" @click="handleUploadFile(item.id)">
                                  <Upload class="w-4 h-4 mr-2" />
                                  上传
                                </Button>
                                <Button variant="ghost" class="w-full justify-start text-sm h-9" @click="handleCreateSubFolder(item.id)">
                                  <FolderOpen class="w-4 h-4 mr-2" />
                                  新建子文件夹
                                </Button>
                                <Button variant="ghost" class="w-full justify-start text-sm h-9" @click="openRenameDialog(item.id)">
                                  <Edit3 class="w-4 h-4 mr-2" />
                                  重命名
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
                                    {{ child.authorized_roles.length + child.authorized_users.length }}
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent class="w-64 p-3">
                                  <div class="space-y-3">
                                    <div class="text-sm font-medium">授权角色</div>
                                    <div class="space-y-2">
                                      <label
                                        v-for="role in roles"
                                        :key="role.id"
                                        class="flex items-center gap-2 cursor-pointer"
                                      >
                                        <Checkbox
                                          :checked="child.authorized_roles.includes(role.id)"
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
                              <Popover>
                                <PopoverTrigger as-child>
                                  <Button variant="ghost" size="icon" class="h-8 w-8">
                                    <MoreVertical class="w-4 h-4" />
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent class="w-40 p-1" align="end">
                                  <template v-if="child.type === 'folder'">
                                    <Button variant="ghost" class="w-full justify-start text-sm h-9" @click="openRenameDialog(child.id)">
                                      <Edit3 class="w-4 h-4 mr-2" />
                                      重命名
                                    </Button>
                                    <Separator class="my-1" />
                                  </template>
                                  <Button
                                    variant="ghost"
                                    class="w-full justify-start text-sm h-9 text-destructive"
                                    @click="confirmDelete({ id: child.id, type: child.type as 'file' | 'folder' })"
                                  >
                                    <Trash2 class="w-4 h-4 mr-2" />
                                    删除
                                  </Button>
                                </PopoverContent>
                              </Popover>
                            </div>
                          </div>
                        </div>

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
                                  {{ item.authorized_roles.length + item.authorized_users.length }}
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent class="w-64 p-3">
                                <div class="space-y-3">
                                  <div class="text-sm font-medium">授权角色</div>
                                  <div class="space-y-2">
                                    <label
                                      v-for="role in roles"
                                      :key="role.id"
                                      class="flex items-center gap-2 cursor-pointer"
                                    >
                                      <Checkbox
                                        :checked="item.authorized_roles.includes(role.id)"
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

            <TabsContent value="permission" class="m-0 flex-1 flex flex-col">
              <ScrollArea class="flex-1 h-[calc(100vh-20rem)]">
                <div class="p-6">
                  <div class="grid grid-cols-2 gap-6">
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
                            v-for="role in roles"
                            :key="role.id"
                            class="flex items-center gap-3 p-3 rounded-lg border dark:border-slate-700 hover:bg-muted/50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                          >
                            <Checkbox
                              :checked="kbPermissions.roles.includes(role.id)"
                              @update:checked="(val) => toggleKnowledgeBaseAuthorization('role', role.id, val)"
                            />
                            <div class="flex-1">
                              <div class="font-medium text-sm">{{ role.name }}</div>
                              <div class="text-xs text-muted-foreground">访问和管理知识库内容</div>
                            </div>
                            <Badge v-if="kbPermissions.roles.includes(role.id)" variant="secondary" class="text-[10px]">
                              <Check class="w-3 h-3 mr-1" />
                              已授权
                            </Badge>
                          </label>
                        </div>
                      </CardContent>
                    </Card>

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
                          <div v-for="user in users" :key="user.id" class="flex items-center gap-3 p-3 rounded-lg border dark:border-slate-700 hover:bg-muted/50 dark:hover:bg-slate-800/50 transition-colors">
                            <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-primary text-sm font-medium">
                              {{ user.name.charAt(0) }}
                            </div>
                            <div class="flex-1">
                              <div class="font-medium text-sm">{{ user.name }}</div>
                              <div class="text-xs text-muted-foreground">ID: {{ user.id }}</div>
                            </div>
                            <Checkbox
                              :checked="kbPermissions.users.includes(user.id)"
                              @update:checked="(val) => toggleKnowledgeBaseAuthorization('user', user.id, val)"
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

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
                                v-for="role in roles"
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
                                v-for="user in users"
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

            <TabsContent value="config" class="m-0 flex-1 flex flex-col">
              <ScrollArea class="flex-1 h-[calc(100vh-20rem)]">
                <div class="p-6 space-y-6">
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
                          :checked="config.enable_rag"
                          @update:checked="(val) => { config.enable_rag = val; hasUnsavedChanges = true; }"
                        />
                      </div>

                      <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-700">
                        <div class="space-y-0.5">
                          <Label class="text-base dark:text-slate-200">启用知识图谱</Label>
                          <p class="text-sm text-muted-foreground">开启结构化知识图谱检索</p>
                        </div>
                        <Switch
                          :checked="config.enable_kg"
                          @update:checked="(val) => { config.enable_kg = val; hasUnsavedChanges = true; }"
                        />
                      </div>

                      <Separator />

                      <div class="grid grid-cols-2 gap-6">
                        <div class="space-y-3">
                          <Label class="dark:text-slate-200">检索策略</Label>
                          <Select
                            v-model="config.retrieval_strategy"
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
                            v-model="config.embedding_model"
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
                              v-model.number="config.chunk_size"
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
                              v-model.number="config.max_file_size"
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
                            v-for="type in config.allowed_file_types"
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

    <Dialog v-model:open="isRenameDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>重命名文件夹</DialogTitle>
          <DialogDescription>请输入新的文件夹名称。</DialogDescription>
        </DialogHeader>
        <div class="space-y-2 py-4">
          <Label>文件夹名称</Label>
          <Input v-model="renameForm.name" placeholder="例如：产品文档" />
        </div>
        <DialogFooter>
          <Button variant="outline" :disabled="renameLoading" @click="isRenameDialogOpen = false">取消</Button>
          <Button :disabled="renameLoading || !renameForm.name.trim()" @click="handleRename">
            <Loader2 v-if="renameLoading" class="w-4 h-4 mr-2 animate-spin" />
            确认
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
