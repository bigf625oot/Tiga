<template>
  <div class="h-full flex flex-col bg-white font-sans">
    <!-- Header & Actions -->
    <div class="flex flex-col gap-6 px-8 pt-8 pb-4">
        <div class="flex justify-between items-center">
            <div class="flex items-center gap-4">
                <h1 class="text-2xl font-bold text-slate-900 tracking-tight">指标管理</h1>
                <span class="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs font-medium border border-slate-200">{{ total }} 个指标</span>
            </div>
            <div class="flex gap-3">
                 <div class="relative group">
                    <input 
                        v-model="searchQuery"
                        @keyup.enter="fetchIndicators"
                        type="text" 
                        placeholder="搜索指标名称或分组..." 
                        class="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm w-72 transition-all focus:w-80 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 shadow-sm placeholder:text-slate-400"
                    >
                    <svg class="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 group-focus-within:text-blue-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                 </div>
                 <button @click="openImportDialog" class="px-4 py-2.5 bg-white text-slate-700 border border-slate-200 rounded-xl font-medium hover:bg-slate-50 transition-all flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                    批量导入
                 </button>
                 <button @click="openBatchPromptDialog" class="px-4 py-2.5 bg-amber-50 text-amber-600 border border-amber-100 rounded-xl font-medium hover:bg-amber-100 transition-all flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    生成 Prompt
                 </button>
                 <button @click="openDialog('create')" class="px-4 py-2.5 bg-blue-600 text-white rounded-xl font-medium shadow-lg shadow-blue-600/20 hover:bg-blue-700 hover:-translate-y-0.5 transition-all flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    添加指标
                 </button>
            </div>
        </div>
        
        <!-- Quick Filters -->
        <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            <button 
                @click="filterGroup = ''"
                :class="!filterGroup ? 'bg-slate-900 text-white shadow-md shadow-slate-900/10' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'"
                class="px-5 py-2 rounded-full text-sm font-medium transition-all"
            >全部</button>
            <button 
                v-for="group in uniqueGroups" 
                :key="group"
                @click="filterGroup = group"
                :class="filterGroup === group ? 'bg-slate-900 text-white shadow-md shadow-slate-900/10' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'"
                class="px-5 py-2 rounded-full text-sm font-medium transition-all"
            >{{ group }}</button>
        </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-y-auto px-8 pb-32">
        <!-- Loading State -->
        <div v-if="loading" class="flex flex-col items-center justify-center h-64 text-slate-400">
            <svg class="animate-spin h-8 w-8 mb-3 text-blue-600" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span class="text-sm font-medium">加载数据中...</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredIndicators.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-slate-300 animate-[fadeIn_0.5s_ease-out]">
            <div class="relative w-48 h-48 mb-6 opacity-80">
                <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
                    <rect x="40" y="60" width="120" height="80" rx="8" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="2"/>
                    <path d="M40 90H160" stroke="#CBD5E1" stroke-width="2"/>
                    <rect x="55" y="75" width="40" height="6" rx="3" fill="#E2E8F0"/>
                    <rect x="55" y="105" width="90" height="6" rx="3" fill="#E2E8F0"/>
                    <rect x="55" y="120" width="60" height="6" rx="3" fill="#E2E8F0"/>
                    <circle cx="150" cy="50" r="15" fill="#3B82F6" fill-opacity="0.1"/>
                    <path d="M150 42V58M142 50H158" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <h3 class="text-lg font-bold text-slate-700 mb-2">暂无相关指标</h3>
            <p class="text-slate-400 text-sm mb-6">点击上方按钮添加您的第一个业务指标</p>
            <button @click="openDialog('create')" class="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20">
                立即添加
            </button>
        </div>

        <!-- Card Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 animate-[fadeIn_0.3s_ease-out]">
            <div v-for="item in filteredIndicators" :key="item.id" 
                class="group bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_12px_24px_rgba(0,0,0,0.08)] hover:border-blue-500/20 hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between h-[220px] relative"
            >
                <!-- Card Header -->
                <div>
                    <div class="flex justify-between items-start mb-3">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 truncate max-w-[120px]">
                            {{ item.group }}
                        </span>
                        
                        <!-- Actions Dropdown -->
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                             <a-dropdown placement="bottomRight" :trigger="['click']">
                                <button class="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>
                                </button>
                                <template #overlay>
                                    <a-menu class="!rounded-xl !p-1 !min-w-[120px] !shadow-xl !border !border-slate-100">
                                        <a-menu-item key="edit" @click="openDialog('edit', item)" class="!rounded-lg">
                                            <div class="flex items-center gap-2 text-slate-700">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                                                编辑
                                            </div>
                                        </a-menu-item>
                                        <a-menu-item key="extract" @click="handleExtract(item)" class="!rounded-lg">
                                            <div class="flex items-center gap-2 text-blue-600">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                                                提取
                                            </div>
                                        </a-menu-item>
                                        <a-menu-divider class="!my-1" />
                                        <a-menu-item key="delete" @click="handleDelete(item)" class="!rounded-lg !text-red-500">
                                            <div class="flex items-center gap-2">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                                删除
                                            </div>
                                        </a-menu-item>
                                    </a-menu>
                                </template>
                            </a-dropdown>
                        </div>
                    </div>
                    
                    <h3 class="text-lg font-bold text-slate-800 mb-1 truncate" :title="item.name">{{ item.name }}</h3>
                    <div class="text-xs text-slate-400 mb-3 truncate" v-if="item.alias">别名: {{ item.alias }}</div>
                    <div class="text-xs text-slate-400 mb-3 h-4" v-else></div>
                    
                    <p class="text-sm text-slate-500 line-clamp-3 leading-relaxed h-[60px]">
                        {{ item.description || '暂无描述信息...' }}
                    </p>
                </div>

                <!-- Card Footer -->
                <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-50">
                    <span class="text-xs text-slate-400">{{ formatDate(item.created_at) }}</span>
                    <button 
                        @click="handleExtract(item)"
                        class="text-xs font-medium text-blue-600 bg-blue-50 px-2.5 py-1.5 rounded-lg hover:bg-blue-100 transition-colors flex items-center gap-1"
                    >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                        去提取
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Create/Edit Dialog -->
    <a-modal
        v-model:open="dialogVisible"
        :title="dialogType === 'create' ? '添加指标' : '编辑指标'"
        :footer="null"
        width="800px"
        destroyOnClose
        centered
    >
        <div class="py-4">
            <IndicatorForm 
                :initialData="selectedIndicator" 
                :isEdit="dialogType === 'edit'"
                @submit="handleFormSubmit"
                @cancel="dialogVisible = false"
            />
        </div>
    </a-modal>

    <!-- Import Dialog -->
    <a-modal 
        v-model:open="importDialogVisible" 
        title="批量导入指标" 
        :footer="null"
        width="600px"
        destroyOnClose
        centered
    >
        <div class="py-4 space-y-4">
            <div class="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-700 flex gap-2">
                <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <div class="leading-relaxed">
                    请上传 CSV 或 Excel 文件。必填表头：指标分组 (Group), 指标名称 (Name), 指标描述 (Description)。
                </div>
            </div>
            
            <div class="border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-blue-50/30 transition-all group" @click="triggerFileInput">
                <input type="file" ref="fileInput" class="hidden" accept=".csv,.xlsx,.xls" @change="handleImportFile">
                <div class="w-12 h-12 rounded-full bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center mb-3 transition-colors">
                    <svg class="w-6 h-6 text-slate-400 group-hover:text-blue-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                </div>
                <p class="text-sm font-medium text-slate-700">点击上传或拖拽文件到此处</p>
                <p class="text-xs text-slate-400 mt-1">支持 .csv, .xlsx, .xls 格式</p>
            </div>

            <div v-if="importing || importResult" class="mt-4">
                <div v-if="importing" class="w-full bg-slate-100 rounded-full h-2 mb-2 overflow-hidden">
                    <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" :style="{ width: importProgress + '%' }"></div>
                </div>
                <div v-if="importResult" class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <div class="flex gap-4 mb-2 text-sm">
                        <span class="text-green-600 font-bold">成功: {{ importResult.success }}</span>
                        <span class="text-red-600 font-bold">失败: {{ importResult.failed }}</span>
                    </div>
                    <div v-if="importResult.errors.length > 0" class="max-h-32 overflow-y-auto text-xs text-red-500 space-y-1 custom-scrollbar pr-2">
                        <div v-for="(err, idx) in importResult.errors" :key="idx">{{ err }}</div>
                    </div>
                </div>
            </div>
        </div>
    </a-modal>

    <!-- Batch Prompt Dialog -->
    <a-modal 
        v-model:open="batchPromptDialogVisible" 
        title="批量生成 Prompt" 
        :footer="null"
        width="700px"
        destroyOnClose
        centered
    >
        <div class="py-4 space-y-4">
            <div class="bg-amber-50 border border-amber-100 rounded-lg p-3 text-sm text-amber-700 leading-relaxed">
                该功能将根据当前列表中的所有指标（受搜索条件影响），自动生成一份完整的指标提取 Prompt 模板。
            </div>

            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 h-[400px] overflow-y-auto font-mono text-sm whitespace-pre-wrap select-text custom-scrollbar">
                <div v-if="generatingPrompt" class="flex flex-col items-center justify-center h-full text-slate-400">
                    <svg class="animate-spin h-8 w-8 mb-2 text-amber-500" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span>正在生成 Prompt...</span>
                </div>
                <div v-else class="text-slate-700">{{ generatedPrompt || '点击下方按钮开始生成...' }}</div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
                <button @click="generateBatchPrompt" :disabled="generatingPrompt" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50">
                    {{ generatingPrompt ? '生成中...' : '开始生成' }}
                </button>
                <button v-if="generatedPrompt" @click="copyPrompt" class="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
                    复制内容
                </button>
            </div>
        </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineAsyncComponent } from 'vue';
import axios from 'axios';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';

const IndicatorForm = defineAsyncComponent(() => import('./IndicatorForm.vue'));

const emit = defineEmits(['navigate-to-extraction']);

const api = axios.create({ baseURL: '/api/v1' });

// State
const indicators = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const filterGroup = ref('');
const total = ref(0);

// Import State
const importDialogVisible = ref(false);
const importing = ref(false);
const importProgress = ref(0);
const importResult = ref(null);
const fileInput = ref(null);

// Batch Prompt State
const batchPromptDialogVisible = ref(false);
const generatingPrompt = ref(false);
const generatedPrompt = ref('');

// Computed
const uniqueGroups = computed(() => {
    const groups = new Set(indicators.value.map(i => i.group).filter(Boolean));
    return Array.from(groups);
});

const filteredIndicators = computed(() => {
    return indicators.value.filter(item => {
        const matchesSearch = !searchQuery.value || 
            item.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
            (item.group && item.group.toLowerCase().includes(searchQuery.value.toLowerCase()));
        
        const matchesGroup = !filterGroup.value || item.group === filterGroup.value;
        
        return matchesSearch && matchesGroup;
    });
});

// Dialog State
const dialogVisible = ref(false);
const dialogType = ref('create');
const submitting = ref(false);
const form = reactive({
  id: null,
  group: '',
  name: '',
  alias: '',
  description: ''
});

const selectedIndicator = ref(null);

// Methods
const fetchIndicators = async () => {
  loading.value = true;
  try {
    const res = await api.get('/indicators/', { params: { limit: 1000 } });
    indicators.value = res.data;
    total.value = res.data.length;
  } catch (e) {
    message.error('获取指标列表失败');
  } finally {
    loading.value = false;
  }
};

const formatDate = (date) => dayjs(date).format('YYYY-MM-DD');

const openDialog = (type, row = null) => {
  dialogType.value = type;
  if (type === 'edit' && row) {
    selectedIndicator.value = { ...row };
  } else {
    selectedIndicator.value = null;
  }
  dialogVisible.value = true;
};

const handleFormSubmit = async (payload) => {
  submitting.value = true;
  try {
    if (dialogType.value === 'create') {
      await api.post('/indicators/', payload);
      message.success('添加成功');
      // Reset filters to ensure new item is visible
      searchQuery.value = '';
      filterGroup.value = '';
    } else {
      await api.patch(`/indicators/${selectedIndicator.value.id}`, payload);
      message.success('更新成功');
    }
    dialogVisible.value = false;
    fetchIndicators();
  } catch (e) {
    console.error(e);
    message.error(e.response?.data?.detail || '操作失败');
  } finally {
    submitting.value = false;
  }
};

const handleDelete = (row) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除指标 "${row.name}" 吗？此操作无法撤销。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await api.delete(`/indicators/${row.id}`);
        message.success('删除成功');
        fetchIndicators();
      } catch (e) {
        message.error('删除失败');
      }
    }
  });
};

const handleExtract = (row) => {
  emit('navigate-to-extraction', row);
};

// Import Logic
const openImportDialog = () => {
    importDialogVisible.value = true;
    importResult.value = null;
    importProgress.value = 0;
};

const triggerFileInput = () => {
    fileInput.value.click();
};

const handleImportFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    importing.value = true;
    importProgress.value = 20;
    importResult.value = null;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Mock progress
        const timer = setInterval(() => {
            if (importProgress.value < 90) importProgress.value += 10;
        }, 200);
        
        const res = await api.post('/indicators/import', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        clearInterval(timer);
        importProgress.value = 100;
        importResult.value = res.data;
        
        if (res.data.failed === 0) {
            message.success(`成功导入 ${res.data.success} 条数据`);
            setTimeout(() => {
                importDialogVisible.value = false;
                fetchIndicators();
            }, 1500);
        } else {
            message.warning(`导入完成，但有 ${res.data.failed} 条失败`);
            fetchIndicators();
        }
    } catch (e) {
        message.error(e.response?.data?.detail || '导入失败');
        importProgress.value = 0;
    } finally {
        importing.value = false;
        e.target.value = ''; // Reset input
    }
};

// Batch Prompt Logic
const openBatchPromptDialog = () => {
    batchPromptDialogVisible.value = true;
    generatedPrompt.value = '';
};

const generateBatchPrompt = async () => {
    generatingPrompt.value = true;
    try {
        if (filteredIndicators.value.length === 0) {
            generatedPrompt.value = "当前没有指标数据，无法生成 Prompt。";
            return;
        }

        const batchRes = await api.post('/metrics/batch_generate_prompts', {
            indicators: filteredIndicators.value,
            output_format: "JSON",
            language: "CN",
            extraction_mode: "Multi"
        });
        
        const results = batchRes.data;
        let finalOutput = "";
        
        results.forEach((item, index) => {
            finalOutput += `### ${index + 1}. ${item.indicator_name}\n`;
            finalOutput += `\`\`\`\n${item.prompt}\n\`\`\`\n\n`;
            finalOutput += `--------------------------------------------------\n\n`;
        });

        generatedPrompt.value = finalOutput;
    } catch (e) {
        message.error('生成失败');
        console.error(e);
    } finally {
        generatingPrompt.value = false;
    }
};

const copyPrompt = async () => {
    if (!generatedPrompt.value) return;
    try {
        await navigator.clipboard.writeText(generatedPrompt.value);
        message.success('已复制到剪贴板');
    } catch (err) {
        message.error('复制失败');
    }
};

onMounted(() => {
  fetchIndicators();
});
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>