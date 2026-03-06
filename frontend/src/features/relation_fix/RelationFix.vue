<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header Banner (Unified Style) -->
    <div class="px-10 pt-12 pb-6 flex-shrink-0">
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">关系修复</h2>
          <p class="text-[#86868B] text-lg font-medium">检测并修复知识图谱中的关系缺失。</p>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex overflow-hidden border-t border-slate-200">
      <!-- Left Sidebar (Editor) -->
      <div class="w-96 flex-shrink-0 border-r border-slate-200 bg-white z-10 overflow-y-auto custom-scrollbar">
        <RelationEditor 
          :fixes="fixes"
          :currentRelations="currentRelations"
          @search="handleSearch"
          @detect="handleDetect"
          @applyFixes="handleApplyFixes"
          @create="handleCreate"
          @delete="handleDelete"
          @backup="handleBackup"
          @restore="handleRestore"
        />
      </div>

      <!-- Right Content (Graph) -->
      <div class="flex-1 relative bg-slate-50">
        <!-- Skeleton Loading State -->
        <div v-if="loading" class="absolute inset-0 z-30 bg-white p-8 flex flex-col items-center justify-center">
             <div class="w-full h-full max-w-4xl mx-auto flex flex-col gap-8 items-center justify-center opacity-50">
                 <!-- Mock Graph Nodes -->
                 <div class="relative w-full h-96">
                     <div class="absolute top-1/2 left-1/2 w-20 h-20 bg-slate-200 rounded-full animate-pulse -translate-x-1/2 -translate-y-1/2"></div>
                     <div class="absolute top-1/4 left-1/4 w-12 h-12 bg-slate-200 rounded-full animate-pulse"></div>
                     <div class="absolute bottom-1/4 right-1/4 w-14 h-14 bg-slate-200 rounded-full animate-pulse"></div>
                     <div class="absolute top-1/3 right-1/3 w-10 h-10 bg-slate-200 rounded-full animate-pulse"></div>
                     <div class="absolute bottom-1/3 left-1/3 w-16 h-16 bg-slate-200 rounded-full animate-pulse"></div>
                 </div>
                 <div class="space-y-4 w-64 text-center">
                     <div class="h-4 bg-slate-200 rounded w-3/4 mx-auto animate-pulse"></div>
                     <div class="h-3 bg-slate-200 rounded w-1/2 mx-auto animate-pulse"></div>
                 </div>
             </div>
        </div>

        <GraphViewer
          ref="graphViewerRef"
          :nodes="nodes"
          :edges="edges"
          :loading="false" 
          :show-toolbar="true"
          class="w-full h-full"
          @node-click="handleNodeClick"
        >
          <template #toolbar-extras>
            <button 
              class="w-7 h-7 inline-flex items-center justify-center rounded-md text-[#2a2f3c] bg-gray-100 hover:bg-gray-200 transition-colors cursor-pointer"
              @click="showLogs = !showLogs"
              :class="{ 'bg-blue-100 text-blue-600': showLogs }"
              title="操作日志"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </button>
          </template>
        </GraphViewer>
        
        <!-- Logs Drawer / Overlay -->
        <div v-if="showLogs" class="absolute bottom-16 right-4 w-96 max-h-64 bg-black/80 text-white text-xs p-2 rounded overflow-y-auto font-mono pointer-events-auto shadow-lg z-20">
          <div class="flex justify-between items-center mb-1 pb-1 border-b border-white/20">
              <span class="font-bold">操作日志</span>
              <button @click="loadLogs" class="text-blue-300 hover:text-blue-100">刷新</button>
          </div>
          <div v-if="logs.length === 0" class="text-gray-400 italic p-2 text-center">暂无日志</div>
          <div v-for="(log, i) in logs" :key="i" class="whitespace-pre-wrap">{{ log }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import GraphViewer from '@/shared/components/organisms/GraphViewer/GraphViewer.vue';
import RelationEditor from './components/RelationEditor.vue';
import { relationFixApi, type RelationFix } from './api';

const nodes = ref<Record<string, any>>({});
const edges = ref<Record<string, any>>({});
const loading = ref(false);
const fixes = ref<RelationFix[]>([]);
const logs = ref<string[]>([]);
const showLogs = ref(false);
const graphViewerRef = ref();
const currentNodeId = ref<string>('');

const currentRelations = computed(() => Object.values(edges.value));

const loadLogs = async () => {
  try {
      logs.value = await relationFixApi.getLogs();
  } catch (e) {
      console.error("Failed to load logs", e);
  }
};

const handleSearch = async (query: string) => {
  loading.value = true;
  try {
    const results = await relationFixApi.searchNodes(query);
    if (results.length > 0) {
      // Load first match
      await loadNode(results[0], false); // Don't set global loading inside
    } else {
        alert("未找到相关节点");
    }
  } catch (e) {
      console.error(e);
      alert("搜索失败");
  } finally {
    loading.value = false;
  }
};

const loadNode = async (nodeId: string, setGlobalLoading = true) => {
  if (setGlobalLoading) loading.value = true;
  currentNodeId.value = nodeId;
  try {
    const data = await relationFixApi.getNodeRelations(nodeId);
    
    // Transform to GraphViewer format
    const newNodes: Record<string, any> = {};
    const newEdges: Record<string, any> = {};
    
    data.nodes.forEach(n => {
      newNodes[n.id] = { name: n.label, ...n };
    });
    
    data.edges.forEach((e, idx) => {
      const id = `edge_${idx}`;
      newEdges[id] = {
        source: e.source,
        target: e.target,
        label: e.data?.label || e.data?.description || 'related'
      };
    });
    
    nodes.value = newNodes;
    edges.value = newEdges;
    
    // Focus
    if (graphViewerRef.value) {
        // Wait for update
        setTimeout(() => {
            if (graphViewerRef.value) graphViewerRef.value.focusNode(nodeId);
        }, 300);
    }
  } catch (e) {
    console.error(e);
  } finally {
    if (setGlobalLoading) loading.value = false;
  }
};

const handleDetect = async (mainNode: string, keyword: string) => {
  if (!mainNode || !keyword) {
      alert("请输入主节点和关键词");
      return;
  }
  loading.value = true;
  try {
    // First load the main node to see it
    await loadNode(mainNode, false);
    
    const results = await relationFixApi.detectRelations(mainNode, keyword);
    fixes.value = results;
    if (results.length === 0) {
        alert("未发现可修复的关系");
    }
  } catch (e) {
      console.error(e);
      alert("检测失败");
  } finally {
    loading.value = false;
  }
};

const handleApplyFixes = async (selectedFixes: RelationFix[]) => {
  if (selectedFixes.length === 0) return;
  
  loading.value = true;
  try {
    const res = await relationFixApi.applyFixes(selectedFixes);
    alert(`已修复 ${res.count} 个关系`);
    fixes.value = []; // Clear fixes
    // Reload graph
    if (selectedFixes.length > 0) {
        await loadNode(selectedFixes[0].source, false);
    }
    await loadLogs();
  } catch (e) {
      console.error(e);
      alert("修复失败");
  } finally {
    loading.value = false;
  }
};

const handleCreate = async (source: string, target: string, type: string) => {
  loading.value = true;
  try {
    await relationFixApi.createRelation(source, target, type);
    alert('创建成功');
    await loadNode(source, false);
    await loadLogs();
  } catch (e) {
      console.error(e);
      alert("创建失败");
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (relations: Array<{ source: string, target: string }>) => {
  loading.value = true;
  try {
    const res = await relationFixApi.deleteRelations(relations);
    alert(`已解除 ${res.count} 个关系`);
    if (currentNodeId.value) {
        await loadNode(currentNodeId.value, false);
    }
    await loadLogs();
  } catch (e) {
      console.error(e);
      alert("解除关系失败");
  } finally {
    loading.value = false;
  }
};

const handleBackup = async () => {
  try {
      const res = await relationFixApi.backupGraph();
      alert(`备份已创建: ${res.path}`);
      await loadLogs();
  } catch (e) {
      console.error(e);
      alert("备份失败");
  }
};

const handleRestore = async () => {
  if (confirm('确定要回滚到最近一次备份吗？这将覆盖当前更改。')) {
    loading.value = true;
    try {
        const res = await relationFixApi.restoreBackup();
        if (res.success) {
            alert('回滚成功');
            await loadLogs();
            // Reload current graph if possible
            if (Object.keys(nodes.value).length > 0) {
                 const firstNode = Object.keys(nodes.value)[0];
                 await loadNode(firstNode, false);
            }
        } else {
            alert('回滚失败');
        }
    } catch (e) {
        console.error(e);
        alert("回滚出错");
    } finally {
        loading.value = false;
    }
  }
};

const handleNodeClick = (nodeId: string) => {
    loadNode(nodeId);
};

onMounted(() => {
    loadLogs();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #CBD5E0;
}
</style>
