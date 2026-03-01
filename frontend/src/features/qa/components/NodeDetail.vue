<template>
  <div class="h-full flex flex-col bg-slate-50/30">
    <div class="px-5 py-3 border-b border-slate-100 flex items-center gap-3 bg-white">
      <button 
        class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
        @click="$emit('back')"
      >
        <ArrowLeftOutlined class="text-xs" />
      </button>
      <div>
        <h3 class="font-bold text-slate-900 text-sm m-0">{{ node.name }}</h3>
        <span class="text-[10px] text-slate-400 font-mono">{{ node.id }}</span>
      </div>
      <div class="ml-auto">
          <span 
            class="px-2 py-0.5 text-[10px] font-bold rounded-full border uppercase"
            :class="{
                'bg-emerald-50 text-emerald-600 border-emerald-100': node.status === 'online',
                'bg-rose-50 text-rose-600 border-rose-100': node.status === 'offline' || node.status === 'error',
                'bg-amber-50 text-amber-600 border-amber-100': node.status === 'busy',
                'bg-slate-50 text-slate-500 border-slate-100': !node.status
            }"
          >
            {{ node.status === 'online' ? '在线' : (node.status === 'offline' ? '离线' : (node.status || '未知')) }}
          </span>
      </div>
    </div>

    <div class="p-5 space-y-4 overflow-y-auto custom-scrollbar">
      <!-- Metrics Cards -->
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-blue-50 text-blue-600 rounded-lg"><dashboard-outlined /></div>
             <span class="text-xs font-bold text-slate-600">CPU 使用率</span>
           </div>
           <div class="text-2xl font-bold text-slate-800 font-mono">{{ metrics.cpu || 0 }}<span class="text-xs text-slate-400 ml-1">%</span></div>
           <div class="h-1.5 w-full bg-slate-100 rounded-full mt-2 overflow-hidden">
              <div class="h-full bg-blue-500 rounded-full transition-all duration-500" :style="{ width: (metrics.cpu || 0) + '%' }"></div>
           </div>
        </div>

        <div class="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-purple-50 text-purple-600 rounded-lg"><hdd-outlined /></div>
             <span class="text-xs font-bold text-slate-600">内存使用率</span>
           </div>
           <div class="text-2xl font-bold text-slate-800 font-mono">{{ metrics.memory || 0 }}<span class="text-xs text-slate-400 ml-1">%</span></div>
           <div class="h-1.5 w-full bg-slate-100 rounded-full mt-2 overflow-hidden">
              <div class="h-full bg-purple-500 rounded-full transition-all duration-500" :style="{ width: (metrics.memory || 0) + '%' }"></div>
           </div>
        </div>
        
        <div class="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-orange-50 text-orange-600 rounded-lg"><database-outlined /></div>
             <span class="text-xs font-bold text-slate-600">磁盘使用率</span>
           </div>
           <div class="text-2xl font-bold text-slate-800 font-mono">{{ metrics.disk || 0 }}<span class="text-xs text-slate-400 ml-1">%</span></div>
           <div class="h-1.5 w-full bg-slate-100 rounded-full mt-2 overflow-hidden">
              <div class="h-full bg-orange-500 rounded-full transition-all duration-500" :style="{ width: (metrics.disk || 0) + '%' }"></div>
           </div>
        </div>

        <div class="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg"><cloud-server-outlined /></div>
             <span class="text-xs font-bold text-slate-600">网络流量</span>
           </div>
           <div class="flex justify-between items-end">
             <div>
                <span class="text-[10px] text-slate-400 block">入站</span>
                <span class="text-sm font-bold font-mono">{{ metrics.net_in || 0 }} KB/s</span>
             </div>
             <div>
                <span class="text-[10px] text-slate-400 block text-right">出站</span>
                <span class="text-sm font-bold font-mono">{{ metrics.net_out || 0 }} KB/s</span>
             </div>
           </div>
        </div>

        <div class="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-cyan-50 text-cyan-600 rounded-lg"><wifi-outlined /></div>
             <span class="text-xs font-bold text-slate-600">连接延迟</span>
           </div>
           <div class="text-2xl font-bold text-slate-800 font-mono">{{ metrics.latency || 0 }}<span class="text-xs text-slate-400 ml-1">ms</span></div>
           <div class="text-[10px] text-slate-400 mt-1 flex justify-between">
             <span>丢包率</span>
             <span :class="metrics.packet_loss > 0 ? 'text-rose-500 font-bold' : 'text-emerald-500'">{{ metrics.packet_loss || 0 }}%</span>
           </div>
        </div>
      </div>

      <!-- Recent Alerts -->
      <div>
        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">最近告警</h4>
        <div v-if="!alerts.length" class="text-center py-4 text-xs text-slate-400 bg-white rounded-xl border border-slate-100">
           暂无活跃告警
        </div>
        <div v-else class="space-y-2">
           <div v-for="alert in alerts" :key="alert.id" class="bg-white p-3 rounded-xl border border-l-4 shadow-sm"
                :class="{
                    'border-l-rose-500': alert.level === 'P0',
                    'border-l-orange-500': alert.level === 'P1',
                    'border-l-blue-500': alert.level === 'P2'
                }">
              <div class="flex justify-between items-start">
                  <span class="text-xs font-bold" :class="{
                    'text-rose-600': alert.level === 'P0',
                    'text-orange-600': alert.level === 'P1',
                    'text-blue-600': alert.level === 'P2'
                  }">{{ alert.level }}</span>
                  <span class="text-[10px] text-slate-400">{{ new Date(alert.created_at).toLocaleTimeString() }}</span>
              </div>
              <p class="text-xs text-slate-700 mt-1 m-0">{{ alert.message }}</p>
           </div>
        </div>
      </div>

      <!-- Actions -->
      <div>
        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">操作</h4>
        <div class="grid grid-cols-2 gap-2">
           <button 
             class="py-2 border rounded-lg text-xs font-medium transition-colors"
             :class="node.status === 'online' ? 'bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600' : 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed'"
             :disabled="node.status !== 'online'"
           >
              重启 Agent
           </button>
           <button 
             class="py-2 border rounded-lg text-xs font-medium transition-colors"
             :class="node.status === 'online' ? 'bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600' : 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed'"
             :disabled="node.status !== 'online'"
           >
              查看日志
           </button>
           <button 
             class="py-2 border rounded-lg text-xs font-medium transition-colors"
             :class="node.status === 'online' ? 'bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600' : 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed'"
             :disabled="node.status !== 'online'"
           >
              更新配置
           </button>
           <button class="py-2 bg-rose-50 border border-rose-100 rounded-lg text-xs font-medium text-rose-600 hover:bg-rose-100 transition-colors">
              节点退役
           </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { 
  ArrowLeftOutlined,
  DashboardOutlined,
  HddOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  WifiOutlined
} from '@ant-design/icons-vue';

const props = defineProps<{
  node: any;
}>();

defineEmits(['back']);

// Mock metrics for now, normally fetched from API
const metrics = computed(() => {
    // 如果节点离线，返回0
    if (props.node.status !== 'online') {
        return { cpu: 0, memory: 0, disk: 0, net_in: 0, net_out: 0, latency: 0, packet_loss: 0 };
    }
    
    // In a real app, we would fetch /api/v1/nodes/{id}/metrics
    return {
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        disk: Math.floor(Math.random() * 100),
        net_in: Math.floor(Math.random() * 1000),
        net_out: Math.floor(Math.random() * 1000),
        latency: Math.floor(Math.random() * 50) + 10,
        packet_loss: Math.random() > 0.9 ? Math.floor(Math.random() * 5) : 0
    };
});

// Mock alerts
const alerts = computed(() => {
    if (props.node.status === 'offline') {
        return [{ id: 1, level: 'P0', message: 'Node heartbeat timeout', created_at: new Date() }];
    }
    if (props.node.status === 'busy') {
        return [{ id: 2, level: 'P1', message: 'High CPU usage', created_at: new Date() }];
    }
    return [];
});
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
