<template>
  <div 
    class="rounded-lg border shadow-xl p-4 w-64 transition-colors group"
    :class="[
      isLightMode 
        ? 'bg-white border-border hover:border-blue-400 shadow-gray-200/50' 
        : 'bg-[#1F2937] border-gray-700 hover:border-blue-500 shadow-black/50'
    ]"
  >
    <!-- Node Header -->
    <div class="flex items-center gap-4 m-4">
      <div 
        class="w-10 h-10 rounded-lg flex items-center justify-center font-semibold text-lg"
        :class="{
          'bg-purple-100 text-purple-600': isLightMode && data.type === 'classifier',
          'bg-orange-100 text-orange-600': isLightMode && data.type === 'condition',
          'bg-blue-100 text-primary': isLightMode && data.type === 'validator',
          'bg-purple-900/50 text-purple-400': !isLightMode && data.type === 'classifier',
          'bg-orange-900/50 text-orange-400': !isLightMode && data.type === 'condition',
          'bg-blue-900/50 text-blue-400': !isLightMode && data.type === 'validator'
        }"
      >
        {{ getNodeIconText(data.type) }}
      </div>
      <div>
        <div class="font-medium text-[15px]" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ data.label }}</div>
        <div class="text-[13px]" :class="isLightMode ? 'text-gray-500' : 'text-gray-500'">{{ data.subLabel }}</div>
      </div>
      <!-- Delete Button (Hover) -->
      <button 
        class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity font-semibold text-xl leading-none px-2 nodrag"
        :class="isLightMode ? 'text-gray-400 hover:text-red-500' : 'text-gray-600 hover:text-red-500'"
        @click.stop="onDelete"
      >
        &times;
      </button>
    </div>

    <!-- Stats -->
    <div class="space-y-2">
      <div class="flex justify-between text-[13px]">
        <span :class="isLightMode ? 'text-gray-500' : 'text-gray-500'">处理总数</span>
        <span class="text-[13px] font-din" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ data.stats.total.toLocaleString() }}</span>
      </div>
      <div class="flex justify-between text-[13px]">
        <span :class="isLightMode ? 'text-gray-500' : 'text-gray-500'">通过率</span>
        <span class="text-[13px] font-din" :class="data.stats.pass_rate > 90 ? 'text-green-600' : 'text-yellow-600'">{{ data.stats.pass_rate }}%</span>
      </div>
      <!-- Progress Bar -->
      <div class="flex gap-1 h-1.5 mt-1">
        <div class="bg-green-500 rounded-l-full" :style="{ width: `${data.stats.pass_rate}%` }"></div>
        <div class="bg-red-500 rounded-r-full flex-1"></div>
      </div>
      <div class="flex justify-between text-[10px] mt-1">
        <span class="text-[12px] font-din text-green-600">{{ data.stats.passed }} 通过</span>
        <span class="text-[12px] font-din text-red-500">{{ data.stats.failed }} 失败</span>
      </div>
    </div>
    
    <!-- Handles -->
    <Handle type="target" :position="Position.Left" class="!w-2 !h-2 !bg-blue-500 !border-0" />
    <Handle type="source" :position="Position.Right" class="!w-2 !h-2 !bg-blue-500 !border-0" />
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
