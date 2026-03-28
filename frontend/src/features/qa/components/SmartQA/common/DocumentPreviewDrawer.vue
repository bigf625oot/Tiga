<template>
  <Sheet :open="visible" @update:open="updateVisible">
    <SheetContent side="right" class="w-[600px] sm:max-w-[800px] p-0 flex flex-col h-full z-[100] border-l border-border bg-background shadow-2xl">
      <SheetHeader class="px-6 py-4 border-b border-border bg-muted/5 shrink-0">
        <SheetTitle class="flex items-center gap-2 text-foreground">
          <FileText class="w-5 h-5 text-primary" />
          <span class="truncate">{{ docTitle || '文档预览' }}</span>
        </SheetTitle>
      </SheetHeader>
      
      <div class="flex-1 overflow-hidden relative bg-background/50 flex flex-col">
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
          <Loader2 class="w-8 h-8 animate-spin text-primary/50" />
        </div>
        <div v-else-if="error" class="absolute inset-0 flex items-center justify-center text-destructive">
          {{ error }}
        </div>
        <ScrollArea v-else class="flex-1 h-full w-full custom-scrollbar">
          <div class="p-6 md:p-8 markdown-body text-sm leading-relaxed max-w-4xl mx-auto" v-html="renderedContent"></div>
        </ScrollArea>
      </div>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { FileText, Loader2 } from 'lucide-vue-next';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { knowledgeService } from '../../../services/knowledgeService';
import { marked } from 'marked';

const props = defineProps<{
  visible: boolean;
  docId: string | number | null;
}>();

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
}>();

const loading = ref(false);
const error = ref('');
const docTitle = ref('');
const renderedContent = ref('');

const updateVisible = (val: boolean) => {
  emit('update:visible', val);
};

const fetchContent = async () => {
  if (!props.docId) return;
  
  loading.value = true;
  error.value = '';
  docTitle.value = '加载中...';
  renderedContent.value = '';
  
  try {
    const res = await knowledgeService.getDocumentContent(props.docId);
    docTitle.value = res.filename || `Document #${props.docId}`;
    
    if (res.content) {
      // Basic text to markdown conversion if it's plain text
      let text = res.content;
      // if it doesn't look like markdown, just wrap in pre
      if (!text.includes('#') && !text.includes('**')) {
         text = '```text\n' + text + '\n```';
      }
      renderedContent.value = marked.parse(text) as string;
    } else {
      renderedContent.value = '<div class="text-muted-foreground italic">暂无内容</div>';
    }
  } catch (err: any) {
    console.error('Failed to fetch doc content:', err);
    error.value = '加载文档内容失败';
    docTitle.value = `Document #${props.docId}`;
  } finally {
    loading.value = false;
  }
};

watch(() => props.visible, (newVal) => {
  if (newVal && props.docId) {
    fetchContent();
  }
});
</script>

<style scoped>
.markdown-body { 
  font-size: 14px; 
  line-height: 1.6; 
  color: hsl(var(--foreground)); 
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"; 
}
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { 
  font-weight: 600; 
  margin-top: 1.5em; 
  margin-bottom: 0.5em; 
  color: hsl(var(--foreground)); 
}
.markdown-body :deep(h1) { font-size: 1.5em; border-bottom: 1px solid hsl(var(--border)); padding-bottom: 0.3em; }
.markdown-body :deep(h2) { font-size: 1.3em; }
.markdown-body :deep(h3) { font-size: 1.1em; }
.markdown-body :deep(p) { margin-bottom: 1em; }
.markdown-body :deep(strong) { font-weight: 600; color: hsl(var(--foreground)); }
.markdown-body :deep(ul) { list-style-type: disc; padding-left: 1.5em; margin-bottom: 1em; }
.markdown-body :deep(ol) { list-style-type: decimal; padding-left: 1.5em; margin-bottom: 1em; }
.markdown-body :deep(li) { margin-bottom: 0.25em; }
.markdown-body :deep(blockquote) { border-left: 3px solid hsl(var(--border)); padding-left: 1em; color: hsl(var(--muted-foreground)); margin: 1em 0; }
.markdown-body :deep(pre) {
    background-color: hsl(var(--muted));
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    font-family: monospace;
    font-size: 0.875rem;
    white-space: pre-wrap;
    word-break: break-word;
    border: 1px solid hsl(var(--border));
}
.markdown-body :deep(code) { 
  background-color: hsl(var(--muted)); 
  padding: 0.2em 0.4em; 
  border-radius: 4px; 
  font-size: 0.9em; 
  font-family: monospace; 
}
.markdown-body :deep(pre code) { 
  background-color: transparent; 
  padding: 0; 
  color: inherit; 
  border: none;
}
</style>
