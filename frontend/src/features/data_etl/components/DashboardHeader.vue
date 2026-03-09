<template>
  <div 
    class="px-4 py-3 flex items-center justify-between border-b transition-colors duration-300 backdrop-blur supports-[backdrop-filter]:bg-background/60"
    :class="isLightMode ? 'bg-white/95 border-slate-200' : 'bg-[#0B0C10]/95 border-gray-800'"
  >
    <div class="flex items-center gap-3">
      <h2 
        class="text-lg font-semibold tracking-tight transition-colors"
        :class="isLightMode ? 'text-slate-900' : 'text-white'"
      >数据大盘</h2>
      <div class="h-4 w-px bg-border"></div>
      <span 
        class="px-1.5 py-0.5 text-[10px] font-semibold rounded border"
        :class="isLightMode ? 'bg-blue-100 text-blue-600 border-blue-200' : 'bg-[#1E3A8A] text-[#60A5FA] border-[#1E40AF]'"
      >LIVE</span>
    </div>
    
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2 px-3 py-1 bg-[#064E3B] border border-[#065F46] rounded-full">
        <div class="w-1.5 h-1.5 rounded-full bg-[#34D399] animate-pulse"></div>
        <span class="text-xs font-medium text-[#34D399]">引擎运行中</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from '@/composables/useTheme';

const { isLightMode, toggleTheme } = useTheme();
</script>
