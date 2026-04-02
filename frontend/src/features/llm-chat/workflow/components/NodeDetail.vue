<template>
  <div class="h-full flex flex-col bg-muted/50/30 dark:bg-slate-900/50">
    <div class="p-6 p-4 border-b border-border flex items-center gap-4 bg-white dark:bg-slate-800">
      <button 
        class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-muted text-muted-foreground hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
        @click="$emit('back')"
      >
        <ArrowLeftOutlined class="text-xs" />
      </button>
      <div>
        <h3 class="font-semibold text-slate-900 dark:text-slate-100 text-sm m-0">{{ node.name }}</h3>
        <span class="text-[10px] text-muted-foreground font-mono">{{ node.id }}</span>
      </div>
      <div class="ml-auto">
          <span 
            class="px-2 py-0.5 text-[10px] font-semibold rounded-full border uppercase"
            :class="{
                'bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-900/50': node.status === 'online',
                'bg-rose-50 text-rose-600 border-rose-100 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-900/50': node.status === 'offline' || node.status === 'error',
                'bg-amber-50 text-amber-600 border-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-900/50': node.status === 'busy',
                'bg-muted/50 text-muted-foreground border-border dark:bg-slate-800 dark:text-slate-400': !node.status
            }"
          >
            {{ node.status === 'online' ? '在线' : (node.status === 'offline' ? '离线' : (node.status || '未知')) }}
          </span>
      </div>
    </div>

    <div class="p-6 space-y-4 overflow-y-auto custom-scrollbar">
      <!-- Metrics Cards -->
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg border border-border dark:border-slate-700 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-foreground rounded-lg"><dashboard-outlined /></div>
             <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">CPU 使用率</span>
           </div>
           <div class="text-2xl font-semibold text-slate-800 dark:text-slate-100 font-mono">{{ metrics.cpu || 0 }}<span class="text-xs text-muted-foreground ml-1">%</span></div>
           <div class="h-1.5 w-full bg-muted dark:bg-slate-700 rounded-full mt-2 overflow-hidden">
              <div class="h-full bg-blue-500 rounded-full transition-all duration-500" :style="{ width: (metrics.cpu || 0) + '%' }"></div>
           </div>
        </div>

        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg border border-border dark:border-slate-700 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400 rounded-lg"><hdd-outlined /></div>
             <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">内存使用率</span>
           </div>
           <div class="text-2xl font-semibold text-slate-800 dark:text-slate-100 font-mono">{{ metrics.memory || 0 }}<span class="text-xs text-muted-foreground ml-1">%</span></div>
           <div class="h-1.5 w-full bg-muted dark:bg-slate-700 rounded-full mt-2 overflow-hidden">
              <div class="h-full bg-purple-500 rounded-full transition-all duration-500" :style="{ width: (metrics.memory || 0) + '%' }"></div>
           </div>
        </div>
        
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg border border-border dark:border-slate-700 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400 rounded-lg"><database-outlined /></div>
             <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">磁盘使用率</span>
           </div>
           <div class="text-2xl font-semibold text-slate-800 dark:text-slate-100 font-mono">{{ metrics.disk || 0 }}<span class="text-xs text-muted-foreground ml-1">%</span></div>
           <div class="h-1.5 w-full bg-muted dark:bg-slate-700 rounded-full mt-2 overflow-hidden">
              <div class="h-full bg-orange-500 rounded-full transition-all duration-500" :style="{ width: (metrics.disk || 0) + '%' }"></div>
           </div>
        </div>

        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg border border-border dark:border-slate-700 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400 rounded-lg"><cloud-server-outlined /></div>
             <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">网络流量</span>
           </div>
           <div class="flex justify-between items-end">
             <div>
                <span class="text-[10px] text-muted-foreground block">入站</span>
                <span class="text-sm font-semibold font-mono text-slate-800 dark:text-slate-100">{{ metrics.net_in || 0 }} KB/s</span>
             </div>
             <div>
                <span class="text-[10px] text-muted-foreground block text-right">出站</span>
                <span class="text-sm font-semibold font-mono text-slate-800 dark:text-slate-100">{{ metrics.net_out || 0 }} KB/s</span>
             </div>
           </div>
        </div>

        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg border border-border dark:border-slate-700 shadow-sm">
           <div class="flex items-center gap-2 mb-2">
             <div class="p-1.5 bg-cyan-50 text-cyan-600 dark:bg-cyan-900/30 dark:text-cyan-400 rounded-lg"><wifi-outlined /></div>
             <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">连接延迟</span>
           </div>
           <div class="text-2xl font-semibold text-slate-800 dark:text-slate-100 font-mono">{{ metrics.latency || 0 }}<span class="text-xs text-muted-foreground ml-1">ms</span></div>
           <div class="text-[10px] text-muted-foreground mt-1 flex justify-between">
             <span>丢包率</span>
             <span :class="metrics.packet_loss > 0 ? 'text-rose-500 font-semibold' : 'text-emerald-500 dark:text-emerald-400'">{{ metrics.packet_loss || 0 }}%</span>
           </div>
        </div>
      </div>

      <!-- Recent Alerts -->
      <div>
        <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">最近告警</h4>
        <div v-if="!alerts.length" class="text-center py-4 text-xs text-muted-foreground bg-white dark:bg-slate-800 rounded-lg border border-border">
           暂无活跃告警
        </div>
        <div v-else class="space-y-2">
           <div v-for="alert in alerts" :key="alert.id" class="bg-white dark:bg-slate-800 p-4 rounded-lg border border-l-4 shadow-sm"
                :class="{
                    'border-l-rose-500': alert.level === 'P0',
                    'border-l-orange-500': alert.level === 'P1',
                    'border-l-blue-500': alert.level === 'P2'
                }">
              <div class="flex justify-between items-start">
                  <span class="text-xs font-semibold" :class="{
                    'text-rose-600 dark:text-rose-400': alert.level === 'P0',
                    'text-orange-600 dark:text-orange-400': alert.level === 'P1',
                    'text-primary': alert.level === 'P2'
                  }">{{ alert.level }}</span>
                  <span class="text-[10px] text-muted-foreground">{{ new Date(alert.created_at).toLocaleTimeString() }}</span>
              </div>
              <p class="text-xs text-slate-700 dark:text-slate-300 mt-1 m-0">{{ alert.message }}</p>
           </div>
        </div>
      </div>

      <!-- Actions -->
      <div>
        <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">操作</h4>
        <div class="grid grid-cols-2 gap-2">
           <button 
             class="py-2 border rounded-lg text-xs font-medium transition-colors"
             :class="node.status === 'online' ? 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-600 dark:hover:text-indigo-400' : 'bg-muted/50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-muted-foreground cursor-not-allowed'"
             :disabled="node.status !== 'online'"
           >
              重启 Agent
           </button>
           <button 
             class="py-2 border rounded-lg text-xs font-medium transition-colors"
             :class="node.status === 'online' ? 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-600 dark:hover:text-indigo-400' : 'bg-muted/50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-muted-foreground cursor-not-allowed'"
             :disabled="node.status !== 'online'"
           >
              查看日志
           </button>
           <button 
             class="py-2 border rounded-lg text-xs font-medium transition-colors"
             :class="node.status === 'online' ? 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-600 dark:hover:text-indigo-400' : 'bg-muted/50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-muted-foreground cursor-not-allowed'"
             :disabled="node.status !== 'online'"
           >
              更新配置
           </button>
           <button class="py-2 bg-rose-50 dark:bg-rose-900/20 border border-rose-100 dark:border-rose-900/30 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/30 transition-colors">
              节点退役
           </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * @场景    节点列表中进入单节点详情后查看运行指标、告警与维护操作
 * @功能    提供节点状态摘要、资源指标面板与告警信息展示
 * @依赖    Vue3、TypeScript、Ant Design 图标
 * @备注    当前指标与告警为本地模拟数据，后续需切换到真实监控接口
 */
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
