import { computed } from 'vue';
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation } from 'd3-force';
import dagre from 'dagre';
import ELK from 'elkjs/lib/elk.bundled.js';
import type { PipelineEdge, PipelineNode } from '../types/pipeline';

export type PipelineLayoutMode =
  | 'grid'
  | 'circle'
  | 'dagre-tb'
  | 'dagre-lr'
  | 'elk-tb'
  | 'elk-lr'
  | 'force';

type NodeSize = { width: number; height: number };
type NodeSizeMap = Record<string, NodeSize>;

const DEFAULT_NODE_SIZE: NodeSize = { width: 160, height: 90 };

const getNodeSize = (sizes: NodeSizeMap | undefined, id: string): NodeSize => {
  return sizes?.[id] ?? DEFAULT_NODE_SIZE;
};

const elk = new ELK();

export function usePipelineLayout() {
  const layoutLabels = computed<Record<PipelineLayoutMode, string>>(() => ({
    grid: '网格',
    circle: '环形',
    'dagre-tb': 'Dagre（上下）',
    'dagre-lr': 'Dagre（左右）',
    'elk-tb': 'ELK（上下）',
    'elk-lr': 'ELK（左右）',
    force: '力导向',
  }));

  const applyLayout = async (params: {
    mode: PipelineLayoutMode;
    nodes: PipelineNode[];
    edges: PipelineEdge[];
    nodeSizes?: NodeSizeMap;
  }): Promise<PipelineNode[]> => {
    const { mode, nodes, edges, nodeSizes } = params;

    if (nodes.length === 0) return nodes;

    if (mode === 'grid') {
      const count = nodes.length;
      const cols = Math.ceil(Math.sqrt(count));
      const gapX = 220;
      const gapY = 150;
      return nodes.map((n, idx) => {
        const row = Math.floor(idx / cols);
        const col = idx % cols;
        return {
          ...n,
          position: {
            x: col * gapX,
            y: row * gapY,
          },
        };
      });
    }

    if (mode === 'circle') {
      const count = nodes.length;
      const radius = Math.max(count * 50, 320);
      const angleStep = (2 * Math.PI) / count;
      return nodes.map((n, idx) => {
        const size = getNodeSize(nodeSizes, n.id);
        const cx = radius * Math.cos(idx * angleStep);
        const cy = radius * Math.sin(idx * angleStep);
        return {
          ...n,
          position: {
            x: cx - size.width / 2,
            y: cy - size.height / 2,
          },
        };
      });
    }

    if (mode === 'elk-tb' || mode === 'elk-lr') {
      const graph = {
        id: 'root',
        layoutOptions: {
          'elk.algorithm': 'layered',
          'elk.direction': mode === 'elk-lr' ? 'RIGHT' : 'DOWN',
          'elk.spacing.nodeNode': '60',
          'elk.layered.spacing.nodeNodeBetweenLayers': '90',
          'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
          'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
        },
        children: nodes.map((n) => {
          const size = getNodeSize(nodeSizes, n.id);
          return {
            id: n.id,
            width: size.width,
            height: size.height,
          };
        }),
        edges: edges
          .filter((e) => e?.source && e?.target && e.source !== e.target)
          .map((e) => ({
            id: e.id,
            sources: [e.source],
            targets: [e.target],
          })),
      };

      const result = await elk.layout(graph as any);
      const posMap = new Map<string, { x: number; y: number }>();
      for (const c of (result?.children ?? []) as any[]) {
        if (c?.id) posMap.set(c.id, { x: c.x ?? 0, y: c.y ?? 0 });
      }

      return nodes.map((n) => {
        const p = posMap.get(n.id);
        if (!p) return n;
        return {
          ...n,
          position: { x: p.x, y: p.y },
        };
      });
    }

    if (mode === 'dagre-tb' || mode === 'dagre-lr') {
      const g = new dagre.graphlib.Graph();
      g.setDefaultEdgeLabel(() => ({}));
      g.setGraph({
        rankdir: mode === 'dagre-lr' ? 'LR' : 'TB',
        nodesep: 60,
        ranksep: 90,
      });

      for (const n of nodes) {
        const size = getNodeSize(nodeSizes, n.id);
        g.setNode(n.id, { width: size.width, height: size.height });
      }

      for (const e of edges) {
        if (!e?.source || !e?.target) continue;
        if (e.source === e.target) continue;
        g.setEdge(e.source, e.target);
      }

      dagre.layout(g);

      return nodes.map((n) => {
        const nodeWithPos = g.node(n.id) as { x: number; y: number; width: number; height: number } | undefined;
        if (!nodeWithPos) return n;
        return {
          ...n,
          position: {
            x: nodeWithPos.x - nodeWithPos.width / 2,
            y: nodeWithPos.y - nodeWithPos.height / 2,
          },
        };
      });
    }

    const simNodes = nodes.map((n) => ({
      id: n.id,
      x: n.position?.x ?? 0,
      y: n.position?.y ?? 0,
    }));

    const simEdges = edges
      .filter((e) => e?.source && e?.target)
      .map((e) => ({ source: e.source, target: e.target }));

    const collideRadius = (d: { id: string }) => {
      const size = getNodeSize(nodeSizes, d.id);
      return Math.max(size.width, size.height) / 2 + 18;
    };

    const simulation = forceSimulation(simNodes as any)
      .force('charge', forceManyBody().strength(-900))
      .force('center', forceCenter(0, 0))
      .force('collide', forceCollide(collideRadius as any).iterations(2))
      .force('link', forceLink(simEdges as any).id((d: any) => d.id).distance(180).strength(0.25))
      .alpha(1)
      .alphaDecay(0.04);

    for (let i = 0; i < 220; i += 1) simulation.tick();
    simulation.stop();

    const posMap = new Map(simNodes.map((n) => [n.id, { x: n.x ?? 0, y: n.y ?? 0 }]));

    return nodes.map((n) => {
      const p = posMap.get(n.id);
      if (!p) return n;
      return {
        ...n,
        position: { x: p.x, y: p.y },
      };
    });
  };

  return {
    layoutLabels,
    applyLayout,
  };
}
