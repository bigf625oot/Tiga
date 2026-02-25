<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="text-sm text-slate-500">为智能体预设常用对话场景，方便用户快速开始。</div>
      <button 
        @click="showCreate = true" 
        class="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors flex items-center gap-1.5"
        v-if="!showCreate"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
        添加剧本
      </button>
    </div>

    <!-- Create Form -->
    <div v-if="showCreate" class="p-4 border border-slate-200 rounded-xl bg-slate-50/50 animate-fade-in-down shadow-sm">
      <div class="flex justify-between items-start mb-3">
        <h4 class="text-sm font-bold text-slate-700">新建剧本</h4>
        <button @click="cancelCreate" class="text-slate-400 hover:text-slate-600">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      <div class="space-y-3">
        <div>
          <label class="block text-xs font-medium text-slate-500 mb-1.5">剧本名称 <span class="text-red-500">*</span></label>
          <input 
            v-model="createForm.title" 
            maxlength="50" 
            class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" 
            placeholder="例如：翻译助手"
          >
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-500 mb-1.5">提示词内容 (Prompt) <span class="text-red-500">*</span></label>
          <textarea 
            v-model="createForm.content" 
            rows="3" 
            maxlength="500" 
            class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none font-mono text-slate-600" 
            placeholder="用户点击剧本后自动发送的内容..."
          ></textarea>
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-500 mb-1.5">描述 (可选)</label>
          <input 
            v-model="createForm.description" 
            maxlength="200" 
            class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" 
            placeholder="简短描述该剧本的用途"
          >
        </div>
        
        <div class="flex justify-end gap-2 pt-2">
            <button @click="cancelCreate" class="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">取消</button>
            <button 
                @click="submitCreate" 
                class="px-4 py-2 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-1.5 shadow-sm shadow-blue-200" 
                :disabled="createLoading"
            >
                <span v-if="createLoading" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>保存剧本</span>
            </button>
        </div>
      </div>
    </div>

    <!-- List -->
    <div v-if="loading" class="py-8 flex justify-center">
        <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
    
    <div v-else-if="items.length === 0 && !showCreate" class="py-8 flex flex-col items-center justify-center text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
        <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-2">
            <svg class="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <span class="text-sm text-slate-500 font-medium">暂无预设剧本</span>
        <span class="text-xs text-slate-400 mt-1">添加剧本以引导用户更好地使用智能体</span>
    </div>

    <div v-else class="space-y-3">
      <div 
        v-for="(it, idx) in items" 
        :key="it.localId" 
        class="group bg-white border border-slate-200 rounded-xl transition-all hover:shadow-md hover:border-blue-300"
        :class="{'ring-2 ring-blue-100 border-blue-400': editingId === it.localId}"
        draggable="true" 
        @dragstart="dragStart(idx)" 
        @dragover.prevent 
        @drop="dragDrop(idx)"
      >
        <!-- View Mode -->
        <div v-if="editingId !== it.localId" class="p-4 flex items-start gap-4">
            <div class="mt-1 text-slate-300 cursor-move hover:text-slate-500 transition-colors" title="拖拽排序">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"></path></svg>
            </div>
            <div class="flex-1 min-w-0 cursor-pointer" @click="startEdit(it)">
                <div class="flex items-center gap-2 mb-1">
                    <span class="font-bold text-slate-700 text-sm truncate">{{ it.title }}</span>
                    <span v-if="it.description" class="text-xs text-slate-400 truncate border-l border-slate-200 pl-2 max-w-[200px]">{{ it.description }}</span>
                </div>
                <div class="bg-slate-50 px-3 py-2 rounded-lg text-xs text-slate-600 font-mono line-clamp-2 border border-slate-100 group-hover:bg-blue-50/30 group-hover:border-blue-100 transition-colors">
                    {{ it.content }}
                </div>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                <button @click.stop="startEdit(it)" class="p-2 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors" title="编辑">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                </button>
                <button @click.stop="confirmDelete(it)" class="p-2 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors" title="删除">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            </div>
        </div>

        <!-- Edit Mode -->
        <div v-else class="p-4 bg-blue-50/30 space-y-3 rounded-xl">
            <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-bold text-blue-600 uppercase tracking-wider">编辑剧本</span>
            </div>
            <div class="space-y-3">
                <div class="grid grid-cols-2 gap-3">
                    <div class="space-y-1">
                        <label class="text-[10px] text-slate-500 font-medium">标题</label>
                        <input v-model="it.editTitle" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all">
                    </div>
                    <div class="space-y-1">
                        <label class="text-[10px] text-slate-500 font-medium">描述</label>
                        <input v-model="it.editDescription" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all">
                    </div>
                </div>
                <div class="space-y-1">
                    <label class="text-[10px] text-slate-500 font-medium">内容</label>
                    <textarea v-model="it.editContent" rows="3" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none resize-none font-mono text-slate-600"></textarea>
                </div>
            </div>
            <div class="flex justify-end gap-2 pt-1">
                <button @click="cancelEdit(it)" class="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">取消</button>
                <button @click="saveEdit(it)" class="px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm">保存修改</button>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { createVNode } from 'vue';

const props = defineProps({
  agentId: { type: String, required: true }
});

const items = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const createLoading = ref(false);
const editingId = ref(null);

const createForm = ref({ title: '', description: '', content: '' });

const fetchItems = async () => {
  loading.value = true;
  try {
    const res = await fetch(`/api/v1/user_scripts?agent_id=${props.agentId}`);
    if (res.ok) {
      const data = await res.json();
      // Add localId for drag key and edit state
      items.value = data.map(x => ({ 
          ...x, 
          localId: `${x.id}-${Math.random()}`,
          editTitle: x.title,
          editContent: x.content,
          editDescription: x.description
      }));
    }
  } catch (e) {
      console.error(e);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchItems);

const cancelCreate = () => {
  showCreate.value = false;
  createForm.value = { title: '', description: '', content: '' };
};

const submitCreate = async () => {
  if (!createForm.value.title.trim() || !createForm.value.content.trim()) {
      message.warning('标题和内容不能为空');
      return;
  }

  createLoading.value = true;
  try {
    const payload = {
      agent_id: props.agentId,
      title: createForm.value.title.trim(),
      content: createForm.value.content.trim(),
      sort_order: items.value.length + 1,
      description: (createForm.value.description || '').trim()
    };
    
    const res = await fetch('/api/v1/user_scripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error('Failed');
    
    const obj = await res.json();
    items.value.push({ 
        ...obj, 
        localId: `${obj.id}-${Math.random()}`,
        editTitle: obj.title,
        editContent: obj.content,
        editDescription: obj.description
    });
    cancelCreate();
    message.success('添加成功');
  } catch (e) {
    message.error('创建失败');
  } finally {
    createLoading.value = false;
  }
};

const startEdit = (it) => {
    editingId.value = it.localId;
    // Reset edit fields to current values
    it.editTitle = it.title;
    it.editContent = it.content;
    it.editDescription = it.description;
};

const cancelEdit = (it) => {
    editingId.value = null;
};

const saveEdit = async (it) => {
    if (!it.id) return;
    
    try {
        const payload = {
            title: it.editTitle,
            content: it.editContent,
            description: it.editDescription,
            sort_order: it.sort_order
        };
        
        const res = await fetch(`/api/v1/user_scripts/${it.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            // Update local state
            it.title = it.editTitle;
            it.content = it.editContent;
            it.description = it.editDescription;
            editingId.value = null;
            message.success('已更新');
        }
    } catch (e) {
        message.error('更新失败');
    }
};

const confirmDelete = (it) => {
  Modal.confirm({
      title: '确定要删除该剧本吗？',
      icon: createVNode(ExclamationCircleOutlined),
      content: '删除后将无法恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: () => removeItem(it)
  });
};

const removeItem = async (it) => {
  if (!it.id) return;
  try {
      const res = await fetch(`/api/v1/user_scripts/${it.id}`, { method: 'DELETE' });
      if (res.ok) {
          items.value = items.value.filter(x => x.id !== it.id);
          message.success('已删除');
      }
  } catch(e) {
      message.error('删除失败');
  }
};

let dragIndex = -1;
const dragStart = (idx) => { dragIndex = idx; };
const dragDrop = async (idx) => {
  if (dragIndex === -1 || dragIndex === idx) return;
  const moved = items.value.splice(dragIndex, 1)[0];
  items.value.splice(idx, 0, moved);
  
  // Update sort order for all
  items.value.forEach(async (x, i) => {
    x.sort_order = i + 1;
    await fetch(`/api/v1/user_scripts/${x.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sort_order: x.sort_order })
    });
  });
  dragIndex = -1;
};
</script>

<style scoped>
.animate-fade-in-down {
    animation: fadeInDown 0.3s ease-out;
}
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>