<template>
  <div class="h-full flex flex-col space-y-4">
    <!-- Basic Info -->
    <div class="space-y-2">
      <Label class="text-xs text-muted-foreground font-medium">节点名称 (ID)</Label>
      <div class="p-2.5 bg-muted/30 border rounded-md text-sm font-mono break-all select-all shadow-sm">{{ node.id }}</div>
    </div>

    <!-- Type (Special Attribute) -->
    <div class="space-y-2">
      <Label class="text-xs text-muted-foreground font-medium">实体类型 (Type)</Label>
      <Input v-model="entityType" placeholder="例如: Person, Organization..." class="h-9 text-sm" />
    </div>

    <!-- Attributes -->
    <div class="flex-1 flex flex-col min-h-0 space-y-2">
      <div class="flex items-center justify-between">
          <Label class="text-xs text-muted-foreground font-medium">属性列表</Label>
          <Button size="sm" variant="ghost" class="h-6 px-2 text-xs hover:bg-muted" @click="addAttribute">
            <PlusIcon class="h-3 w-3 mr-1"/> 添加
          </Button>
      </div>
      
      <ScrollArea class="flex-1 border rounded-md bg-muted/10">
          <div class="p-2 space-y-2">
            <div v-for="(attr, index) in otherAttributes" :key="index" class="group flex items-center gap-2">
                <Input v-model="attr.key" placeholder="Key" class="h-8 text-xs font-mono w-1/3 bg-background shadow-sm" />
                <div class="text-muted-foreground/50">:</div>
                <Input v-model="attr.value" placeholder="Value" class="h-8 text-xs flex-1 bg-background shadow-sm" />
                <Button 
                  size="icon" 
                  variant="ghost" 
                  class="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive hover:bg-destructive/10" 
                  @click="removeAttribute(index)"
                >
                  <Trash2Icon class="h-3 w-3" />
                </Button>
            </div>
            <div v-if="otherAttributes.length === 0" class="text-center text-xs text-muted-foreground py-8 flex flex-col items-center gap-2">
                <div class="p-2 rounded-full bg-muted/50">
                  <ListIcon class="h-4 w-4 opacity-50" />
                </div>
                暂无其他属性
            </div>
          </div>
      </ScrollArea>
    </div>
    
    <div class="pt-2">
      <Button class="w-full h-9" @click="save" :disabled="loading" size="sm">
        <SaveIcon class="h-3.5 w-3.5 mr-2" />
        {{ loading ? '保存中...' : '保存更改' }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { Plus as PlusIcon, Trash2 as Trash2Icon, Save as SaveIcon, List as ListIcon } from 'lucide-vue-next';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';

const props = defineProps<{
  node: any;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'save', nodeId: string, attributes: Record<string, any>): void;
}>();

const entityType = ref('');
const otherAttributes = ref<{ key: string; value: string }[]>([]);

// Initialize local state from props
watch(() => props.node, (newNode) => {
  if (newNode) {
    // Extract type
    entityType.value = newNode.type || newNode.label || ''; // Default to label if type missing, or empty
    if (entityType.value === newNode.id) entityType.value = ''; // Don't use ID as type by default

    // Extract other attributes
    const attrs: { key: string; value: string }[] = [];
    for (const [key, value] of Object.entries(newNode)) {
      if (key === 'id' || key === 'label' || key === 'type') continue; // Skip special fields
      if (typeof value === 'object') {
         attrs.push({ key, value: JSON.stringify(value) });
      } else {
         attrs.push({ key, value: String(value) });
      }
    }
    otherAttributes.value = attrs;
  }
}, { immediate: true });

const addAttribute = () => {
  otherAttributes.value.push({ key: '', value: '' });
};

const removeAttribute = (index: number) => {
  otherAttributes.value.splice(index, 1);
};

const save = () => {
  const attributes: Record<string, any> = {};
  
  if (entityType.value) {
    attributes.type = entityType.value;
  }
  
  for (const attr of otherAttributes.value) {
    if (attr.key.trim()) {
      attributes[attr.key.trim()] = attr.value;
    }
  }
  
  emit('save', props.node.id, attributes);
};
</script>