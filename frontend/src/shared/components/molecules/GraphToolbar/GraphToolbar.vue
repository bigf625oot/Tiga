<template>
  <div class="graph-toolbar dark:bg-slate-800/90 dark:border-slate-700 transition-colors" role="toolbar" aria-label="Graph tools">
    <!-- Search Bar -->
    <div v-if="showSearch" class="absolute bottom-full right-0 mb-2 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 p-2 w-64 flex gap-2">
        <input 
            v-model="searchQuery"
            @keyup.enter="handleSearch"
            type="text" 
            placeholder="搜索节点..." 
            class="flex-1 px-2 py-1 text-sm border dark:border-slate-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 bg-transparent dark:text-slate-200"
            autofocus
        />
        <button 
            @click="handleSearch"
            class="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 dark:hover:bg-blue-600 transition-colors"
        >
            搜索
        </button>
    </div>

    <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="showTools = !showTools" aria-label="切换工具栏" title="切换工具栏">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
    </button>
    
    <template v-if="showTools">
        <!-- Extra Tools Slot -->
        <slot name="extra-tools"></slot>

        <!-- Theme Toggle -->
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="toggleTheme" aria-label="切换主题" title="切换主题">
            <!-- Sun Icon (for Dark Mode) -->
            <svg v-if="!isLightMode" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            <!-- Moon Icon (for Light Mode) -->
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>

        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" :disabled="fullscreen" @click="$emit('enterFullscreen')" aria-label="最大化" title="最大化 (F)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
        </button>
        <button v-show="fullscreen" class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('exitFullscreen')" aria-label="最小化" title="最小化 (Esc)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>
        </button>
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" :disabled="!selectedNodeId" @click="$emit('focusOnSelected')" aria-label="定位到选中" title="地图定位 (G)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </button>
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('zoomIn')" aria-label="放大" title="放大 (Ctrl +)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        </button>
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('zoomOut')" aria-label="缩小" title="缩小 (Ctrl -)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13H5v-2h14v2z"/></svg>
        </button>
        
        <span class="zoom-indicator dark:text-slate-400" :aria-label="`缩放比例 ${Math.round(scale*100)}%`">{{ Math.round(scale*100) }}%</span>
        
        <template v-if="showScopeToggle">
            <button
                class="px-2 py-0.5 text-[11px] transition-all ml-1 rounded dark:border dark:border-slate-600"
                :class="scope === 'doc' ? 'bg-primary text-white dark:bg-blue-600 dark:border-blue-500' : 'text-[#2a2f3c] dark:text-slate-300 dark:hover:bg-slate-700'"
                @click="$emit('switchScope', 'doc')"
                title="当前文档"
            >当前文档</button>
            <button
                class="px-2 py-0.5 text-[11px] transition-all rounded dark:border dark:border-slate-600"
                :class="scope === 'global' ? 'bg-primary text-white dark:bg-blue-600 dark:border-blue-500' : 'text-[#2a2f3c] dark:text-slate-300 dark:hover:bg-slate-700'"
                @click="$emit('switchScope', 'global')"
                title="全部文档"
            >全部文档</button>
        </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { IGraphToolbarProps } from './types';
import { useTheme } from '@/composables/useTheme';

const { isLightMode, toggleTheme } = useTheme();

defineProps<IGraphToolbarProps>();
const emit = defineEmits(['enterFullscreen', 'exitFullscreen', 'focusOnSelected', 'zoomIn', 'zoomOut', 'switchScope', 'search']);

const showTools = ref(true);
const showSearch = ref(false);
const searchQuery = ref('');

const handleSearch = () => {
    if (searchQuery.value.trim()) {
        emit('search', searchQuery.value);
        // Optional: close search bar after search?
        // showSearch.value = false;
    }
};
</script>

<style scoped>
.graph-toolbar {
  position: absolute;
  right: 8px;
  bottom: 8px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: rgba(255,255,255,0.9);
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  z-index: 10;
}
.tool-btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #2a2f3c;
  background: #f3f4f6;
  transition: all .2s ease;
  cursor: pointer;
}
.tool-btn:hover { background: #e5e6eb }
.tool-btn:disabled { opacity: .4; cursor: not-allowed }
.zoom-indicator {
  font-size: 12px;
  color: #666;
  min-width: 36px;
  text-align: right;
}
</style>
