<template>
  <div class="h-full flex flex-col p-4 overflow-y-auto bg-background/50">
    <Accordion type="multiple" class="w-full space-y-4" :defaultValue="['search', 'details', 'detect', 'manage', 'system']">
      
      <!-- Search Node -->
      <AccordionItem value="search" class="border rounded-lg bg-card shadow-sm px-4">
        <AccordionTrigger class="hover:no-underline py-3">
          <div class="flex items-center gap-2">
            <SearchIcon class="h-4 w-4 text-primary" />
            <span class="font-semibold text-sm">节点搜索</span>
          </div>
        </AccordionTrigger>
        <AccordionContent class="pb-4 pt-1">
          <div class="flex gap-2">
            <div class="relative flex-1">
              <Input 
                v-model="searchQuery" 
                @keyup.enter="handleSearch"
                type="text" 
                placeholder="输入节点名称..." 
                class="h-9 text-sm"
              />
              <Button 
                v-if="searchQuery"
                variant="ghost"
                size="icon"
                @click="searchQuery = ''"
                class="absolute right-0 top-0 h-9 w-9 text-muted-foreground hover:text-foreground"
              >
                <XIcon class="h-3 w-3" />
              </Button>
            </div>
            <Button @click="handleSearch" size="sm" class="h-9 px-4">搜索</Button>
          </div>
        </AccordionContent>
      </AccordionItem>

      <!-- Node Details -->
      <AccordionItem value="details" v-if="selectedNode" class="border rounded-lg bg-card shadow-sm px-4">
        <AccordionTrigger class="hover:no-underline py-3">
          <div class="flex items-center gap-2">
            <InfoIcon class="h-4 w-4 text-primary" />
            <span class="font-semibold text-sm">节点详情</span>
          </div>
        </AccordionTrigger>
        <AccordionContent class="pb-4 pt-1">
          <NodeDetails 
            :node="selectedNode"
            @save="(id, attrs) => $emit('updateNode', id, attrs)"
          />
        </AccordionContent>
      </AccordionItem>

      <!-- Relation Detection -->
      <AccordionItem value="detect" class="border rounded-lg bg-card shadow-sm px-4">
        <AccordionTrigger class="hover:no-underline py-3">
          <div class="flex items-center gap-2">
            <ScanIcon class="h-4 w-4 text-primary" />
            <span class="font-semibold text-sm">关系修复检测</span>
          </div>
        </AccordionTrigger>
        <AccordionContent class="pb-4 pt-1 space-y-4">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label class="text-xs text-muted-foreground">主节点</Label>
              <Input v-model="detectMainNode" placeholder="例如: 中国联通" class="h-9 text-sm" />
            </div>
            <div class="space-y-1.5">
              <Label class="text-xs text-muted-foreground">包含关键词</Label>
              <Input v-model="detectKeyword" placeholder="例如: 联通" class="h-9 text-sm" />
            </div>
            <Button 
              @click="$emit('detect', detectMainNode, detectKeyword)" 
              class="w-full h-9"
              size="sm"
            >
              检测缺失关系
            </Button>
          </div>

          <!-- Detection Results -->
          <div v-if="fixes.length > 0" class="mt-4 border-t pt-4">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs font-medium text-muted-foreground">检测结果 ({{ fixes.length }})</span>
              <Button 
                variant="secondary" 
                size="sm"
                class="h-7 text-xs px-2"
                @click="$emit('applyFixes', selectedFixes)"
                :disabled="selectedFixes.length === 0"
              >
                修复选中 ({{ selectedFixes.length }})
              </Button>
            </div>
            <ScrollArea class="h-[180px] rounded-md border bg-muted/30 p-2">
              <div class="space-y-2">
                <div 
                  v-for="(fix, idx) in fixes" 
                  :key="idx" 
                  class="flex items-start gap-3 p-2.5 rounded-md border bg-background hover:bg-accent/50 transition-colors"
                >
                  <Checkbox 
                    :checked="selectedFixes.includes(fix)"
                    @update:checked="(checked) => toggleFixSelection(fix, checked)"
                    class="mt-0.5"
                  />
                  <div class="space-y-0.5 min-w-0 flex-1">
                    <div class="text-xs font-medium leading-none truncate flex items-center">
                      <span class="truncate">{{ fix.source }}</span>
                      <ArrowRightIcon class="h-3 w-3 mx-1 text-muted-foreground flex-shrink-0" />
                      <span class="truncate">{{ fix.target }}</span>
                    </div>
                    <div class="text-[10px] text-muted-foreground truncate">{{ fix.reason }}</div>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </div>
        </AccordionContent>
      </AccordionItem>

      <!-- Relation Management -->
      <AccordionItem value="manage" class="border rounded-lg bg-card shadow-sm px-4">
        <AccordionTrigger class="hover:no-underline py-3">
          <div class="flex items-center gap-2">
            <LinkIcon class="h-4 w-4 text-primary" />
            <span class="font-semibold text-sm">关系管理</span>
          </div>
        </AccordionTrigger>
        <AccordionContent class="pb-4 pt-1">
          <Tabs v-model="activeTab" class="w-full">
            <TabsList class="grid w-full grid-cols-2 mb-4 h-9">
              <TabsTrigger value="create" class="text-xs">新建关系</TabsTrigger>
              <TabsTrigger value="delete" class="text-xs">解除关系</TabsTrigger>
            </TabsList>
            
            <TabsContent value="create" class="space-y-4 mt-0">
              <div class="grid grid-cols-2 gap-2">
                <div class="space-y-1.5">
                   <Label class="text-xs text-muted-foreground">源节点</Label>
                   <Input v-model="newRel.source" placeholder="源节点" class="h-9 text-sm" />
                </div>
                <div class="space-y-1.5">
                   <Label class="text-xs text-muted-foreground">目标节点</Label>
                   <Input v-model="newRel.target" placeholder="目标节点" class="h-9 text-sm" />
                </div>
              </div>
              <div class="space-y-1.5">
                 <Label class="text-xs text-muted-foreground">关系类型</Label>
                 <Input v-model="newRel.type" placeholder="例如: 属于、包含" class="h-9 text-sm" />
              </div>
              <!-- Relation Attributes -->
               <div class="space-y-2">
                 <div class="flex items-center justify-between">
                    <Label class="text-xs text-muted-foreground">关系属性</Label>
                    <Button size="sm" variant="ghost" class="h-6 px-2 text-xs hover:bg-muted" @click="addRelAttribute">
                      <PlusIcon class="h-3 w-3 mr-1"/> 添加
                    </Button>
                 </div>
                 <div v-for="(attr, idx) in newRelAttributes" :key="idx" class="flex gap-2 items-center">
                    <Input v-model="attr.key" placeholder="Key" class="h-8 text-xs w-1/3 font-mono" />
                    <Input v-model="attr.value" placeholder="Value" class="h-8 text-xs flex-1" />
                    <Button size="icon" variant="ghost" class="h-8 w-8 text-muted-foreground hover:text-destructive" @click="newRelAttributes.splice(idx, 1)">
                      <XIcon class="h-3 w-3" />
                    </Button>
                 </div>
                 <div v-if="newRelAttributes.length === 0" class="text-[10px] text-muted-foreground text-center py-2 bg-muted/20 rounded border border-dashed">
                    暂无额外属性
                 </div>
              </div>

              <Button @click="createRelation" class="w-full h-9" size="sm">创建关系</Button>
            </TabsContent>

            <TabsContent value="delete" class="mt-0 space-y-3">
              <div v-if="!currentRelations || currentRelations.length === 0" class="text-xs text-muted-foreground text-center py-8 border rounded-lg border-dashed bg-muted/10">
                暂无可见关系，请先搜索加载节点
              </div>
              <div v-else class="space-y-3">
                <div class="flex items-center justify-between px-1">
                   <span class="text-xs text-muted-foreground">当前列表 ({{ currentRelations.length }})</span>
                   <Button 
                     variant="ghost" 
                     size="sm" 
                     class="h-6 p-0 text-xs text-primary hover:bg-transparent hover:underline"
                     @click="toggleAllDeleteSelection"
                   >
                     {{ selectedRelationsToDelete.length < currentRelations.length ? '全选' : '取消全选' }}
                   </Button>
                </div>
                
                <ScrollArea class="h-[200px] rounded-md border bg-muted/30 p-2">
                  <div class="space-y-2">
                    <div 
                      v-for="(rel, idx) in currentRelations" 
                      :key="idx" 
                      class="flex items-center gap-3 p-2 rounded-md border bg-background hover:bg-accent cursor-pointer group transition-all"
                      :class="{ 'border-destructive/30 bg-destructive/5': selectedRelationsToDelete.includes(rel) }"
                      @click="toggleDeleteSelection(rel)"
                    >
                      <Checkbox 
                        :checked="selectedRelationsToDelete.includes(rel)"
                        class="data-[state=checked]:bg-destructive data-[state=checked]:border-destructive"
                      />
                      <div class="text-sm flex-1 min-w-0">
                        <div class="flex items-center gap-1 truncate text-xs font-medium">
                           <span class="truncate">{{ rel.source }}</span>
                           <ArrowRightIcon class="h-3 w-3 text-muted-foreground shrink-0" />
                           <span class="truncate">{{ rel.target }}</span>
                        </div>
                        <div class="text-[10px] text-muted-foreground mt-0.5 flex items-center gap-2" v-if="rel.label">
                          <span class="bg-muted px-1 rounded">{{ rel.label }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </ScrollArea>

                <Button 
                  variant="destructive" 
                  class="w-full h-9"
                  size="sm"
                  :disabled="selectedRelationsToDelete.length === 0"
                  @click="deleteRelations"
                >
                  解除选中关系 ({{ selectedRelationsToDelete.length }})
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </AccordionContent>
      </AccordionItem>

      <!-- System Actions -->
      <AccordionItem value="system" class="border rounded-lg bg-card shadow-sm px-4">
        <AccordionTrigger class="hover:no-underline py-3">
          <div class="flex items-center gap-2">
            <SettingsIcon class="h-4 w-4 text-primary" />
            <span class="font-semibold text-sm">系统操作</span>
          </div>
        </AccordionTrigger>
        <AccordionContent class="pb-4 pt-1">
          <div class="grid grid-cols-2 gap-3">
            <Button variant="outline" size="sm" @click="$emit('backup')" class="h-9">备份图谱</Button>
            <Button variant="outline" size="sm" class="h-9 text-destructive hover:bg-destructive/10 hover:text-destructive border-destructive/20" @click="$emit('restore')">回滚操作</Button>
          </div>
        </AccordionContent>
      </AccordionItem>

    </Accordion>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { 
  X as XIcon, 
  ArrowRight as ArrowRightIcon, 
  Plus as PlusIcon, 
  Search as SearchIcon, 
  Info as InfoIcon,
  Scan as ScanIcon,
  Link as LinkIcon,
  Settings as SettingsIcon
} from 'lucide-vue-next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@/components/ui/accordion';
import NodeDetails from './NodeDetails.vue';
import type { RelationFix } from '../api';

const props = defineProps<{
  fixes: RelationFix[];
  currentRelations?: Array<{ source: string; target: string; label?: string }>;
  selectedNode?: any;
}>();

const emit = defineEmits<{
  (e: 'search', query: string): void;
  (e: 'detect', mainNode: string, keyword: string): void;
  (e: 'applyFixes', fixes: RelationFix[]): void;
  (e: 'create', source: string, target: string, type: string, attributes: Record<string, any>): void;
  (e: 'delete', relations: Array<{ source: string; target: string }>): void;
  (e: 'backup'): void;
  (e: 'restore'): void;
  (e: 'updateNode', nodeId: string, attributes: Record<string, any>): void;
}>();

const searchQuery = ref('');
const detectMainNode = ref('');
const detectKeyword = ref('');
const selectedFixes = ref<RelationFix[]>([]);
const newRel = ref({ source: '', target: '', type: '包含' });
const newRelAttributes = ref<{ key: string; value: string }[]>([]);
const activeTab = ref<string>('create');
const selectedRelationsToDelete = ref<any[]>([]);

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value);
  }
};

const addRelAttribute = () => {
  newRelAttributes.value.push({ key: '', value: '' });
};

const createRelation = () => {
  if (newRel.value.source && newRel.value.target) {
    const attributes: Record<string, any> = {};
    for (const attr of newRelAttributes.value) {
      if (attr.key.trim()) {
        attributes[attr.key.trim()] = attr.value;
      }
    }
    
    emit('create', newRel.value.source, newRel.value.target, newRel.value.type || 'related', attributes);
    newRel.value = { source: '', target: '', type: '包含' };
    newRelAttributes.value = [];
  }
};

const toggleFixSelection = (fix: RelationFix, checked: boolean) => {
  if (checked) {
    if (!selectedFixes.value.includes(fix)) {
      selectedFixes.value.push(fix);
    }
  } else {
    const index = selectedFixes.value.indexOf(fix);
    if (index > -1) {
      selectedFixes.value.splice(index, 1);
    }
  }
};

const toggleDeleteSelection = (rel: any) => {
  const index = selectedRelationsToDelete.value.indexOf(rel);
  if (index === -1) {
    selectedRelationsToDelete.value.push(rel);
  } else {
    selectedRelationsToDelete.value.splice(index, 1);
  }
};

const toggleAllDeleteSelection = () => {
  if (props.currentRelations && selectedRelationsToDelete.value.length < props.currentRelations.length) {
    selectedRelationsToDelete.value = [...props.currentRelations];
  } else {
    selectedRelationsToDelete.value = [];
  }
};

const deleteRelations = () => {
  if (selectedRelationsToDelete.value.length === 0) return;
  
  if (confirm(`确定要解除选中的 ${selectedRelationsToDelete.value.length} 个关系吗？`)) {
    emit('delete', selectedRelationsToDelete.value);
    selectedRelationsToDelete.value = [];
  }
};

watch(() => props.fixes, (newFixes) => {
  selectedFixes.value = [...newFixes]; // Select all by default
});

// Auto-fill create source if node selected
watch(() => props.selectedNode, (node) => {
  if (node && !newRel.value.source) {
    newRel.value.source = node.id;
  }
});
</script>