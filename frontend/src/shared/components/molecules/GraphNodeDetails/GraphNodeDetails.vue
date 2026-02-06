<template>
    <div v-if="selectedNodeData" class="absolute bottom-4 left-4 z-20 w-80 bg-white p-4 rounded-lg border border-gray-200 shadow-xl backdrop-blur-md max-h-[80%] flex flex-col">
        <div class="flex justify-between items-start mb-2 flex-shrink-0">
            <h3 class="font-bold text-gray-800 text-lg">{{ selectedNodeData.name }}</h3>
            <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 p-1">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="flex-shrink-0 mb-3">
            <span class="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded font-medium border border-blue-100">
                {{ selectedNodeData.type || '未知类型' }}
            </span>
        </div>
        
        <div class="overflow-y-auto custom-scrollbar flex-grow pr-2">
            <div v-if="selectedNodeData.attributes && Object.keys(selectedNodeData.attributes).length > 0" class="space-y-4">
                <div v-for="(val, key) in selectedNodeData.attributes" :key="key" class="group">
                    <!-- Internal / Hidden fields: Ignore anything starting with _ or specific junk keys -->
                    <template v-if="key.startsWith('_') || ['source_content', 'entity_id', 'truncate', 'source_id', 'chunk_id'].includes(key.toLowerCase())"></template>

                    <!-- Chunks / Source IDs (Card Style) -->
                    <template v-else-if="key === 'chunks'">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 block">来源原文 (Chunks)</span>
                        <div class="grid grid-cols-1 gap-2">
                            <a-popover v-for="(chunk, idx) in val" :key="idx" placement="right">
                                <template #content>
                                    <div class="max-w-md p-2 text-xs leading-relaxed text-gray-700">
                                        <div class="font-bold text-blue-600 mb-2 border-b pb-1">原文片段 #{{ Number(idx) + 1 }}</div>
                                        {{ chunk.content || '暂无原文内容' }}
                                    </div>
                                </template>
                                <div class="cursor-help bg-slate-50 border border-slate-200 rounded-md p-2 hover:bg-blue-50 hover:border-blue-300 transition-all shadow-sm">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-[10px] font-mono text-slate-400">ID: {{ chunk.id.substring(0, 8) }}...</span>
                                        <span class="text-[10px] bg-white px-1 border border-slate-200 rounded text-slate-500">#{{ Number(idx) + 1 }}</span>
                                    </div>
                                    <div class="text-[11px] text-slate-600 line-clamp-2 italic">
                                        {{ chunk.content || '悬停查看原文...' }}
                                    </div>
                                </div>
                            </a-popover>
                        </div>
                    </template>

                    <!-- File Name (Primary focus) - Hide 'file_path' if 'file_name' exists to avoid duplication -->
                    <template v-else-if="key === 'file_name' || (key === 'file_path' && !selectedNodeData.attributes.file_name)">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1 block">来源文件</span>
                        <div class="flex items-center gap-2 text-blue-600 bg-blue-50/50 p-2 rounded border border-blue-100">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
                            <span class="text-sm font-medium truncate" :title="val">{{ val }}</span>
                        </div>
                    </template>

                    <!-- Ignore file_path if we are already showing file_name -->
                    <template v-else-if="key === 'file_path' && selectedNodeData.attributes.file_name"></template>

                    <!-- Time -->
                    <template v-else-if="key === 'created_at'">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1 block">创建时间</span>
                        <span class="text-sm text-gray-600 flex items-center gap-2">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            {{ val }}
                        </span>
                    </template>

                    <!-- Other fields -->
                    <template v-else>
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1 block">{{ key }}</span>
                        <span class="text-sm text-gray-700 leading-snug break-words">{{ val }}</span>
                    </template>
                </div>
            </div>
            <div v-else class="text-center py-10">
                <div class="text-gray-300 mb-2">
                    <svg class="mx-auto" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/><circle cx="12" cy="15" r="3"/></svg>
                </div>
                <div class="text-sm text-gray-400">暂无属性信息</div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { IGraphNodeDetailsProps } from './types';

defineProps<IGraphNodeDetailsProps>();
defineEmits(['close']);
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #999;
}
/* Ensure scrollbar is always visible in the container */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #ccc #f1f1f1;
}
</style>
