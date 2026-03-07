<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Trash2, Plus, Code, ListFilter } from 'lucide-vue-next';
import { Switch } from '@/components/ui/switch';

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits(['update:modelValue']);

// Data structures
interface Condition {
  id: string;
  field: string;
  operator: string;
  value: string;
}

const mode = ref<'visual' | 'code'>('visual');
const logic = ref<'&' | '|'>('&');
const conditions = ref<Condition[]>([]);
const rawExpression = ref('');

// Predefined options
const commonFields = [
  { value: 'intent', label: '意图 (Intent)' },
  { value: 'confidence', label: '置信度 (Confidence)' },
  { value: 'content', label: '内容 (Content)' },
  { value: 'timestamp', label: '时间戳 (Timestamp)' },
];

const operators = [
  { value: '==', label: '等于 (==)' },
  { value: '!=', label: '不等于 (!=)' },
  { value: '>', label: '大于 (>)' },
  { value: '<', label: '小于 (<)' },
  { value: '>=', label: '大于等于 (>=)' },
  { value: '<=', label: '小于等于 (<=)' },
  // Pathway string methods might need special handling, but let's stick to basics first
  // .contains() is not standard python operator syntax without method call
  // We can support it by generating `col('field').contains('value')`
];

// Initialize
onMounted(() => {
  rawExpression.value = props.modelValue || '';
  if (props.modelValue && !props.modelValue.includes("col('")) {
    // If complex expression, switch to code mode
    mode.value = 'code';
  } else {
    // Try to parse simple expressions?
    // Parsing is hard. For now, if there is a value, we start in code mode to avoid overwriting.
    // If empty, visual mode.
    if (props.modelValue) {
      mode.value = 'code';
    } else {
      addCondition();
    }
  }
});

const addCondition = () => {
  conditions.value.push({
    id: Math.random().toString(36).substring(7),
    field: 'intent',
    operator: '==',
    value: ''
  });
  updateExpression();
};

const removeCondition = (index: number) => {
  conditions.value.splice(index, 1);
  updateExpression();
};

const updateExpression = () => {
  if (mode.value !== 'visual') return;

  if (conditions.value.length === 0) {
    rawExpression.value = '';
    emit('update:modelValue', '');
    return;
  }

  const parts = conditions.value.map(c => {
    // Handle value quoting
    let val = c.value;
    const isNumber = !isNaN(parseFloat(val)) && isFinite(Number(val));
    if (!isNumber && !val.startsWith("'") && !val.startsWith('"')) {
      val = `'${val}'`;
    }

    // Generate syntax: col('field') op value
    // Special handling for methods if we add them later
    return `(col('${c.field}') ${c.operator} ${val})`;
  });

  rawExpression.value = parts.join(` ${logic.value} `);
  emit('update:modelValue', rawExpression.value);
};

// Watchers for visual changes
watch(conditions, updateExpression, { deep: true });
watch(logic, updateExpression);

// Watch for external code changes (only if in code mode)
watch(() => props.modelValue, (newVal) => {
  if (mode.value === 'code' && newVal !== rawExpression.value) {
    rawExpression.value = newVal;
  }
});

const handleCodeChange = (val: string) => {
  rawExpression.value = val;
  emit('update:modelValue', val);
};

const toggleMode = (checked: boolean) => {
  mode.value = checked ? 'visual' : 'code';
  if (mode.value === 'visual' && conditions.value.length === 0) {
     // If switching to visual and empty, init
     addCondition();
  }
};
</script>

<template>
  <div class="space-y-4 border rounded-md p-3 bg-muted/20">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <ListFilter class="w-4 h-4 text-muted-foreground" v-if="mode === 'visual'" />
        <Code class="w-4 h-4 text-muted-foreground" v-else />
        <Label class="text-sm font-medium">
          {{ mode === 'visual' ? '可视化构建器' : '代码编辑器' }}
        </Label>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-xs text-muted-foreground">代码模式</span>
        <Switch :checked="mode === 'visual'" @update:checked="toggleMode" />
        <span class="text-xs text-muted-foreground">可视化</span>
      </div>
    </div>

    <!-- Visual Mode -->
    <div v-if="mode === 'visual'" class="space-y-3">
      <div class="flex items-center space-x-2 mb-2">
        <Label class="text-xs">逻辑关系:</Label>
        <Select v-model="logic">
          <SelectTrigger class="w-24 h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="&">AND (且)</SelectItem>
            <SelectItem value="|">OR (或)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div v-for="(condition, index) in conditions" :key="condition.id" class="flex items-center space-x-2">
        <!-- Field -->
        <div class="flex-1 min-w-[120px]">
           <!-- Simple Input for now, could be combobox -->
           <div class="relative">
             <Input 
               v-model="condition.field" 
               placeholder="字段 (如 intent)" 
               class="h-8 text-xs font-mono" 
               list="common-fields"
             />
             <datalist id="common-fields">
               <option v-for="f in commonFields" :key="f.value" :value="f.value">{{ f.label }}</option>
             </datalist>
           </div>
        </div>

        <!-- Operator -->
        <Select v-model="condition.operator">
          <SelectTrigger class="w-[110px] h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="op in operators" :key="op.value" :value="op.value">
              {{ op.label }}
            </SelectItem>
          </SelectContent>
        </Select>

        <!-- Value -->
        <div class="flex-1">
          <Input 
            v-model="condition.value" 
            placeholder="值" 
            class="h-8 text-xs" 
          />
        </div>

        <!-- Delete -->
        <Button variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="removeCondition(index)">
          <Trash2 class="w-4 h-4" />
        </Button>
      </div>

      <Button variant="outline" size="sm" class="w-full h-8 border-dashed" @click="addCondition">
        <Plus class="w-3 h-3 mr-2" />
        添加条件
      </Button>

      <div class="mt-4 p-2 bg-muted rounded text-xs font-mono text-muted-foreground break-all">
        预览: {{ rawExpression || '(空)' }}
      </div>
    </div>

    <!-- Code Mode -->
    <div v-else>
      <textarea 
        class="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono text-xs"
        :value="rawExpression"
        @input="(e) => handleCodeChange((e.target as HTMLTextAreaElement).value)"
        placeholder="col('intent') == 'refund' & col('confidence') > 0.8"
      />
      <p class="text-xs text-muted-foreground mt-2">
        使用 Python 语法。可用变量: <code>col('name')</code>, <code>table</code>.
        <br>逻辑运算符: <code>&</code> (AND), <code>|</code> (OR).
      </p>
    </div>
  </div>
</template>
