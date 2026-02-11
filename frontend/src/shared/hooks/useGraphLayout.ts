import { ref, reactive, type Ref, watch } from 'vue';
import * as vNG from "v-network-graph";
import { ForceLayout } from "v-network-graph/lib/force-layout";
import type { LayoutType, IGraphNode } from '../types/graph';

export function useGraphLayout(nodes: Ref<Record<string, IGraphNode>>) {
  const currentLayout = ref<LayoutType>('force');
  const layouts = ref<vNG.Layouts>({ nodes: {} });
  const zoomLevel = ref(1);

  // Configs
  const configs = reactive(
    vNG.defineConfigs({
      view: {
        layoutHandler: new ForceLayout({
          positionFixedByDrag: false,
          positionFixedByClickWithAltKey: true,
          createSimulation: (d3: any, nodes: any, edges: any) => {
            const forceLink = d3.forceLink(edges).id((d: any) => d.id)
            return d3
              .forceSimulation(nodes)
              .force("edge", forceLink.distance(150))
              .force("charge", d3.forceManyBody().strength(-800))
              .force("center", d3.forceCenter().strength(0.05))
              .alphaMin(0.001)
          }
        }),
        scalingObjects: true,
        minZoomLevel: 0.1,
        maxZoomLevel: 5,
      },
      node: {
        normal: {
          type: "circle",
          radius: 20,
          color: (n: any) => n.color || "#4466cc",
        },
        label: {
          visible: true,
          direction: "south",
          color: "#000000",
          fontSize: 12,
        },
        // focus: {
        //   color: "#ff8800",
        //   radius: 24
        // }
      },
      edge: {
          normal: {
              color: "#999999",
              width: 2,
          },
          marker: {
              target: {
                  type: "arrow",
                  width: 4,
                  height: 4,
              }
          },
          label: {
              // @ts-ignore
              visible: true,
              fontFamily: "PingFang SC, Microsoft YaHei, sans-serif",
              fontSize: 11,
              lineHeight: 1.1,
              color: "#666666",
              margin: 4,
              background: {
                  visible: true,
                  color: "#ffffff",
                  padding: {
                      vertical: 1,
                      horizontal: 4,
                  },
                  borderRadius: 2,
              },
          }
      }
    })
  );

  const applyGridLayout = () => {
    configs.view!.layoutHandler = new vNG.SimpleLayout()
    
    const nodeIds = Object.keys(nodes.value)
    const count = nodeIds.length
    if (count === 0) return
  
    const cols = Math.ceil(Math.sqrt(count))
    const gap = 160 
    
    const newLayout: Record<string, {x: number, y: number}> = {}
    nodeIds.forEach((nodeId, index) => {
      const row = Math.floor(index / cols)
      const col = index % cols
      newLayout[nodeId] = {
        x: col * gap,
        y: row * gap
      }
    })
    layouts.value = { nodes: newLayout }
  }
  
  const applyCircleLayout = () => {
    configs.view!.layoutHandler = new vNG.SimpleLayout()
    
    const nodeIds = Object.keys(nodes.value)
    const count = nodeIds.length
    if (count === 0) return
  
    const radius = Math.max(count * 30, 300)
    const angleStep = (2 * Math.PI) / count
    
    const newLayout: Record<string, {x: number, y: number}> = {}
    nodeIds.forEach((nodeId, index) => {
      newLayout[nodeId] = {
        x: radius * Math.cos(index * angleStep),
        y: radius * Math.sin(index * angleStep)
      }
    })
    layouts.value = { nodes: newLayout }
  }

  const switchLayout = (type: LayoutType) => {
    currentLayout.value = type
    
    if (type === 'force') {
      configs.view!.layoutHandler = new ForceLayout({
          positionFixedByDrag: false,
          createSimulation: (d3: any, nodes: any, edges: any) => {
            const forceLink = d3.forceLink(edges).id((d: any) => d.id)
            return d3
              .forceSimulation(nodes)
              .force("edge", forceLink.distance(150))
              .force("charge", d3.forceManyBody().strength(-800))
              .force("center", d3.forceCenter().strength(0.05))
              .alphaMin(0.001)
          }
      })
    } else if (type === 'grid') {
      applyGridLayout()
    } else if (type === 'circle') {
      applyCircleLayout()
    } else if (type === '3d') {
      // 3D mode handled by component logic
    }
  }
  
  watch(nodes, () => {
      if (currentLayout.value === 'grid') applyGridLayout()
      if (currentLayout.value === 'circle') applyCircleLayout()
  }, { deep: true })

  return {
    currentLayout,
    layouts,
    configs,
    zoomLevel,
    switchLayout
  };
}
