<template>
  <div class="h-full flex flex-col bg-slate-50 relative">
    <div v-if="showHeader" class="bg-white px-4 py-3 border-b border-slate-100 flex justify-between items-center shadow-sm z-10">
        <div class="flex items-center gap-2 min-w-0">
           <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
               <FileTextOutlined class="text-emerald-600" />
           </div>
           <div class="min-w-0">
              <div class="text-sm font-bold text-slate-800 leading-none">文档空间</div>
              <div class="mt-1 text-xs text-slate-400 truncate">共 {{ documents.length }} 篇</div>
           </div>
        </div>
        
        <button
           v-if="documents.length"
           class="text-xs px-2 py-1 rounded bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
           @click="clearDocs"
        >
           清空
        </button>
    </div>

    <div class="flex-1 min-h-0 overflow-hidden bg-white">
        <ArtifactEditor
            v-if="currentDoc"
            :value="currentDoc.content"
            language="markdown"
            :read-only="true"
            class="h-full w-full"
        />
        <div v-else class="h-full w-full">
            <div v-if="store.isRunning" class="h-full w-full p-8 flex flex-col justify-center">
                 <a-skeleton active :paragraph="{ rows: 8 }" />
            </div>
            <EmptyState v-else />
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import ArtifactEditor from '@/features/workflow/components/editor/ArtifactEditor.vue';
import EmptyState from '@/features/workflow/components/EmptyState.vue';
import { FileTextOutlined } from '@ant-design/icons-vue';

defineProps({
    showHeader: { type: Boolean, default: true }
});

const store = useWorkflowStore();
const documents = computed(() => store.documents);
const selectedId = ref('');

const currentDoc = computed(() => documents.value.find(d => d.id === selectedId.value));

watch(() => documents.value.length, (len) => {
    const nv = documents.value;
    if (!len) {
        selectedId.value = '';
        return;
    }
    if (!selectedId.value || !nv.some(d => d.id === selectedId.value)) {
        selectedId.value = nv[0].id;
    }
}, { immediate: true });

const clearDocs = () => {
    store.documents.splice(0, store.documents.length);
    selectedId.value = '';
};


</script>

<style scoped>
</style>
