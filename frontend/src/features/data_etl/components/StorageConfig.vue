<script setup lang="ts">
import { reactive, ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { useToast } from '@/components/ui/toast/use-toast';
import { Loader2, HardDrive, Cloud, Settings2, Plus, Trash2 } from 'lucide-vue-next';

const { toast } = useToast();

interface StorageConfig {
  id: string;
  name: string;
  type: 'local' | 's3' | 'aliyun_oss';
  path?: string;
  endpoint?: string;
  region?: string;
  accessKey?: string;
  secretKey?: string;
  bucketName?: string;
  accessKeyId?: string;
  accessKeySecret?: string;
  bucket?: string;
}

const connections = ref<StorageConfig[]>([
  {
    id: 'local-1',
    name: '本地存储',
    type: 'local',
    path: './data/recordings'
  },
  {
    id: 's3-1',
    name: 'S3 / MinIO',
    type: 's3',
    endpoint: '',
    region: 'us-east-1',
    accessKey: 'minioadmin',
    secretKey: 'minioadmin',
    bucketName: 'recordings'
  },
  {
    id: 'aliyun-1',
    name: '阿里云 OSS',
    type: 'aliyun_oss',
    endpoint: 'oss-cn-shanghai.aliyuncs.com',
    accessKeyId: '',
    accessKeySecret: '',
    bucket: ''
  }
]);

const activeStorageId = ref('local-1');
const isTesting = ref(false);

const drawerState = ref<{
  isOpen: boolean;
  mode: 'add' | 'edit';
  config: StorageConfig;
}>({
  isOpen: false,
  mode: 'add',
  config: {} as StorageConfig
});

const drawerSetAsActive = ref(false);

const openDrawer = (conn: StorageConfig) => {
  drawerState.value = {
    isOpen: true,
    mode: 'edit',
    config: JSON.parse(JSON.stringify(conn))
  };
  drawerSetAsActive.value = activeStorageId.value === conn.id;
};

const openAddDrawer = () => {
  drawerState.value = {
    isOpen: true,
    mode: 'add',
    config: {
      id: Date.now().toString(),
      name: '新建 S3 存储',
      type: 's3',
      endpoint: '',
      region: 'us-east-1',
      accessKey: '',
      secretKey: '',
      bucketName: ''
    }
  };
  drawerSetAsActive.value = false;
};

const closeDrawer = () => {
  drawerState.value.isOpen = false;
};

const handleTypeChange = (val: string) => {
  const newType = val as 'local' | 's3' | 'aliyun_oss';
  const id = drawerState.value.config.id;
  if (newType === 's3') {
    drawerState.value.config = {
      id, name: '新建 S3 存储', type: 's3', endpoint: '', region: 'us-east-1', accessKey: '', secretKey: '', bucketName: ''
    };
  } else if (newType === 'aliyun_oss') {
    drawerState.value.config = {
      id, name: '新建阿里云 OSS', type: 'aliyun_oss', endpoint: '', accessKeyId: '', accessKeySecret: '', bucket: ''
    };
  } else if (newType === 'local') {
    drawerState.value.config = {
      id, name: '新建本地存储', type: 'local', path: './data/recordings'
    };
  }
};

const saveConfig = () => {
  if (!drawerState.value.config.name) {
    toast({ title: '参数错误', description: '配置名称不能为空', variant: 'destructive' });
    return;
  }
  const idx = connections.value.findIndex(c => c.id === drawerState.value.config.id);
  if (drawerState.value.mode === 'add') {
    connections.value.push(JSON.parse(JSON.stringify(drawerState.value.config)));
  } else {
    if (idx !== -1) {
      connections.value[idx] = JSON.parse(JSON.stringify(drawerState.value.config));
    }
  }
  
  if (drawerSetAsActive.value) {
    activeStorageId.value = drawerState.value.config.id;
  }

  toast({
    title: '保存成功',
    description: '外部存储配置已更新',
  });
  closeDrawer();
};

const deleteConfig = () => {
  if (drawerState.value.config.id === activeStorageId.value) {
    toast({
      title: '删除失败',
      description: '不能删除当前启用的存储配置',
      variant: 'destructive'
    });
    return;
  }
  connections.value = connections.value.filter(c => c.id !== drawerState.value.config.id);
  toast({
    title: '删除成功',
    description: '存储配置已删除',
  });
  closeDrawer();
};

const testConnection = async () => {
  isTesting.value = true;
  setTimeout(() => {
    isTesting.value = false;
    toast({
      title: '连接成功',
      description: '存储服务访问正常',
      class: 'bg-green-500 text-white border-green-600',
    });
  }, 1000);
};

// UI Helpers
const getIcon = (type: string) => {
  if (type === 'local') return HardDrive;
  if (type === 's3' || type === 'aliyun_oss') return Cloud;
  return HardDrive;
};

const getIconBgClass = (type: string) => {
  if (type === 'local') return 'bg-slate-50 text-slate-500 dark:bg-slate-900/20';
  if (type === 's3') return 'bg-blue-50 text-blue-500 dark:bg-blue-900/20';
  if (type === 'aliyun_oss') return 'bg-orange-50 text-orange-500 dark:bg-orange-900/20';
  return 'bg-slate-50 text-slate-500';
};

const getBadgeText = (type: string) => {
  if (type === 'local') return 'Local';
  if (type === 's3') return 'S3 Compatible';
  if (type === 'aliyun_oss') return 'Aliyun';
  return '';
};

const getEndpointText = (conn: StorageConfig) => {
  if (conn.type === 'local') return conn.path || './data/recordings';
  if (conn.type === 's3') return conn.endpoint || '未配置';
  if (conn.type === 'aliyun_oss') return conn.endpoint || '未配置';
  return '';
};
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start">
    
    <!-- Connection Cards -->
    <Card 
      v-for="conn in connections" 
      :key="conn.id"
      class="group relative hover:border-blue-500/50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col justify-between h-[220px] bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 rounded-2xl cursor-pointer"
      @click="openDrawer(conn)"
    >
      <div class="absolute top-0 left-0 right-0 h-1.5" :class="activeStorageId === conn.id ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-700'"></div>
      
      <div class="absolute top-4 right-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0 z-10">
        <Button variant="outline" size="icon" class="h-8 w-8 rounded-full bg-white/90 backdrop-blur-sm shadow-sm hover:text-blue-600 hover:border-blue-200 dark:bg-slate-900/90">
          <Settings2 class="w-3.5 h-3.5" />
        </Button>
      </div>

      <CardContent class="p-6 flex-1 flex flex-col h-full pt-7">
        <div class="flex items-center gap-4 mb-5">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-sm transition-transform group-hover:scale-110" :class="getIconBgClass(conn.type)">
            <component :is="getIcon(conn.type)" class="w-6 h-6" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-base text-slate-800 dark:text-slate-100 truncate mb-1" :title="conn.name">
              {{ conn.name }}
            </h3>
            <div class="flex items-center gap-2">
              <Badge variant="secondary" class="text-[10px] font-medium px-2 py-0 h-4.5 rounded-sm bg-slate-100 text-slate-500 dark:bg-slate-800 border-none">
                {{ getBadgeText(conn.type) }}
              </Badge>
            </div>
          </div>
        </div>

        <div class="flex-1 flex flex-col justify-center items-center py-2 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl mb-4 group-hover:bg-blue-50/50 dark:group-hover:bg-blue-900/10 transition-colors">
          <div class="text-[11px] text-slate-400 font-medium mb-1 tracking-wider uppercase">
            {{ conn.type === 'local' ? '存储路径' : 'Endpoint' }}
          </div>
          <div class="flex items-baseline gap-1.5 text-slate-800 dark:text-slate-100 px-2 text-center">
            <span class="text-sm font-bold font-mono truncate max-w-full">{{ getEndpointText(conn) }}</span>
          </div>
        </div>

        <div class="flex items-center justify-between mt-auto pt-1">
          <div class="flex items-center gap-2">
            <div class="relative flex h-2.5 w-2.5">
              <span v-if="activeStorageId === conn.id" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="activeStorageId === conn.id ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'"></span>
            </div>
            <span class="text-xs font-medium" :class="activeStorageId === conn.id ? 'text-emerald-600 dark:text-emerald-500' : 'text-slate-400'">
              {{ activeStorageId === conn.id ? '当前启用' : '未启用' }}
            </span>
          </div>
          <Button 
            v-if="activeStorageId !== conn.id"
            variant="ghost" 
            size="sm" 
            class="h-6 text-xs px-2 hover:text-blue-600"
            @click.stop="activeStorageId = conn.id"
          >
            设为启用
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Add Connection Card -->
    <Card 
      class="group relative hover:border-blue-500/50 hover:shadow-lg transition-all duration-300 flex flex-col justify-center items-center h-[220px] bg-transparent border-2 border-dashed border-slate-300 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/50 rounded-2xl cursor-pointer"
      @click="openAddDrawer"
    >
      <div class="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 mb-3 text-slate-500 group-hover:text-blue-500">
        <Plus class="w-6 h-6" />
      </div>
      <span class="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400">添加存储连接</span>
    </Card>

    <!-- Right Drawer for Configuration -->
    <Sheet :open="drawerState.isOpen" @update:open="(val) => !val && closeDrawer()">
      <SheetContent class="sm:max-w-[500px] dark:bg-slate-950 dark:border-slate-800 overflow-y-auto custom-scrollbar">
        <SheetHeader class="mb-6">
          <div class="flex items-center justify-between">
            <div class="space-y-1">
              <SheetTitle class="dark:text-slate-50">
                {{ drawerState.mode === 'add' ? '添加存储连接' : '编辑存储连接' }}
              </SheetTitle>
              <SheetDescription class="dark:text-slate-400">
                配置对象存储的连接参数与访问凭证
              </SheetDescription>
            </div>
            <Button 
              v-if="drawerState.mode === 'edit' && activeStorageId !== drawerState.config.id" 
              variant="ghost" 
              size="icon" 
              class="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50 -mr-2"
              @click="deleteConfig"
              title="删除配置"
            >
              <Trash2 class="w-4 h-4" />
            </Button>
          </div>
        </SheetHeader>

        <div class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border dark:border-slate-800 mb-6">
          <div class="space-y-0.5">
            <Label class="text-sm font-medium dark:text-slate-200">启用该存储</Label>
            <p class="text-[11px] text-slate-500">将此存储作为当前系统的默认对象存储</p>
          </div>
          <Switch v-model:checked="drawerSetAsActive" />
        </div>

        <!-- Basic Info Form -->
        <div class="space-y-6 pb-20">
          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">配置名称</Label>
            <Input v-model="drawerState.config.name" placeholder="例如：生产环境 S3" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>

          <div class="space-y-3" v-if="drawerState.mode === 'add'">
            <Label class="text-sm font-medium dark:text-slate-200">存储类型</Label>
            <Select v-model="drawerState.config.type" @update:modelValue="handleTypeChange">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 w-full">
                <SelectValue placeholder="选择存储类型" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="local" class="dark:text-slate-200">本地存储 (Local)</SelectItem>
                <SelectItem value="s3" class="dark:text-slate-200">S3 / MinIO 兼容存储</SelectItem>
                <SelectItem value="aliyun_oss" class="dark:text-slate-200">阿里云 OSS</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-3" v-else>
            <Label class="text-sm font-medium dark:text-slate-200">存储类型</Label>
            <Input :value="getBadgeText(drawerState.config.type)" disabled class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-500 bg-slate-50 dark:bg-slate-900" />
          </div>

          <div class="h-px bg-slate-200 dark:bg-slate-800 my-6"></div>

          <!-- Local Form -->
          <div v-if="drawerState.config.type === 'local'" class="space-y-6">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">存储路径</Label>
              <Input v-model="drawerState.config.path" placeholder="./data/recordings" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              <p class="text-[11px] text-slate-500">配置服务器上的本地文件夹路径。</p>
            </div>
          </div>

          <!-- S3 Form -->
          <div v-else-if="drawerState.config.type === 's3'" class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-3">
                <Label class="text-sm font-medium dark:text-slate-200">S3 Endpoint URL</Label>
                <Input v-model="drawerState.config.endpoint" placeholder="http://localhost:9000" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              </div>
              <div class="space-y-3">
                <Label class="text-sm font-medium dark:text-slate-200">区域 (Region)</Label>
                <Input v-model="drawerState.config.region" placeholder="us-east-1" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-3">
                <Label class="text-sm font-medium dark:text-slate-200">Access Key</Label>
                <Input v-model="drawerState.config.accessKey" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              </div>
              <div class="space-y-3">
                <Label class="text-sm font-medium dark:text-slate-200">Secret Key</Label>
                <Input type="password" v-model="drawerState.config.secretKey" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              </div>
            </div>
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">Bucket Name</Label>
              <Input v-model="drawerState.config.bucketName" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>

          <!-- Aliyun Form -->
          <div v-else-if="drawerState.config.type === 'aliyun_oss'" class="space-y-6">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">OSS Endpoint</Label>
              <Input v-model="drawerState.config.endpoint" placeholder="oss-cn-shanghai.aliyuncs.com" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-3">
                <Label class="text-sm font-medium dark:text-slate-200">Access Key ID</Label>
                <Input v-model="drawerState.config.accessKeyId" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              </div>
              <div class="space-y-3">
                <Label class="text-sm font-medium dark:text-slate-200">Access Key Secret</Label>
                <Input type="password" v-model="drawerState.config.accessKeySecret" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
              </div>
            </div>
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">Bucket Name</Label>
              <Input v-model="drawerState.config.bucket" placeholder="留空则使用默认 bucket" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>
        </div>

        <SheetFooter class="absolute bottom-0 left-0 right-0 p-6 bg-white dark:bg-slate-950 border-t dark:border-slate-800 flex flex-row gap-3 z-10">
          <Button 
            v-if="drawerState.config.type !== 'local'"
            variant="outline" 
            class="flex-1"
            @click="testConnection" 
            :disabled="isTesting"
          >
            <Loader2 v-if="isTesting" class="mr-2 h-4 w-4 animate-spin" />
            测试连接
          </Button>
          <Button class="flex-1 bg-blue-600 hover:bg-blue-700 text-white" @click="saveConfig">保存配置</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  </div>
</template>