<template>
    <div v-if="selectedNodeData" class="absolute bottom-4 left-4 z-20 w-72 bg-white/90 dark:bg-slate-900/90 p-3 rounded-xl border border-border dark:border-slate-700/50 shadow-2xl backdrop-blur-md max-h-[70%] flex flex-col transition-all duration-300">
        <div class="flex justify-between items-center mb-2 flex-shrink-0 border-b border-slate-100 dark:border-slate-800 pb-2">
            <h3 class="font-bold text-slate-800 dark:text-slate-100 text-base truncate pr-2" :title="selectedNodeData.name">{{ selectedNodeData.name }}</h3>
            <button @click="$emit('close')" class="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="flex-shrink-0 mb-3 px-1">
            <span class="text-[10px] text-primary dark:text-blue-300 bg-primary/5 dark:bg-blue-500/20 px-2 py-0.5 rounded-full font-medium border border-primary/10 dark:border-blue-500/30">
                {{ selectedNodeData.type || '未知类型' }}
            </span>
        </div>
        
        <div class="overflow-y-auto custom-scrollbar flex-grow pr-1">
            <div v-if="selectedNodeData.attributes && Object.keys(selectedNodeData.attributes).length > 0" class="space-y-3">
                <div v-for="(val, key) in selectedNodeData.attributes" :key="key" class="group px-1">
                    <!-- Internal / Hidden fields: Ignore anything starting with _ or specific junk keys -->
                    <template v-if="key.startsWith('_') || ['source_content', 'entity_id', 'truncate', 'source_id', 'chunk_id'].includes(key.toLowerCase())"></template>

                    <!-- Chunks / Source IDs (Card Style) -->
                    <template v-else-if="key === 'chunks'">
                        <span class="text-[10px] font-bold text-slate-400/80 dark:text-slate-500 uppercase tracking-wider mb-1.5 block">来源原文 (Chunks)</span>
                        <div class="grid grid-cols-1 gap-1.5">
                            <a-popover v-for="(chunk, idx) in val" :key="idx" placement="right">
                                <template #content>
                                    <div class="max-w-md p-2 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                                        <div class="font-semibold text-primary dark:text-blue-400 mb-2 border-b dark:border-slate-700 pb-1">原文片段 #{{ Number(idx) + 1 }}</div>
                                        {{ chunk.content || '暂无原文内容' }}
                                    </div>
                                </template>
                                <div class="cursor-help bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700 rounded-lg p-2 hover:bg-primary/5 dark:hover:bg-blue-500/10 hover:border-primary/20 dark:hover:border-blue-500/30 transition-all shadow-sm group-hover:shadow-md">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-[10px] font-mono text-slate-400 dark:text-slate-500">ID: {{ chunk.id.substring(0, 8) }}...</span>
                                        <span class="text-[9px] bg-white dark:bg-slate-900 px-1 border border-slate-100 dark:border-slate-700 rounded text-slate-400">#{{ Number(idx) + 1 }}</span>
                                    </div>
                                    <div class="text-[10px] text-slate-600 dark:text-slate-400 line-clamp-2 italic">
                                        {{ chunk.content || '悬停查看原文...' }}
                                    </div>
                                </div>
                            </a-popover>
                        </div>
                    </template>

                    <!-- File Name (Primary focus) - Hide 'file_path' if 'file_name' exists to avoid duplication -->
                    <template v-else-if="key === 'file_name' || (key === 'file_path' && !selectedNodeData.attributes.file_name)">
                        <span class="text-[10px] font-bold text-slate-400/80 dark:text-slate-500 uppercase tracking-wider mb-1 block">来源文件</span>
                        <div class="flex items-center gap-2 text-primary dark:text-blue-300 bg-primary/5 dark:bg-blue-500/10 p-1.5 rounded-lg border border-primary/10 dark:border-blue-500/20">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
                            <span class="text-xs font-medium truncate" :title="val">{{ val }}</span>
                        </div>
                    </template>

                    <!-- Ignore file_path if we are already showing file_name -->
                    <template v-else-if="key === 'file_path' && selectedNodeData.attributes.file_name"></template>

                    <!-- Time -->
                    <template v-else-if="isDateKey(key)">
                        <span class="text-[10px] font-bold text-slate-400/80 dark:text-slate-500 uppercase tracking-wider mb-0.5 block">{{ key === 'created_at' ? '创建时间' : (key === 'updated_at' ? '更新时间' : key) }}</span>
                        <span class="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            {{ formatDate(val) }}
                        </span>
                    </template>

                    <!-- Other fields -->
                    <template v-else>
                        <span class="text-[10px] font-bold text-slate-400/80 dark:text-slate-500 uppercase tracking-wider mb-0.5 block">{{ key }}</span>
                        <span class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed break-words block">{{ val }}</span>
                    </template>
                </div>
            </div>
            <div v-else class="text-center py-8">
                <div class="text-slate-200 dark:text-slate-700 mb-2">
                    <svg class="mx-auto" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/><circle cx="12" cy="15" r="3"/></svg>
                </div>
                <div class="text-xs text-slate-400 dark:text-slate-600">暂无属性信息</div>
            </div>

            <!-- Related Nodes Section -->
            <div v-if="relatedNodes && relatedNodes.length > 0" class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <h4 class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">关联节点 ({{ relatedNodes.length }})</h4>
                <div class="grid grid-cols-1 gap-1.5">
                    <div 
                        v-for="node in sortedRelatedNodes" 
                        :key="node.id" 
                        class="flex items-center justify-between p-1.5 rounded-lg bg-slate-50/50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer group"
                        @click="$emit('select-node', node.id)"
                    >
                        <div class="flex items-center gap-2 overflow-hidden">
                            <span class="w-1.5 h-1.5 rounded-full flex-shrink-0 ring-2 ring-white dark:ring-slate-900" :style="{ backgroundColor: node.color || '#ccc' }"></span>
                            <span class="text-xs text-slate-700 dark:text-slate-300 truncate font-medium group-hover:text-primary dark:group-hover:text-blue-400 transition-colors">{{ node.name || node.id }}</span>
                        </div>
                        <span class="text-[9px] px-1.5 py-0.5 rounded-md bg-slate-200/50 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 flex-shrink-0">{{ node.type }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { IGraphNodeDetailsProps } from './types';
import dayjs from 'dayjs';

const props = defineProps<IGraphNodeDetailsProps>();
defineEmits(['close', 'select-node']);

const getTime = (n: any) => {
    const ts = n.timestamp || n.created_at || (n.metadata && n.metadata.created_at) || n.updated_at;
    if (ts) return new Date(ts).getTime();
    return 0;
};

const sortedRelatedNodes = computed(() => {
    if (!props.relatedNodes) return [];
    
    return [...props.relatedNodes].sort((a, b) => {
        // Prioritize timestamp/created_at
        const timeA = getTime(a);
        const timeB = getTime(b);
        if (timeA && timeB) return timeB - timeA; // Descending
        if (timeA) return -1;
        if (timeB) return 1;
        
        // Fallback to ID or Name
        return (a.name || a.id).localeCompare(b.name || b.id);
    }).slice(0, 5);
});

const formatDate = (val: any) => {
    if (!val) return val;
    // Handle numeric timestamps
    if (typeof val === 'number') {
        // 10 digits = seconds (e.g. 1700000000)
        if (String(val).length === 10) {
            return dayjs.unix(val).format('YYYY-MM-DD HH:mm:ss');
        }
        // 13 digits = milliseconds
        if (String(val).length === 13) {
            return dayjs(val).format('YYYY-MM-DD HH:mm:ss');
        }
    }
    // Handle string dates
    const d = dayjs(val);
    if (d.isValid() && (typeof val === 'string' && val.length > 4)) { // Avoid formatting short numbers/strings as dates
        return d.format('YYYY-MM-DD HH:mm:ss');
    }
    return val;
};

const isDateKey = (key: string) => {
    const k = key.toLowerCase();
    return k === 'created_at' || k === 'updated_at' || k.endsWith('_time') || k.endsWith('_date') || k === 'date';
};
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
