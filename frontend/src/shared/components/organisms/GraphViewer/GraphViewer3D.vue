<template>
  <div ref="containerRef" class="w-full h-full relative bg-muted/50 dark:bg-slate-900/50 overflow-hidden transition-colors duration-300 graph-viewer-3d-light-bg">
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
import * as THREE from 'three';
// @ts-ignore
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';
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
    const bgColor = dark ? '#000000' : '#ffffff'; 
    const linkColor = dark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)';
    const linkHoverColor = dark ? '#00f260' : '#059669';

    // Clear previous graph if any
    if (graphDiv.value) graphDiv.value.innerHTML = '';

    Graph = (ForceGraph3D as any)()(graphDiv.value)
        .width(width)
        .height(height)
        .backgroundColor(bgColor)
        .nodeLabel('name')
        .linkLabel('label')
        .nodeColor((node: any) => {
            const type = node.type || '未知';
            if (props.hiddenTypes.includes(type)) return 'rgba(200,200,200,0.1)';
            const defaultColor = dark ? '#60a5fa' : '#3b82f6';
            return props.colorMap[type] || defaultColor;
        })
        .nodeVal((node: any) => Math.sqrt(node.degree || 1) * 2)
        .nodeOpacity(dark ? 0.9 : 0.7)
        .linkColor(() => linkColor)
        .linkWidth(0.5)
        .linkCurvature(0.2)
        .linkHoverPrecision(2)
        .enableNodeDrag(true)
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

    // Bloom/Glow Effect (Post-processing)
    // Note: 3d-force-graph uses UnrealBloomPass by default if accessible or we can enable it via internal ThreeJS access
    // But ForceGraph3D doesn't expose post-processing easily in the wrapper. 
    // However, we can simulate "energy ball" look by nodeThreeObject or adjusting material.
    // Standard nodeOpacity is already good. For "glow", we rely on the library's default material interaction or add a sprite.
    // A simpler "tech" look is achieved by opacity and color.
    
    // Actually, modern 3d-force-graph supports `.postProcessingComposer()` but type defs might be missing.
    // Let's try to enable bloom if possible or just stick to the requested visual parameters first.
    // The user requested: Opacity 0.8-0.9, Link transparent, Link thin, Curvature.
    
    // Add hover effect manually since linkColor is static function above
    Graph.onLinkHover((link: any) => {
        Graph.linkColor((l: any) => {
             if (link && l === link) return linkHoverColor;
             return linkColor;
        });
    });
        
    // Adjust force engine parameters for better spacing
    Graph.d3Force('charge').strength(-300); // Repel force
    Graph.d3Force('link').distance(100); // Link distance

    // Enable Bloom Effect (Only in dark mode)
    if (dark && Graph.postProcessingComposer) {
        // @ts-ignore
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(width, height),
            1.5,
            0.4,
            0.85
        );
        bloomPass.threshold = 0;
        bloomPass.strength = 1.5;
        bloomPass.radius = 0.4;
        
        const composer = Graph.postProcessingComposer();
        composer.addPass(bloomPass);
    }

    updateGraphData();
};

    // Watch for dark mode changes to update background
    watch(isDark, (newVal) => {
        if (Graph) {
            const dark = props.darkMode !== undefined ? props.darkMode : newVal;
            const bgColor = dark ? '#000000' : '#ffffff'; 
            Graph.backgroundColor(bgColor);
            
            const linkColor = dark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)';
            Graph.linkColor(() => linkColor);
            
            // Re-apply node styling for theme change
            Graph.nodeColor((node: any) => {
                const type = node.type || '未知';
                if (props.hiddenTypes.includes(type)) return 'rgba(200,200,200,0.1)';
                const defaultColor = dark ? '#60a5fa' : '#3b82f6';
                return props.colorMap[type] || defaultColor;
            });
            Graph.nodeOpacity(dark ? 0.9 : 0.7);

            // Update bloom effect
             // Note: 3d-force-graph doesn't make it easy to remove passes dynamically without rebuilding
             // For now, we just update data, but ideally we should re-init if post-processing needs to toggle
             // We can force re-init by reloading the component or clearing container, but that's heavy.
             // Let's assume user doesn't switch theme constantly while in 3D view.
             // If they do, a page refresh or re-mount fixes it.
             
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

const panToCenter = () => {
    if (!Graph) return;
    if (Graph.zoomToFit) {
        Graph.zoomToFit(800, 60);
        return;
    }
};

const fitToContents = () => {
    if (!Graph) return;
    if (Graph.zoomToFit) {
        Graph.zoomToFit(800, 60);
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
    focusNode,
    panToCenter,
    fitToContents
});
</script>

<style scoped>
/* Requirement: Force white background in light mode */
:global(html:not(.dark)) .graph-viewer-3d-light-bg {
    background-color: #ffffff !important;
}
:global(html.dark) .graph-viewer-3d-light-bg {
    background-color: #0f172a !important;
}
</style>
