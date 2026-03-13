<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[800px] h-[80vh] flex flex-col p-0 gap-0 overflow-hidden">
      <DialogHeader class="px-6 py-4 border-b flex-shrink-0">
        <DialogTitle class="text-xl">添加附件</DialogTitle>
        <DialogDescription>支持上传本地文件或从知识库中选择文档作为上下文。</DialogDescription>
      </DialogHeader>

      <Tabs :model-value="activeTab" @update:model-value="$emit('update:activeTab', $event)" class="flex-1 flex flex-col min-h-0">
        <div class="px-6 pt-2 pb-0 bg-muted/10 border-b flex-shrink-0">
          <TabsList class="w-full justify-start h-10 bg-transparent p-0 border-b border-transparent">
            <TabsTrigger 
              value="local" 
              class="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
            >
              本地文件
            </TabsTrigger>
            <TabsTrigger 
              value="knowledge" 
              class="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
            >
              知识库文档
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="local" class="flex-1 flex flex-col gap-6 p-6 min-h-0 data-[state=inactive]:hidden">
          <!-- Upload Area -->
          <div 
            class="relative border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 cursor-pointer group"
            :class="isDragOver ? 'border-primary bg-primary/5 scale-[1.01]' : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'"
            @click="triggerFileInput" 
            @drop.prevent="handleDrop" 
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
          >
            <input type="file" ref="fileInputRef" class="hidden" multiple @change="handleFileChange" />
            <div class="flex flex-col items-center gap-3">
              <div class="p-4 rounded-full bg-muted group-hover:bg-background transition-colors shadow-sm">
                <Upload class="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              <div class="space-y-1">
                <p class="text-base font-semibold text-foreground">点击或拖拽文件上传</p>
                <p class="text-xs text-muted-foreground">支持 PDF, DOCX, PPTX, XLSX, TXT (Max 50MB)</p>
              </div>
            </div>
          </div>

          <!-- File List -->
          <div class="flex-1 flex flex-col min-h-0 border rounded-lg bg-background/50">
            <div class="px-4 py-3 border-b bg-muted/20 flex justify-between items-center">
              <span class="text-sm font-medium">已选文件 ({{ localFileList.length }})</span>
              <Button v-if="localFileList.length > 0" variant="ghost" size="sm" class="h-7 text-xs text-destructive hover:bg-destructive/10" @click="localFileList.forEach(f => $emit('remove-local-file', f))">
                清空列表
              </Button>
            </div>
            <ScrollArea class="flex-1">
              <div v-if="localFileList.length === 0" class="h-full flex flex-col items-center justify-center text-muted-foreground py-10 opacity-50">
                <FileText class="w-12 h-12 mb-2" />
                <p class="text-sm">暂无本地文件</p>
              </div>
              <div v-else class="p-2 space-y-1">
                <div v-for="file in localFileList" :key="file.name" class="flex items-center justify-between p-3 hover:bg-muted/50 rounded-md group transition-colors border border-transparent hover:border-border/50">
                  <div class="flex items-center gap-3 overflow-hidden">
                    <div class="w-10 h-10 rounded bg-blue-50 flex items-center justify-center shrink-0">
                      <FileText class="w-5 h-5 text-blue-600" />
                    </div>
                    <div class="flex flex-col min-w-0">
                      <span class="text-sm font-medium truncate">{{ file.name }}</span>
                      <span class="text-xs text-muted-foreground">{{ formatFileSize(file.size) }}</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity" @click="$emit('remove-local-file', file)">
                    <Trash2 class="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </ScrollArea>
          </div>
        </TabsContent>

        <TabsContent value="knowledge" class="flex-1 flex flex-col min-h-0 p-0 data-[state=inactive]:hidden">
          <!-- Toolbar -->
          <div class="flex flex-col gap-3 px-6 py-4 border-b bg-background/50">
            <div class="flex gap-3">
              <div class="relative flex-1">
                <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  :model-value="knowledgeSearchKeyword" 
                  @update:model-value="$emit('update:knowledgeSearchKeyword', $event)" 
                  placeholder="搜索文档名称..." 
                  class="pl-9 bg-background" 
                />
              </div>
              <Select v-model="filterType">
                <SelectTrigger class="w-[140px]">
                  <SelectValue placeholder="文件类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有类型</SelectItem>
                  <SelectItem value="pdf">PDF 文档</SelectItem>
                  <SelectItem value="docx">Word 文档</SelectItem>
                  <SelectItem value="txt">文本文件</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon" :disabled="knowledgeLoading" @click="$emit('refresh-knowledge')" title="刷新">
                <RefreshCw :class="['w-4 h-4', knowledgeLoading ? 'animate-spin' : '']" />
              </Button>
            </div>
          </div>

          <!-- Table Area -->
          <div class="flex-1 min-h-0 relative">
            <ScrollArea class="h-full">
              <Table>
                <TableHeader class="sticky top-0 bg-background z-10 shadow-sm">
                  <TableRow>
                    <TableHead class="w-[50px] text-center">
                      <Checkbox 
                        :checked="isAllSelected"
                        @update:checked="toggleSelectAll"
                      />
                    </TableHead>
                    <TableHead class="cursor-pointer hover:text-primary transition-colors" @click="toggleSort('filename')">
                      文档名称
                      <ArrowUpDown class="inline w-3 h-3 ml-1 opacity-50" />
                    </TableHead>
                    <TableHead class="w-[100px] cursor-pointer hover:text-primary transition-colors" @click="toggleSort('file_size')">
                      大小
                      <ArrowUpDown class="inline w-3 h-3 ml-1 opacity-50" />
                    </TableHead>
                    <TableHead class="w-[150px] text-right cursor-pointer hover:text-primary transition-colors" @click="toggleSort('updated_at')">
                      修改时间
                      <ArrowUpDown class="inline w-3 h-3 ml-1 opacity-50" />
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <template v-if="knowledgeLoading">
                     <TableRow v-for="i in 5" :key="i">
                       <TableCell><Skeleton class="h-4 w-4 rounded" /></TableCell>
                       <TableCell><Skeleton class="h-4 w-[200px]" /></TableCell>
                       <TableCell><Skeleton class="h-4 w-[60px]" /></TableCell>
                       <TableCell><Skeleton class="h-4 w-[100px] ml-auto" /></TableCell>
                     </TableRow>
                  </template>
                  <template v-else-if="paginatedDocs.length > 0">
                    <TableRow 
                      v-for="doc in paginatedDocs" 
                      :key="doc.id"
                      class="cursor-pointer hover:bg-muted/50"
                      :data-state="selectedKnowledgeRowKeys.includes(doc.id) ? 'selected' : ''"
                      @click="toggleRow(doc.id)"
                    >
                      <TableCell class="text-center" @click.stop>
                         <Checkbox 
                           :checked="selectedKnowledgeRowKeys.includes(doc.id)"
                           @update:checked="(val) => toggleRow(doc.id)"
                         />
                      </TableCell>
                      <TableCell>
                        <div class="flex items-center gap-2">
                          <FileText class="w-4 h-4 text-muted-foreground" />
                          <span class="font-medium truncate max-w-[300px]" :title="doc.filename">{{ doc.filename }}</span>
                        </div>
                      </TableCell>
                      <TableCell class="text-muted-foreground text-xs">{{ formatFileSize(doc.file_size) }}</TableCell>
                      <TableCell class="text-right text-muted-foreground text-xs font-mono">{{ formatDate(doc.updated_at) }}</TableCell>
                    </TableRow>
                  </template>
                  <template v-else>
                    <TableRow>
                      <TableCell colspan="4" class="h-[300px] text-center">
                        <div class="flex flex-col items-center justify-center text-muted-foreground opacity-50">
                          <SearchX class="w-12 h-12 mb-2" />
                          <p>未找到相关文档</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  </template>
                </TableBody>
              </Table>
            </ScrollArea>
          </div>

          <!-- Pagination -->
          <div class="px-6 py-3 border-t bg-muted/10 flex items-center justify-between flex-shrink-0">
            <span class="text-xs text-muted-foreground">
              共 {{ sortedDocs.length }} 项，当前 {{ currentPage }} / {{ totalPages }} 页
            </span>
            <div class="flex items-center gap-2">
              <Button variant="outline" size="sm" :disabled="currentPage === 1" @click="currentPage--">上一页</Button>
              <Button variant="outline" size="sm" :disabled="currentPage === totalPages" @click="currentPage++">下一页</Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <DialogFooter class="px-6 py-4 border-t bg-background flex-shrink-0 flex justify-between items-center sm:justify-between">
        <div class="flex items-center gap-2 text-sm text-muted-foreground">
          <span v-if="totalSelected > 0" class="flex items-center gap-2 text-primary font-medium animate-in fade-in slide-in-from-bottom-2">
            <Badge variant="default" class="rounded-full px-2">{{ totalSelected }}</Badge>
            已选择 {{ totalSelected }} 个文件
          </span>
          <span v-else>请选择文件</span>
        </div>
        <div class="flex gap-3">
          <Button variant="outline" @click="$emit('update:open', false)">取消</Button>
          <Button @click="$emit('confirm')" :disabled="totalSelected === 0">确认添加</Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Upload, Paperclip, Trash2, Search, Loader2, FileText, RefreshCw, ArrowUpDown, SearchX } from 'lucide-vue-next';
import type { KnowledgeDoc } from '../../types';

const props = defineProps<{
  open: boolean;
  activeTab: string;
  localFileList: File[];
  knowledgeDocs: KnowledgeDoc[];
  filteredKnowledgeDocs: KnowledgeDoc[]; // Keyword filtered from parent
  selectedKnowledgeRowKeys: string[];
  knowledgeSearchKeyword: string;
  knowledgeLoading: boolean;
}>();

const emit = defineEmits([
  'update:open',
  'update:activeTab',
  'update:knowledgeSearchKeyword',
  'file-change',
  'remove-local-file',
  'refresh-knowledge',
  'toggle-knowledge-selection',
  'confirm'
]);

// --- Local Upload Logic ---
const fileInputRef = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    emit('file-change', Array.from(target.files));
    target.value = '';
  }
};

const handleDrop = (e: DragEvent) => {
  isDragOver.value = false;
  if (e.dataTransfer?.files) {
    emit('file-change', Array.from(e.dataTransfer.files));
  }
};

// --- Knowledge Table Logic ---
const filterType = ref('all');
const sortKey = ref('updated_at');
const sortOrder = ref<'asc' | 'desc'>('desc');
const currentPage = ref(1);
const pageSize = 10;

// Reset page on filter change
watch([() => props.knowledgeSearchKeyword, filterType], () => {
  currentPage.value = 1;
});

const sortedDocs = computed(() => {
  let docs = [...props.filteredKnowledgeDocs];

  // Filter Type
  if (filterType.value !== 'all') {
    docs = docs.filter(d => d.filename.toLowerCase().endsWith(`.${filterType.value}`));
  }

  // Sort
  docs.sort((a, b) => {
    let valA = a[sortKey.value as keyof KnowledgeDoc];
    let valB = b[sortKey.value as keyof KnowledgeDoc];
    
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });

  return docs;
});

const totalPages = computed(() => Math.ceil(sortedDocs.value.length / pageSize) || 1);

const paginatedDocs = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return sortedDocs.value.slice(start, start + pageSize);
});

const toggleSort = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'desc'; // Default desc for new key
  }
};

const toggleRow = (id: string) => {
  const isSelected = props.selectedKnowledgeRowKeys.includes(id);
  emit('toggle-knowledge-selection', id, !isSelected);
};

const isAllSelected = computed(() => {
  if (paginatedDocs.value.length === 0) return false;
  return paginatedDocs.value.every(d => props.selectedKnowledgeRowKeys.includes(d.id));
});

const toggleSelectAll = (checked: boolean) => {
  paginatedDocs.value.forEach(doc => {
    const isSelected = props.selectedKnowledgeRowKeys.includes(doc.id);
    if (checked && !isSelected) {
      emit('toggle-knowledge-selection', doc.id, true);
    } else if (!checked && isSelected) {
      emit('toggle-knowledge-selection', doc.id, false);
    }
  });
};

// --- Helpers ---
const totalSelected = computed(() => props.localFileList.length + props.selectedKnowledgeRowKeys.length);

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleDateString();
  } catch {
    return dateStr;
  }
};
</script>
