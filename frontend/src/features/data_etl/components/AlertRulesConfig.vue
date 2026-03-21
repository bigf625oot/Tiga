<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Settings, AlertTriangle, Clock, Activity, Trash2, Pencil } from 'lucide-vue-next';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();

interface AlertRule {
  id: string;
  name: string;
  type: string;
  threshold: string;
  enabled: boolean;
  severity: 'low' | 'medium' | 'high';
}

const rules = ref<AlertRule[]>([
  {
    id: '1',
    name: 'ETL 失败告警',
    type: 'failure_count',
    threshold: '3',
    enabled: true,
    severity: 'high',
  },
  {
    id: '2',
    name: 'API 响应超时',
    type: 'latency',
    threshold: '5000',
    enabled: true,
    severity: 'medium',
  },
  {
    id: '3',
    name: '数据质量异常',
    type: 'data_quality',
    threshold: '0.8',
    enabled: false,
    severity: 'low',
  },
]);

const isDialogOpen = ref(false);
const editingRule = ref<AlertRule | null>(null);

const defaultForm = {
  name: '',
  type: 'failure_count',
  threshold: '',
  severity: 'medium' as const,
  enabled: true,
};

const form = reactive({ ...defaultForm });

const openCreateDialog = () => {
  editingRule.value = null;
  Object.assign(form, defaultForm);
  isDialogOpen.value = true;
};

const openEditDialog = (rule: AlertRule) => {
  editingRule.value = rule;
  Object.assign(form, {
    name: rule.name,
    type: rule.type,
    threshold: rule.threshold,
    severity: rule.severity,
    enabled: rule.enabled,
  });
  isDialogOpen.value = true;
};

const saveRule = () => {
  if (!form.name || !form.threshold) {
    toast({
      title: '参数错误',
      description: '规则名称和阈值不能为空',
      variant: 'destructive',
    });
    return;
  }

  if (editingRule.value) {
    // Update existing
    Object.assign(editingRule.value, form);
    toast({
      title: '规则已更新',
      description: `"${form.name}" 配置已保存`,
    });
  } else {
    // Create new
    rules.value.push({
      id: Date.now().toString(),
      name: form.name,
      type: form.type,
      threshold: form.threshold,
      enabled: form.enabled,
      severity: form.severity,
    });
    toast({
      title: '规则已创建',
      description: `"${form.name}" 已添加到告警列表`,
    });
  }
  isDialogOpen.value = false;
};

const deleteRule = (id: string) => {
  rules.value = rules.value.filter(r => r.id !== id);
  toast({
    title: '规则已删除',
    description: '告警规则已移除',
    variant: 'destructive',
  });
};

const onSwitchChange = (rule: AlertRule, val: boolean) => {
  rule.enabled = val;
  toast({
    title: val ? '规则已启用' : '规则已禁用',
    description: `"${rule.name}" 状态已更新`,
    class: val ? 'bg-green-500 text-white border-green-600' : '',
  });
};

const getIcon = (type: string) => {
  switch (type) {
    case 'failure_count': return AlertTriangle;
    case 'latency': return Clock;
    case 'data_quality': return Activity;
    default: return AlertTriangle;
  }
};
</script>

<template>
  <div class="w-full">
    <div class="flex items-center justify-end mb-6">
      <Sheet :open="isDialogOpen" @update:open="isDialogOpen = $event">
        <SheetTrigger as-child>
          <Button @click="openCreateDialog" class="gap-2 bg-blue-600 hover:bg-blue-700 text-white shadow-sm">
            <Plus class="w-4 h-4" />
            新建规则
          </Button>
        </SheetTrigger>
        <SheetContent class="sm:max-w-[500px] dark:bg-slate-950 dark:border-slate-800">
          <SheetHeader>
            <SheetTitle class="dark:text-slate-50">{{ editingRule ? '编辑规则' : '新建告警规则' }}</SheetTitle>
            <SheetDescription class="dark:text-slate-400">
              设置监控指标阈值，当系统指标超过设定值时触发告警。
            </SheetDescription>
          </SheetHeader>
          
          <div class="grid gap-6 py-8">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">规则名称</Label>
              <Input v-model="form.name" class="w-full dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" placeholder="例如：API 响应过慢" />
            </div>
            
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">监控指标</Label>
              <Select v-model="form.type">
                <SelectTrigger class="w-full dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                  <SelectValue placeholder="选择指标" />
                </SelectTrigger>
                <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                  <SelectItem value="failure_count" class="dark:text-slate-200 dark:focus:bg-slate-800">失败次数 (Count)</SelectItem>
                  <SelectItem value="latency" class="dark:text-slate-200 dark:focus:bg-slate-800">响应延迟 (ms)</SelectItem>
                  <SelectItem value="data_quality" class="dark:text-slate-200 dark:focus:bg-slate-800">数据质量评分 (0-1)</SelectItem>
                  <SelectItem value="cpu_usage" class="dark:text-slate-200 dark:focus:bg-slate-800">CPU 使用率 (%)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">触发阈值</Label>
              <Input v-model="form.threshold" class="w-full dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" placeholder="输入数值" />
            </div>

            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">告警等级</Label>
              <Select v-model="form.severity">
                <SelectTrigger class="w-full dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                  <SelectValue placeholder="选择等级" />
                </SelectTrigger>
                <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                  <SelectItem value="low" class="dark:text-slate-200 dark:focus:bg-slate-800">低 (Low)</SelectItem>
                  <SelectItem value="medium" class="dark:text-slate-200 dark:focus:bg-slate-800">中 (Medium)</SelectItem>
                  <SelectItem value="high" class="dark:text-slate-200 dark:focus:bg-slate-800">高 (High)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <SheetFooter class="absolute bottom-0 left-0 right-0 p-6 bg-white dark:bg-slate-950 border-t dark:border-slate-800">
            <Button variant="outline" @click="isDialogOpen = false" class="dark:bg-transparent dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-800">取消</Button>
            <Button @click="saveRule" class="bg-blue-600 hover:bg-blue-700 text-white">保存配置</Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
    
    <div class="w-full">
      <div v-if="rules.length === 0" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full mx-auto border rounded-xl bg-card/50">
        <div class="w-12 h-12 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
          <img src="/Placeholder/null_file.svg" alt="Placeholder" class="w-full h-full object-cover" />
        </div>
        <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">暂无告警规则</h3>
        <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">当前暂无告警规则，您可以点击下方按钮创建一个新的告警规则。</p>
        <Button @click="openCreateDialog" class="px-8 shadow-sm hover:scale-105 transition-transform bg-blue-600 hover:bg-blue-700 text-white">
          <Plus class="w-4 h-4 mr-2" />
          立即创建
        </Button>
      </div>
      
      <!-- Rules Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start">
        <Card 
          v-for="rule in rules" 
          :key="rule.id"
          class="group relative hover:border-blue-500/50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col justify-between h-[220px] bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 rounded-2xl"
          :class="{ 'opacity-60 grayscale-[0.2]': !rule.enabled }"
        >
          <!-- 卡片顶部色条装饰，用于区分优先级 -->
          <div class="absolute top-0 left-0 right-0 h-1.5" :class="{
            'bg-red-500': rule.severity === 'high',
            'bg-orange-400': rule.severity === 'medium',
            'bg-blue-400': rule.severity === 'low',
          }"></div>

          <!-- 悬浮操作层 -->
          <div class="absolute top-4 right-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0 z-10">
            <Button variant="outline" size="icon" class="h-8 w-8  bg-white/90 backdrop-blur-sm  hover:text-blue-600 hover:border-blue-200 dark:bg-slate-900/90" @click.stop="openEditDialog(rule)">
              <Pencil class="w-3.5 h-3.5" />
            </Button>
            <Button variant="outline" size="icon" class="h-8 w-8  bg-white/90 backdrop-blur-sm  hover:text-red-600 hover:border-red-200 dark:bg-slate-900/90" @click.stop="deleteRule(rule.id)">
              <Trash2 class="w-3.5 h-3.5" />
            </Button>
          </div>

          <CardContent class="p-6 flex-1 flex flex-col h-full cursor-pointer pb-0" @click="openEditDialog(rule)">
            <!-- 头部：图标与标题 -->
            <div class="flex items-center gap-4 mb-2">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-transform group-hover:scale-105" :class="[
                rule.type === 'failure_count' ? 'bg-red-50 text-red-500 dark:bg-red-900/20' : 
                rule.type === 'latency' ? 'bg-orange-50 text-orange-500 dark:bg-orange-900/20' : 
                'bg-blue-50 text-blue-500 dark:bg-blue-900/20'
              ]">
                <component :is="getIcon(rule.type)" class="w-6 h-6" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-[15px] text-slate-800 dark:text-slate-100 truncate mb-1" :title="rule.name">
                  {{ rule.name }}
                </h3>
                <div class="flex items-center gap-1.5">
                  <div class="w-1.5 h-1.5 rounded-full" :class="rule.enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'"></div>
                  <span class="text-[11px] font-medium" :class="rule.enabled ? 'text-emerald-600 dark:text-emerald-500' : 'text-slate-400'">{{ rule.enabled ? '已启用' : '已禁用' }}</span>
                </div>
              </div>
            </div>

            <!-- 中部：触发条件 -->
            <div class="flex-1 flex flex-col justify-center mt-1">
              <div class="text-[11px] text-slate-400 font-medium mb-1.5">触发条件</div>
              <div class="flex items-baseline gap-1 text-slate-800 dark:text-slate-100">
                <span class="text-xl font-bold font-mono">{{ rule.type === 'latency' ? '>' : '≥' }}</span>
                <span class="text-3xl font-bold tracking-tight">{{ rule.threshold }}</span>
                <span class="text-xs font-medium text-slate-500 ml-1">{{ rule.type === 'latency' ? 'ms' : rule.type === 'failure_count' ? '次' : '' }}</span>
              </div>
              
              <div class="mt-4 flex items-center justify-between pb-2">
                 <Badge 
                    variant="outline" 
                    class="text-[10px] font-medium px-2 py-0.5 h-5 rounded-full bg-transparent"
                    :class="{
                      'text-red-500 border-red-200 dark:border-red-900/50': rule.severity === 'high',
                      'text-orange-500 border-orange-200 dark:border-orange-900/50': rule.severity === 'medium',
                      'text-blue-500 border-blue-200 dark:border-blue-900/50': rule.severity === 'low',
                    }"
                  >
                    {{ rule.severity === 'high' ? '高优先级' : rule.severity === 'medium' ? '中优先级' : '低优先级' }}
                  </Badge>

                  <div @click.stop>
                    <Switch 
                      :checked="rule.enabled"
                      @update:checked="(val) => onSwitchChange(rule, val)"
                      class="z-50"
                    />
                  </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
