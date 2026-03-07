<template>
  <div 
    class="resource-card cursor-pointer bg-white border border-slate-200 rounded-lg p-4 my-2 flex items-center gap-4 hover:shadow-md transition-all group select-none relative overflow-hidden"
    @click="$emit('click', id)"
  >
    <!-- Icon Container -->
    <div 
        class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-colors"
        :class="iconClasses"
    >
        <!-- Doc Icon -->
        <svg v-if="type === 'doc'" xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <!-- File Icon -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0 text-left">
      <h4 class="text-sm font-semibold text-slate-800 truncate mb-0.5 leading-tight">{{ title }}</h4>
      <p class="text-xs text-muted-foreground m-0">{{ subtitle }}</p>
    </div>

    <!-- Action Icon -->
    <div class="text-muted-foreground group-hover:text-blue-500 transition-colors">
        <!-- Arrow for Doc -->
        <svg v-if="type === 'doc'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        <!-- Download for File -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
    type: 'doc' | 'file';
    id: string;
    title: string;
    meta?: string | number;
}

const props = defineProps<Props>();
defineEmits<{
    (e: 'click', id: string): void
}>();

const iconClasses = computed(() => {
    if (props.type === 'doc') {
        return 'bg-primary/10 text-primary group-hover:bg-blue-100';
    }
    return 'bg-indigo-50 text-indigo-600 group-hover:bg-indigo-100';
});

const subtitle = computed(() => {
    if (props.type === 'file') {
        const size = typeof props.meta === 'number' ? props.meta : 0;
        return size > 0 
            ? (size / 1024).toFixed(1) + ' KB' 
            : (props.meta || 'File');
    }
    return '点击打开文档空间';
});
</script>
