<template>
  <div 
    class="h-14 flex items-center justify-between px-6 border-b transition-colors duration-300"
    :class="isLightMode ? 'bg-white border-border' : 'bg-[#0B0C10] border-gray-800'"
  >
    <div class="flex items-center gap-4">
      <h1 
        class="text-[20px] font-semibold tracking-wide transition-colors"
        :class="isLightMode ? 'text-gray-900' : 'text-white'"
      >图谱实时大盘</h1>
      <span class="px-1.5 py-0.5 text-[11px] font-semibold bg-[#1E3A8A] text-[#60A5FA] rounded border border-[#1E40AF]">LIVE</span>
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
