<template>
  <div ref="containerRef" class="w-full h-full relative bg-slate-50 overflow-hidden">
    <!-- Graph Container -->
    <div ref="graphDiv" class="w-full h-full"></div>

    <!-- Legend -->
    <div class="absolute bottom-4 right-4 z-10 bg-white/90 backdrop-blur-sm p-3 rounded-lg shadow-sm border border-slate-200 max-w-[200px]">
        <div class="text-[10px] font-bold text-slate-400 uppercase mb-2">图例 (3D)</div>
        <div class="flex flex-wrap gap-2">
            <div v-for="(color, type) in colorMap" :key="type" class="flex items-center gap-1.5 cursor-pointer hover:opacity-80">
                <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: hiddenTypes.includes(type) ? '#ccc' : color }"></span>
                <span class="text-xs text-slate-600" :class="{ 'line-through opacity-50': hiddenTypes.includes(type) }">{{ type }}</span>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import ForceGraph3D from '3d-force-graph';
import type { IGraphNode } from '@/shared/types/graph';

// Define Props
interface Props {
    nodes: Record<string, IGraphNode>;
    edges: Record<string, any>;
    hiddenTypes?: string[];
    colorMap?: Record<string, string>;
}

const props = withDefaults(defineProps<Props>(), {
    hiddenTypes: () => [],
    colorMap: () => ({})
});

const emit = defineEmits(['nodeClick']);

const containerRef = ref<HTMLElement | null>(null);
const graphDiv = ref<HTMLElement | null>(null);
let Graph: any = null;

const initGraph = () => {
    if (!graphDiv.value || !containerRef.value) return;
    
    const width = containerRef.value.clientWidth;
    const height = containerRef.value.clientHeight;

    Graph = (ForceGraph3D as any)()(graphDiv.value)
        .width(width)
        .height(height)
        .backgroundColor('#f8fafc') // slate-50
        .nodeLabel('name')
        .linkLabel('label')
        .nodeColor((node: any) => {
            const type = node.type || '未知';
            if (props.hiddenTypes.includes(type)) return 'rgba(200,200,200,0.1)';
            return props.colorMap[type] || '#6b7280';
        })
        .nodeVal((node: any) => Math.sqrt(node.degree || 1) * 2)
        .linkColor(() => '#999999') // darker grey for better visibility
        .linkOpacity(0.6)
        .linkWidth(1.5)
        .nodeResolution(16)
        .onNodeClick((node: any) => {
            // Emit click event
            emit('nodeClick', node.id);
            
            // Focus on node
            const distance = 40;
            const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
            Graph.cameraPosition(
                { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                node,
                3000
            );
        });

    updateGraphData();
};

const updateGraphData = () => {
    if (!Graph || !props.nodes) return;
    
    const nodes: any[] = [];
    const links: any[] = [];
    
    // Convert object to array
    Object.keys(props.nodes).forEach(id => {
        const n = props.nodes[id];
        // Filter hidden types
        const type = n.type || '未知';
        if (!props.hiddenTypes.includes(type)) {
            nodes.push({ ...n, id });
        }
    });
    
    Object.keys(props.edges).forEach(id => {
        const e = props.edges[id];
        // Only include edges where both source and target exist in visible nodes
        // Note: props.edges source/target are just IDs string
        const sourceVisible = nodes.find(n => n.id === e.source);
        const targetVisible = nodes.find(n => n.id === e.target);
        
        if (sourceVisible && targetVisible) {
            links.push({ ...e });
        }
    });
    
    Graph.graphData({ nodes, links });
};

const focusNode = (nodeId: string) => {
    if (!Graph) return;
    const { nodes } = Graph.graphData();
    const node = nodes.find((n: any) => n.id === nodeId);
    if (node) {
        const distance = 40;
        const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
        Graph.cameraPosition(
            { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
            node,
            3000
        );
    }
};

// Handle resize
const onResize = () => {
    if (Graph && containerRef.value) {
        Graph.width(containerRef.value.clientWidth);
        Graph.height(containerRef.value.clientHeight);
    }
};

watch(() => [props.nodes, props.edges, props.hiddenTypes], () => {
    updateGraphData();
}, { deep: true });

onMounted(() => {
    initGraph();
    window.addEventListener('resize', onResize);
});

onUnmounted(() => {
    window.removeEventListener('resize', onResize);
    if (Graph) Graph._destructor();
});

defineExpose({
    focusNode
});
</script>
