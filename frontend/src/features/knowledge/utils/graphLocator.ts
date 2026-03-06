import { ref, type Ref } from 'vue';
import type { IGraphNode } from '@/shared/types/graph';

export interface GraphLocatorContext {
    nodes: Ref<Record<string, IGraphNode>>;
    layouts: Ref<any>;
    onNodeClick?: (nodeId: string, node: IGraphNode) => void;
}

/**
 * Abstract Graph Locator Adapter
 */
export class GraphLocatorAdapter {
    protected engine: Ref<any>;
    protected context: GraphLocatorContext;

    constructor(engine: Ref<any>, context: GraphLocatorContext) {
        this.engine = engine;
        this.context = context;
    }

    /**
     * Locate a node in the graph
     */
    async locateNode(nodeId: string): Promise<void> {
        throw new Error("Method not implemented");
    }

    /**
     * Clear highlights
     */
    clearHighlights(): void {
        throw new Error("Method not implemented");
    }
}

/**
 * Adapter for v-network-graph
 */
export class VNetworkGraphLocator extends GraphLocatorAdapter {
    private highlightedNodes: Ref<Set<string>>;
    private maxHighlights: number;

    constructor(engine: Ref<any>, context: GraphLocatorContext) {
        super(engine, context);
        this.highlightedNodes = ref(new Set());
        this.maxHighlights = 3;
    }

    async locateNode(nodeId: string): Promise<void> {
        if (!this.engine || !this.engine.value) {
            console.warn("Graph engine not initialized");
            return;
        }

        const graph = this.engine.value;
        const { nodes, layouts } = this.context;

        if (!nodes.value[nodeId]) {
            console.warn(`Node ${nodeId} not found in graph`);
            return;
        }

        // 1. Manage Highlights (Queue of 3)
        if (this.highlightedNodes.value.has(nodeId)) {
            // Already highlighted, maybe just re-center
        } else {
            if (this.highlightedNodes.value.size >= this.maxHighlights) {
                // Remove oldest (first item in Set iterator)
                const first = this.highlightedNodes.value.values().next().value;
                if (first) this.highlightedNodes.value.delete(first);
            }
            this.highlightedNodes.value.add(nodeId);
        }

        // 2. Center and Zoom
        // Get node position
        const pos = layouts.value.nodes?.[nodeId];
        if (pos) {
            // v-network-graph panTo/zoomTo
            if (typeof graph.transitionWhile === 'function') {
                graph.transitionWhile(() => {
                    graph.setView({
                        pan: { x: pos.x, y: pos.y },
                        zoom: 1.5, // Arbitrary zoom level for "focus"
                    });
                }, { duration: 800 });
            }
        }

        // 3. Trigger Side Panel (Callback)
        if (this.context.onNodeClick) {
            this.context.onNodeClick(nodeId, nodes.value[nodeId]);
        }
    }

    clearHighlights(): void {
        this.highlightedNodes.value.clear();
    }
}

export type GraphEngineType = 'v-network-graph' | '3d';

export const createGraphLocator = (type: GraphEngineType | string, engine: Ref<any>, context: GraphLocatorContext): GraphLocatorAdapter => {
    switch (type) {
        case 'v-network-graph':
            return new VNetworkGraphLocator(engine, context);
        default:
            console.warn(`Unsupported graph engine type: ${type}`);
            return new GraphLocatorAdapter(engine, context);
    }
};
