<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Plus, Trash2, ArrowUp, ArrowDown, Code, ListFilter, Play, 
  Type, Eraser, Replace, Shield, FileText 
} from 'lucide-vue-next';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardTitle, CardDescription} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

// --- Types ---
interface CleaningRule {
  id: string;
  type: string;
  name: string;
  params: Record<string, any>;
  enabled: boolean;
}

interface RuleDefinition {
  type: string;
  name: string;
  category: 'format' | 'remove' | 'replace' | 'mask' | 'filter';
  description: string;
  defaultParams?: Record<string, any>;
  paramSchema?: Array<{
    key: string;
    label: string;
    type: 'text' | 'number' | 'boolean';
    placeholder?: string;
  }>;
}

// --- Props & Emits ---
const props = defineProps<{
  code?: string;
  rules?: CleaningRule[];
}>();

const emit = defineEmits<{
  (e: 'update:code', value: string): void;
  (e: 'update:rules', value: CleaningRule[]): void;
}>();

// --- State ---
const mode = ref<'visual' | 'code'>('visual');
const localRules = ref<CleaningRule[]>(props.rules ? JSON.parse(JSON.stringify(props.rules)) : []);
const localCode = ref(props.code || '');
const previewInput = ref('Example Text: Hello   World! Contact: test@example.com 123-456-7890');
const isPreviewOpen = ref(true);

// --- Constants: Rule Definitions (20+ Rules) ---
const ruleDefinitions: RuleDefinition[] = [
  // Format
  { type: 'trim', name: '去除首尾空格', category: 'format', description: '去除文本开头和结尾的空白字符' },
  { type: 'normalize_whitespace', name: '标准化空格', category: 'format', description: '将连续的多个空格替换为单个空格' },
  { type: 'lowercase', name: '转小写', category: 'format', description: '将所有文本转换为小写字母' },
  { type: 'uppercase', name: '转大写', category: 'format', description: '将所有文本转换为大写字母' },
  { type: 'titlecase', name: '标题大写', category: 'format', description: '将每个单词的首字母转换为大写' },
  { type: 'pad_start', name: '左填充', category: 'format', description: '在文本左侧填充字符以达到指定长度', paramSchema: [{ key: 'length', label: '长度', type: 'number' }, { key: 'char', label: '字符', type: 'text', placeholder: ' ' }] },
  { type: 'pad_end', name: '右填充', category: 'format', description: '在文本右侧填充字符以达到指定长度', paramSchema: [{ key: 'length', label: '长度', type: 'number' }, { key: 'char', label: '字符', type: 'text', placeholder: ' ' }] },
  
  // Remove
  { type: 'remove_punctuation', name: '去除标点', category: 'remove', description: '移除所有标点符号' },
  { type: 'remove_numbers', name: '去除数字', category: 'remove', description: '移除所有数字字符' },
  { type: 'remove_html', name: '去除 HTML 标签', category: 'remove', description: '移除文本中的 HTML 标签' },
  { type: 'remove_urls', name: '去除 URL', category: 'remove', description: '移除文本中的网址链接' },
  { type: 'remove_emails', name: '去除邮箱', category: 'remove', description: '移除文本中的电子邮箱地址' },
  { type: 'remove_emojis', name: '去除表情符号', category: 'remove', description: '移除文本中的表情符号' },
  { type: 'remove_stop_words', name: '去除停用词', category: 'remove', description: '移除常见停用词（支持中/英）', paramSchema: [{ key: 'lang', label: '语言', type: 'text', placeholder: 'en' }] },

  // Replace
  { type: 'replace', name: '文本替换', category: 'replace', description: '将指定文本替换为新文本', paramSchema: [{ key: 'old', label: '查找', type: 'text' }, { key: 'new', label: '替换为', type: 'text' }] },
  { type: 'regex_replace', name: '正则替换', category: 'replace', description: '使用正则表达式进行匹配和替换', paramSchema: [{ key: 'pattern', label: '正则', type: 'text' }, { key: 'replacement', label: '替换为', type: 'text' }] },
  { type: 'fill_na', name: '空值填充', category: 'replace', description: '填充空值或 NULL 值', paramSchema: [{ key: 'value', label: '填充值', type: 'text' }] },

  // Filter/Keep
  { type: 'keep_numeric', name: '仅保留数字', category: 'filter', description: '移除除数字以外的所有字符' },
  { type: 'keep_alpha', name: '仅保留字母', category: 'filter', description: '移除除字母以外的所有字符' },
  { type: 'truncate', name: '截断文本', category: 'filter', description: '将文本截断到指定长度', paramSchema: [{ key: 'length', label: '长度', type: 'number' }] },

  // Mask
  { type: 'mask_email', name: '邮箱脱敏', category: 'mask', description: '对电子邮箱地址进行脱敏处理' },
  { type: 'mask_phone', name: '手机号脱敏', category: 'mask', description: '对手机号码进行脱敏处理' },
];

const categories = [
  { id: 'format', label: '格式化', icon: Type },
  { id: 'remove', label: '移除', icon: Eraser },
  { id: 'replace', label: '替换', icon: Replace },
  { id: 'filter', label: '过滤', icon: FileText },
  { id: 'mask', label: '脱敏', icon: Shield },
];

// --- Actions ---

const addRule = (def: RuleDefinition) => {
  const newRule: CleaningRule = {
    id: Math.random().toString(36).substring(7),
    type: def.type,
    name: def.name,
    params: def.defaultParams ? { ...def.defaultParams } : {},
    enabled: true,
  };
  
  // Initialize params from schema if not in defaultParams
  if (def.paramSchema) {
    def.paramSchema.forEach(p => {
      if (newRule.params[p.key] === undefined) {
        newRule.params[p.key] = p.type === 'number' ? 0 : '';
      }
    });
  }

  localRules.value.push(newRule);
  updateCode();
};

const removeRule = (index: number) => {
  localRules.value.splice(index, 1);
  updateCode();
};

const moveRule = (index: number, direction: -1 | 1) => {
  if (index + direction < 0 || index + direction >= localRules.value.length) return;
  const temp = localRules.value[index];
  localRules.value[index] = localRules.value[index + direction];
  localRules.value[index + direction] = temp;
  updateCode();
};

// --- Code Generation ---
const generatePythonCode = (rules: CleaningRule[]) => {
  if (!rules.length) return '';
  
  let code = `# Auto-generated cleaning rules\n`;
  code += `def clean_text(text):\n`;
  code += `    if not text: return ""\n`;
  
  rules.forEach(rule => {
    if (!rule.enabled) return;
    
    code += `    # ${rule.name}\n`;
    switch (rule.type) {
      case 'trim':
        code += `    text = text.strip()\n`;
        break;
      case 'normalize_whitespace':
        code += `    import re\n    text = re.sub(r'\\s+', ' ', text).strip()\n`;
        break;
      case 'lowercase':
        code += `    text = text.lower()\n`;
        break;
      case 'uppercase':
        code += `    text = text.upper()\n`;
        break;
      case 'titlecase':
        code += `    text = text.title()\n`;
        break;
      case 'replace':
        code += `    text = text.replace('${rule.params.old}', '${rule.params.new}')\n`;
        break;
      case 'regex_replace':
        code += `    import re\n    text = re.sub(r'${rule.params.pattern}', '${rule.params.replacement}', text)\n`;
        break;
      case 'remove_punctuation':
        code += `    import string\n    text = text.translate(str.maketrans('', '', string.punctuation))\n`;
        break;
      case 'remove_numbers':
        code += `    import re\n    text = re.sub(r'\\d+', '', text)\n`;
        break;
      case 'remove_html':
        code += `    import re\n    text = re.sub(r'<[^>]+>', '', text)\n`;
        break;
      case 'remove_urls':
        code += `    import re\n    text = re.sub(r'http\\S+|www.\\S+', '', text)\n`;
        break;
      case 'remove_emails':
        code += `    import re\n    text = re.sub(r'\\S+@\\S+', '', text)\n`;
        break;
      case 'keep_numeric':
        code += `    import re\n    text = re.sub(r'[^0-9]', '', text)\n`;
        break;
      case 'keep_alpha':
        code += `    import re\n    text = re.sub(r'[^a-zA-Z]', '', text)\n`;
        break;
      case 'truncate':
        code += `    text = text[:${rule.params.length}]\n`;
        break;
      case 'pad_start':
        code += `    text = text.rjust(${rule.params.length}, '${rule.params.char}')\n`;
        break;
      case 'pad_end':
        code += `    text = text.ljust(${rule.params.length}, '${rule.params.char}')\n`;
        break;
      case 'mask_email':
        code += `    # Simple masking logic\n    if '@' in text:\n        u, d = text.split('@', 1)\n        text = u[:2] + '***' + '@' + d\n`;
        break;
      // Add more cases as needed
      default:
        code += `    # TODO: Implement ${rule.type}\n`;
    }
  });
  
  code += `    return text\n`;
  return code;
};

const updateCode = () => {
  if (mode.value !== 'visual') return;
  const code = generatePythonCode(localRules.value);
  localCode.value = code;
  emit('update:code', code);
  emit('update:rules', localRules.value);
};

// --- Preview Logic (JS Simulation) ---
const previewOutput = computed(() => {
  let text = previewInput.value;
  if (!text) return '';

  localRules.value.forEach(rule => {
    if (!rule.enabled) return;

    try {
      switch (rule.type) {
        case 'trim':
          text = text.trim();
          break;
        case 'normalize_whitespace':
          text = text.replace(/\s+/g, ' ').trim();
          break;
        case 'lowercase':
          text = text.toLowerCase();
          break;
        case 'uppercase':
          text = text.toUpperCase();
          break;
        case 'titlecase':
          text = text.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
          break;
        case 'replace':
          text = text.split(rule.params.old || '').join(rule.params.new || '');
          break;
        case 'regex_replace':
          if (rule.params.pattern) {
             try {
                const re = new RegExp(rule.params.pattern, 'g');
                text = text.replace(re, rule.params.replacement || '');
             } catch (e) { /* ignore invalid regex */ }
          }
          break;
        case 'remove_punctuation':
          text = text.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "");
          break;
        case 'remove_numbers':
          text = text.replace(/\d+/g, '');
          break;
        case 'remove_html':
          text = text.replace(/<[^>]*>?/gm, '');
          break;
        case 'remove_urls':
          text = text.replace(/(https?:\/\/[^\s]+)/g, '');
          break;
        case 'remove_emails':
          text = text.replace(/[\w\.-]+@[\w\.-]+\.\w+/g, '');
          break;
        case 'keep_numeric':
          text = text.replace(/[^0-9]/g, '');
          break;
        case 'keep_alpha':
          text = text.replace(/[^a-zA-Z]/g, '');
          break;
        case 'truncate':
          if (rule.params.length) text = text.substring(0, parseInt(rule.params.length));
          break;
        case 'pad_start':
           text = text.padStart(parseInt(rule.params.length) || 0, rule.params.char || ' ');
           break;
        case 'pad_end':
           text = text.padEnd(parseInt(rule.params.length) || 0, rule.params.char || ' ');
           break;
        case 'mask_email':
           text = text.replace(/([\w\.-]+)(@[\w\.-]+\.\w+)/g, (match, p1, p2) => {
             return p1.substring(0, 2) + '***' + p2;
           });
           break;
      }
    } catch (e) {
      console.error(`Error applying rule ${rule.type}`, e);
    }
  });

  return text;
});

// --- Watchers ---
watch(() => props.rules, (newVal) => {
  if (newVal && JSON.stringify(newVal) !== JSON.stringify(localRules.value)) {
    localRules.value = JSON.parse(JSON.stringify(newVal));
  }
}, { deep: true });

watch(localCode, (newVal) => {
  if (mode.value === 'code') {
    emit('update:code', newVal);
  }
});

// Initialize
if (localRules.value.length === 0 && !localCode.value) {
  // Add a default rule if empty
  // addRule(ruleDefinitions.find(r => r.type === 'trim')!);
}
</script>

<template>
  <div class="flex flex-col h-full bg-background border rounded-lg overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center justify-between p-3 border-b bg-muted/30">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-medium">清洗规则</h3>
        <div class="flex bg-muted rounded-md p-0.5 border">
          <button 
            @click="mode = 'visual'"
            class="px-2 py-1 text-xs rounded-sm transition-all flex items-center gap-1"
            :class="mode === 'visual' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'"
          >
            <ListFilter class="w-3 h-3" />
            可视化
          </button>
          <button 
            @click="mode = 'code'"
            class="px-2 py-1 text-xs rounded-sm transition-all flex items-center gap-1"
            :class="mode === 'code' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'"
          >
            <Code class="w-3 h-3" />
            代码
          </button>
        </div>
      </div>
      
      <Dialog v-if="mode === 'visual'">
        <DialogTrigger as-child>
          <Button size="sm" class="h-8 gap-1">
            <Plus class="w-3 h-3" />
            添加规则
          </Button>
        </DialogTrigger>
        <DialogContent class="sm:max-w-[800px] max-h-[85vh] flex flex-col p-0 gap-0">
          <div class="p-6 pb-4 border-b">
             <DialogHeader>
              <DialogTitle>选择清洗规则</DialogTitle>
            </DialogHeader>
          </div>
          
          <ScrollArea class="p-6 pt-4 h-[600px] min-h-0">
             <div class="space-y-8">
                <div v-for="cat in categories" :key="cat.id" class="space-y-3">
                   <div class="flex items-center gap-2 text-sm font-semibold text-foreground">
                     <div class="p-1.5 bg-primary/10 rounded-md">
                       <component :is="cat.icon" class="w-4 h-4 text-primary" />
                     </div>
                     {{ cat.label }}
                   </div>
                   <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                     <Card
                       v-for="rule in ruleDefinitions.filter(r => r.category === cat.id)"
                       :key="rule.type"
                       class="cursor-pointer hover:border-primary/50 hover:bg-muted/30 hover:shadow-sm transition-all group border-muted shadow-none"
                       @click="addRule(rule)"
                     >
                       <CardHeader class="p-4 space-y-1.5">
                         <CardTitle class="text-sm font-medium group-hover:text-primary transition-colors flex justify-between items-center">
                           {{ rule.name }}
                           <Plus class="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all text-primary" />
                         </CardTitle>
                         <CardDescription class="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                           {{ rule.description }}
                         </CardDescription>
                       </CardHeader>
                     </Card>
                   </div>
                </div>
             </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>

    <!-- Main Content Area -->
    <ScrollArea class="flex-1 bg-muted/10">
      <!-- Visual Mode: Rule List -->
      <div v-if="mode === 'visual'" class="p-4 space-y-3">
        <div v-if="localRules.length === 0" class="text-center py-8 text-muted-foreground text-sm">
          <div class="mb-2 flex justify-center"><ListFilter class="w-8 h-8 opacity-20" /></div>
          暂无规则，请点击右上角添加
        </div>

        <div 
          v-for="(rule, index) in localRules" 
          :key="rule.id"
          class="group flex flex-col gap-2 p-3 bg-card border rounded-md shadow-sm transition-all hover:shadow-md"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Switch 
                :checked="rule.enabled" 
                @update:checked="(v) => { rule.enabled = v; updateCode(); }" 
                class="scale-75"
              />
              <span class="text-sm font-medium" :class="{ 'opacity-50': !rule.enabled }">
                {{ rule.name }}
              </span>
              <span class="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {{ rule.type }}
              </span>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button variant="ghost" size="icon" class="h-6 w-6" :disabled="index === 0" @click="moveRule(index, -1)">
                <ArrowUp class="w-3 h-3" />
              </Button>
              <Button variant="ghost" size="icon" class="h-6 w-6" :disabled="index === localRules.length - 1" @click="moveRule(index, 1)">
                <ArrowDown class="w-3 h-3" />
              </Button>
              <Button variant="ghost" size="icon" class="h-6 w-6 text-destructive hover:text-destructive" @click="removeRule(index)">
                <Trash2 class="w-3 h-3" />
              </Button>
            </div>
          </div>

          <!-- Params Inputs -->
          <div v-if="ruleDefinitions.find(r => r.type === rule.type)?.paramSchema" class="grid grid-cols-2 gap-2 mt-1 pl-9">
            <div 
              v-for="param in ruleDefinitions.find(r => r.type === rule.type)?.paramSchema" 
              :key="param.key"
              class="space-y-1"
            >
              <Label class="text-[10px] text-muted-foreground uppercase">{{ param.label }}</Label>
              <Input 
                v-model="rule.params[param.key]"
                :type="param.type === 'number' ? 'number' : 'text'"
                :placeholder="param.placeholder"
                class="h-7 text-xs"
                @input="updateCode"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Code Mode: Editor -->
      <div v-else class="h-full">
        <textarea 
          v-model="localCode"
          class="w-full h-full min-h-[300px] p-4 font-mono text-xs bg-transparent border-none resize-none focus:outline-none"
          placeholder="# 在此输入 Python 清洗代码..."
        ></textarea>
      </div>
    </ScrollArea>

    <!-- Preview Panel -->
    <div class="border-t bg-card">
      <div 
        class="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-muted/50 transition-colors"
        @click="isPreviewOpen = !isPreviewOpen"
      >
        <div class="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Play class="w-3 h-3" />
          实时预览
        </div>
        <div class="text-[10px] text-muted-foreground">
          {{ isPreviewOpen ? '收起' : '展开' }}
        </div>
      </div>
      
      <div v-if="isPreviewOpen" class="grid grid-cols-2 gap-0 border-t divide-x h-32">
        <div class="flex flex-col">
          <div class="px-2 py-1 text-[10px] text-muted-foreground bg-muted/20 border-b">输入 (Input)</div>
          <textarea 
            v-model="previewInput"
            class="flex-1 w-full p-2 text-xs font-mono bg-transparent border-none resize-none focus:outline-none"
          ></textarea>
        </div>
        <div class="flex flex-col bg-muted/10">
          <div class="px-2 py-1 text-[10px] text-muted-foreground bg-muted/20 border-b">输出 (Output)</div>
          <div class="flex-1 w-full p-2 text-xs font-mono overflow-auto whitespace-pre-wrap break-all">
            <span v-if="previewOutput === previewInput" class="text-muted-foreground/50">{{ previewOutput }}</span>
            <span v-else class="text-green-600 dark:text-green-400 font-medium">{{ previewOutput }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
