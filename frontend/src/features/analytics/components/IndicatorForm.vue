<template>
  <div class="space-y-6">
    <!-- Basic Info -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">指标分组 <span class="text-red-500">*</span></label>
        <input 
          v-model="form.group" 
          type="text" 
          placeholder="例如：财务指标" 
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">指标名称 <span class="text-red-500">*</span></label>
        <input 
          v-model="form.name" 
          type="text" 
          placeholder="例如：营业收入" 
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">指标别名 <span class="text-red-500">*</span></label>
        <input 
          v-model="form.alias" 
          type="text" 
          placeholder="例如：Revenue, 营收" 
          maxlength="50"
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">指标编码 <span class="text-red-500">*</span></label>
        <input 
          v-model="form.code" 
          type="text" 
          placeholder="例如：REV_001" 
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">数据类型 <span class="text-red-500">*</span></label>
        <a-select 
          v-model:value="form.type" 
          class="w-full text-xs-select"
          placeholder="请选择数据类型"
          :dropdownStyle="{ fontSize: '12px' }"
        >
          <a-select-option value="number">数值型 (Number)</a-select-option>
          <a-select-option value="currency">金额型 (Currency)</a-select-option>
          <a-select-option value="percentage">百分比 (Percentage)</a-select-option>
          <a-select-option value="text">文本型 (Text)</a-select-option>
          <a-select-option value="boolean">布尔型 (Boolean)</a-select-option>
        </a-select>
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">单位</label>
        <input 
          v-model="form.unit" 
          type="text" 
          placeholder="例如：万元, %, 个" 
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
      </div>
    </div>

    <!-- Advanced Info -->
    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">计算公式</label>
      <input 
        v-model="form.formula" 
        type="text" 
        placeholder="例如：营业收入 - 营业成本" 
        class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
      >
    </div>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">阈值范围</label>
      <div class="flex items-center gap-2">
        <input 
          v-model="form.threshold_min" 
          type="text" 
          placeholder="最小值" 
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
        <span class="text-slate-400">-</span>
        <input 
          v-model="form.threshold_max" 
          type="text" 
          placeholder="最大值" 
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        >
      </div>
    </div>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">业务含义描述 <span class="text-red-500">*</span></label>
      <textarea 
        v-model="form.description" 
        rows="3" 
        placeholder="详细描述该指标的定义、业务场景..." 
        class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
      ></textarea>
    </div>

    <!-- Prompt Generation -->
    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
      <div class="flex justify-between items-center mb-3">
        <label class="text-sm font-bold text-slate-800 flex items-center gap-2">
          <svg class="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          智能 Prompt 模板
        </label>
        <button 
          @click="generatePrompt" 
          :disabled="generatingPrompt || !form.name"
          class="text-xs px-3 py-1.5 bg-white border border-slate-200 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          <svg v-if="generatingPrompt" class="animate-spin w-3 h-3" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          {{ generatingPrompt ? '生成中...' : '自动生成' }}
        </button>
      </div>
      <textarea 
        v-model="form.prompt_template" 
        rows="6" 
        placeholder="点击“自动生成”或手动输入 Prompt 模板..." 
        class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
      ></textarea>
      <div class="flex justify-end mt-2">
         <button 
          v-if="form.prompt_template"
          @click="previewPrompt"
          class="text-xs text-slate-500 hover:text-blue-600 flex items-center gap-1"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
          预览效果
        </button>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
      <button 
        @click="$emit('cancel')" 
        class="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
      >
        取消
      </button>
      <button 
        @click="handleSubmit" 
        :disabled="submitting"
        class="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50 shadow-lg shadow-blue-600/20"
      >
        <svg v-if="submitting" class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        {{ submitting ? '保存中...' : '确认保存' }}
      </button>
    </div>

    <!-- Preview Modal -->
    <a-modal
      v-model:open="previewVisible"
      title="Prompt 效果预览"
      :footer="null"
      width="600px"
      centered
      destroyOnClose
    >
      <div class="py-4">
        <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 text-sm font-mono whitespace-pre-wrap max-h-[400px] overflow-y-auto">
          {{ form.prompt_template }}
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue';
import axios from 'axios';
import { message } from 'ant-design-vue';

const props = defineProps({
  initialData: {
    type: Object,
    default: () => ({})
  },
  isEdit: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['submit', 'cancel']);

const api = axios.create({ baseURL: '/api/v1' });

const form = reactive({
  group: '',
  name: '',
  alias: '',
  code: '',
  type: 'number',
  unit: '',
  formula: '',
  threshold_min: '',
  threshold_max: '',
  description: '',
  prompt_template: ''
});

const generatingPrompt = ref(false);
const submitting = ref(false);
const previewVisible = ref(false);

// Watch for initial data changes
watch(() => props.initialData, (newVal) => {
  if (newVal) {
    Object.assign(form, {
      group: newVal.group || '',
      name: newVal.name || '',
      alias: newVal.alias || '',
      code: newVal.code || newVal.advanced_options?.code || '',
      type: newVal.type || newVal.advanced_options?.type || 'number',
      unit: newVal.unit || newVal.advanced_options?.unit || '',
      formula: newVal.formula || newVal.advanced_options?.formula || '',
      threshold_min: newVal.threshold_min || newVal.advanced_options?.threshold_min || '',
      threshold_max: newVal.threshold_max || newVal.advanced_options?.threshold_max || '',
      description: newVal.description || '',
      prompt_template: newVal.prompt_template || newVal.advanced_options?.prompt || ''
    });
  }
}, { immediate: true, deep: true });

const generatePrompt = async () => {
  if (!form.name) {
    message.warning('请先填写指标名称');
    return;
  }
  
  generatingPrompt.value = true;
  try {
    // Call backend to generate prompt based on current form
    const res = await api.post('/metrics/preview_prompt', {
      indicator_name: form.name,
      definition: form.description,
      advanced_options: {
        code: form.code,
        type: form.type,
        unit: form.unit,
        formula: form.formula,
        threshold_range: `${form.threshold_min}-${form.threshold_max}`
      },
      output_format: 'JSON',
      language: 'CN'
    });
    
    form.prompt_template = res.data.prompt;
    message.success('Prompt 生成成功');
  } catch (e) {
    console.error(e);
    message.error('生成失败');
  } finally {
    generatingPrompt.value = false;
  }
};

const previewPrompt = () => {
  previewVisible.value = true;
};

const handleSubmit = async () => {
  if (!form.name || !form.alias || !form.code || !form.type || !form.description) {
    message.warning('请填写所有必填字段');
    return;
  }
  
  if (form.alias.length > 50) {
    message.warning('指标别名长度不能超过50个字符');
    return;
  }
  
  submitting.value = true;
  try {
    // Construct payload
    // Note: Since backend model might not have all these fields as top-level columns yet,
    // we might need to pack them into 'advanced_options' or ensure backend supports them.
    // Assuming we pack them for safety if backend isn't updated.
    // But requirement says "Backend need to provide RESTful API".
    // I'll emit the form data and let the parent component handle the actual API call
    // OR I can handle it here if passed an ID.
    // But to be flexible, I'll emit 'submit' with the payload.
    
    const payload = {
      ...form,
      // Map back to legacy structure if needed, or just send flat object
      advanced_options: {
        code: form.code,
        type: form.type,
        unit: form.unit,
        formula: form.formula,
        threshold_min: form.threshold_min,
        threshold_max: form.threshold_max,
        prompt: form.prompt_template
      }
    };
    
    emit('submit', payload);
  } catch (e) {
    console.error(e);
    message.error('提交失败');
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
/* 强制覆盖 Ant Design Select 的字体大小为 12px */
.text-xs-select :deep(.ant-select-selector),
.text-xs-select :deep(.ant-select-selection-item),
.text-xs-select :deep(.ant-select-selection-placeholder) {
  font-size: 12px !important;
  line-height: 20px !important; /* 适配 12px 字体的行高 */
  min-height: 32px !important; /* 保持与其他输入框高度一致 */
}

/* 覆盖下拉选项的字体大小 */
/* 注意：由于下拉菜单可能渲染在 body 根节点，scoped 样式可能无法渗透。
   建议在全局样式中添加，或使用 dropdownClassName 属性指定类名 */
:global(.ant-select-dropdown .ant-select-item-option-content) {
  font-size: 12px !important;
}
</style>