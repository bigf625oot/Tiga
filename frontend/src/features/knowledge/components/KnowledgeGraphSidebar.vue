<template>
  <div class="h-full flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 w-80 flex-shrink-0 transition-colors duration-300">
    <!-- Header -->
    <div class="p-4 border-b border-slate-100 dark:border-slate-800">
      <h3 class="font-medium text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
        <span class="w-1 h-4 bg-blue-500 rounded-full"></span>
        图谱控制台
      </h3>
      
      <!-- Search -->
      <div class="relative">
        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          :model-value="localSearch"
          @update:model-value="(val) => { localSearch = val as string; onSearchChange(); }"
          placeholder="搜索节点名称/属性..."
          class="pl-9 pr-8"
          @keydown.enter="onSearch"
        />
        <button
          v-if="localSearch"
          @click="localSearch = ''; onSearchChange()"
          class="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground focus:outline-none"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700">
      <!-- Stats Card -->
      <div class="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-3 border border-slate-100 dark:border-slate-700">
        <h4 class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">视图统计</h4>
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-white dark:bg-slate-800 p-2 rounded border border-slate-100 dark:border-slate-700 text-center">
            <div class="text-xs text-slate-400 dark:text-slate-500">节点</div>
            <div class="text-lg font-bold text-slate-700 dark:text-slate-200">
              <span :class="{'text-blue-600 dark:text-blue-400': stats.visibleNodes !== stats.totalNodes}">{{ stats.visibleNodes }}</span>
              <span class="text-slate-300 dark:text-slate-600 text-xs font-normal"> / {{ stats.totalNodes }}</span>
            </div>
          </div>
          <div class="bg-white dark:bg-slate-800 p-2 rounded border border-slate-100 dark:border-slate-700 text-center">
            <div class="text-xs text-slate-400 dark:text-slate-500">关系</div>
            <div class="text-lg font-bold text-slate-700 dark:text-slate-200">
              <span :class="{'text-blue-600 dark:text-blue-400': stats.visibleEdges !== stats.totalEdges}">{{ stats.visibleEdges }}</span>
              <span class="text-slate-300 dark:text-slate-600 text-xs font-normal"> / {{ stats.totalEdges }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Type Filter -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <h4 class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">实体类型</h4>
          <div class="flex gap-2">
             <button 
                @click="selectAllTypes"
                class="text-[10px] text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer transition-colors"
             >
                全选
             </button>
             <button 
                @click="invertTypes"
                class="text-[10px] text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer transition-colors"
             >
                反选
             </button>
          </div>
        </div>
        <a-checkbox-group v-model:value="localSelectedTypes" class="flex flex-col gap-2 w-full" @change="onTypeChange">
            <div 
                v-for="type in allTypes" 
                :key="type"
                class="flex items-center justify-between w-full group hover:bg-slate-50 dark:hover:bg-slate-800 p-1 rounded transition-colors"
            >
                <a-checkbox :value="type" class="text-sm text-slate-700 dark:text-slate-300 !mr-0 flex-1 flex items-center gap-2 custom-checkbox">
                    <span 
                        class="w-2.5 h-2.5 rounded-full inline-block ring-1 ring-white/20"
                        :style="{ backgroundColor: colorMap[type] || '#ccc' }"
                    ></span>
                    {{ type }}
                </a-checkbox>
                <span class="text-xs text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded-full border border-transparent dark:border-slate-700">{{ typeCounts[type] || 0 }}</span>
            </div>
        </a-checkbox-group>
      </div>

      <!-- Timeline -->
      <div>
        <h4 class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">时序查询</h4>
        <div class="px-2">
            <a-slider
                v-model:value="localTimeRange"
                range
                :min="timeBounds.min"
                :max="timeBounds.max"
                :disabled="timeBounds.min === timeBounds.max"
                :tip-formatter="formatDate"
                @change="onTimeChange"
                class="custom-slider"
            />
            <div class="flex justify-between text-[10px] text-slate-400 dark:text-slate-500 mt-1 font-mono">
                <span>{{ formatDate(timeBounds.min) }}</span>
                <span>{{ formatDate(timeBounds.max) }}</span>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Checkbox, Slider } from 'ant-design-vue';
import { Input } from '@/components/ui/input';
import { Search, X } from 'lucide-vue-next';

const props = defineProps<{
  searchQuery: string;
  selectedTypes: string[];
  allTypes: string[];
  colorMap: Record<string, string>;
  typeCounts: Record<string, number>;
  stats: {
    totalNodes: number;
    totalEdges: number;
    visibleNodes: number;
    visibleEdges: number;
  };
  timeRange: [number, number];
  timeBounds: { min: number; max: number };
}>();

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void;
  (e: 'update:selectedTypes', val: string[]): void;
  (e: 'update:timeRange', val: [number, number]): void;
}>();

// Local state for immediate feedback handling if needed, currently direct mapping
const localSearch = ref(props.searchQuery);
const localSelectedTypes = ref(props.selectedTypes);
const localTimeRange = ref<[number, number]>([...props.timeRange]);

// Sync with props
watch(() => props.searchQuery, val => localSearch.value = val);
watch(() => props.selectedTypes, val => localSelectedTypes.value = val);
watch(() => props.timeRange, val => localTimeRange.value = [...val]);

// Event handlers
const onSearchChange = () => {
  emit('update:searchQuery', localSearch.value);
};
const onSearch = () => {
    // Search is handled via update:searchQuery
    emit('update:searchQuery', localSearch.value);
};

const onTypeChange = () => {
  emit('update:selectedTypes', localSelectedTypes.value);
};

const onTimeChange = () => {
  emit('update:timeRange', localTimeRange.value);
};

const selectAllTypes = () => {
  localSelectedTypes.value = [...props.allTypes];
  onTypeChange();
};

const invertTypes = () => {
  const current = new Set(localSelectedTypes.value);
  localSelectedTypes.value = props.allTypes.filter(t => !current.has(t));
  onTypeChange();
};

const formatDate = (ts: number) => {
    if (!ts) return '';
    const date = new Date(ts);
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};
</script>

<style scoped>
:deep(.ant-slider-track) {
    background-color: #3b82f6;
}
:deep(.ant-slider-handle) {
    border-color: #3b82f6;
}
</style>
