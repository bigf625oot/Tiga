<template>
  <div class="w-full">
    <div v-if="loading" class="p-4 text-center text-muted-foreground">加载中...</div>
    <div v-else-if="items.length === 0" class="p-4 text-center text-muted-foreground">暂无数据</div>
    <a-table
      v-else
      :columns="columns"
      :data-source="pagedItems"
      :pagination="pagination"
      :row-key="rowKey"
      @change="handleChange"
      class="rounded-lg border border-slate-200 overflow-hidden"
    />
  </div>
</template>

<script setup>
/**
 * @场景    以表格形式浏览参考来源记录，适用于结构化来源查看
 * @功能    提供来源排序、分页与表格渲染能力
 * @依赖    Vue3、Ant Design Vue Table
 * @备注    当前在 SmartQA 中仅导入未使用，属于候选下线组件
 */
import { computed, ref, watch } from 'vue';

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
});

const page = ref(1);
const pageSize = ref(10);
const sortField = ref('createTime');
const sortOrder = ref('descend');

const columns = [
  { title: 'ID', dataIndex: 'id', sorter: true },
  { title: '标题', dataIndex: 'title', sorter: true },
  { title: '创建时间', dataIndex: 'createTime', sorter: true },
  { title: '摘要', dataIndex: 'summary' }
];

const rowKey = (r) => `${r.id}-${r.title}`;

const sortedItems = computed(() => {
  const arr = [...props.items];
  const field = sortField.value;
  arr.sort((a, b) => {
    const va = a[field] || '';
    const vb = b[field] || '';
    if (sortOrder.value === 'ascend') return va > vb ? 1 : -1;
    return va < vb ? 1 : -1;
  });
  return arr;
});

const pagedItems = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return sortedItems.value.slice(start, start + pageSize.value);
});

const pagination = computed(() => ({
  current: page.value,
  pageSize: pageSize.value,
  total: props.items.length,
  showSizeChanger: true
}));

const handleChange = (p, f, s) => {
  page.value = p.current;
  pageSize.value = p.pageSize;
  if (s && s.field) {
    sortField.value = s.field;
    sortOrder.value = s.order || 'descend';
  }
};
</script>
