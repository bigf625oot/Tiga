<template>
  <div class="h-full w-full flex flex-col transition-colors duration-300" :class="isLightMode ? 'bg-[#F9FAFB] text-gray-900' : 'bg-black text-white'">
    
    <!-- Header -->
    <div class="h-14 px-6 border-b flex items-center justify-between shrink-0 transition-colors"
      :class="isLightMode ? 'bg-white border-border' : 'bg-black border-gray-800'">
      
      <div class="flex items-center gap-4">
        <Button 
          variant="ghost" 
          size="icon" 
          class="mr-2"
          @click="emit('back')"
          title="返回列表"
        >
          <ArrowLeft class="w-5 h-5" />
        </Button>

        <div class="flex items-center gap-2">
          <div v-if="!isEditingName" 
            @click="startEditingName" 
            class="text-lg font-semibold cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 px-2 py-0.5 rounded transition-colors"
          >
            {{ pipelineName }}
          </div>
          <input 
            v-else
            ref="nameInputRef"
            v-model="pipelineName"
            @blur="finishEditingName"
            @keyup.enter="finishEditingName"
            class="text-lg font-semibold bg-transparent border-b border-blue-500 outline-none px-2 py-0.5 w-64"
          />
        </div>
        <span 
          class="px-1.5 py-0.5 text-[10px] font-semibold rounded border"
          :class="isLightMode ? 'bg-blue-100 text-blue-600 border-blue-200' : 'bg-[#1E3A8A] text-[#60A5FA] border-[#1E40AF]'"
        >实时</span>
        
        <!-- Category Filter -->
        <!-- Moved to sidebar -->
      </div>

      <div class="flex items-center gap-4">


        <!-- Actions -->
        <Button 
          variant="outline" 
          size="sm" 
          class="gap-1.5 mr-2 text-xs font-semibold"
        >
          <Save class="w-3.5 h-3.5" />
          保存
        </Button>

        <Button 
          size="sm" 
          class="gap-1.5 text-xs font-semibold"
        >
          <Play class="w-3.5 h-3.5" />
          运行
        </Button>
        

      </div>
    </div>

    <!-- Main Content -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar: Component Library -->
      <div class="w-64 border-r flex flex-col z-20 transition-colors"
        :class="isLightMode ? 'bg-white border-border' : 'bg-black border-gray-800'">
        
        <div class="p-4 border-b transition-colors" :class="isLightMode ? 'border-border' : 'border-gray-800'">
          <h2 class="text-sm font-semibold mb-3" :class="isLightMode ? 'text-gray-900' : 'text-white'">组件库</h2>
          
          <Select v-model="selectedCategory">
            <SelectTrigger class="w-full h-8 text-xs bg-transparent border-input">
              <SelectValue placeholder="筛选分类" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部显示 (All)</SelectItem>
              <SelectItem value="Extract">数据源 (Extract)</SelectItem>
              <SelectItem value="Transform">转换器 (Transform)</SelectItem>
              <SelectItem value="Graph">图谱构建 (Graph)</SelectItem>
              <SelectItem value="Load">存储端 (Load)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Component List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar px-2 space-y-6 pt-4">
          <!-- Extract -->
          <div v-if="selectedCategory === 'all' || selectedCategory === 'Extract'">
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-blue-500">数据源</div>
            <div class="space-y-2">
              <div v-for="comp in extractComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-blue-300' : 'bg-black border-gray-800 hover:border-blue-500/50'"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <div class="w-8 h-8 rounded flex items-center justify-center bg-blue-500 text-white shrink-0">
                  <component :is="comp.icon" class="w-5 h-5" />
                </div>
                <span class="text-sm font-medium" :class="isLightMode ? 'text-gray-700' : 'text-gray-200'">{{ comp.label }}</span>
              </div>
            </div>
          </div>

          <!-- Transform -->
          <div v-if="selectedCategory === 'all' || selectedCategory === 'Transform'">
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-purple-500">转换器</div>
            <div class="space-y-2">
              <div v-for="comp in transformComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-purple-300' : 'bg-black border-gray-800 hover:border-purple-500/50'"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <div class="w-8 h-8 rounded flex items-center justify-center bg-purple-500 text-white shrink-0">
                  <component :is="comp.icon" class="w-5 h-5" />
                </div>
                <span class="text-sm font-medium" :class="isLightMode ? 'text-gray-700' : 'text-gray-200'">{{ comp.label }}</span>
              </div>
            </div>
          </div>

          <!-- Graph -->
          <div v-if="selectedCategory === 'all' || selectedCategory === 'Graph'">
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-orange-500">图谱构建</div>
            <div class="space-y-2">
              <div v-for="comp in graphComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-orange-300' : 'bg-black border-gray-800 hover:border-orange-500/50'"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <div class="w-8 h-8 rounded flex items-center justify-center bg-orange-500 text-white shrink-0">
                  <component :is="comp.icon" class="w-5 h-5" />
                </div>
                <span class="text-sm font-medium" :class="isLightMode ? 'text-gray-700' : 'text-gray-200'">{{ comp.label }}</span>
              </div>
            </div>
          </div>

          <!-- Load -->
          <div v-if="selectedCategory === 'all' || selectedCategory === 'Load'">
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-green-500">存储端</div>
            <div class="space-y-2">
              <div v-for="comp in loadComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-green-300' : 'bg-black border-gray-800 hover:border-green-500/50'"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <div class="w-8 h-8 rounded flex items-center justify-center bg-green-500 text-white shrink-0">
                  <component :is="comp.icon" class="w-5 h-5" />
                </div>
                <span class="text-sm font-medium" :class="isLightMode ? 'text-gray-700' : 'text-gray-200'">{{ comp.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Canvas Area -->
      <div class="flex-1 relative transition-colors" :class="isLightMode ? 'bg-white' : 'bg-black'">
        <VueFlow
          v-model="nodes"
          v-model:edges="edges"
          :node-types="nodeTypes"
          :default-viewport="{ zoom: 0.8 }"
          :min-zoom="0.2"
          :max-zoom="4"
          fit-view-on-init
          @dragover="onDragOver"
          @drop="onDrop"
        >
          <Background 
            :pattern-color="isLightMode ? '#9CA3AF' : '#3B82F6'" 
            :gap="24" 
            :size="1" 
            variant="dots"
            class="transition-colors duration-300"
            :class="isLightMode ? 'bg-[#F3F4F6] opacity-20' : 'bg-black'"
          />
        </VueFlow>

        <!-- Bottom Stats -->
        <div class="absolute bottom-6 left-6 flex gap-4">
          <div class="border rounded-lg p-4 min-w-[100px]" :class="isLightMode ? 'bg-white border-gray-200' : 'bg-black border-gray-800'">
            <div class="text-[10px] text-gray-500 mb-1">节点总数</div>
            <div class="text-xl font-din font-semibold" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ nodes.length }}</div>
          </div>
          <div class="border rounded-lg p-4 min-w-[100px]" :class="isLightMode ? 'bg-white border-gray-200' : 'bg-black border-gray-800'">
            <div class="text-[10px] text-gray-500 mb-1">连接数</div>
            <div class="text-xl font-din font-semibold" :class="isLightMode ? 'text-gray-900' : 'text-white'">{{ edges.length }}</div>
          </div>
          <div class="border rounded-lg p-4 min-w-[100px]" :class="isLightMode ? 'bg-white border-green-200' : 'bg-[#064E3B] border-[#065F46]'">
            <div class="text-[10px] mb-1" :class="isLightMode ? 'text-green-600' : 'text-green-300'">处理速率</div>
            <div class="text-xl font-din font-semibold" :class="isLightMode ? 'text-green-600' : 'text-[#34D399]'">1.8k/s</div>
          </div>
        </div>

        <!-- Graph Preview (Bottom Right) -->
        <div class="absolute bottom-6 right-6 w-72 h-48 border rounded-lg shadow-2xl overflow-hidden flex flex-col"
             :class="isLightMode ? 'bg-white border-gray-200' : 'bg-black border-gray-800'">
          <div class="p-4 py-2 border-b flex justify-between items-center"
               :class="isLightMode ? 'bg-white border-gray-200' : 'bg-gray-900 border-gray-800'">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              <span class="text-xs font-semibold" :class="isLightMode ? 'text-gray-900' : 'text-white'">图谱预览</span>
            </div>
            <span class="px-1 py-0.5 text-[9px] bg-green-900 text-green-400 rounded border border-green-800">实时</span>
          </div>
          <div class="flex-1 relative p-2 overflow-hidden">
             <!-- Mock Graph Visual -->
             <div class="text-[10px] text-gray-500 mb-2 absolute top-2 left-2 z-10">实时构建中...</div>
             <div class="w-full h-full">
               <VNetworkGraph
                 :nodes="previewNodes"
                 :edges="previewEdges"
                 :configs="previewConfigs"
                 :layouts="previewLayouts"
                 :zoom-level="2.5"
               />
             </div>
             <div class="absolute bottom-2 left-2 text-[9px] text-gray-500 pointer-events-none">
               <div>节点总数 <span class="ml-1" :class="isLightMode ? 'text-gray-900' : 'text-white'">6</span></div>
               <div>关系总数 <span class="ml-1" :class="isLightMode ? 'text-gray-900' : 'text-white'">6</span></div>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h, markRaw, onMounted, reactive } from 'vue';
import { VueFlow, useVueFlow, type Node, type Edge, MarkerType } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { useTheme } from '@/composables/useTheme';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Save, Play, ArrowLeft } from 'lucide-vue-next';
import { VNetworkGraph, defineConfigs } from "v-network-graph"
import { ForceLayout } from "v-network-graph/lib/force-layout"
import "v-network-graph/lib/style.css"

import EtlNode from './components/EtlNode.vue';
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';
import dayjs from 'dayjs';

const { isLightMode, toggleTheme } = useTheme();
const emit = defineEmits(['back']);
const { addNodes, project, findNode } = useVueFlow();

const selectedCategory = ref('all');

// Preview Graph Data
const previewNodes = {
  node1: { name: "N1", color: "#3B82F6" },
  node2: { name: "N2", color: "#A855F7" },
  node3: { name: "N3", color: "#3B82F6" },
  node4: { name: "N4", color: "#10B981" },
  node5: { name: "N5", color: "#A855F7" },
  node6: { name: "N6", color: "#3B82F6" },
};

const previewEdges = {
  edge1: { source: "node1", target: "node2" },
  edge2: { source: "node2", target: "node3" },
  edge3: { source: "node2", target: "node4" },
  edge4: { source: "node3", target: "node5" },
  edge5: { source: "node4", target: "node6" },
  edge6: { source: "node5", target: "node1" },
};

const previewLayouts = reactive({
  nodes: {
    node1: { x: 0, y: 0 },
    node2: { x: 50, y: 50 },
    node3: { x: 100, y: 0 },
    node4: { x: 50, y: -50 },
    node5: { x: 100, y: 50 },
    node6: { x: 0, y: -50 },
  },
});

const previewConfigs = reactive(
  defineConfigs({
    view: {
      layoutHandler: new ForceLayout({
        positionFixedByDrag: false,
        positionFixedByClickWithAltKey: true,
        createSimulation: (d3, nodes, edges) => {
          // d3-force simulation setup
          const forceLink = d3.forceLink(edges).id((d: any) => d.id)
          return d3
            .forceSimulation(nodes)
            .force("edge", forceLink.distance(40))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(0, 0))
            .alphaMin(0.001)
        }
      }),
      scalingObjects: true,
      minZoomLevel: 0.1,
      maxZoomLevel: 16,
      panEnabled: true,
      zoomEnabled: true,
    },
    node: {
      normal: {
        type: "circle",
        radius: 6,
        color: (node: any) => node.color,
      },
      hover: {
        radius: 8,
      },
      label: {
        visible: false,
      },
    },
    edge: {
      normal: {
        width: 1,
        color: "#6B7280",
        dasharray: "0",
        linecap: "butt",
        animate: false,
        animationSpeed: 50,
      },
    },
  })
);

// Pipeline Name Management
const generatePipelineName = () => {
  const dateStr = dayjs().format('YYYYMMDD');
  const randomNum = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `流水线_${dateStr}_${randomNum}`;
};

const pipelineName = ref(generatePipelineName());
const isEditingName = ref(false);
const nameInputRef = ref<HTMLInputElement | null>(null);

const startEditingName = () => {
  isEditingName.value = true;
  // Focus input on next tick
  setTimeout(() => nameInputRef.value?.focus(), 0);
};

const finishEditingName = () => {
  if (!pipelineName.value.trim()) {
    pipelineName.value = generatePipelineName();
  }
  isEditingName.value = false;
};

// Icons
const IconServer = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" })]);
const IconGlobe = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" })]);
const IconDatabase = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" })]);
const IconSparkles = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 3.214L13 21l-2.286-6.857L5 12l5.714-3.214L13 3z" })]);
const IconFilter = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" })]);
const IconShield = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" })]);
const IconGraph = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" })]);
const IconApi = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" })]);
const IconDuplicate = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" })]);
const IconWand = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" })]);
const IconMask = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" })]);
const IconMap = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" })]);
const IconAggregation = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" })]);
const IconList = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M4 6h16M4 10h16M4 14h16M4 18h16" })]);
const IconAssign = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" })]);
const IconData = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" })]);
const IconText = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" })]);
const IconCode = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" })]);
const IconNer = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" })]);
const IconRelation = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" })]);
const IconAttribute = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" })]);
const IconAlignment = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" })]); // Reusing Map icon for alignment concept or similar

const extractComponents = [
  { type: 'sftp', label: 'SFTP 数据源', icon: IconServer, category: 'Extract' },
  { type: 'crawler', label: 'Web 爬虫', icon: IconGlobe, category: 'Extract' },
  { type: 'database', label: 'SQL 数据库', icon: IconDatabase, category: 'Extract' },
  { type: 'api', label: 'API 接口', icon: IconApi, category: 'Extract' },
];

const transformComponents = [
  { type: 'llm', label: 'LLM 语义分块', icon: IconSparkles, category: 'Transform' },
  { type: 'filter', label: '正则清洗', icon: IconFilter, category: 'Transform' },
  { type: 'shield', label: 'Pydantic 校验', icon: IconShield, category: 'Transform' },
  { type: 'dedup', label: '去重', icon: IconDuplicate, category: 'Transform' },
  { type: 'fill', label: '缺失值填充', icon: IconWand, category: 'Transform' },
  { type: 'mask', label: '隐私脱敏', icon: IconMask, category: 'Transform' },
  { type: 'map', label: '字段映射', icon: IconMap, category: 'Transform' },
  { type: 'aggregation', label: '变量聚合', icon: IconAggregation, category: 'Transform' },
  { type: 'list', label: '列表操作', icon: IconList, category: 'Transform' },
  { type: 'assign', label: '变量赋值器', icon: IconAssign, category: 'Transform' },
  { type: 'data_manipulation', label: '数据操作', icon: IconData, category: 'Transform' },
  { type: 'text_process', label: '文本处理', icon: IconText, category: 'Transform' },
  { type: 'code', label: 'Python 代码', icon: IconCode, category: 'Transform' },
];

const graphComponents = [
  { type: 'ner', label: 'NER 实体识别', icon: IconNer, category: 'Graph' },
  { type: 'relation', label: '关系抽取', icon: IconRelation, category: 'Graph' },
  { type: 'attribute', label: '属性提取', icon: IconAttribute, category: 'Graph' },
  { type: 'alignment', label: '实体对齐', icon: IconAlignment, category: 'Graph' },
];

const loadComponents = [
  { type: 'neo4j', label: 'Neo4j 图库', icon: IconGraph, category: 'Load' },
  { type: 'vector', label: '向量库', icon: IconDatabase, category: 'Load' },
];

const nodeTypes = {
  custom: markRaw(EtlNode),
};

const nodes = ref<Node[]>([
  { id: '1', type: 'custom', position: { x: 100, y: 100 }, data: { label: 'SFTP 数据源', category: 'Extract', icon: 'sftp', status: 'ok' } },
  { id: '2', type: 'custom', position: { x: 400, y: 100 }, data: { label: 'PyMuPDF 解析', category: 'Transform', icon: 'document', status: 'ok' } },
  { id: '3', type: 'custom', position: { x: 700, y: 100 }, data: { label: 'LLM 语义分块', category: 'Transform', icon: 'llm', status: 'ok' } },
  { id: '4', type: 'custom', position: { x: 1000, y: 100 }, data: { label: 'Neo4j 图库', category: 'Load', icon: 'graph', status: 'ok', metrics: { label: 'Load', value: 'OK' } } },
]);

const edges = ref<Edge[]>([
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#3B82F6', strokeWidth: 2 } },
  { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#8B5CF6', strokeWidth: 2 } },
  { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#10B981', strokeWidth: 2 } },
]);

// Drag & Drop
const onDragStart = (event: DragEvent, nodeData: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
  }
};

const onDragOver = (event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move';
  }
};

const onDrop = (event: DragEvent) => {
  const dataStr = event.dataTransfer?.getData('application/vueflow');
  if (!dataStr) return;
  
  const nodeData = JSON.parse(dataStr);
  const { left, top } = document.querySelector('.vue-flow__renderer')?.getBoundingClientRect() || { left: 0, top: 0 };
  
  const position = project({
    x: event.clientX - left,
    y: event.clientY - top,
  });

  const newNode: Node = {
    id: `node-${nodes.value.length + 1}`,
    type: 'custom',
    position,
    data: { 
      label: nodeData.label, 
      category: nodeData.category,
      icon: nodeData.type,
      status: 'ok'
    },
  };

  addNodes([newNode]);
};
</script>

<style>
/* Custom Scrollbar for Sidebar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 2px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: #4B5563;
}
.light .custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: #D1D5DB;
}
</style>
