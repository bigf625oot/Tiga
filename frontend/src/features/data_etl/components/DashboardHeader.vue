<template>
  <div 
    class="h-16 flex items-center justify-between px-6 border-b transition-colors duration-300 backdrop-blur-md"
    :class="isLightMode ? 'bg-white/80 border-slate-200' : 'bg-[#0B0C10] border-gray-800'"
  >
    <div class="flex items-center gap-4">
      <h1 
        class="text-[20px] font-semibold tracking-wide transition-colors"
        :class="isLightMode ? 'text-slate-900' : 'text-white'"
      >图谱实时大盘</h1>
      <span 
        class="px-1.5 py-0.5 text-[11px] font-semibold rounded border"
        :class="isLightMode ? 'bg-blue-100 text-blue-600 border-blue-200' : 'bg-[#1E3A8A] text-[#60A5FA] border-[#1E40AF]'"
      >LIVE</span>
    </div>
    
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2 p-4 py-1 bg-[#064E3B] border border-[#065F46] rounded-full">
        <div class="w-2 h-2 rounded-full bg-[#34D399] animate-pulse"></div>
        <span class="text-[13px] font-medium text-[#34D399]">流水线引擎运行中</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from '@/composables/useTheme';

const { isLightMode, toggleTheme } = useTheme();
</script>
