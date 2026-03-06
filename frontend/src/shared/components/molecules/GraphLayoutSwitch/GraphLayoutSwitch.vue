<template>
    <div class="absolute top-4 right-4 z-10 flex gap-2 bg-white/80 p-1 rounded-lg border border-gray-200 shadow-sm backdrop-blur-sm">
      <a-tooltip title="力导向布局 (Force)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === 'force' }"
          @click="$emit('switchLayout', 'force')"
        >
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 16.5A4.5 4.5 0 1 1 12 7.5a4.5 4.5 0 0 1 0 9zm0-13.5v4.5m0 9v4.5M7.5 12H3m18 0h-4.5"/></svg>
          </template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="网格布局 (Grid)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === 'grid' }"
          @click="$emit('switchLayout', 'grid')"
        >
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          </template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="环形布局 (Circle)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === 'circle' }"
          @click="$emit('switchLayout', 'circle')"
        >
          <template #icon>
             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
          </template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="3D 视图 (3D)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === '3d' }"
          @click="$emit('switchLayout', '3d')"
        >
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </template>
        </a-button>
      </a-tooltip>
    </div>
</template>

<script setup lang="ts">
import type { IGraphLayoutSwitchProps } from './types';

defineProps<IGraphLayoutSwitchProps>();
defineEmits(['switchLayout']);
</script>
