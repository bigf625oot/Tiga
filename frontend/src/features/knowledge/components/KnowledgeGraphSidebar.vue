<template>
  <div class="h-full flex flex-col w-full flex-shrink-0 transition-colors duration-300 bg-background border-r border-border overflow-hidden">
    <div class="p-4 border-b border-zinc-200/50 dark:border-zinc-700/50 flex items-start justify-between gap-2">
      <div v-if="!collapsed" class="min-w-0 flex-1">
        <h3 class="font-medium text-zinc-800 dark:text-zinc-100 mb-3 flex items-center gap-2">
          <span class="w-1 h-4 bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]"></span>
          节点搜索
        </h3>

        <div v-if="!loading" class="relative">
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
        <div v-else class="space-y-2">
          <Skeleton class="h-9 w-full" />
          <Skeleton class="h-3 w-1/2" />
        </div>
      </div>


    </div>

    <ScrollArea v-if="!collapsed" class="flex-1">
      <div v-if="loading" class="p-4 space-y-4">
        <Skeleton class="h-20 w-full" />
        <Skeleton class="h-4 w-24" />
        <div class="space-y-2">
          <Skeleton class="h-8 w-full" />
          <Skeleton class="h-8 w-full" />
          <Skeleton class="h-8 w-full" />
        </div>
        <Skeleton class="h-4 w-24" />
        <Skeleton class="h-12 w-full" />
      </div>
      <div v-else class="p-4 space-y-6">
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
          <div class="grid grid-cols-2 gap-2 w-full">
              <div 
                  v-for="type in filteredEntityTypes" 
                  :key="type"
                  class="flex items-center justify-between group hover:bg-zinc-50 dark:hover:bg-zinc-800 p-2 rounded border border-zinc-100 dark:border-zinc-700/50 transition-colors cursor-pointer"
                  @click="handleTypeCheck(type, !localSelectedTypes.includes(type))"
              >
                  <div class="flex items-center gap-2 min-w-0">
                    <div 
                        class="w-2 h-2 rounded-full flex-shrink-0 ring-1 ring-white/20"
                        :style="{ backgroundColor: colorMap[type] || '#ccc' }"
                    ></div>
                    <span class="text-xs text-zinc-700 dark:text-zinc-200 font-medium truncate" :title="type">{{ type }}</span>
                  </div>
                  
                  <div class="flex items-center gap-1.5 pl-1">
                      <span class="text-[10px] text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded-full border border-transparent dark:border-zinc-700">{{ typeCounts[type] || 0 }}</span>
                      <div 
                        class="w-3 h-3 rounded-full border flex items-center justify-center transition-colors"
                        :class="localSelectedTypes.includes(type) ? 'bg-blue-500 border-blue-500' : 'border-zinc-300 dark:border-zinc-600'"
                      >
                          <svg v-if="localSelectedTypes.includes(type)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" class="w-2 h-2 text-white"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      </div>
                  </div>
              </div>
          </div>
        </div>

        <!-- Timeline -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">时序查询</h4>
            <button 
               v-if="isTimeModified"
               @click="resetTime"
               class="text-[10px] text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer transition-colors"
            >
               重置
            </button>
          </div>
          
          <div class="bg-zinc-50 dark:bg-zinc-800/50 rounded-lg p-3 border border-zinc-100 dark:border-zinc-700">
              <div class="flex items-center gap-2 mb-2">
                  <Clock class="w-3.5 h-3.5 text-zinc-400" />
                  <span class="text-xs text-zinc-600 dark:text-zinc-300 font-medium">
                      {{ formatDate(localTimeRange[0]) }} - {{ formatDate(localTimeRange[1]) }}
                  </span>
              </div>
              
              <p class="text-[10px] text-zinc-400 dark:text-zinc-500 mb-3 leading-relaxed">
                  筛选在此时间窗口内发生或创建的实体（基于文档创建时间或事件发生时间）。
              </p>

              <div class="px-1">
                <Slider
                    v-model="localTimeRange"
                    :min="timeBounds.min"
                    :max="timeBounds.max"
                    :step="1000 * 60 * 60 * 24"
                    :disabled="timeBounds.min === timeBounds.max"
                    @update:modelValue="onTimeChange"
                    class="my-4"
                />
              </div>
              
               <div class="flex gap-1.5 flex-wrap mt-2">
                   <button 
                     v-for="opt in timePresets" 
                     :key="opt.label"
                     @click="applyTimePreset(opt.days)"
                     class="px-2 py-1 text-[10px] rounded border transition-colors"
                     :class="isPresetActive(opt.days) ? 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800' : 'bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700'"
                   >
                     {{ opt.label }}
                   </button>
               </div>

               <div class="flex items-center gap-3 mt-4 pt-3 border-t border-zinc-200 dark:border-zinc-700/50">
                    <button 
                        class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors flex-shrink-0"
                        @click="togglePlay"
                        title="播放/暂停时序演化"
                    >
                        <Pause v-if="isPlaying" class="w-3.5 h-3.5 fill-current" />
                        <Play v-else class="w-3.5 h-3.5 fill-current ml-0.5" />
                    </button>
                    <div class="flex-1 min-w-0">
                        <div class="text-xs font-medium text-zinc-700 dark:text-zinc-300">时序演化播放</div>
                        <div class="text-[10px] text-zinc-400 truncate">自动演示知识随时间的动态变化</div>
                    </div>
               </div>
          </div>
        </div>
        
        <!-- Current Events -->
        <div v-if="currentEvents && currentEvents.length > 0">
            <h4 class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-2">当前窗口事件 ({{ currentEvents.length }})</h4>
            <div class="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
                <div 
                    v-for="event in (currentEvents || []).slice(0, 20)" 
                    :key="event.id"
                    class="bg-white dark:bg-zinc-800 p-2 rounded border border-zinc-100 dark:border-zinc-700 text-xs flex flex-col gap-1"
                >
                    <div class="font-medium text-zinc-700 dark:text-zinc-200 truncate" :title="event.name">{{ event.name }}</div>
                    <div class="text-[10px] text-zinc-400 flex items-center gap-1">
                        <Clock class="w-3 h-3" />
                        {{ formatDate(event.time) }}
                    </div>
                </div>
                <div v-if="(currentEvents || []).length > 20" class="text-center text-[10px] text-zinc-400 italic py-1">
                    还有 {{ (currentEvents || []).length - 20 }} 个事件...
                </div>
            </div>
        </div>
      </div>
    </ScrollArea>


  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, X, Clock, Play, Pause } from 'lucide-vue-next';

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
  collapsed?: boolean;
  loading?: boolean;
  currentEvents?: any[];
}>();

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void;
  (e: 'update:selectedTypes', val: string[]): void;
  (e: 'update:timeRange', val: [number, number]): void;
  (e: 'update:collapsed', val: boolean): void;
}>();

const collapsed = computed(() => !!props.collapsed);
const loading = computed(() => !!props.loading);



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

const filteredEntityTypes = computed(() => {
  if (!props.searchQuery) return props.allTypes;
  return props.allTypes.filter(t => (props.typeCounts[t] || 0) > 0);
});

const selectAllTypes = () => {
  localSelectedTypes.value = [...filteredEntityTypes.value];
  onTypeChange();
};

const invertTypes = () => {
  const current = new Set(localSelectedTypes.value);
  localSelectedTypes.value = filteredEntityTypes.value.filter(t => !current.has(t));
  onTypeChange();
};

const formatDate = (ts: number) => {
    if (!ts) return '';
    const date = new Date(ts);
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

const isTimeModified = computed(() => {
    return localTimeRange.value[0] !== props.timeBounds.min || localTimeRange.value[1] !== props.timeBounds.max;
});

const timePresets = [
    { label: '近7天', days: 7 },
    { label: '近30天', days: 30 },
    { label: '近3个月', days: 90 },
    { label: '近1年', days: 365 },
];

const applyTimePreset = (days: number) => {
    const end = props.timeBounds.max;
    const start = Math.max(props.timeBounds.min, end - days * 24 * 60 * 60 * 1000);
    localTimeRange.value = [start, end];
    onTimeChange([start, end]);
};

const resetTime = () => {
    localTimeRange.value = [props.timeBounds.min, props.timeBounds.max];
    onTimeChange(localTimeRange.value);
};

const isPresetActive = (days: number) => {
    const end = props.timeBounds.max;
    const start = Math.max(props.timeBounds.min, end - days * 24 * 60 * 60 * 1000);
    return Math.abs(localTimeRange.value[1] - end) < 1000 && Math.abs(localTimeRange.value[0] - start) < 1000;
};

const isPlaying = ref(false);
let animationFrameId: number | null = null;
let lastFrameTime = 0;
const PLAY_DURATION_MS = 10000; // Total cycle time: 10 seconds

const togglePlay = () => {
    isPlaying.value = !isPlaying.value;
    if (isPlaying.value) {
        // Reset to start if at the end or invalid range
        if (localTimeRange.value[1] >= props.timeBounds.max - 1000) {
             const start = props.timeBounds.min;
             // Start with a small window (5% of total range)
             const windowSize = (props.timeBounds.max - props.timeBounds.min) * 0.05;
             localTimeRange.value = [start, start + windowSize];
             onTimeChange(localTimeRange.value);
        }
        lastFrameTime = performance.now();
        animationFrameId = requestAnimationFrame(animate);
    } else {
        if (animationFrameId !== null) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
    }
};

const animate = (timestamp: number) => {
    if (!isPlaying.value) return;

    const elapsed = timestamp - lastFrameTime;
    
    // Limit update rate to ~30fps to avoid overwhelming the graph renderer
    if (elapsed > 32) {
        const range = props.timeBounds.max - props.timeBounds.min;
        // Step size based on total duration (e.g. traverse full range in 10s)
        const step = (range / PLAY_DURATION_MS) * elapsed;
        
        let [start, end] = localTimeRange.value;
        const currentWindow = end - start;
        
        // Strategy: Sliding Window
        // Move both start and end forward
        let newStart = start + step;
        let newEnd = end + step;
        
        // Boundary check
        if (newEnd >= props.timeBounds.max) {
            newEnd = props.timeBounds.max;
            newStart = newEnd - currentWindow; // Keep window size at end
            
            localTimeRange.value = [newStart, newEnd];
            onTimeChange(localTimeRange.value);
            isPlaying.value = false;
            animationFrameId = null;
            return;
        }
        
        localTimeRange.value = [newStart, newEnd];
        onTimeChange(localTimeRange.value);
        lastFrameTime = timestamp;
    }
    
    animationFrameId = requestAnimationFrame(animate);
};

// Stop playing if component unmounts or inputs change drastically
watch(() => props.timeBounds, () => {
    if (isPlaying.value) togglePlay();
});
</script>
