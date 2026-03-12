<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[600px]">
      <DialogHeader>
        <DialogTitle>选择附件</DialogTitle>
      </DialogHeader>

      <Tabs :model-value="activeTab" @update:model-value="$emit('update:activeTab', $event)" class="w-full">
        <TabsList class="grid w-full grid-cols-2">
          <TabsTrigger value="local">本地文件</TabsTrigger>
          <TabsTrigger value="knowledge">知识库文档</TabsTrigger>
        </TabsList>

        <TabsContent value="local" class="py-4">
          <div class="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer"
            @click="triggerFileInput" @drop.prevent="handleDrop" @dragover.prevent>
            <input type="file" ref="fileInputRef" class="hidden" multiple @change="handleFileChange" />
            <div class="flex flex-col items-center gap-2 text-muted-foreground">
              <Upload class="w-10 h-10 mb-2 text-muted-foreground/50" />
              <p class="text-sm font-medium">点击或拖拽文件到此区域上传</p>
              <p class="text-xs">支持 PDF, DOCX, PPTX, XLSX, TXT 格式，最大 50MB</p>
            </div>
          </div>

          <div v-if="localFileList.length > 0" class="mt-4 max-h-40 overflow-y-auto space-y-2 custom-scrollbar pr-2">
            <div v-for="file in localFileList" :key="file.name" class="flex items-center justify-between p-2 bg-muted/30 rounded border border-border">
              <div class="flex items-center gap-2 truncate">
                <Paperclip class="w-4 h-4 text-muted-foreground" />
                <span class="text-sm text-foreground truncate max-w-[300px]">{{ file.name }}</span>
                <span class="text-xs text-muted-foreground">({{ (file.size / 1024).toFixed(1) }} KB)</span>
              </div>
              <Button variant="ghost" size="icon" class="h-6 w-6 text-muted-foreground hover:text-destructive" @click="$emit('remove-local-file', file)">
                <Trash2 class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="knowledge" class="py-4">
          <div class="flex flex-col gap-4 h-[400px]">
            <div class="flex gap-2">
              <div class="relative flex-1">
                <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input :model-value="knowledgeSearchKeyword" @update:model-value="$emit('update:knowledgeSearchKeyword', $event)" placeholder="搜索文档名称..." class="pl-9" />
              </div>
              <Button variant="outline" :disabled="knowledgeLoading" @click="$emit('refresh-knowledge')">
                <Loader2 v-if="knowledgeLoading" class="w-4 h-4 animate-spin mr-2" />
                刷新
              </Button>
            </div>

            <div class="border rounded-md flex-1 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="w-[40px]"></TableHead>
                    <TableHead>文档名称</TableHead>
                    <TableHead>大小</TableHead>
                    <TableHead class="text-right">修改时间</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="doc in filteredKnowledgeDocs" :key="doc.id">
                    <TableCell>
                      <input type="checkbox"
                        :checked="selectedKnowledgeRowKeys.includes(doc.id)"
                        @change="(e: any) => $emit('toggle-knowledge-selection', doc.id, e.target.checked)"
                        class="rounded border-gray-300 text-primary focus:ring-primary" />
                    </TableCell>
                    <TableCell class="font-medium">{{ doc.filename }}</TableCell>
                    <TableCell>{{ (doc.file_size / 1024).toFixed(2) }} KB</TableCell>
                    <TableCell class="text-right">{{ new Date(doc.updated_at).toLocaleDateString() }}</TableCell>
                  </TableRow>
                  <TableRow v-if="filteredKnowledgeDocs.length === 0">
                    <TableCell colspan="4" class="h-24 text-center text-muted-foreground">暂无文档</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <DialogFooter>
        <Button variant="outline" @click="$emit('update:open', false)">取消</Button>
        <Button @click="$emit('confirm')">确认 ({{ localFileList.length + selectedKnowledgeRowKeys.length }})</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Upload, Paperclip, Trash2, Search, Loader2 } from 'lucide-vue-next';
import type { KnowledgeDoc } from '../../types';

defineProps<{
  open: boolean;
  activeTab: string;
  localFileList: File[];
  knowledgeDocs: KnowledgeDoc[];
  filteredKnowledgeDocs: KnowledgeDoc[];
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

const fileInputRef = ref<HTMLInputElement | null>(null);

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    const files = Array.from(target.files);
    emit('file-change', files);
    target.value = '';
  }
};

const handleDrop = (e: DragEvent) => {
  if (e.dataTransfer?.files) {
    const files = Array.from(e.dataTransfer.files);
    emit('file-change', files);
  }
};
</script>
