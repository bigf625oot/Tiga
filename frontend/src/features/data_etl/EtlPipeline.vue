<template>
  <div class="h-full w-full flex flex-col transition-colors duration-300" :class="isLightMode ? 'bg-[#F9FAFB] text-gray-900' : 'bg-[#0B0C10] text-white'">
    
    <!-- Header -->
    <div class="h-14 px-6 border-b flex items-center justify-between shrink-0 transition-colors"
      :class="isLightMode ? 'bg-white border-border' : 'bg-[#0B0C10] border-gray-800'">
      
      <div class="flex items-center gap-4">
        <button 
          @click="emit('back')"
          class="p-1.5 rounded-full transition-colors mr-1"
          :class="isLightMode ? 'hover:bg-gray-100 text-gray-600' : 'hover:bg-gray-800 text-gray-400'"
          title="返回列表"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>

        <h1 class="text-lg font-semibold flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          ETL 流水线编辑器
        </h1>
        <span class="px-1.5 py-0.5 text-[10px] font-semibold bg-[#1E3A8A] text-[#60A5FA] rounded border border-[#1E40AF]">LIVE</span>
        
        <!-- Legends -->
        <div class="flex items-center gap-4 ml-4 text-xs">
          <div class="flex items-center gap-1.5">
            <div class="w-2.5 h-2.5 rounded bg-blue-500"></div>
            <span :class="isLightMode ? 'text-gray-600' : 'text-gray-400'">Extract</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-2.5 h-2.5 rounded bg-purple-500"></div>
            <span :class="isLightMode ? 'text-gray-600' : 'text-gray-400'">Transform</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-2.5 h-2.5 rounded bg-green-500"></div>
            <span :class="isLightMode ? 'text-gray-600' : 'text-gray-400'">Load</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- View Toggle -->
        <div class="flex rounded-lg border overflow-hidden p-0.5 text-xs"
          :class="isLightMode ? 'bg-gray-100 border-border' : 'bg-gray-800 border-gray-700'">
          <button class="p-4 py-1 rounded transition-colors" :class="isLightMode ? 'bg-white shadow-sm text-primary' : 'bg-gray-700 text-white'">标准视图</button>
          <button class="p-4 py-1 rounded transition-colors" :class="isLightMode ? 'text-gray-500 hover:text-gray-700' : 'text-gray-400 hover:text-gray-200'">DAG 高级视图</button>
        </div>

        <div class="w-px h-4 bg-gray-700 mx-1"></div>

        <!-- Actions -->
        <button class="flex items-center gap-1.5 p-4 py-1.5 rounded bg-green-900/30 text-green-400 border border-green-800 hover:bg-green-900/50 transition-colors text-xs font-semibold">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          运行
        </button>
        
        <button class="p-1.5 rounded hover:bg-gray-800 transition-colors text-gray-400">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
        </button>
        <button class="p-1.5 rounded hover:bg-gray-800 transition-colors text-gray-400">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar: Component Library -->
      <div class="w-64 border-r flex flex-col z-20 transition-colors"
        :class="isLightMode ? 'bg-white border-border' : 'bg-[#0B0C10] border-gray-800'">
        
        <div class="p-4 border-b transition-colors" :class="isLightMode ? 'border-border' : 'border-gray-800'">
          <h2 class="text-sm font-semibold mb-1" :class="isLightMode ? 'text-gray-900' : 'text-white'">组件库</h2>
          <p class="text-xs" :class="isLightMode ? 'text-gray-500' : 'text-gray-500'">拖拽添加组件到画布</p>
        </div>

        <!-- File Upload Area -->
        <div class="p-4">
          <div class="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors group"
            :class="isLightMode ? 'border-border hover:border-blue-400 bg-gray-50' : 'border-gray-700 hover:border-blue-500 bg-[#111827]'">
            <svg class="w-6 h-6 mx-auto mb-2 text-gray-400 group-hover:text-blue-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div class="text-xs font-medium" :class="isLightMode ? 'text-gray-700' : 'text-gray-300'">点击选择文件</div>
            <div class="text-[10px] text-gray-500 mt-1">或拖拽到此处</div>
          </div>
        </div>

        <!-- Component List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar px-2 space-y-6">
          <!-- Extract -->
          <div>
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-blue-500">数据源 (Extract)</div>
            <div class="space-y-2">
              <div v-for="comp in extractComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-blue-300' : 'bg-[#1F2937] border-gray-700 hover:border-blue-500/50'"
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
          <div>
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-purple-500">转换器 (Transform)</div>
            <div class="space-y-2">
              <div v-for="comp in transformComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-purple-300' : 'bg-[#1F2937] border-gray-700 hover:border-purple-500/50'"
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

          <!-- Load -->
          <div>
            <div class="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-green-500">存储端 (Load)</div>
            <div class="space-y-2">
              <div v-for="comp in loadComponents" :key="comp.type" 
                class="flex items-center gap-4 p-4 rounded-lg cursor-grab border transition-all hover:-translate-y-0.5 hover:shadow-md"
                :class="isLightMode ? 'bg-white border-border hover:border-green-300' : 'bg-[#1F2937] border-gray-700 hover:border-green-500/50'"
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
      <div class="flex-1 relative bg-[#000]">
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
            :class="isLightMode ? 'bg-[#F3F4F6] opacity-20' : 'bg-[#000] opacity-20'"
          />
        </VueFlow>

        <!-- Bottom Stats -->
        <div class="absolute bottom-6 left-6 flex gap-4">
          <div class="bg-[#111827] border border-gray-700 rounded-lg p-4 min-w-[100px]">
            <div class="text-[10px] text-gray-500 mb-1">节点总数</div>
            <div class="text-xl font-din font-semibold text-white">{{ nodes.length }}</div>
          </div>
          <div class="bg-[#111827] border border-gray-700 rounded-lg p-4 min-w-[100px]">
            <div class="text-[10px] text-gray-500 mb-1">连接数</div>
            <div class="text-xl font-din font-semibold text-white">{{ edges.length }}</div>
          </div>
          <div class="bg-[#064E3B] border border-[#065F46] rounded-lg p-4 min-w-[100px]">
            <div class="text-[10px] text-green-300 mb-1">处理速率</div>
            <div class="text-xl font-din font-semibold text-[#34D399]">1.8k/s</div>
          </div>
        </div>

        <!-- Graph Preview (Bottom Right) -->
        <div class="absolute bottom-6 right-6 w-72 h-48 bg-[#111827] border border-gray-700 rounded-lg shadow-2xl overflow-hidden flex flex-col">
          <div class="p-4 py-2 border-b border-gray-700 flex justify-between items-center bg-[#1F2937]">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              <span class="text-xs font-semibold text-white">图谱预览</span>
            </div>
            <span class="px-1 py-0.5 text-[9px] bg-green-900 text-green-400 rounded border border-green-800">LIVE</span>
          </div>
          <div class="flex-1 relative p-2">
             <!-- Mock Graph Visual -->
             <div class="text-[10px] text-gray-500 mb-2">实时构建中...</div>
             <div class="absolute inset-0 flex items-center justify-center opacity-50">
                <!-- Simple CSS Graph representation -->
                <div class="relative w-full h-full">
                  <div class="absolute top-1/2 left-1/4 w-3 h-3 bg-blue-500 rounded-full"></div>
                  <div class="absolute top-1/3 left-1/2 w-3 h-3 bg-purple-500 rounded-full"></div>
                  <div class="absolute top-2/3 left-2/3 w-3 h-3 bg-blue-500 rounded-full"></div>
                  <svg class="absolute inset-0 w-full h-full pointer-events-none">
                    <line x1="25%" y1="50%" x2="50%" y2="33%" stroke="#4B5563" stroke-width="1" />
                    <line x1="50%" y1="33%" x2="66%" y2="66%" stroke="#4B5563" stroke-width="1" />
                  </svg>
                </div>
             </div>
             <div class="absolute bottom-2 left-2 text-[9px] text-gray-500">
               <div>节点总数 <span class="text-white ml-1">8</span></div>
               <div>关系总数 <span class="text-white ml-1">8</span></div>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h, markRaw } from 'vue';
import { VueFlow, useVueFlow, type Node, type Edge, MarkerType } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { useTheme } from '@/composables/useTheme';
import EtlNode from './components/EtlNode.vue';
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';

const { isLightMode, toggleTheme } = useTheme();
const emit = defineEmits(['back']);
const { addNodes, project, findNode } = useVueFlow();

// Icons
const IconServer = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" })]);
const IconGlobe = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" })]);
const IconDatabase = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" })]);
const IconSparkles = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 3.214L13 21l-2.286-6.857L5 12l5.714-3.214L13 3z" })]);
const IconFilter = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" })]);
const IconShield = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" })]);
const IconGraph = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" })]);

const extractComponents = [
  { type: 'sftp', label: 'SFTP 数据源', icon: IconServer, category: 'Extract' },
  { type: 'crawler', label: 'Web 爬虫', icon: IconGlobe, category: 'Extract' },
  { type: 'database', label: 'SQL 数据库', icon: IconDatabase, category: 'Extract' },
];

const transformComponents = [
  { type: 'llm', label: 'LLM 语义分块', icon: IconSparkles, category: 'Transform' },
  { type: 'filter', label: '正则清洗', icon: IconFilter, category: 'Transform' },
  { type: 'shield', label: 'Pydantic 校验', icon: IconShield, category: 'Transform' },
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
  background: #4B5563;
  border-radius: 2px;
}
.light .custom-scrollbar::-webkit-scrollbar-thumb {
  background: #D1D5DB;
}
</style>
