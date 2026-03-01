<template>
  <div class="flex-1 overflow-y-auto p-5 space-y-8 custom-scrollbar bg-slate-50/30">
      
      <!-- Today's Tasks Statistics -->
      <section>
        <div class="mb-4">
          <h4 class="text-sm font-bold text-slate-900 tracking-tight m-0">今日任务</h4>
          <p class="text-[11px] text-slate-500 mt-0.5 m-0">实时监控任务状态</p>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <StatCard
            v-for="(stat, idx) in stats" 
            :key="idx"
            v-bind="stat"
          />
        </div>
      </section>

      <!-- Input Area -->
      <section id="task-input" :class="{'opacity-100 translate-y-0': inputValue, 'opacity-0 -translate-y-4 pointer-events-none absolute': !inputValue}" class="transition-all duration-300 ease-in-out">
        <div class="border border-indigo-100 bg-gradient-to-br from-indigo-50/50 to-white shadow-sm rounded-2xl overflow-hidden">
          <div class="p-3 pb-2 border-b border-indigo-50/50 flex items-center gap-2">
            <div class="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600 text-white">
              <ThunderboltFilled class="text-xs" />
            </div>
            <span class="text-sm font-medium text-indigo-900">创建任务</span>
          </div>
          <div class="p-3 space-y-3">
            <textarea
              ref="inputRef"
              v-model="inputValue"
              rows="3"
              class="w-full resize-none border border-indigo-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white text-xs rounded-xl p-3 outline-none transition-all"
              placeholder="输入任务描述..."
            ></textarea>
            <div class="flex justify-end gap-2">
              <button
                @click="inputValue = ''"
                class="h-8 text-xs px-4 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                @click="handleCreateTask"
                class="bg-indigo-600 hover:bg-indigo-700 text-white h-8 text-xs px-4 shadow-sm rounded-lg flex items-center gap-1.5 transition-colors"
                :disabled="isCreatingTask"
              >
                <ThunderboltFilled class="text-[10px]" />
                {{ isCreatingTask ? '创建中...' : '创建任务' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Templates Section -->
      <section>
        <div class="flex items-end justify-between mb-4">
          <div>
            <h4 class="text-sm font-bold text-slate-900 tracking-tight m-0">自动化模板</h4>
            <p class="text-[11px] text-slate-500 mt-0.5 m-0">快速创建任务</p>
          </div>
          <div class="flex bg-slate-100 p-0.5 rounded-lg">
            <button
              @click="showAllTemplates = false"
              class="px-3 py-1 rounded-md text-xs font-medium transition-all"
              :class="!showAllTemplates ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
            >
              常用
            </button>
            <button
              @click="showAllTemplates = true"
              class="px-3 py-1 rounded-md text-xs font-medium transition-all"
              :class="showAllTemplates ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
            >
              全部
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <TemplateCard
            v-for="template in displayedTemplates"
            :key="template.title"
            v-bind="template"
            @fill="handleTemplateFill"
          />
        </div>
      </section>
      
      <!-- Recent Activity (Time Grouped) -->
      <section>
        <div class="flex justify-between items-center mb-4">
          <div>
            <h4 class="text-sm font-bold text-slate-900 tracking-tight m-0">最近活动</h4>
            <p class="text-[11px] text-slate-500 mt-0.5 m-0">任务执行记录</p>
          </div>
          <button 
            class="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-indigo-500 transition-colors"
            :class="{ 'animate-spin': activitiesLoading }"
            @click="$emit('refresh-activities')"
          >
            <ReloadOutlined />
          </button>
        </div>
        
        <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
          <div v-if="activitiesLoading" class="space-y-4">
             <a-skeleton active :paragraph="{ rows: 2 }" avatar />
             <a-skeleton active :paragraph="{ rows: 1 }" avatar />
          </div>
          
          <div v-else-if="!activityGroups.length" class="flex flex-col items-center justify-center py-12 text-slate-400">
             <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                <InboxOutlined class="text-2xl text-slate-300" />
             </div>
             <span class="text-xs">暂无活动记录</span>
          </div>
          
          <div v-else class="relative">
            <!-- Global Timeline Line -->
            <div class="absolute left-4 top-4 bottom-4 w-0.5 bg-slate-100"></div>

            <div v-for="(group, idx) in activityGroups" :key="group.time" class="relative mb-6 last:mb-0">
              <!-- Time Header -->
              <div 
                @click="toggleTimeGroup(group.time)"
                class="flex items-center gap-3 cursor-pointer py-1 hover:bg-slate-50 rounded-lg transition-colors relative z-10 mb-3"
              >
                <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white shadow-sm transition-transform duration-200"
                     :class="expandedTimeGroups.has(group.time) ? 'bg-indigo-500 rotate-0' : 'bg-slate-300 -rotate-90'">
                  <ClockCircleOutlined class="text-sm" />
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <h3 class="text-sm font-bold text-slate-900 m-0">{{ group.time }}</h3>
                    <span class="text-[10px] text-slate-400 font-normal">{{ group.activities.length }}个任务</span>
                  </div>
                </div>
                <div class="w-6 h-6 flex items-center justify-center rounded-full bg-slate-50 text-slate-400">
                    <DownOutlined class="text-[10px] transition-transform duration-200" :class="{ 'rotate-180': expandedTimeGroups.has(group.time) }" />
                </div>
              </div>

              <!-- Activities List -->
              <div class="space-y-3 pl-12 transition-all duration-300 origin-top overflow-hidden"
                   :style="{ maxHeight: expandedTimeGroups.has(group.time) ? '1000px' : '0', opacity: expandedTimeGroups.has(group.time) ? '1' : '0', marginBottom: expandedTimeGroups.has(group.time) ? '0' : '-10px' }">
                <div v-for="act in group.activities" :key="act.id" class="relative">
                   <div class="bg-white border border-slate-100 rounded-xl p-3 hover:shadow-md hover:border-indigo-100 transition-all duration-200 cursor-pointer group/card flex gap-3" @click="handleActivityClick(act)">
                      <!-- Icon -->
                      <div class="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-colors" :class="getActivityIconClass(act.type)">
                         <component :is="getActivityIcon(act.type)" />
                      </div>
                      
                      <!-- Content -->
                      <div class="flex-1 min-w-0">
                         <div class="flex items-center gap-2 mb-1">
                            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-md" :class="getActivityTagClass(act.type)">{{ getActivityLabel(act.type) }}</span>
                            <span class="text-[10px] text-slate-400">{{ act.duration || '0s' }}</span>
                         </div>
                         <p class="text-xs text-slate-700 font-medium leading-relaxed m-0 line-clamp-2 group-hover/card:text-indigo-600 transition-colors">
                            {{ act.message }}
                         </p>
                         <div class="flex items-center gap-2 mt-1.5" v-if="act.dataSize">
                            <div class="w-1 h-1 rounded-full bg-slate-300"></div>
                            <span class="text-[10px] text-slate-400">{{ act.dataSize }}</span>
                         </div>
                      </div>
                   </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, nextTick } from 'vue';
import StatCard from './StatCard.vue';
import TemplateCard from './TemplateCard.vue';
import { 
  ThunderboltFilled,
  ReloadOutlined,
  InboxOutlined,
  ClockCircleOutlined,
  DownOutlined,
  SearchOutlined,
  LineChartOutlined,
  CameraOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue';

const props = defineProps<{
  stats: any[];
  activities: any[];
  activitiesLoading: boolean;
  templates: any[];
}>();

const emit = defineEmits(['create-task', 'refresh-activities', 'run-task']);

const inputValue = ref('');
const inputRef = ref<HTMLTextAreaElement | null>(null);
const showAllTemplates = ref(false);
const expandedTimeGroups = ref<Set<string>>(new Set(['10分钟前', '1小时前']));
const isCreatingTask = ref(false);

const displayedTemplates = computed(() => {
  return showAllTemplates.value ? props.templates : props.templates.slice(0, 6);
});

// Group activities logic
const activityGroups = computed(() => {
  const rawActivities = props.activities;

  // Simple grouping logic
  const groups: any[] = [];
  const now = Date.now();
  
  // Helper to parse date
  const getTimestamp = (act: any) => {
      if (act.timestamp) return act.timestamp;
      if (act.last_run) return new Date(act.last_run).getTime();
      return 0;
  };

  // 10 mins ago
  const recent = rawActivities.filter(a => {
     const ts = getTimestamp(a);
     if (!ts) return false;
     const diff = now - ts;
     return diff < 1000 * 60 * 60;
  });
  if (recent.length) {
    groups.push({ time: "10分钟前", activities: recent });
  }

  // 1 hour ago
  const hourAgo = rawActivities.filter(a => {
     const ts = getTimestamp(a);
     if (!ts) return false;
     const diff = now - ts;
     return diff >= 1000 * 60 * 60 && diff < 1000 * 60 * 60 * 24;
  });
  if (hourAgo.length) {
    groups.push({ time: "1小时前", activities: hourAgo });
  }

  // Earlier
  const earlier = rawActivities.filter(a => {
     const ts = getTimestamp(a);
     if (!ts) return false;
     const diff = now - ts;
     return diff >= 1000 * 60 * 60 * 24;
  });
  if (earlier.length) {
    groups.push({ time: "更早之前", activities: earlier });
  }

  return groups;
});

const handleTemplateFill = (template: string) => {
  inputValue.value = template;
  nextTick(() => {
    const inputArea = document.getElementById("task-input");
    inputArea?.scrollIntoView({ behavior: "smooth", block: "center" });
    inputRef.value?.focus();
  });
};

const handleCreateTask = async () => {
  if (!inputValue.value.trim()) return;
  
  isCreatingTask.value = true;
  try {
      // Emit event to parent to handle API call
      emit('create-task', inputValue.value);
      inputValue.value = '';
  } catch (e) {
      console.error(e);
  } finally {
      isCreatingTask.value = false;
  }
};

const toggleTimeGroup = (time: string) => {
  if (expandedTimeGroups.value.has(time)) {
    expandedTimeGroups.value.delete(time);
  } else {
    expandedTimeGroups.value.add(time);
  }
};

const handleActivityClick = (act: any) => {
    console.log("Activity clicked", act);
};

const getActivityIcon = (type: string) => {
  const t = (type || '').toLowerCase();
  if (t.includes('抓取') || t.includes('crawl')) return SearchOutlined;
  if (t.includes('监控') || t.includes('monitor')) return LineChartOutlined;
  if (t.includes('截图') || t.includes('screenshot')) return CameraOutlined;
  if (t.includes('分析') || t.includes('analysis')) return FileTextOutlined;
  return InboxOutlined;
};

const getActivityIconClass = (type: string) => {
  const t = (type || '').toLowerCase();
  if (t.includes('抓取') || t.includes('crawl')) return 'bg-emerald-100 text-emerald-600';
  if (t.includes('监控') || t.includes('monitor')) return 'bg-purple-100 text-purple-600';
  if (t.includes('截图') || t.includes('screenshot')) return 'bg-orange-100 text-orange-600';
  return 'bg-slate-100 text-slate-500';
};

const getActivityTagClass = (type: string) => {
  const t = (type || '').toLowerCase();
  if (t.includes('抓取') || t.includes('crawl')) return 'bg-emerald-50 text-emerald-600 border border-emerald-100';
  if (t.includes('监控') || t.includes('monitor')) return 'bg-purple-50 text-purple-600 border border-purple-100';
  if (t.includes('截图') || t.includes('screenshot')) return 'bg-orange-50 text-orange-600 border border-orange-100';
  return 'bg-slate-50 text-slate-500 border border-slate-100';
};

const getActivityLabel = (type: string) => {
    const t = (type || '').toLowerCase();
    if (t.includes('crawl')) return '抓取';
    if (t.includes('monitor')) return '监控';
    if (t.includes('screenshot')) return '截图';
    if (t.includes('analysis')) return '分析';
    return type;
};
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 20px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
    background-color: #94a3b8;
}
</style>
