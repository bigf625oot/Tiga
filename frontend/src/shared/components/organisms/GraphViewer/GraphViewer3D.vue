<template>
  <div ref="containerRef" class="w-full h-full relative bg-muted/50 dark:bg-slate-900/50 overflow-hidden transition-colors duration-300">
    <!-- Graph Container -->
    <div ref="graphDiv" class="w-full h-full"></div>

    <!-- Legend -->
    <div class="absolute bottom-4 right-4 z-10 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 max-w-[200px] transition-colors">
        <div class="text-[10px] font-semibold text-muted-foreground dark:text-slate-400 uppercase mb-2">图例 (3D)</div>
        <div class="flex flex-wrap gap-2">
            <div v-for="(color, type) in colorMap" :key="type" class="flex items-center gap-1.5 cursor-pointer hover:opacity-80">
                <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: hiddenTypes.includes(type) ? '#ccc' : color }"></span>
                <span class="text-xs text-slate-600 dark:text-slate-300" :class="{ 'line-through opacity-50': hiddenTypes.includes(type) }">{{ type }}</span>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, inject, computed } from 'vue';
import ForceGraph3D from '3d-force-graph';
import type { IGraphNode } from '@/shared/types/graph';
import { useTheme } from '@/composables/useTheme';

const { isLightMode } = useTheme();
const isDark = computed(() => !isLightMode.value);

// Define Props
interface Props {
    nodes: Record<string, IGraphNode>;
    edges: Record<string, any>;
    hiddenTypes?: string[];
    colorMap?: Record<string, string>;
    darkMode?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    hiddenTypes: () => [],
    colorMap: () => ({}),
    darkMode: undefined
});

const emit = defineEmits(['nodeClick']);

const containerRef = ref<HTMLElement | null>(null);
const graphDiv = ref<HTMLElement | null>(null);
let Graph: any = null;

const initGraph = () => {
    if (!graphDiv.value || !containerRef.value) return;
    
    const width = containerRef.value.clientWidth;
    const height = containerRef.value.clientHeight;
    
    // Determine background color
    const dark = props.darkMode !== undefined ? props.darkMode : isDark.value;
    const bgColor = dark ? '#0f172a' : '#f8fafc';
    const textColor = dark ? '#e2e8f0' : '#1e293b';
    const linkColor = dark ? '#475569' : '#999999';

    Graph = (ForceGraph3D as any)()(graphDiv.value)
        .width(width)
        .height(height)
        .backgroundColor(bgColor)
        .nodeLabel('name')
        .linkLabel('label')
        .nodeColor((node: any) => {
            const type = node.type || '未知';
            if (props.hiddenTypes.includes(type)) return 'rgba(200,200,200,0.1)';
            return props.colorMap[type] || (dark ? '#60a5fa' : '#6b7280');
        })
        .nodeVal((node: any) => Math.sqrt(node.degree || 1) * 2)
        .linkColor(() => linkColor)
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
        
    // Adjust force engine parameters for better spacing
    Graph.d3Force('charge').strength(-300); // Repel force
    Graph.d3Force('link').distance(100); // Link distance

    updateGraphData();
};

// Watch for dark mode changes to update background
watch(isDark, (newVal) => {
    if (Graph) {
        const dark = props.darkMode !== undefined ? props.darkMode : newVal;
        const bgColor = dark ? '#0f172a' : '#f8fafc';
        const linkColor = dark ? '#475569' : '#999999';
        
        Graph.backgroundColor(bgColor);
        Graph.linkColor(() => linkColor);
        // Force refresh
        updateGraphData(); 
    }
});

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
