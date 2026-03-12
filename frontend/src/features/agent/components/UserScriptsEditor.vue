<template>
  <div class="h-full flex flex-col">
    <!-- Create Form -->
    <div v-if="showCreate" class="mx-4 mt-4 p-4 border border-border/60 rounded-lg bg-background animate-fade-in-down shadow-sm">
      <div class="flex justify-between items-start mb-4">
        <h4 class="text-sm font-semibold text-foreground">新建剧本</h4>
        <button @click="cancelCreate" class="text-muted-foreground hover:text-foreground transition-colors">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      <div class="space-y-3">
        <div>
          <label class="block text-xs font-medium text-muted-foreground mb-1.5">剧本名称 <span class="text-red-500">*</span></label>
          <input 
            v-model="createForm.title" 
            maxlength="50" 
            class="w-full p-2 bg-muted/5 border border-input/60 rounded-md text-sm focus:bg-background focus:ring-1 focus:ring-primary/20 focus:border-primary outline-none transition-all" 
            placeholder="例如：翻译助手"
          >
        </div>
        <div>
          <label class="block text-xs font-medium text-muted-foreground mb-1.5">提示词内容 (Prompt) <span class="text-red-500">*</span></label>
          <textarea 
            v-model="createForm.content" 
            rows="3" 
            maxlength="500" 
            class="w-full p-2 bg-muted/5 border border-input/60 rounded-md text-sm focus:bg-background focus:ring-1 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none font-mono text-foreground" 
            placeholder="用户点击剧本后自动发送的内容..."
          ></textarea>
        </div>
        <div>
          <label class="block text-xs font-medium text-muted-foreground mb-1.5">描述 (可选)</label>
          <input 
            v-model="createForm.description" 
            maxlength="200" 
            class="w-full p-2 bg-muted/5 border border-input/60 rounded-md text-sm focus:bg-background focus:ring-1 focus:ring-primary/20 focus:border-primary outline-none transition-all" 
            placeholder="简短描述该剧本的用途"
          >
        </div>
        
        <div class="flex justify-end gap-2 pt-2">
            <button @click="cancelCreate" class="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted rounded-md transition-colors">取消</button>
            <button 
                @click="submitCreate" 
                class="px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1.5 shadow-sm" 
                :disabled="createLoading"
            >
                <span v-if="createLoading" class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                <span>保存剧本</span>
            </button>
        </div>
      </div>
    </div>

    <!-- List -->
    <div v-if="loading" class="py-8 flex justify-center">
        <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>
    
    <div v-else-if="items.length === 0 && !showCreate" class="flex-1 flex flex-col items-center justify-center text-center p-8">
        <div class="w-12 h-12 rounded-full bg-muted/30 flex items-center justify-center mb-3">
            <svg class="w-6 h-6 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <span class="text-sm text-muted-foreground font-medium">暂无预设剧本</span>
        <span class="text-xs text-muted-foreground/60 mt-1">点击右上角“新建剧本”开始添加</span>
    </div>

    <div v-else class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
      <div 
        v-for="(it, idx) in items" 
        :key="it.localId" 
        class="group bg-background border border-border/40 rounded-lg transition-all hover:shadow-sm hover:border-primary/30"
        :class="{'ring-1 ring-primary/20 border-primary/50 bg-primary/5': editingId === it.localId}"
        draggable="true" 
        @dragstart="dragStart(idx)" 
        @dragover.prevent 
        @drop="dragDrop(idx)"
      >
        <!-- View Mode -->
        <div v-if="editingId !== it.localId" class="p-4 flex items-start gap-4">
            <div v-if="!readonly" class="mt-1 text-muted-foreground cursor-move hover:text-foreground transition-colors" title="拖拽排序">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"></path></svg>
            </div>
            <div class="flex-1 min-w-0" :class="!readonly ? 'cursor-pointer' : ''" @click="!readonly && startEdit(it)">
                <div class="flex items-center gap-2 mb-1">
                    <span class="font-semibold text-foreground text-sm truncate">{{ it.title }}</span>
                    <span v-if="it.description" class="text-xs text-muted-foreground truncate border-l border-border pl-2 max-w-[200px]">{{ it.description }}</span>
                </div>
                <div class="bg-muted/50 p-4 py-2 rounded-lg text-xs text-muted-foreground font-mono line-clamp-2 border border-border group-hover:bg-primary/5 group-hover:border-primary/20 transition-colors">
                    {{ it.content }}
                </div>
            </div>
            <div v-if="!readonly" class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                <button @click.stop="startEdit(it)" class="p-2 text-muted-foreground hover:text-primary rounded-lg hover:bg-primary/10 transition-colors" title="编辑">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                </button>
                <button @click.stop="confirmDelete(it)" class="p-2 text-muted-foreground hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors" title="删除">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            </div>
        </div>

        <!-- Edit Mode -->
        <div v-else class="p-4 bg-primary/5 space-y-3 rounded-lg border border-primary/10">
            <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-semibold text-primary uppercase tracking-wider">编辑剧本</span>
            </div>
            <div class="space-y-3">
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-[10px] text-muted-foreground font-medium">标题</label>
                        <input v-model="it.editTitle" class="w-full p-2 bg-background border border-input rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
                    </div>
                    <div class="space-y-1">
                        <label class="text-[10px] text-muted-foreground font-medium">描述</label>
                        <input v-model="it.editDescription" class="w-full p-2 bg-background border border-input rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
                    </div>
                </div>
                <div class="space-y-1">
                    <label class="text-[10px] text-muted-foreground font-medium">内容</label>
                    <textarea v-model="it.editContent" rows="3" class="w-full p-2 bg-background border border-input rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none font-mono text-foreground"></textarea>
                </div>
            </div>
            <div class="flex justify-end gap-2 pt-1">
                <button @click="cancelEdit(it)" class="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted rounded-lg transition-colors">取消</button>
                <button @click="saveEdit(it)" class="px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors shadow-sm">保存修改</button>
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
  agentId: { type: String, required: false, default: null },
  readonly: { type: Boolean, default: false }
});

const items = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const createLoading = ref(false);
const editingId = ref(null);

const createForm = ref({ title: '', description: '', content: '' });

const fetchItems = async () => {
  if (!props.agentId) {
      items.value = [];
      return;
  }
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
          editDescription: x.description,
          isTemp: false
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
  
  // Local only mode (when creating new agent)
  if (!props.agentId) {
      const newItem = {
          id: `temp-${Date.now()}`,
          localId: `temp-${Date.now()}-${Math.random()}`,
          title: createForm.value.title.trim(),
          content: createForm.value.content.trim(),
          description: (createForm.value.description || '').trim(),
          sort_order: items.value.length + 1,
          isTemp: true,
          editTitle: createForm.value.title.trim(),
          editContent: createForm.value.content.trim(),
          editDescription: (createForm.value.description || '').trim()
      };
      items.value.push(newItem);
      cancelCreate();
      createLoading.value = false;
      return;
  }

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
        editDescription: obj.description,
        isTemp: false
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
    
    if (it.isTemp) {
        it.title = it.editTitle;
        it.content = it.editContent;
        it.description = it.editDescription;
        editingId.value = null;
        return;
    }
    
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
  
  if (it.isTemp) {
      items.value = items.value.filter(x => x.localId !== it.localId);
      return;
  }
  
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
    
    if (x.isTemp) return; // Skip temp items

    await fetch(`/api/v1/user_scripts/${x.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sort_order: x.sort_order })
    });
  });
  dragIndex = -1;
};

const savePendingScripts = async (realAgentId) => {
    if (!realAgentId) return;
    
    const tempItems = items.value.filter(i => i.isTemp);
    if (tempItems.length === 0) return;

    try {
        await Promise.all(tempItems.map((item, index) => {
            const payload = {
                agent_id: realAgentId,
                title: item.title,
                content: item.content,
                description: item.description,
                sort_order: index + 1 // Use current index
            };
            return fetch('/api/v1/user_scripts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }));
        
        // Refresh items after saving
        // Actually, the parent component might close or refresh, but let's clear temp items or refresh
        // But since we usually close or reload, maybe just return
    } catch (e) {
        console.error("Failed to save pending scripts", e);
        message.error("部分剧本保存失败");
    }
};

defineExpose({
  openCreate: () => { showCreate.value = true; },
  savePendingScripts
});
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