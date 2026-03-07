<template>
  <div 
    class="flex flex-col h-full w-full overflow-hidden font-sans transition-colors duration-300"
    :class="isLightMode ? 'bg-[#F9FAFB] text-gray-900' : 'bg-[#0B0C10] text-white'"
  >
    <DashboardHeader />

    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar: Data Sources -->
      <div 
        class="w-80 border-r flex flex-col z-20 transition-colors duration-300"
        :class="isLightMode ? 'bg-white border-border' : 'bg-[#0B0C10] border-gray-800'"
      >
        <div 
          class="p-4 border-b transition-colors"
          :class="isLightMode ? 'border-border' : 'border-gray-800'"
        >
          <h2 
            class="text-[14px] font-semibold uppercase tracking-wider mb-1"
            :class="isLightMode ? 'text-gray-500' : 'text-gray-400'"
          >数据源</h2>
          <div 
            class="text-[13px]"
            :class="isLightMode ? 'text-gray-500' : 'text-gray-600'"
          >{{ dataSources.length }} 个活跃数据源</div>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          <button 
            class="w-full p-4 border border-dashed rounded-lg transition-colors flex items-center justify-center gap-2 group mb-4"
            :class="isLightMode ? 'border-border text-gray-500 hover:text-primary hover:border-blue-400' : 'border-gray-700 text-gray-500 hover:text-white hover:border-gray-500'"
          >
            <div 
              class="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
              :class="isLightMode ? 'bg-gray-100 group-hover:bg-primary/10' : 'bg-gray-800 group-hover:bg-gray-700'"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <span class="text-[15px] font-medium">添加数据源</span>
          </button>
          <DataSourceCard 
            v-for="source in dataSources" 
            :key="source.id" 
            :data="source"
          />
        </div>
      </div>

      <!-- Middle: Canvas & Logs -->
      <div 
        class="flex-1 relative overflow-hidden transition-colors duration-300"
        :class="isLightMode ? 'bg-[#F3F4F6]' : 'bg-[#000]'"
      >
        <FlowCanvas 
          :nodes="flowNodes" 
          @add-node="addRandomNode"
          @delete-node="deleteNode"
        />
        <LogPanel :logs="logs" />
      </div>

      <!-- Right Sidebar: Storage -->
      <div 
        class="w-80 border-l flex flex-col z-20 transition-colors duration-300"
        :class="isLightMode ? 'bg-white border-border' : 'bg-[#0B0C10] border-gray-800'"
      >
        <div 
          class="p-4 border-b transition-colors"
          :class="isLightMode ? 'border-border' : 'border-gray-800'"
        >
          <h2 
            class="text-[14px] font-semibold uppercase tracking-wider mb-1"
            :class="isLightMode ? 'text-gray-500' : 'text-gray-400'"
          >存储终点</h2>
          <div 
            class="text-[13px]"
            :class="isLightMode ? 'text-gray-500' : 'text-gray-600'"
          >{{ storageNodes.length }} 个活跃存储</div>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          <StorageCard 
            v-for="storage in storageNodes" 
            :key="storage.id" 
            :data="storage" 
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useDashboardMock } from './composables/useDashboardMock';
import DashboardHeader from './components/DashboardHeader.vue';
import DataSourceCard from './components/DataSourceCard.vue';
import StorageCard from './components/StorageCard.vue';
import FlowCanvas from './components/FlowCanvas.vue';
import LogPanel from './components/LogPanel.vue';
import { useTheme } from '@/composables/useTheme';

const { isLightMode } = useTheme();
const { dataSources, storageNodes, flowNodes, logs, setMode } = useDashboardMock();

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'm') {
    // Toggle modes
    if (dataSources.value.length === 0) setMode('normal');
    else if (dataSources.value[0].status === 'error') setMode('empty');
    else setMode('abnormal');
  }
};

const addRandomNode = () => {
  // Logic to add a random node to mock data (simplified for demo)
  // In a real app, this would update the store
  console.log('Add node clicked');
};

const deleteNode = (id: string) => {
  console.log('Delete node clicked', id);
};

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #0B0C10;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #1F2937;
  border-radius: 2px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #374151;
}
</style>
