<template>
  <div class="container mx-auto p-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div class="flex flex-col space-y-2">
      <h1 class="text-3xl font-bold tracking-tight">数据概览</h1>
      <p class="text-muted-foreground">
        实时监控指标提取与分析任务的运行状态
      </p>
    </div>

    <!-- Summary Cards -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card v-for="(stat, index) in stats" :key="index" class="p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
        <div class="flex items-center justify-between space-y-0 pb-2">
          <span class="text-sm font-medium text-muted-foreground">{{ stat.title }}</span>
          <component :is="stat.icon" class="h-4 w-4 text-muted-foreground" />
        </div>
        <div class="space-y-1">
          <div class="text-2xl font-bold tracking-tight">{{ stat.value }}</div>
          <p class="text-xs text-muted-foreground flex items-center gap-1">
            <span :class="stat.trend > 0 ? 'text-green-500' : 'text-red-500'" class="flex items-center">
              <ArrowUpRight v-if="stat.trend > 0" class="w-3 h-3 mr-0.5" />
              <ArrowDownRight v-else class="w-3 h-3 mr-0.5" />
              {{ Math.abs(stat.trend) }}%
            </span>
            <span>较上周</span>
          </p>
        </div>
      </Card>
    </div>

    <!-- Charts Section -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
      <!-- Main Trend Chart -->
      <Card class="col-span-4 p-6 flex flex-col">
        <div class="mb-4">
          <h3 class="text-lg font-semibold">提取任务趋势</h3>
          <p class="text-sm text-muted-foreground">过去 7 天的任务执行情况</p>
        </div>
        <div class="flex-1 min-h-[300px] w-full bg-muted/10 rounded-lg relative overflow-hidden">
             <ChartFrame :option="trendChartOption" class="w-full h-full" />
        </div>
      </Card>

      <!-- Distribution Chart -->
      <Card class="col-span-3 p-6 flex flex-col">
        <div class="mb-4">
          <h3 class="text-lg font-semibold">指标类型分布</h3>
          <p class="text-sm text-muted-foreground">按指标类别统计</p>
        </div>
        <div class="flex-1 min-h-[300px] w-full bg-muted/10 rounded-lg relative overflow-hidden">
             <ChartFrame :option="pieChartOption" class="w-full h-full" />
        </div>
      </Card>
    </div>

    <!-- Recent Activity & Models -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
      <Card class="col-span-4 p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-lg font-semibold">最近活动</h3>
            <p class="text-sm text-muted-foreground">最新的 5 条任务记录</p>
          </div>
          <Button variant="ghost" size="sm" class="text-xs">查看全部</Button>
        </div>
        <div class="space-y-4">
          <div v-for="(activity, i) in recentActivities" :key="i" class="flex items-center justify-between border-b last:border-0 pb-4 last:pb-0">
            <div class="flex items-center gap-4">
              <div class="w-9 h-9 rounded-full bg-muted/50 flex items-center justify-center border">
                <FileText v-if="activity.type === 'batch'" class="w-4 h-4 text-blue-500" />
                <File v-else class="w-4 h-4 text-purple-500" />
              </div>
              <div class="space-y-1">
                <p class="text-sm font-medium leading-none">{{ activity.name }}</p>
                <p class="text-xs text-muted-foreground">{{ activity.time }}</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
               <Badge :variant="activity.status === 'completed' ? 'secondary' : 'destructive'" class="text-[10px]">
                 {{ activity.status === 'completed' ? '成功' : '失败' }}
               </Badge>
               <span class="text-xs font-mono text-muted-foreground">{{ activity.duration }}s</span>
            </div>
          </div>
        </div>
      </Card>

      <Card class="col-span-3 p-6">
        <div class="mb-4">
          <h3 class="text-lg font-semibold">模型使用概况</h3>
          <p class="text-sm text-muted-foreground">各模型调用次数统计</p>
        </div>
        <div class="space-y-4">
          <div v-for="model in modelUsage" :key="model.name" class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" :class="model.color"></span>
                <span class="font-medium">{{ model.name }}</span>
              </div>
              <span class="text-muted-foreground">{{ model.count }} 次</span>
            </div>
            <div class="h-2 w-full bg-muted rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500" :class="model.color.replace('text-', 'bg-')" :style="{ width: model.percentage + '%' }"></div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  Activity, ArrowUpRight, ArrowDownRight, Users, 
  FileText, File, Clock, Zap, BarChart3 
} from 'lucide-vue-next';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import ChartFrame from './ChartFrame.vue';

// Stats Data
const stats = [
  { 
    title: '总提取任务', 
    value: '1,284', 
    icon: Activity, 
    trend: 12.5 
  },
  { 
    title: '平均准确率', 
    value: '98.2%', 
    icon: BarChart3, 
    trend: 0.8 
  },
  { 
    title: '活跃指标数', 
    value: '342', 
    icon: Zap, 
    trend: -2.1 
  },
  { 
    title: '平均耗时', 
    value: '1.8s', 
    icon: Clock, 
    trend: -5.4 
  },
];

// Recent Activities
const recentActivities = [
  { name: 'Q3_财务报告_批量提取', type: 'batch', time: '10分钟前', status: 'completed', duration: 45.2 },
  { name: '新能源行业分析.pdf', type: 'single', time: '25分钟前', status: 'completed', duration: 2.1 },
  { name: '2023年度审计报告.docx', type: 'single', time: '1小时前', status: 'failed', duration: 1.5 },
  { name: '竞品分析_V2.pdf', type: 'single', time: '2小时前', status: 'completed', duration: 3.4 },
  { name: '市场调研数据_0901', type: 'batch', time: '3小时前', status: 'completed', duration: 128.5 },
];

// Model Usage
const modelUsage = [
  { name: 'Qwen-Plus', count: 854, percentage: 65, color: 'text-purple-500' },
  { name: 'Qwen-Max', count: 321, percentage: 25, color: 'text-blue-500' },
  { name: 'Qwen-Long', count: 109, percentage: 10, color: 'text-indigo-500' },
];

// ECharts Options
const trendChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: '#e2e8f0',
    textStyle: { color: '#1e293b' }
  },
  grid: {
    top: '10%',
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    axisLine: { lineStyle: { color: '#94a3b8' } },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f1f5f9' } },
    axisLine: { show: false },
    axisTick: { show: false }
  },
  series: [
    {
      name: '任务量',
      type: 'line',
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.1,
        color: '#9333ea'
      },
      lineStyle: {
        width: 3,
        color: '#9333ea'
      },
      data: [120, 132, 101, 134, 90, 230, 210]
    }
  ]
}));

const pieChartOption = computed(() => ({
  tooltip: {
    trigger: 'item'
  },
  legend: {
    bottom: '0%',
    left: 'center',
    icon: 'circle'
  },
  series: [
    {
      name: '指标分布',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 20,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: [
        { value: 1048, name: '财务指标', itemStyle: { color: '#9333ea' } },
        { value: 735, name: '运营指标', itemStyle: { color: '#a855f7' } },
        { value: 580, name: '市场指标', itemStyle: { color: '#c084fc' } },
        { value: 484, name: '风险指标', itemStyle: { color: '#d8b4fe' } },
        { value: 300, name: '其他', itemStyle: { color: '#e9d5ff' } }
      ]
    }
  ]
}));
</script>
