<template>
  <div class="px-4 py-3 flex items-center justify-between border-b transition-colors duration-300 backdrop-blur supports-[backdrop-filter]:bg-background/60 bg-background/95 border-border">
    <!-- Left: Title -->
    <div class="flex items-center gap-3">
      <h2 class="text-lg font-semibold tracking-tight transition-colors text-foreground">数据大盘</h2>
      <div class="h-4 w-px bg-border"></div>
      <span class="px-1.5 py-0.5 text-[10px] font-semibold rounded border bg-blue-500/10 text-blue-500 border-blue-500/20">LIVE</span>
    </div>
    
    <!-- Right: Actions -->
    <div class="flex items-center gap-3">
      <!-- Last Updated -->
      <div class="hidden md:flex items-center gap-2 text-xs text-muted-foreground mr-2">
         <Clock class="w-3.5 h-3.5" />
         <span>最后更新: {{ lastUpdated }}</span>
      </div>

      <!-- Engine Status -->
      <div class="flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full mr-2">
        <div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
        <span class="text-xs font-medium text-green-600 dark:text-green-400">引擎运行中</span>
      </div>

      <div class="h-4 w-px bg-border"></div>

      <!-- Action Buttons -->
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground" @click="refreshData">
              <RefreshCcw class="w-4 h-4" :class="{'animate-spin': isRefreshing}" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>刷新数据</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground">
              <Settings class="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>大盘设置</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { RefreshCcw, Settings, Clock } from 'lucide-vue-next';
import dayjs from 'dayjs';

const lastUpdated = ref('');
const isRefreshing = ref(false);

const updateTime = () => {
  lastUpdated.value = dayjs().format('HH:mm:ss');
};

const refreshData = () => {
  isRefreshing.value = true;
  // Mock refresh delay
  setTimeout(() => {
    isRefreshing.value = false;
    updateTime();
  }, 1000);
};

onMounted(() => {
  updateTime();
});
</script>
