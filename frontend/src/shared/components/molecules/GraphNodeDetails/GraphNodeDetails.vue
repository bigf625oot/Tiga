<template>
    <div v-if="selectedNodeData" class="absolute bottom-4 left-4 z-20 w-80 bg-white dark:bg-slate-800 p-4 rounded-lg border border-border dark:border-slate-700 shadow-xl backdrop-blur-md max-h-[80%] flex flex-col transition-colors">
        <div class="flex justify-between items-start mb-2 flex-shrink-0">
            <h3 class="font-semibold text-gray-800 dark:text-slate-100 text-lg">{{ selectedNodeData.name }}</h3>
            <button @click="$emit('close')" class="text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 p-1">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="flex-shrink-0 m-4">
            <span class="text-xs text-primary dark:text-blue-400 bg-primary/10 dark:bg-blue-900/30 px-2 py-1 rounded font-medium border border-blue-100 dark:border-blue-800">
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
                        <span class="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2 block">来源原文 (Chunks)</span>
                        <div class="grid grid-cols-1 gap-2">
                            <a-popover v-for="(chunk, idx) in val" :key="idx" placement="right">
                                <template #content>
                                    <div class="max-w-md p-2 text-xs leading-relaxed text-gray-700 dark:text-slate-300">
                                        <div class="font-semibold text-primary dark:text-blue-400 mb-2 border-b dark:border-slate-700 pb-1">原文片段 #{{ Number(idx) + 1 }}</div>
                                        {{ chunk.content || '暂无原文内容' }}
                                    </div>
                                </template>
                                <div class="cursor-help bg-muted/50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md p-2 hover:bg-primary/10 dark:hover:bg-blue-900/30 hover:border-blue-300 dark:hover:border-blue-700 transition-all shadow-sm">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-[10px] font-mono text-muted-foreground dark:text-slate-400">ID: {{ chunk.id.substring(0, 8) }}...</span>
                                        <span class="text-[10px] bg-white dark:bg-slate-800 px-1 border border-slate-200 dark:border-slate-600 rounded text-muted-foreground dark:text-slate-400">#{{ Number(idx) + 1 }}</span>
                                    </div>
                                    <div class="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 italic">
                                        {{ chunk.content || '悬停查看原文...' }}
                                    </div>
                                </div>
                            </a-popover>
                        </div>
                    </template>

                    <!-- File Name (Primary focus) - Hide 'file_path' if 'file_name' exists to avoid duplication -->
                    <template v-else-if="key === 'file_name' || (key === 'file_path' && !selectedNodeData.attributes.file_name)">
                        <span class="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1 block">来源文件</span>
                        <div class="flex items-center gap-2 text-primary dark:text-blue-400 bg-primary/10/50 dark:bg-blue-900/20 p-2 rounded border border-blue-100 dark:border-blue-800">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
                            <span class="text-sm font-medium truncate" :title="val">{{ val }}</span>
                        </div>
                    </template>

                    <!-- Ignore file_path if we are already showing file_name -->
                    <template v-else-if="key === 'file_path' && selectedNodeData.attributes.file_name"></template>

                    <!-- Time -->
                    <template v-else-if="isDateKey(key)">
                        <span class="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1 block">{{ key === 'created_at' ? '创建时间' : (key === 'updated_at' ? '更新时间' : key) }}</span>
                        <span class="text-sm text-gray-600 dark:text-slate-300 flex items-center gap-2">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            {{ formatDate(val) }}
                        </span>
                    </template>

                    <!-- Other fields -->
                    <template v-else>
                        <span class="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1 block">{{ key }}</span>
                        <span class="text-sm text-gray-700 dark:text-slate-300 leading-snug break-words">{{ val }}</span>
                    </template>
                </div>
            </div>
            <div v-else class="text-center py-10">
                <div class="text-gray-300 dark:text-slate-600 mb-2">
                    <svg class="mx-auto" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/><circle cx="12" cy="15" r="3"/></svg>
                </div>
                <div class="text-sm text-gray-400 dark:text-slate-500">暂无属性信息</div>
            </div>

            <!-- Related Nodes Section -->
            <div v-if="relatedNodes && relatedNodes.length > 0" class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
                <h4 class="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">关联节点 ({{ relatedNodes.length }})</h4>
                <div class="grid grid-cols-1 gap-2">
                    <div 
                        v-for="node in sortedRelatedNodes" 
                        :key="node.id" 
                        class="flex items-center justify-between p-2 rounded-md bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors cursor-pointer group"
                        @click="$emit('select-node', node.id)"
                    >
                        <div class="flex items-center gap-2 overflow-hidden">
                            <span class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: node.color || '#ccc' }"></span>
                            <span class="text-sm text-slate-700 dark:text-slate-300 truncate font-medium group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{{ node.name || node.id }}</span>
                        </div>
                        <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 flex-shrink-0">{{ node.type }}</span>
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
