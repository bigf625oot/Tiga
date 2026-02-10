<template>
  <div class="task-tree font-sans h-full">
    <div v-if="tasks.length === 0" class="flex flex-col items-center justify-center h-full text-slate-500 text-sm gap-3">
      <img src="/bot.svg" alt="Waiting" class="w-16 h-16 opacity-50 grayscale" />
      <span>等待任务规划...</span>
    </div>
    <div v-else class="space-y-2">
      <div v-for="task in tasks" :key="task.id" class="task-item">
        <!-- Task Header -->
        <div class="flex items-center gap-3 p-3 bg-white border border-slate-100 rounded-lg shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
           <!-- Status Indicator -->
           <div class="absolute left-0 top-0 bottom-0 w-1" :class="statusColor(task.status)"></div>
           
           <!-- Icon -->
           <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0" :class="statusBg(task.status)">
              <component :is="statusIcon(task.status)" class="w-4 h-4 text-white" />
           </div>
           
           <!-- Content -->
           <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                 <span class="font-medium text-slate-700 truncate" :title="task.name">{{ task.name }}</span>
                 <span class="text-xs px-2 py-0.5 rounded-full" :class="priorityClass(task.priority)">
                    {{ task.priority || 'Normal' }}
                 </span>
              </div>

              <!-- Description -->
              <div v-if="task.description" class="text-xs text-slate-500 mb-2 line-clamp-2" :title="task.description">
                  {{ task.description }}
              </div>

              <div class="flex items-center gap-3 text-[10px] text-slate-400">
                 <!-- Time -->
                 <div class="flex items-center gap-1">
                     <ClockCircleOutlined />
                     <span v-if="task.status === 'pending' && task.estimatedTime">预计 {{ task.estimatedTime }}s</span>
                     <span v-else-if="task.startTime">{{ formatTime(task.startTime) }} <span v-if="task.endTime">- {{ formatTime(task.endTime) }} ({{ ((task.endTime - task.startTime) / 1000).toFixed(1) }}s)</span></span>
                     <span v-else>--:--</span>
                 </div>
                 
                 <!-- Deps -->
                 <div v-if="task.dependencies?.length" class="flex items-center gap-1">
                     <LinkOutlined />
                     <span>依赖: {{ task.dependencies.join(', ') }}</span>
                 </div>
              </div>

              <!-- Progress Bar if running -->
              <div v-if="task.status === 'running'" class="mt-2 h-1 bg-slate-100 rounded-full overflow-hidden">
                 <div class="h-full bg-blue-500 animate-pulse" style="width: 60%"></div>
              </div>
           </div>
        </div>
        
        <!-- Children (Recursive) -->
        <div v-if="task.children && task.children.length" class="pl-6 mt-2 border-l-2 border-slate-100 ml-4">
            <TaskTree :tasks="task.children" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  CheckCircleOutlined, 
  SyncOutlined, 
  ClockCircleOutlined, 
  CloseCircleOutlined,
  LinkOutlined
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';

defineOptions({
  name: 'TaskTree'
});

defineProps({
  tasks: {
    type: Array,
    default: () => []
  }
});

const statusColor = (status) => {
    switch(status) {
        case 'completed': return 'bg-green-500';
        case 'running': return 'bg-blue-500';
        case 'failed': return 'bg-red-500';
        default: return 'bg-slate-300';
    }
};

const statusBg = (status) => {
    switch(status) {
        case 'completed': return 'bg-green-500';
        case 'running': return 'bg-blue-500';
        case 'failed': return 'bg-red-500';
        default: return 'bg-slate-200';
    }
};

const statusIcon = (status) => {
    switch(status) {
        case 'completed': return CheckCircleOutlined;
        case 'running': return SyncOutlined;
        case 'failed': return CloseCircleOutlined;
        default: return ClockCircleOutlined;
    }
};

const priorityClass = (p) => {
    switch(p) {
        case 'high': return 'bg-red-100 text-red-600';
        case 'medium': return 'bg-amber-100 text-amber-600';
        case 'low': return 'bg-blue-100 text-blue-600';
        default: return 'bg-slate-100 text-slate-500';
    }
};

const formatTime = (ts) => {
    if (!ts) return '--:--';
    return dayjs(ts).format('HH:mm:ss');
};
</script>
