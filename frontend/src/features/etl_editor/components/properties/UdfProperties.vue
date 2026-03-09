<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { usePipelineStore } from '../../composables/usePipelineStore';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  AlertCircle, 
  Code2, 
  Play, 
  CheckCircle2, 
  Terminal,
  Plus,
  Trash2,
  X
} from 'lucide-vue-next';

// --- Monaco Editor Import (Dynamic to avoid SSR issues if any, though this is SPA) ---
// In a real project, we'd use a proper Monaco Editor wrapper component.
// For now, we'll use a Textarea with monospace font as a fallback/simplified version,
// or we can try to use the installed @guolao/vue-monaco-editor if configured.
// Let's stick to a enhanced Textarea for stability in this demo context, 
// but style it to look like an editor.

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

// --- State ---
const activeTab = ref('code'); // code, libraries, output
const executionStatus = ref<'idle' | 'running' | 'success' | 'error'>('idle');
const executionOutput = ref('');
const executionTime = ref(0);
const isConsoleVisible = computed(() => executionStatus.value !== 'idle');

// --- Default Code Template ---
const defaultCode = `def process(record):
    """
    Process a single record.
    Args:
        record (dict): Input data record
    Returns:
        dict: Processed record, or None to filter out
    """
    # Example: Add a timestamp
    # record['processed_at'] = time.time()
    
    # Example: Simple calculation
    # record['total'] = record['price'] * record['quantity']
    
    return record
`;

onMounted(() => {
  if (!config.value.code) {
    updateConfig('code', defaultCode);
  }
});

// --- Dependency Management ---
const newLib = ref('');
const addLibrary = () => {
  const val = newLib.value.trim();
  if (!val) return;
  const current = config.value.libraries || [];
  if (!current.includes(val)) {
    updateConfig('libraries', [...current, val]);
  }
  newLib.value = '';
};
const removeLibrary = (index: number) => {
  const current = [...(config.value.libraries || [])];
  current.splice(index, 1);
  updateConfig('libraries', current);
};

// --- Mock Execution ---
const runTest = () => {
  executionStatus.value = 'running';
  executionOutput.value = 'Running test with sample data...\n';
  const startTime = performance.now();
  
  setTimeout(() => {
    try {
      // Very basic validation: check for syntax errors (mock)
      if (config.value.code.includes('error')) {
        throw new Error('SyntaxError: invalid syntax');
      }
      
      executionOutput.value += `
> pip install ${config.value.libraries?.join(' ') || 'no-deps'}
> Executing user function...
> Input: {"id": 1, "value": "test"}
> Output: {"id": 1, "value": "test", "processed": true}

Process finished successfully.
`;
      executionStatus.value = 'success';
    } catch (e: any) {
      executionOutput.value += `\nTraceback (most recent call last):\n  File "udf.py", line 10, in <module>\n${e.message}`;
      executionStatus.value = 'error';
    } finally {
      executionTime.value = performance.now() - startTime;
    }
  }, 1000);
};

// --- Validation ---
const validationErrors = computed(() => {
  const errors: string[] = [];
  if (!config.value.code?.trim()) errors.push('代码内容不能为空');
  return errors;
});
</script>

<template>
  <div class="flex flex-col w-full min-h-[600px] bg-background/50 border rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b bg-muted/20">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="p-1.5 bg-blue-500/10 rounded-md">
            <Code2 class="w-4 h-4 text-blue-500" />
          </div>
          <div>
            <h3 class="text-sm font-medium">Python UDF</h3>
            <p class="text-[10px] text-muted-foreground">编写自定义 Python 函数处理数据</p>
          </div>
        </div>
        <Button 
          size="sm" 
          :variant="executionStatus === 'running' ? 'secondary' : 'default'"
          class="h-7 text-xs gap-1.5"
          @click="runTest"
          :disabled="executionStatus === 'running'"
        >
          <Play class="w-3 h-3 fill-current" />
          测试运行
        </Button>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="flex items-center border-b px-4 py-2 gap-4 bg-background text-xs">
      <button 
        class="flex items-center gap-1.5 hover:text-primary transition-colors"
        :class="activeTab === 'code' ? 'text-primary font-medium' : 'text-muted-foreground'"
        @click="activeTab = 'code'"
      >
        <Code2 class="w-3.5 h-3.5" />
        代码编辑器
      </button>
      <button 
        class="flex items-center gap-1.5 hover:text-primary transition-colors"
        :class="activeTab === 'libraries' ? 'text-primary font-medium' : 'text-muted-foreground'"
        @click="activeTab = 'libraries'"
      >
        <Badge variant="secondary" class="text-[10px] px-1 h-4 min-w-[1.2rem] flex justify-center">{{ config.libraries?.length || 0 }}</Badge>
        依赖管理
      </button>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-h-0 bg-background">
      
      <!-- Code Editor View -->
      <div v-show="activeTab === 'code'" class="flex-1 flex flex-col relative">
        <Textarea 
          class="flex-1 border-0 rounded-none resize-none font-mono text-xs p-4 leading-relaxed focus-visible:ring-0 bg-[#1e1e1e] text-[#d4d4d4]"
          spellcheck="false"
          :model-value="config.code"
          @update:model-value="(v) => updateConfig('code', v)"
          placeholder="# 在此输入 Python 代码..."
        />
        <div class="absolute bottom-2 right-4 text-[10px] text-muted-foreground opacity-50 pointer-events-none">
          Python 3.11 Runtime
        </div>
      </div>

      <!-- Dependencies View -->
      <div v-show="activeTab === 'libraries'" class="flex-1 p-4 space-y-4 overflow-y-auto">
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-sm font-medium">第三方依赖 (Pip)</CardTitle>
            <CardDescription class="text-xs">添加运行所需的 Python 包，如 `numpy`, `pandas`</CardDescription>
          </CardHeader>
          <CardContent class="space-y-3">
            <div class="flex gap-2">
              <Input 
                v-model="newLib" 
                placeholder="输入包名 (e.g. pandas==2.0.0)" 
                class="h-8 text-xs" 
                @keyup.enter="addLibrary" 
              />
              <Button size="sm" variant="secondary" class="h-8 w-8 p-0" @click="addLibrary">
                <Plus class="w-4 h-4" />
              </Button>
            </div>
            <div class="flex flex-col gap-2">
              <div 
                v-for="(lib, idx) in (config.libraries || [])" 
                :key="idx"
                class="flex items-center justify-between p-2 rounded-md border bg-muted/10 text-xs"
              >
                <div class="flex items-center gap-2">
                  <div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                  <span class="font-mono">{{ lib }}</span>
                </div>
                <Trash2 
                  class="w-3.5 h-3.5 cursor-pointer text-muted-foreground hover:text-destructive transition-colors" 
                  @click="removeLibrary(Number(idx))" 
                />
              </div>
              <div v-if="!(config.libraries?.length)" class="text-center py-8 text-xs text-muted-foreground">
                暂无依赖，使用标准库运行
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Output Console (Always visible at bottom if not idle) -->
      <div 
        v-if="isConsoleVisible" 
        class="border-t bg-black/95 text-white flex flex-col transition-all duration-300"
        :class="isConsoleVisible ? 'h-[160px]' : 'h-0 overflow-hidden'"
      >
        <div class="flex items-center justify-between px-3 py-1.5 border-b border-white/10 bg-white/5">
          <div class="flex items-center gap-2 text-[10px] font-medium text-muted-foreground">
            <Terminal class="w-3 h-3" />
            控制台输出
          </div>
          <div class="flex items-center gap-2">
            <span v-if="executionTime > 0" class="text-[10px] text-muted-foreground">{{ executionTime.toFixed(0) }}ms</span>
            <button class="hover:text-white" @click="executionStatus = 'idle'">
              <X class="w-3 h-3" />
            </button>
          </div>
        </div>
        <div class="flex-1 p-3 overflow-auto font-mono text-[10px] leading-relaxed whitespace-pre-wrap text-gray-300 selection:bg-white/20">
          {{ executionOutput }}
        </div>
        <div 
          class="h-1 w-full"
          :class="{
            'bg-yellow-500 animate-pulse': executionStatus === 'running',
            'bg-green-500': executionStatus === 'success',
            'bg-red-500': executionStatus === 'error'
          }"
        ></div>
      </div>
    </div>
  </div>
</template>
