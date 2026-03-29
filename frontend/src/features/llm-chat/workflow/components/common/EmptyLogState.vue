<template>
  <div class="empty-log-state flex flex-col items-center justify-center h-full w-full py-8 select-none" data-testid="empty-log-state">
    <img 
      :src="isDarkMode ? darkSvg : lightSvg" 
      alt="暂无日志" 
      class="w-[240px] h-[180px] object-contain block"
    />
    <span 
      class="mt-4 text-[14px] font-normal font-sans transition-colors duration-300"
      :class="isDarkMode ? 'text-[#C0C4CC]' : 'text-[#909399]'"
    >
      暂无日志
    </span>
  </div>
</template>

<script setup>
import lightSvg from '@/assets/svg/empty-log.svg';
import darkSvg from '@/assets/svg/empty-log-dark.svg';

defineProps({
  isDarkMode: {
    type: Boolean,
    default: false
  }
});
</script>
