
<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header Banner -->
    <div class="px-0 pt-0 pb-6">
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">图谱导入</h2>
          <p class="text-[#86868B] text-lg font-medium">配置结构化数据到知识图谱的映射与导入任务。</p>
        </div>
        <button 
          @click="openCreateModal"
          class="bg-[#0071e3] text-white px-5 py-2.5 rounded-full hover:bg-[#0077ED] transition-all shadow-sm hover:shadow-md font-medium flex items-center gap-2 active:scale-95 text-sm"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
          新建配置
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto px-0 pb-10 custom-scrollbar">
      
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-8">
        <div v-for="i in 5" :key="i" class="bg-white rounded-[24px] border border-slate-200 overflow-hidden h-[280px]">
            <div class="aspect-video bg-slate-50 animate-pulse"></div>
            <div class="p-5 space-y-3">
                 <a-skeleton active :title="false" :paragraph="{ rows: 1, width: '80%' }" />
                 <a-skeleton active :title="false" :paragraph="{ rows: 2, width: '100%' }" />
            </div>
        </div>
      </div>

      <div v-else-if="configs.length === 0" class="flex flex-col items-center justify-center py-40 text-[#86868B]">
        <div class="w-20 h-20 bg-slate-50 rounded-[24px] flex items-center justify-center mb-6 border border-slate-100">
            <svg class="w-10 h-10 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        </div>
        <span class="text-lg font-semibold text-[#1D1D1F]">暂无配置</span>
        <p class="text-sm mt-2 opacity-80">点击右上角新建配置开始使用</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-8">
        <!-- Card -->
        <div v-for="config in configs" :key="config.id" class="bg-white rounded-[24px] shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-500 flex flex-col group overflow-hidden relative border border-slate-200">
            <!-- Icon/Thumbnail Area -->
            <div class="aspect-video bg-[#F5F5F7] flex items-center justify-center relative overflow-hidden group-hover:bg-[#E8E8ED] transition-colors duration-500 cursor-pointer" @click="openEditModal(config)">
                 <!-- Run Button Overlay -->
                 <div class="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center backdrop-blur-[2px] z-10">
                    <button 
                        @click.stop="runExport(config)"
                        class="bg-white/90 backdrop-blur-md text-[#1D1D1F] px-4 py-2 rounded-full font-medium shadow-lg transform scale-90 group-hover:scale-100 transition-transform duration-300 hover:text-[#0071e3] flex items-center gap-2"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        运行
                    </button>
                 </div>

                 <div class="w-20 h-20 text-[#86868B] group-hover:text-[#0071e3] transition-all duration-500 group-hover:scale-105">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                 </div>
            </div>

            <!-- Content Area -->
            <div class="p-5 flex-1 flex flex-col">
                <div class="mb-2">
                    <h4 class="font-semibold text-[#1D1D1F] text-[15px] line-clamp-1 leading-snug mb-1" :title="config.name">{{ config.name }}</h4>
                    <div class="flex items-center gap-2 text-sm text-[#86868B] font-medium">
                        <span class="font-din tracking-wide">{{ formatDate(config.updated_at) }}</span>
                    </div>
                    <p class="text-sm text-[#86868B] mt-2 line-clamp-2 h-10 leading-relaxed">{{ config.description || '暂无描述' }}</p>
                </div>

                <!-- Actions (Visible on Hover) -->
                <div class="mt-auto pt-4 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-y-2 group-hover:translate-y-0">
                    <div class="flex gap-1">
                        <button @click="openEditModal(config)" class="p-1.5 text-[#86868B] hover:text-[#0071e3] hover:bg-blue-50 rounded-lg transition-colors" title="编辑">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        </button>
                        <a-popconfirm
                            title="确定要删除此配置吗?"
                            ok-text="删除"
                            cancel-text="取消"
                            @confirm="deleteConfig(config.id)"
                        >
                            <button class="p-1.5 text-[#86868B] hover:text-[#FF3B30] hover:bg-red-50 rounded-lg transition-colors" title="删除">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                            </button>
                        </a-popconfirm>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>

    <!-- Edit/Create Modal -->
    <a-modal
        v-model:open="modalVisible"
        :title="isEditing ? '编辑配置' : '新建配置'"
        width="800px"
        @ok="handleSave"
        :confirmLoading="saving"
        :maskClosable="false"
        okText="确认"
        cancelText="取消"
    >
        <div class="py-4 flex flex-col gap-4">
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">配置名称</label>
                <a-input v-model:value="form.name" placeholder="例如：主数据库全量导出" />
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">描述</label>
                <a-textarea v-model:value="form.description" placeholder="可选：描述该配置的用途" :rows="2" />
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">选择数据源</label>
                <a-select
                    v-model:value="selectedDataSourceId"
                    placeholder="选择已连接数据库"
                    class="w-full"
                    @change="handleDataSourceChange"
                    :disabled="dataSources.length === 0"
                >
                    <template #notFoundContent>
                        <div class="text-xs text-slate-400 p-2 text-center">
                            暂无已保存的数据库连接<br/>
                            请先在"数据库"页面添加
                        </div>
                    </template>
                    <a-select-option v-for="ds in dataSources" :key="ds.id" :value="ds.id">
                        {{ ds.name }}
                    </a-select-option>
                </a-select>
            </div>
            <div class="flex-1 flex flex-col">
                <div class="flex justify-between items-center mb-1">
                    <label class="block text-sm font-medium text-slate-700">
                        配置内容 (JSON)
                        <span class="text-xs text-slate-400 font-normal ml-2">包含 database, graph, output, processing 等字段</span>
                    </label>
                    <div class="flex gap-3 items-center">
                        <button 
                            @click="handleAIGenerate"
                            :disabled="!selectedDataSourceId || aiGenerating"
                            class="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-xs font-medium rounded-lg hover:shadow-md hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <svg v-if="aiGenerating" class="animate-spin h-3 w-3" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                            一键 AI 生成配置
                        </button>
                        <button 
                            @click="loadTemplate" 
                            class="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                        >
                            加载默认模板
                        </button>
                    </div>
                </div>
                <div class="relative h-[500px] rounded-lg focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all">
                    <textarea
                        v-model="form.config_json"
                        style="font-family: 'Hack', monospace;"
                        class="w-full h-full p-3 font-mono text-xs leading-relaxed outline-none resize-y bg-slate-50 rounded-lg"
                        placeholder="{ ... }"
                        spellcheck="false"
                        resize="false"
                    ></textarea>
                </div>
                <div v-if="jsonError" class="text-red-500 text-xs mt-1">{{ jsonError }}</div>
            </div>
        </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { message, Modal, Select } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';

const api = axios.create({ baseURL: '/api/v1' });

const loading = ref(false);
const configs = ref([]);
const modalVisible = ref(false);
const saving = ref(false);
const isEditing = ref(false);
const jsonError = ref('');
const aiGenerating = ref(false);
const dbConfig = ref(null); // Store fetched database config

const form = ref({
    id: null,
    name: '',
    description: '',
    config_json: ''
});

const defaultTemplate = {
    "database": {
        "url": "mysql+pymysql://user:password@localhost:3306/dbname",
        "chunk_size": 10000
    },
    "graph": {
        "nodes": [
            {
                "table": "users",
                "label": "用户",
                "id_col": "id",
                "properties": ["username", "email", "created_at"]
            }
        ],
        "edges": [
            {
                "source_table": "orders",
                "source_col": "user_id",
                "target_table": "users",
                "target_col": "id",
                "relation": "下单"
            }
        ]
    },
    "output": {
        "output_dir": "./data/lightrag_store",
        "update_mode": "merge",
        "lightrag_format": true
    },
    "processing": {
        "max_workers": 4,
        "batch_size": 5000
    }
};

const fetchConfigs = async () => {
    loading.value = true;
    try {
        const res = await api.get('/graph_export/');
        configs.value = res.data;
    } catch (e) {
        message.error("获取配置列表失败");
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm');
};

const openCreateModal = () => {
    isEditing.value = false;
    form.value = {
        id: null,
        name: '',
        description: '',
        config_json: JSON.stringify(defaultTemplate, null, 4)
    };
    jsonError.value = '';
    modalVisible.value = true;
};

const openEditModal = (config) => {
    isEditing.value = true;
    form.value = {
        id: config.id,
        name: config.name,
        description: config.description,
        config_json: JSON.stringify(config.config_json, null, 4)
    };
    jsonError.value = '';
    modalVisible.value = true;
};

const loadTemplate = () => {
    form.value.config_json = JSON.stringify(defaultTemplate, null, 4);
    jsonError.value = '';
};

const validateJson = () => {
    try {
        const parsed = JSON.parse(form.value.config_json);
        // 此处可以添加基本的 Schema 验证
        return parsed;
    } catch (e) {
        jsonError.value = "JSON 格式错误: " + e.message;
        return null;
    }
};

const handleSave = async () => {
    if (!form.value.name.trim()) {
        message.warning("请输入配置名称");
        return;
    }

    const configData = validateJson();
    if (!configData) return;

    saving.value = true;
    try {
        const payload = {
            name: form.value.name,
            description: form.value.description,
            config_json: configData
        };

        if (isEditing.value) {
            await api.put(`/graph_export/${form.value.id}`, payload);
            message.success("更新成功");
        } else {
            await api.post('/graph_export/', payload);
            message.success("创建成功");
        }
        modalVisible.value = false;
        fetchConfigs();
    } catch (e) {
        message.error(isEditing.value ? "更新失败" : "创建失败");
        console.error(e);
    } finally {
        saving.value = false;
    }
};

const deleteConfig = async (id) => {
    try {
        await api.delete(`/graph_export/${id}`);
        message.success("删除成功");
        fetchConfigs();
    } catch (e) {
        message.error("删除失败");
    }
};

const runExport = async (config) => {
    Modal.confirm({
        title: '运行导出任务',
        content: `确定要运行配置 "${config.name}" 吗？这将在后台启动一个耗时任务。`,
        okText: '确认运行',
        cancelText: '取消',
        onOk: async () => {
            try {
                const res = await api.post(`/graph_export/${config.id}/run`);
                message.success(res.data.message || "任务已启动");
            } catch (e) {
                message.error("启动失败: " + (e.response?.data?.detail || e.message));
            }
        }
    });
};

const dataSources = ref([]);
const selectedDataSourceId = ref(null);

const fetchDataSources = async () => {
    dataSources.value = [];
    try {
        // 1. Fetch saved data sources
        const resList = await api.get('/data-sources/');
        if (Array.isArray(resList.data)) {
            dataSources.value = resList.data;
        }

        // 2. Fetch current active config
        const resCurrent = await api.get('/data_query/config');
        const current = resCurrent.data;
        
        // Check if current config is valid (has at least host/path and type)
        if (current && (current.host || current.path) && current.type) {
            // Adapt to DataSource structure
            const activeDS = {
                id: 'current',
                name: current.host || current.path || `当前活跃连接 (${current.type})`, // Use Host/Path as name to match DatabaseManagement
                type: current.type,
                host: current.host,
                port: current.port,
                username: current.user, // Map user -> username
                password: current.password, // Keep password for constructing URL
                database: current.database,
                path: current.path // SQLite path
            };
            
            // Check if this config already exists in the saved list to avoid duplicates
            // Matching criteria: type, host, port, database, username
            const exists = dataSources.value.findIndex(d => 
                d.type === activeDS.type &&
                d.host === activeDS.host &&
                d.port === activeDS.port &&
                d.database === activeDS.database &&
                d.username === activeDS.username &&
                d.path === activeDS.path
            );

            if (exists !== -1) {
                // If exists, mark it as active or default select it? 
                // Let's just default select it if no selection
                if (!selectedDataSourceId.value) {
                    selectedDataSourceId.value = dataSources.value[exists].id;
                }
            } else {
                // If not in list, add it to the top
                dataSources.value.unshift(activeDS);
                if (!selectedDataSourceId.value) {
                    selectedDataSourceId.value = 'current';
                }
            }
        }
    } catch (e) {
        console.error("Failed to fetch data sources", e);
    }
};

const handleDataSourceChange = (id) => {
    const ds = dataSources.value.find(d => d.id === id);
    if (!ds) return;
    
    let url = '';
    
    if (ds.type === 'sqlite') {
        const path = ds.path || ds.database || ds.host; // Try to find path
        url = `sqlite:///${path}`;
    } else {
        const typeMap = {
            'mysql': 'mysql+pymysql',
            'postgresql': 'postgresql'
        };
        const driver = typeMap[ds.type] || ds.type;
        const port = ds.port ? `:${ds.port}` : '';
        const db = ds.database ? `/${ds.database}` : '';
        
        // If it's the 'current' config, we have the password, so use it
        // If it's a saved config (id is number), password is not available here, so use ***
        const isCurrent = id === 'current';
        const pass = isCurrent && ds.password ? `:${ds.password}` : (isCurrent ? '' : ':***');
        
        url = `${driver}://${ds.username}${pass}@${ds.host}${port}${db}`;
    }

    try {
        let currentJson = {};
        try {
            currentJson = JSON.parse(form.value.config_json);
        } catch {
            currentJson = { ...defaultTemplate };
        }
        
        if (!currentJson.database) currentJson.database = {};
        
        currentJson.database.url = url;
        
        // Only set data_source_id if it's a real saved config (ID is number)
        if (typeof ds.id === 'number') {
            currentJson.database.data_source_id = ds.id;
        } else {
            // Remove data_source_id if selecting 'current' to avoid backend lookup failure
            delete currentJson.database.data_source_id;
        }
        
        form.value.config_json = JSON.stringify(currentJson, null, 4);
        message.success(`已应用数据源: ${ds.name}`);
        selectedDataSourceId.value = null; // Reset selection
    } catch (e) {
        message.error("应用配置失败: " + e.message);
    }
};

const handleAIGenerate = async () => {
    let currentJson = {};
    try {
        currentJson = JSON.parse(form.value.config_json);
    } catch (e) {
        message.warning("当前配置 JSON 格式错误，无法解析");
        return;
    }
    
    const db = currentJson.database || {};
    // Priority: 1. data_source_id in JSON, 2. selectedDataSourceId (if any), 3. URL in JSON
    let dsId = db.data_source_id || selectedDataSourceId.value;
    
    // Ensure dsId is a number. If it is "current" or any non-number, set to null.
    if (typeof dsId !== 'number') {
        dsId = null;
    }
    
    const dbUrl = db.url;
    
    if (!dsId && !dbUrl) {
        message.warning("请先配置数据库连接或选择数据源");
        return;
    }
    
    aiGenerating.value = true;
    try {
        const payload = {
            data_source_id: dsId,
            database_url: dbUrl,
            existing_config: currentJson
        };
        
        const res = await api.post('/graph_export/ai_generate', payload);
        
        if (res.data) {
            const aiConfig = res.data;
            
            if (aiConfig.graph) currentJson.graph = aiConfig.graph;
            if (aiConfig.output) currentJson.output = { ...currentJson.output, ...aiConfig.output };
            if (aiConfig.processing) currentJson.processing = { ...currentJson.processing, ...aiConfig.processing };
            
            form.value.config_json = JSON.stringify(currentJson, null, 4);
            message.success("AI 已成功生成图谱配置");
        }
    } catch (e) {
        console.error("AI Generate Error:", e);
        let errorMsg = e.message;
        if (e.response) {
            if (e.response.data && e.response.data.detail) {
                const detail = e.response.data.detail;
                errorMsg = typeof detail === 'object' ? JSON.stringify(detail) : detail;
            } else if (e.response.status === 404) {
                errorMsg = "后端接口未找到 (404)，请检查服务是否已重启";
            } else if (e.response.status === 500) {
                errorMsg = "服务器内部错误 (500)";
            }
        }
        message.error("AI 生成失败: " + errorMsg);
    } finally {
        aiGenerating.value = false;
    }
};

onMounted(() => {
    fetchConfigs();
    fetchDataSources();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #CBD5E0;
}
</style>
