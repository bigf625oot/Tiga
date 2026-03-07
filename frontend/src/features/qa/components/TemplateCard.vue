<template>
  <button 
    class="w-full text-left group h-full relative overflow-hidden border border-border bg-white hover:border-indigo-100 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 rounded-lg"
    @click="$emit('fill', template)"
  >
    <!-- Background Gradient -->
    <div class="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" :class="gradient"></div>
    
    <div class="p-4 relative z-10 flex flex-col h-full">
       <div class="flex items-start gap-4 mb-2">
         <div class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-sm group-hover:scale-110 transition-transform duration-300 bg-gradient-to-br" :class="iconBg">
           <component :is="icon" class="text-sm" />
         </div>
         <div class="min-w-0 pt-0.5">
           <h3 class="text-xs font-semibold text-slate-900 mb-0.5 group-hover:text-indigo-700 transition-colors truncate">{{ title }}</h3>
           <p class="text-[10px] text-muted-foreground leading-tight line-clamp-2 pr-1">{{ description }}</p>
         </div>
       </div>
       
       <div class="mt-auto flex items-center justify-end">
         <span class="text-[10px] font-semibold text-indigo-500 group-hover:text-indigo-600 transition-colors flex items-center gap-0.5 opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 transition-all duration-300">
           使用
           <ArrowRightOutlined class="text-[8px]" />
         </span>
       </div>
    </div>
  </button>
</template>

<script lang="ts" setup>
/**
 * @场景    自动任务模板库中展示可一键填充的任务模板卡片
 * @功能    渲染模板标题、描述、图标与点击填充事件
 * @依赖    Vue3、TypeScript、Ant Design 图标
 * @备注    仅做展示与事件抛出，具体任务创建由父组件处理
 */
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
