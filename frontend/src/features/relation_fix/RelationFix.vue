<template>
  <div class="h-full flex flex-col bg-background text-foreground overflow-hidden">
    <!-- Header Banner -->
    <header class="h-14 flex-none px-4 border-b bg-background/95 backdrop-blur flex items-center justify-between z-20">
      <div class="flex items-center gap-4 flex-1">
        <div class="flex items-center gap-3">
          <div class="p-1.5 bg-primary/10 rounded-md">
            <Share2Icon class="h-5 w-5 text-primary" />
          </div>
          <h2 class="text-base font-semibold tracking-tight">图谱治理</h2>
        </div>
        
        <div class="h-4 w-px bg-border/60"></div>
        
        <!-- Global Search -->
        <div class="relative w-full max-w-sm">
          <Popover v-model:open="showSearchSuggestions">
            <PopoverTrigger asChild>
               <div class="relative w-full">
                  <SearchIcon class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" />
                  <Input 
                    v-model="searchQuery"
                    @keyup.enter="handleSearch"
                    placeholder="搜索节点 ID 或名称..." 
                    class="pl-9 pr-9 h-9 text-sm bg-muted/30 focus:bg-background transition-colors"
                    @focus="showSearchSuggestions = searchResults.length > 0"
                  />
                  <Button 
                    v-if="searchQuery"
                    variant="ghost"
                    size="icon"
                    class="absolute right-0 top-0 h-9 w-9 text-muted-foreground hover:text-foreground z-10"
                    @click="searchQuery = ''; showSearchSuggestions = false;"
                  >
                    <XIcon class="h-3.5 w-3.5" />
                  </Button>
               </div>
            </PopoverTrigger>
            <PopoverContent 
              class="p-0 w-[var(--radix-popover-trigger-width)] max-h-[300px] overflow-y-auto" 
              align="start" 
              :sideOffset="4"
              @openAutoFocus.prevent
            >
               <div class="p-1">
                  <div 
                    v-for="result in searchResults" 
                    :key="result"
                    class="px-2 py-1.5 text-sm rounded-sm hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2"
                    @click="selectSuggestion(result)"
                  >
                    <SearchIcon class="h-3.5 w-3.5 text-muted-foreground" />
                    <span class="truncate">{{ result }}</span>
                  </div>
                  <div v-if="searchResults.length === 0" class="p-4 text-center text-xs text-muted-foreground">
                     未找到相关节点
                  </div>
                </div>
            </PopoverContent>
          </Popover>
        </div>
        <div class="flex items-center gap-1">
          <Button variant="outline" size="icon" class="h-9 w-9" @click="handleRandomExplore" title="随机探索">
              <ShuffleIcon class="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" class="h-9 w-9" @click="refreshGraph" title="刷新图谱">
              <RefreshCwIcon class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div class="flex items-center space-x-2">
         <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" class="h-9 px-3 text-xs gap-2" @click="handleBackup">
                  <SaveIcon class="h-3.5 w-3.5" />
                  <span>备份</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>创建当前图谱快照</TooltipContent>
            </Tooltip>
         </TooltipProvider>

         <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" class="h-9 px-3 text-xs gap-2 text-destructive hover:text-destructive border-destructive/20 hover:bg-destructive/5" @click="handleRestore">
                  <RotateCcwIcon class="h-3.5 w-3.5" />
                  <span>回滚</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>恢复到最近一次备份</TooltipContent>
            </Tooltip>
         </TooltipProvider>

         <div class="w-px h-4 bg-border/60 mx-1"></div>

         <Button 
            variant="ghost" 
            size="icon" 
            class="h-9 w-9"
            :class="{ 'bg-primary/10 text-primary': showLogs }"
            @click="showLogs = !showLogs"
            title="操作日志"
         >
            <FileTextIcon class="h-4 w-4" />
         </Button>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="flex-1 flex overflow-hidden relative">
      <!-- Left Sidebar (Fixes) -->
      <aside class="w-80 flex-shrink-0 border-r bg-background z-10 flex flex-col">
        <RelationFixPanel 
          :fixes="fixes"
          :loading="loading"
          @detect="handleDetect"
          @apply="handleApplyFixes"
        />
      </aside>

      <!-- Center Content (Graph) -->
      <main class="flex-1 relative bg-muted/10 overflow-hidden flex flex-col">
        <!-- Loading Overlay -->
        <div v-if="loading" class="absolute inset-0 z-50 bg-background/50 backdrop-blur-[1px] flex items-center justify-center">
             <div class="flex flex-col items-center gap-4 p-6 rounded-xl bg-background shadow-lg border">
                 <div class="relative h-10 w-10">
                    <div class="absolute inset-0 border-2 border-primary/20 rounded-full"></div>
                    <div class="absolute inset-0 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                 </div>
                 <p class="text-sm font-medium text-muted-foreground animate-pulse">处理中...</p>
             </div>
        </div>

        <div v-if="Object.keys(nodes).length === 0 && !loading" class="flex-1 flex flex-col items-center justify-center text-muted-foreground z-10">
             <div class="bg-background/80 backdrop-blur-sm p-8 rounded-xl border shadow-lg flex flex-col items-center gap-4 max-w-md text-center pointer-events-auto">
                 <div class="p-4 rounded-full bg-primary/10 mb-2">
                    <Share2Icon class="h-8 w-8 text-primary" />
                 </div>
                 <h3 class="text-lg font-semibold text-foreground">开始图谱治理</h3>
                 <p class="text-sm">
                   您可以搜索特定节点，或者使用随机探索功能发现潜在的数据问题。
                 </p>
                 <div class="flex gap-3 mt-2">
                    <Button variant="outline" @click="handleRandomExplore">
                       <ShuffleIcon class="h-4 w-4 mr-2" />
                       随机探索
                    </Button>
                 </div>
             </div>
        </div>

        <GraphViewer
          v-else
          ref="graphViewerRef"
          :nodes="nodes"
          :edges="edges"
          :loading="false" 
          :show-toolbar="true"
          class="w-full h-full"
          @node-click="handleNodeClick"
        />
        
        <!-- Logs Panel (Floating) -->
        <div 
          v-if="showLogs" 
          class="absolute bottom-4 right-4 w-96 z-30 shadow-xl border rounded-lg bg-background/95 backdrop-blur animate-in slide-in-from-bottom-2 fade-in duration-200"
        >
          <div class="flex items-center justify-between px-3 py-2 border-b bg-muted/30">
            <span class="text-xs font-medium flex items-center gap-2">
              <FileTextIcon class="h-3.5 w-3.5" />
              操作日志
            </span>
            <Button variant="ghost" size="icon" class="h-6 w-6" @click="loadLogs">
              <RefreshCwIcon class="h-3 w-3" />
            </Button>
          </div>
          <ScrollArea class="h-48 w-full">
            <div class="p-2 space-y-1">
               <div v-if="logs.length === 0" class="text-muted-foreground text-[10px] text-center py-4">暂无日志</div>
               <div v-for="(log, i) in logs" :key="i" class="text-[10px] font-mono p-1.5 border-b last:border-0 border-border/50 text-muted-foreground">
                  <span class="text-primary/50 mr-1">[{{ i + 1 }}]</span> {{ log }}
               </div>
            </div>
          </ScrollArea>
        </div>
      </main>

      <!-- Right Sidebar (Inspector) -->
      <aside 
        v-if="selectedNode" 
        class="w-96 flex-shrink-0 border-l bg-background z-10 transition-all duration-300 ease-in-out shadow-lg"
      >
        <NodeInspector 
          :node="selectedNode"
          :relations="currentRelations"
          :loading="loading"
          @close="handleCloseInspector"
          @updateNode="handleUpdateNode"
          @createRelation="handleCreate"
          @deleteRelations="handleDelete"
        />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { 
  FileText as FileTextIcon, 
  RefreshCw as RefreshCwIcon, 
  Search as SearchIcon,
  Save as SaveIcon,
  RotateCcw as RotateCcwIcon,
  Share2 as Share2Icon,
  X as XIcon,
  Shuffle as ShuffleIcon
} from 'lucide-vue-next';
import GraphViewer from '@/shared/components/organisms/GraphViewer/GraphViewer.vue';
import RelationFixPanel from './components/RelationFixPanel.vue';
import NodeInspector from './components/NodeInspector.vue';
import { relationFixApi, type RelationFix } from './api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

const { toast } = useToast();

const nodes = ref<Record<string, any>>({});
const edges = ref<Record<string, any>>({});
const loading = ref(false);
const fixes = ref<RelationFix[]>([]);
const logs = ref<string[]>([]);
const showLogs = ref(false);
const graphViewerRef = ref();
const currentNodeId = ref<string>('');
const searchQuery = ref('');
const searchResults = ref<string[]>([]);
const showSearchSuggestions = ref(false);

const debouncedSearch = useDebounceFn(async (query: string) => {
  if (!query.trim()) {
    searchResults.value = [];
    return;
  }
  try {
    const results = await relationFixApi.searchNodes(query);
    searchResults.value = results;
    showSearchSuggestions.value = results.length > 0;
  } catch (e) {
    console.error(e);
  }
}, 300);

watch(searchQuery, (newQuery) => {
  if (!newQuery) {
    searchResults.value = [];
    showSearchSuggestions.value = false;
  } else {
    debouncedSearch(newQuery);
  }
});

const selectSuggestion = (nodeId: string) => {
  searchQuery.value = nodeId;
  showSearchSuggestions.value = false;
  handleSearch();
};

const currentRelations = computed(() => Object.values(edges.value));

const selectedNode = computed(() => {
  if (currentNodeId.value && nodes.value[currentNodeId.value]) {
    return nodes.value[currentNodeId.value];
  }
  return null;
});

const loadLogs = async () => {
  try {
      logs.value = await relationFixApi.getLogs();
  } catch (e) {
      console.error("Failed to load logs", e);
  }
};

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return;
  
  loading.value = true;
  try {
    const results = await relationFixApi.searchNodes(searchQuery.value);
    if (results.length > 0) {
      // Load first match
      await loadNode(results[0], false); 
    } else {
        toast({
          title: "未找到相关节点",
          description: `未发现与 "${searchQuery.value}" 匹配的节点`,
          variant: "destructive"
        });
    }
  } catch (e) {
      console.error(e);
      toast({
          title: "搜索失败",
          variant: "destructive"
      });
  } finally {
    loading.value = false;
  }
};

const handleRandomExplore = async () => {
  loading.value = true;
  try {
    const nodes = await relationFixApi.getRandomNodes(1);
    if (nodes && nodes.length > 0) {
       await loadNode(nodes[0], false);
       toast({
         title: "随机探索",
         description: `已加载节点: ${nodes[0]}`
       });
    } else {
       toast({
         title: "无法获取节点",
         description: "图谱可能为空或服务异常",
         variant: "destructive"
       });
    }
  } catch (e) {
     console.error("Random explore failed", e);
     toast({
       title: "操作失败",
       description: "随机探索请求失败",
       variant: "destructive"
     });
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
    await nextTick();
    if (graphViewerRef.value) {
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

const handleUpdateNode = async (nodeId: string, attributes: Record<string, any>) => {
  loading.value = true;
  try {
    await relationFixApi.updateNode(nodeId, attributes);
    toast({ title: "更新成功", description: `节点 ${nodeId} 属性已保存` });
    await loadNode(nodeId, false);
    await loadLogs();
  } catch (e) {
    console.error(e);
    toast({ title: "更新失败", description: "无法保存节点属性更改", variant: "destructive" });
  } finally {
    loading.value = false;
  }
};

const handleDetect = async (mainNode: string, keyword: string) => {
  if (!mainNode || !keyword) {
      toast({
          title: "输入不完整",
          description: "请输入主节点和关键词以开始检测",
          variant: "destructive"
      });
      return;
  }
  loading.value = true;
  try {
    // First load the main node to see it
    await loadNode(mainNode, false);
    
    const results = await relationFixApi.detectRelations(mainNode, keyword);
    fixes.value = results;
    if (results.length === 0) {
        toast({
            title: "检测完成",
            description: "当前节点关系完整或未找到相关缺失。"
        });
    } else {
        toast({
            title: "检测完成",
            description: `发现了 ${results.length} 个潜在的缺失关系`
        });
    }
  } catch (e) {
      console.error(e);
      toast({
          title: "检测失败",
          variant: "destructive"
      });
  } finally {
    loading.value = false;
  }
};

const handleApplyFixes = async (selectedFixes: RelationFix[]) => {
  if (selectedFixes.length === 0) return;
  
  loading.value = true;
  try {
    const res = await relationFixApi.applyFixes(selectedFixes);
    toast({
        title: "修复成功",
        description: `已修复 ${res.count} 个关系`
    });
    fixes.value = []; // Clear fixes
    // Reload graph
    if (selectedFixes.length > 0) {
        await loadNode(selectedFixes[0].source, false);
    }
    await loadLogs();
  } catch (e) {
      console.error(e);
      toast({
          title: "修复失败",
          variant: "destructive"
      });
  } finally {
    loading.value = false;
  }
};

const handleCreate = async (source: string, target: string, type: string, attributes: Record<string, any>) => {
  loading.value = true;
  try {
    await relationFixApi.createRelation(source, target, type, attributes);
    toast({
        title: "创建成功",
        description: `已建立 ${source} -> ${target} 的关系`
    });
    await loadNode(source, false);
    await loadLogs();
  } catch (e) {
      console.error(e);
      toast({
          title: "创建失败",
          variant: "destructive"
      });
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (relations: Array<{ source: string, target: string }>) => {
  if (!confirm(`确定要删除选中的 ${relations.length} 个关系吗？`)) return;

  loading.value = true;
  try {
    const res = await relationFixApi.deleteRelations(relations);
    toast({
        title: "解除成功",
        description: `已解除 ${res.count} 个关系`
    });
    if (currentNodeId.value) {
        await loadNode(currentNodeId.value, false);
    }
    await loadLogs();
  } catch (e) {
      console.error(e);
      toast({
          title: "解除关系失败",
          variant: "destructive"
      });
  } finally {
    loading.value = false;
  }
};

const handleBackup = async () => {
  try {
      const res = await relationFixApi.backupGraph();
      toast({
          title: "备份已创建",
          description: `路径: ${res.path}`
      });
      await loadLogs();
  } catch (e) {
      console.error(e);
      toast({
          title: "备份失败",
          variant: "destructive"
      });
  }
};

const handleRestore = async () => {
  if (confirm('确定要回滚到最近一次备份吗？这将覆盖当前更改。')) {
    loading.value = true;
    try {
        const res = await relationFixApi.restoreBackup();
        if (res.success) {
            toast({
                title: "回滚成功",
                description: "图谱已恢复到最近的备份状态"
            });
            await loadLogs();
            // Reload current graph if possible
            if (Object.keys(nodes.value).length > 0) {
                 const firstNode = Object.keys(nodes.value)[0];
                 await loadNode(firstNode, false);
            }
        } else {
            toast({
                title: "回滚失败",
                variant: "destructive"
            });
        }
    } catch (e) {
        console.error(e);
        toast({
            title: "回滚出错",
            variant: "destructive"
        });
    } finally {
        loading.value = false;
    }
  }
};

const handleNodeClick = (nodeId: string) => {
    loadNode(nodeId);
};

const handleCloseInspector = () => {
  currentNodeId.value = '';
};

const refreshGraph = async () => {
  // Clear current state
  currentNodeId.value = '';
  nodes.value = {};
  edges.value = {};
  searchQuery.value = '';
  fixes.value = [];
  
  await loadLogs();
  
  toast({
    title: "图谱已刷新",
    description: "视图和状态已重置"
  });
};

onMounted(() => {
    loadLogs();
});
</script>
