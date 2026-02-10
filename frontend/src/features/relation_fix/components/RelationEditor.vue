<template>
  <div class="h-full flex flex-col gap-4 p-4 overflow-y-auto">
    <!-- Search Node -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <h3 class="font-medium text-slate-800 mb-2">节点搜索</h3>
      <div class="flex gap-2">
        <div class="relative flex-1">
          <input 
            v-model="searchQuery" 
            @keyup.enter="handleSearch"
            type="text" 
            placeholder="输入节点名称..." 
            class="w-full px-3 py-2 pr-8 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button 
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <button 
          @click="handleSearch"
          class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
        >
          搜索
        </button>
      </div>
    </div>

    <!-- Relation Detection -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <h3 class="font-medium text-slate-800 mb-2">关系修复检测</h3>
      <div class="space-y-3">
        <div>
          <label class="block text-xs text-slate-500 mb-1">主节点</label>
          <input v-model="detectMainNode" type="text" class="w-full px-3 py-2 border rounded-md text-sm" placeholder="例如: 中国联通" />
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">包含关键词</label>
          <input v-model="detectKeyword" type="text" class="w-full px-3 py-2 border rounded-md text-sm" placeholder="例如: 联通" />
        </div>
        <button 
          @click="$emit('detect', detectMainNode, detectKeyword)"
          class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
        >
          检测缺失关系
        </button>
      </div>
    </div>

    <!-- Detection Results -->
    <div v-if="fixes.length > 0" class="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex-1 min-h-[200px] flex flex-col">
      <div class="flex justify-between items-center mb-2">
        <h3 class="font-medium text-slate-800">检测结果 ({{ fixes.length }})</h3>
        <button @click="$emit('applyFixes', selectedFixes)" class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200">
          修复选中 ({{ selectedFixes.length }})
        </button>
      </div>
      <div class="flex-1 overflow-y-auto space-y-2 text-sm">
        <div v-for="(fix, idx) in fixes" :key="idx" class="flex items-start gap-2 p-2 bg-slate-50 rounded border border-slate-100">
          <input type="checkbox" :value="fix" v-model="selectedFixes" class="mt-1" />
          <div>
            <div class="font-medium">{{ fix.source }} <span class="text-slate-400">-></span> {{ fix.target }}</div>
            <div class="text-xs text-slate-500">{{ fix.reason }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Manual Relation -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <h3 class="font-medium text-slate-800 mb-2">新建关系</h3>
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-2">
          <input v-model="newRel.source" placeholder="源节点" class="px-3 py-2 border rounded-md text-sm" />
          <input v-model="newRel.target" placeholder="目标节点" class="px-3 py-2 border rounded-md text-sm" />
        </div>
        <input v-model="newRel.type" placeholder="关系类型 (如: related)" class="w-full px-3 py-2 border rounded-md text-sm" />
        <button 
          @click="createRelation"
          class="w-full py-2 bg-slate-800 text-white rounded-md text-sm hover:bg-slate-900"
        >
          创建关系
        </button>
      </div>
    </div>

    <!-- System Actions -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <h3 class="font-medium text-slate-800 mb-2">系统操作</h3>
      <div class="flex gap-2">
        <button @click="$emit('backup')" class="flex-1 py-2 border border-slate-300 rounded-md text-sm hover:bg-slate-50">备份图谱</button>
        <button @click="$emit('restore')" class="flex-1 py-2 border border-red-200 text-red-600 rounded-md text-sm hover:bg-red-50">回滚操作</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { RelationFix } from '../api';

const props = defineProps<{
  fixes: RelationFix[];
}>();

const emit = defineEmits<{
  (e: 'search', query: string): void;
  (e: 'detect', mainNode: string, keyword: string): void;
  (e: 'applyFixes', fixes: RelationFix[]): void;
  (e: 'create', source: string, target: string, type: string): void;
  (e: 'backup'): void;
  (e: 'restore'): void;
}>();

const searchQuery = ref('');
const detectMainNode = ref('');
const detectKeyword = ref('');
const selectedFixes = ref<RelationFix[]>([]);
const newRel = ref({ source: '', target: '', type: 'related' });

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value);
  }
};

const createRelation = () => {
  if (newRel.value.source && newRel.value.target) {
    emit('create', newRel.value.source, newRel.value.target, newRel.value.type);
    newRel.value = { source: '', target: '', type: 'related' };
  }
};

watch(() => props.fixes, (newFixes) => {
  selectedFixes.value = [...newFixes]; // Select all by default
});
</script>
