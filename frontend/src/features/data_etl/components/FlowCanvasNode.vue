<template>
  <div 
    class="relative rounded-xl border shadow-lg bg-white w-64 transition-all duration-300 group overflow-hidden"
    :class="[
      isLightMode 
        ? 'border-slate-200 hover:border-blue-500/30 hover:shadow-xl' 
        : 'dark:bg-white/5 dark:backdrop-blur-md dark:border-t-white/20 dark:border-x-white/10 dark:border-b-transparent dark:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)] dark:hover:border-blue-500/50'
    ]"
  >
    <!-- Left Status Strip -->
    <div 
      class="absolute left-0 top-0 bottom-0 w-1 transition-all duration-300"
      :class="{
        'bg-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)]': data.type === 'classifier',
        'bg-orange-500 shadow-[0_0_15px_rgba(249,115,22,0.4)]': data.type === 'condition',
        'bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.4)]': data.type === 'validator'
      }"
    ></div>

    <div class="p-4 pl-5">
      <!-- Node Header -->
      <div class="flex items-center gap-3 mb-4">
        <div 
          class="w-9 h-9 rounded-lg flex items-center justify-center shadow-inner"
          :class="{
            'bg-gradient-to-br from-purple-50 to-purple-100 text-purple-600': isLightMode && data.type === 'classifier',
            'bg-gradient-to-br from-orange-50 to-orange-100 text-orange-600': isLightMode && data.type === 'condition',
            'bg-gradient-to-br from-blue-50 to-blue-100 text-blue-600': isLightMode && data.type === 'validator',
            'bg-purple-900/30 text-purple-400': !isLightMode && data.type === 'classifier',
            'bg-orange-900/30 text-orange-400': !isLightMode && data.type === 'condition',
            'bg-blue-900/30 text-blue-400': !isLightMode && data.type === 'validator'
          }"
        >
          <svg v-if="data.type === 'classifier'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <svg v-else-if="data.type === 'condition'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <div class="font-bold text-[14px]" :class="isLightMode ? 'text-slate-800' : 'text-white'">{{ data.label }}</div>
          <div class="text-[12px]" :class="isLightMode ? 'text-slate-500' : 'text-white/60'">{{ data.subLabel }}</div>
        </div>
        
        <button 
          class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-full hover:bg-red-50 text-slate-400 hover:text-red-500 nodrag"
          @click.stop="onDelete"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Stats -->
      <div class="space-y-3">
        <div class="flex justify-between items-center text-[12px]">
          <span :class="isLightMode ? 'text-slate-500' : 'text-white/60'">处理效率</span>
          <span class="font-mono font-medium" :class="isLightMode ? 'text-slate-700' : 'text-gray-200'">
            {{ data.stats.total.toLocaleString() }} 
            <span class="text-[10px]" :class="isLightMode ? 'text-slate-400' : 'text-white/60'">ops</span>
          </span>
        </div>
        
        <!-- Refined Progress Bar -->
        <div class="space-y-1.5">
          <div class="flex justify-between text-[11px]">
            <span :class="isLightMode ? 'text-slate-400' : 'text-white/60'">成功率</span>
            <span class="font-mono font-medium" :class="data.stats.pass_rate > 90 ? 'text-green-500' : 'text-yellow-500'">
              {{ data.stats.pass_rate }}
              <span :class="isLightMode ? 'text-slate-400' : 'text-white/60'">%</span>
            </span>
          </div>
          <div class="h-1.5 w-full bg-slate-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div 
              class="h-full rounded-full transition-all duration-500"
              :class="data.stats.pass_rate > 90 ? 'bg-green-500' : 'bg-yellow-500'"
              :style="{ width: `${data.stats.pass_rate}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Refined Handles -->
    <Handle 
      type="target" 
      :position="Position.Left" 
      class="!w-2.5 !h-2.5 !bg-white !border-2 !border-slate-300 dark:!border-gray-600 !-ml-1.5 transition-colors hover:!border-blue-500 hover:!bg-blue-50" 
    />
    <Handle 
      type="source" 
      :position="Position.Right" 
      class="!w-2.5 !h-2.5 !bg-white !border-2 !border-slate-300 dark:!border-gray-600 !-mr-1.5 transition-colors hover:!border-blue-500 hover:!bg-blue-50" 
    />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position, useVueFlow, type NodeProps } from '@vue-flow/core';
import { useTheme } from '@/composables/useTheme';

const props = defineProps<NodeProps>();

const { isLightMode } = useTheme();
const { removeNodes } = useVueFlow();

const getNodeIconText = (type: string) => {
  switch(type) {
    case 'classifier': return 'C';
    case 'condition': return '?';
    case 'validator': return 'V';
    default: return '#';
  }
};

const onDelete = () => {
  removeNodes(props.id);
  // Also emit custom event if needed via Vue Flow instance or global event bus, but removeNodes updates the graph directly.
};
</script>
