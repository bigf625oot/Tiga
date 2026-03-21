<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { useToast } from '@/components/ui/toast/use-toast';
import { Loader2, HelpCircle, CheckCircle2, XCircle, Database, Server, Settings2 } from 'lucide-vue-next';

const { toast } = useToast();

interface DBConfig {
  type: string;
  mode: 'standalone' | 'cluster';
  host: string;
  port: number;
  clusterNodes: string;
  dbName: string;
  user: string;
  password: string;
  ssl: boolean;
  timeout: number;
  allowed_tables?: string;
  sensitive_fields?: string;
}

const graphDB = reactive<DBConfig>({
  type: 'neo4j',
  mode: 'standalone',
  host: 'localhost',
  port: 7687,
  clusterNodes: '',
  dbName: 'neo4j',
  user: 'neo4j',
  password: '',
  ssl: false,
  timeout: 30,
  allowed_tables: '',
  sensitive_fields: ''
});

const vectorDB = reactive<DBConfig>({
  type: 'milvus',
  mode: 'standalone',
  host: 'localhost',
  port: 19530,
  clusterNodes: '',
  dbName: 'default',
  user: 'root',
  password: '',
  ssl: false,
  timeout: 30,
  allowed_tables: '',
  sensitive_fields: ''
});

const isGraphTesting = ref(false);
const isVectorTesting = ref(false);
const graphConnected = ref(true);
const vectorConnected = ref(false);

const activeDrawer = ref<'graph' | 'vector' | null>(null);

const openDrawer = (type: 'graph' | 'vector') => {
  activeDrawer.value = type;
};

const closeDrawer = () => {
  activeDrawer.value = null;
};

const validateForm = (config: DBConfig) => {
  if (config.mode === 'standalone') {
    if (!config.host) return '主机地址不能为空';
    if (!config.port) return '端口不能为空';
  } else {
    if (!config.clusterNodes || !config.clusterNodes.trim()) return '集群节点不能为空';
  }
  if (config.timeout < 1) return '连接超时必须大于0';
  return null;
};

const testConnection = async (type: 'graph' | 'vector') => {
  const config = type === 'graph' ? graphDB : vectorDB;
  const loadingRef = type === 'graph' ? isGraphTesting : isVectorTesting;
  const connectedRef = type === 'graph' ? graphConnected : vectorConnected;
  
  const error = validateForm(config);
  if (error) {
    toast({
      title: '参数错误',
      description: error,
      variant: 'destructive',
    });
    return;
  }

  loadingRef.value = true;

  // Mock API call
  try {
    await new Promise((resolve, reject) => {
      setTimeout(() => {
        // Simulate random success/failure
        Math.random() > 0.3 ? resolve(true) : reject(new Error('连接超时'));
      }, 1500);
    });

    connectedRef.value = true;
    toast({
      title: '连接成功',
      description: `已成功连接到 ${config.type} 数据库`,
      class: 'bg-green-500 text-white border-green-600',
    });
  } catch (err) {
    connectedRef.value = false;
    toast({
      title: '连接失败',
      description: err instanceof Error ? err.message : '未知错误',
      variant: 'destructive',
    });
  } finally {
    loadingRef.value = false;
  }
};
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start">
    <!-- Graph Database Card -->
    <Card 
      class="group relative hover:border-blue-500/50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col justify-between h-[220px] bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 rounded-2xl cursor-pointer"
      @click="openDrawer('graph')"
    >
      <!-- 连接状态顶部色条 -->
      <div class="absolute top-0 left-0 right-0 h-1.5" :class="graphConnected ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-700'"></div>

      <div class="absolute top-4 right-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0 z-10">
        <Button variant="outline" size="icon" class="h-8 w-8 rounded-full bg-white/90 backdrop-blur-sm shadow-sm hover:text-blue-600 hover:border-blue-200 dark:bg-slate-900/90">
          <Settings2 class="w-3.5 h-3.5" />
        </Button>
      </div>

      <CardContent class="p-6 flex-1 flex flex-col h-full pt-7">
        <div class="flex items-center gap-4 mb-5">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-sm transition-transform group-hover:scale-110 bg-indigo-50 text-indigo-500 dark:bg-indigo-900/20">
            <Database class="w-6 h-6" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-base text-slate-800 dark:text-slate-100 truncate mb-1">
              图数据库配置
            </h3>
            <div class="flex items-center gap-2">
              <Badge variant="secondary" class="text-[10px] font-medium px-2 py-0 h-4.5 rounded-sm bg-slate-100 text-slate-500 dark:bg-slate-800 border-none">
                {{ graphDB.type }}
              </Badge>
            </div>
          </div>
        </div>

        <div class="flex-1 flex flex-col justify-center items-center py-2 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl mb-4 group-hover:bg-blue-50/50 dark:group-hover:bg-blue-900/10 transition-colors">
          <div class="text-[11px] text-slate-400 font-medium mb-1 tracking-wider uppercase">
            {{ graphDB.mode === 'cluster' ? '集群地址' : '连接地址' }}
          </div>
          <div class="flex items-baseline gap-1.5 text-slate-800 dark:text-slate-100">
            <template v-if="graphDB.mode === 'standalone'">
              <span class="text-lg font-bold font-mono">{{ graphDB.host }}</span>
              <span class="text-sm font-medium text-slate-500 ml-0.5">:{{ graphDB.port }}</span>
            </template>
            <template v-else>
              <span class="text-lg font-bold font-mono">{{ graphDB.clusterNodes.split('\n').filter(Boolean)[0]?.split(':')[0] || '未配置' }}</span>
              <span class="text-sm font-medium text-slate-500 ml-0.5" v-if="graphDB.clusterNodes.split('\n').filter(Boolean).length > 1">
                等 {{ graphDB.clusterNodes.split('\n').filter(Boolean).length }} 个节点
              </span>
            </template>
          </div>
        </div>

        <div class="flex items-center justify-between mt-auto pt-1">
          <div class="flex items-center gap-2">
            <div class="relative flex h-2.5 w-2.5">
              <span v-if="graphConnected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="graphConnected ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'"></span>
            </div>
            <span class="text-xs font-medium" :class="graphConnected ? 'text-emerald-600 dark:text-emerald-500' : 'text-slate-400'">
              {{ graphConnected ? '已连接' : '未连接' }}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Vector Database Card -->
    <Card 
      class="group relative hover:border-blue-500/50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col justify-between h-[220px] bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 rounded-2xl cursor-pointer"
      @click="openDrawer('vector')"
    >
      <div class="absolute top-0 left-0 right-0 h-1.5" :class="vectorConnected ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-700'"></div>

      <div class="absolute top-4 right-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0 z-10">
        <Button variant="outline" size="icon" class="h-8 w-8 rounded-full bg-white/90 backdrop-blur-sm shadow-sm hover:text-blue-600 hover:border-blue-200 dark:bg-slate-900/90">
          <Settings2 class="w-3.5 h-3.5" />
        </Button>
      </div>

      <CardContent class="p-6 flex-1 flex flex-col h-full pt-7">
        <div class="flex items-center gap-4 mb-5">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-sm transition-transform group-hover:scale-110 bg-teal-50 text-teal-500 dark:bg-teal-900/20">
            <Server class="w-6 h-6" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-base text-slate-800 dark:text-slate-100 truncate mb-1">
              向量数据库配置
            </h3>
            <div class="flex items-center gap-2">
              <Badge variant="secondary" class="text-[10px] font-medium px-2 py-0 h-4.5 rounded-sm bg-slate-100 text-slate-500 dark:bg-slate-800 border-none">
                {{ vectorDB.type }}
              </Badge>
            </div>
          </div>
        </div>

        <div class="flex-1 flex flex-col justify-center items-center py-2 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl mb-4 group-hover:bg-blue-50/50 dark:group-hover:bg-blue-900/10 transition-colors">
          <div class="text-[11px] text-slate-400 font-medium mb-1 tracking-wider uppercase">
            {{ vectorDB.mode === 'cluster' ? '集群地址' : '连接地址' }}
          </div>
          <div class="flex items-baseline gap-1.5 text-slate-800 dark:text-slate-100">
            <template v-if="vectorDB.mode === 'standalone'">
              <span class="text-lg font-bold font-mono">{{ vectorDB.host }}</span>
              <span class="text-sm font-medium text-slate-500 ml-0.5">:{{ vectorDB.port }}</span>
            </template>
            <template v-else>
              <span class="text-lg font-bold font-mono">{{ vectorDB.clusterNodes.split('\n').filter(Boolean)[0]?.split(':')[0] || '未配置' }}</span>
              <span class="text-sm font-medium text-slate-500 ml-0.5" v-if="vectorDB.clusterNodes.split('\n').filter(Boolean).length > 1">
                等 {{ vectorDB.clusterNodes.split('\n').filter(Boolean).length }} 个节点
              </span>
            </template>
          </div>
        </div>

        <div class="flex items-center justify-between mt-auto pt-1">
          <div class="flex items-center gap-2">
            <div class="relative flex h-2.5 w-2.5">
              <span v-if="vectorConnected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="vectorConnected ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'"></span>
            </div>
            <span class="text-xs font-medium" :class="vectorConnected ? 'text-emerald-600 dark:text-emerald-500' : 'text-slate-400'">
              {{ vectorConnected ? '已连接' : '未连接' }}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Right Drawer for Configuration -->
    <Sheet :open="activeDrawer !== null" @update:open="(val) => !val && closeDrawer()">
      <SheetContent class="sm:max-w-[500px] dark:bg-slate-950 dark:border-slate-800 overflow-y-auto custom-scrollbar">
        <SheetHeader class="mb-6">
          <SheetTitle class="dark:text-slate-50">
            {{ activeDrawer === 'graph' ? '图数据库配置' : '向量数据库配置' }}
          </SheetTitle>
          <SheetDescription class="dark:text-slate-400">
            {{ activeDrawer === 'graph' ? '配置 Neo4j 或 JanusGraph 连接信息' : '配置 Milvus、Pinecone 或 Qdrant 连接信息' }}
          </SheetDescription>
        </SheetHeader>

        <!-- Graph DB Form -->
        <div v-if="activeDrawer === 'graph'" class="space-y-6 pb-20">
          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">数据库类型</Label>
            <Select v-model="graphDB.type">
              <SelectTrigger class="w-full dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="neo4j" class="dark:text-slate-200 dark:focus:bg-slate-800">Neo4j</SelectItem>
                <SelectItem value="janusgraph" class="dark:text-slate-200 dark:focus:bg-slate-800">JanusGraph</SelectItem>
                <SelectItem value="nebula" class="dark:text-slate-200 dark:focus:bg-slate-800">Nebula Graph</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">部署模式</Label>
            <Tabs v-model="graphDB.mode" class="w-full">
              <TabsList class="grid w-full grid-cols-2 dark:bg-slate-900/50">
                <TabsTrigger value="standalone" class="dark:data-[state=active]:bg-slate-800">单机部署</TabsTrigger>
                <TabsTrigger value="cluster" class="dark:data-[state=active]:bg-slate-800">集群部署</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <div v-if="graphDB.mode === 'standalone'" class="grid grid-cols-2 gap-4">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">主机地址 (Host)</Label>
              <Input v-model="graphDB.host" placeholder="localhost" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">端口 (Port)</Label>
              <Input type="number" v-model.number="graphDB.port" placeholder="7687" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>

          <div v-else class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">集群节点地址</Label>
            <Textarea 
              v-model="graphDB.clusterNodes" 
              placeholder="输入节点地址，每行一个。例如：&#10;192.168.1.101:7687&#10;192.168.1.102:7687" 
              class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 font-mono text-sm min-h-[100px] resize-y" 
            />
            <p class="text-[11px] text-slate-500">支持输入多个节点地址，通常用于因果集群或存储计算分离架构。</p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">用户名</Label>
              <Input v-model="graphDB.user" placeholder="neo4j" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">密码</Label>
              <Input type="password" v-model="graphDB.password" placeholder="••••••••" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>

          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">数据库名称</Label>
            <Input v-model="graphDB.dbName" placeholder="neo4j" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>

          <div class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border dark:border-slate-800">
            <div class="space-y-0.5">
              <Label class="text-sm font-medium dark:text-slate-200">启用 SSL 安全连接</Label>
              <p class="text-[11px] text-slate-500">使用加密通道传输数据</p>
            </div>
            <Switch :checked="graphDB.ssl" @update:checked="(val) => graphDB.ssl = val" />
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Label class="text-sm font-medium dark:text-slate-200">连接超时 (秒)</Label>
            </div>
            <Input type="number" v-model.number="graphDB.timeout" min="1" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>

          <div class="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
            <h4 class="text-sm font-medium text-slate-800 dark:text-slate-200">安全与权限设置</h4>
            <div class="space-y-3">
              <Label class="text-xs dark:text-slate-300">允许访问的集合/图 (Allowed Collections)</Label>
              <Input v-model="graphDB.allowed_tables" placeholder="用逗号分隔，留空允许所有" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="space-y-3">
              <Label class="text-xs dark:text-slate-300">敏感属性脱敏 (Sensitive Fields)</Label>
              <Input v-model="graphDB.sensitive_fields" placeholder="用逗号分隔" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>
        </div>

        <!-- Vector DB Form -->
        <div v-else-if="activeDrawer === 'vector'" class="space-y-6 pb-20">
          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">数据库类型</Label>
            <Select v-model="vectorDB.type">
              <SelectTrigger class="w-full dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="milvus" class="dark:text-slate-200 dark:focus:bg-slate-800">Milvus</SelectItem>
                <SelectItem value="pinecone" class="dark:text-slate-200 dark:focus:bg-slate-800">Pinecone</SelectItem>
                <SelectItem value="qdrant" class="dark:text-slate-200 dark:focus:bg-slate-800">Qdrant</SelectItem>
                <SelectItem value="weaviate" class="dark:text-slate-200 dark:focus:bg-slate-800">Weaviate</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">部署模式</Label>
            <Tabs v-model="vectorDB.mode" class="w-full">
              <TabsList class="grid w-full grid-cols-2 dark:bg-slate-900/50">
                <TabsTrigger value="standalone" class="dark:data-[state=active]:bg-slate-800">单机部署</TabsTrigger>
                <TabsTrigger value="cluster" class="dark:data-[state=active]:bg-slate-800">集群部署</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <div v-if="vectorDB.mode === 'standalone'" class="grid grid-cols-2 gap-4">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">主机地址 (Host)</Label>
              <Input v-model="vectorDB.host" placeholder="localhost" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">端口 (Port)</Label>
              <Input type="number" v-model.number="vectorDB.port" placeholder="19530" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>

          <div v-else class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">集群节点地址</Label>
            <Textarea 
              v-model="vectorDB.clusterNodes" 
              placeholder="输入节点地址，每行一个。例如：&#10;192.168.1.201:19530&#10;192.168.1.202:19530" 
              class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 font-mono text-sm min-h-[100px] resize-y" 
            />
            <p class="text-[11px] text-slate-500">支持输入多个代理节点或分片节点地址，用于高可用访问。</p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">用户名</Label>
              <Input v-model="vectorDB.user" placeholder="root" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="space-y-3">
              <Label class="text-sm font-medium dark:text-slate-200">密码</Label>
              <Input type="password" v-model="vectorDB.password" placeholder="••••••••" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>

          <div class="space-y-3">
            <Label class="text-sm font-medium dark:text-slate-200">数据库名称 / Collection</Label>
            <Input v-model="vectorDB.dbName" placeholder="default" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>

          <div class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border dark:border-slate-800">
            <div class="space-y-0.5">
              <Label class="text-sm font-medium dark:text-slate-200">启用 SSL 安全连接</Label>
              <p class="text-[11px] text-slate-500">使用加密通道传输数据</p>
            </div>
            <Switch :checked="vectorDB.ssl" @update:checked="(val) => vectorDB.ssl = val" />
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Label class="text-sm font-medium dark:text-slate-200">连接超时 (秒)</Label>
            </div>
            <Input type="number" v-model.number="vectorDB.timeout" min="1" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>

          <div class="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
            <h4 class="text-sm font-medium text-slate-800 dark:text-slate-200">安全与权限设置</h4>
            <div class="space-y-3">
              <Label class="text-xs dark:text-slate-300">允许访问的集合/图 (Allowed Collections)</Label>
              <Input v-model="vectorDB.allowed_tables" placeholder="用逗号分隔，留空允许所有" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
            <div class="space-y-3">
              <Label class="text-xs dark:text-slate-300">敏感属性脱敏 (Sensitive Fields)</Label>
              <Input v-model="vectorDB.sensitive_fields" placeholder="用逗号分隔" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
          </div>
        </div>

        <SheetFooter class="absolute bottom-0 left-0 right-0 p-6 bg-white dark:bg-slate-950 border-t dark:border-slate-800 flex flex-row gap-3">
          <Button 
            variant="outline" 
            class="flex-1"
            @click="testConnection(activeDrawer!)" 
            :disabled="activeDrawer === 'graph' ? isGraphTesting : isVectorTesting"
          >
            <Loader2 v-if="activeDrawer === 'graph' ? isGraphTesting : isVectorTesting" class="mr-2 h-4 w-4 animate-spin" />
            测试连接
          </Button>
          <Button class="flex-1 bg-blue-600 hover:bg-blue-700 text-white" @click="closeDrawer">保存配置</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  </div>
</template>
