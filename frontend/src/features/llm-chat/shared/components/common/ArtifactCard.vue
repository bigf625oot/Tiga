<template>
  <div class="my-4 inline-flex items-center p-3 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-shadow max-w-sm w-full gap-3 cursor-pointer group" @click="handleDownload">
    <div class="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg" :class="iconBgClass">
      <component :is="fileIcon" class="w-5 h-5" :class="iconColorClass" />
    </div>
    
    <div class="flex-1 min-w-0 flex flex-col justify-center">
      <p class="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors" :title="name">
        {{ name }}
      </p>
      <div class="flex items-center gap-2 mt-1">
        <span class="text-xs text-muted-foreground">{{ ext.toUpperCase() }} 文档</span>
      </div>
    </div>

    <div class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full hover:bg-muted transition-colors">
      <Download class="w-4 h-4 text-muted-foreground group-hover:text-primary" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { 
  FileText, 
  FileSpreadsheet, 
  FileCode, 
  FileImage, 
  FileArchive, 
  File as FileIconDefault,
  Download
} from 'lucide-vue-next';

const props = defineProps<{
  name: string;
  url: string;
}>();

const ext = computed(() => {
  const parts = props.name.split('.');
  return parts.length > 1 ? parts.pop()?.toLowerCase() || '' : '';
});

const fileIcon = computed(() => {
  switch (ext.value) {
    case 'pdf':
    case 'docx':
    case 'doc':
    case 'txt':
    case 'md':
      return FileText;
    case 'xlsx':
    case 'xls':
    case 'csv':
      return FileSpreadsheet;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'webp':
      return FileImage;
    case 'zip':
    case 'tar':
    case 'gz':
    case 'rar':
      return FileArchive;
    case 'js':
    case 'ts':
    case 'py':
    case 'json':
    case 'html':
    case 'css':
      return FileCode;
    default:
      return FileIconDefault;
  }
});

const iconColorClass = computed(() => {
  switch (ext.value) {
    case 'pdf': return 'text-red-500';
    case 'docx':
    case 'doc': return 'text-blue-500';
    case 'xlsx':
    case 'xls':
    case 'csv': return 'text-emerald-500';
    case 'zip':
    case 'rar': return 'text-amber-500';
    default: return 'text-slate-500';
  }
});

const iconBgClass = computed(() => {
  switch (ext.value) {
    case 'pdf': return 'bg-red-50 dark:bg-red-500/10';
    case 'docx':
    case 'doc': return 'bg-blue-50 dark:bg-blue-500/10';
    case 'xlsx':
    case 'xls':
    case 'csv': return 'bg-emerald-50 dark:bg-emerald-500/10';
    case 'zip':
    case 'rar': return 'bg-amber-50 dark:bg-amber-500/10';
    default: return 'bg-slate-50 dark:bg-slate-500/10';
  }
});

const handleDownload = () => {
  if (!props.url) return;
  // Create a temporary link to trigger download
  const link = document.createElement('a');
  link.href = props.url;
  link.download = props.name || 'download';
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
</script>
