<template>
  <div 
    class="inline-flex items-center gap-2 px-3 py-1.5 my-1 rounded-lg border border-border bg-card shadow-sm hover:shadow hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all duration-200 group w-fit max-w-full align-middle"
    @click="handleClick"
    title="点击预览文档"
  >
    <div class="flex items-center justify-center w-6 h-6 rounded-md bg-primary/10 text-primary shrink-0 group-hover:bg-primary/20 transition-colors">
      <FileText class="w-3.5 h-3.5" />
    </div>
    <div class="flex flex-col min-w-0">
      <span class="text-sm font-medium text-foreground truncate flex items-center gap-1">
        <span class="text-primary/80 font-bold shrink-0">doc#{{ docId }}:</span>
        <span class="truncate" :title="title">《{{ title }}》</span>
      </span>
    </div>
    <ChevronRight class="w-4 h-4 text-muted-foreground/50 group-hover:text-primary/70 transition-colors shrink-0" />
  </div>
</template>

<script setup lang="ts">
import { FileText, ChevronRight } from 'lucide-vue-next';

const props = defineProps<{
  docId: string;
  title: string;
}>();

const emit = defineEmits<{
  (e: 'click', docId: string): void;
}>();

const handleClick = () => {
  emit('click', props.docId);
};
</script>
