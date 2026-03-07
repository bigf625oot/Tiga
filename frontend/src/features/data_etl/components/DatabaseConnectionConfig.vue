<script setup lang="ts">
import { ref, reactive } from 'vue';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import { Loader2, HelpCircle, CheckCircle2, XCircle } from 'lucide-vue-next';

const { toast } = useToast();

interface DBConfig {
  type: string;
  host: string;
  port: number;
  dbName: string;
  user: string;
  password: string;
  ssl: boolean;
  timeout: number;
}

const graphDB = reactive<DBConfig>({
  type: 'neo4j',
  host: 'localhost',
  port: 7687,
  dbName: 'neo4j',
  user: 'neo4j',
  password: '',
  ssl: false,
  timeout: 30,
});

const vectorDB = reactive<DBConfig>({
  type: 'milvus',
  host: 'localhost',
  port: 19530,
  dbName: 'default',
  user: 'root',
  password: '',
  ssl: false,
  timeout: 30,
});

const isGraphTesting = ref(false);
const isVectorTesting = ref(false);
const graphConnected = ref(true);
const vectorConnected = ref(false);

const validateForm = (config: DBConfig) => {
  if (!config.host) return '主机地址不能为空';
  if (!config.port) return '端口不能为空';
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
  <div class="space-y-6">
    <!-- Graph Database Config -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div class="space-y-1">
            <CardTitle class="flex items-center gap-2 dark:text-slate-50">
              图数据库配置
              <span v-if="graphConnected" class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            </CardTitle>
            <CardDescription class="dark:text-slate-400">配置 Neo4j 或 JanusGraph 连接信息</CardDescription>
          </div>
          <Badge v-if="graphConnected" variant="outline" class="bg-green-50 text-green-700 border-green-200 gap-1 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
            <CheckCircle2 class="w-3 h-3" />
            已连接
          </Badge>
          <Badge v-else variant="outline" class="bg-gray-50 text-gray-500 border-gray-200 gap-1 dark:bg-gray-800/50 dark:text-gray-400 dark:border-gray-700">
            <XCircle class="w-3 h-3" />
            未连接
          </Badge>
        </div>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">数据库类型</Label>
            <Select v-model="graphDB.type">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent class="dark:bg-slate-950 dark:border-slate-800">
                <SelectItem value="neo4j" class="dark:text-slate-200 dark:focus:bg-slate-800">Neo4j</SelectItem>
                <SelectItem value="janusgraph" class="dark:text-slate-200 dark:focus:bg-slate-800">JanusGraph</SelectItem>
                <SelectItem value="nebula" class="dark:text-slate-200 dark:focus:bg-slate-800">Nebula Graph</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <Label class="dark:text-slate-200">连接超时 (秒)</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <HelpCircle class="w-3.5 h-3.5 text-muted-foreground cursor-help dark:text-slate-400" />
                  </TooltipTrigger>
                  <TooltipContent class="dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700">
                    <p>建立数据库连接的最大等待时间</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Input type="number" v-model.number="graphDB.timeout" min="1" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-6">
          <div class="col-span-2 space-y-2">
            <Label class="dark:text-slate-200">主机地址 (Host)</Label>
            <Input v-model="graphDB.host" placeholder="localhost" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">端口 (Port)</Label>
            <Input type="number" v-model.number="graphDB.port" placeholder="7687" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">用户名</Label>
            <Input v-model="graphDB.user" placeholder="neo4j" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">密码</Label>
            <Input type="password" v-model="graphDB.password" placeholder="••••••••" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
            <div class="flex items-center space-x-2">
                <Switch id="graph-ssl" :checked="graphDB.ssl" @update:checked="(val) => graphDB.ssl = val" />
                <Label htmlFor="graph-ssl" class="cursor-pointer dark:text-slate-200">启用 SSL 安全连接</Label>
            </div>
            <div class="space-y-2 w-1/2">
               <Label class="dark:text-slate-200">数据库名称</Label>
               <Input v-model="graphDB.dbName" placeholder="neo4j" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
        </div>

        <div class="pt-4 flex justify-end">
          <Button @click="testConnection('graph')" :disabled="isGraphTesting">
            <Loader2 v-if="isGraphTesting" class="mr-2 h-4 w-4 animate-spin" />
            {{ isGraphTesting ? '测试连接中...' : '测试连接' }}
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Vector Database Config -->
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div class="space-y-1">
            <CardTitle class="flex items-center gap-2 dark:text-slate-50">
              向量数据库配置
              <span v-if="vectorConnected" class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            </CardTitle>
            <CardDescription class="dark:text-slate-400">配置 Milvus、Pinecone 或 Qdrant 连接信息</CardDescription>
          </div>
          <Badge v-if="vectorConnected" variant="outline" class="bg-green-50 text-green-700 border-green-200 gap-1 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
            <CheckCircle2 class="w-3 h-3" />
            已连接
          </Badge>
          <Badge v-else variant="outline" class="bg-gray-50 text-gray-500 border-gray-200 gap-1 dark:bg-gray-800/50 dark:text-gray-400 dark:border-gray-700">
            <XCircle class="w-3 h-3" />
            未连接
          </Badge>
        </div>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">数据库类型</Label>
            <Select v-model="vectorDB.type">
              <SelectTrigger class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200">
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
          <div class="space-y-2">
             <div class="flex items-center gap-2">
              <Label class="dark:text-slate-200">连接超时 (秒)</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <HelpCircle class="w-3.5 h-3.5 text-muted-foreground cursor-help dark:text-slate-400" />
                  </TooltipTrigger>
                  <TooltipContent class="dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700">
                    <p>建立数据库连接的最大等待时间</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Input type="number" v-model.number="vectorDB.timeout" min="1" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-6">
          <div class="col-span-2 space-y-2">
            <Label class="dark:text-slate-200">主机地址 (Host)</Label>
            <Input v-model="vectorDB.host" placeholder="localhost" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">端口 (Port)</Label>
            <Input type="number" v-model.number="vectorDB.port" placeholder="19530" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label class="dark:text-slate-200">用户名</Label>
            <Input v-model="vectorDB.user" placeholder="root" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
          <div class="space-y-2">
            <Label class="dark:text-slate-200">密码</Label>
            <Input type="password" v-model="vectorDB.password" placeholder="••••••••" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
            <div class="flex items-center space-x-2">
                <Switch id="vector-ssl" :checked="vectorDB.ssl" @update:checked="(val) => vectorDB.ssl = val" />
                <Label htmlFor="vector-ssl" class="cursor-pointer dark:text-slate-200">启用 SSL 安全连接</Label>
            </div>
            <div class="space-y-2 w-1/2">
               <Label class="dark:text-slate-200">数据库名称 / Collection</Label>
               <Input v-model="vectorDB.dbName" placeholder="default" class="dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200" />
            </div>
        </div>

        <div class="pt-4 flex justify-end">
          <Button @click="testConnection('vector')" :disabled="isVectorTesting" variant="secondary">
            <Loader2 v-if="isVectorTesting" class="mr-2 h-4 w-4 animate-spin" />
            {{ isVectorTesting ? '测试连接中...' : '测试连接' }}
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
