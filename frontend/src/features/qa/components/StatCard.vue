<template>
  <div class="relative overflow-hidden border border-slate-100 bg-white shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group rounded-2xl p-4 cursor-default">
    <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r" :class="accentColor"></div>
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs text-slate-500 font-medium m-0">{{ label }}</p>
      <div class="flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full" :class="trendUp ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50'">
        <RiseOutlined v-if="trendUp" />
        <FallOutlined v-else />
        {{ trend }}
      </div>
    </div>
    <div class="flex items-baseline">
      <span class="text-2xl font-bold text-slate-900 tracking-tight">{{ count }}</span>
      <span class="text-xs text-slate-400 ml-1">次</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * @场景    自动任务统计区域展示单项指标卡片（次数、趋势、色彩提示）
 * @功能    提供通用统计卡片渲染能力
 * @依赖    Vue3、TypeScript、Ant Design 图标
 * @备注    作为纯展示组件，可复用到其他任务运营面板
 */
import { RiseOutlined, FallOutlined } from '@ant-design/icons-vue';

defineProps<{
  label: string;
  count: number | string;
  trend: string;
  trendUp: boolean;
  accentColor: string;
}>();
</script>
