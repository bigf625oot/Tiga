<template>
  <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar bg-slate-50/30">
    <div class="flex justify-between items-center mb-2">
      <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">节点列表 ({{ nodes.length }})</span>
      <button 
        class="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-indigo-500 transition-colors"
        :class="{ 'animate-spin': loading }"
        @click="$emit('refresh')"
      >
        <ReloadOutlined />
      </button>
    </div>

    <div v-if="loading" class="space-y-3">
       <div class="bg-white p-4 rounded-xl border border-slate-100 shadow-sm"><a-skeleton active :paragraph="{ rows: 1 }" /></div>
       <div class="bg-white p-4 rounded-xl border border-slate-100 shadow-sm"><a-skeleton active :paragraph="{ rows: 1 }" /></div>
    </div>

    <div v-else-if="!nodes.length" class="flex flex-col items-center justify-center py-16 text-slate-400">
       <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-3">
          <DisconnectOutlined class="text-2xl text-slate-300" />
       </div>
       <span class="text-xs">暂无在线节点</span>
       <button class="mt-4 text-xs text-indigo-600 font-medium hover:underline" @click="$emit('refresh')">刷新重试</button>
    </div>

    <div v-else class="grid grid-cols-1 gap-3">
      <div 
        v-for="node in nodes" 
        :key="node.id" 
        class="group relative bg-white rounded-xl border transition-all duration-200 hover:shadow-md overflow-hidden"
        :class="node.status === 'online' ? 'border-slate-200 hover:border-indigo-300' : 'border-slate-100 opacity-80'"
        @click="$emit('select', node)"
      >
         <!-- Header -->
         <div class="p-4 border-b border-slate-50 flex justify-between items-start">
            <div class="flex items-center gap-3">
               <!-- Status Indicator -->
               <div class="relative flex h-3 w-3">
                  <span v-if="node.status === 'online'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-3 w-3" 
                    :class="{
                        'bg-emerald-500': node.status === 'online',
                        'bg-slate-300': node.status === 'offline' || node.status === 'unknown',
                        'bg-amber-500': node.status === 'busy'
                    }"
                  ></span>
               </div>
               
               <div class="overflow-hidden">
                 <div class="flex items-center gap-2">
                    <h5 class="font-bold text-slate-800 text-sm m-0 truncate">{{ node.name }}</h5>
                    <span v-if="node.platform && node.platform !== 'unknown'" class="px-1.5 py-0.5 bg-slate-100 text-slate-500 text-[10px] rounded font-medium uppercase shrink-0">{{ node.platform }}</span>
                 </div>
                 <div class="text-[10px] text-slate-400 font-mono mt-0.5 truncate" :title="node.id">ID: {{ node.id }}</div>
               </div>
            </div>
            
            <div class="flex flex-col items-end shrink-0">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                    :class="{
                        'bg-emerald-50 text-emerald-600': node.status === 'online',
                        'bg-slate-100 text-slate-500': node.status === 'offline' || node.status === 'unknown',
                        'bg-amber-50 text-amber-600': node.status === 'busy'
                    }"
                >
                    {{ node.status === 'online' ? '运行中' : (node.status === 'busy' ? '忙碌' : '离线') }}
                </span>
            </div>
         </div>
         
         <!-- Details -->
         <div class="p-4 bg-slate-50/30 grid grid-cols-2 gap-4">
            <div>
              <div class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">版本</div>
              <div class="text-xs font-mono text-slate-600">{{ node.version || '--' }}</div>
            </div>
            <div>
              <div class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">地址</div>
              <div class="text-xs font-mono text-slate-600 truncate" :title="node.address">{{ node.address || '--' }}</div>
            </div>
         </div>

         <!-- Actions -->
         <div class="px-4 py-3 bg-white border-t border-slate-50 flex gap-2" @click.stop>
            <button 
              class="flex-1 py-1.5 rounded-lg border text-xs font-medium transition-colors flex items-center justify-center gap-1.5"
              :class="node.status === 'online' ? 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-indigo-600 hover:border-indigo-200' : 'border-slate-100 text-slate-300 cursor-not-allowed'"
              :disabled="node.status !== 'online'"
              @click="node.status === 'online' && $emit('run-command', node.id, 'check')"
            >
              <CheckCircleOutlined /> 状态检查
            </button>
             <button 
              class="flex-1 py-1.5 rounded-lg border text-xs font-medium transition-colors flex items-center justify-center gap-1.5"
              :class="node.status === 'online' ? 'bg-indigo-50 text-indigo-600 border-indigo-100 hover:bg-indigo-100 hover:border-indigo-200' : 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed'"
              :disabled="node.status !== 'online'"
              @click="node.status === 'online' && $emit('run-command', node.id, 'screenshot')"
            >
              <CameraOutlined /> 截图
            </button>
         </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { 
  ReloadOutlined, 
  DisconnectOutlined, 
  CheckCircleOutlined, 
  CameraOutlined 
} from '@ant-design/icons-vue';

defineProps<{
  nodes: any[];
  loading: boolean;
}>();

defineEmits(['refresh', 'run-command', 'select']);
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
