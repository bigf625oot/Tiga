<script setup lang="ts">
import { ref, computed, markRaw, nextTick } from 'vue';
import { VueFlow, useVueFlow, type Node, type Edge, type Connection, MarkerType, type VueFlowStore } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { MiniMap } from '@vue-flow/minimap';
import { usePipelineStore } from '../composables/usePipelineStore';
import { usePipelineLayout, type PipelineLayoutMode } from '../composables/usePipelineLayout';
import CustomNode from './CustomNode.vue';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { LayoutGrid, Redo, Undo } from 'lucide-vue-next';
import { useTheme } from '@/composables/useTheme';
import type { NodeData } from '../types/pipeline';

// Styles
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';
import '@vue-flow/controls/dist/style.css';
import '@vue-flow/minimap/dist/style.css';
// import '@vue-flow/background/dist/style.css';

const store = usePipelineStore();
const flow = useVueFlow();
const { fitView } = flow;
const { isLightMode } = useTheme();
const { applyLayout, layoutLabels } = usePipelineLayout();
let flowInstance: VueFlowStore | null = null;

// Register node types
const nodeTypes = {
  custom: markRaw(CustomNode),
};

const onPaneReady = (instance: VueFlowStore) => {
  flowInstance = instance;
};

const applyQuickLayout = async (mode: PipelineLayoutMode) => {
  const instanceNodes = (flowInstance?.getNodes?.value as any[] | undefined) ?? (flow.getNodes.value as any[] | undefined) ?? [];
  const sizes: Record<string, { width: number; height: number }> = {};

  if (instanceNodes?.length) {
    for (const n of instanceNodes) {
      const width = n?.dimensions?.width ?? n?.width;
      const height = n?.dimensions?.height ?? n?.height;
      if (n?.id && Number.isFinite(width) && Number.isFinite(height)) {
        sizes[n.id] = { width, height };
      }
    }
  }

  store.nodes = await applyLayout({
    mode,
    nodes: store.nodes,
    edges: store.edges,
    nodeSizes: sizes,
  });

  await nextTick();
  try {
    await fitView({ padding: 0.2 });
  } catch {}
};

// Handle connections
const onConnect = (params: Connection) => {
  if (!flowInstance) return;
  
  // Basic validation: Check for self-loops and duplicates
  if (params.source === params.target) return;
  const exists = store.edges.some(e => e.source === params.source && e.target === params.target);
  if (exists) return;

  // Validate connection types (Source -> Transform -> Sink)
  const sourceNode = store.nodes.find(n => n.id === params.source);
  const targetNode = store.nodes.find(n => n.id === params.target);

  if (sourceNode && targetNode) {
    const sourceType = sourceNode.data?.type;
    const targetType = targetNode.data?.type;

    // Rules:
    // 1. Source cannot be a target (handled by handle type usually, but double check)
    // 2. Sink cannot be a source
    // 3. Source can connect to Transform or Sink
    // 4. Transform can connect to Transform or Sink
    
    if (sourceType === 'sink') return; // Sink cannot be source
    if (targetType === 'source') return; // Source cannot be target
  }

  const newEdge: Edge = {
    ...params,
    id: `vueflow__edge-${params.source}${params.sourceHandle || ''}-${params.target}${params.targetHandle || ''}`,
    animated: true,
    style: { 
      stroke: isLightMode.value ? '#94a3b8' : '#475569', 
      strokeWidth: 2 
    },
    markerEnd: MarkerType.ArrowClosed,
  };
  flowInstance.addEdges([newEdge]);
};

const onDragOver = (event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move';
  }
};

const onDrop = (event: DragEvent) => {
  const typeStr = event.dataTransfer?.getData('application/vueflow');
  if (!typeStr || !flowInstance) return;

  const { type, subType, label } = JSON.parse(typeStr);
  
  // Use project to convert screen coordinates to flow coordinates
  // We need to subtract the bounding rect of the flow container to get relative coordinates
  // But flowInstance.project usually expects coordinates relative to the viewport? 
  // Actually, project() maps a coordinate {x, y} to the graph's coordinate system.
  // The input to project() should be relative to the flow pane if the pane is offset.
  // But typically with event.clientX/Y and screenToFlowCoordinate is better.
  
  // Assuming we have screenToFlowCoordinate from instance in newer versions, 
  // but to be safe with unknown version, let's use project with a calculated offset.
  // Or better, let's just use event.offsetX/Y which is relative to the target.
  // If the drop target is the pane, offsetX/Y is correct-ish (ignoring zoom/pan for a moment).
  // BUT, we need to account for zoom and pan. `project` does that.
  
  // Best bet without screenToFlowCoordinate:
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const position = flowInstance.project({
    x: event.clientX - bounds.left,
    y: event.clientY - bounds.top
  });

  // Create a new node
  const newNode: Node<NodeData> = {
    id: `node_${Date.now()}`,
    type: 'custom',
    position, 
    data: { 
      label: label || `New ${subType}`, 
      type, 
      subType,
      config: {},
      status: 'idle' 
    },
  };
  
  store.addNode(newNode);
};

const patternColor = computed(() => isLightMode.value ? '#cbd5e1' : '#334155');
const bgColor = computed(() => isLightMode.value ? '#ffffff' : '#000000');
const edgeOptions = computed(() => ({
  animated: true,
  style: { 
    stroke: isLightMode.value ? '#94a3b8' : '#475569', 
    strokeWidth: 2 
  },
  markerEnd: MarkerType.ArrowClosed,
}));
</script>

<template>
  <div class="w-full h-full bg-white dark:bg-black relative" @dragover="onDragOver" @drop="onDrop">
    <VueFlow
      v-model="store.nodes"
      v-model:edges="store.edges"
      :node-types="nodeTypes"
      :default-viewport="{ zoom: 1 }"
      :min-zoom="0.2"
      :max-zoom="4"
      :default-edge-options="edgeOptions"
      :elevate-nodes-on-select="false"
      :elevate-edges-on-select="false"
      :only-render-visible-elements="true"
      fit-view-on-init
      class="etl-flow"
      @pane-ready="onPaneReady"
      @connect="onConnect"
      @node-click="(e) => store.setSelectedNode(e.node.id)"
      @pane-click="() => store.setSelectedNode(null)"
    >
      <Background 
        variant="dots"
        :gap="20" 
        :size="1.5" 
        :pattern-color="isLightMode ? '#94a3b8' : '#475569'" 
      />
      <Controls />
      <MiniMap />
      
      <!-- Controls Panel -->
      <div class="absolute top-4 right-4 flex gap-2 p-1.5 bg-background/80 backdrop-blur border border-border rounded-lg shadow-sm z-10">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8" title="快捷布局">
              <LayoutGrid class="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem @click="applyQuickLayout('dagre-lr')">
              {{ layoutLabels['dagre-lr'] }}
            </DropdownMenuItem>
            <DropdownMenuItem @click="applyQuickLayout('dagre-tb')">
              {{ layoutLabels['dagre-tb'] }}
            </DropdownMenuItem>
            <DropdownMenuItem @click="applyQuickLayout('elk-lr')">
              {{ layoutLabels['elk-lr'] }}
            </DropdownMenuItem>
            <DropdownMenuItem @click="applyQuickLayout('elk-tb')">
              {{ layoutLabels['elk-tb'] }}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="applyQuickLayout('force')">
              {{ layoutLabels.force }}
            </DropdownMenuItem>
            <DropdownMenuItem @click="applyQuickLayout('grid')">
              {{ layoutLabels.grid }}
            </DropdownMenuItem>
            <DropdownMenuItem @click="applyQuickLayout('circle')">
              {{ layoutLabels.circle }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button variant="ghost" size="icon" class="h-8 w-8" @click="store.undo" :disabled="!store.canUndo">
          <Undo class="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon" class="h-8 w-8" @click="store.redo" :disabled="!store.canRedo">
          <Redo class="w-4 h-4" />
        </Button>
      </div>
    </VueFlow>
  </div>
</template>

<style>
/* Vue Flow Overrides */
.vue-flow__node-custom {
  /* Ensure custom node doesn't have default styles interfering */
  padding: 0;
  border: none;
  background: transparent;
}
</style>
