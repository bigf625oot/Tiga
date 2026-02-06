<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <div class="text-sm font-medium text-slate-700">用户剧本</div>
      <button @click="showCreate = true" class="px-3 py-1.5 text-xs rounded bg-blue-600 text-white">添加剧本</button>
    </div>
    <div v-if="showCreate" class="p-3 mb-3 border rounded bg-white space-y-2">
      <a-form ref="formRef" :model="createForm" :rules="createRules" layout="vertical">
        <a-form-item label="剧本名称" name="title">
          <a-input v-model:value="createForm.title" maxlength="50" placeholder="剧本名称（2-50字符）" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-input v-model:value="createForm.description" maxlength="200" placeholder="描述（可选，最多200字符）" />
        </a-form-item>
        <a-form-item label="内容" name="content">
          <a-textarea v-model:value="createForm.content" :rows="4" maxlength="500" placeholder="内容（必填，最多500字符）" />
        </a-form-item>
      </a-form>
      <a-alert v-if="createError" :message="createError" type="error" show-icon />
      <div class="flex items-center justify-end gap-2">
        <a-button type="primary" :loading="createLoading" @click="submitCreate">保存</a-button>
        <a-button @click="cancelCreate">取消</a-button>
      </div>
    </div>
    <div v-if="loading" class="p-3 text-slate-500 text-xs">加载中...</div>
    <div v-else-if="items.length===0" class="p-3 text-slate-400 text-xs">暂无剧本</div>
    <div v-else class="space-y-3">
      <div v-for="(it, idx) in items" :key="it.localId" class="p-3 border rounded bg-white flex flex-col gap-2"
           draggable="true" @dragstart="dragStart(idx)" @dragover.prevent @drop="dragDrop(idx)">
        <div class="flex items-center gap-2">
          <input v-model="it.title" @input="saveAuto(it)" maxlength="50" placeholder="标题" class="flex-1 border rounded px-2 py-1 text-xs" />
          <input v-model.number="it.sort_order" @input="saveAuto(it)" type="number" class="w-24 border rounded px-2 py-1 text-xs" />
          <button @click="confirmDelete(it)" class="px-2 py-1 text-xs rounded bg-red-50 text-red-600">删除</button>
        </div>
        <textarea v-model="it.content" @input="saveAuto(it)" maxlength="500" rows="3" placeholder="内容" class="border rounded px-2 py-1 text-xs"></textarea>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
const props = defineProps({ agentId: { type: String, required: true } });
const items = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const createLoading = ref(false);
const createError = ref('');
const createForm = ref({ title: '', description: '', content: '' });
const createRules = {
  title: [
    { required: true, message: '剧本名称为必填', trigger: 'blur' },
    { type: 'string', min: 2, max: 50, message: '长度需在2-50字符', trigger: 'blur' }
  ],
  description: [
    { type: 'string', max: 200, message: '描述长度最多200字符', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '内容为必填', trigger: 'blur' },
    { type: 'string', min: 1, max: 500, message: '内容长度需在1-500字符', trigger: 'blur' },
    { pattern: /\S+/, message: '内容不可为空白', trigger: 'blur' }
  ]
};
const formRef = ref();
let dragIndex = -1;
const fetchItems = async () => {
  loading.value = true;
  try {
    const res = await fetch(`/api/v1/user_scripts?agent_id=${props.agentId}`);
    if (res.ok) {
      const data = await res.json();
      items.value = data.map(x => ({ ...x, localId: `${x.id}-${Math.random()}` }));
    }
  } finally {
    loading.value = false;
  }
};
onMounted(fetchItems);
const cancelCreate = () => {
  showCreate.value = false;
  createError.value = '';
  createForm.value = { title: '', description: '', content: '' };
};
const submitCreate = async () => {
  createError.value = '';
  try {
    await formRef.value?.validate();
  } catch {
    createError.value = '请完善表单信息';
    return;
  }
  createLoading.value = true;
  try {
    const payload = { agent_id: props.agentId, title: createForm.value.title.trim(), content: createForm.value.content.trim(), sort_order: items.value.length + 1, description: (createForm.value.description || '').trim() };
    const res = await fetch('/api/v1/user_scripts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!res.ok) { createError.value = '提交失败'; return; }
    const obj = await res.json();
    items.value.push({ ...obj, localId: `${obj.id}-${Math.random()}` });
    cancelCreate();
    message.success('创建成功');
  } catch (e) {
    createError.value = '网络错误';
    message.error('创建失败');
  } finally {
    createLoading.value = false;
  }
};
const saveAuto = async (it) => {
  if (!it.id) return;
  await fetch(`/api/v1/user_scripts/${it.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: it.title, content: it.content, sort_order: it.sort_order }) });
};
const confirmDelete = (it) => {
  if (confirm('确定删除该剧本？')) removeItem(it);
};
const removeItem = async (it) => {
  if (!it.id) return;
  const res = await fetch(`/api/v1/user_scripts/${it.id}`, { method: 'DELETE' });
  if (res.ok) items.value = items.value.filter(x => x.id !== it.id);
};
const dragStart = (idx) => { dragIndex = idx; };
const dragDrop = async (idx) => {
  if (dragIndex === -1 || dragIndex === idx) return;
  const moved = items.value.splice(dragIndex, 1)[0];
  items.value.splice(idx, 0, moved);
  items.value.forEach(async (x, i) => {
    x.sort_order = i + 1;
    await saveAuto(x);
  });
  dragIndex = -1;
};
</script>
