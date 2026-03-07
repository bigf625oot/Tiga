<template>
  <div class="relative w-full h-full bg-muted/50 dark:bg-slate-900/50 overflow-hidden rounded-lg transition-colors duration-300" ref="containerRef">
    <!-- Empty State -->
    <div v-if="!hasNodes && !loading" class="absolute inset-0 flex flex-col items-center justify-center z-10">
        <div class="w-[120px] h-[120px] mb-4 opacity-80 dark:opacity-60">
            <img src="/empty-graph.svg" alt="No Data" class="w-full h-full object-contain dark:invert dark:opacity-75" />
        </div>
        <p class="text-muted-foreground dark:text-slate-400 text-sm font-medium">暂无图谱数据</p>
    </div>

    <!-- Layout Switcher (Molecule) -->
    <GraphLayoutSwitch v-if="hasNodes" :current-layout="currentLayout" @switch-layout="switchLayout" />

    <!-- 3D Graph Canvas -->
    <GraphViewer3D
      v-if="hasNodes && currentLayout === '3d'"
      ref="graph3DRef"
      class="w-full h-full"
      :nodes="nodes"
      :edges="edges"
      :hidden-types="hiddenTypes"
      :color-map="colorMap"
      @node-click="handleNodeClick"
    />

    <!-- Graph Canvas (Atom/Lib Wrapper) -->
    <v-network-graph
      v-else-if="hasNodes"
      ref="graphRef"
      class="w-full h-full"
      :nodes="nodes"
      :edges="edges"
      :configs="computedConfigs"
      v-model:layouts="layouts"
      :event-handlers="eventHandlers"
      v-model:selected-nodes="selectedNodes"
      v-model:zoom-level="zoomLevel"
    >
        <template #edge-label="{ edge, ...slotProps }">
            <v-edge-label :text="edge.label" align="center" vertical-align="above" v-bind="slotProps" style="font-size: 10px; fill: #666; stroke: none;" />
        </template>
    </v-network-graph>

    <!-- Node Details (Molecule) -->
    <GraphNodeDetails 
        :selected-node-data="selectedNodeData" 
        :related-nodes="relatedNodes"
        @close="clearSelection" 
        @select-node="handleSelectNode"
    />

    <!-- Toolbar (Molecule) -->
    <GraphToolbar
        v-if="showToolbar"
        :current-layout="currentLayout"
        :fullscreen="isFullscreen"
        :scale="zoomLevel"
        :scope="scope"
        :show-scope-toggle="showScopeToggle"
        :selected-node-id="selectedNodeId"
        @enter-fullscreen="enterFullscreen"
        @exit-fullscreen="exitFullscreen"
        @focus-on-selected="focusOnSelected"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @switch-scope="$emit('switchScope', $event)"
        @search="$emit('search', $event)"
    >
        <template #extra-tools>
            <slot name="toolbar-extras"></slot>
        </template>
    </GraphToolbar>
    
    <!-- Loading Overlay with Skeleton -->
    <div v-if="loading" class="absolute inset-0 bg-background/80 dark:bg-slate-900/80 z-50 flex items-center justify-center backdrop-blur-sm">
        <div class="relative w-full h-full overflow-hidden">
             <!-- Skeleton Animation -->
             <div class="absolute inset-0 animate-pulse opacity-20">
                 <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                     <circle cx="50%" cy="50%" r="20" class="fill-foreground dark:fill-slate-400" />
                     <circle cx="30%" cy="30%" r="15" class="fill-foreground dark:fill-slate-400" />
                     <circle cx="70%" cy="70%" r="18" class="fill-foreground dark:fill-slate-400" />
                     <circle cx="20%" cy="60%" r="12" class="fill-foreground dark:fill-slate-400" />
                     <circle cx="80%" cy="40%" r="16" class="fill-foreground dark:fill-slate-400" />
                     <circle cx="40%" cy="80%" r="14" class="fill-foreground dark:fill-slate-400" />
                     
                     <line x1="50%" y1="50%" x2="30%" y2="30%" stroke="currentColor" class="dark:stroke-slate-600" stroke-width="1" />
                     <line x1="50%" y1="50%" x2="70%" y2="70%" stroke="currentColor" class="dark:stroke-slate-600" stroke-width="1" />
                     <line x1="30%" y1="30%" x2="20%" y2="60%" stroke="currentColor" class="dark:stroke-slate-600" stroke-width="1" />
                     <line x1="70%" y1="70%" x2="40%" y2="80%" stroke="currentColor" class="dark:stroke-slate-600" stroke-width="1" />
                     <line x1="50%" y1="50%" x2="80%" y2="40%" stroke="currentColor" class="dark:stroke-slate-600" stroke-width="1" />
                 </svg>
             </div>
             
             <!-- Loading Text -->
             <div class="absolute inset-0 flex items-center justify-center">
                 <div class="bg-card dark:bg-slate-800 px-6 py-3 rounded-full border border-border dark:border-slate-700 shadow-lg flex items-center gap-3">
                     <div class="w-5 h-5 border-2 border-primary dark:border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                     <span class="text-sm font-medium text-foreground dark:text-slate-200">图谱构建中...</span>
                 </div>
             </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRefs, onMounted, onUnmounted, nextTick, watch, inject } from 'vue';
import { VNetworkGraph, VEdgeLabel } from "v-network-graph";
import GraphViewer3D from './GraphViewer3D.vue';
import { useGraphLayout } from '@/shared/hooks/useGraphLayout';
import { GraphToolbar } from '@/shared/components/molecules/GraphToolbar';
import { GraphLayoutSwitch } from '@/shared/components/molecules/GraphLayoutSwitch';
import { GraphNodeDetails } from '@/shared/components/molecules/GraphNodeDetails';
import { Loading } from '@/shared/components/atoms/Loading';
import { createGraphLocator, type GraphLocatorAdapter } from '@/features/knowledge/utils/graphLocator';
import type { IGraphViewerProps } from './types';
import type { IGraphNode } from '@/shared/types/graph';
import { useTheme } from '@/composables/useTheme';

const { isLightMode } = useTheme();
const isDark = computed(() => !isLightMode.value);

const props = withDefaults(defineProps<IGraphViewerProps>(), {
    showToolbar: true,
    showScopeToggle: false,
    scope: 'doc',
    hiddenTypes: () => [],
    colorMap: () => ({}),
    loading: false,
    // darkMode prop is optional, but we can also use global state
    darkMode: undefined
});

const emit = defineEmits(['switchScope', 'nodeClick', 'search']);

const { nodes } = toRefs(props);
const hasNodes = computed(() => Object.keys(nodes.value).length > 0);
const { currentLayout, layouts, configs, zoomLevel, switchLayout } = useGraphLayout(nodes);

// Unified Configs (Handles both Dark/Light mode and custom overrides)
const computedConfigs = computed(() => {
    const base = configs;
    // Prefer prop if set, otherwise global dark mode state
    const dark = props.darkMode !== undefined ? props.darkMode : isDark.value;
    
    return {
        ...base,
        node: {
            ...(base.node || {}),
            normal: {
                ...(base.node?.normal || {}),
                // Ensure colorMap is used in both modes
                color: (node: any) => node.color || props.colorMap[node.type] || (dark ? '#60a5fa' : '#4466cc'),
                strokeWidth: dark ? 1 : 1,
                strokeColor: dark ? '#1e293b' : '#ffffff',
                radius: 16,
            },
            hover: {
                ...(base.node?.hover || {}),
                color: '#00f260', // Neon Green for hover
                strokeWidth: 2,
                strokeColor: '#fff'
            },
            label: {
                ...(base.node?.label || {}),
                color: dark ? '#cbd5e1' : '#1e293b',
                fontSize: 11,
            }
        },
        edge: {
            ...(base.edge || {}),
            normal: {
                ...(base.edge?.normal || {}),
                color: dark ? '#475569' : '#94a3b8',
                width: 1,
                opacity: 0.6
            },
            hover: {
                ...(base.edge?.hover || {}),
                color: '#00f260',
                width: 2,
                opacity: 1
            },
            label: {
                ...(base.edge?.label || {}),
                color: dark ? '#64748b' : '#64748b',
                fontSize: 10
            }
        },
        view: {
            ...(base.view || {}),
            grid: {
                visible: false, // Force disable grid in all modes
                interval: 20,
                thickIncrement: 5,
                lineColor: dark ? "#1e293b" : "#e2e8f0",
                thickColor: dark ? "#334155" : "#cbd5e1"
            },
            background: "transparent" // Let parent handle bg color
        }
    };
});


// Selection State
const selectedNodes = ref<string[]>([]);
const selectedNodeId = computed(() => selectedNodes.value.length > 0 ? selectedNodes.value[0] : null);
const selectedNodeData = computed<IGraphNode | null>(() => {
    if (!selectedNodeId.value) return null;
    return props.nodes[selectedNodeId.value] || null;
});

const relatedNodes = computed<IGraphNode[]>(() => {
    if (!selectedNodeId.value) return [];
    
    const related: IGraphNode[] = [];
    const seen = new Set<string>();
    
    // Check all edges
    Object.values(props.edges).forEach(edge => {
        let neighborId = '';
        if (edge.source === selectedNodeId.value) {
            neighborId = edge.target;
        } else if (edge.target === selectedNodeId.value) {
            neighborId = edge.source;
        }
        
        if (neighborId && !seen.has(neighborId) && props.nodes[neighborId]) {
            seen.add(neighborId);
            related.push(props.nodes[neighborId]);
        }
    });
    
    return related;
});

const handleSelectNode = (nodeId: string) => {
    handleNodeClick(nodeId);
    focusNode(nodeId);
};

const clearSelection = () => {
    selectedNodes.value = [];
};

// Graph Ref
const graphRef = ref<InstanceType<typeof VNetworkGraph>>();
const graph3DRef = ref<InstanceType<typeof GraphViewer3D>>();
const locator = ref<GraphLocatorAdapter | null>(null);

// Initialize Locator
watch([graphRef, currentLayout], async ([g, layout]) => {
    if (layout !== '3d' && g) {
        await nextTick();
        locator.value = createGraphLocator('v-network-graph', graphRef, { 
            nodes, 
            layouts, 
            onNodeClick: handleNodeClick 
        });
    } else {
        locator.value = null;
    }
});

// Event Handlers
const handleNodeClick = (nodeId: string) => {
    selectedNodes.value = [nodeId];
    emit('nodeClick', nodeId);
};

const eventHandlers = {
  "node:click": ({ node }: { node: string }) => {
    handleNodeClick(node);
  },
};

// Zoom Actions
const zoomIn = () => {
    try {
        if (graphRef.value) {
            graphRef.value.zoomIn();
        }
    } catch (e) {
        console.warn("Graph zoomIn failed:", e);
    }
};

const zoomOut = () => {
    try {
        if (graphRef.value) {
            graphRef.value.zoomOut();
        }
    } catch (e) {
        console.warn("Graph zoomOut failed:", e);
    }
};

const focusNode = async (nodeId: string) => {
    if (!nodeId) return;
    await nextTick();
    
    if (currentLayout.value === '3d' && graph3DRef.value) {
        graph3DRef.value.focusNode(nodeId);
    } else if (locator.value) {
        await locator.value.locateNode(nodeId);
    } else if (graphRef.value) {
        // Fallback
        const nodePos = layouts.value.nodes[nodeId];
        if (nodePos) {
             graphRef.value.panTo({ x: nodePos.x, y: nodePos.y });
        }
    }
};

const focusOnSelected = () => {
    if (selectedNodeId.value) {
        focusNode(selectedNodeId.value);
    }
};

// ...

// Expose methods for parent components
defineExpose({
    focusNode,
    zoomIn,
    zoomOut
});

// Fullscreen
const containerRef = ref<HTMLElement | null>(null);
const isFullscreen = ref(false);

const enterFullscreen = async () => {
  if (containerRef.value) {
    try {
      await containerRef.value.requestFullscreen();
      isFullscreen.value = true;
    } catch (e) {
      console.error(e);
    }
  }
};

const exitFullscreen = async () => {
  try {
    if (document.fullscreenElement) {
        await document.exitFullscreen();
    }
    isFullscreen.value = false;
  } catch (e) {
      console.error(e);
  }
};

// Listen for fullscreen change
const onFullscreenChange = () => {
    isFullscreen.value = !!document.fullscreenElement;
};

onMounted(() => {
    document.addEventListener('fullscreenchange', onFullscreenChange);
});

onUnmounted(() => {
    document.removeEventListener('fullscreenchange', onFullscreenChange);
});
</script>

<style scoped>
/* No extra styles needed thanks to Tailwind */
</style>
