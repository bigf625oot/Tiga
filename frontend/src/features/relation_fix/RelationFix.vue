<template>
  <div class="h-full flex flex-col bg-background text-foreground">
    <!-- Header Banner -->
    <div class="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">图谱治理</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-muted-foreground text-xs truncate max-w-xl">
            检测并修复知识图谱中的关系缺失，管理实体属性与关联。
          </p>
        </div>
        <div class="flex items-center space-x-2">
            <!-- Future header actions can go here -->
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Sidebar (Editor) -->
      <div class="w-80 flex-shrink-0 border-r bg-muted/10">
        <RelationEditor 
          :fixes="fixes"
          :currentRelations="currentRelations"
          :selectedNode="selectedNode"
          @search="handleSearch"
          @detect="handleDetect"
          @applyFixes="handleApplyFixes"
          @create="handleCreate"
          @delete="handleDelete"
          @backup="handleBackup"
          @restore="handleRestore"
          @updateNode="handleUpdateNode"
        />
      </div>

      <!-- Right Content (Graph) -->
      <div class="flex-1 relative bg-muted/20">
        <!-- Skeleton Loading State -->
        <div v-if="loading" class="absolute inset-0 z-30 bg-background/50 backdrop-blur-sm flex items-center justify-center transition-all duration-300">
             <div class="flex flex-col items-center gap-6">
                 <div class="relative">
                    <Skeleton class="h-32 w-32 rounded-full border-4 border-background shadow-xl animate-pulse" />
                    <div class="absolute inset-0 border-t-4 border-primary rounded-full animate-spin"></div>
                 </div>
                 <div class="space-y-2 text-center">
                     <Skeleton class="h-4 w-[200px]" />
                     <Skeleton class="h-3 w-[150px]" />
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
            <Button
              variant="outline"
              size="icon"
              class="h-8 w-8 shadow-sm"
              :class="{ 'bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground border-primary': showLogs }"
              @click="showLogs = !showLogs"
              title="操作日志"
            >
              <FileTextIcon class="h-4 w-4" />
            </Button>
          </template>
        </GraphViewer>
        
        <!-- Logs Panel -->
        <Card 
          v-if="showLogs" 
          class="absolute bottom-4 right-4 w-96 max-h-[300px] flex flex-col shadow-xl border-border/60 z-20 animate-in slide-in-from-bottom-4 fade-in-0 duration-200"
        >
          <CardHeader class="py-2.5 px-4 flex flex-row items-center justify-between space-y-0 border-b bg-muted/40">
            <CardTitle class="text-xs font-medium uppercase tracking-wider text-muted-foreground">操作日志</CardTitle>
            <Button 
              variant="ghost" 
              size="sm" 
              class="h-6 w-6 p-0 hover:bg-background"
              @click="loadLogs"
              title="刷新日志"
            >
              <RefreshCwIcon class="h-3.5 w-3.5" />
            </Button>
          </CardHeader>
          <CardContent class="p-0 flex-1 min-h-0 bg-zinc-950 text-zinc-50 font-mono text-[10px] leading-relaxed">
             <ScrollArea class="h-64 w-full">
               <div class="p-3 space-y-1">
                 <div v-if="logs.length === 0" class="text-zinc-500 italic text-center py-4">暂无日志记录</div>
                 <div v-for="(log, i) in logs" :key="i" class="break-all border-b border-white/5 last:border-0 pb-1 mb-1 last:pb-0 last:mb-0 opacity-90 hover:opacity-100 transition-opacity">
                    <span class="text-zinc-500 select-none mr-2">[{{ i + 1 }}]</span>
                    {{ log }}
                 </div>
               </div>
             </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { FileText as FileTextIcon, RefreshCw as RefreshCwIcon } from 'lucide-vue-next';
import GraphViewer from '@/shared/components/organisms/GraphViewer/GraphViewer.vue';
import RelationEditor from './components/RelationEditor.vue';
import { relationFixApi, type RelationFix } from './api';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();

const nodes = ref<Record<string, any>>({});
const edges = ref<Record<string, any>>({});
const loading = ref(false);
const fixes = ref<RelationFix[]>([]);
const logs = ref<string[]>([]);
const showLogs = ref(false);
const graphViewerRef = ref();
const currentNodeId = ref<string>('');

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

const handleSearch = async (query: string) => {
  loading.value = true;
  try {
    const results = await relationFixApi.searchNodes(query);
    if (results.length > 0) {
      // Load first match
      await loadNode(results[0], false); // Don't set global loading inside
    } else {
        toast({
          title: "未找到相关节点",
          description: `未发现与 "${query}" 匹配的节点`,
          variant: "destructive"
        });
    }
  } catch (e) {
      console.error(e);
      toast({
          title: "搜索失败",
          description: "请检查网络连接或稍后重试",
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

onMounted(() => {
    loadLogs();
});
</script>