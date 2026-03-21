<script setup lang="ts">
import { reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();

const agents = reactive([
  { id: 1, name: 'DataAgent', type: '数据分析', status: true, description: '执行数据查询与分析任务' },
  { id: 2, name: 'SearchAgent', type: '信息检索', status: true, description: '全库检索与知识问答' },
  { id: 3, name: 'ReportAgent', type: '报告生成', status: false, description: '自动生成分析报告' },
]);

const saveConfig = () => {
  toast({
    title: '保存成功',
    description: '智能体配置已更新',
  });
};
</script>

<template>
  <div class="space-y-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">智能体配置</CardTitle>
        <CardDescription class="dark:text-slate-400">管理 Agent 智能体与工作流</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-3">
          <div v-for="agent in agents" :key="agent.id" 
               class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-800">
            <div class="space-y-0.5">
              <div class="flex items-center gap-2">
                <Label class="text-base dark:text-slate-200">{{ agent.name }}</Label>
                <span class="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary">{{ agent.type }}</span>
              </div>
              <p class="text-sm text-muted-foreground dark:text-slate-400">{{ agent.description }}</p>
            </div>
            <Switch :checked="agent.status" @update:checked="(val) => agent.status = val" />
          </div>
        </div>
        <div class="flex justify-end pt-4">
          <Button @click="saveConfig">保存配置</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
