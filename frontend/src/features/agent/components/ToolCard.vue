<template>
  <div 
    class="group bg-white border border-slate-200 rounded-2xl hover:shadow-xl hover:border-blue-200 transition-all duration-300 flex flex-col h-[260px] relative overflow-hidden"
  >
    <div class="p-5 flex flex-col h-full">
      <!-- Header: Icon + Title + Menu -->
      <div class="flex gap-4 mb-3">
        <!-- Icon -->
        <div 
          v-if="item.iconUrl" 
          class="relative flex-shrink-0 w-12 h-12 bg-slate-50 rounded-xl p-0.5 group-hover:scale-105 transition-transform duration-300 flex items-center justify-center"
        >
          <img :src="item.iconUrl" class="w-full h-full object-contain" alt="icon" />
          <!-- Status Indicator -->
          <div v-if="item.is_active !== false" class="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full z-10"></div>
        </div>
        
        <div 
          v-else 
          class="relative flex-shrink-0 w-12 h-12 flex items-center justify-center text-xl text-slate-400 bg-slate-50 rounded-xl border border-slate-100 shadow-sm group-hover:scale-105 transition-transform duration-300"
        >
          {{ item.icon || item.name.charAt(0).toUpperCase() }}
          <!-- Status Indicator -->
          <div v-if="item.is_active !== false" class="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full z-10"></div>
        </div>
        
        <!-- Title & Tags Area -->
        <div class="flex-1 min-w-0 flex flex-col justify-between py-0.5">
          <div class="flex justify-between items-start">
            <h3 class="font-bold text-slate-800 text-base leading-tight truncate pr-2 group-hover:text-blue-600 transition-colors" :title="item.name">
              {{ item.name }}
            </h3>
            
            <!-- Menu Trigger -->
            <div v-if="!item.is_official" class="relative flex-shrink-0">
              <button 
                @click.stop="$emit('toggle-menu', item.id)"
                class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                :class="{'opacity-100 bg-slate-100 text-slate-600': activeMenuId === item.id}"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </button>
              
              <!-- Dropdown Menu -->
              <div 
                v-if="activeMenuId === item.id"
                class="absolute right-0 top-full mt-1 w-32 bg-white border border-slate-100 rounded-xl shadow-xl z-20 py-1.5 animate-in fade-in zoom-in duration-100 origin-top-right"
                @click.stop
              >
                <button 
                  @click="$emit('edit', item); $emit('toggle-menu', null)"
                  class="w-full text-left px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-blue-600 transition-colors flex items-center gap-2"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  编辑配置
                </button>
                <button 
                  @click="$emit('delete', item); $emit('toggle-menu', null)"
                  class="w-full text-left px-4 py-2 text-xs font-medium text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors flex items-center gap-2"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  移除工具
                </button>
              </div>
            </div>
          </div>

          <!-- Tags -->
          <div class="flex flex-wrap items-center gap-2 mt-1">
            <span class="px-2 py-0.5 rounded-md text-[10px] font-bold border tracking-wide uppercase" 
              :class="item.type === 'mcp' ? 'bg-purple-50 text-purple-600 border-purple-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'">
              {{ item.type === 'mcp' ? 'MCP' : 'Skill' }}
            </span>
            <span v-if="item.is_official" class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-100 flex items-center gap-1">
              <svg class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              官方认证
            </span>
          </div>
        </div>
      </div>

      <!-- Description -->
      <p class="text-xs text-slate-500 leading-relaxed line-clamp-3 mb-4 flex-1 h-[4.5em] group-hover:text-slate-600 transition-colors" :title="item.description">
        {{ item.description || '暂无描述信息' }}
      </p>

      <!-- Footer -->
      <div class="mt-auto pt-4 border-t border-slate-50 flex flex-col gap-3">
        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] font-bold text-slate-500">
              {{ item.author ? item.author.charAt(0).toUpperCase() : 'U' }}
            </div>
            <span class="truncate max-w-[80px]" :title="item.author">@{{ item.author }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span v-if="item.downloads" class="flex items-center gap-1" title="下载量">
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              {{ item.downloads }}k
            </span>
            <span class="bg-slate-50 px-1.5 py-0.5 rounded text-slate-400 font-mono">v{{ item.version }}</span>
          </div>
        </div>

        <button 
          @click.stop="$emit('install', item)"
          class="w-full py-2 text-xs font-medium rounded-lg transition-all duration-200 border flex items-center justify-center gap-2"
          :class="item.installed || (item.is_active === false)
            ? 'bg-slate-50 text-slate-400 border-transparent cursor-default' 
            : 'bg-white border-slate-200 text-slate-700 hover:text-blue-600 hover:border-blue-200 hover:shadow-md hover:bg-blue-50/30 active:scale-[0.98]'"
          :disabled="item.installed || item.isInstalling || (item.is_active === false)"
          :title="(item.is_active === false) ? '工具未配置或不可用' : ''"
        >
          <template v-if="item.isInstalling">
            <svg class="animate-spin h-3.5 w-3.5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="text-blue-500">安装中...</span>
          </template>
          <template v-else-if="item.installed">
            <svg class="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span>已安装</span>
          </template>
          <template v-else-if="item.is_active === false">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            <span>不可用</span>
          </template>
          <template v-else>
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>获取工具</span>
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  item: {
    type: Object,
    required: true
  },
  activeMenuId: {
    type: String,
    default: null
  }
});

defineEmits(['toggle-menu', 'edit', 'delete', 'install']);
</script>
