
<template>
  <div v-if="sources && sources.length > 0" class="source-panel mt-4 border-t border-slate-100 pt-3">
    <!-- Header / Toggle -->
    <div 
      class="flex items-center justify-between cursor-pointer py-2 hover:bg-slate-50 rounded px-2 transition-colors select-none"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex items-center gap-2 text-xs font-semibold text-slate-500">
        <span class="bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded border border-indigo-100">
            {{ isDocMode ? '文档来源' : '图谱/文档片段' }}
        </span>
        <span>共 {{ sources.length }} 条来源</span>
      </div>
      <div class="text-slate-400 transform transition-transform duration-200" :class="{ 'rotate-180': isExpanded }">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>

    <!-- Content Area -->
    <div 
      v-show="isExpanded" 
      class="mt-2 grid gap-2 overflow-hidden transition-all duration-300"
      :class="cardsLayoutClass"
    >
      <!-- Mode A: All Documents (Doc Cards) -->
      <template v-if="isDocMode">
        <div 
          v-for="(item, idx) in sources" 
          :key="item.docId || idx"
          class="doc-card p-3 rounded-lg border border-slate-200 bg-white hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer group relative"
          @click="handleDocClick(item)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
                <div class="w-8 h-8 rounded bg-blue-50 flex items-center justify-center shrink-0 text-blue-500">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </div>
                <div class="min-w-0">
                    <h4 class="text-sm font-medium text-slate-700 truncate group-hover:text-indigo-600 transition-colors" :title="item.title">
                        {{ item.title }}
                    </h4>
                    <div class="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                        <span v-if="item.updateTime">{{ formatDate(item.updateTime) }}</span>
                    </div>
                </div>
            </div>
            <div class="shrink-0 flex flex-col items-end">
                <span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                    {{ (item.score * 100).toFixed(0) }}%
                </span>
            </div>
          </div>
          
          <!-- Summary Tooltip/Popover Logic handled by parent or simple expansion -->
          <div v-if="activeDocId === item.docId" class="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-600 leading-relaxed bg-slate-50/50 p-2 rounded">
             {{ item.summary || '暂无摘要' }}
          </div>
        </div>
      </template>

      <!-- Mode B: Single Document (Chunk Cards) -->
      <template v-else>
        <div 
          v-for="(item, idx) in sources" 
          :key="item.chunkId || idx"
          class="chunk-card p-3 rounded-lg border border-slate-200 bg-white hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer group relative"
          @click="handleChunkClick(item)"
          @mouseenter="hoveredChunkId = item.chunkId"
          @mouseleave="hoveredChunkId = null"
        >
          <div class="flex justify-between items-start mb-1">
            <div class="flex items-center gap-1.5">
                <span class="w-5 h-5 flex items-center justify-center bg-indigo-100 text-indigo-600 text-[10px] font-bold rounded">
                    #{{ item.chunkId || idx + 1 }}
                </span>
                <span v-if="item.pageNo" class="text-[10px] text-slate-400 bg-slate-100 px-1.5 rounded">
                    P{{ item.pageNo }}
                </span>
            </div>
            <span class="text-[10px] font-medium text-slate-400">
                Sim: {{ (item.score || 0).toFixed(2) }}
            </span>
          </div>
          
          <p class="text-xs text-slate-600 line-clamp-3 leading-relaxed mb-0 group-hover:text-slate-800">
            {{ item.text || item.content }}
          </p>

          <!-- Hover Hint -->
          <div 
            v-if="hoveredChunkId === item.chunkId" 
            class="absolute inset-0 bg-indigo-900/5 backdrop-blur-[1px] rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <span class="bg-white text-indigo-600 text-xs font-medium px-3 py-1.5 rounded-full shadow-sm border border-indigo-100 flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
                </svg>
                点击定位图谱节点
            </span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import dayjs from 'dayjs';

const props = defineProps({
  sources: {
    type: Array,
    default: () => []
  },
  // 'doc' (all docs) or 'chunk' (single doc)
  // If not provided, inferred from data
  mode: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['locate-node', 'show-doc-summary']);

const isExpanded = ref(true);
const activeDocId = ref(null);
const hoveredChunkId = ref(null);

const isDocMode = computed(() => {
  if (props.mode) return props.mode === 'doc';
  // Infer: if first item has 'chunkId' or 'text', it's chunk mode. If 'title' and 'docId', it's doc mode.
  if (props.sources && props.sources.length > 0) {
    const first = props.sources[0];
    // Check for chunk-specific fields
    if (first.chunkId !== undefined || first.nodeId !== undefined || first.source === 'vector' || first.source === 'graph') {
        // However, 'vector' source in backend has 'title' too.
        // Let's look for specific requirement keys
        // All Docs: docId, title, summary, score, updateTime
        // Single Doc: chunkId, docId, nodeId, text, score, pageNo
        if (first.chunkId !== undefined || first.nodeId !== undefined) return false;
        if (first.docId !== undefined && first.summary !== undefined && !first.text) return true;
    }
  }
  return false;
});

const cardsLayoutClass = computed(() => {
  return isDocMode.value ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
});

const handleDocClick = (item) => {
    if (activeDocId.value === item.docId) {
        activeDocId.value = null;
    } else {
        activeDocId.value = item.docId;
    }
    emit('show-doc-summary', item);
};

const handleChunkClick = (item) => {
    emit('locate-node', item);
};

const formatDate = (ts) => {
    if (!ts) return '';
    return dayjs(ts).format('YYYY-MM-DD');
};
</script>

<style scoped>
.source-panel {
    animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
