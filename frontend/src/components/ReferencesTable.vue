<template>
  <div class="w-full">
    <div v-if="loading" class="p-4 text-center text-slate-500">加载中...</div>
    <div v-else-if="items.length === 0" class="p-4 text-center text-slate-400">暂无数据</div>
    <a-table
      v-else
      :columns="columns"
      :data-source="pagedItems"
      :pagination="pagination"
      :row-key="rowKey"
      @change="handleChange"
      class="rounded-xl border border-slate-200 overflow-hidden"
    />
  </div>
</template>

<script setup>
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
