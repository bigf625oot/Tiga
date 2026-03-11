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

        <button
            class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            :class="{ 'bg-blue-500 text-white dark:bg-blue-600': boxSelectionActive }"
            :disabled="currentLayout === '3d'"
            @click="$emit('toggleBoxSelection')"
            aria-label="框选"
            title="框选"
        >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 7a4 4 0 0 1 4-4h3v2H7a2 2 0 0 0-2 2v3H3V7zm16 3V7a2 2 0 0 0-2-2h-3V3h3a4 4 0 0 1 4 4v3h-2zM5 14v3a2 2 0 0 0 2 2h3v2H7a4 4 0 0 1-4-4v-3h2zm16 0v3a4 4 0 0 1-4 4h-3v-2h3a2 2 0 0 0 2-2v-3h2z"/></svg>
        </button>
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('selectAll')" aria-label="全选" title="全选">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 7a2 2 0 0 1 2-2h4v2H5v4H3V7zm16 4V7h-4V5h4a2 2 0 0 1 2 2v4h-2zM5 13v4h4v2H5a2 2 0 0 1-2-2v-4h2zm16 4a2 2 0 0 1-2 2h-4v-2h4v-4h2v4zM8 11h8v2H8v-2z"/></svg>
        </button>
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('clearSelection')" aria-label="清空选择" title="清空选择">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v2H6V6zm4 0h8v2h-8V6zM6 10h2v2H6v-2zm4 0h8v2h-8v-2zM6 14h2v2H6v-2zm4 0h8v2h-8v-2z"/></svg>
        </button>

        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('resetView')" aria-label="重置视图" title="重置视图">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4a8 8 0 1 0 8 8h-2a6 6 0 1 1-6-6V4zm8 0v6h-6l2.2-2.2A7.96 7.96 0 0 1 20 12h2a9.96 9.96 0 0 0-2.93-7.07L20 4z"/></svg>
        </button>
        <button class="tool-btn dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600" @click="$emit('fitToContents')" aria-label="自适应缩放" title="自适应缩放">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M4 9V4h5v2H6v3H4zm14-3h-3V4h5v5h-2V6zM6 18h3v2H4v-5h2v3zm14-3v5h-5v-2h3v-3h2z"/></svg>
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
import { computed, ref } from 'vue';
import type { IGraphToolbarProps } from './types';

const props = defineProps<IGraphToolbarProps>();
const emit = defineEmits(['toggleBoxSelection', 'selectAll', 'clearSelection', 'resetView', 'fitToContents', 'zoomIn', 'zoomOut', 'switchScope', 'search']);

const showTools = ref(true);
const showSearch = ref(false);
const searchQuery = ref('');

const boxSelectionActive = computed(() => !!props.boxSelectionActive);

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
