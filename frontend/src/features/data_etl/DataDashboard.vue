<template>
  <div 
    class="flex flex-col h-full w-full overflow-hidden font-sans transition-colors duration-300"
    :class="isLightMode ? 'bg-slate-50 text-slate-900' : 'bg-[#0B0C10] text-white'"
  >
    <DashboardHeader />

    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar: Data Sources -->
      <div 
        class="w-80 border-r flex flex-col z-20 transition-colors duration-300 backdrop-blur-md"
        :class="isLightMode ? 'bg-white/80 border-slate-200' : 'bg-[#0B0C10] border-gray-800'"
      >
        <div 
          class="p-6 border-b transition-colors"
          :class="isLightMode ? 'border-slate-200' : 'border-gray-800'"
        >
          <h2 
            class="text-[14px] font-semibold uppercase tracking-wider mb-1"
            :class="isLightMode ? 'text-slate-500' : 'text-gray-400'"
          >数据源</h2>
          <div 
            class="text-[13px]"
            :class="isLightMode ? 'text-slate-500' : 'text-gray-600'"
          >{{ dataSources.length }} 个活跃数据源</div>
        </div>
        <div class="flex-1 overflow-y-auto px-6 pt-6 pb-2 space-y-4 custom-scrollbar">
          <DataSourceCard 
            v-for="source in dataSources" 
            :key="source.id" 
            :data="source"
            :is-selected="selectedSourceId === source.id"
            @select="handleSelectSource"
          />
        </div>
      </div>

      <!-- Middle: Canvas & Logs -->
      <div 
        class="flex-1 relative overflow-hidden transition-colors duration-300"
        :class="isLightMode ? 'bg-slate-50' : 'bg-[#000]'"
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
        class="w-80 border-l flex flex-col z-20 transition-colors duration-300 backdrop-blur-md"
        :class="isLightMode ? 'bg-white/80 border-slate-200' : 'bg-[#0B0C10] border-gray-800'"
      >
        <div 
          class="p-6 border-b transition-colors"
          :class="isLightMode ? 'border-slate-200' : 'border-gray-800'"
        >
          <h2 
            class="text-[14px] font-semibold uppercase tracking-wider mb-1"
            :class="isLightMode ? 'text-slate-500' : 'text-gray-400'"
          >存储终点</h2>
          <div 
            class="text-[13px]"
            :class="isLightMode ? 'text-slate-500' : 'text-gray-600'"
          >{{ storageNodes.length }} 个活跃存储</div>
        </div>
        <div class="flex-1 overflow-y-auto px-6 pt-6 pb-2 space-y-4 custom-scrollbar">
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
import { onMounted, onUnmounted, ref } from 'vue';
import { useDashboardMock } from './composables/useDashboardMock';
import DashboardHeader from './components/DashboardHeader.vue';
import DataSourceCard from './components/DataSourceCard.vue';
import StorageCard from './components/StorageCard.vue';
import FlowCanvas from './components/FlowCanvas.vue';
import LogPanel from './components/LogPanel.vue';
import { useTheme } from '@/composables/useTheme';

const { isLightMode } = useTheme();
const { dataSources, storageNodes, flowNodes, logs, setMode } = useDashboardMock();

const selectedSourceId = ref<string | null>(null);

const handleSelectSource = (id: string) => {
  selectedSourceId.value = id;
};

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
