<template>
  <div class="w-full">
    <div v-if="loading" class="p-4 text-center text-muted-foreground">加载中...</div>
    <div v-else-if="items.length === 0" class="p-4 text-center text-muted-foreground">暂无数据</div>
    <div v-else class="grid gap-4" :class="gridClass">
      <div v-for="it in items" :key="it.id + '-' + it.title" class="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
        <img v-if="it.coverImage" :src="it.coverImage" alt="" loading="lazy" class="w-full object-cover max-h-40">
        <div class="p-4">
          <div class="text-sm font-medium text-slate-700 truncate">{{ it.title }}</div>
          <div class="text-xs text-muted-foreground mt-1">{{ it.createTime }}</div>
          <div class="text-xs text-slate-600 mt-2 line-clamp-3">{{ it.summary }}</div>
          <div class="flex flex-wrap gap-2 mt-2">
            <span v-for="t in it.tags || []" :key="t" class="px-2 py-0.5 text-[11px] rounded bg-muted text-slate-600">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @场景    以卡片形式展示参考来源，适合图文化内容浏览
 * @功能    提供网格布局、封面图与标签渲染
 * @依赖    Vue3
 * @备注    当前在 SmartQA 中仅导入未使用，建议与 ReferencesTable 二选一保留
 */
import { computed } from 'vue';
const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  mode: { type: String, default: 'grid' }
});
const gridClass = computed(() => props.mode === 'masonry' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 auto-rows-max' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3');
</script>

<style>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
