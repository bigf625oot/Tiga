<template>
  <div class="h-full w-full flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[600px]">
     <!-- Header with Tabs -->
     <div class="border-b border-slate-200 bg-slate-50 flex items-center justify-between px-4">
        <div class="flex">
            <button 
                @click="activeTab = 'designer'"
                class="px-6 py-3 text-sm font-medium transition-colors border-b-2 outline-none"
                :class="activeTab === 'designer' ? 'border-blue-500 text-blue-600 bg-white' : 'border-transparent text-slate-500 hover:text-slate-700'"
            >
                流程编排 (Designer)
            </button>
            <button 
                @click="activeTab = 'registry'"
                class="px-6 py-3 text-sm font-medium transition-colors border-b-2 outline-none"
                :class="activeTab === 'registry' ? 'border-blue-500 text-blue-600 bg-white' : 'border-transparent text-slate-500 hover:text-slate-700'"
            >
                注册管理 (Registry)
            </button>
        </div>
        
        <div v-if="activeTab === 'designer'" class="flex items-center gap-2">
             <input v-model="n8nUrl" class="px-2 py-1.5 text-xs border border-slate-300 rounded-md w-64 bg-white outline-none focus:border-blue-500" placeholder="N8N URL (e.g. http://localhost:5678)">
             <button @click="refreshIframe" class="p-1.5 text-slate-500 hover:text-blue-600 bg-white border border-slate-200 rounded-md shadow-sm" title="Refresh">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
             </button>
        </div>
        <div v-else>
             <button @click="openRegisterModal" class="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 flex items-center gap-1 shadow-sm shadow-blue-200">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                注册工作流
             </button>
        </div>
     </div>

     <!-- Content -->
     <div class="flex-1 relative overflow-hidden bg-slate-50 flex flex-col">
        <!-- Designer Tab -->
        <div v-show="activeTab === 'designer'" class="flex-1 w-full h-full flex flex-col items-center justify-center relative min-h-0">
             <iframe 
                v-if="iframeUrl"
                :src="iframeUrl" 
                class="w-full h-full border-0 absolute inset-0"
                ref="iframeRef"
                allow="clipboard-read; clipboard-write"
             ></iframe>
             <div v-else class="text-center p-8">
                <p class="text-slate-400 mb-4">请输入有效的 N8N 地址以加载设计器</p>
             </div>
        </div>

        <!-- Registry Tab -->
        <div v-show="activeTab === 'registry'" class="h-full overflow-y-auto p-6">
            <Loading v-if="loading" type="skeleton-card" />
            <div v-else-if="workflows.length === 0" class="text-center py-20 text-slate-400 bg-white rounded-xl border border-dashed border-slate-200">
                <div class="mb-2">暂无注册的工作流</div>
                <div class="text-xs opacity-70">点击右上角“注册工作流”添加供智能体调用的 N8N Webhook</div>
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div v-for="wf in workflows" :key="wf.id" class="bg-white p-5 rounded-xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all group relative">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex items-center gap-2">
                            <div class="w-8 h-8 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center border border-rose-100">
                                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                            </div>
                            <h3 class="font-bold text-slate-800 text-sm">{{ wf.name }}</h3>
                        </div>
                        <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button @click="editWorkflow(wf)" class="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-50 rounded"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg></button>
                            <button @click="deleteWorkflow(wf.id)" class="p-1 text-slate-400 hover:text-red-600 hover:bg-slate-50 rounded"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>
                        </div>
                    </div>
                    <p class="text-xs text-slate-500 mb-4 line-clamp-2 h-8 leading-relaxed">{{ wf.description || '无描述' }}</p>
                    
                    <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 mb-3 group-hover:bg-blue-50/30 transition-colors">
                        <div class="text-[10px] text-slate-400 uppercase font-bold mb-1">Webhook URL</div>
                        <div class="text-xs font-mono text-slate-600 truncate select-all" :title="wf.webhook_url">
                            {{ wf.webhook_url }}
                        </div>
                    </div>
                    
                    <div class="flex items-center justify-between mt-2">
                        <div class="flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full animate-pulse" :class="wf.is_active ? 'bg-green-500' : 'bg-slate-300'"></span>
                            <span class="text-xs font-medium" :class="wf.is_active ? 'text-green-600' : 'text-slate-400'">{{ wf.is_active ? '已启用' : '已禁用' }}</span>
                        </div>
                        <span class="text-[10px] text-slate-300">{{ new Date(wf.updated_at).toLocaleDateString() }}</span>
                    </div>
                </div>
            </div>
        </div>
     </div>

     <!-- Modal -->
     <a-modal v-model:open="showModal" :title="editingId ? '编辑工作流' : '注册工作流'" @ok="handleSubmit">
        <div class="space-y-4 py-4">
            <div>
                <label class="block text-xs font-medium text-slate-500 mb-1">名称 (Name)</label>
                <input v-model="form.name" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors" placeholder="例如: 发送邮件通知">
            </div>
            <div>
                <label class="block text-xs font-medium text-slate-500 mb-1">Webhook URL</label>
                <input v-model="form.webhook_url" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors" placeholder="https://n8n.example.com/webhook/...">
            </div>
            <div>
                <label class="block text-xs font-medium text-slate-500 mb-1">描述 (Description)</label>
                <textarea v-model="form.description" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none transition-colors" rows="3" placeholder="描述该工作流的功能、输入参数格式等，以便智能体准确调用"></textarea>
            </div>
            <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="form.is_active" class="rounded text-blue-600 focus:ring-blue-500">
                <span class="text-sm text-slate-600">启用此工作流</span>
            </label>
        </div>
     </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import Loading from './common/Loading.vue';

const activeTab = ref('designer');
const n8nUrl = ref(localStorage.getItem('n8n_url') || 'http://localhost:5678');
const iframeUrl = ref(n8nUrl.value);
const iframeRef = ref(null);

const workflows = ref([]);
const loading = ref(false);
const showModal = ref(false);
const editingId = ref(null);
const form = ref({
    name: '',
    webhook_url: '',
    description: '',
    is_active: true
});

watch(n8nUrl, (val) => {
    localStorage.setItem('n8n_url', val);
});

const refreshIframe = () => {
    iframeUrl.value = n8nUrl.value;
    if (iframeRef.value) {
        iframeRef.value.src = n8nUrl.value;
    }
};

const fetchWorkflows = async () => {
    loading.value = true;
    try {
        const res = await fetch('/api/v1/workflows/');
        if (res.ok) {
            workflows.value = await res.json();
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const openRegisterModal = () => {
    editingId.value = null;
    form.value = { name: '', webhook_url: '', description: '', is_active: true };
    showModal.value = true;
};

const editWorkflow = (wf) => {
    editingId.value = wf.id;
    form.value = { ...wf };
    showModal.value = true;
};

const handleSubmit = async () => {
    if (!form.value.name || !form.value.webhook_url) {
        message.error("名称和 Webhook URL 必填");
        return;
    }
    
    try {
        const url = editingId.value 
            ? `/api/v1/workflows/${editingId.value}`
            : '/api/v1/workflows/';
        const method = editingId.value ? 'PUT' : 'POST';
        
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form.value)
        });
        
        if (res.ok) {
            message.success(editingId.value ? "更新成功" : "注册成功");
            showModal.value = false;
            fetchWorkflows();
        } else {
            message.error("操作失败");
        }
    } catch (e) {
        message.error("网络错误");
    }
};

const deleteWorkflow = async (id) => {
    if(!confirm("确认删除?")) return;
    try {
        const res = await fetch(`/api/v1/workflows/${id}`, { method: 'DELETE' });
        if (res.ok) {
            message.success("删除成功");
            fetchWorkflows();
        }
    } catch (e) {
        message.error("删除失败");
    }
};

onMounted(() => {
    fetchWorkflows();
});
</script>
