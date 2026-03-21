<script setup lang="ts">
import { reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/toast/use-toast';
import { useI18n } from '@/locales';

const { locale, setLocale } = useI18n();
const { toast } = useToast();

const languages = [
  { code: 'zh-CN', name: '简体中文' }
  // { code: 'en-US', name: 'English' },
  // { code: 'ja-JP', name: '日本語' },
  // { code: 'ko-KR', name: '한국어' }
] as const;

const config = reactive({
  language: locale,
  logLevel: 'INFO',
  kgQ2sEnable: true,
  agnoMonitoring: true
});

const saveConfig = () => {
  setLocale(config.language);
  toast({
    title: '保存成功',
    description: '基础业务设置已更新',
  });
};
</script>

<template>
  <div class="space-y-6 px-0 pt-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">基础业务设置</CardTitle>
        <CardDescription class="dark:text-slate-400">配置系统本地化、日志与核心业务开关</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">系统语言 (Language)</Label>
            <Select v-model="config.language">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择语言" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem v-for="lang in languages" :key="lang.code" :value="lang.code" class="dark:text-slate-200">
                  {{ lang.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">日志级别 (Log Level)</Label>
            <Select v-model="config.logLevel">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择日志级别" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="DEBUG" class="dark:text-slate-200">DEBUG</SelectItem>
                <SelectItem value="INFO" class="dark:text-slate-200">INFO</SelectItem>
                <SelectItem value="WARNING" class="dark:text-slate-200">WARNING</SelectItem>
                <SelectItem value="ERROR" class="dark:text-slate-200">ERROR</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- <div class="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
          <h4 class="text-sm font-medium dark:text-slate-200">功能开关</h4>
          
          <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-800">
            <div class="space-y-0.5">
              <Label class="text-base dark:text-slate-200">智能问数 (KG_Q2S_ENABLE)</Label>
              <p class="text-sm text-muted-foreground dark:text-slate-400">开启基于知识图谱的 Text-to-SQL 问答能力</p>
            </div>
            <Switch :checked="config.kgQ2sEnable" @update:checked="(val) => config.kgQ2sEnable = val" />
          </div>

          <div class="flex items-center justify-between p-4 border rounded-lg dark:border-slate-800">
            <div class="space-y-0.5">
              <Label class="text-base dark:text-slate-200">Agent 监控 (AGNO_MONITORING)</Label>
              <p class="text-sm text-muted-foreground dark:text-slate-400">开启 Agno / Phidata 运行监控与追踪</p>
            </div>
            <Switch :checked="config.agnoMonitoring" @update:checked="(val) => config.agnoMonitoring = val" />
          </div>
        </div> -->

        <div class="pt-4 flex justify-end">
          <Button @click="saveConfig">保存配置</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>