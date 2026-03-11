<template>
  <div class="h-full flex flex-col bg-background border-l">
    <!-- Header -->
    <div class="px-4 py-3 border-b flex items-center justify-between bg-muted/20">
      <div class="flex items-center gap-2 font-semibold text-sm">
        <InfoIcon class="h-4 w-4 text-primary" />
        <span>节点检查器</span>
      </div>
      <Button variant="ghost" size="icon" class="h-6 w-6" @click="$emit('close')">
        <XIcon class="h-4 w-4" />
      </Button>
    </div>

    <!-- Content -->
    <Tabs defaultValue="attributes" class="flex-1 flex flex-col min-h-0">
      <div class="px-4 pt-2">
        <TabsList class="w-full grid grid-cols-2">
          <TabsTrigger value="attributes" class="text-xs px-2 h-8">属性详情</TabsTrigger>
          <TabsTrigger value="relations" class="text-xs px-2 h-8">关系管理</TabsTrigger>
        </TabsList>
      </div>

      <!-- Attributes Tab -->
      <TabsContent value="attributes" class="flex-1 min-h-0 p-4 space-y-4 flex flex-col overflow-hidden mt-0">
        <NodeDetails 
          v-if="node" 
          :node="node" 
          :loading="loading"
          @save="handleSaveDetails"
        />
        <div v-else class="text-center text-muted-foreground py-8 text-xs">
          请选择一个节点查看详情
        </div>
      </TabsContent>

      <!-- Relations Tab -->
      <TabsContent value="relations" class="flex-1 min-h-0 flex flex-col overflow-hidden mt-0">
        <div class="p-4 space-y-4 flex-1 overflow-y-auto">
          <!-- Create New Relation -->
          <div class="space-y-3 border rounded-md p-3 bg-muted/10">
            <h4 class="text-xs font-medium flex items-center gap-2">
              <PlusIcon class="h-3.5 w-3.5" />
              新建关系
            </h4>
            
            <div class="grid gap-2">
              <div class="grid grid-cols-2 gap-2">
                 <div class="space-y-1">
                   <Label class="text-[10px] text-muted-foreground">源节点</Label>
                   <Input v-model="newRel.source" class="h-7 text-xs" readonly disabled />
                 </div>
                 <div class="space-y-1">
                   <Label class="text-[10px] text-muted-foreground">目标节点 ID</Label>
                   <Input v-model="newRel.target" placeholder="目标 ID" class="h-7 text-xs" />
                 </div>
              </div>
              
              <div class="space-y-1">
                 <Label class="text-[10px] text-muted-foreground">关系类型</Label>
                 <Input v-model="newRel.type" placeholder="例如: 包含" class="h-7 text-xs" />
              </div>

              <!-- Simple attributes for relation -->
              <div class="space-y-1">
                 <div class="flex justify-between items-center">
                    <Label class="text-[10px] text-muted-foreground">附加属性</Label>
                    <Button variant="ghost" size="sm" class="h-5 px-1 text-[10px]" @click="addRelAttr">
                      <PlusIcon class="h-3 w-3" />
                    </Button>
                 </div>
                 <div v-for="(attr, idx) in newRelAttrs" :key="idx" class="flex gap-1 mb-1">
                    <Input v-model="attr.key" placeholder="Key" class="h-6 text-[10px] w-1/3" />
                    <Input v-model="attr.value" placeholder="Value" class="h-6 text-[10px] flex-1" />
                    <Button variant="ghost" size="icon" class="h-6 w-6 text-destructive" @click="newRelAttrs.splice(idx, 1)">
                       <XIcon class="h-3 w-3" />
                    </Button>
                 </div>
              </div>

              <Button size="sm" class="h-7 text-xs mt-1" @click="createRelation" :disabled="!newRel.target">
                创建
              </Button>
            </div>
          </div>

          <!-- Existing Relations List -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h4 class="text-xs font-medium">现有关系 ({{ relations.length }})</h4>
              <Button 
                variant="destructive" 
                size="sm" 
                class="h-6 text-[10px] px-2"
                :disabled="selectedRels.length === 0"
                @click="deleteRelations"
              >
                删除选中 ({{ selectedRels.length }})
              </Button>
            </div>

            <div v-if="relations.length === 0" class="text-xs text-muted-foreground text-center py-4 border border-dashed rounded">
              无可见关系
            </div>

            <div v-else class="space-y-1.5">
               <div 
                 v-for="(rel, idx) in relations" 
                 :key="idx"
                 class="flex items-center gap-2 p-2 rounded border bg-card hover:bg-accent/50 text-xs group"
               >
                 <Checkbox 
                   :checked="selectedRels.includes(rel)"
                   @update:checked="(checked) => toggleRelSelect(rel, checked)"
                 />
                 <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-1">
                      <span class="truncate font-mono text-muted-foreground">{{ rel.source }}</span>
                      <ArrowRightIcon class="h-3 w-3 text-muted-foreground/50" />
                      <span class="truncate font-medium">{{ rel.target }}</span>
                    </div>
                    <div class="text-[10px] text-muted-foreground mt-0.5" v-if="rel.label">
                      {{ rel.label }}
                    </div>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { 
  Info as InfoIcon, 
  X as XIcon, 
  Plus as PlusIcon, 
  ArrowRight as ArrowRightIcon 
} from 'lucide-vue-next';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import NodeDetails from './NodeDetails.vue';

const props = defineProps<{
  node: any;
  relations: Array<{ source: string; target: string; label?: string }>;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updateNode', id: string, attrs: any): void;
  (e: 'createRelation', source: string, target: string, type: string, attrs: any): void;
  (e: 'deleteRelations', rels: Array<{ source: string; target: string }>): void;
}>();

const newRel = ref({ source: '', target: '', type: '包含' });
const newRelAttrs = ref<{key: string, value: string}[]>([]);
const selectedRels = ref<any[]>([]);

// Sync source with node id
watch(() => props.node, (newNode) => {
  if (newNode) {
    newRel.value.source = newNode.id;
    selectedRels.value = []; // Clear selection on node change
  }
}, { immediate: true });

const handleSaveDetails = (id: string, attrs: any) => {
  emit('updateNode', id, attrs);
};

const addRelAttr = () => {
  newRelAttrs.value.push({ key: '', value: '' });
};

const createRelation = () => {
  if (!newRel.value.target) return;
  
  const attrs: Record<string, any> = {};
  newRelAttrs.value.forEach(a => {
    if (a.key) attrs[a.key] = a.value;
  });

  emit('createRelation', newRel.value.source, newRel.value.target, newRel.value.type, attrs);
  
  // Reset form partly
  newRel.value.target = '';
  newRelAttrs.value = [];
};

const toggleRelSelect = (rel: any, checked: boolean) => {
  if (checked) {
    if (!selectedRels.value.includes(rel)) selectedRels.value.push(rel);
  } else {
    const idx = selectedRels.value.indexOf(rel);
    if (idx > -1) selectedRels.value.splice(idx, 1);
  }
};

const deleteRelations = () => {
  if (selectedRels.value.length === 0) return;
  emit('deleteRelations', selectedRels.value);
  selectedRels.value = [];
};
</script>
