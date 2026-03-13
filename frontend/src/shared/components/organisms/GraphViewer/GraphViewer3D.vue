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
const hoverNode = ref<any>(null); // Track hovered node for dynamic styling

// Reusable texture for smooth glow halo
let haloTexture: THREE.CanvasTexture | null = null;
const getHaloTexture = () => {
    if (haloTexture) return haloTexture;
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const context = canvas.getContext('2d');
    if (context) {
        // Create a smooth radial gradient (soft glow)
        const gradient = context.createRadialGradient(64, 64, 0, 64, 64, 64);
        gradient.addColorStop(0, 'rgba(255,255,255,1)');       // Bright core
        gradient.addColorStop(0.4, 'rgba(255,255,255,0.2)');   // Smooth falloff
        gradient.addColorStop(1, 'rgba(255,255,255,0)');       // Transparent edge
        context.fillStyle = gradient;
        context.fillRect(0, 0, 128, 128);
    }
    haloTexture = new THREE.CanvasTexture(canvas);
    return haloTexture;
};

const createTextSprite = (text: string, color: string) => {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) return null;

    // Increased resolution for sharper text
    const fontSize = 64; 
    const font = 'Arial';
    context.font = `bold ${fontSize}px ${font}`;
    
    const metrics = context.measureText(text);
    const textWidth = metrics.width;
    
    // Add padding
    canvas.width = textWidth + 40;
    canvas.height = fontSize + 40;
    
    context.font = `bold ${fontSize}px ${font}`;
    context.fillStyle = color;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    
    // Removed shadow for clean text rendering as requested
    
    context.fillText(text, canvas.width / 2, canvas.height / 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    
    const material = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true, 
        depthTest: false,
    });
    const sprite = new THREE.Sprite(material);
    
    // Adjust scale to match original visual size but with higher resolution texture
    // Original: fontSize 24, scale 0.2 -> effective height ~4.8 world units
    // New: fontSize 64, we need scale ~ 0.075 to match
    const scale = 0.08;
    sprite.scale.set(canvas.width * scale, canvas.height * scale, 1);
    
    return sprite;
};

const createNodeObject = (node: any, dark: boolean) => {
    const type = node.type || '未知';
    
    // In original code: if hidden, color is transparent.
    // So we should respect that.
    
    const isHidden = props.hiddenTypes.includes(type);
    
    // Color
    const defaultColor = dark ? '#60a5fa' : '#3b82f6';
    let color = props.colorMap[type] || defaultColor;
    if (isHidden) color = 'rgba(200,200,200,0.1)';
    
    // Size (Radius)
    // Increased base size for larger nodes
    const baseSize = 8; 
    const radius = Math.sqrt(node.degree || 1) * baseSize;
    
    // Sphere (Increased segments for smoother look)
    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    
    // Use Phong material for better 3D look (shininess)
    const material = new THREE.MeshPhongMaterial({
        color: color,
        transparent: true,
        opacity: isHidden ? 0.1 : (dark ? 0.9 : 0.8),
        shininess: 30,
        emissive: color,
        emissiveIntensity: dark ? 0.2 : 0, // Slight self-emission in dark mode
    });
    const sphere = new THREE.Mesh(geometry, material);
    
    if (isHidden) return sphere;

    const group = new THREE.Group();
    
    // Elegant Glow Style in Dark Mode
    if (dark) {
        // 1. Add Soft Halo Sprite behind the sphere
        const haloMat = new THREE.SpriteMaterial({ 
            map: getHaloTexture(), 
            color: color, 
            transparent: true, 
            opacity: 0.5, // Subtle glow
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });
        const haloSprite = new THREE.Sprite(haloMat);
        const scale = radius * 2.8; // Halo extends beyond sphere
        haloSprite.scale.set(scale, scale, 1);
        group.add(haloSprite);
        
        // 2. Add the physical sphere
        group.add(sphere);
    } else {
        // Light mode: standard sphere
        group.add(sphere);
    }
    
    // Text Label
    // Reduce text brightness to ~0.75 to avoid Bloom (threshold 0.8)
    const textColor = dark ? 'rgba(190,190,190,1)' : 'rgba(30,41,59,0.9)';
    const sprite = createTextSprite(node.name || '', textColor);
    
    if (sprite) {
        sprite.position.y = radius + 2; // Above the sphere
        group.add(sprite);
    }
    
    return group;
};

const initGraph = () => {
    if (!graphDiv.value || !containerRef.value) return;
    
    const width = containerRef.value.clientWidth;
    const height = containerRef.value.clientHeight;
    
    // Determine background color
    const dark = props.darkMode !== undefined ? props.darkMode : isDark.value;
    const bgColor = dark ? '#000000' : '#ffffff'; 
    const linkColor = dark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.4)';
    const linkHoverColor = dark ? '#00f260' : '#059669';

    // Helper to calculate link color based on hover state
    const getLinkColor = (link: any) => {
        if (!dark) return linkColor; // Standard behavior in light mode
        
        // In dark mode: if a node is hovered, highlight connected links
        if (hoverNode.value) {
            // Direct connection
            if (link.source.id === hoverNode.value.id || link.target.id === hoverNode.value.id) {
                return 'rgba(255, 255, 255, 0.9)'; // Bright white/glow
            }
            // Optional: 2nd degree could be handled here if we traverse neighbors, 
            // but for "closest links" direct connection is primary.
            return 'rgba(255, 255, 255, 0.05)'; // Dim others significantly
        }
        
        // Default state (no hover): faint glow
        return 'rgba(255, 255, 255, 0.2)';
    };

    // Clear previous graph if any
    if (graphDiv.value) graphDiv.value.innerHTML = '';

    Graph = (ForceGraph3D as any)()(graphDiv.value)
        .width(width)
        .height(height)
        .backgroundColor(bgColor)
        .nodeLabel('name')
        .linkLabel('label')
        .nodeThreeObject((node: any) => createNodeObject(node, dark))
        // .nodeColor and .nodeVal are replaced by nodeThreeObject but we can keep them for reference or if nodeThreeObject returns null/undefined
        .nodeColor((node: any) => {
            const type = node.type || '未知';
            if (props.hiddenTypes.includes(type)) return 'rgba(200,200,200,0.1)';
            const defaultColor = dark ? '#60a5fa' : '#3b82f6';
            return props.colorMap[type] || defaultColor;
        })
        .nodeVal((node: any) => Math.sqrt(node.degree || 1) * 8) // Sync nodeVal for collision/layout logic if used internally
        .nodeOpacity(dark ? 0.9 : 0.7)
        .linkColor(getLinkColor)
        .linkWidth(dark ? 1.5 : 0.5) // Slightly thicker in dark mode for glow effect visibility
        .linkCurvature(0.2)
        .linkHoverPrecision(2)
        .enableNodeDrag(true)
        .nodeResolution(16)
        .onNodeHover((node: any) => {
            hoverNode.value = node || null;
            if (graphDiv.value) {
                graphDiv.value.style.cursor = node ? 'pointer' : 'default';
            }
            // Trigger update of link colors
            Graph.linkColor(Graph.linkColor()); 
        })
        .onBackgroundClick(() => {
            hoverNode.value = null;
            Graph.linkColor(Graph.linkColor());
        })
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
    
    // Add hover effect manually since linkColor is dynamic function now
    Graph.onLinkHover((link: any) => {
        // We handle hover styling in the main linkColor function via hoverNode state
        // But if we want specific link hover color (green), we can keep this or merge logic.
        // Let's merge: if specific link is hovered, it should be green.
        // We can just rely on the main render loop re-evaluating linkColor if we trigger update.
        // 3d-force-graph onLinkHover triggers re-render automatically usually? No, we need to trigger update.
        
        if (link) {
            // Force update for single link hover
             Graph.linkColor(Graph.linkColor());
        }
    });
        
    // Adjust force engine parameters for better spacing
    Graph.d3Force('charge').strength(-300); // Repel force
    Graph.d3Force('link').distance(100); // Link distance

    // Nebula/Stardust Links in Dark Mode
    if (dark) {
        // Add particles traveling along links to simulate energy flow
        Graph.linkDirectionalParticles(2); // Number of particles per link
        Graph.linkDirectionalParticleWidth(2); // Size of particles
        Graph.linkDirectionalParticleSpeed(0.005); // Speed of flow
        
        // Use a slightly more transparent link color to let particles stand out
        Graph.linkColor(() => 'rgba(255,255,255,0.1)'); 
    } else {
        Graph.linkDirectionalParticles(0); // Disable in light mode
    }

    // Enable Bloom Effect (Only in dark mode)
    if (dark && Graph.postProcessingComposer) {
        // @ts-ignore
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(width, height),
            1.5,
            0.4,
            0.85
        );
        // Fine-tuned Bloom parameters
        // Threshold 0.85 means only very bright things (brightness > 0.85) will glow
        // Link highlight is 0.9, so it glows. Default link is 0.2, no glow.
        // Text is 0.9 (white), so it might glow slightly. Let's adjust text color slightly down if needed, 
        // or just accept slight text glow as consistent with "dark mode".
        // But user said "no special effects for text". 
        // We set text color to rgba(220, 220, 220, 0.9) ~ 0.86 brightness, barely glowing or not at all.
        // Let's adjust text color in createNodeObject to be safe.
        
        bloomPass.threshold = 0.8; 
        bloomPass.strength = 1.2;  
        bloomPass.radius = 0.4;
        
        const composer = Graph.postProcessingComposer();
        composer.addPass(bloomPass);
    }

    updateGraphData();
};

    // Watch for dark mode changes to update background
    watch(isDark, (newVal) => {
        // Re-initialize graph to ensure post-processing and materials are correctly set for the theme
        // This is necessary because UnrealBloomPass from dark mode can cause white screen in light mode
        // and we want clean state.
        if (graphDiv.value) {
            initGraph();
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
