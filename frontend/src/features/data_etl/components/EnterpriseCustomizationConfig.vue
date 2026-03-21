<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/toast/use-toast';
import { Upload, X, Image as ImageIcon } from 'lucide-vue-next';

const { toast } = useToast();

const config = reactive({
  systemName: 'Tiga Agent Platform',
  topLogoUrl: '',
  loginLogoUrl: '',
  loginBgUrl: '',
});

// Using a simple mock file input handler
const handleImageUpload = (field: 'topLogoUrl' | 'loginLogoUrl' | 'loginBgUrl') => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = (e: any) => {
    const file = e.target.files?.[0];
    if (file) {
      // Mock upload process and object URL generation for preview
      const reader = new FileReader();
      reader.onload = (event) => {
        config[field] = event.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  };
  input.click();
};

const clearImage = (field: 'topLogoUrl' | 'loginLogoUrl' | 'loginBgUrl') => {
  config[field] = '';
};

const saveConfig = () => {
  toast({
    title: '保存成功',
    description: '企业个性化设置已更新',
  });
};
</script>

<template>
  <div class="space-y-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <CardTitle class="dark:text-slate-50 text-lg font-bold">个性化设置</CardTitle>
        <CardDescription class="dark:text-slate-400">配置系统名称、系统LOGO、登录页背景等个性化信息，支持自定义品牌形象</CardDescription>
      </CardHeader>
      <CardContent class="space-y-8">
        <!-- System Name -->
        <div class="space-y-2 max-w-xl">
          <Label class="dark:text-slate-200">系统名称 (System Name)</Label>
          <Input v-model="config.systemName" placeholder="请输入系统名称" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          <p class="text-sm text-muted-foreground dark:text-slate-400">显示在浏览器标签页、登录页面等位置</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl">
          <!-- Top Navigation Logo -->
          <div class="space-y-3">
            <div class="space-y-1">
              <Label class="dark:text-slate-200">顶部导航 LOGO (Top Navigation Logo)</Label>
              <p class="text-xs text-muted-foreground dark:text-slate-400">建议尺寸 120x32px，支持 PNG/SVG/JPG，透明背景效果最佳</p>
            </div>
            
            <div 
              class="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center relative transition-colors"
              :class="config.topLogoUrl ? 'border-primary/50 bg-primary/5 dark:bg-primary/10' : 'border-slate-200 dark:border-slate-800 hover:border-primary/50 hover:bg-slate-50 dark:hover:bg-slate-900/50'"
            >
              <div v-if="config.topLogoUrl" class="w-full flex flex-col items-center gap-4">
                <div class="h-16 flex items-center justify-center w-full bg-slate-100 dark:bg-slate-900 rounded border dark:border-slate-700 p-2">
                  <img :src="config.topLogoUrl" alt="Top Logo Preview" class="max-h-full max-w-full object-contain" />
                </div>
                <div class="flex gap-2">
                  <Button variant="outline" size="sm" @click="handleImageUpload('topLogoUrl')">更换图片</Button>
                  <Button variant="destructive" size="sm" @click="clearImage('topLogoUrl')">
                    <X class="w-4 h-4 mr-1" /> 清除
                  </Button>
                </div>
              </div>
              
              <div v-else class="text-center cursor-pointer w-full h-full min-h-[120px] flex flex-col items-center justify-center" @click="handleImageUpload('topLogoUrl')">
                <div class="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3 text-slate-500">
                  <ImageIcon class="w-5 h-5" />
                </div>
                <p class="text-sm font-medium dark:text-slate-200">点击上传图片</p>
                <p class="text-xs text-muted-foreground mt-1">支持拖拽上传 (最大 2MB)</p>
              </div>
            </div>
          </div>

          <!-- Login Page Logo -->
          <div class="space-y-3">
            <div class="space-y-1">
              <Label class="dark:text-slate-200">登录页 LOGO (Login Page Logo)</Label>
              <p class="text-xs text-muted-foreground dark:text-slate-400">建议尺寸 200x60px，支持 PNG/SVG/JPG，透明背景效果最佳</p>
            </div>
            
            <div 
              class="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center relative transition-colors"
              :class="config.loginLogoUrl ? 'border-primary/50 bg-primary/5 dark:bg-primary/10' : 'border-slate-200 dark:border-slate-800 hover:border-primary/50 hover:bg-slate-50 dark:hover:bg-slate-900/50'"
            >
              <div v-if="config.loginLogoUrl" class="w-full flex flex-col items-center gap-4">
                <div class="h-16 flex items-center justify-center w-full bg-slate-100 dark:bg-slate-900 rounded border dark:border-slate-700 p-2">
                  <img :src="config.loginLogoUrl" alt="Login Logo Preview" class="max-h-full max-w-full object-contain" />
                </div>
                <div class="flex gap-2">
                  <Button variant="outline" size="sm" @click="handleImageUpload('loginLogoUrl')">更换图片</Button>
                  <Button variant="destructive" size="sm" @click="clearImage('loginLogoUrl')">
                    <X class="w-4 h-4 mr-1" /> 清除
                  </Button>
                </div>
              </div>
              
              <div v-else class="text-center cursor-pointer w-full h-full min-h-[120px] flex flex-col items-center justify-center" @click="handleImageUpload('loginLogoUrl')">
                <div class="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3 text-slate-500">
                  <Upload class="w-5 h-5" />
                </div>
                <p class="text-sm font-medium dark:text-slate-200">点击上传图片</p>
                <p class="text-xs text-muted-foreground mt-1">支持拖拽上传 (最大 2MB)</p>
              </div>
            </div>
          </div>
          
          <!-- Login Background -->
          <div class="space-y-3 md:col-span-2">
            <div class="space-y-1">
              <Label class="dark:text-slate-200">登录页背景图 (Login Background)</Label>
              <p class="text-xs text-muted-foreground dark:text-slate-400">建议尺寸 1920x1080px，支持 JPG/PNG，以提升登录页面的视觉效果</p>
            </div>
            
            <div 
              class="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center relative transition-colors"
              :class="config.loginBgUrl ? 'border-primary/50 bg-primary/5 dark:bg-primary/10' : 'border-slate-200 dark:border-slate-800 hover:border-primary/50 hover:bg-slate-50 dark:hover:bg-slate-900/50'"
            >
              <div v-if="config.loginBgUrl" class="w-full flex flex-col items-center gap-4">
                <div class="h-40 flex items-center justify-center w-full bg-slate-100 dark:bg-slate-900 rounded border dark:border-slate-700 overflow-hidden relative group">
                  <img :src="config.loginBgUrl" alt="Login Background Preview" class="w-full h-full object-cover" />
                  <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                    <Button variant="secondary" size="sm" @click="handleImageUpload('loginBgUrl')">更换背景</Button>
                    <Button variant="destructive" size="sm" @click="clearImage('loginBgUrl')">清除</Button>
                  </div>
                </div>
              </div>
              
              <div v-else class="text-center cursor-pointer w-full h-full min-h-[160px] flex flex-col items-center justify-center" @click="handleImageUpload('loginBgUrl')">
                <div class="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3 text-slate-500">
                  <ImageIcon class="w-6 h-6" />
                </div>
                <p class="text-sm font-medium dark:text-slate-200">点击或拖拽上传背景图片</p>
                <p class="text-xs text-muted-foreground mt-1">推荐尺寸：1920x1080px (最大 5MB)</p>
              </div>
            </div>
          </div>
        </div>

        <div class="pt-6 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <Button @click="saveConfig" class="px-6">保存个性化配置</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
