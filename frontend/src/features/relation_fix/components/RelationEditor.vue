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

    <!-- Relation Management -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <div class="flex border-b border-slate-200 mb-4">
        <button 
          @click="activeTab = 'create'"
          class="flex-1 pb-2 text-sm font-medium transition-colors relative"
          :class="activeTab === 'create' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'"
        >
          新建关系
          <div v-if="activeTab === 'create'" class="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600"></div>
        </button>
        <button 
          @click="activeTab = 'delete'"
          class="flex-1 pb-2 text-sm font-medium transition-colors relative"
          :class="activeTab === 'delete' ? 'text-red-600' : 'text-slate-500 hover:text-slate-700'"
        >
          解除关系
          <div v-if="activeTab === 'delete'" class="absolute bottom-0 left-0 w-full h-0.5 bg-red-600"></div>
        </button>
      </div>

      <!-- Create Tab -->
      <div v-if="activeTab === 'create'" class="space-y-3">
        <div class="grid grid-cols-2 gap-2">
          <input v-model="newRel.source" placeholder="源节点 (例如: 北京分公司)" class="px-3 py-2 border rounded-md text-sm" />
          <input v-model="newRel.target" placeholder="目标节点 (例如: 中国联通)" class="px-3 py-2 border rounded-md text-sm" />
        </div>
        <div>
           <label class="block text-xs text-slate-500 mb-1 ml-1">关系类型</label>
           <input v-model="newRel.type" placeholder="例如: 属于、包含、位于" class="w-full px-3 py-2 border rounded-md text-sm" />
        </div>
        <button 
          @click="createRelation"
          class="w-full py-2 bg-slate-800 text-white rounded-md text-sm hover:bg-slate-900"
        >
          创建关系
        </button>
      </div>

      <!-- Delete Tab -->
      <div v-else class="space-y-3">
        <div v-if="!currentRelations || currentRelations.length === 0" class="text-xs text-slate-500 text-center py-4 bg-slate-50 rounded">
          当前无可见关系，请先搜索并加载节点
        </div>
        <div v-else>
          <div class="flex items-center justify-between mb-2 px-1">
             <span class="text-xs text-slate-500">当前列表 ({{ currentRelations.length }})</span>
             <button 
               v-if="selectedRelationsToDelete.length < currentRelations.length"
               @click="selectedRelationsToDelete = [...currentRelations]"
               class="text-xs text-blue-600 hover:underline"
             >全选</button>
             <button 
               v-else
               @click="selectedRelationsToDelete = []"
               class="text-xs text-blue-600 hover:underline"
             >取消全选</button>
          </div>
          <div class="flex flex-col gap-2 max-h-[240px] overflow-y-auto pr-1 custom-scrollbar">
            <div 
              v-for="(rel, idx) in currentRelations" 
              :key="idx" 
              class="flex items-start gap-2 p-2 rounded border transition-colors cursor-pointer"
              :class="selectedRelationsToDelete.includes(rel) ? 'bg-red-50 border-red-100' : 'bg-white border-slate-100 hover:border-slate-300'"
              @click="toggleSelection(rel)"
            >
              <input 
                type="checkbox" 
                :checked="selectedRelationsToDelete.includes(rel)"
                class="mt-1 text-red-600 focus:ring-red-500" 
                @click.stop="toggleSelection(rel)"
              />
              <div class="text-xs flex-1 break-all">
                <div class="flex flex-wrap gap-1 items-center">
                   <span class="font-medium text-slate-700">{{ rel.source }}</span>
                   <span class="text-slate-400">-></span>
                   <span class="font-medium text-slate-700">{{ rel.target }}</span>
                </div>
                <div class="mt-1 text-[10px] text-slate-400" v-if="rel.label">类型: {{ rel.label }}</div>
              </div>
            </div>
          </div>
          <button 
            @click="deleteRelations"
            :disabled="selectedRelationsToDelete.length === 0"
            class="w-full mt-3 py-2 bg-red-50 text-red-600 border border-red-200 rounded-md text-sm hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            解除选中关系 ({{ selectedRelationsToDelete.length }})
          </button>
        </div>
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
  currentRelations?: Array<{ source: string; target: string; label?: string }>;
}>();

const emit = defineEmits<{
  (e: 'search', query: string): void;
  (e: 'detect', mainNode: string, keyword: string): void;
  (e: 'applyFixes', fixes: RelationFix[]): void;
  (e: 'create', source: string, target: string, type: string): void;
  (e: 'delete', relations: Array<{ source: string; target: string }>): void;
  (e: 'backup'): void;
  (e: 'restore'): void;
}>();

const searchQuery = ref('');
const detectMainNode = ref('');
const detectKeyword = ref('');
const selectedFixes = ref<RelationFix[]>([]);
const newRel = ref({ source: '', target: '', type: '包含' });
const activeTab = ref<'create' | 'delete'>('create');
const selectedRelationsToDelete = ref<any[]>([]);

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value);
  }
};

const createRelation = () => {
  if (newRel.value.source && newRel.value.target) {
    emit('create', newRel.value.source, newRel.value.target, newRel.value.type || 'related');
    newRel.value = { source: '', target: '', type: '包含' };
  }
};

const toggleSelection = (rel: any) => {
  const index = selectedRelationsToDelete.value.indexOf(rel);
  if (index === -1) {
    selectedRelationsToDelete.value.push(rel);
  } else {
    selectedRelationsToDelete.value.splice(index, 1);
  }
};

const deleteRelations = () => {
  if (selectedRelationsToDelete.value.length === 0) return;
  
  if (confirm(`确定要解除选中的 ${selectedRelationsToDelete.value.length} 个关系吗？`)) {
    emit('delete', selectedRelationsToDelete.value);
    selectedRelationsToDelete.value = [];
  }
};

watch(() => props.fixes, (newFixes) => {
  selectedFixes.value = [...newFixes]; // Select all by default
});
</script>
