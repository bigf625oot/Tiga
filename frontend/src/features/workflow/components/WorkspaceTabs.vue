<template>
  <div class="h-full flex flex-col bg-background overflow-hidden">
    <div class="bg-background border-b px-4 py-2">
      <div class="flex items-center justify-between gap-4">
        <Tabs v-model="activeTab" class="w-full">
          <div class="flex items-center justify-between w-full">
            <TabsList class="grid w-auto grid-cols-3 h-10">
              <TabsTrigger value="task" class="px-4 gap-2 data-[state=active]:bg-background">
                <LayoutDashboard class="w-4 h-4" />
                <span>任务空间</span>
                <Badge 
                  :variant="store.isRunning ? 'default' : 'secondary'"
                  class="ml-1 px-1.5 py-0 h-5 text-[10px] font-normal"
                >
                  {{ store.isRunning ? '执行中' : '空闲' }}
                </Badge>
              </TabsTrigger>
              
              <TabsTrigger value="doc" class="px-4 gap-2 data-[state=active]:bg-background">
                <FileText class="w-4 h-4" />
                <span>文档空间</span>
                <Badge 
                  v-if="store.documents.length" 
                  variant="secondary"
                  class="ml-1 px-1.5 py-0 h-5 text-[10px] font-normal bg-emerald-100 text-emerald-700 hover:bg-emerald-100/80 dark:bg-emerald-900/30 dark:text-emerald-400"
                >
                  {{ store.documents.length }}
                </Badge>
              </TabsTrigger>
              
              <TabsTrigger value="graph" class="px-4 gap-2 data-[state=active]:bg-background">
                <Share2 class="w-4 h-4" />
                <span>知识图谱</span>
              </TabsTrigger>
            </TabsList>

            <div class="flex items-center gap-2 shrink-0">
              <Button
                v-if="activeTab === 'doc' && store.documents.length"
                variant="ghost"
                size="sm"
                class="h-8 px-2 text-xs text-muted-foreground hover:text-foreground"
                @click="clearDocs"
              >
                <Trash2 class="w-3.5 h-3.5 mr-1.5" />
                清空
              </Button>
            </div>
          </div>
        </Tabs>
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-hidden bg-background relative">
      <div v-show="activeTab === 'task'" class="h-full">
        <TaskPanel
          ref="taskPanelRef"
          embedded
          :showEmbeddedHeader="true"
          :sessionId="sessionId"
          :agentName="agentName"
          :isWorkflowMode="isWorkflowMode"
          :attachmentsCount="attachmentsCount"
        />
      </div>

      <div v-show="activeTab === 'doc'" class="h-full">
        <DocumentPanel ref="documentPanelRef" :showHeader="false" />
      </div>

      <div v-if="activeTab === 'graph'" class="h-full relative">
        <div v-if="!hasKnowledgeBase" class="h-full flex flex-col items-center justify-center text-muted-foreground">
            <Database class="w-12 h-12 mb-4 opacity-50" />
            <p>当前智能体未绑定知识库</p>
        </div>
        <GraphViewer 
            v-else
            ref="graphViewerRef"
            :nodes="graphNodes" 
            :edges="graphEdges" 
            :loading="graphLoading"
            :scope="graphScope"
            @nodeClick="handleNodeClick"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import TaskPanel from '@/features/workflow/components/TaskPanel.vue';
import DocumentPanel from '@/features/workflow/components/DocumentPanel.vue';
import GraphViewer from '@/shared/components/organisms/GraphViewer/GraphViewer.vue';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, FileText, Share2, Trash2, Database } from 'lucide-vue-next';

const props = defineProps({
  sessionId: { type: String, default: '' },
  agentName: { type: String, default: '' },
  isWorkflowMode: { type: Boolean, default: true },
  attachmentsCount: { type: Number, default: 0 }
});

const store = useWorkflowStore();
const activeTab = ref('task');
const taskPanelRef = ref(null);
const documentPanelRef = ref(null);
const graphViewerRef = ref(null);

// Graph State
const graphNodes = ref({});
const graphEdges = ref({});
const graphLoading = ref(false);
const currentDocId = ref(null);
const isLocating = ref(false);

const graphScope = computed(() => currentDocId.value ? 'doc' : 'global');

watch(() => store.documents.length, (len, prev) => {
  if (len > prev) activeTab.value = 'doc';
});

watch(activeTab, (val) => {
    if (val === 'graph' && !isLocating.value) {
        // If graph is empty or we haven't loaded anything yet, load global graph
        if (Object.keys(graphNodes.value).length === 0) {
            loadGraph(null);
        }
    }
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

watch(() => props.hasKnowledgeBase, (val) => {
  if (!val) {
    graphNodes.value = {};
    graphEdges.value = {};
  } else if (activeTab.value === 'graph') {
    loadGraph(null);
  }
});

// Graph Methods
const loadGraph = async (docId = null) => {
    // If no knowledge base and trying to load global graph (docId is null), skip
    if (!docId && !props.hasKnowledgeBase) {
        graphNodes.value = {};
        graphEdges.value = {};
        return;
    }

    // Don't reload if we are already on the same doc (or both null)
    // Exception: if we want to force reload, we might need another param or method
    if (currentDocId.value === docId && Object.keys(graphNodes.value).length > 0) return;
    
    graphLoading.value = true;
    try {
        const url = docId 
            ? `/api/v1/knowledge/${docId}/graph`
            : `/api/v1/knowledge/graph`;
            
        const res = await fetch(url);
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
    isLocating.value = true;
    activeTab.value = 'graph';
    try {
        await loadGraph(docId || null);
        
        // Wait for view switch and data load
        setTimeout(() => {
            graphViewerRef.value?.focusNode(nodeId);
        }, 100);
    } finally {
        isLocating.value = false;
    }
};

const handleNodeClick = (nodeId) => {
    // Handle side panel or info
    console.log("Node clicked:", nodeId);
};

const openDocSpace = (docId) => {
    activeTab.value = 'doc';
    if (docId) {
        documentPanelRef.value?.selectDoc?.(docId);
    }
};

defineExpose({
  openTaskLogs,
  locateNode,
  openDocSpace
});
</script>
