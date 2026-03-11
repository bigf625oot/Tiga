<template>
  <div class="flex flex-col h-full w-full overflow-hidden font-sans transition-colors duration-300 bg-background text-foreground">
    <!-- Header -->
    <DashboardHeader />

    <div class="flex flex-1 overflow-hidden relative">
      <!-- Left Sidebar: Data Sources -->
      <div 
        class="border-r flex flex-col z-20 transition-all duration-300 ease-in-out backdrop-blur-md bg-card/80 border-border relative"
        :class="[isLeftCollapsed ? 'w-0 border-r-0 opacity-0' : 'w-80 opacity-100']"
      >
        <div class="p-4 border-b border-border transition-colors space-y-3 min-w-[320px]">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-[14px] font-semibold uppercase tracking-wider mb-1 text-muted-foreground">数据源</h2>
              <div class="text-[13px] text-muted-foreground/80">{{ filteredDataSources.length }} 个活跃数据源</div>
            </div>
            <!-- Close Button (Mobile/Desktop) -->
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground" @click="isLeftCollapsed = true">
              <ChevronLeft class="h-4 w-4" />
            </Button>
          </div>
          <!-- Search Input -->
          <div class="relative">
            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              v-model="sourceSearch" 
              placeholder="搜索数据源..." 
              class="pl-9 h-9 bg-background/50 border-muted-foreground/20 focus-visible:ring-1"
            />
          </div>
        </div>
        
        <ScrollArea class="flex-1 min-w-[320px]">
          <div class="px-4 pt-4 pb-2 space-y-3">
            <template v-if="filteredDataSources.length > 0">
              <DataSourceCard 
                v-for="source in filteredDataSources" 
                :key="source.id" 
                :data="source"
                :is-selected="selectedSourceId === source.id"
                :selected-pipeline-id="selectedPipelineId"
                @select="handleSelectSource"
                @select-pipeline="handleSelectPipeline"
              />
            </template>
            <div v-else class="text-center py-8 text-muted-foreground text-sm">
              未找到相关数据源
            </div>
          </div>
        </ScrollArea>
      </div>

      <!-- Expand Left Sidebar Button (Floating) -->
      <div 
        v-if="isLeftCollapsed"
        class="absolute left-4 top-4 z-30"
      >
         <Button 
           variant="outline" 
           size="icon" 
           class="h-9 w-9 shadow-md bg-background/80 backdrop-blur border-border text-muted-foreground hover:text-foreground"
           @click="isLeftCollapsed = false"
         >
           <ChevronRight class="h-4 w-4" />
         </Button>
      </div>

      <!-- Middle: Canvas & Logs -->
      <div class="flex-1 relative overflow-hidden transition-colors duration-300 bg-background flex flex-col">
        <div class="flex-1 relative">
          <FlowCanvas 
            v-if="selectedPipelineId"
            :nodes="flowNodes" 
          />
          <div v-else class="flex flex-col items-center justify-center h-full text-muted-foreground/50">
             <div class="p-6 rounded-full bg-muted/20 mb-4">
                <Workflow class="w-12 h-12" />
             </div>
             <h3 class="text-lg font-medium text-muted-foreground">未选择流水线</h3>
             <p class="text-sm mt-1 max-w-xs text-center">请从左侧数据源列表中选择一条流水线以查看详细流程图</p>
          </div>

          <!-- Pipeline Metrics Panel -->
          <div 
            v-if="selectedPipelineId && pipelineMetrics.length > 0"
            class="absolute left-4 z-20 bg-card/90 backdrop-blur border border-border rounded-lg shadow-lg p-2.5 transition-all duration-300 flex items-center gap-4"
            :style="{ bottom: isLogExpanded ? '272px' : '52px' }"
          >
            <div class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground px-1 flex items-center gap-2 border-r border-border pr-3">
              <span>流水线指标</span>
              <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
            </div>
            <div class="flex items-center gap-4">
              <div 
                v-for="(metric, idx) in pipelineMetrics" 
                :key="idx"
                class="flex flex-col min-w-[80px]"
              >
                <div class="flex items-center gap-1.5 mb-0.5">
                  <TooltipProvider v-if="metric.description">
                    <Tooltip :delay-duration="300">
                      <TooltipTrigger as-child>
                        <div class="flex items-center gap-1 cursor-help group">
                          <span class="text-[10px] text-muted-foreground truncate font-medium group-hover:text-foreground transition-colors">
                            {{ metric.label }}
                          </span>
                          <HelpCircle class="w-3 h-3 text-muted-foreground/50 group-hover:text-primary transition-colors" />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" align="start" class="bg-popover text-popover-foreground shadow-md border border-border">
                        <p class="text-xs font-normal max-w-[200px]">{{ metric.description }}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <span v-else class="text-[10px] text-muted-foreground truncate font-medium">
                    {{ metric.label }}
                  </span>
                  <div v-if="metric.trend" class="flex items-center">
                    <svg v-if="metric.trend === 'up'" class="w-2.5 h-2.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                    <svg v-else class="w-2.5 h-2.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>
                  </div>
                </div>
                <div class="flex items-baseline gap-1">
                  <span class="text-[15px] font-bold font-din tracking-tight text-foreground leading-none">{{ metric.value }}</span>
                  <span v-if="metric.unit" class="text-[10px] text-muted-foreground/80 font-medium leading-none">{{ metric.unit }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <LogPanel :logs="logs" v-model:expanded="isLogExpanded" />
      </div>

      <!-- Expand Right Sidebar Button (Floating) -->
      <div 
        v-if="isRightCollapsed"
        class="absolute right-4 top-4 z-30"
      >
         <Button 
           variant="outline" 
           size="icon" 
           class="h-9 w-9 shadow-md bg-background/80 backdrop-blur border-border text-muted-foreground hover:text-foreground"
           @click="isRightCollapsed = false"
         >
           <ChevronLeft class="h-4 w-4" />
         </Button>
      </div>

      <!-- Right Sidebar: Storage -->
      <div 
        class="border-l flex flex-col z-20 transition-all duration-300 ease-in-out backdrop-blur-md bg-card/80 border-border relative"
        :class="[isRightCollapsed ? 'w-0 border-l-0 opacity-0' : 'w-80 opacity-100']"
      >
        <div class="p-4 border-b border-border transition-colors space-y-3 min-w-[320px]">
          <div class="flex items-center justify-between">
             <!-- Close Button -->
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground" @click="isRightCollapsed = true">
              <ChevronRight class="h-4 w-4" />
            </Button>
            <div class="text-right">
              <h2 class="text-[14px] font-semibold uppercase tracking-wider mb-1 text-muted-foreground">存储终点</h2>
              <div class="text-[13px] text-muted-foreground/80">{{ filteredStorageNodes.length }} 个活跃存储</div>
            </div>
          </div>
          <!-- Search Input -->
          <div class="relative">
            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              v-model="storageSearch" 
              placeholder="搜索存储节点..." 
              class="pl-9 h-9 bg-background/50 border-muted-foreground/20 focus-visible:ring-1"
            />
          </div>
        </div>
        <ScrollArea class="flex-1 min-w-[320px]">
          <div class="px-4 pt-4 pb-2 space-y-3">
             <template v-if="filteredStorageNodes.length > 0">
              <StorageCard 
                v-for="storage in filteredStorageNodes" 
                :key="storage.id" 
                :data="storage" 
              />
            </template>
            <div v-else class="text-center py-8 text-muted-foreground text-sm">
              未找到相关存储节点
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useDashboardMock } from './composables/useDashboardMock';
import DashboardHeader from './components/DashboardHeader.vue';
import DataSourceCard from './components/DataSourceCard.vue';
import StorageCard from './components/StorageCard.vue';
import FlowCanvas from './components/FlowCanvas.vue';
import LogPanel from './components/LogPanel.vue';
import { 
  Search, 
  ChevronLeft,
  ChevronRight,
  Workflow,
  HelpCircle
} from 'lucide-vue-next';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const { dataSources, storageNodes, flowNodes, logs, selectedPipelineId, setSelectedPipeline, pipelineMetrics } = useDashboardMock();

// Sidebar States
const isLeftCollapsed = ref(false);
const isRightCollapsed = ref(false);
const isLogExpanded = ref(true);

// Selection State
const selectedSourceId = ref<string | null>(null);
// const selectedPipelineId = ref<string | null>(null); // Removed local ref

// Search States
const sourceSearch = ref('');
const storageSearch = ref('');

// Filtered Data
const filteredDataSources = computed(() => {
  if (!sourceSearch.value) return dataSources.value;
  const query = sourceSearch.value.toLowerCase();
  return dataSources.value.filter(s => 
    s.name.toLowerCase().includes(query) || 
    s.type.toLowerCase().includes(query)
  );
});

const filteredStorageNodes = computed(() => {
  if (!storageSearch.value) return storageNodes.value;
  const query = storageSearch.value.toLowerCase();
  return storageNodes.value.filter(s => 
    s.name.toLowerCase().includes(query) || 
    s.type.toLowerCase().includes(query)
  );
});

const handleSelectSource = (id: string) => {
  selectedSourceId.value = id;
};

const handleSelectPipeline = (id: string) => {
  setSelectedPipeline(id);
};
</script>

<style scoped>
/* Ensure content doesn't wrap awkwardly during transition */
.min-w-\[320px\] {
  min-width: 320px;
}
</style>
