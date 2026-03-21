<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import { GraphViewer } from '@/shared/components/organisms/GraphViewer';
import type { IGraphNode, IGraphEdge } from '@/shared/types/graph';

const props = defineProps<{
  entityTypes: string[];
  relationTypes: string[];
}>();

const nodeColors: Record<string, string> = {
  人物: '#3b82f6',
  组织: '#8b5cf6',
  地点: '#10b981',
  产品: '#f59e0b',
  事件: '#ef4444',
  default: '#6366f1'
};

const nodes = ref<Record<string, IGraphNode>>({});
const edges = ref<Record<string, IGraphEdge>>({});

const generatePreview = () => {
  if (props.entityTypes.length === 0) {
    nodes.value = {};
    edges.value = {};
    return;
  }

  const newNodes: Record<string, IGraphNode> = {};
  const newEdges: Record<string, IGraphEdge> = {};

  props.entityTypes.forEach((type, i) => {
    const count = type.length > 2 ? 2 : 1;
    for (let j = 0; j < count; j++) {
      const label = type + (count > 1 ? (j + 1) : '');
      const id = `${type}-${j}`;
      newNodes[id] = {
        id,
        name: label,
        type,
        color: nodeColors[type] || nodeColors.default,
        attributes: {}
      };
    }

    if (i < props.entityTypes.length - 1) {
      const relType = props.relationTypes[i % props.relationTypes.length] || '关联';
      const edgeId = `edge-${i}`;
      newEdges[edgeId] = {
        id: edgeId,
        source: `${type}-0`,
        target: `${props.entityTypes[(i + 1) % props.entityTypes.length]}-0`,
        label: relType
      };
    }
  });

  if (props.entityTypes.length > 2 && props.relationTypes.length > 0) {
    const midIndex = Math.floor(props.entityTypes.length / 2);
    const edgeId = 'edge-cross';
    newEdges[edgeId] = {
      id: edgeId,
      source: `${props.entityTypes[0]}-0`,
      target: `${props.entityTypes[midIndex]}-0`,
      label: props.relationTypes[props.relationTypes.length - 1]
    };
  }

  nodes.value = newNodes;
  edges.value = newEdges;
};

onMounted(generatePreview);
watch([() => props.entityTypes, () => props.relationTypes], generatePreview, { deep: true });

const nodeCount = computed(() => Object.keys(nodes.value).length);
const edgeCount = computed(() => Object.keys(edges.value).length);

</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col h-full">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <div class="w-2.5 h-2.5 rounded-full bg-indigo-500 dark:bg-indigo-400 animate-pulse"></div>
        <span class="text-sm font-medium text-slate-700 dark:text-slate-200">图谱预览</span>
      </div>
      <div class="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
          {{ nodeCount }} 个实体
        </span>
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
          {{ edgeCount }} 条关系
        </span>
      </div>
    </div>

    <div v-if="nodeCount === 0" class="flex-1 flex flex-col items-center justify-center min-h-[400px] text-slate-400 dark:text-slate-500">
      <svg class="w-12 h-12 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
      <span class="text-sm">添加实体类型后预览图谱</span>
    </div>

    <!--  --><div v-else class="relative w-full h-[500px] bg-slate-50/50 dark:bg-slate-950/50 rounded-lg overflow-hidden border border-slate-100 dark:border-slate-800">
      <GraphViewer
        :nodes="nodes"
        :edges="edges"
        :show-toolbar="true"
        :color-map="nodeColors"
      />
    </div>

    <div class="flex items-center justify-center gap-5 mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/50">
      <div v-for="type in entityTypes.slice(0, 5)" :key="type" class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full ring-2 ring-white dark:ring-slate-900 shadow-sm" :style="{ backgroundColor: nodeColors[type] || nodeColors.default }"></div>
        <span class="text-xs text-slate-600 dark:text-slate-300 font-medium">{{ type }}</span>
      </div>
    </div>
  </div>
</template>
