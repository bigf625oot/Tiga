<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Settings, AlertTriangle, Clock, Activity, Trash2 } from 'lucide-vue-next';
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
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold tracking-tight dark:text-slate-50">告警规则</h2>
        <p class="text-sm text-muted-foreground mt-1 dark:text-slate-400">配置系统监控指标与异常通知规则</p>
      </div>
      
      <Dialog :open="isDialogOpen" @update:open="isDialogOpen = $event">
        <DialogTrigger as-child>
          <Button @click="openCreateDialog" class="gap-2">
            <Plus class="w-4 h-4" />
            新建规则
          </Button>
        </DialogTrigger>
        <DialogContent class="sm:max-w-[500px] dark:bg-slate-950 dark:border-slate-800">
          <DialogHeader>
            <DialogTitle class="dark:text-slate-50">{{ editingRule ? '编辑规则' : '新建告警规则' }}</DialogTitle>
            <DialogDescription class="dark:text-slate-400">
              设置监控指标阈值，当系统指标超过设定值时触发告警。
            </DialogDescription>
          </DialogHeader>
          
          <div class="grid gap-6 py-4">
            <div class="grid grid-cols-4 items-center gap-4">
              <Label class="text-right dark:text-slate-200">规则名称</Label>
              <Input v-model="form.name" class="col-span-3 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" placeholder="例如：API 响应过慢" />
            </div>
            
            <div class="grid grid-cols-4 items-center gap-4">
              <Label class="text-right dark:text-slate-200">监控指标</Label>
              <Select v-model="form.type">
                <SelectTrigger class="col-span-3 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
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

            <div class="grid grid-cols-4 items-center gap-4">
              <Label class="text-right dark:text-slate-200">触发阈值</Label>
              <Input v-model="form.threshold" class="col-span-3 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" placeholder="输入数值" />
            </div>

            <div class="grid grid-cols-4 items-center gap-4">
              <Label class="text-right dark:text-slate-200">告警等级</Label>
              <Select v-model="form.severity">
                <SelectTrigger class="col-span-3 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
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

          <DialogFooter>
            <Button variant="outline" @click="isDialogOpen = false" class="dark:bg-transparent dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-800">取消</Button>
            <Button @click="saveRule">保存配置</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>

    <!-- Rules Grid -->
    <div class="grid grid-cols-1 gap-4">
      <Card 
        v-for="rule in rules" 
        :key="rule.id"
        class="transition-all hover:shadow-md dark:bg-slate-950 dark:border-slate-800"
        :class="{ 'opacity-75 bg-muted/30 dark:bg-slate-900/30': !rule.enabled }"
      >
        <CardContent class="p-6 flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="p-3 rounded-full bg-primary/10 text-primary">
              <component :is="getIcon(rule.type)" class="w-5 h-5" />
            </div>
            
            <div class="space-y-1">
              <div class="flex items-center gap-3">
                <h3 class="font-semibold text-base dark:text-slate-50">{{ rule.name }}</h3>
                <Badge 
                  variant="outline" 
                  class="capitalize text-[10px] px-2 py-0.5 h-5"
                  :class="{
                    'text-red-600 border-red-200 bg-red-50 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800': rule.severity === 'high',
                    'text-orange-600 border-orange-200 bg-orange-50 dark:bg-orange-900/20 dark:text-orange-400 dark:border-orange-800': rule.severity === 'medium',
                    'text-blue-600 border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800': rule.severity === 'low',
                  }"
                >
                  {{ rule.severity }}
                </Badge>
              </div>
              <p class="text-sm text-muted-foreground dark:text-slate-400">
                触发条件: {{ rule.type === 'latency' ? '>' : '≥' }} {{ rule.threshold }} 
                <span v-if="rule.type === 'latency'">ms</span>
                <span v-else-if="rule.type === 'failure_count'">次</span>
              </p>
            </div>
          </div>

          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <Label class="text-xs text-muted-foreground font-normal mr-2 dark:text-slate-400">
                {{ rule.enabled ? '已启用' : '已禁用' }}
              </Label>
              <Switch 
                :checked="rule.enabled"
                @update:checked="(val) => onSwitchChange(rule, val)"
              />
            </div>
            
            <div class="h-8 w-px bg-border mx-2 dark:bg-slate-800"></div>
            
            <div class="flex items-center gap-2">
              <Button variant="ghost" size="icon" @click="openEditDialog(rule)">
                <Settings class="w-4 h-4 text-muted-foreground hover:text-foreground dark:text-slate-400 dark:hover:text-slate-200" />
              </Button>
              <Button variant="ghost" size="icon" class="text-muted-foreground hover:text-destructive dark:text-slate-400 dark:hover:text-red-400" @click="deleteRule(rule.id)">
                <Trash2 class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
