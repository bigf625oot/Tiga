<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h4 class="text-sm font-medium text-muted-foreground">参数定义</h4>
      <Button variant="outline" size="sm" class="h-7 text-xs" @click="addProperty">
        <Plus class="w-3 h-3 mr-1" /> 添加参数
      </Button>
    </div>

    <div v-if="properties.length === 0" class="text-center py-8 border border-dashed rounded-lg text-xs text-muted-foreground bg-muted/20">
      暂无参数定义，点击右上角添加。
    </div>

    <div v-else class="space-y-2">
      <div v-for="(prop, index) in properties" :key="index" class="flex gap-2 items-start group">
        <div class="grid gap-2 flex-1 p-3 border rounded-md bg-card/50 hover:bg-card transition-colors">
          <div class="flex gap-2">
            <Input v-model="prop.name" placeholder="参数名 (key)" class="h-7 text-xs font-mono" />
            <Select v-model="prop.type">
              <SelectTrigger class="h-7 text-xs w-[100px]">
                <SelectValue placeholder="类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="string">String</SelectItem>
                <SelectItem value="number">Number</SelectItem>
                <SelectItem value="integer">Integer</SelectItem>
                <SelectItem value="boolean">Boolean</SelectItem>
                <SelectItem value="array">Array</SelectItem>
                <SelectItem value="object">Object</SelectItem>
              </SelectContent>
            </Select>
            <div class="flex items-center space-x-2 border rounded px-2 h-7 bg-background">
              <Checkbox :id="`req-${index}`" :checked="prop.required" @update:checked="(v) => prop.required = v" />
              <Label :for="`req-${index}`" class="text-[10px] cursor-pointer">必填</Label>
            </div>
          </div>
          <Input v-model="prop.description" placeholder="参数描述 (description)" class="h-7 text-xs text-muted-foreground" />
        </div>
        <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" @click="removeProperty(index)">
          <Trash2 class="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { Plus, Trash2 } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['update:modelValue']);

// Local state to manage the UI form
const properties = ref([]);

// Initialize from props
onMounted(() => {
  parseSchema(props.modelValue);
});

// Watch for external changes (e.g. reset form)
watch(() => props.modelValue, (newVal) => {
  // Only update if we are not the ones triggering it (simple check to avoid loops, or just parse)
  // Ideally we need deep comparison, but for now simple re-parse if empty or different
  if (Object.keys(newVal).length === 0 && properties.value.length > 0) {
     properties.value = [];
  } else {
     // Optional: re-parse if needed, but usually we just sync one way
  }
}, { deep: true });

const parseSchema = (schema) => {
  if (!schema || !schema.properties) {
    properties.value = [];
    return;
  }
  
  const requiredSet = new Set(schema.required || []);
  properties.value = Object.entries(schema.properties).map(([key, value]) => ({
    name: key,
    type: value.type || 'string',
    description: value.description || '',
    required: requiredSet.has(key)
  }));
};

const addProperty = () => {
  properties.value.push({
    name: '',
    type: 'string',
    description: '',
    required: false
  });
};

const removeProperty = (index) => {
  properties.value.splice(index, 1);
};

// Sync back to parent
watch(properties, () => {
  const schema = {
    type: "object",
    properties: {},
    required: []
  };

  properties.value.forEach(prop => {
    if (prop.name) {
      schema.properties[prop.name] = {
        type: prop.type,
        description: prop.description
      };
      if (prop.required) {
        schema.required.push(prop.name);
      }
    }
  });

  emit('update:modelValue', schema);
}, { deep: true });

</script>
