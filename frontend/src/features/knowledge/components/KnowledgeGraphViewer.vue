<template>
    <div class="h-full flex flex-row overflow-hidden bg-background transition-colors duration-300">
        <!-- Left: Sidebar -->
        <KnowledgeGraphSidebar
            v-if="!loading && hasData"
            v-model:searchQuery="searchQuery"
            v-model:selectedTypes="selectedTypes"
            v-model:timeRange="timeRange"
            :allTypes="allTypes"
            :colorMap="colorMap"
            :typeCounts="typeCounts"
            :stats="stats"
            :timeBounds="timeBounds"
        />

        <!-- Right: Graph -->
        <div class="flex-1 relative h-full overflow-hidden bg-muted/10">
            <div v-if="loading" class="h-full flex flex-col items-center justify-center p-8 gap-4">
                <!-- Skeleton for Graph -->
                <div class="w-full h-full bg-background graph-skeleton relative overflow-hidden rounded-xl border border-border">
                    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
                        <div class="w-16 h-16 rounded-full bg-muted mb-4"></div>
                        <div class="w-32 h-4 bg-muted rounded"></div>
                    </div>
                    <!-- Random Nodes -->
                    <div class="absolute top-1/4 left-1/4 w-12 h-12 rounded-full bg-muted"></div>
                    <div class="absolute bottom-1/4 right-1/4 w-10 h-10 rounded-full bg-muted"></div>
                    <div class="absolute top-1/3 right-1/3 w-8 h-8 rounded-full bg-muted"></div>
                </div>
            </div>
            <div v-else class="h-full relative">
                <div v-if="graphReason" class="absolute top-3 left-3 z-10 px-3 py-2 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-lg text-xs shadow-sm border border-amber-100 dark:border-amber-800/50 backdrop-blur-sm">
                    {{ graphReason }}
                </div>
                <GraphViewer 
                    ref="graphViewerRef" 
                    :nodes="filteredNodes" 
                    :edges="filteredEdges" 
                    :hiddenTypes="[]" 
                    :colorMap="colorMap" 
                    :reload="reloadGraph" 
                    :scope="scope" 
                    @switchScope="handleSwitchScope" 
                    @search="handleGraphSearch"
                    :showScopeToggle="!!docId"
                    class="bg-background"
                >
                    <template #toolbar-extras>
                        <Button 
                            variant="outline" 
                            size="icon" 
                            class="h-9 w-9"
                            :class="{'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20': showChat}"
                            @click="$emit('toggle-chat')"
                            title="知识问答"
                        >
                            <MessageSquare class="w-4 h-4" />
                        </Button>
                    </template>
                </GraphViewer>
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
import { Button } from '@/components/ui/button';
import { MessageSquare } from 'lucide-vue-next';

// Props
const props = defineProps<{
    docId?: number | string | null;
    initialScope?: string;
    showChat?: boolean;
}>();

// Emits
const emit = defineEmits<{
    (e: 'toggle-chat'): void;
    (e: 'nodes-updated', nodes: any): void;
    (e: 'scope-changed', scope: string): void;
}>();

// State
const loading = ref(true);
const graphReason = ref('');
const rawNodes = shallowRef<Record<string, any>>({});
const rawEdges = shallowRef<Record<string, any>>({});
const scope = ref(props.initialScope || 'doc');
const colorMap = ref<Record<string, string>>({});
const graphViewerRef = ref<any>(null);

// Filter State
const searchQuery = ref('');

// Watch search query changes to trigger focus logic
watch(searchQuery, (newQuery) => {
    if (!newQuery) {
        // Clear focus if needed
        return;
    }
    
    // We wait for filteredNodes to update (which happens automatically via computed)
    // But we might need nextTick if we want to focus on the DOM element rendered by GraphViewer
    // However, GraphViewer usually takes data and renders.
    
    // Let's implement auto-focus on first match when searching from Sidebar
    const q = newQuery.toLowerCase();
    const matches = Object.keys(filteredNodes.value).filter(id => {
        const n = filteredNodes.value[id];
        // Only consider "highlighted" nodes as matches
        return n.color === '#ff0055'; 
    });
    
    if (matches.length > 0) {
        // Debounce focus to avoid jumping around while typing?
        // Or just focus the first one.
        // focusNode(matches[0]); // This might be annoying while typing.
        // Maybe only focus on "Enter" or explicit search action?
        // Sidebar emits update on input.
        
        // Let's NOT auto-focus on every keystroke. 
        // Only highlight.
    }
});
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

const assignTypesFromAttributes = () => {
  Object.keys(rawNodes.value || {}).forEach(id => {
    const n = rawNodes.value[id];
    if (!n.type) n.type = typeGuess(n);
  });
};

const typeCounts = ref<Record<string, number>>({});

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
  
  typeCounts.value = counts;
  
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
    // Don't reset immediately to avoid flicker or empty state if we want to keep old data while loading?
    // But requirement says "loading" state.
    rawNodes.value = {};
    rawEdges.value = {};
    graphReason.value = '';
    
    // Notify parent that nodes are empty during load
    emit('nodes-updated', {});

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
            
            // assignTypesFromAttributes(); // Removed as we did it above
            rebuildFilterFromGraph();
            calculateTimeBounds();
            
            // Emit updated nodes to parent for QA panel to use
            emit('nodes-updated', rawNodes.value);
        }
    } catch (e: any) {
        console.error(e);
        message.error("获取图谱数据失败: " + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};

const reloadGraph = () => loadGraphData();

// Filtering Logic
const filteredNodes = computed(() => {
    const nodes: Record<string, any> = {};
    const query = searchQuery.value.trim().toLowerCase();
    const types = new Set(selectedTypes.value);
    const [minTime, maxTime] = timeRange.value;
    const isSearchActive = !!query;

    Object.entries(rawNodes.value).forEach(([id, node]: [string, any]) => {
        // 1. Time Filter (Strict)
        const ts = node.timestamp || node.created_at || (node.metadata && node.metadata.created_at);
        if (ts) {
            const time = new Date(ts).getTime();
            if (!isNaN(time) && (time < minTime || time > maxTime)) {
                return; // Skip
            }
        }

        // 2. Type Filter (Strict)
        if (!types.has(node.type || '文档')) {
            return; // Skip
        }

        // 3. Search (Filter - strict match)
        if (isSearchActive) {
            const name = (node.name || '').toLowerCase();
            const type = (node.type || '').toLowerCase();
            const match = name.includes(query) || type.includes(query) || id.toLowerCase().includes(query);
            
            if (!match) {
                return; // Skip if not matching
            }
            
            // If matches, include it (with potential highlighting if we still want it, but user asked for filtering)
            // We can still add color to indicate it matched search explicitly, or just leave it default.
            // Let's keep the highlighting as a visual cue even in filtered view, or revert to standard color.
            // Requirement says "visual distinction for filtered nodes", but if we HIDE others, 
            // the distinction is implicit (only matching nodes are shown).
            // However, previous logic added high contrast color.
            // Let's keep the high contrast color for filtered search results to make them pop against the white background.
            nodes[id] = {
                ...node,
                color: '#ff0055', // Neon Red/Pink
                strokeColor: '#ffffff',
                strokeWidth: 3
            };
        } else {
            nodes[id] = node; // Reuse reference for memory efficiency
        }
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

const hasData = computed(() => Object.keys(rawNodes.value).length > 0);

const stats = computed(() => ({
    totalNodes: Object.keys(rawNodes.value).length,
    totalEdges: Object.keys(rawEdges.value).length,
    visibleNodes: Object.keys(filteredNodes.value).length,
    visibleEdges: Object.keys(filteredEdges.value).length
}));

const handleGraphSearch = (query: string) => {
    // This handler is called by GraphViewer component when its internal search bar is used
    // OR when we might want to programmatically trigger search.
    // However, the Sidebar updates `searchQuery` ref directly via v-model.
    // The `searchQuery` ref drives `filteredNodes`.
    // So this method might be redundant or conflicting if it tries to set searchQuery again 
    // or if it implements different logic.
    
    // In previous implementation (before sidebar), this handled search logic.
    // Now Sidebar handles search input -> updates `searchQuery` -> updates `filteredNodes`.
    
    // If GraphViewer emits 'search', we should sync it to sidebar?
    // But we hid the internal toolbar search of GraphViewer?
    // The template says:
    // <GraphViewer ... @search="handleGraphSearch">
    
    // If GraphViewer has its own search bar, we should probably hide it or sync it.
    // Assuming we want to use the Sidebar search exclusively.
    
    // But let's support it just in case:
    searchQuery.value = query;
};

const handleSwitchScope = (newScope: string) => {
    if (scope.value === newScope) return;
    scope.value = newScope;
    emit('scope-changed', newScope);
    loadGraphData();
};

const focusNode = (nodeId: string) => {
    if (graphViewerRef.value) {
        graphViewerRef.value.focusNode(nodeId);
    }
};

// Lifecycle & Watch
onMounted(() => {
    if (!props.docId && props.initialScope !== 'global') {
        scope.value = 'global';
        emit('scope-changed', 'global');
    } else if (props.initialScope) {
        scope.value = props.initialScope;
    }
    loadGraphData();
});

watch(() => props.docId, () => {
    // Reset to default scope logic when docId changes
    if (!props.docId) {
        scope.value = 'global';
        emit('scope-changed', 'global');
    } else {
        scope.value = props.initialScope || 'doc';
        emit('scope-changed', scope.value);
    }
    loadGraphData();
});

// Expose methods for parent
defineExpose({
    focusNode
});
</script>

<style scoped>
.graph-skeleton {
    position: relative;
    overflow: hidden;
}

.graph-skeleton::after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    transform: translateX(-100%);
    background-image: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0) 0,
        rgba(255, 255, 255, 0.4) 20%,
        rgba(255, 255, 255, 0.7) 60%,
        rgba(255, 255, 255, 0)
    );
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    100% {
        transform: translateX(100%);
    }
}
</style>
