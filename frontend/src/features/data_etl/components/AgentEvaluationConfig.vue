<script setup lang="ts">
import { ref, computed } from 'vue';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  Activity, 
  Clock, 
  Coins, 
  BrainCircuit, 
  CheckCircle2, 
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  ListChecks,
  TestTube2,
  FileJson,
  PlayCircle,
  RefreshCw,
  HelpCircle,
  ChevronRight,
  Check,
  X,
  Info,
  Zap,
  Eye,
  Settings,
  Loader2
} from 'lucide-vue-next';

interface Trace {
  id: string;
  agent: string;
  task: string;
  status: 'success' | 'error' | 'pending';
  latency: string;
  cost: string;
  time: string;
  tokens: number;
}

interface TestSuite {
  id: string;
  name: string;
  casesCount: number;
  lastRun: string;
  score: number | null;
  status: 'passed' | 'warning' | 'pending';
}

interface Rubric {
  id: string;
  name: string;
  type: string;
  weight: string;
  desc: string;
}

const lastUpdateTime = ref(new Date());
const isRefreshing = ref(false);
const activeTab = ref('monitoring');
const selectedTraceId = ref<string | null>(null);
const showConfirmDialog = ref(false);
const pendingAction = ref<(() => void) | null>(null);

const metrics = ref({
  totalCalls: 12543,
  successRate: 98.5,
  avgLatency: 1.2,
  totalCost: 142.50,
  trend: '+12%',
  trendDirection: 'up' as 'up' | 'down'
});

const recentTraces = ref<Trace[]>([
  { id: 'tr-001', agent: '数据分析助手', task: '提取本月营收报表', status: 'success', latency: '1.5秒', cost: '¥0.09', time: '2分钟前', tokens: 1250 },
  { id: 'tr-002', agent: '网页采集助手', task: '抓取竞品价格信息', status: 'success', latency: '3.2秒', cost: '¥0.18', time: '15分钟前', tokens: 3420 },
  { id: 'tr-003', agent: '代码生成助手', task: '编写单元测试', status: 'error', latency: '5.1秒', cost: '¥0.06', time: '1小时前', tokens: 850 },
  { id: 'tr-004', agent: '客服助手', task: '解答用户发票疑问', status: 'success', latency: '0.8秒', cost: '¥0.04', time: '2小时前', tokens: 420 },
]);

const modelUsage = ref([
  { model: 'GPT-4o', modelName: 'OpenAI主力模型', percentage: 65, calls: 8152 },
  { model: 'Claude-3.5', modelName: 'Anthropic主力模型', percentage: 25, calls: 3135 },
  { model: 'DeepSeek', modelName: '国产开源模型', percentage: 10, calls: 1256 },
]);

const testSuites = ref<TestSuite[]>([
  { id: 'ts-001', name: '职场生产力套件', casesCount: 24, lastRun: '2026-03-19 14:30', score: 92, status: 'passed' },
  { id: 'ts-002', name: '技术开发与重构套件', casesCount: 15, lastRun: '2026-03-20 09:15', score: 78, status: 'warning' },
  { id: 'ts-003', name: '多轮对话与状态保持套件', casesCount: 8, lastRun: '暂未运行', score: null, status: 'pending' }
]);

const rubrics = ref<Rubric[]>([
  { id: 'r-001', name: '结构化输出检查', type: '格式验证', weight: '高', desc: '检查输出是否包含清晰的段落和标题，方便阅读' },
  { id: 'r-002', name: '信息缺口追问', type: '对话质量', weight: '中', desc: '当信息不足时，助手是否主动询问而不是胡乱回答' },
  { id: 'r-003', name: '敏感词过滤', type: '合规检查', weight: '高', desc: '检查输出中是否包含禁用词汇或竞品名称' },
  { id: 'r-004', name: '推理过程检查', type: '逻辑验证', weight: '高', desc: '检查助手的思考过程是否完整清晰' },
]);

const statusConfig = {
  success: { label: '成功', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400', icon: CheckCircle2 },
  error: { label: '失败', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', icon: AlertTriangle },
  pending: { label: '进行中', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400', icon: Loader2 },
};

const testStatusConfig = {
  passed: { label: '通过', color: 'bg-emerald-500 hover:bg-emerald-600', variant: 'default' as const },
  warning: { label: '需优化', color: '', variant: 'destructive' as const },
  pending: { label: '待运行', color: '', variant: 'secondary' as const },
};

const formatUpdateTime = computed(() => {
  const now = new Date();
  const diff = Math.floor((now.getTime() - lastUpdateTime.value.getTime()) / 1000);
  if (diff < 60) return `刚刚`;
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
  return lastUpdateTime.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
});

const handleRefresh = async () => {
  isRefreshing.value = true;
  await new Promise(resolve => setTimeout(resolve, 1000));
  lastUpdateTime.value = new Date();
  isRefreshing.value = false;
};

const confirmAction = (action: () => void) => {
  pendingAction.value = action;
  showConfirmDialog.value = true;
};

const executeAction = () => {
  if (pendingAction.value) {
    pendingAction.value();
    pendingAction.value = null;
  }
  showConfirmDialog.value = false;
};

const cancelAction = () => {
  pendingAction.value = null;
  showConfirmDialog.value = false;
};

const selectTrace = (traceId: string) => {
  selectedTraceId.value = selectedTraceId.value === traceId ? null : traceId;
};

const getTraceDetails = (trace: Trace) => {
  const status = statusConfig[trace.status];
  return {
    ...trace,
    statusLabel: status.label,
    tokenDisplay: trace.tokens >= 1000 ? `${(trace.tokens / 1000).toFixed(1)}k` : trace.tokens.toString(),
  };
};
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <h2 class="text-lg font-semibold dark:text-slate-50">智能体监控与评估</h2>
      </div>
      <div class="flex items-center gap-3">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger as-child>
              <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
                <RefreshCw class="w-3 h-3" />
                <span>更新: {{ formatUpdateTime }}</span>
              </div>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p>数据更新时间</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button 
          size="sm" 
          variant="outline" 
          class="gap-1.5"
          :disabled="isRefreshing"
          @click="handleRefresh"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isRefreshing }" />
          {{ isRefreshing ? '刷新中...' : '刷新数据' }}
        </Button>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger as-child>
              <Button size="sm" variant="ghost" class="gap-1.5">
                <HelpCircle class="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" class="max-w-[280px]">
              <p class="font-medium mb-1">功能说明</p>
              <p class="text-xs">实时监控 Agent 执行状态，查看测试评估结果，管理判分规则</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>

    <!-- Top KPIs -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card class="dark:bg-slate-950 dark:border-slate-800">
        <CardContent class="p-6">
          <div class="flex items-center justify-between space-y-0 pb-2">
            <p class="text-sm font-medium tracking-tight dark:text-slate-200">总调用次数</p>
            <Activity class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="flex items-baseline gap-2">
            <h2 class="text-3xl font-bold dark:text-slate-50">{{ metrics.totalCalls.toLocaleString() }}</h2>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger as-child>
                  <span class="text-xs text-emerald-500 flex items-center cursor-help">
                    <ArrowUpRight class="w-3 h-3 mr-0.5"/>
                    {{ metrics.trend }}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>较上周环比增长</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <p class="text-xs text-muted-foreground mt-1">累计成功执行的任务总数</p>
        </CardContent>
      </Card>

      <Card class="dark:bg-slate-950 dark:border-slate-800">
        <CardContent class="p-6">
          <div class="flex items-center justify-between space-y-0 pb-2">
            <p class="text-sm font-medium tracking-tight dark:text-slate-200">平均执行耗时</p>
            <Clock class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="flex items-baseline gap-2">
            <h2 class="text-3xl font-bold dark:text-slate-50">{{ metrics.avgLatency }}<span class="text-lg font-normal">秒</span></h2>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger as-child>
                  <span class="text-xs text-red-400 flex items-center cursor-help">
                    <ArrowUpRight class="w-3 h-3 mr-0.5"/>
                    0.2秒
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>较上月略有增加</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <p class="text-xs text-muted-foreground mt-1">单次任务平均处理时间</p>
        </CardContent>
      </Card>

      <Card class="dark:bg-slate-950 dark:border-slate-800">
        <CardContent class="p-6">
          <div class="flex items-center justify-between space-y-0 pb-2">
            <p class="text-sm font-medium tracking-tight dark:text-slate-200">任务成功率</p>
            <CheckCircle2 class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="flex flex-col gap-2 mt-2">
            <h2 class="text-3xl font-bold dark:text-slate-50">{{ metrics.successRate }}<span class="text-lg font-normal">%</span></h2>
            <Progress :model-value="metrics.successRate" class="h-2" />
          </div>
          <p class="text-xs text-emerald-500 mt-1 flex items-center gap-1">
            <Check class="w-3 h-3" /> 达到质量目标
          </p>
        </CardContent>
      </Card>

      <Card class="dark:bg-slate-950 dark:border-slate-800">
        <CardContent class="p-6">
          <div class="flex items-center justify-between space-y-0 pb-2">
            <p class="text-sm font-medium tracking-tight dark:text-slate-200">预估消耗总成本</p>
            <Coins class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="flex items-baseline gap-2">
            <h2 class="text-3xl font-bold dark:text-slate-50">¥{{ metrics.totalCost.toFixed(2) }}</h2>
          </div>
          <p class="text-xs text-muted-foreground mt-1">本月AI资源消耗累计</p>
        </CardContent>
      </Card>
    </div>

    <!-- Main Content Tabs -->
    <Tabs v-model="activeTab" class="w-full">
      <div class="flex items-center justify-between mb-4">
        <TabsList class="grid w-[480px] grid-cols-2">
          <TabsTrigger value="monitoring" class="flex items-center gap-2">
            <Eye class="w-4 h-4" />实时监控
          </TabsTrigger>
          <TabsTrigger value="evaluation" class="flex items-center gap-2">
            <TestTube2 class="w-4 h-4" />自动化评估
          </TabsTrigger>
        </TabsList>
        <div class="text-xs text-muted-foreground">
          <span v-if="activeTab === 'monitoring'" class="flex items-center gap-1">
            <Activity class="w-3 h-3 text-emerald-500" /> 实时追踪 Agent 执行状态
          </span>
          <span v-else class="flex items-center gap-1">
            <Zap class="w-3 h-3 text-amber-500" /> 管理测试套件与判分规则
          </span>
        </div>
      </div>

      <!-- Tab: Monitoring & Tracing -->
      <TabsContent value="monitoring" class="space-y-6 mt-0">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Recent Traces -->
          <Card class="lg:col-span-2 dark:bg-slate-950 dark:border-slate-800">
            <CardHeader>
              <div class="flex items-center justify-between">
                <div class="space-y-1">
                  <CardTitle class="flex text-lg items-center gap-2 dark:text-slate-50">
                    智能体执行追踪
                  </CardTitle>
                  <CardDescription class="dark:text-slate-400">点击可查看任务详情</CardDescription>
                </div>
                <Badge variant="outline" class="bg-emerald-500/10 text-emerald-500 border-emerald-500/30">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                  实时
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea class="h-[400px] pr-4">
                <div class="space-y-3">
                  <div 
                    v-for="trace in recentTraces" 
                    :key="trace.id" 
                    class="p-4 border rounded-lg dark:border-slate-800 bg-muted/5 hover:bg-muted/20 transition-all cursor-pointer"
                    :class="{ 'ring-2 ring-primary/50 bg-primary/5': selectedTraceId === trace.id }"
                    @click="selectTrace(trace.id)"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0" :class="statusConfig[trace.status].color">
                          <component :is="statusConfig[trace.status].icon" class="w-5 h-5" />
                        </div>
                        <div class="space-y-1">
                          <p class="text-sm font-medium dark:text-slate-200">{{ trace.task }}</p>
                          <div class="flex items-center gap-2 text-xs text-muted-foreground">
                            <Badge variant="secondary" class="font-normal text-[10px]">{{ trace.agent }}</Badge>
                            <span class="font-mono">{{ trace.id }}</span>
                          </div>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <div class="text-right text-sm space-y-1">
                          <div class="flex items-center gap-2 font-medium dark:text-slate-200">
                            <span class="px-1.5 py-0.5 rounded text-[10px]" :class="statusConfig[trace.status].color">{{ statusConfig[trace.status].label }}</span>
                            <ChevronRight class="w-4 h-4 text-muted-foreground" :class="{ 'rotate-90': selectedTraceId === trace.id }" />
                          </div>
                          <p class="text-xs text-muted-foreground">{{ trace.time }}</p>
                        </div>
                      </div>
                    </div>
                    <div v-if="selectedTraceId === trace.id" class="mt-3 pt-3 border-t dark:border-slate-700 grid grid-cols-3 gap-4">
                      <div class="text-center p-2 bg-muted/30 rounded">
                        <p class="text-[10px] text-muted-foreground mb-0.5">执行耗时</p>
                        <p class="text-sm font-semibold dark:text-slate-200">{{ trace.latency }}</p>
                      </div>
                      <div class="text-center p-2 bg-muted/30 rounded">
                        <p class="text-[10px] text-muted-foreground mb-0.5">Token消耗</p>
                        <p class="text-sm font-semibold dark:text-slate-200">{{ trace.tokens.toLocaleString() }}</p>
                      </div>
                      <div class="text-center p-2 bg-muted/30 rounded">
                        <p class="text-[10px] text-muted-foreground mb-0.5">预估成本</p>
                        <p class="text-sm font-semibold dark:text-slate-200">{{ trace.cost }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <!-- Model Usage Distribution -->
          <Card class="dark:bg-slate-950 dark:border-slate-800">
            <CardHeader>
              <CardTitle class="flex text-lg items-center gap-2 dark:text-slate-50">
                模型调用分布
              </CardTitle>
              <CardDescription class="dark:text-slate-400">查看各AI模型的使用占比</CardDescription>
            </CardHeader>
            <CardContent>
              <div class="space-y-5 pt-2">
                <div v-for="(item, index) in modelUsage" :key="item.model" class="space-y-2">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="w-5 h-5 rounded bg-primary/10 text-primary text-[10px] flex items-center justify-center font-medium">{{ index + 1 }}</span>
                      <span class="font-medium text-sm dark:text-slate-200">{{ item.model }}</span>
                    </div>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <span class="text-muted-foreground text-sm cursor-help">{{ item.percentage }}%</span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p class="text-xs">{{ item.modelName }}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <Progress :model-value="item.percentage" class="h-2.5" />
                  <p class="text-xs text-muted-foreground text-right">{{ item.calls.toLocaleString() }} 次调用</p>
                </div>
              </div>
              <div class="mt-6 p-3 bg-muted/30 rounded-lg border border-dashed dark:border-slate-700">
                <div class="flex items-start gap-2">
                  <Info class="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <p class="text-xs text-muted-foreground">模型调用占比反映AI资源分配，可据此优化成本与性能</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- Tab: Evaluation (Datasets & Rubrics) -->
      <TabsContent value="evaluation" class="space-y-6 mt-0">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Test Suites -->
          <Card class="dark:bg-slate-950 dark:border-slate-800">
            <CardHeader class="flex flex-row items-start justify-between space-y-0">
              <div class="space-y-1">
                <CardTitle class="flex items-center gap-2 dark:text-slate-50">
                  <FileJson class="w-5 h-5 text-primary" />
                  评估测试套件
                </CardTitle>
                <CardDescription class="dark:text-slate-400">管理并执行结构化的 Agent 测试用例</CardDescription>
              </div>
              <div class="flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger as-child>
                      <Button size="sm" variant="ghost" class="gap-1.5">
                        <Settings class="w-4 h-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>套件设置</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Button 
                  size="sm" 
                  variant="default"
                  class="gap-1.5 bg-emerald-600 hover:bg-emerald-700"
                  @click="confirmAction(() => {})"
                >
                  <PlayCircle class="w-4 h-4" /> 运行全部测试
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div class="space-y-4">
                <div 
                  v-for="suite in testSuites" 
                  :key="suite.id" 
                  class="p-4 border rounded-lg dark:border-slate-800 bg-muted/5 hover:bg-muted/20 transition-colors"
                >
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center gap-2">
                      <h4 class="font-medium text-sm dark:text-slate-200">{{ suite.name }}</h4>
                      <Badge 
                        :variant="testStatusConfig[suite.status].variant"
                        :class="testStatusConfig[suite.status].color"
                      >
                        {{ testStatusConfig[suite.status].label }}
                      </Badge>
                    </div>
                    <div v-if="suite.score !== null" class="flex items-center gap-1">
                      <div class="w-16 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          class="h-full rounded-full transition-all"
                          :class="suite.score >= 90 ? 'bg-emerald-500' : suite.score >= 70 ? 'bg-amber-500' : 'bg-red-500'"
                          :style="{ width: `${suite.score}%` }"
                        ></div>
                      </div>
                      <span class="text-sm font-semibold dark:text-slate-200">{{ suite.score }}分</span>
                    </div>
                    <span v-else class="text-xs text-muted-foreground">待评估</span>
                  </div>
                  <div class="flex items-center justify-between text-xs text-muted-foreground">
                    <span class="flex items-center gap-1">
                      <TestTube2 class="w-3.5 h-3.5"/> 
                      <span class="font-medium">{{ suite.casesCount }}</span> 个测试用例
                    </span>
                    <span class="flex items-center gap-1">
                      <Clock class="w-3.5 h-3.5"/> 
                      {{ suite.lastRun }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="mt-4 p-3 bg-muted/30 rounded-lg border border-dashed dark:border-slate-700">
                <div class="flex items-start gap-2">
                  <Info class="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <div class="space-y-1">
                    <p class="text-xs text-muted-foreground">测试套件分数说明</p>
                    <div class="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> 90+ 优秀</span>
                      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-500"></span> 70-89 合格</span>
                      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500"></span> &lt;70 需优化</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Rubrics -->
          <Card class="dark:bg-slate-950 dark:border-slate-800">
            <CardHeader>
              <div class="flex items-center justify-between">
                <div class="space-y-1">
                  <CardTitle class="flex items-center gap-2 dark:text-slate-50">
                    <ListChecks class="w-5 h-5 text-primary" />
                    判分规则库
                  </CardTitle>
                  <CardDescription class="dark:text-slate-400">启发式与 LLM-as-a-Judge 混合评估准则</CardDescription>
                </div>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger as-child>
                      <Badge variant="outline" class="bg-primary/10 text-primary border-primary/30">
                        <Info class="w-3 h-3 mr-1" />
                        {{ rubrics.length }} 条规则
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>当前配置的质量检查规则</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea class="h-[350px] pr-4">
                <div class="space-y-4">
                  <div 
                    v-for="rubric in rubrics" 
                    :key="rubric.id" 
                    class="p-3 border-l-2 border-l-primary bg-muted/10 rounded-r-md space-y-2 hover:bg-muted/20 transition-colors"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-medium text-sm dark:text-slate-200">{{ rubric.name }}</span>
                      <div class="flex items-center gap-2">
                        <Badge variant="outline" class="text-[10px]">{{ rubric.type }}</Badge>
                        <Badge 
                          :variant="rubric.weight === '高' ? 'default' : 'secondary'"
                          :class="rubric.weight === '高' ? 'bg-primary/20 text-primary border-primary/30' : ''"
                        >
                          {{ rubric.weight }}优先级
                        </Badge>
                      </div>
                    </div>
                    <p class="text-xs text-muted-foreground leading-relaxed">{{ rubric.desc }}</p>
                  </div>
                </div>
              </ScrollArea>
              <div class="mt-4 pt-4 border-t dark:border-slate-800">
                <div class="flex items-center justify-between text-xs text-muted-foreground">
                  <span>评估模式说明</span>
                  <span class="font-medium">启发式 + LLM 混合</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>

    <!-- Confirmation Dialog -->
    <Teleport to="body">
      <div v-if="showConfirmDialog" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="cancelAction"></div>
        <Card class="relative z-10 w-[380px] dark:bg-slate-900">
          <CardHeader class="pb-4">
            <CardTitle class="text-base flex items-center gap-2">
              <AlertTriangle class="w-5 h-5 text-amber-500" />
              确认执行操作
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-muted-foreground mb-4">
              确定要运行全部测试套件吗？这可能需要几分钟时间。
            </p>
            <div class="flex items-center justify-end gap-2">
              <Button variant="outline" size="sm" @click="cancelAction">
                <X class="w-4 h-4 mr-1" /> 取消
              </Button>
              <Button variant="default" size="sm" @click="executeAction">
                <Check class="w-4 h-4 mr-1" /> 确认运行
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Teleport>
  </div>
</template>