<template>
  <div ref="containerEl" class="graph-container relative" :class="{ 'is-fullscreen': fullscreen }" @keydown.esc="exitFullscreen" tabindex="0">
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
      :nodes="styledNodes"
      :edges="filteredEdges"
      :style="{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`, transformOrigin: 'center center' }"
      :layouts="layouts"
      :configs="configs"
      :event-handlers="eventHandlers"
    >
      <template #edge-label="{ edge, ...slotProps }">
        <v-edge-label :text="edge.label" align="center" vertical-align="above" v-bind="slotProps" />
      </template>
    </v-network-graph>

    <div v-if="selectedNodeData" class="absolute bottom-4 left-4 z-20 w-80 bg-white p-4 rounded-lg border border-gray-200 shadow-xl backdrop-blur-md max-h-[80%] flex flex-col">
        <div class="flex justify-between items-start mb-2 flex-shrink-0">
            <h3 class="font-bold text-gray-800 text-lg">{{ selectedNodeData.name }}</h3>
            <button @click="selectedNodeId = null" class="text-gray-400 hover:text-gray-600 p-1">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="flex-shrink-0 mb-3">
            <span class="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded font-medium border border-blue-100">
                {{ selectedNodeData.type || '未知类型' }}
            </span>
        </div>
        
        <div class="overflow-y-auto custom-scrollbar flex-grow pr-2">
            <div v-if="selectedNodeData.attributes && Object.keys(selectedNodeData.attributes).length > 0" class="space-y-4">
                <div v-for="(val, key) in selectedNodeData.attributes" :key="key" class="group">
                    <!-- Internal / Hidden fields: Ignore anything starting with _ or specific junk keys -->
                    <template v-if="key.startsWith('_') || ['source_content', 'entity_id', 'truncate', 'source_id', 'chunk_id'].includes(key.toLowerCase())"></template>

                    <!-- Chunks / Source IDs (Card Style) -->
                    <template v-else-if="key === 'chunks'">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 block">来源原文 (Chunks)</span>
                        <div class="grid grid-cols-1 gap-2">
                            <a-popover v-for="(chunk, idx) in val" :key="idx" placement="right">
                                <template #content>
                                    <div class="max-w-md p-2 text-xs leading-relaxed text-gray-700">
                                        <div class="font-bold text-blue-600 mb-2 border-b pb-1">原文片段 #{{ idx + 1 }}</div>
                                        {{ chunk.content || '暂无原文内容' }}
                                    </div>
                                </template>
                                <div class="cursor-help bg-slate-50 border border-slate-200 rounded-md p-2 hover:bg-blue-50 hover:border-blue-300 transition-all shadow-sm">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-[10px] font-mono text-slate-400">ID: {{ chunk.id.substring(0, 8) }}...</span>
                                        <span class="text-[10px] bg-white px-1 border border-slate-200 rounded text-slate-500">#{{ idx + 1 }}</span>
                                    </div>
                                    <div class="text-[11px] text-slate-600 line-clamp-2 italic">
                                        {{ chunk.content || '悬停查看原文...' }}
                                    </div>
                                </div>
                            </a-popover>
                        </div>
                    </template>

                    <!-- File Name (Primary focus) - Hide 'file_path' if 'file_name' exists to avoid duplication -->
                    <template v-else-if="key === 'file_name' || (key === 'file_path' && !selectedNodeData.attributes.file_name)">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1 block">来源文件</span>
                        <div class="flex items-center gap-2 text-blue-600 bg-blue-50/50 p-2 rounded border border-blue-100">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
                            <span class="text-sm font-medium truncate" :title="val">{{ val }}</span>
                        </div>
                    </template>

                    <!-- Ignore file_path if we are already showing file_name -->
                    <template v-else-if="key === 'file_path' && selectedNodeData.attributes.file_name"></template>

                    <!-- Time -->
                    <template v-else-if="key === 'created_at'">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1 block">创建时间</span>
                        <span class="text-sm text-gray-600 flex items-center gap-2">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            {{ val }}
                        </span>
                    </template>

                    <!-- Other fields -->
                    <template v-else>
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1 block">{{ key }}</span>
                        <span class="text-sm text-gray-700 leading-snug break-words">{{ val }}</span>
                    </template>
                </div>
            </div>
            <div v-else class="text-center py-10">
                <div class="text-gray-300 mb-2">
                    <svg class="mx-auto" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/><circle cx="12" cy="15" r="3"/></svg>
                </div>
                <div class="text-sm text-gray-400">暂无属性信息</div>
            </div>
        </div>
    </div>

    <div v-else-if="!nodes || Object.keys(nodes).length === 0" class="flex items-center justify-center h-full text-gray-400">
      <div class="flex flex-col items-center gap-2">
        <div>暂无图谱数据</div>
        <button v-if="reload" @click="reload()" class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-slate-50">
          重新加载
        </button>
      </div>
    </div>
    <!-- Toolbar -->
    <div class="graph-toolbar" role="toolbar" aria-label="Graph tools">
      <button class="tool-btn" @click="showTools = !showTools" aria-label="切换工具栏" title="切换工具栏">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4V6zm0 5h10v2H4v-2zm0 5h16v2H4v-2z"/></svg>
      </button>
      <button v-show="showTools" class="tool-btn" :disabled="fullscreen" @click="enterFullscreen" aria-label="最大化" title="最大化 (F)">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M4 4h7v2H6v5H4V4zm10 0h6v6h-2V6h-4V4zm6 10v6h-6v-2h4v-4h2zM4 14h2v4h4v2H4v-6z"/></svg>
      </button>
      <button v-show="showTools && fullscreen" class="tool-btn" @click="exitFullscreen" aria-label="最小化" title="最小化 (Esc)">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M6 6h4v2H8v2H6V6zm10 0h2v4h-2V8h-2V6h2zM6 14h2v2h2v2H6v-4zm10 0h2v4h-4v-2h2v-2z"/></svg>
      </button>
      <button v-show="showTools" class="tool-btn" :disabled="!selectedNodeId" @click="focusOnSelected" aria-label="定位到选中" title="地图定位 (G)">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 8a4 4 0 1 1 0 8a4 4 0 0 1 0-8m0-6a1 1 0 0 1 1 1v2.06a8 8 0 0 1 6.94 6.94H22a1 1 0 1 1 0 2h-2.06a8 8 0 0 1-6.94 6.94V22a1 1 0 1 1-2 0v-2.06A8 8 0 0 1 4.06 14H2a1 1 0 1 1 0-2h2.06A8 8 0 0 1 11 5.06V3a1 1 0 0 1 1-1Z"/></svg>
      </button>
      <button v-show="showTools" class="tool-btn" @click="zoomIn" aria-label="放大" title="放大 (Ctrl +)">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M11 11V6h2v5h5v2h-5v5h-2v-5H6v-2h5Z"/></svg>
      </button>
      <button v-show="showTools" class="tool-btn" @click="zoomOut" aria-label="缩小" title="缩小 (Ctrl -)">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M6 11h12v2H6z"/></svg>
      </button>
      <span v-show="showTools" class="zoom-indicator" :aria-label="`缩放比例 ${Math.round(scale*100)}%`">{{ Math.round(scale*100) }}%</span>
      <button
        v-show="showTools"
        class="px-2 py-0.5 text-[11px] transition-all ml-1"
        :class="props.scope === 'doc' ? 'bg-blue-600 text-white' : 'text-[#2a2f3c]'"
        @click="props.switchScope && props.switchScope('doc')"
        aria-label="当前文档"
        title="当前文档"
      >当前文档</button>
      <button
        v-show="showTools"
        class="px-2 py-0.5 text-[11px] transition-all"
        :class="props.scope === 'global' ? 'bg-blue-600 text-white' : 'text-[#2a2f3c]'"
        @click="props.switchScope && props.switchScope('global')"
        aria-label="全部文档"
        title="全部文档"
      >全部文档</button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, reactive, ref, watch, computed } from "vue"
import * as vNG from "v-network-graph"
import { ForceLayout } from "v-network-graph/lib/force-layout"
import { filterEdges as filterEdgesUtil } from "@/utils/graphFilter"

const props = defineProps({
  nodes: Object,
  edges: Object,
  hiddenTypes: { type: Array, default: () => [] },
  colorMap: { type: Object, default: () => ({}) },
  reload: { type: Function, default: null },
  scope: { type: String, default: null },
  switchScope: { type: Function, default: null }
})

const graph = ref(null)
const containerEl = ref(null)
const currentLayout = ref('force')
const layouts = ref({
  nodes: {}
})

const selectedNodeId = ref(null)
const fullscreen = ref(false)
const scale = ref(1)
const showTools = ref(true)
const pan = reactive({ x: 0, y: 0 })
const isPanning = ref(false)
const lastPos = reactive({ x: 0, y: 0 })
const spacePressed = ref(false)

const selectedNodeData = computed(() => {
  if (!selectedNodeId.value || !props.nodes || !props.nodes[selectedNodeId.value]) return null
  return props.nodes[selectedNodeId.value]
})

// Styled nodes with color
const styledNodes = computed(() => {
  if (!props.nodes) return {}
  const out = {}
  Object.keys(props.nodes).forEach(id => {
    const n = props.nodes[id]
    const type = (n.type || '').toLowerCase()
    const color = props.colorMap[type] || "#4466cc"
    out[id] = { ...n, color }
  })
  return out
})

// Filter edges if either node hidden
const filteredEdges = computed(() => filterEdgesUtil(props.nodes || {}, props.edges || {}, (props.hiddenTypes || []).map(s => s.toLowerCase())))

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
      scalingObjects: true
    },
    node: {
      normal: {
        type: "circle",
        radius: 20,
        color: (n) => n.color || "#4466cc",
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
// fullscreen
const enterFullscreen = () => { fullscreen.value = true; try { document.body.style.overflow = 'hidden' } catch (e) {} }
const exitFullscreen = () => { fullscreen.value = false; try { document.body.style.overflow = '' } catch (e) {} }

// zoom
const zoomIn = () => { scale.value = Math.min(3, scale.value + 0.25) }
const zoomOut = () => { scale.value = Math.max(0.25, scale.value - 0.25) }
const onWheel = (e) => { 
  e.preventDefault()
  const rect = containerEl.value?.getBoundingClientRect?.()
  const mx = e.clientX - (rect?.left ?? 0)
  const my = e.clientY - (rect?.top ?? 0)
  const oldScale = scale.value
  const zoomStep = 0.25
  const newScale = e.deltaY < 0 ? Math.min(3, oldScale + zoomStep) : Math.max(0.25, oldScale - zoomStep)
  const factor = newScale / oldScale
  pan.x = mx - factor * (mx - pan.x)
  pan.y = my - factor * (my - pan.y)
  scale.value = newScale
}

// focus selected
const focusOnSelected = () => {
  if (!selectedNodeId.value) return
  focusNode(selectedNodeId.value)
}

const focusNode = (nodeId) => {
  if (!nodeId || !props.nodes[nodeId]) return
  
  selectedNodeId.value = nodeId
  
  // Use v-network-graph's focusNode if available
  if (graph.value) {
    try {
      // Get node position from layouts
      const pos = layouts.value.nodes[nodeId]
      if (pos) {
        // Simple pan to position
        pan.x = -pos.x * scale.value + (containerEl.value?.clientWidth / 2 || 0)
        pan.y = -pos.y * scale.value + (containerEl.value?.clientHeight / 2 || 0)
      } else {
        // If no fixed position (force layout), we might need to wait for simulation or just let it be
        // For now, selecting it is enough as the attribute card will show up
      }
    } catch (e) {
      console.warn("Focus node failed:", e)
    }
  }
}

defineExpose({
  focusNode
})

// keyboard shortcuts
const onKeydown = (e) => {
  if (e.ctrlKey && e.key === "+") { e.preventDefault(); zoomIn() }
  if (e.ctrlKey && e.key === "-") { e.preventDefault(); zoomOut() }
  if (e.key.toLowerCase() === "g") { e.preventDefault(); focusOnSelected() }
  if (e.key.toLowerCase() === "f") { e.preventDefault(); enterFullscreen() }
  if (e.code === "Space") { spacePressed.value = true }
}
const onKeyup = (e) => { if (e.code === "Space") spacePressed.value = false }
const onMouseDown = (e) => {
  if (e.button === 1 || spacePressed.value) {
    isPanning.value = true
    lastPos.x = e.clientX
    lastPos.y = e.clientY
    e.preventDefault()
  }
}
const onMouseMove = (e) => {
  if (!isPanning.value) return
  const dx = e.clientX - lastPos.x
  const dy = e.clientY - lastPos.y
  pan.x += dx
  pan.y += dy
  lastPos.x = e.clientX
  lastPos.y = e.clientY
}
const onMouseUp = () => { isPanning.value = false }

// bind wheel and keydown
watch(containerEl, (el) => { 
  if (el) {
    el.addEventListener("wheel", onWheel, { passive: false })
    el.addEventListener("mousedown", onMouseDown)
    el.addEventListener("mousemove", onMouseMove)
    el.addEventListener("mouseup", onMouseUp)
    el.addEventListener("mouseleave", onMouseUp)
  }
})
if (typeof window !== "undefined") { window.addEventListener("keydown", onKeydown) }
if (typeof window !== "undefined") { window.addEventListener("keyup", onKeyup) }
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
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #999;
}
/* Ensure scrollbar is always visible in the container */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #ccc #f1f1f1;
}
.graph-toolbar {
  position: absolute;
  right: 8px;
  bottom: 8px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: rgba(255,255,255,0.9);
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.tool-btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #2a2f3c;
  background: #f3f4f6;
  transition: all .2s ease;
}
.tool-btn:hover { background: #e5e6eb }
.tool-btn:disabled { opacity: .4; cursor: not-allowed }
.zoom-indicator {
  font-size: 12px;
  color: #666;
  min-width: 36px;
  text-align: right;
}
.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #ffffff;
  border-radius: 0;
  border: none;
}
</style>
