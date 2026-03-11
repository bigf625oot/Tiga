<template>
    <div class="h-full flex flex-col bg-background text-foreground">
        <!-- Header Banner -->
        <div class="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <h2 class="text-lg font-semibold tracking-tight">图谱控制台</h2>
                    <div class="h-4 w-px bg-border"></div>
                    <p class="text-muted-foreground text-xs truncate max-w-xl">
                        探索实体间的关联关系，支持多维度的筛选与时序分析。
                    </p>
                </div>
                <div class="flex items-center space-x-2">
                    <Button 
                        variant="outline" 
                        size="sm" 
                        :class="{'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20': showChat}"
                        @click="showChat = !showChat"
                    >
                        <MessageSquare class="w-4 h-4 mr-2" />
                        {{ showChat ? '隐藏对话' : '开启对话' }}
                    </Button>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="flex-1 flex flex-row overflow-hidden min-w-0 min-h-0">
             <!-- Left Sidebar -->
             <div class="flex-shrink-0 border-r bg-background flex flex-col min-h-0 transition-[width] duration-300" :class="sidebarCollapsed ? 'w-12' : 'w-80'">
                 <KnowledgeGraphSidebar
                     v-model:searchQuery="searchQuery"
                     v-model:selectedTypes="selectedTypes"
                     v-model:timeRange="timeRange"
                     v-model:collapsed="sidebarCollapsed"
                     :loading="loading"
                     :allTypes="allTypes"
                     :colorMap="colorMap"
                     :typeCounts="typeCounts"
                     :stats="stats"
                    :timeBounds="timeBounds"
                    :currentEvents="currentEvents"
                    class="h-full border-none bg-transparent"
                />
             </div>

             <!-- Right Content (Graph) -->
             <div class="flex-1 relative bg-background overflow-hidden flex flex-row min-w-0 min-h-0 isolate" style="contain: paint; transform: translateZ(0); clip-path: inset(0);">
                 <!-- Graph Container -->
                 <div class="flex-1 relative h-full min-w-0 min-h-0 overflow-hidden isolate" style="contain: paint; transform: translateZ(0); clip-path: inset(0);">
                     <!-- Graph Reason (Error/Warning) -->
                     <div v-if="graphReason" class="absolute top-4 left-4 z-20 px-3 py-2 bg-amber-50/90 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-lg text-xs shadow-sm border border-amber-200/50 backdrop-blur-sm">
                        {{ graphReason }}
                     </div>

                     <!-- Graph Viewer -->
                     <GraphViewer 
                        ref="graphViewerRef"
                        :nodes="filteredNodes"
                        :edges="filteredEdges"
                        :colorMap="colorMap"
                        :loading="loading"
                        :scope="scope" 
                        @switchScope="handleSwitchScope" 
                        @search="(q) => searchQuery = q"
                        :showScopeToggle="!!docId"
                        class="w-full h-full bg-background"
                        @node-click="handleNodeClick"
                     />
                 </div>
                 
                 <!-- Chat Panel (Right Sidebar Style) -->
                 <div 
                    class="h-full bg-background border-l shadow-xl transition-all duration-300 overflow-hidden relative z-20"
                    :style="{ width: showChat ? '400px' : '0px', opacity: showChat ? 1 : 0 }"
                 >
                     <div class="w-[400px] h-full">
                         <KnowledgeQAPanel
                            :visible="true"
                            :doc-id="docId"
                            :scope="scope"
                            :nodes="rawNodes" 
                            @close="showChat = false"
                            @locate-node="handleLocateNode"
                         />
                     </div>
                 </div>
             </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, shallowRef } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue';
import { GraphViewer } from '@/shared/components/organisms/GraphViewer';
import KnowledgeGraphSidebar from './KnowledgeGraphSidebar.vue';
import KnowledgeQAPanel from './KnowledgeQAPanel.vue';
import { Button } from '@/components/ui/button';
import { MessageSquare } from 'lucide-vue-next';

// Props
const props = defineProps<{
    docId?: number | string | null;
    initialScope?: string;
}>();

// State
const showChat = ref(false);
const loading = ref(true);
const graphReason = ref('');
const rawNodes = shallowRef<Record<string, any>>({});
const rawEdges = shallowRef<Record<string, any>>({});
const scope = ref(props.initialScope || 'doc');
const colorMap = ref<Record<string, string>>({});
const graphViewerRef = ref<any>(null);
const sidebarCollapsed = ref(false);

// Filter State
const searchQuery = ref('');
const selectedTypes = ref<string[]>([]);
const allTypes = ref<string[]>([]);
const timeRange = ref<[number, number]>([0, 0]);
const timeBounds = ref({ min: 0, max: 0 });

const api = axios.create({ baseURL: '/api/v1' });

const baseColorMap: Record<string, string> = {
  "人": "#3b82f6", // Blue
  "组织": "#eab308", // Yellow
  "事件": "#ef4444", // Red
  "文档": "#10b981", // Green
  "资产": "#8b5cf6", // Purple
  "地点": "#f97316", // Orange
  "概念": "#06b6d4", // Cyan
  "其他": "#64748b"  // Slate
};
const knownTypeOrder = ["人","组织","事件","文档","资产", "地点", "概念"];

// Methods
const typeGuess = (n: any) => {
  const t = (n.type || '').toLowerCase();
  if (t.includes('person') || t.includes('user')) return '人';
  if (t.includes('org') || t.includes('company') || t.includes('team')) return '组织';
  if (t.includes('event') || t.includes('incident')) return '事件';
  if (t.includes('doc') || t.includes('file') || t.includes('page')) return '文档';
  if (t.includes('asset') || t.includes('resource')) return '资产';
  if (t.includes('loc') || t.includes('place') || t.includes('area')) return '地点';
  if (t.includes('concept') || t.includes('tag')) return '概念';
  return '其他';
};

const baseTypeCounts = ref<Record<string, number>>({});

const rebuildFilterFromGraph = () => {
  const typesPresent = new Set<string>();
  const counts: Record<string, number> = {};
  
  Object.values(rawNodes.value || {}).forEach((n: any) => {
    const t = n.type || typeGuess(n);
    if (t) {
        typesPresent.add(t);
        counts[t] = (counts[t] || 0) + 1;
    }
  });
  
  baseTypeCounts.value = counts;
  
  // Set all types
  const ordered = Array.from(typesPresent).sort((a,b) => {
    const ia = knownTypeOrder.indexOf(a);
    const ib = knownTypeOrder.indexOf(b);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return a.localeCompare(b, 'zh-CN');
  });
  
  allTypes.value = ordered;
  selectedTypes.value = ordered; // Default select all

  const cmap: Record<string, string> = {};
  // Generate colors for unknown types dynamically if not in base map
  const colors = [
      "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", 
      "#06b6d4", "#f97316", "#6366f1", "#14b8a6", "#d946ef", "#84cc16"
  ];
  
  ordered.forEach((t, index) => {
    let col = baseColorMap[t];
    if (!col) {
        // Deterministic color assignment based on type name hash or index
        col = colors[index % colors.length];
    }
    cmap[t] = col;
  });
  colorMap.value = cmap;
};

const calculateTimeBounds = () => {
    let min = Infinity;
    let max = -Infinity;
    let hasTime = false;

    Object.values(rawNodes.value).forEach((n: any) => {
        // Assume timestamp or created_at exists, or fallback to now
        const ts = n.timestamp || n.created_at || (n.metadata && n.metadata.created_at);
        if (ts) {
            const time = new Date(ts).getTime();
            if (!isNaN(time)) {
                if (time < min) min = time;
                if (time > max) max = time;
                hasTime = true;
            }
        }
    });

    if (!hasTime) {
        // Fallback range if no time data
        const now = Date.now();
        min = now - 30 * 24 * 60 * 60 * 1000; // 30 days ago
        max = now;
    }

    timeBounds.value = { min, max };
    timeRange.value = [min, max];
};

const mapGraphReason = (reason: string) => {
    if (!reason) return '';
    if (reason === 'document_not_found') return '未找到文档或文档已被删除';
    if (reason === 'empty_content_or_not_available') return '文档内容为空或不可获取，无法生成图谱';
    if (reason === 'no_significant_cooccurrence') return '未检测到足够的词共现关系，无法生成图谱';
    if (reason === 'fallback_disabled') return '图谱生成已禁用';
    if (reason.startsWith('error:')) return '系统错误：' + reason.replace('error:', '');
    return '图谱不可用';
};

const loadGraphData = async () => {
    loading.value = true;
    rawNodes.value = {};
    rawEdges.value = {};
    graphReason.value = '';
    
    try {
        const url = scope.value === 'global' ? `/knowledge/graph` : `/knowledge/${props.docId}/graph`;
        const res = await api.get(url);
        if (res.data) {
            const nodes = res.data.nodes || {};
            const edges = res.data.edges || {};
            
            // Process nodes before assignment to ensure consistency
            Object.keys(nodes).forEach(id => {
                const n = nodes[id];
                if (!n.type) n.type = typeGuess(n);
            });

            rawNodes.value = nodes;
            rawEdges.value = edges;
            graphReason.value = mapGraphReason(res.data.reason || '');
            
            rebuildFilterFromGraph();
            calculateTimeBounds();
        }
    } catch (e: any) {
        console.error(e);
        message.error("获取图谱数据失败: " + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};

// Filtering Logic
const searchTimeFilteredNodes = computed(() => {
    const nodes: Record<string, any> = {};
    const query = searchQuery.value.trim().toLowerCase();
    const [minTime, maxTime] = timeRange.value;
    const isSearchActive = !!query;

    Object.entries(rawNodes.value).forEach(([id, node]: [string, any]) => {
        const ts = node.timestamp || node.created_at || (node.metadata && node.metadata.created_at);
        if (ts) {
            const time = new Date(ts).getTime();
            if (!isNaN(time) && (time < minTime || time > maxTime)) return;
        }

        if (isSearchActive) {
            const name = (node.name || '').toLowerCase();
            const type = (node.type || '').toLowerCase();
            const match = name.includes(query) || type.includes(query) || id.toLowerCase().includes(query);
            if (!match) return;

            nodes[id] = {
                ...node,
                color: '#ff0055',
                strokeColor: '#ffffff',
                strokeWidth: 3
            };
            return;
        }

        nodes[id] = node;
    });

    return nodes;
});

const filteredNodes = computed(() => {
    const nodes: Record<string, any> = {};
    const types = new Set(selectedTypes.value);

    Object.entries(searchTimeFilteredNodes.value).forEach(([id, node]: [string, any]) => {
        if (!types.has(node.type || '文档')) return;
        nodes[id] = node;
    });

    return nodes;
});

const filteredEdges = computed(() => {
    const edges: Record<string, any> = {};
    const nodeIds = new Set(Object.keys(filteredNodes.value));
    
    // Only show edges where both source and target are visible
    Object.entries(rawEdges.value).forEach(([id, edge]: [string, any]) => {
        if (nodeIds.has(edge.source) && nodeIds.has(edge.target)) {
            edges[id] = edge;
        }
    });
    
    return edges;
});

const typeCounts = computed<Record<string, number>>(() => {
    const counts: Record<string, number> = { ...baseTypeCounts.value };
    Object.keys(counts).forEach(k => (counts[k] = 0));

    Object.values(searchTimeFilteredNodes.value).forEach((n: any) => {
        const t = n.type || typeGuess(n);
        counts[t] = (counts[t] || 0) + 1;
    });

    return counts;
});

const hasData = computed(() => Object.keys(rawNodes.value).length > 0);

const stats = computed(() => ({
    totalNodes: Object.keys(rawNodes.value).length,
    totalEdges: Object.keys(rawEdges.value).length,
    visibleNodes: Object.keys(filteredNodes.value).length,
    visibleEdges: Object.keys(filteredEdges.value).length
}));

const currentEvents = computed(() => {
    const events: any[] = [];
    Object.values(searchTimeFilteredNodes.value).forEach((n: any) => {
        // Only include nodes that are events or have explicit timestamps
        const type = n.type || typeGuess(n);
        const ts = n.timestamp || n.created_at || (n.metadata && n.metadata.created_at);
        if (ts && (type === '事件' || type === 'Event')) {
             events.push({
                 id: n.id,
                 name: n.name,
                 type: type,
                 time: new Date(ts).getTime(),
                 dateStr: new Date(ts).toLocaleDateString()
             });
        }
    });
    // Sort by time descending
    return events.sort((a, b) => b.time - a.time);
});

const handleSwitchScope = (newScope: string) => {
    if (scope.value === newScope) return;
    scope.value = newScope;
    loadGraphData();
};

const handleNodeClick = (nodeId: string) => {
    // Optional: Auto-search or show details
    // For now just focus
    if (graphViewerRef.value) {
        graphViewerRef.value.focusNode(nodeId);
    }
};

const handleLocateNode = (nodeId: string) => {
    if (graphViewerRef.value) {
        graphViewerRef.value.focusNode(nodeId);
        
        // Find node name for feedback
        const node = (rawNodes.value as any)[nodeId];
        const nodeName = node?.name || nodeId;
        message.success(`已定位: ${nodeName}`);
    } else {
        message.warning('图谱组件未就绪');
    }
};

// Lifecycle & Watch
onMounted(() => {
    if (!props.docId && props.initialScope !== 'global') {
        scope.value = 'global';
    } else if (props.initialScope) {
        scope.value = props.initialScope;
    }
    loadGraphData();
});

watch(() => props.docId, () => {
    // Reset to default scope logic when docId changes
    if (!props.docId) {
        scope.value = 'global';
    } else {
        scope.value = props.initialScope || 'doc';
    }
    loadGraphData();
});
</script>
