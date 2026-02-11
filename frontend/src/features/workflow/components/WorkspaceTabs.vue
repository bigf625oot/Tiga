<template>
  <div class="h-full flex flex-col bg-slate-50 overflow-hidden">
    <div class="bg-white px-4 pt-3 border-b border-slate-100">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-5 min-w-0">
          <button
            class="relative pb-3 text-sm font-semibold transition-colors"
            :class="activeTab === 'task' ? 'text-slate-900' : 'text-slate-500 hover:text-slate-700'"
            @click="activeTab = 'task'"
          >
            任务空间
            <span
              class="ml-2 text-[11px] px-2 py-0.5 rounded-full font-medium align-middle"
              :class="store.isRunning ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'"
            >
              {{ store.isRunning ? '执行中' : '空闲' }}
            </span>
            <span
              v-if="activeTab === 'task'"
              class="absolute left-0 right-0 -bottom-[1px] h-0.5 bg-slate-900 rounded"
            ></span>
          </button>

          <button
            class="relative pb-3 text-sm font-semibold transition-colors"
            :class="activeTab === 'doc' ? 'text-slate-900' : 'text-slate-500 hover:text-slate-700'"
            @click="activeTab = 'doc'"
          >
            文档空间
            <span v-if="store.documents.length" class="ml-2 text-[11px] px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 align-middle">
              {{ store.documents.length }}
            </span>
            <span
              v-if="activeTab === 'doc'"
              class="absolute left-0 right-0 -bottom-[1px] h-0.5 bg-slate-900 rounded"
            ></span>
          </button>

          <button
            class="relative pb-3 text-sm font-semibold transition-colors"
            :class="activeTab === 'graph' ? 'text-slate-900' : 'text-slate-500 hover:text-slate-700'"
            @click="activeTab = 'graph'"
          >
            知识图谱
            <span
              v-if="activeTab === 'graph'"
              class="absolute left-0 right-0 -bottom-[1px] h-0.5 bg-slate-900 rounded"
            ></span>
          </button>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <button
            v-if="activeTab === 'doc' && store.documents.length"
            class="text-xs px-2 py-1 rounded bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
            @click="clearDocs"
          >
            清空
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-hidden bg-white">
      <div v-show="activeTab === 'task'" class="h-full">
        <TaskPanel
          ref="taskPanelRef"
          embedded
          :showEmbeddedHeader="false"
          :sessionId="sessionId"
          :agentName="agentName"
          :isWorkflowMode="isWorkflowMode"
          :attachmentsCount="attachmentsCount"
        />
      </div>

      <div v-show="activeTab === 'doc'" class="h-full">
        <DocumentPanel :showHeader="false" />
      </div>

      <div v-if="activeTab === 'graph'" class="h-full relative">
        <GraphViewer 
            ref="graphViewerRef"
            :nodes="graphNodes" 
            :edges="graphEdges" 
            :loading="graphLoading"
            scope="doc"
            @nodeClick="handleNodeClick"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import TaskPanel from '@/features/workflow/components/TaskPanel.vue';
import DocumentPanel from '@/features/workflow/components/DocumentPanel.vue';
import GraphViewer from '@/shared/components/organisms/GraphViewer/GraphViewer.vue';
import { CodeOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  sessionId: { type: String, default: '' },
  agentName: { type: String, default: '' },
  isWorkflowMode: { type: Boolean, default: true },
  attachmentsCount: { type: Number, default: 0 }
});

const store = useWorkflowStore();
const activeTab = ref('task');
const taskPanelRef = ref(null);
const graphViewerRef = ref(null);

// Graph State
const graphNodes = ref({});
const graphEdges = ref({});
const graphLoading = ref(false);
const currentDocId = ref(null);

watch(() => store.documents.length, (len, prev) => {
  if (len > prev) activeTab.value = 'doc';
});

const openTaskLogs = () => {
  taskPanelRef.value?.openLogDrawer?.();
};

const clearDocs = () => {
  store.documents.splice(0, store.documents.length);
  activeTab.value = 'task';
};

watch(() => props.isWorkflowMode, (val) => {
  if (!val) activeTab.value = 'task';
});

// Graph Methods
const loadGraph = async (docId) => {
    if (!docId || currentDocId.value === docId) return;
    graphLoading.value = true;
    try {
        const res = await fetch(`/api/v1/knowledge/graph/${docId}`);
        if (res.ok) {
            const data = await res.json();
            graphNodes.value = data.nodes || {};
            graphEdges.value = data.edges || {};
            currentDocId.value = docId;
        }
    } catch (e) {
        console.error("Failed to load graph", e);
    } finally {
        graphLoading.value = false;
    }
};

const locateNode = async (nodeId, docId) => {
    activeTab.value = 'graph';
    if (docId) {
        await loadGraph(docId);
    }
    // Wait for view switch and data load
    setTimeout(() => {
        graphViewerRef.value?.focusNode(nodeId);
    }, 100);
};

const handleNodeClick = (nodeId) => {
    // Handle side panel or info
    console.log("Node clicked:", nodeId);
};

defineExpose({
  openTaskLogs,
  locateNode
});
</script>
