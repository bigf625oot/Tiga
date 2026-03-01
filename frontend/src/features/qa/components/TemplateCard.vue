<template>
  <button 
    class="w-full text-left group h-full relative overflow-hidden border border-slate-100 bg-white hover:border-indigo-100 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 rounded-2xl"
    @click="$emit('fill', template)"
  >
    <!-- Background Gradient -->
    <div class="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" :class="gradient"></div>
    
    <div class="p-3 relative z-10 flex flex-col h-full">
       <div class="flex items-start gap-3 mb-2">
         <div class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-sm group-hover:scale-110 transition-transform duration-300 bg-gradient-to-br" :class="iconBg">
           <component :is="icon" class="text-sm" />
         </div>
         <div class="min-w-0 pt-0.5">
           <h3 class="text-xs font-bold text-slate-900 mb-0.5 group-hover:text-indigo-700 transition-colors truncate">{{ title }}</h3>
           <p class="text-[10px] text-slate-500 leading-tight line-clamp-2 pr-1">{{ description }}</p>
         </div>
       </div>
       
       <div class="mt-auto flex items-center justify-end">
         <span class="text-[10px] font-bold text-indigo-500 group-hover:text-indigo-600 transition-colors flex items-center gap-0.5 opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 transition-all duration-300">
           使用
           <ArrowRightOutlined class="text-[8px]" />
         </span>
       </div>
    </div>
  </button>
</template>

<script lang="ts" setup>
import { ArrowRightOutlined } from '@ant-design/icons-vue';

defineProps<{
  icon: any;
  title: string;
  description: string;
  template: string;
  gradient: string;
  iconBg: string;
}>();

defineEmits(['fill']);
</script>
