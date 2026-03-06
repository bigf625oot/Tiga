<template>
  <div 
    class="group bg-white border border-slate-200 rounded-2xl hover:shadow-xl hover:border-blue-200 transition-all duration-300 flex flex-col h-[200px] relative overflow-hidden cursor-pointer"
    @click="$emit('click', agent)"
  >
    <div class="p-5 flex flex-col h-full">
      <!-- Header: Icon + Title + Menu -->
      <div class="flex gap-4 mb-3">
        <!-- Icon -->
        <div 
          class="relative flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center overflow-hidden transition-transform duration-300 group-hover:scale-105"
          :class="isTemplate ? 'bg-transparent border border-slate-100' : 'bg-white shadow-sm border border-slate-100'"
        >
          <img v-if="isImage" :src="agent.icon" class="w-full h-full object-cover" />
          <component v-else :is="agent.iconComponent" class="w-6 h-6 text-slate-700" />
        </div>
        
        <!-- Title & Tags Area -->
        <div class="flex-1 min-w-0 flex flex-col py-0.5">
          <div class="flex justify-between items-start">
            <h3 class="font-bold text-slate-800 text-base leading-tight truncate pr-6 group-hover:text-blue-600 transition-colors" :title="agent.name">
              {{ agent.name }}
            </h3>
            
            <!-- Menu Trigger (Only for non-template agents) -->
            <div v-if="!isTemplate" class="absolute top-5 right-4" @click.stop>
              <div class="relative">
                <button 
                  @click="toggleMenu"
                  class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                  :class="{'opacity-100 bg-slate-100 text-slate-600': showMenu}"
                >
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
                
                <!-- Dropdown Menu -->
                <div 
                  v-if="showMenu"
                  class="absolute right-0 top-full mt-1 w-32 bg-white border border-slate-100 rounded-xl shadow-xl z-20 py-1.5 animate-in fade-in zoom-in duration-100 origin-top-right"
                >
                  <button 
                    @click="handleAction('edit')"
                    class="w-full text-left px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-blue-600 transition-colors flex items-center gap-2"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    编辑配置
                  </button>
                  <button 
                    @click="handleAction('delete')"
                    class="w-full text-left px-4 py-2 text-xs font-medium text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors flex items-center gap-2"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    删除智能体
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-1 flex items-center gap-2">
             <span v-if="isTemplate" class="px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-600 border border-indigo-100">
               模版
             </span>
             <span v-else class="px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-600 border border-blue-100">
               我的助手
             </span>
          </div>
        </div>
      </div>

      <!-- Description -->
      <p class="text-xs text-slate-500 leading-relaxed line-clamp-3 mb-4 flex-1 h-[4.5em] group-hover:text-slate-600 transition-colors">
        {{ agent.description || '暂无描述信息...' }}
      </p>

      <!-- Footer -->
      <div class="mt-auto pt-3 border-t border-slate-50 flex items-center justify-between">
        <div class="flex items-center gap-1.5">
           <!-- Status Dot -->
           <div class="w-2 h-2 rounded-full" :class="agent.is_active !== false ? 'bg-green-500' : 'bg-slate-300'"></div>
           <span class="text-[10px] text-slate-400">{{ agent.is_active !== false ? 'Active' : 'Inactive' }}</span>
        </div>
        
        <div class="text-[10px] text-slate-400 font-mono">
           ID: {{ agent.id ? agent.id.substring(0, 6) : '---' }}
        </div>
      </div>
    </div>
    
    <!-- Click Overlay for closing menu -->
    <div v-if="showMenu" class="fixed inset-0 z-10" @click.stop="showMenu = false"></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  agent: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['click', 'edit', 'delete']);

const showMenu = ref(false);

const isTemplate = computed(() => props.agent.is_template);

const isImage = computed(() => {
    const icon = props.agent.icon;
    if (!icon || typeof icon !== 'string') return false;
    const value = icon.trim();
    if (!value) return false;
    if (value.startsWith('data:image')) return true;
    if (value.startsWith('blob:')) return true;
    if (/^https?:\/\//i.test(value)) return true;
    if (value.startsWith('/') || value.startsWith('./') || value.startsWith('../')) return true;
    return /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i.test(value);
});

const toggleMenu = () => {
  showMenu.value = !showMenu.value;
};

const handleAction = (action) => {
  emit(action, props.agent);
  showMenu.value = false;
};
</script>
