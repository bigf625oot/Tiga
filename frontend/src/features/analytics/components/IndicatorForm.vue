<template>
  <div class="space-y-6">
    <!-- Basic Info -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="space-y-2">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          指标分组 <span class="text-destructive">*</span>
        </label>
        <Input 
          v-model="form.group" 
          type="text" 
          placeholder="例如：财务指标" 
        />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          指标名称 <span class="text-destructive">*</span>
        </label>
        <Input 
          v-model="form.name" 
          type="text" 
          placeholder="例如：营业收入" 
        />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          指标别名 <span class="text-destructive">*</span>
        </label>
        <Input 
          v-model="form.alias" 
          type="text" 
          placeholder="例如：Revenue, 营收" 
          maxlength="50"
        />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          指标编码 <span class="text-destructive">*</span>
        </label>
        <Input 
          v-model="form.code" 
          type="text" 
          placeholder="例如：REV_001" 
        />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          数据类型 <span class="text-destructive">*</span>
        </label>
        <Select v-model="form.type">
          <SelectTrigger>
            <SelectValue placeholder="请选择数据类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="number">数值型 (Number)</SelectItem>
            <SelectItem value="currency">金额型 (Currency)</SelectItem>
            <SelectItem value="percentage">百分比 (Percentage)</SelectItem>
            <SelectItem value="text">文本型 (Text)</SelectItem>
            <SelectItem value="boolean">布尔型 (Boolean)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          单位
        </label>
        <Input 
          v-model="form.unit" 
          type="text" 
          placeholder="例如：万元, %, 个" 
        />
      </div>
    </div>

    <!-- Advanced Info -->
    <div class="space-y-2">
      <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        计算公式
      </label>
      <Input 
        v-model="form.formula" 
        type="text" 
        placeholder="例如：营业收入 - 营业成本" 
      />
    </div>

    <div class="space-y-2">
      <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        阈值范围
      </label>
      <div class="flex items-center gap-2">
        <Input 
          v-model="form.threshold_min" 
          type="text" 
          placeholder="最小值" 
        />
        <span class="text-muted-foreground">-</span>
        <Input 
          v-model="form.threshold_max" 
          type="text" 
          placeholder="最大值" 
        />
      </div>
    </div>

    <div class="space-y-2">
      <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        业务含义描述 <span class="text-destructive">*</span>
      </label>
      <Textarea 
        v-model="form.description" 
        rows="3" 
        placeholder="详细描述该指标的定义、业务场景..." 
        class="resize-none"
      />
    </div>

    <!-- Prompt Generation -->
    <div class="bg-muted/30 p-4 rounded-lg border border-border">
      <div class="flex justify-between items-center mb-4">
        <label class="text-sm font-semibold flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-primary" />
          智能 Prompt 模板
        </label>
        <Button 
          @click="generatePrompt" 
          :disabled="generatingPrompt || !form.name"
          variant="outline"
          size="sm"
          class="h-8 gap-1"
        >
          <Loader2 v-if="generatingPrompt" class="w-3 h-3 animate-spin" />
          {{ generatingPrompt ? '生成中...' : '自动生成' }}
        </Button>
      </div>
      <Textarea 
        v-model="form.prompt_template" 
        rows="6" 
        placeholder="点击“自动生成”或手动输入 Prompt 模板..." 
        class="font-mono text-xs resize-none bg-background"
      />
      <div class="flex justify-end mt-2">
         <Button 
          v-if="form.prompt_template"
          @click="previewPrompt"
          variant="ghost"
          size="sm"
          class="h-6 text-xs text-muted-foreground hover:text-primary gap-1 px-2"
        >
          <Eye class="w-3 h-3" />
          预览效果
        </Button>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end gap-4 pt-4 border-t border-border">
      <Button variant="outline" @click="$emit('cancel')">
        取消
      </Button>
      <Button 
        @click="handleSubmit" 
        :disabled="submitting"
        class="shadow-lg shadow-primary/20"
      >
        <Loader2 v-if="submitting" class="mr-2 h-4 w-4 animate-spin" />
        {{ submitting ? '保存中...' : '确认保存' }}
      </Button>
    </div>

    <!-- Preview Dialog -->
    <Dialog v-model:open="previewVisible">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Prompt 效果预览</DialogTitle>
        </DialogHeader>
        <div class="py-4">
          <ScrollArea class="h-[400px] w-full rounded-md border p-4 bg-muted/50 font-mono text-sm whitespace-pre-wrap">
            {{ form.prompt_template }}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue';
import axios from 'axios';
import { Sparkles, Loader2, Eye } from 'lucide-vue-next';

// UI Components
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/toast/use-toast';

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
const { toast } = useToast();

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
    toast({ title: '请先填写指标名称', variant: 'warning' });
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
    toast({ title: 'Prompt 生成成功' });
  } catch (e) {
    console.error(e);
    toast({ title: '生成失败', description: e.message, variant: 'destructive' });
  } finally {
    generatingPrompt.value = false;
  }
};

const previewPrompt = () => {
  previewVisible.value = true;
};

const handleSubmit = async () => {
  if (!form.name || !form.alias || !form.code || !form.type || !form.description) {
    toast({ title: '请填写所有必填字段', variant: 'warning' });
    return;
  }
  
  if (form.alias.length > 50) {
    toast({ title: '指标别名长度不能超过50个字符', variant: 'warning' });
    return;
  }
  
  submitting.value = true;
  try {
    const payload = {
      ...form,
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
    toast({ title: '提交失败', variant: 'destructive' });
  } finally {
    submitting.value = false;
  }
};
</script>
