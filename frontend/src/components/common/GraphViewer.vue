<template>
  <div class="graph-container relative">
    <div class="absolute top-4 right-4 z-10 flex gap-2 bg-white/80 p-1 rounded-lg border border-gray-200 shadow-sm backdrop-blur-sm">
      <a-tooltip title="力导向布局 (Force)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === 'force' }"
          @click="switchLayout('force')"
        >
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 16.5A4.5 4.5 0 1 1 12 7.5a4.5 4.5 0 0 1 0 9zm0-13.5v4.5m0 9v4.5M7.5 12H3m18 0h-4.5"/></svg>
          </template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="网格布局 (Grid)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === 'grid' }"
          @click="switchLayout('grid')"
        >
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          </template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="环形布局 (Circle)">
        <a-button 
          type="text" 
          size="small" 
          :class="{ 'bg-blue-50 text-blue-600': currentLayout === 'circle' }"
          @click="switchLayout('circle')"
        >
          <template #icon>
             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
          </template>
        </a-button>
      </a-tooltip>
    </div>

    <v-network-graph
      v-if="nodes && Object.keys(nodes).length > 0"
      ref="graph"
      class="graph"
      :nodes="nodes"
      :edges="edges"
      :layouts="layouts"
      :configs="configs"
      :event-handlers="eventHandlers"
    >
      <template #edge-label="{ edge, ...slotProps }">
        <v-edge-label :text="edge.label" align="center" vertical-align="above" v-bind="slotProps" />
      </template>
    </v-network-graph>

    <!-- Node Attribute Card -->
    <div v-if="selectedNodeData" class="absolute bottom-4 left-4 z-20 w-64 bg-white p-4 rounded-lg border border-gray-200 shadow-lg backdrop-blur-sm max-h-96 overflow-y-auto">
        <div class="flex justify-between items-start mb-2">
            <h3 class="font-bold text-gray-800">{{ selectedNodeData.name }}</h3>
            <button @click="selectedNodeId = null" class="text-gray-400 hover:text-gray-600">×</button>
        </div>
        <div class="text-xs text-gray-500 mb-3 bg-gray-100 px-2 py-1 rounded inline-block">
            {{ selectedNodeData.type || 'Unknown Type' }}
        </div>
        
        <div v-if="selectedNodeData.attributes && Object.keys(selectedNodeData.attributes).length > 0" class="space-y-2 mb-3">
            <div v-for="(val, key) in selectedNodeData.attributes" :key="key" class="border-b border-gray-100 pb-1 last:border-0">
                <span class="text-xs text-gray-500 block">{{ key }}</span>
                <span class="text-sm text-gray-800 break-words">{{ val }}</span>
            </div>
        </div>
        <div v-else class="text-sm text-gray-400 italic mb-3">
            暂无属性信息
        </div>

        <!-- Source Context Section -->
        <div v-if="selectedNodeData.source_chunks && selectedNodeData.source_chunks.length > 0">
            <div class="text-xs font-bold text-gray-500 mb-1 border-t border-gray-200 pt-2">来源上下文 ({{ selectedNodeData.source_chunks.length }})</div>
            <div class="space-y-2 max-h-40 overflow-y-auto">
                <div v-for="(chunk, idx) in selectedNodeData.source_chunks" :key="idx" class="text-xs text-gray-600 bg-gray-50 p-2 rounded border border-gray-100">
                    <span class="font-mono text-gray-400 mr-1">#{{ chunk.chunk_id + 1 }}</span>
                    {{ chunk.text }}
                </div>
            </div>
        </div>
    </div>

    <div v-else-if="!nodes || Object.keys(nodes).length === 0" class="flex items-center justify-center h-full text-gray-400">
      暂无图谱数据
    </div>
  </div>
</template>

<script setup>
import { defineProps, reactive, ref, watch, computed } from "vue"
import * as vNG from "v-network-graph"
import { ForceLayout } from "v-network-graph/lib/force-layout"

const props = defineProps({
  nodes: Object,
  edges: Object
})

const graph = ref(null)
const currentLayout = ref('force')
const layouts = ref({
  nodes: {}
})

const selectedNodeId = ref(null)

const selectedNodeData = computed(() => {
  if (!selectedNodeId.value || !props.nodes || !props.nodes[selectedNodeId.value]) return null
  return props.nodes[selectedNodeId.value]
})

const eventHandlers = {
  "node:click": ({ node }) => {
    selectedNodeId.value = node
    console.log("Selected Node:", props.nodes[node])
  },
  "view:click": () => {
    selectedNodeId.value = null
  }
}

// 初始化布局
const configs = reactive(
  vNG.defineConfigs({
    view: {
      layoutHandler: new ForceLayout({
        positionFixedByDrag: false,
        positionFixedByClickWithAltKey: true,
        createSimulation: (d3, nodes, edges) => {
          const forceLink = d3.forceLink(edges).id(d => d.id)
          return d3
            .forceSimulation(nodes)
            .force("edge", forceLink.distance(100))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter().strength(0.05))
            .alphaMin(0.001)
        }
      }),
    },
    node: {
      normal: {
        type: "circle",
        radius: 20,
        color: "#4466cc",
      },
      label: {
        visible: true,
        direction: "south",
        color: "#000000",
        fontSize: 12,
      },
    },
    edge: {
        normal: {
            color: "#aaaaaa",
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
            fontSize: 11,
            color: "#666666"
        }
    }
  })
)

const switchLayout = (type) => {
  currentLayout.value = type
  
  if (type === 'force') {
    // 切换回力导向
    configs.view.layoutHandler = new ForceLayout({
        positionFixedByDrag: false,
        createSimulation: (d3, nodes, edges) => {
          const forceLink = d3.forceLink(edges).id(d => d.id)
          return d3
            .forceSimulation(nodes)
            .force("edge", forceLink.distance(100))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter().strength(0.05))
            .alphaMin(0.001)
        }
    })
  } else if (type === 'grid') {
    // 网格布局计算
    applyGridLayout()
  } else if (type === 'circle') {
    // 环形布局计算
    applyCircleLayout()
  }
}

const applyGridLayout = () => {
  // 禁用 Force Layout
  configs.view.layoutHandler = new vNG.SimpleLayout()
  
  const nodeIds = Object.keys(props.nodes)
  const count = nodeIds.length
  if (count === 0) return

  const cols = Math.ceil(Math.sqrt(count))
  const gap = 120 // 间距
  
  const newLayout = {}
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
  // 禁用 Force Layout
  configs.view.layoutHandler = new vNG.SimpleLayout()
  
  const nodeIds = Object.keys(props.nodes)
  const count = nodeIds.length
  if (count === 0) return

  const radius = count * 20 + 50 // 根据节点数动态半径
  const angleStep = (2 * Math.PI) / count
  
  const newLayout = {}
  nodeIds.forEach((nodeId, index) => {
    newLayout[nodeId] = {
      x: radius * Math.cos(index * angleStep),
      y: radius * Math.sin(index * angleStep)
    }
  })
  layouts.value = { nodes: newLayout }
}

// 监听数据变化，如果是静态布局则重新计算
watch(() => props.nodes, () => {
  if (currentLayout.value === 'grid') {
    applyGridLayout()
  } else if (currentLayout.value === 'circle') {
    applyCircleLayout()
  }
})
</script>

<style scoped>
.graph-container {
  width: 100%;
  height: 100%;
  background-color: #f9f9fa;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
}
.graph {
  width: 100%;
  height: 100%;
}
</style>
