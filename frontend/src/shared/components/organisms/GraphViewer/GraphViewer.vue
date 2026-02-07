<template>
  <div class="relative w-full h-full bg-slate-50 overflow-hidden rounded-xl" ref="containerRef">
    <!-- Layout Switcher (Molecule) -->
    <GraphLayoutSwitch :current-layout="currentLayout" @switch-layout="switchLayout" />

    <!-- 3D Graph Canvas -->
    <GraphViewer3D
      v-if="currentLayout === '3d'"
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
      v-else
      ref="graphRef"
      class="w-full h-full"
      :nodes="nodes"
      :edges="edges"
      :configs="configs"
      v-model:layouts="layouts"
      :event-handlers="eventHandlers"
      v-model:selected-nodes="selectedNodes"
      v-model:zoom-level="zoomLevel"
    >
    </v-network-graph>

    <!-- Node Details (Molecule) -->
    <GraphNodeDetails 
        :selected-node-data="selectedNodeData" 
        @close="clearSelection" 
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
    >
        <template #extra-tools>
            <slot name="toolbar-extras"></slot>
        </template>
    </GraphToolbar>
    
    <!-- Loading Overlay -->
    <div v-if="loading" class="absolute inset-0 bg-white/50 z-50 flex items-center justify-center backdrop-blur-sm">
         <Loading type="spinner" text="加载图谱数据..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRefs, onMounted, onUnmounted, nextTick } from 'vue';
import { VNetworkGraph } from "v-network-graph";
import GraphViewer3D from './GraphViewer3D.vue';
import { useGraphLayout } from '@/shared/hooks/useGraphLayout';
import { GraphToolbar } from '@/shared/components/molecules/GraphToolbar';
import { GraphLayoutSwitch } from '@/shared/components/molecules/GraphLayoutSwitch';
import { GraphNodeDetails } from '@/shared/components/molecules/GraphNodeDetails';
import { Loading } from '@/shared/components/atoms/Loading';
import type { IGraphViewerProps } from './types';
import type { IGraphNode } from '@/shared/types/graph';

const props = withDefaults(defineProps<IGraphViewerProps>(), {
    showToolbar: true,
    showScopeToggle: false,
    scope: 'doc',
    hiddenTypes: () => [],
    colorMap: () => ({}),
    loading: false
});

const emit = defineEmits(['switchScope', 'nodeClick']);

const { nodes } = toRefs(props);
const { currentLayout, layouts, configs, zoomLevel, switchLayout } = useGraphLayout(nodes);

// Selection State
const selectedNodes = ref<string[]>([]);
const selectedNodeId = computed(() => selectedNodes.value.length > 0 ? selectedNodes.value[0] : null);
const selectedNodeData = computed<IGraphNode | null>(() => {
    if (!selectedNodeId.value) return null;
    return props.nodes[selectedNodeId.value] || null;
});

const clearSelection = () => {
    selectedNodes.value = [];
};

// Graph Ref
const graphRef = ref<InstanceType<typeof VNetworkGraph>>();
const graph3DRef = ref<InstanceType<typeof GraphViewer3D>>();

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
    } else if (graphRef.value) {
        // Use fitToContents with delay for better robustness
        setTimeout(() => {
            try {
                if (graphRef.value) {
                    const nodePos = layouts.value.nodes[nodeId];
                    if (nodePos) {
                        // Use transitionWhile for animation
                        if (typeof graphRef.value.transitionWhile === 'function') {
                             graphRef.value.transitionWhile(() => {
                                graphRef.value?.panTo({ x: nodePos.x, y: nodePos.y });
                             }, 500);
                        } else {
                            graphRef.value.panTo({ x: nodePos.x, y: nodePos.y });
                        }
                    }
                }
            } catch (e) {
                console.warn("Graph focusNode failed:", e);
                // Last resort fallback
                try {
                    const nodePos = layouts.value.nodes[nodeId];
                    if (nodePos && graphRef.value) {
                         graphRef.value.panTo({ x: nodePos.x, y: nodePos.y });
                    }
                } catch (e2) {
                     console.warn("Graph panTo fallback failed:", e2);
                }
            }
        }, 100);
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
