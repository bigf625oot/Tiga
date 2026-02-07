<template>
  <div class="graph-toolbar" role="toolbar" aria-label="Graph tools">
    <button class="tool-btn" @click="showTools = !showTools" aria-label="切换工具栏" title="切换工具栏">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4V6zm0 5h10v2H4v-2zm0 5h16v2H4v-2z"/></svg>
    </button>
    
    <template v-if="showTools">
        <button class="tool-btn" :disabled="fullscreen" @click="$emit('enterFullscreen')" aria-label="最大化" title="最大化 (F)">
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M4 4h7v2H6v5H4V4zm10 0h6v6h-2V6h-4V4zm6 10v6h-6v-2h4v-4h2zM4 14h2v4h4v2H4v-6z"/></svg>
        </button>
        <button v-show="fullscreen" class="tool-btn" @click="$emit('exitFullscreen')" aria-label="最小化" title="最小化 (Esc)">
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M6 6h4v2H8v2H6V6zm10 0h2v4h-2V8h-2V6h2zM6 14h2v2h2v2H6v-4zm10 0h2v4h-4v-2h2v-2z"/></svg>
        </button>
        <button class="tool-btn" :disabled="!selectedNodeId" @click="$emit('focusOnSelected')" aria-label="定位到选中" title="地图定位 (G)">
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 8a4 4 0 1 1 0 8a4 4 0 0 1 0-8m0-6a1 1 0 0 1 1 1v2.06a8 8 0 0 1 6.94 6.94H22a1 1 0 1 1 0 2h-2.06a8 8 0 0 1-6.94 6.94V22a1 1 0 1 1-2 0v-2.06A8 8 0 0 1 4.06 14H2a1 1 0 1 1 0-2h2.06A8 8 0 0 1 11 5.06V3a1 1 0 0 1 1-1Z"/></svg>
        </button>
        <button class="tool-btn" @click="$emit('zoomIn')" aria-label="放大" title="放大 (Ctrl +)">
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M11 11V6h2v5h5v2h-5v5h-2v-5H6v-2h5Z"/></svg>
        </button>
        <button class="tool-btn" @click="$emit('zoomOut')" aria-label="缩小" title="缩小 (Ctrl -)">
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M6 11h12v2H6z"/></svg>
        </button>
        
        <!-- Extra Tools Slot -->
        <slot name="extra-tools"></slot>

        <span class="zoom-indicator" :aria-label="`缩放比例 ${Math.round(scale*100)}%`">{{ Math.round(scale*100) }}%</span>
        
        <template v-if="showScopeToggle">
            <button
                class="px-2 py-0.5 text-[11px] transition-all ml-1"
                :class="scope === 'doc' ? 'bg-blue-600 text-white' : 'text-[#2a2f3c]'"
                @click="$emit('switchScope', 'doc')"
                title="当前文档"
            >当前文档</button>
            <button
                class="px-2 py-0.5 text-[11px] transition-all"
                :class="scope === 'global' ? 'bg-blue-600 text-white' : 'text-[#2a2f3c]'"
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

defineProps<IGraphToolbarProps>();
defineEmits(['enterFullscreen', 'exitFullscreen', 'focusOnSelected', 'zoomIn', 'zoomOut', 'switchScope']);

const showTools = ref(true);
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
