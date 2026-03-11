<template>
  <div 
    class="rounded-xl border p-5 relative overflow-hidden group transition-all duration-300 flex flex-col gap-5 bg-card text-card-foreground border-border hover:border-primary/50 hover:-translate-y-[2px] hover:shadow-lg"
    :class="[
      isSelected 
        ? 'ring-2 ring-primary shadow-[inset_0_0_0_1px_rgba(59,130,246,0.1)]' 
        : ''
    ]"
  >
    <!-- Selected Indicator Strip -->
    <div 
      v-if="isSelected"
      class="absolute left-0 top-0 bottom-0 w-1 bg-primary"
    ></div>
    <!-- Header Section -->
    <div class="flex justify-between items-start cursor-pointer" @click="$emit('select', data.id)">
      <div class="flex items-center gap-4">
        <div 
          class="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20"
          :class="getIconBgColor(data.type)"
        >
          <component :is="getIconComponent(data.type)" class="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 class="font-bold text-[16px] tracking-tight text-foreground">{{ data.name }}</h3>
          <div class="flex items-center gap-2 mt-1.5">
            <div class="relative flex h-2 w-2">
              <span v-if="data.status === 'healthy'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" :class="statusColor"></span>
            </div>
            <span class="text-[12px] font-medium uppercase tracking-wide opacity-80" :class="statusTextColor">{{ statusText }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bento Grid Layout -->
    <div class="grid grid-cols-2 gap-3" @click="$emit('select', data.id)">
      <!-- Throughput Box -->
      <div class="rounded-xl p-3 flex flex-col justify-between h-20 bg-muted/50">
        <span class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">实时吞吐</span>
        <div class="flex items-end justify-between">
            <span class="text-[18px] font-inter font-bold tracking-tight text-foreground">{{ data.throughput }}</span>
        </div>
      </div>

      <!-- Active Pipeline Box -->
      <div class="rounded-xl p-3 flex flex-col justify-between h-20 bg-muted/50">
        <span class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">活跃流水线</span>
        <div class="flex items-end gap-1">
            <span class="text-[20px] font-inter font-bold tracking-tight text-foreground">{{ data.active_pipelines }}</span>
            <span class="text-[11px] font-medium text-muted-foreground mb-1.5">个</span>
        </div>
      </div>
    </div>

    <!-- Pipelines List (Expandable or List) -->
    <div v-if="data.pipelines && data.pipelines.length > 0" class="space-y-2">
      <div class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground px-1">关联流水线</div>
      <div 
        v-for="pipeline in data.pipelines"
        :key="pipeline.id"
        class="rounded-lg p-2.5 flex items-center justify-between group/item cursor-pointer transition-all border border-transparent hover:border-primary/20"
        :class="[
          selectedPipelineId === pipeline.id 
            ? 'bg-blue-500/10 border-blue-500/30' 
            : 'bg-muted/30 hover:bg-muted/50'
        ]"
        @click.stop="$emit('select-pipeline', pipeline.id)"
      >
        <div class="flex items-center gap-3">
          <div 
            class="w-1.5 h-1.5 rounded-full"
            :class="pipeline.status === 'active' ? 'bg-green-500' : 'bg-slate-400'"
          ></div>
          <div class="flex flex-col">
            <span class="text-[13px] font-medium text-foreground">{{ pipeline.name }}</span>
            <span 
              v-if="pipeline.status === 'active' && selectedPipelineId === pipeline.id" 
              class="text-[10px] text-blue-500 font-medium"
            >
              正在展示
            </span>
          </div>
        </div>
        <div class="text-[12px] font-mono text-muted-foreground group-hover/item:text-foreground">
          {{ pipeline.processed.toLocaleString() }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { DataSource } from '../composables/useDashboardMock';

import { 
  Database, 
  Globe, 
  File, 
  Server 
} from 'lucide-vue-next';

const props = defineProps<{
  data: DataSource;
  isSelected?: boolean;
  selectedPipelineId?: string | null;
}>();

defineEmits(['select', 'select-pipeline']);

const getIconComponent = (type: string) => {
  switch(type) {
    case 'crawler': return Globe;
    case 'sftp': return File;
    case 'database': return Database;
    case 'api': return Server;
    default: return Globe;
  }
};

const getIconBgColor = (type: string) => {
  switch(type) {
    case 'crawler': return 'bg-green-500';
    case 'sftp': return 'bg-blue-500';
    case 'database': return 'bg-purple-500';
    case 'api': return 'bg-amber-500';
    default: return 'bg-gray-500';
  }
};

const statusColor = computed(() => {
  switch (props.data.status) {
    case 'healthy': return 'bg-green-500';
    case 'warning': return 'bg-yellow-500';
    case 'error': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
});

const statusTextColor = computed(() => {
  switch (props.data.status) {
    case 'healthy': return 'text-green-600 dark:text-green-500';
    case 'warning': return 'text-yellow-600 dark:text-yellow-500';
    case 'error': return 'text-red-600 dark:text-red-500';
    default: return 'text-muted-foreground';
  }
});

const statusText = computed(() => {
  switch (props.data.status) {
    case 'healthy': return '健康';
    case 'warning': return '警告';
    case 'error': return '异常';
    default: return '未知';
  }
});
</script>

<style scoped>
</style>
