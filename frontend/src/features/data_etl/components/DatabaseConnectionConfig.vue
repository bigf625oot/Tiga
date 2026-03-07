<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import { Loader2 } from 'lucide-vue-next';

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

const validateForm = (config: DBConfig) => {
  if (!config.host) return '主机地址不能为空';
  if (!config.port) return '端口不能为空';
  if (config.timeout < 1) return '连接超时必须大于0';
  return null;
};

const testConnection = async (type: 'graph' | 'vector') => {
  const config = type === 'graph' ? graphDB : vectorDB;
  const loadingRef = type === 'graph' ? isGraphTesting : isVectorTesting;
  
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

    toast({
      title: '连接成功',
      description: `已成功连接到 ${config.type} 数据库`,
      variant: 'default', // success variant might need custom config, default is fine
      class: 'bg-green-500 text-white border-green-600',
    });
  } catch (err) {
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
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="text-lg font-semibold flex items-center gap-2">
              图数据库配置
              <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            </CardTitle>
            <CardDescription>配置 Neo4j 或 JanusGraph 连接信息</CardDescription>
          </div>
          <div class="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200 flex items-center gap-1.5">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
            已连接
          </div>
        </div>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>数据库类型</Label>
            <Select v-model="graphDB.type">
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="neo4j">Neo4j</SelectItem>
                <SelectItem value="janusgraph">JanusGraph</SelectItem>
                <SelectItem value="nebula">Nebula Graph</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>连接超时 (秒)</Label>
            <Input type="number" v-model.number="graphDB.timeout" min="1" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <div class="col-span-2 space-y-2">
            <Label>主机地址 (Host)</Label>
            <Input v-model="graphDB.host" placeholder="localhost" />
          </div>
          <div class="space-y-2">
            <Label>端口 (Port)</Label>
            <Input type="number" v-model.number="graphDB.port" placeholder="7687" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>用户名</Label>
            <Input v-model="graphDB.user" placeholder="neo4j" />
          </div>
          <div class="space-y-2">
            <Label>密码</Label>
            <Input type="password" v-model="graphDB.password" placeholder="••••••••" />
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
            <div class="flex items-center space-x-2">
                <Switch id="graph-ssl" :checked="graphDB.ssl" @update:checked="(val) => graphDB.ssl = val" />
                <Label htmlFor="graph-ssl">启用 SSL 安全连接</Label>
            </div>
            <div class="space-y-2 w-1/2">
               <Label>数据库名称</Label>
               <Input v-model="graphDB.dbName" placeholder="neo4j" />
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
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="text-lg font-semibold flex items-center gap-2">
              向量数据库配置
              <div class="w-2 h-2 rounded-full bg-gray-300"></div>
            </CardTitle>
            <CardDescription>配置 Milvus、Pinecone 或 Qdrant 连接信息</CardDescription>
          </div>
          <div class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500 border border-gray-200 flex items-center gap-1.5">
            未连接
          </div>
        </div>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>数据库类型</Label>
            <Select v-model="vectorDB.type">
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="milvus">Milvus</SelectItem>
                <SelectItem value="pinecone">Pinecone</SelectItem>
                <SelectItem value="qdrant">Qdrant</SelectItem>
                <SelectItem value="weaviate">Weaviate</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>连接超时 (秒)</Label>
            <Input type="number" v-model.number="vectorDB.timeout" min="1" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <div class="col-span-2 space-y-2">
            <Label>主机地址 (Host)</Label>
            <Input v-model="vectorDB.host" placeholder="localhost" />
          </div>
          <div class="space-y-2">
            <Label>端口 (Port)</Label>
            <Input type="number" v-model.number="vectorDB.port" placeholder="19530" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>用户名</Label>
            <Input v-model="vectorDB.user" placeholder="root" />
          </div>
          <div class="space-y-2">
            <Label>密码</Label>
            <Input type="password" v-model="vectorDB.password" placeholder="••••••••" />
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
            <div class="flex items-center space-x-2">
                <Switch id="vector-ssl" :checked="vectorDB.ssl" @update:checked="(val) => vectorDB.ssl = val" />
                <Label htmlFor="vector-ssl">启用 SSL 安全连接</Label>
            </div>
            <div class="space-y-2 w-1/2">
               <Label>数据库名称 / Collection</Label>
               <Input v-model="vectorDB.dbName" placeholder="default" />
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
