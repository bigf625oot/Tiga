<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  ArrowRight, 
  Trash2, 
  Plus, 
  ArrowRightLeft,
  Sparkles,
  RotateCcw,
  FileJson,
  Braces
} from 'lucide-vue-next';

const store = usePipelineStore();
const node = computed(() => store.selectedNode);

// --- Helpers ---
const updateConfig = (key: string, value: any) => {
  if (node.value && node.value.data) {
    const newConfig = { ...(node.value.data.config || {}), [key]: value };
    store.updateNodeData(node.value.id, { config: newConfig });
  }
};

const config = computed(() => node.value?.data?.config || {});
const mappings = computed(() => config.value.mappings || []);

// --- Schema Discovery State ---
const discoveredFields = ref<string[]>([]);
const schemaInput = ref('');
const isSchemaDialogOpen = ref(false);

const parseSchema = () => {
  try {
    const input = schemaInput.value.trim();
    if (!input) return;
    
    let fields: string[] = [];
    
    // Try parsing as JSON
    if (input.startsWith('{') || input.startsWith('[')) {
      const parsed = JSON.parse(input);
      const sample = Array.isArray(parsed) ? parsed[0] : parsed;
      fields = Object.keys(sample);
    } 
    // Try parsing as CSV Header (comma separated)
    else if (input.includes(',')) {
      fields = input.split(',').map(f => f.trim());
    } 
    // Treat as newline separated list
    else {
      fields = input.split('\n').map(f => f.trim()).filter(Boolean);
    }
    
    discoveredFields.value = fields;
    isSchemaDialogOpen.value = false;
  } catch (e) {
    console.error('Failed to parse schema', e);
    // Could show a toast here
  }
};

// --- Mapping Operations ---

const addEmptyRow = () => {
  const current = [...mappings.value];
  current.push({
    source: '',
    target: '',
    type: 'rename',
    expression: ''
  });
  updateConfig('mappings', current);
};

const updateRow = (index: number, field: string, value: any) => {
  const current = [...mappings.value];
  current[index] = { ...current[index], [field]: value };
  
  // Auto-fill target if source is set and target is empty (for convenience)
  if (field === 'source' && value && !current[index].target) {
    current[index].target = value;
  }
  
  updateConfig('mappings', current);
};

const removeRow = (index: number) => {
  const current = [...mappings.value];
  current.splice(index, 1);
  updateConfig('mappings', current);
};

const clearAll = () => {
  updateConfig('mappings', []);
};

const autoMap = () => {
  // Map discovered fields to themselves
  const current = [...mappings.value];
  const existingSources = new Set(current.map((m: any) => m.source));
  
  discoveredFields.value.forEach(field => {
    if (!existingSources.has(field)) {
      current.push({
        source: field,
        target: field,
        type: 'rename',
        expression: ''
      });
    }
  });
  
  updateConfig('mappings', current);
};

// --- Initial Setup ---
onMounted(() => {
  if (mappings.value.length === 0) {
    // Add one empty row to start
    addEmptyRow();
  }
});
</script>

<template>
  <div class="flex flex-col w-full min-h-[500px] bg-background/50 border rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b bg-muted/20 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="p-1.5 bg-primary/10 rounded-md">
          <ArrowRightLeft class="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 class="text-sm font-medium">字段映射</h3>
          <p class="text-[10px] text-muted-foreground">配置输入到输出的转换规则</p>
        </div>
      </div>
      
      <div class="flex gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          class="h-7 text-xs gap-1" 
          @click="clearAll"
          :disabled="mappings.length === 0"
        >
          <RotateCcw class="w-3 h-3" />
          清空
        </Button>
        <Dialog v-model:open="isSchemaDialogOpen">
          <DialogTrigger as-child>
            <Button variant="secondary" size="sm" class="h-7 text-xs gap-1">
              <FileJson class="w-3 h-3" />
              导入字段
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>导入源字段</DialogTitle>
              <DialogDescription>
                粘贴 JSON 样例数据或 CSV 表头，系统将自动识别可用字段。
              </DialogDescription>
            </DialogHeader>
            <Textarea 
              v-model="schemaInput" 
              placeholder='Example: {"id": 1, "name": "Alice", "age": 30}' 
              class="min-h-[150px] font-mono text-xs"
            />
            <DialogFooter>
              <Button @click="parseSchema">识别字段</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>

    <!-- Quick Actions Bar -->
    <div class="px-4 py-2 bg-background border-b flex items-center gap-2" v-if="discoveredFields.length > 0">
      <Sparkles class="w-3.5 h-3.5 text-yellow-500" />
      <span class="text-xs text-muted-foreground">已识别 {{ discoveredFields.length }} 个字段</span>
      <Button variant="ghost" size="sm" class="h-6 text-xs text-primary hover:text-primary/80 px-2 ml-auto" @click="autoMap">
        自动填充所有映射
      </Button>
    </div>

    <!-- Main Table -->
    <ScrollArea class="flex-1">
      <div class="min-w-[500px]">
        <Table>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead class="w-[35%] text-xs h-9">输入字段 (Input)</TableHead>
              <TableHead class="w-[25%] text-xs h-9 text-center">转换逻辑</TableHead>
              <TableHead class="w-[35%] text-xs h-9">输出字段 (Output)</TableHead>
              <TableHead class="w-[5%] h-9"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="(row, idx) in mappings" :key="idx" class="group hover:bg-muted/30">
              <!-- Source Column -->
              <TableCell class="p-2 align-top">
                <div class="flex flex-col gap-1">
                  <!-- Use Select if we have discovered fields, otherwise Input -->
                  <div v-if="discoveredFields.length > 0 && row.type !== 'constant' && row.type !== 'expression'" class="relative">
                    <Select 
                      :model-value="row.source" 
                      @update:model-value="(v) => updateRow(idx, 'source', v)"
                    >
                      <SelectTrigger class="h-8 text-xs">
                        <SelectValue placeholder="选择字段..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem v-for="f in discoveredFields" :key="f" :value="f">{{ f }}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Input 
                    v-else-if="row.type !== 'constant' && row.type !== 'expression'"
                    :model-value="row.source" 
                    @update:model-value="(v) => updateRow(idx, 'source', v)"
                    placeholder="源字段名" 
                    class="h-8 text-xs font-mono"
                  />
                  
                  <!-- Expression Input -->
                  <Input 
                    v-if="row.type === 'expression'"
                    :model-value="row.expression"
                    @update:model-value="(v) => updateRow(idx, 'expression', v)"
                    placeholder="e.g. price * 0.8"
                    class="h-8 text-xs font-mono text-blue-600"
                  />
                  <!-- Constant Input -->
                  <Input 
                    v-if="row.type === 'constant'"
                    :model-value="row.expression"
                    @update:model-value="(v) => updateRow(idx, 'expression', v)"
                    placeholder="固定值"
                    class="h-8 text-xs font-mono text-purple-600"
                  />
                </div>
              </TableCell>

              <!-- Transformation Column -->
              <TableCell class="p-2 align-top">
                <div class="flex justify-center">
                  <Select 
                    :model-value="row.type" 
                    @update:model-value="(v) => updateRow(idx, 'type', v)"
                  >
                    <SelectTrigger class="h-8 w-[110px] text-xs bg-muted/20 border-dashed">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rename">直接映射 (->)</SelectItem>
                      <SelectItem value="constant">设为常量 (=)</SelectItem>
                      <SelectItem value="cast">类型转换 (as)</SelectItem>
                      <SelectItem value="expression">计算公式 (fx)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <!-- Cast Type Selector -->
                <div v-if="row.type === 'cast'" class="mt-1 flex justify-center">
                  <Select 
                    :model-value="row.expression || 'string'" 
                    @update:model-value="(v) => updateRow(idx, 'expression', v)"
                  >
                    <SelectTrigger class="h-6 w-[110px] text-[10px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="string">String</SelectItem>
                      <SelectItem value="int">Integer</SelectItem>
                      <SelectItem value="float">Float</SelectItem>
                      <SelectItem value="bool">Boolean</SelectItem>
                      <SelectItem value="datetime">Time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TableCell>

              <!-- Target Column -->
              <TableCell class="p-2 align-top">
                <div class="flex items-center gap-2">
                  <ArrowRight class="w-3 h-3 text-muted-foreground shrink-0 opacity-50" />
                  <Input 
                    :model-value="row.target" 
                    @update:model-value="(v) => updateRow(idx, 'target', v)"
                    placeholder="目标字段名" 
                    class="h-8 text-xs font-mono border-primary/20 focus-visible:border-primary"
                  />
                </div>
              </TableCell>

              <!-- Actions -->
              <TableCell class="p-2 align-top">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  class="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                  @click="removeRow(idx)"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </ScrollArea>

    <!-- Footer -->
    <div class="p-3 border-t bg-background">
      <Button 
        variant="outline" 
        class="w-full h-8 text-xs border-dashed text-muted-foreground hover:text-foreground"
        @click="addEmptyRow"
      >
        <Plus class="w-3.5 h-3.5 mr-1.5" />
        添加映射规则
      </Button>
    </div>
  </div>
</template>
