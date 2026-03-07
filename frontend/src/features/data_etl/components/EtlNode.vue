<template>
  <div 
    class="rounded-lg border shadow-lg p-4 w-56 transition-all group"
    :class="[
      selected ? 'ring-2 ring-blue-500' : '',
      isLightMode 
        ? 'bg-white border-border hover:shadow-md' 
        : 'bg-[#1F2937] border-gray-700 hover:border-gray-600'
    ]"
  >
    <!-- Header -->
    <div class="flex items-start gap-4 mb-2">
      <!-- Icon Box -->
      <div 
        class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 shadow-sm"
        :class="iconBgClass"
      >
        <component :is="iconComponent" class="w-6 h-6" :class="iconTextClass" />
      </div>

      <!-- Title -->
      <div class="flex-1 min-w-0">
        <div class="font-semibold text-[14px] truncate" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ data.label }}</div>
        <div class="text-[11px] font-medium uppercase tracking-wide mt-0.5" :class="categoryTextClass">{{ data.category }}</div>
      </div>

      <!-- Status Indicator (Optional) -->
      <div v-if="data.status" class="flex items-center gap-1">
        <svg class="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span class="text-[10px] font-semibold text-green-500">OK</span>
      </div>
    </div>

    <!-- Handles -->
    <Handle type="target" :position="Position.Left" class="!w-2 !h-2 !bg-gray-400 !border-0 hover:!bg-blue-500 transition-colors" />
    <Handle type="source" :position="Position.Right" class="!w-2 !h-2 !bg-gray-400 !border-0 hover:!bg-blue-500 transition-colors" />
    
    <!-- Bottom Metrics (Optional) -->
    <div v-if="data.metrics" class="mt-2 pt-2 border-t flex justify-between items-center text-[10px]" :class="isLightMode ? 'border-gray-100' : 'border-gray-700'">
        <span :class="isLightMode ? 'text-gray-500' : 'text-gray-400'">{{ data.metrics.label }}</span>
        <span class="font-din font-semibold" :class="metricColorClass">{{ data.metrics.value }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import { Handle, Position, type NodeProps } from '@vue-flow/core';
import { useTheme } from '@/composables/useTheme';

const props = defineProps<NodeProps>();
const { isLightMode } = useTheme();

// Icons
const IconDatabase = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" })
]);
const IconGlobe = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" })
]);
const IconServer = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" })
]);
const IconSparkles = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 3.214L13 21l-2.286-6.857L5 12l5.714-3.214L13 3z" })
]);
const IconFilter = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" })
]);
const IconShield = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" })
]);
const IconDocument = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 011.414.586l5.414 5.414a1 1 0 01.586 1.414V19a2 2 0 01-2 2z" })
]);
const IconGraph = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
  h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" }) 
  // Simplified graph icon
]);

const iconComponent = computed(() => {
  switch(props.data.icon) {
    case 'sftp': return IconServer;
    case 'crawler': return IconGlobe;
    case 'database': return IconDatabase;
    case 'llm': return IconSparkles;
    case 'filter': return IconFilter;
    case 'shield': return IconShield;
    case 'document': return IconDocument;
    case 'graph': return IconGraph; // Neo4j
    default: return IconDocument;
  }
});

const categoryColor = computed(() => {
  switch(props.data.category?.toLowerCase()) {
    case 'extract': return 'blue';
    case 'transform': return 'purple';
    case 'load': return 'green';
    default: return 'gray';
  }
});

const iconBgClass = computed(() => {
  const color = categoryColor.value;
  if (isLightMode.value) {
    if (color === 'blue') return 'bg-blue-500 text-white shadow-blue-200';
    if (color === 'purple') return 'bg-purple-500 text-white shadow-purple-200';
    if (color === 'green') return 'bg-green-500 text-white shadow-green-200';
    return 'bg-gray-500 text-white';
  } else {
    // Dark mode: use vibrant backgrounds but slightly muted/adjusted for dark theme if needed, or keep same for "pop"
    if (color === 'blue') return 'bg-primary text-white';
    if (color === 'purple') return 'bg-purple-600 text-white';
    if (color === 'green') return 'bg-green-600 text-white';
    return 'bg-gray-600 text-white';
  }
});

const iconTextClass = computed(() => '');

const categoryTextClass = computed(() => {
  const color = categoryColor.value;
  if (color === 'blue') return 'text-blue-500';
  if (color === 'purple') return 'text-purple-500';
  if (color === 'green') return 'text-green-500';
  return 'text-gray-500';
});

const metricColorClass = computed(() => {
  if (props.data.metrics?.trend === 'up') return 'text-green-500';
  if (props.data.metrics?.trend === 'down') return 'text-red-500';
  return isLightMode.value ? 'text-gray-700' : 'text-gray-300';
});

</script>
