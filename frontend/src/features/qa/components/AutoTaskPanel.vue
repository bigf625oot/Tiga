<template>
  <div class="h-full flex flex-col bg-white border-l border-slate-100 shadow-xl shadow-slate-200/50 relative z-10 font-sans">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-white/95 backdrop-blur-sm sticky top-0 z-20">
      <div class="flex items-center gap-4">
        <div>
          <h3 class="font-bold text-slate-900 text-base m-0 tracking-tight">自动任务工作台</h3>
          <p class="text-xs text-slate-500 m-0">自动化任务管理</p>
        </div>
        <div class="bg-slate-100 p-0.5 rounded-lg flex items-center ml-4">
          <button 
            v-for="tab in ['host', 'task', 'node']" 
            :key="tab"
            @click="activeTab = tab"
            class="px-3 py-1 text-xs font-medium rounded-md transition-all duration-200"
            :class="activeTab === tab ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >
            {{ tab === 'host' ? 'GateWay' : (tab === 'task' ? '任务' : '节点') }}
          </button>
        </div>
      </div>
      <button 
        class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
        @click="$emit('close')"
      >
        <CloseOutlined class="text-xs" />
      </button>
    </div>

    <!-- HOST TAB -->
    <GatewayInfo v-if="activeTab === 'host'" />

    <!-- TASK TAB -->
    <TaskManagement 
      v-else-if="activeTab === 'task'"
      :stats="stats"
      :activities="activities"
      :activities-loading="activitiesLoading"
      :templates="templates"
      @create-task="handleCreateTask"
      @refresh-activities="fetchActivities"
      @run-task="(msg) => $emit('run-task', msg)"
    />

    <!-- NODES TAB -->
    <template v-else>
      <NodeDetail 
        v-if="selectedNode" 
        :node="selectedNode" 
        @back="selectedNode = null" 
      />
      <NodeList 
        v-else 
        :nodes="nodes" 
        :loading="nodesLoading" 
        @refresh="fetchNodes" 
        @run-command="runOnNode"
        @select="selectedNode = $event"
      />
    </template>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { CloseOutlined, LineChartOutlined, DollarOutlined, FileTextOutlined, CameraOutlined, ReadOutlined, BarChartOutlined, BellOutlined, AimOutlined } from '@ant-design/icons-vue';
import TaskManagement from './TaskManagement.vue';
import NodeList from './NodeList.vue';
import NodeDetail from './NodeDetail.vue';
import GatewayInfo from './GatewayInfo.vue';

const emit = defineEmits(['close', 'run-task']);

const activeTab = ref('host');
const activitiesLoading = ref(false);
const nodesLoading = ref(false);
const activities = ref<any[]>([]);
const nodes = ref<any[]>([]);
const selectedNode = ref<any>(null);

// Stats Data
const stats = ref<any[]>([
  { label: '抓取', count: '-', trend: '-', trendUp: true, accentColor: 'from-blue-500 to-indigo-600' },
  { label: '监控', count: '-', trend: '-', trendUp: true, accentColor: 'from-purple-500 to-pink-600' },
  { label: '截图', count: '-', trend: '-', trendUp: true, accentColor: 'from-emerald-500 to-teal-600' }
]);

// Templates Data
const templates = [
  {
    icon: LineChartOutlined,
    title: "竞品监控",
    description: "每天9点抓取[网站]，对比[产品]价格变化",
    template: "每天9点抓取 [输入竞品网站URL]，对比 [输入产品名称] 价格变化并发送报告",
    gradient: "from-blue-500/20 via-indigo-500/20 to-purple-500/20",
    iconBg: "from-blue-500 to-indigo-600",
  },
  {
    icon: DollarOutlined,
    title: "价格追踪",
    description: "监控[商品链接]，降价[幅度]%时通知我",
    template: "监控 [输入商品链接]，当降价超过 [输入百分比]% 时通知我",
    gradient: "from-emerald-500/20 via-teal-500/20 to-cyan-500/20",
    iconBg: "from-emerald-500 to-teal-600",
  },
  {
    icon: FileTextOutlined,
    title: "周报生成",
    description: "每周五汇总[数据源]，生成[格式]周报",
    template: "每周五下午5点汇总 [输入数据源]，生成 [输入格式：PDF/Word/HTML] 周报并发送",
    gradient: "from-purple-500/20 via-pink-500/20 to-rose-500/20",
    iconBg: "from-purple-500 to-pink-600",
  },
  {
    icon: CameraOutlined,
    title: "截图存档",
    description: "定期网页截图，留存证据",
    template: "每天 [输入时间] 对 [输入网页URL] 进行全屏截图并保存到云端",
    gradient: "from-amber-500/20 via-orange-500/20 to-red-500/20",
    iconBg: "from-amber-500 to-orange-600",
  },
  {
    icon: ReadOutlined,
    title: "新闻监控",
    description: "监控[关键词]相关新闻，实时推送",
    template: "监控 [输入关键词] 相关新闻，每小时检查一次，有新内容时推送到 [邮箱/微信/钉钉]",
    gradient: "from-cyan-500/20 via-sky-500/20 to-blue-500/20",
    iconBg: "from-cyan-500 to-blue-600",
  },
  {
    icon: BarChartOutlined,
    title: "数据统计",
    description: "每日统计[网站]流量/销量数据",
    template: "每天 [输入时间] 统计 [输入网站/平台] 的 [流量/销量/用户数] 数据并生成图表",
    gradient: "from-violet-500/20 via-purple-500/20 to-fuchsia-500/20",
    iconBg: "from-violet-500 to-purple-600",
  },
  {
    icon: BellOutlined,
    title: "库存监控",
    description: "监控商品库存，有货时通知",
    template: "每 [输入分钟数] 分钟检查 [输入商品链接] 库存状态，有货时立即通知我",
    gradient: "from-red-500/20 via-rose-500/20 to-pink-500/20",
    iconBg: "from-red-500 to-rose-600",
  },
  {
    icon: AimOutlined,
    title: "舆情监控",
    description: "监控社交媒体[品牌/关键词]提及",
    template: "监控 [微博/知乎/小红书] 平台关于 [输入品牌/关键词] 的提及，每天汇总发送",
    gradient: "from-pink-500/20 via-rose-500/20 to-red-500/20",
    iconBg: "from-pink-500 to-rose-600",
  },
];

const handleCreateTask = (prompt: string) => {
  emit('run-task', prompt);
};

const fetchActivities = async () => {
  activitiesLoading.value = true;
  try {
    const res = await fetch('/api/v1/openclaw/activities');
    if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
            activities.value = data;
        } else {
             activities.value = [];
        }
    } else {
        activities.value = [];
    }
  } catch (e) {
    console.error(e);
    activities.value = [];
  } finally {
    activitiesLoading.value = false;
  }
};

const fetchStats = async () => {
  try {
    const res = await fetch('/api/v1/openclaw/stats');
    if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
            stats.value = data;
        }
    }
  } catch (e) {
    console.error(e);
  }
};

const fetchNodes = async () => {
  nodesLoading.value = true;
  try {
    const res = await fetch('/api/v1/nodes/');
    if (res.ok) {
        const data = await res.json();
        nodes.value = data.map((n: any) => ({
            ...n,
            address: n.ip_address || n.address || 'Unknown'
        }));
    } else {
        nodes.value = [];
    }
  } catch (e) {
    console.error(e);
    nodes.value = [];
  } finally {
    nodesLoading.value = false;
  }
};

const runOnNode = (nodeId: string, action: string) => {
    let prompt = '';
    if (action === 'check') {
        prompt = `Check status of node ${nodeId} using 'oc_nodes' tool.`;
    } else if (action === 'screenshot') {
        prompt = `Take a screenshot using node ${nodeId} via 'oc_nodes' run command or 'oc_browser'.`;
    }
    if (prompt) emit('run-task', prompt);
};

let pollInterval: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  fetchActivities();
  fetchStats();
  fetchNodes();
  
  pollInterval = setInterval(() => {
    fetchActivities();
    fetchStats();
  }, 30000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});
</script>
