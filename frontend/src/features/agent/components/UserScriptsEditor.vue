<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <div class="text-xs text-slate-500">为智能体预设常用对话场景，方便用户快速开始。</div>
      <button @click="showCreate = true" class="px-2 py-1 text-xs font-medium rounded bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors flex items-center gap-1">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
        添加剧本
      </button>
    </div>

    <!-- Create Form -->
    <div v-if="showCreate" class="p-3 mb-3 border border-slate-200 rounded-lg bg-slate-50 animate-fade-in-down">
      <div class="space-y-3">
        <div>
          <label class="block text-xs font-medium text-slate-500 mb-1">剧本名称</label>
          <input v-model="createForm.title" maxlength="50" class="w-full px-2 py-1.5 bg-white border border-slate-200 rounded text-sm focus:border-blue-500 outline-none" placeholder="e.g. 翻译助手">
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-500 mb-1">提示词内容 (Prompt)</label>
          <textarea v-model="createForm.content" rows="3" maxlength="500" class="w-full px-2 py-1.5 bg-white border border-slate-200 rounded text-sm focus:border-blue-500 outline-none resize-none" placeholder="用户点击剧本后自动发送的内容..."></textarea>
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-500 mb-1">描述 (可选)</label>
          <input v-model="createForm.description" maxlength="200" class="w-full px-2 py-1.5 bg-white border border-slate-200 rounded text-sm focus:border-blue-500 outline-none" placeholder="简短描述该剧本的用途">
        </div>
        
        <div class="flex justify-end gap-2 pt-1">
            <button @click="cancelCreate" class="px-3 py-1 text-xs text-slate-500 hover:bg-slate-200 rounded transition-colors">取消</button>
            <button @click="submitCreate" class="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center gap-1" :disabled="createLoading">
                <span v-if="createLoading" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                保存
            </button>
        </div>
      </div>
    </div>

    <!-- List -->
    <div v-if="loading" class="py-4 flex justify-center"><div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>
    <div v-else-if="items.length === 0 && !showCreate" class="py-6 text-center text-slate-400 text-sm border border-dashed border-slate-200 rounded-lg bg-slate-50">
        暂无预设剧本
    </div>
    <div v-else class="space-y-2">
      <div 
        v-for="(it, idx) in items" 
        :key="it.localId" 
        class="group bg-white border border-slate-200 rounded-lg transition-all hover:shadow-sm hover:border-blue-200"
        draggable="true" 
        @dragstart="dragStart(idx)" 
        @dragover.prevent 
        @drop="dragDrop(idx)"
      >
        <!-- View Mode -->
        <div v-if="editingId !== it.localId" class="p-3 flex items-start gap-3">
            <div class="mt-1 text-slate-300 cursor-move hover:text-slate-500">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </div>
            <div class="flex-1 min-w-0" @click="startEdit(it)">
                <div class="flex items-center gap-2 mb-0.5">
                    <span class="font-medium text-slate-700 text-sm truncate">{{ it.title }}</span>
                    <span v-if="it.description" class="text-xs text-slate-400 truncate max-w-[150px]">{{ it.description }}</span>
                </div>
                <p class="text-xs text-slate-500 line-clamp-1 bg-slate-50 px-1.5 py-0.5 rounded w-fit max-w-full font-mono">{{ it.content }}</p>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button @click="startEdit(it)" class="p-1 text-slate-400 hover:text-blue-500 rounded hover:bg-blue-50">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                </button>
                <button @click="confirmDelete(it)" class="p-1 text-slate-400 hover:text-red-500 rounded hover:bg-red-50">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            </div>
        </div>

        <!-- Edit Mode -->
        <div v-else class="p-3 bg-blue-50/30 space-y-3">
            <div class="flex gap-3">
                <div class="flex-1 space-y-2">
                    <input v-model="it.editTitle" class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-sm focus:border-blue-500 outline-none" placeholder="标题">
                    <textarea v-model="it.editContent" rows="2" class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-sm focus:border-blue-500 outline-none resize-none" placeholder="内容"></textarea>
                    <input v-model="it.editDescription" class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-xs focus:border-blue-500 outline-none" placeholder="描述 (可选)">
                </div>
            </div>
            <div class="flex justify-end gap-2">
                <button @click="cancelEdit(it)" class="px-2 py-1 text-xs text-slate-500 hover:bg-slate-200 rounded">取消</button>
                <button @click="saveEdit(it)" class="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">保存修改</button>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';

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
  if (confirm('确定删除该剧本？')) {
      removeItem(it);
  }
};

const removeItem = async (it) => {
  if (!it.id) return;
  const res = await fetch(`/api/v1/user_scripts/${it.id}`, { method: 'DELETE' });
  if (res.ok) {
      items.value = items.value.filter(x => x.id !== it.id);
      message.success('已删除');
  }
};

let dragIndex = -1;
const dragStart = (idx) => { dragIndex = idx; };
const dragDrop = async (idx) => {
  if (dragIndex === -1 || dragIndex === idx) return;
  const moved = items.value.splice(dragIndex, 1)[0];
  items.value.splice(idx, 0, moved);
  
  // Update sort order for all
  // In a real app, you might want to debounce this or save strictly on drop
  items.value.forEach(async (x, i) => {
    x.sort_order = i + 1;
    // Optimistic update, maybe don't await loop
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