<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[600px] h-[60vh] flex flex-col p-0 gap-0 overflow-hidden">
      <!-- Hidden Inputs (Moved to top level to ensure availability) -->
      <input 
        type="file" 
        ref="fileInputRef" 
        class="hidden" 
        multiple 
        accept=".pdf,.docx,.pptx,.xlsx,.txt,.zip,.rar,.7z,.tar"
        @change="handleFileChange" 
      />
      <input 
        type="file" 
        ref="folderInputRef" 
        class="hidden" 
        webkitdirectory 
        directory 
        multiple 
        @change="handleFolderChange" 
      />
      <input 
        type="file" 
        ref="archiveInputRef" 
        class="hidden" 
        multiple 
        accept=".zip,.rar,.7z,.tar"
        @change="handleFileChange" 
      />

      <DialogHeader class="px-4 py-3 border-b bg-muted/20 flex-shrink-0 !flex-row !items-center !justify-between !space-y-0">
        <div class="flex items-center gap-3">
          <DialogTitle class="text-base">添加附件</DialogTitle>
          <div class="h-3 w-px bg-border"></div>
          <DialogDescription class="!text-xs m-0">支持上传本地文件或从知识库中选择。</DialogDescription>
        </div>
      </DialogHeader>

      <Tabs :model-value="activeTab" @update:model-value="$emit('update:activeTab', $event)" class="flex-1 flex flex-col min-h-0">
        <div class="px-4 pt-1 pb-0 bg-muted/10 border-b flex-shrink-0">
          <TabsList class="w-full justify-start h-9 bg-transparent p-0 border-b border-transparent">
            <TabsTrigger 
              value="local" 
              class="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-3 py-1.5 text-xs"
            >
              本地文件
            </TabsTrigger>
            <TabsTrigger 
              value="knowledge" 
              class="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-3 py-1.5 text-xs"
            >
              知识库文档
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="local" class="flex-1 flex flex-col gap-4 p-4 min-h-0 data-[state=inactive]:hidden">
          <TooltipProvider>
            <!-- Upload Area -->
            <div 
              class="relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 cursor-pointer group"
              :class="[
                isDragOver 
                  ? 'border-primary bg-primary/5 scale-[1.01]' 
                  : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'
              ]"
              @click="triggerFileInput" 
              @drop.prevent="handleDrop" 
              @dragover.prevent="isDragOver = true"
              @dragleave.prevent="isDragOver = false"
            >
              <div class="flex flex-col items-center gap-2">
                <div class="flex items-center gap-4">
                  <div class="p-2.5 rounded-full bg-muted group-hover:bg-background transition-colors shadow-sm relative group/icon hover:bg-primary/10" title="上传文件">
                    <Upload class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  <div class="h-8 w-px bg-border/50"></div>
                  <div class="p-2.5 rounded-full bg-muted group-hover:bg-background transition-colors shadow-sm relative group/icon hover:bg-primary/10" title="上传文件夹" @click.stop="triggerFolderInput">
                    <FolderUp class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  <div class="h-8 w-px bg-border/50"></div>
                  <div class="p-2.5 rounded-full bg-muted group-hover:bg-background transition-colors shadow-sm relative group/icon hover:bg-primary/10" title="上传压缩包" @click.stop="triggerArchiveInput">
                    <FileArchive class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                </div>
                <div class="space-y-0.5 mt-2">
                  <p class="text-sm font-semibold text-foreground">点击上传文件，或点击文件夹/压缩包图标</p>
                  <p class="text-[10px] text-muted-foreground">支持 PDF, DOCX, PPTX, XLSX, TXT, ZIP, RAR, 7Z, TAR (Max 50MB)</p>
                  <p class="text-[9px] text-primary/70" v-if="isProcessing">正在处理文件，请稍候...</p>
                </div>
              </div>
            </div>

            <!-- File List -->
            <div 
              v-if="localFileList.length === 0" 
              class="flex-1 flex flex-col items-center justify-center min-h-0 border rounded-lg bg-background/50 border-dashed p-4 text-center group"
            >
              <div class="relative w-16 h-16 mb-2 flex items-center justify-center">
                <!-- 背景光晕 -->
                <div class="absolute inset-0 bg-primary/5 rounded-full blur-xl group-hover:bg-primary/10 transition-colors duration-500"></div>
                
                <!-- 图标容器 -->
                <div class="relative w-14 h-14 bg-muted/30 rounded-full border-2 border-dashed border-muted-foreground/20 flex items-center justify-center group-hover:border-primary/30 transition-colors duration-300">
                  <!-- 后面的文件图标 -->
                  <FileIcon class="w-5 h-5 text-muted-foreground/40 absolute -translate-x-2 -translate-y-1 transform -rotate-12 transition-transform duration-500 group-hover:-translate-y-2 group-hover:-rotate-[15deg]" />
                  
                  <!-- 前面的上传文件图标 -->
                  <FileUp class="w-7 h-7 text-primary/80 relative z-10 translate-x-0.5 translate-y-0.5 shadow-sm transition-all duration-500 group-hover:scale-110 group-hover:text-primary group-hover:-translate-y-0.5" />
                </div>
              </div>
              <h3 class="text-sm font-medium mb-1">暂无本地文件</h3>
              <p class="text-xs text-muted-foreground max-w-[200px] mx-auto">
                请在上方点击或拖拽上传文件
              </p>
            </div>
            <div v-else class="flex-1 flex flex-col min-h-0 border rounded-lg bg-background/50">
              <div class="px-3 py-2 border-b bg-muted/20 flex justify-between items-center">
                <span class="text-xs font-medium">已选文件 ({{ localFileList.length }})</span>
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button 
                      v-if="localFileList.length > 0" 
                      variant="ghost" 
                      size="sm" 
                      class="h-6 px-2 text-[10px] text-destructive hover:bg-destructive/10 hover:text-destructive" 
                      @click="localFileList.forEach(f => $emit('remove-local-file', f))"
                    >
                      清空
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>清空所有已选文件</TooltipContent>
                </Tooltip>
              </div>
              <ScrollArea class="flex-1">
                <div class="p-1.5 space-y-1">
                  <div 
                    v-for="file in localFileList" 
                    :key="file.name" 
                    class="flex items-center justify-between p-2 hover:bg-muted/50 rounded-md group transition-colors border border-transparent hover:border-border/50"
                  >
                    <div class="flex items-center gap-2 overflow-hidden">
                      <div class="w-8 h-8 rounded bg-blue-50 flex items-center justify-center shrink-0">
                        <component :is="getFileIcon(file.name)" class="w-4 h-4 text-blue-600" />
                      </div>
                      <div class="flex flex-col min-w-0">
                        <span class="text-xs font-medium truncate" :title="file.name">{{ file.name }}</span>
                        <span class="text-[10px] text-muted-foreground">{{ formatFileSize(file.size) }}</span>
                      </div>
                    </div>
                    <Tooltip>
                      <TooltipTrigger as-child>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          class="h-6 w-6 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity" 
                          @click="$emit('remove-local-file', file)"
                        >
                          <Trash2 class="w-3 h-3" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>移除文件</TooltipContent>
                    </Tooltip>
                  </div>
                </div>
              </ScrollArea>
            </div>
          </TooltipProvider>
        </TabsContent>

        <TabsContent value="knowledge" class="flex-1 flex flex-col min-h-0 p-0 data-[state=inactive]:hidden">
          <!-- Toolbar -->
          <div class="flex flex-col gap-2 px-4 py-3 border-b bg-background/50">
            <div class="flex gap-2">
              <div class="relative flex-1">
                <Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                <Input
                  :model-value="knowledgeSearchKeyword"
                  @update:model-value="$emit('update:knowledgeSearchKeyword', $event)"
                  @focus="handleInputFocus"
                  @blur="handleInputBlur"
                  placeholder="搜索文档名称..."
                  class="h-8 text-xs pl-8 pr-8 w-full"
                  @keydown.enter="$emit('refresh-knowledge', knowledgeSearchKeyword)"
                />
                <Button
                  v-if="knowledgeSearchKeyword"
                  variant="ghost"
                  size="icon"
                  class="absolute right-0.5 top-0.5 h-7 w-7 text-muted-foreground hover:text-foreground"
                  @click="() => { $emit('update:knowledgeSearchKeyword', ''); $emit('refresh-knowledge', ''); }"
                >
                  <X class="h-3.5 w-3.5" />
                </Button>
                <!-- Suggestions Dropdown -->
                <div 
                  v-if="showSuggestions && searchSuggestions && searchSuggestions.length > 0"
                  class="absolute top-full left-0 w-full mt-1 bg-popover text-popover-foreground rounded-md border shadow-md z-50 overflow-hidden"
                >
                  <div 
                    v-for="item in searchSuggestions" 
                    :key="item"
                    class="px-3 py-2 text-xs hover:bg-muted cursor-pointer flex items-center gap-2"
                    @mousedown.prevent="handleSelectSuggestion(item)"
                  >
                    <Search class="h-3 w-3 text-muted-foreground" />
                    <span>{{ item }}</span>
                  </div>
                </div>
              </div>
              <Select v-model="filterType">
                <SelectTrigger class="w-[110px] h-8 text-xs">
                  <SelectValue placeholder="类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" class="text-xs">所有类型</SelectItem>
                  <SelectItem value="pdf" class="text-xs">PDF 文档</SelectItem>
                  <SelectItem value="docx" class="text-xs">Word 文档</SelectItem>
                  <SelectItem value="txt" class="text-xs">文本文件</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon" class="h-8 w-8" :disabled="knowledgeLoading" @click="$emit('refresh-knowledge')" title="刷新">
                <RefreshCw :class="['w-3.5 h-3.5', knowledgeLoading ? 'animate-spin' : '']" />
              </Button>
            </div>
          </div>

          <!-- Grid Area -->
          <div class="flex-1 min-h-0 relative p-4 bg-muted/10">
            <ScrollArea class="h-full pr-3">
              <template v-if="knowledgeLoading">
                <div class="grid grid-cols-2 gap-3">
                  <div v-for="i in 6" :key="i" class="h-20 border rounded-lg bg-background p-3 flex gap-2">
                    <Skeleton class="w-8 h-8 rounded" />
                    <div class="flex-1 space-y-1.5">
                      <Skeleton class="h-3.5 w-3/4" />
                      <Skeleton class="h-2.5 w-1/2" />
                    </div>
                  </div>
                </div>
              </template>
              <template v-else-if="paginatedDocs.length > 0">
                <div class="grid grid-cols-2 gap-3">
                  <div 
                    v-for="doc in paginatedDocs" 
                    :key="doc.id"
                    class="relative flex items-start gap-2.5 p-3 rounded-lg border bg-background transition-all duration-200 cursor-pointer group hover:shadow-sm hover:border-primary/50"
                    :class="[selectedKnowledgeRowKeys.includes(doc.id) ? 'ring-1 ring-primary border-primary bg-primary/5' : '']"
                    @click="toggleRow(doc.id)"
                  >
                    <!-- Checkbox (Top Right) -->
                    <div class="absolute top-2.5 right-2.5 z-10">
                       <Checkbox 
                         :checked="selectedKnowledgeRowKeys.includes(doc.id)"
                         @update:checked="(val) => toggleRow(doc.id)"
                         class="h-3.5 w-3.5 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                         @click.stop
                       />
                    </div>

                    <!-- Icon -->
                    <div class="w-8 h-8 rounded-md bg-blue-50 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                      <component :is="getFileIcon(doc.filename)" class="w-4 h-4 text-blue-600" />
                    </div>

                    <!-- Info -->
                    <div class="flex-1 min-w-0 pr-5">
                      <h4 class="text-xs font-medium truncate mb-0.5 text-foreground" :title="doc.filename">
                        {{ doc.filename }}
                      </h4>
                      <div class="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                        <Badge variant="secondary" class="h-4 px-1 font-normal text-[9px] bg-muted">
                          {{ doc.filename.split('.').pop()?.toUpperCase() || 'FILE' }}
                        </Badge>
                        <span>{{ formatFileSize(doc.file_size) }}</span>
                      </div>
                      <div class="mt-1.5 text-[9px] text-muted-foreground/70 flex items-center gap-1">
                        <Clock class="w-2.5 h-2.5" />
                        <span>{{ formatDate(doc.updated_at) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50 py-10">
                  <SearchX class="w-10 h-10 mb-2" />
                  <p class="text-sm font-medium">未找到相关文档</p>
                  <p class="text-xs">请尝试调整搜索关键词或筛选条件</p>
                </div>
              </template>
            </ScrollArea>
          </div>

          <!-- Pagination -->
          <div class="px-4 py-2 border-t bg-muted/10 flex items-center justify-between flex-shrink-0">
            <span class="text-[10px] text-muted-foreground">
              共 {{ sortedDocs.length }} 项，{{ currentPage }}/{{ totalPages }}
            </span>
            <div class="flex items-center gap-1.5">
              <Button variant="outline" size="sm" class="h-6 px-2 text-xs" :disabled="currentPage === 1" @click="currentPage--">上一页</Button>
              <Button variant="outline" size="sm" class="h-6 px-2 text-xs" :disabled="currentPage === totalPages" @click="currentPage++">下一页</Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <DialogFooter class="px-4 py-3 border-t bg-background flex-shrink-0 flex justify-between items-center sm:justify-between">
        <div class="flex items-center gap-2 text-xs text-muted-foreground">
          <span v-if="totalSelected > 0" class="flex items-center gap-1.5 text-primary font-medium animate-in fade-in slide-in-from-bottom-2">
            <Badge variant="default" class="rounded-full px-1.5 h-4 text-[10px]">{{ totalSelected }}</Badge>
            已选择 {{ totalSelected }} 个文件
          </span>
          <span v-else>请选择文件</span>
        </div>
        <div class="flex gap-2">
          <Button variant="outline" size="sm" class="h-8 text-xs" @click="$emit('update:open', false)">取消</Button>
          <Button size="sm" class="h-8 text-xs" @click="handleConfirmClick" :disabled="totalSelected === 0">确认添加</Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <AlertDialog :open="showConfirmDialog" @update:open="showConfirmDialog = $event">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>确认添加附件</AlertDialogTitle>
        <AlertDialogDescription>
          您已选择了 {{ totalSelected }} 个文件。确认将它们添加到当前对话吗？
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>取消</AlertDialogCancel>
        <AlertDialogAction @click="onConfirm">确认</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import JSZip from 'jszip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import { Upload, Paperclip, Trash2, Search, Loader2, FileText, RefreshCw, ArrowUpDown, SearchX, X, File as FileIcon, FileUp, Clock, FolderUp, FileArchive } from 'lucide-vue-next';
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
  searchSuggestions?: string[];
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

const { toast } = useToast();
const showConfirmDialog = ref(false);
const showSuggestions = ref(false);

const handleInputFocus = () => {
  if (props.searchSuggestions && props.searchSuggestions.length > 0) {
    showSuggestions.value = true;
  }
};

const handleInputBlur = () => {
  // Delay hiding to allow click event on suggestion item
  setTimeout(() => {
    showSuggestions.value = false;
  }, 200);
};

const handleSelectSuggestion = (suggestion: string) => {
  emit('update:knowledgeSearchKeyword', suggestion);
  emit('refresh-knowledge', suggestion);
  showSuggestions.value = false;
};

// Watch suggestions to show them if keyword is not empty
watch(() => props.searchSuggestions, (newVal) => {
  if (newVal && newVal.length > 0 && props.knowledgeSearchKeyword) {
    showSuggestions.value = true;
  }
});

const handleConfirmClick = () => {
  if (totalSelected.value > 0) {
    showConfirmDialog.value = true;
  }
};

const onConfirm = () => {
  showConfirmDialog.value = false;
  emit('confirm');
};

const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase();
  if (['zip', 'rar', '7z', 'tar'].includes(ext || '')) {
    return FileArchive;
  }
  return FileText;
};

// --- Local Upload Logic ---
const fileInputRef = ref<HTMLInputElement | null>(null);
const folderInputRef = ref<HTMLInputElement | null>(null);
const archiveInputRef = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);
const isProcessing = ref(false);

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.zip', '.rar', '.7z', '.tar'];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

const validateFile = (file: File): boolean => {
  // Skip hidden files (starting with .)
  if (file.name.startsWith('.')) return false;
  
  const extension = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!SUPPORTED_EXTENSIONS.includes(extension)) {
    // Only show toast for explicit single file uploads to avoid spamming for folder uploads
    // toast({
    //   title: "不支持的文件格式",
    //   description: `文件 ${file.name} 格式不支持。`,
    //   variant: "destructive",
    // });
    return false;
  }
  if (file.size > MAX_FILE_SIZE) {
    toast({
      title: "文件过大",
      description: `文件 ${file.name} 超过 50MB 限制。`,
      variant: "destructive",
    });
    return false;
  }
  return true;
};

const processFiles = async (files: File[]) => {
  if (files.length === 0) return;
  isProcessing.value = true;
  
  let processedFiles: File[] = [];

  try {
    for (const file of files) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      
      // Auto-extract ZIP files
      if (ext === '.zip') {
        try {
          // @ts-ignore
          const zip = new (JSZip as any)();
          const zipContent = await zip.loadAsync(file, {
            // Fix encoding issue for Chinese characters
            decodeFileName: (bytes: Uint8Array) => {
              try {
                // Try UTF-8 first
                return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
              } catch (e) {
                // Fallback to GBK (common in Windows zip)
                return new TextDecoder('gbk', { fatal: true }).decode(bytes);
              }
            }
          });
          const extractionPromises: Promise<File | null>[] = [];

          zipContent.forEach((relativePath, zipEntry) => {
            if (!zipEntry.dir) {
              const entryExt = '.' + zipEntry.name.split('.').pop()?.toLowerCase();
              if (SUPPORTED_EXTENSIONS.includes(entryExt) && !zipEntry.name.startsWith('__MACOSX') && !zipEntry.name.startsWith('.')) {
                extractionPromises.push(
                  zipEntry.async('blob').then(blob => {
                    const filename = zipEntry.name.split('/').pop() || zipEntry.name;
                    return new File([blob], filename, { type: blob.type || 'application/octet-stream' });
                  })
                );
              }
            }
          });

          const extracted = await Promise.all(extractionPromises);
          const validExtracted = extracted.filter((f): f is File => f !== null);
          
          if (validExtracted.length > 0) {
            processedFiles = [...processedFiles, ...validExtracted];
            toast({
              title: "压缩包已解压",
              description: `从 ${file.name} 中获取了 ${validExtracted.length} 个支持的文件。`,
            });
          } else {
             processedFiles.push(file); 
          }
        } catch (e) {
          console.error("Failed to unzip", file.name, e);
          toast({ description: `无法解压 ${file.name}，将作为普通文件处理。`, variant: 'destructive' });
          processedFiles.push(file);
        }
      } else {
        processedFiles.push(file);
      }
    }
  } catch (error) {
    console.error("Error processing files", error);
  } finally {
    isProcessing.value = false;
  }

  const validFiles = processedFiles.filter(validateFile);
  
  if (validFiles.length === 0 && processedFiles.length > 0) {
      toast({
        title: "无有效文件",
        description: `未找到支持的文档格式 (${SUPPORTED_EXTENSIONS.join(', ')}).`,
        variant: "destructive",
      });
      return;
  }

  if (validFiles.length > 0) {
    // Check for duplicates
    const newFiles = validFiles.filter(newFile => 
      !props.localFileList.some(existing => existing.name === newFile.name && existing.size === newFile.size)
    );

    if (newFiles.length < validFiles.length) {
       if (validFiles.length < 5) {
          toast({
            title: "部分文件已存在",
            description: "已自动过滤重复文件。",
          });
       }
    }

    if (newFiles.length > 0) {
      emit('file-change', [...props.localFileList, ...newFiles]); 
      toast({
        title: "文件添加成功",
        description: `已添加 ${newFiles.length} 个文件。`,
      });
    }
  }
};

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const triggerFolderInput = () => {
  folderInputRef.value?.click();
};

const triggerArchiveInput = () => {
  archiveInputRef.value?.click();
};

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    processFiles(Array.from(target.files));
    target.value = '';
  }
};

const handleFolderChange = (e: Event) => {
    const target = e.target as HTMLInputElement;
    if (target.files) {
        processFiles(Array.from(target.files));
        target.value = '';
    }
};

const handleDrop = (e: DragEvent) => {
  isDragOver.value = false;
  if (e.dataTransfer?.files) {
    processFiles(Array.from(e.dataTransfer.files));
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
