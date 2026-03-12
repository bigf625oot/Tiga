<template>
  <div class="h-full w-full flex flex-col items-center justify-center p-8 select-none text-muted-foreground/40">
    <div class="relative w-32 h-32 mb-6">
      <!-- Outer glow -->
      <div class="absolute inset-0 bg-primary/5 rounded-full blur-3xl animate-pulse"></div>
      
      <!-- Hexagon Grid -->
      <svg class="w-full h-full drop-shadow-sm" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M50 20L75 35V65L50 80L25 65V35L50 20Z" class="stroke-current opacity-20" stroke-width="2" stroke-linejoin="round"/>
        <path d="M50 35L62.5 42.5V57.5L50 65L37.5 57.5V42.5L50 35Z" class="stroke-current opacity-40" stroke-width="2" stroke-linejoin="round"/>
        <circle cx="50" cy="50" r="3" class="fill-primary/60 animate-pulse" />
        
        <!-- Animated Particles -->
        <circle cx="50" cy="20" r="1.5" class="fill-current opacity-30 animate-[ping_3s_ease-in-out_infinite]" />
        <circle cx="75" cy="65" r="1.5" class="fill-current opacity-30 animate-[ping_3s_ease-in-out_infinite_1s]" />
        <circle cx="25" cy="65" r="1.5" class="fill-current opacity-30 animate-[ping_3s_ease-in-out_infinite_2s]" />
      </svg>
    </div>
    
    <div class="flex flex-col items-center gap-2">
      <h3 class="text-sm font-semibold tracking-wide text-foreground/60">等待任务启动</h3>
      <p class="text-xs text-muted-foreground/60 max-w-[200px] text-center leading-relaxed">
        请在左侧对话框中输入需求，或选择预设指令开始规划
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
// Empty state component
</script>
