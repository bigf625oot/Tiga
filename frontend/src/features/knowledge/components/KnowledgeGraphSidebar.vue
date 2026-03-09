<template>
  <div class="h-full flex flex-col bg-white dark:bg-zinc-900/80 dark:backdrop-blur-xl border-r border-zinc-200 dark:border-none dark:shadow-[1px_0_0_0_rgba(255,255,255,0.05)] w-80 flex-shrink-0 transition-colors duration-300">
    <!-- Header -->
    <div class="p-4 border-b border-zinc-100 dark:border-none dark:shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
      <h3 class="font-medium text-zinc-800 dark:text-zinc-100 mb-3 flex items-center gap-2">
        <span class="w-1 h-4 bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]"></span>
        图谱控制台
      </h3>
      
      <!-- Search -->
      <div class="relative">
        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          :model-value="localSearch"
          @update:model-value="(val) => { localSearch = String(val); onSearchChange(); }"
          placeholder="搜索节点名称/属性..."
          class="pl-9 pr-8 h-9 text-xs"
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

    <ScrollArea class="flex-1">
      <div class="p-4 space-y-6">
        <!-- Stats Card -->
        <div class="bg-zinc-50 dark:bg-zinc-800/50 rounded-lg p-3 border border-zinc-100 dark:border-zinc-700">
          <h4 class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-2">视图统计</h4>
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-white dark:bg-zinc-800 p-2 rounded border border-zinc-100 dark:border-zinc-700 text-center">
              <div class="text-xs text-zinc-400 dark:text-zinc-500">节点</div>
              <div class="text-lg font-bold text-zinc-700 dark:text-zinc-200">
                <span :class="{'text-blue-600 dark:text-blue-400': stats.visibleNodes !== stats.totalNodes}">{{ stats.visibleNodes }}</span>
                <span class="text-zinc-300 dark:text-zinc-600 text-xs font-normal"> / {{ stats.totalNodes }}</span>
              </div>
            </div>
            <div class="bg-white dark:bg-zinc-800 p-2 rounded border border-zinc-100 dark:border-zinc-700 text-center">
              <div class="text-xs text-zinc-400 dark:text-zinc-500">关系</div>
              <div class="text-lg font-bold text-zinc-700 dark:text-zinc-200">
                <span :class="{'text-blue-600 dark:text-blue-400': stats.visibleEdges !== stats.totalEdges}">{{ stats.visibleEdges }}</span>
                <span class="text-zinc-300 dark:text-zinc-600 text-xs font-normal"> / {{ stats.totalEdges }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Type Filter -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">实体类型</h4>
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
          <div class="flex flex-col gap-2 w-full">
              <div 
                  v-for="type in allTypes" 
                  :key="type"
                  class="flex items-center justify-between w-full group hover:bg-zinc-50 dark:hover:bg-zinc-800 p-1 rounded transition-colors"
              >
                  <div class="flex items-center space-x-2">
                    <Checkbox 
                        :id="`type-${type}`" 
                        :checked="localSelectedTypes.includes(type)"
                        @update:checked="(checked) => handleTypeCheck(type, checked)"
                    />
                    <label 
                        :for="`type-${type}`" 
                        class="text-sm text-zinc-700 dark:text-zinc-300 font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center gap-2 cursor-pointer"
                    >
                        <span 
                            class="w-2.5 h-2.5 rounded-full inline-block ring-1 ring-white/20"
                            :style="{ backgroundColor: colorMap[type] || '#ccc' }"
                        ></span>
                        {{ type }}
                    </label>
                  </div>
                  <span class="text-xs text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded-full border border-transparent dark:border-zinc-700">{{ typeCounts[type] || 0 }}</span>
              </div>
          </div>
        </div>

        <!-- Timeline -->
        <div>
          <h4 class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-4">时序查询</h4>
          <div class="px-2">
              <Slider
                  v-model="localTimeRange"
                  :min="timeBounds.min"
                  :max="timeBounds.max"
                  :step="1000 * 60 * 60 * 24"
                  :disabled="timeBounds.min === timeBounds.max"
                  @update:modelValue="onTimeChange"
                  class="my-4"
              />
              <div class="flex justify-between text-[10px] text-zinc-400 dark:text-zinc-500 mt-1 font-mono">
                  <span>{{ formatDate(timeBounds.min) }}</span>
                  <span>{{ formatDate(timeBounds.max) }}</span>
              </div>
          </div>
        </div>
      </div>
    </ScrollArea>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
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
const localTimeRange = ref<number[]>([...props.timeRange]);

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

const handleTypeCheck = (type: string, checked: boolean) => {
    if (checked) {
        if (!localSelectedTypes.value.includes(type)) {
            localSelectedTypes.value = [...localSelectedTypes.value, type];
        }
    } else {
        localSelectedTypes.value = localSelectedTypes.value.filter(t => t !== type);
    }
    onTypeChange();
};

const onTypeChange = () => {
  emit('update:selectedTypes', localSelectedTypes.value);
};

const onTimeChange = (val: number[] | undefined) => {
    if (!val || val.length < 2) return;
    // Ensure we emit a tuple [number, number]
    if (val.length >= 2) {
        // @ts-ignore
        emit('update:timeRange', [val[0], val[1]]);
    }
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
