<script setup lang="ts">
import { ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Plus, Settings } from 'lucide-vue-next';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();

interface AlertRule {
  id: string;
  name: string;
  threshold: string;
  enabled: boolean;
}

const rules = ref<AlertRule[]>([
  {
    id: '1',
    name: 'ETL 失败告警',
    threshold: '阈值: 3 次',
    enabled: true,
  },
  {
    id: '2',
    name: 'API 响应超时',
    threshold: '阈值: 5000 ms',
    enabled: true,
  },
  {
    id: '3',
    name: '数据质量异常',
    threshold: '阈值: 0.8',
    enabled: false,
  },
]);

const onCheckedChange = (rule: AlertRule, checked: boolean) => {
  rule.enabled = checked;
  
  toast({
    title: rule.enabled ? '规则已启用' : '规则已禁用',
    description: `"${rule.name}" 状态已更新`,
    class: rule.enabled ? 'bg-green-500 text-white border-green-600' : '',
  });
};

const openSettings = (rule: AlertRule) => {
  toast({
    title: '配置规则',
    description: `正在配置 "${rule.name}"...`,
  });
};

const createRule = () => {
  toast({
    title: '新建规则',
    description: '打开新建规则模态框...',
  });
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-900">告警规则</h2>
        <p class="text-sm text-gray-500 mt-1">系统监控与异常告警配置</p>
      </div>
      <Button @click="createRule" class="gap-2">
        <Plus class="w-4 h-4" />
        新建规则
      </Button>
    </div>

    <!-- Rules List -->
    <div class="space-y-4">
      <div 
        v-for="rule in rules" 
        :key="rule.id"
        class="flex items-center justify-between p-4 px-6 rounded-lg border bg-white border-gray-200 shadow-sm transition-all hover:shadow-md"
        :class="{ 'opacity-75': !rule.enabled }"
      >
        <div class="flex items-center gap-6">
          <Checkbox 
            :checked="rule.enabled"
            @update:checked="(val) => onCheckedChange(rule, val)"
            class="w-6 h-6 border-2 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
          />
          <div>
            <div class="font-bold text-base text-gray-900">{{ rule.name }}</div>
            <div class="text-sm text-gray-500 mt-1.5 font-medium opacity-80">{{ rule.threshold }}</div>
          </div>
        </div>

        <div class="flex items-center gap-6">
          <Badge 
            variant="outline"
            class="px-3 py-1 text-xs font-medium rounded-md border"
            :class="rule.enabled 
              ? 'bg-green-900/20 text-green-500 border-green-900/30' 
              : 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700'"
          >
            {{ rule.enabled ? '已启用' : '已禁用' }}
          </Badge>
          
          <Button variant="ghost" size="icon" @click="openSettings(rule)" class="text-gray-400 hover:text-gray-900 h-8 w-8">
            <Settings class="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
