<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
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
import { api } from '@/core/api/client';

const { locale, setLocale } = useI18n();
const { toast } = useToast();

const languages = [
  { code: 'zh-CN', name: '简体中文' }
] as const;

const config = reactive({
  language: locale,
  logLevel: 'INFO',
  kgQ2sEnable: true,
  agnoMonitoring: true
});

const emailConfig = reactive({
  mail_username: '',
  mail_password: '',
  mail_from: '',
  mail_port: 465,
  mail_server: '',
  mail_from_name: 'Tiga System',
  mail_starttls: false,
  mail_ssl_tls: true
});

const configVersion = ref(1);
const isLoading = ref(false);

const loadConfig = async () => {
  isLoading.value = true;
  try {
    const response = await api.get('/system-config/basic-settings');
    if (response.data && response.data.email) {
      Object.assign(emailConfig, response.data.email);
      configVersion.value = response.data.version;
    }
  } catch (error) {
    console.error('Failed to load basic settings:', error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadConfig();
});

const saveConfig = async () => {
  isLoading.value = true;
  try {
    setLocale(config.language);
    
    // Save to backend
    await api.put('/system-config/basic-settings', {
      version: configVersion.value + 1,
      email: { ...emailConfig }
    });
    
    configVersion.value += 1;
    toast({
      title: '保存成功',
      description: '基础业务设置及邮件配置已更新',
    });
  } catch (error) {
    toast({
      title: '保存失败',
      description: '配置保存失败',
      variant: 'destructive'
    });
  } finally {
    isLoading.value = false;
  }
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

        <!-- Email Server Configuration -->
        <div class="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-medium dark:text-slate-200">邮件服务器配置 (SMTP)</h4>
            <p class="text-xs text-muted-foreground">用于系统通知及密码重置等邮件发送</p>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 border rounded-lg dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
            <div class="space-y-2">
              <Label class="dark:text-slate-200">SMTP 服务器 (Server)</Label>
              <Input v-model="emailConfig.mail_server" placeholder="例如: smtp.example.com" class="dark:bg-slate-950" />
            </div>
            
            <div class="space-y-2">
              <Label class="dark:text-slate-200">SMTP 端口 (Port)</Label>
              <Input v-model.number="emailConfig.mail_port" type="number" placeholder="例如: 465 或 587" class="dark:bg-slate-950" />
            </div>

            <div class="space-y-2">
              <Label class="dark:text-slate-200">邮箱账号 (Username)</Label>
              <Input v-model="emailConfig.mail_username" placeholder="发信邮箱账号" class="dark:bg-slate-950" />
            </div>

            <div class="space-y-2">
              <Label class="dark:text-slate-200">授权码/密码 (Password)</Label>
              <Input v-model="emailConfig.mail_password" type="password" placeholder="SMTP 授权码或密码" class="dark:bg-slate-950" />
            </div>

            <div class="space-y-2">
              <Label class="dark:text-slate-200">发件人地址 (From Email)</Label>
              <Input v-model="emailConfig.mail_from" placeholder="通常与账号相同" class="dark:bg-slate-950" />
            </div>

            <div class="space-y-2">
              <Label class="dark:text-slate-200">发件人名称 (From Name)</Label>
              <Input v-model="emailConfig.mail_from_name" placeholder="例如: Tiga System" class="dark:bg-slate-950" />
            </div>

            <div class="flex items-center justify-between col-span-1 md:col-span-2 mt-2">
              <div class="flex items-center space-x-6">
                <div class="flex items-center space-x-2">
                  <Switch id="use-ssl" :checked="emailConfig.mail_ssl_tls" @update:checked="(val) => emailConfig.mail_ssl_tls = val" />
                  <Label for="use-ssl" class="dark:text-slate-200">使用 SSL/TLS</Label>
                </div>
                <div class="flex items-center space-x-2">
                  <Switch id="use-starttls" :checked="emailConfig.mail_starttls" @update:checked="(val) => emailConfig.mail_starttls = val" />
                  <Label for="use-starttls" class="dark:text-slate-200">使用 STARTTLS</Label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="pt-4 flex justify-end">
          <Button @click="saveConfig" :disabled="isLoading">
            {{ isLoading ? '保存中...' : '保存配置' }}
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>