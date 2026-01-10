<template>
  <div class="max-w-[1200px] mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-2">
        <h2 class="text-lg font-bold text-slate-800">模型列表</h2>
      </div>
      <button 
        @click="openCreateModal"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-sm shadow-blue-600/20"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        <span>添加模型</span>
      </button>
    </div>

    <!-- List -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <a-table :columns="columns" :data-source="models" :loading="loading" :pagination="false">
            <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'provider'">
                    <a-tag color="blue">{{ record.provider }}</a-tag>
                </template>
                <template v-if="column.key === 'model_type'">
                    <a-tag v-if="record.model_type === 'multimodal'" color="purple">多模态</a-tag>
                    <a-tag v-else-if="record.model_type === 'image'" color="cyan">图像</a-tag>
                    <a-tag v-else-if="record.model_type === 'video'" color="orange">视频</a-tag>
                    <a-tag v-else-if="record.model_type === 'embedding'" color="green">嵌入</a-tag>
                    <a-tag v-else>文本</a-tag>
                </template>
                <template v-if="column.key === 'is_active'">
                     <a-switch v-model:checked="record.is_active" @change="handleStatusChange(record)" />
                </template>
                <template v-if="column.key === 'created_at'">
                    {{ formatDate(record.created_at) }}
                </template>
                <template v-if="column.key === 'action'">
                    <div class="flex gap-2">
                        <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
                        <a-popconfirm
                            title="确定要删除吗?"
                            ok-text="确认"
                            cancel-text="取消"
                            @confirm="deleteModel(record.id)"
                        >
                            <a-button type="link" danger size="small">删除</a-button>
                        </a-popconfirm>
                    </div>
                </template>
            </template>
        </a-table>
    </div>

    <!-- Drawer (Replaces Modal) -->
    <div v-if="modalVisible" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-end">
        <div class="w-[600px] h-full bg-white shadow-2xl flex flex-col animate-slide-in-right">
            <!-- Header -->
            <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-white">
                <h3 class="text-lg font-bold text-slate-800">{{ isEdit ? '编辑模型' : '添加模型' }}</h3>
                <button @click="modalVisible = false" class="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>

            <!-- Body -->
            <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
                <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">模型名称 <span class="text-red-500">*</span></label>
                        <input v-model="formState.name" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors" placeholder="例如: GPT-4o">
                    </div>
                    
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">提供商 <span class="text-red-500">*</span></label>
                        <select v-model="formState.provider" @change="handleProviderChange" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none bg-white">
                            <option value="openai">OpenAI</option>
                            <option value="aliyun">Aliyun (通义千问)</option>
                            <option value="deepseek">DeepSeek</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="google">Google</option>
                            <option value="local">Local (Ollama/vLLM)</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">模型类型 <span class="text-red-500">*</span></label>
                        <select v-model="formState.model_type" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none bg-white">
                            <option value="text">文本 (Text)</option>
                            <option value="embedding">嵌入 (Embedding)</option>
                            <option value="multimodal">多模态 (Multimodal)</option>
                            <option value="image">图像生成 (Image Generation)</option>
                            <option value="video">视频生成 (Video Generation)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">模型ID <span class="text-red-500">*</span></label>
                        <div class="flex gap-2">
                             <select 
                                v-if="!isCustomModel"
                                v-model="formState.model_id" 
                                class="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none bg-white"
                             >
                                <option value="" disabled>选择模型ID</option>
                                <option v-for="opt in currentModelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                             </select>
                             <input 
                                v-else
                                v-model="formState.model_id" 
                                class="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors"
                                placeholder="输入自定义模型ID"
                            >
                            <button @click="isCustomModel = !isCustomModel" class="text-blue-600 text-xs font-medium hover:underline whitespace-nowrap px-2">
                                {{ isCustomModel ? '选择列表' : '手动输入' }}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">API Key</label>
                        <input type="password" v-model="formState.api_key" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors" placeholder="sk-...">
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Base URL</label>
                        <input v-model="formState.base_url" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors" placeholder="可选, 例如: https://api.openai.com/v1">
                    </div>

                    <div class="flex items-center gap-2">
                         <span class="text-xs font-medium text-slate-500">状态</span>
                         <button 
                            @click="formState.is_active = !formState.is_active"
                            class="w-10 h-5 rounded-full transition-colors relative"
                            :class="formState.is_active ? 'bg-blue-600' : 'bg-slate-200'"
                         >
                            <span class="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform" :class="formState.is_active ? 'translate-x-5' : ''"></span>
                         </button>
                         <span class="text-xs text-slate-500">{{ formState.is_active ? '启用' : '禁用' }}</span>
                    </div>

                    <div class="pt-4 border-t border-slate-100">
                        <button @click="handleTestConnection" :disabled="testing" class="w-full py-2 border border-dashed border-slate-300 rounded-lg text-slate-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-colors flex items-center justify-center gap-2">
                             <svg v-if="testing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                             <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                             <span>测试连接</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-slate-200 bg-white flex justify-end gap-3">
                <button @click="modalVisible = false" class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors">取消</button>
                <button @click="handleSubmit" class="px-6 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm" :disabled="submitting">
                    <span v-if="submitting">保存中...</span>
                    <span v-else>保存配置</span>
                </button>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes slide-in-right {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
.animate-slide-in-right {
    animation: slide-in-right 0.3s ease-out forwards;
}
</style>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1'
});

const models = ref([]);
const loading = ref(false);
const modalVisible = ref(false);
const submitting = ref(false);
const testing = ref(false);
const isEdit = ref(false);
const isCustomModel = ref(false);

const formState = reactive({
    id: null,
    name: '',
    provider: 'openai',
    model_id: '',
    model_type: 'text',
    api_key: '',
    base_url: '',
    is_active: true
});

const providerConfig = {
    openai: {
        baseUrl: 'https://api.openai.com/v1',
        models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'dall-e-3', 'text-embedding-3-small', 'text-embedding-3-large']
    },
    aliyun: {
        baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        models: ['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-vl-max', 'qwen-vl-plus', 'wanx-v1']
    },
    deepseek: {
        baseUrl: 'https://api.deepseek.com',
        models: ['deepseek-chat', 'deepseek-reasoner', 'deepseek-embed']
    },
    anthropic: {
        baseUrl: 'https://api.anthropic.com/v1',
        models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
    },
    google: {
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
        models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro-vision']
    },
    local: {
        baseUrl: 'http://localhost:11434/v1',
        models: ['llama3', 'mistral', 'qwen2']
    },
    other: {
        baseUrl: '',
        models: []
    }
};

const currentModelOptions = ref([]);

const handleProviderChange = (val) => {
    const config = providerConfig[val];
    if (config) {
        // Auto fill base_url if empty or if it was matching a previous default
        // For simplicity, let's just update it if the user switches provider.
        // Or maybe we should only update if it's currently empty?
        // User request says "automatically brought out" (auto filled).
        // Let's set it.
        formState.base_url = config.baseUrl;
        
        // Update model options
        currentModelOptions.value = config.models.map(m => ({ value: m, label: m }));
        
        // Check if current model_id is in the new list, if not, maybe switch to custom or clear
        const isInList = config.models.includes(formState.model_id);
        if (!isInList && formState.model_id) {
             // Keep it but maybe switch to custom view if we want to show it?
             // Or just let user handle it.
             // But for UX, if we switch provider, usually we want to reset model_id or pick first.
             // Let's reset to first option or empty.
             formState.model_id = config.models[0] || '';
             isCustomModel.value = false;
        } else if (!formState.model_id && config.models.length > 0) {
             formState.model_id = config.models[0];
             isCustomModel.value = false;
        }
        
        // For 'local' or 'other', default to custom input
        if (val === 'local' || val === 'other') {
            isCustomModel.value = true;
        }
    } else {
        currentModelOptions.value = [];
        isCustomModel.value = true;
    }
};

// Initial load options when editing
watch(() => modalVisible.value, (val) => {
    if (val) {
        const config = providerConfig[formState.provider];
        if (config) {
            currentModelOptions.value = config.models.map(m => ({ value: m, label: m }));
            
            // Determine if current model is custom
            const isInList = config.models.includes(formState.model_id);
            isCustomModel.value = !isInList && !!formState.model_id;
            
            // Special handling for local/other
            if (formState.provider === 'local' || formState.provider === 'other') {
                isCustomModel.value = true;
            }
        } else {
             isCustomModel.value = true;
        }
    }
});

const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '提供商', dataIndex: 'provider', key: 'provider' },
    { title: '类型', dataIndex: 'model_type', key: 'model_type' },
    { title: '模型ID', dataIndex: 'model_id', key: 'model_id' },
    { title: '状态', key: 'is_active', width: 100 },
    { title: '创建时间', key: 'created_at', width: 200 },
    { title: '操作', key: 'action', width: 150 },
];

const fetchModels = async () => {
    loading.value = true;
    try {
        const res = await api.get('/llm/models');
        models.value = res.data;
    } catch (e) {
        message.error('获取模型列表失败');
    } finally {
        loading.value = false;
    }
};

const openCreateModal = () => {
    isEdit.value = false;
    Object.assign(formState, {
        id: null,
        name: '',
        provider: 'openai',
        model_id: '',
        model_type: 'text',
        api_key: '',
        base_url: '',
        is_active: true
    });
    modalVisible.value = true;
};

const openEditModal = (record) => {
    isEdit.value = true;
    Object.assign(formState, {
        id: record.id,
        name: record.name,
        provider: record.provider,
        model_id: record.model_id,
        model_type: record.model_type || 'text',
        api_key: record.api_key,
        base_url: record.base_url,
        is_active: record.is_active
    });
    modalVisible.value = true;
};

const handleSubmit = async () => {
    if (!formState.name || !formState.model_id) {
        message.error('请填写必要信息');
        return;
    }

    submitting.value = true;
    try {
        if (isEdit.value) {
            await api.put(`/llm/models/${formState.id}`, formState);
            message.success('更新成功');
        } else {
            await api.post('/llm/models', formState);
            message.success('创建成功');
        }
        modalVisible.value = false;
        fetchModels();
    } catch (e) {
        message.error('操作失败');
    } finally {
        submitting.value = false;
    }
};

const handleTestConnection = async () => {
    if (!formState.provider || !formState.model_id) {
        message.warning('请先填写提供商和模型ID');
        return;
    }
    
    testing.value = true;
    try {
        const res = await api.post('/llm/models/test', {
            provider: formState.provider,
            model_id: formState.model_id,
            api_key: formState.api_key,
            base_url: formState.base_url
        });
        
        if (res.data.success) {
            message.success(res.data.message);
        } else {
            message.error(res.data.message);
        }
    } catch (e) {
        message.error('测试请求失败: ' + (e.response?.data?.detail || e.message));
    } finally {
        testing.value = false;
    }
};

const deleteModel = async (id) => {
    try {
        await api.delete(`/llm/models/${id}`);
        message.success('删除成功');
        fetchModels();
    } catch (e) {
        message.error('删除失败');
    }
};

const handleStatusChange = async (record) => {
    try {
        await api.put(`/llm/models/${record.id}`, { is_active: record.is_active });
        message.success('状态更新成功');
    } catch (e) {
        record.is_active = !record.is_active; // revert
        message.error('状态更新失败');
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

onMounted(() => {
    fetchModels();
});
</script>
