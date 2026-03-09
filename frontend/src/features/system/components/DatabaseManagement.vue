<template>
  <div class="h-full flex flex-col bg-background text-foreground transition-colors duration-300">
    <!-- Header Banner -->
    <div class="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">数据库</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-muted-foreground text-xs truncate max-w-xl">
            管理数据库连接配置，支持 MySQL, PostgreSQL 等。
          </p>
        </div>
        <Button 
          @click="openCreateModal" 
          size="sm"
          class="h-9"
        >
          <Plus class="w-4 h-4 mr-2" />
          新建连接
        </Button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-hidden p-6 bg-background">
      <div class="h-full flex flex-col w-full border border-border rounded-lg bg-card shadow-sm overflow-hidden">
         <!-- List Header -->
         <div class="grid grid-cols-12 gap-4 px-4 py-3 bg-muted/50 border-b border-border text-xs font-medium text-muted-foreground">
            <div class="col-span-4 pl-2">连接名称/Host</div>
            <div class="col-span-2">类型</div>
            <div class="col-span-2">端口</div>
            <div class="col-span-2">用户</div>
            <div class="col-span-2 text-right pr-2">操作</div>
         </div>
         
         <!-- List Content -->
         <ScrollArea class="flex-1">
           <div v-if="loading" class="flex flex-col p-4 space-y-4">
              <div v-for="i in 3" :key="i" class="flex items-center gap-4">
                  <Skeleton class="h-10 w-10 rounded-md" />
                  <div class="space-y-2 flex-1">
                    <Skeleton class="h-4 w-full" />
                    <Skeleton class="h-3 w-2/3" />
                  </div>
              </div>
           </div>
           
           <div v-else-if="!currentConfig.host && !currentConfig.path" class="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <div class="w-16 h-16 bg-muted/50 rounded-xl flex items-center justify-center mb-4">
                  <Database class="w-8 h-8 opacity-50" />
              </div>
              <span class="text-sm font-medium">暂无连接配置</span>
           </div>
           
           <div v-else class="flex flex-col">
              <div class="grid grid-cols-12 gap-4 items-center px-4 py-3 border-b border-border hover:bg-muted/30 transition-colors text-sm group">
                 <div class="col-span-4 flex items-center gap-3 overflow-hidden pl-2">
                      <div class="w-8 h-8 flex items-center justify-center bg-muted rounded-md flex-shrink-0">
                          <Database class="w-4 h-4 text-muted-foreground" />
                      </div>
                      <span class="truncate font-medium">{{ currentConfig.name || currentConfig.host || currentConfig.path }}</span>
                 </div>
                 <div class="col-span-2">
                    <Badge variant="outline" class="font-normal bg-muted/50">{{ currentConfig.type }}</Badge>
                 </div>
                 <div class="col-span-2 text-muted-foreground font-mono text-xs">{{ currentConfig.port || '-' }}</div>
                 <div class="col-span-2 text-muted-foreground text-xs">{{ currentConfig.user || '-' }}</div>
                 <div class="col-span-2 flex justify-end items-center gap-2 pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="icon" class="h-8 w-8" @click="viewTables" title="查看表">
                        <TableIcon class="w-4 h-4 text-muted-foreground hover:text-primary" />
                    </Button>
                    <Button variant="ghost" size="icon" class="h-8 w-8" @click="editConfig" title="编辑">
                        <Edit2 class="w-4 h-4 text-muted-foreground hover:text-primary" />
                    </Button>
                    <Button variant="ghost" size="icon" class="h-8 w-8" title="删除" disabled>
                        <Trash2 class="w-4 h-4 text-muted-foreground hover:text-destructive" />
                    </Button>
                 </div>
              </div>
           </div>
         </ScrollArea>
      </div>
    </div>

    <!-- Tables Preview Modal -->
    <Dialog v-model:open="showTablesModal">
        <DialogContent class="max-w-[90vw] w-[1200px] h-[85vh] p-0 flex flex-col gap-0 overflow-hidden">
            <DialogHeader class="px-6 py-4 border-b border-border bg-card">
                <DialogTitle class="text-base flex items-center gap-2">
                    <Database class="w-4 h-4 text-primary" />
                    数据库表预览
                </DialogTitle>
            </DialogHeader>
            
            <div class="flex-1 flex overflow-hidden">
                <!-- Sidebar -->
                <div class="w-64 border-r border-border bg-muted/10 flex flex-col">
                    <div class="p-3 border-b border-border bg-muted/20">
                        <div class="relative">
                            <Search class="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
                            <Input placeholder="搜索表..." class="h-8 pl-8 text-xs bg-background" />
                        </div>
                    </div>
                    <ScrollArea class="flex-1">
                        <div v-if="loadingTables" class="flex justify-center py-10">
                            <Loader2 class="w-5 h-5 animate-spin text-muted-foreground" />
                        </div>
                        <div v-else-if="tables.length === 0" class="text-center py-10 text-muted-foreground text-xs">
                            暂无数据表
                        </div>
                        <div v-else class="p-2 space-y-0.5">
                            <button 
                                v-for="t in tables" :key="t"
                                @click="fetchTableData(t)"
                                class="w-full text-left px-3 py-2 rounded-md text-sm truncate transition-colors flex items-center gap-2"
                                :class="selectedTable === t ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:bg-muted hover:text-foreground'"
                            >
                                <TableIcon class="w-3.5 h-3.5 flex-shrink-0" />
                                <span class="truncate">{{ t }}</span>
                            </button>
                        </div>
                    </ScrollArea>
                </div>

                <!-- Content -->
                <div class="flex-1 flex flex-col overflow-hidden bg-background">
                    <div v-if="!selectedTable" class="flex-1 flex flex-col items-center justify-center text-muted-foreground">
                        <TableIcon class="w-12 h-12 mb-4 opacity-20" />
                        <span class="text-sm">请选择左侧数据表查看详情</span>
                    </div>
                    <div v-else class="flex-1 flex flex-col overflow-hidden">
                        <div class="px-4 py-3 border-b border-border flex justify-between items-center bg-card/50">
                            <div class="flex items-center gap-4">
                                <h3 class="font-medium text-sm flex items-center gap-2">
                                    <TableIcon class="w-4 h-4 text-muted-foreground" />
                                    {{ selectedTable }}
                                </h3>
                                
                                <div class="h-4 w-[1px] bg-border"></div>

                                <!-- Actions -->
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger as-child>
                                            <Button 
                                                variant="outline" 
                                                size="sm" 
                                                class="h-7 text-xs gap-1.5"
                                                :class="{
                                                    'bg-green-50 text-green-600 border-green-200 hover:bg-green-100 dark:bg-green-900/20 dark:text-green-400 dark:border-green-900': convertStatus.status === 'completed',
                                                    'bg-red-50 text-red-600 border-red-200 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900': convertStatus.status === 'failed'
                                                }"
                                                @click="convertTableToGraph"
                                                :disabled="['running', 'pending'].includes(convertStatus.status)"
                                            >
                                                <Loader2 v-if="['running', 'pending'].includes(convertStatus.status)" class="w-3.5 h-3.5 animate-spin" />
                                                <Check v-else-if="convertStatus.status === 'completed'" class="w-3.5 h-3.5" />
                                                <XCircle v-else-if="convertStatus.status === 'failed'" class="w-3.5 h-3.5" />
                                                <Share2 v-else class="w-3.5 h-3.5" />
                                                
                                                {{ convertStatus.status === 'pending' ? '准备中' : 
                                                   convertStatus.status === 'running' ? `转换中 ${convertStatus.progress}%` : 
                                                   convertStatus.status === 'completed' ? '转换完成' : 
                                                   convertStatus.status === 'failed' ? '转换失败' : '转为图谱' }}
                                            </Button>
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p>{{ convertStatus.message || '将表结构和数据转换为知识图谱' }}</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>

                                <Button 
                                    v-if="convertStatus.status === 'completed'" 
                                    variant="link" 
                                    size="sm" 
                                    class="h-7 text-xs p-0"
                                    @click="$emit('navigate', 'knowledge_graph')"
                                >
                                    查看图谱 <ArrowRight class="w-3 h-3 ml-1" />
                                </Button>
                            </div>
                            <span class="text-xs text-muted-foreground" v-if="tableData.length > 0">
                                前 {{ tableData.length }} 条记录
                            </span>
                        </div>
                        
                        <!-- Table Data -->
                        <div class="flex-1 overflow-auto">
                            <div v-if="loadingTableData" class="flex justify-center py-20">
                                <Loader2 class="w-8 h-8 animate-spin text-primary/50" />
                            </div>
                            <Table v-else>
                                <TableHeader>
                                    <TableRow class="hover:bg-transparent">
                                        <TableHead v-for="col in tableColumns" :key="col.key" class="h-9 text-xs font-semibold whitespace-nowrap bg-muted/50 sticky top-0 z-10">
                                            {{ col.title }}
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    <TableRow v-for="(row, idx) in tableData" :key="idx" class="hover:bg-muted/30">
                                        <TableCell v-for="col in tableColumns" :key="col.key" class="py-2 text-xs whitespace-nowrap font-mono">
                                            {{ row[col.key] }}
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </div>
            </div>
        </DialogContent>
    </Dialog>

    <!-- Create/Edit Modal -->
    <Dialog v-model:open="showCreateModal">
        <DialogContent class="sm:max-w-[500px]">
            <DialogHeader>
                <DialogTitle>{{ isEdit ? '编辑连接' : '新建连接' }}</DialogTitle>
                <DialogDescription>
                    配置数据库连接信息。
                </DialogDescription>
            </DialogHeader>
            
            <div class="py-4 space-y-4">
                <div class="space-y-2">
                    <Label>连接名称</Label>
                    <Input v-model="configForm.name" placeholder="请输入连接名称（选填）" />
                </div>

                <div class="space-y-2">
                    <Label>数据库类型</Label>
                    <Select v-model="configForm.type" @update:modelValue="handleTypeChange">
                        <SelectTrigger>
                            <SelectValue placeholder="选择类型" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="sqlite">SQLite</SelectItem>
                            <SelectItem value="postgresql">PostgreSQL</SelectItem>
                            <SelectItem value="mysql">MySQL</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <template v-if="configForm.type === 'sqlite'">
                    <div class="space-y-2">
                        <Label>文件路径</Label>
                        <Input v-model="configForm.path" placeholder="e.g. /data/app.db" />
                        <p class="text-[10px] text-muted-foreground">请输入SQLite数据库文件的绝对路径</p>
                    </div>
                </template>

                <template v-else>
                    <div class="grid grid-cols-3 gap-4">
                        <div class="col-span-2 space-y-2">
                            <Label>主机地址</Label>
                            <Input v-model="configForm.host" placeholder="localhost" />
                        </div>
                        <div class="space-y-2">
                            <Label>端口</Label>
                            <Input type="number" v-model="configForm.port" placeholder="Port" />
                        </div>
                    </div>

                    <div class="space-y-2">
                        <Label>用户名</Label>
                        <Input v-model="configForm.user" placeholder="root" />
                    </div>

                    <div class="space-y-2">
                        <Label>密码</Label>
                        <Input type="password" v-model="configForm.password" placeholder="••••••" />
                    </div>

                    <!-- Advanced Options -->
                    <div class="pt-2">
                        <button 
                            @click="showAdvanced = !showAdvanced" 
                            class="flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                        >
                            <span>更多配置</span>
                            <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="showAdvanced ? 'rotate-180' : ''" />
                        </button>
                        
                        <div v-if="showAdvanced" class="mt-3 space-y-3 p-3 bg-muted/30 rounded-md border border-border animate-in slide-in-from-top-2">
                            <div class="space-y-2">
                                <Label class="text-xs">数据库名称</Label>
                                <Input class="h-8 text-xs" v-model="configForm.database" placeholder="默认数据库" />
                            </div>
                            
                            <div class="grid grid-cols-2 gap-3">
                                <div class="space-y-2">
                                    <Label class="text-xs">超时 (秒)</Label>
                                    <Input class="h-8 text-xs" type="number" v-model="configForm.timeout" />
                                </div>
                                <div class="space-y-2">
                                    <Label class="text-xs">连接池大小</Label>
                                    <Input class="h-8 text-xs" type="number" v-model="configForm.pool_size" />
                                </div>
                            </div>

                            <div v-if="configForm.type === 'mysql'" class="space-y-2">
                                <Label class="text-xs">字符集</Label>
                                <Select v-model="configForm.charset">
                                    <SelectTrigger class="h-8 text-xs">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="utf8mb4">utf8mb4</SelectItem>
                                        <SelectItem value="utf8">utf8</SelectItem>
                                        <SelectItem value="latin1">latin1</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div v-if="configForm.type === 'postgresql'" class="space-y-2">
                                <Label class="text-xs">SSL 模式</Label>
                                <Select v-model="configForm.ssl_mode">
                                    <SelectTrigger class="h-8 text-xs">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="disable">Disable</SelectItem>
                                        <SelectItem value="require">Require</SelectItem>
                                        <SelectItem value="verify-ca">Verify CA</SelectItem>
                                        <SelectItem value="verify-full">Verify Full</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>
                </template>

                <!-- Status Message -->
                <div v-if="testResult" class="p-3 rounded-md text-xs flex items-start gap-2" :class="testResult.success ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'">
                    <component :is="testResult.success ? Check : XCircle" class="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span class="break-all">{{ testResult.message }}</span>
                </div>
            </div>

            <DialogFooter class="gap-2 sm:gap-0">
                <Button variant="outline" @click="testConnection" :disabled="testing || connecting">
                    <Loader2 v-if="testing" class="w-3.5 h-3.5 mr-2 animate-spin" />
                    测试连接
                </Button>
                <Button @click="saveAndConnect" :disabled="testing || connecting">
                    <Loader2 v-if="connecting" class="w-3.5 h-3.5 mr-2 animate-spin" />
                    保存并连接
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, onUnmounted } from 'vue';
import { message } from 'ant-design-vue'; // Keep for global toast messages if preferred, or replace with shadcn toast
// Icons
import { 
    Plus, 
    Database, 
    Table as TableIcon, 
    Edit2, 
    Trash2, 
    Loader2, 
    Search, 
    ChevronDown, 
    Check, 
    XCircle,
    Share2,
    ArrowRight
} from 'lucide-vue-next';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const showCreateModal = ref(false);
const isEdit = ref(false);
const loading = ref(false);
const emit = defineEmits(['navigate']);
const currentConfig = ref({});

// Form State
const configForm = ref({
    name: '',
    type: 'sqlite',
    path: '',
    host: 'localhost',
    port: 5432,
    database: '',
    user: '',
    password: '',
    timeout: 30,
    pool_size: 5,
    charset: 'utf8mb4',
    ssl_mode: 'disable'
});

const showAdvanced = ref(false);
const testing = ref(false);
const connecting = ref(false);
const testResult = ref(null);

const handleTypeChange = (val) => {
    if (val === 'postgresql') configForm.value.port = 5432;
    if (val === 'mysql') configForm.value.port = 3306;
    if (val === 'sqlite') configForm.value.port = null;
    testResult.value = null;
};

const fetchConfig = async () => {
    loading.value = true;
    try {
        const res = await fetch('/api/v1/data_query/config');
        if (res.ok) {
            const data = await res.json();
            if (Object.keys(data).length > 0) {
                currentConfig.value = data;
            }
        }
    } catch (e) {
        console.error("Failed to load config", e);
    } finally {
        loading.value = false;
    }
};

const openCreateModal = () => {
    isEdit.value = false;
    configForm.value = {
        name: '',
        type: 'mysql',
        path: '',
        host: 'localhost',
        port: 3306,
        database: '',
        user: '',
        password: '',
        timeout: 30,
        pool_size: 5,
        charset: 'utf8mb4',
        ssl_mode: 'disable'
    };
    testResult.value = null;
    showCreateModal.value = true;
};

const editConfig = () => {
    isEdit.value = true;
    configForm.value = { ...currentConfig.value };
    testResult.value = null;
    showCreateModal.value = true;
};

// --- Table View Logic ---
const showTablesModal = ref(false);
const tables = ref([]);
const loadingTables = ref(false);
const selectedTable = ref(null);
const tableData = ref([]);
const tableColumns = ref([]);
const loadingTableData = ref(false);

const viewTables = async () => {
    showTablesModal.value = true;
    loadingTables.value = true;
    selectedTable.value = null;
    tables.value = [];
    tableData.value = [];
    
    try {
        const res = await fetch('/api/v1/data_query/tables');
        if (res.ok) {
            const data = await res.json();
            tables.value = data.tables;
        } else {
            const err = await res.json();
            message.error('获取表列表失败: ' + (err.detail || '请先连接数据库'));
        }
    } catch (e) {
        message.error('网络错误: ' + e.message);
    } finally {
        loadingTables.value = false;
    }
};

const fetchTableData = async (tableName) => {
    selectedTable.value = tableName;
    // Reset conversion status
    convertStatus.status = 'idle';
    convertStatus.progress = 0;
    convertStatus.message = '';
    convertStatus.jobId = null;
    if (pollInterval) clearInterval(pollInterval);

    loadingTableData.value = true;
    tableData.value = [];
    tableColumns.value = [];
    
    try {
        const res = await fetch(`/api/v1/data_query/table/${tableName}/data`);
        if (res.ok) {
            const data = await res.json();
            if (data.columns && data.columns.length > 0) {
                tableColumns.value = data.columns.map(col => ({ 
                    title: col, 
                    key: col
                }));
                
                tableData.value = data.data.map((row, index) => {
                    const rowData = { key: index };
                    data.columns.forEach((col, i) => {
                        rowData[col] = row[i];
                    });
                    return rowData;
                });
            } else {
                 message.info('表为空或无列定义');
            }
        } else {
            const err = await res.json();
            message.error('获取表数据失败: ' + (err.detail || '未知错误'));
        }
    } catch (e) {
        message.error('网络错误: ' + e.message);
    } finally {
        loadingTableData.value = false;
    }
};

// --- Connection Actions ---

const validateForm = () => {
    if (!configForm.value.type) return '请选择数据库类型';
    if (configForm.value.type === 'sqlite' && !configForm.value.path) return '请输入文件路径';
    if (configForm.value.type !== 'sqlite') {
        if (!configForm.value.host) return '请输入主机地址';
        if (!configForm.value.user) return '请输入用户名';
    }
    return null;
};

const testConnection = async () => {
    testResult.value = null;
    const error = validateForm();
    if (error) {
        testResult.value = { success: false, message: error };
        return;
    }
    
    testing.value = true;
    try {
        const res = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configForm.value)
        });
        
        if (res.ok) {
            testResult.value = { success: true, message: '连接测试成功！' };
        } else {
            const err = await res.json();
            testResult.value = { success: false, message: '连接失败: ' + (err.detail || '未知错误') };
        }
    } catch (e) {
        testResult.value = { success: false, message: '网络错误: ' + e.message };
    } finally {
        testing.value = false;
    }
};

const saveAndConnect = async () => {
    const error = validateForm();
    if (error) {
        message.warning(error);
        return;
    }
    
    connecting.value = true;
    testResult.value = null;
    
    try {
        // 1. Connect
        const connRes = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configForm.value)
        });
        
        if (!connRes.ok) {
            const err = await connRes.json();
            throw new Error(err.detail || '连接失败');
        }
        
        // 2. Save Config
        const saveRes = await fetch('/api/v1/data_query/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configForm.value)
        });
        
        if (!saveRes.ok) {
            message.warning('连接成功，但配置保存失败');
        } else {
            message.success('配置已保存并连接成功');
            showCreateModal.value = false;
            fetchConfig();
        }
        
    } catch (e) {
        testResult.value = { success: false, message: e.message };
        message.error(e.message);
    } finally {
        connecting.value = false;
    }
};

onMounted(() => {
    fetchConfig();
});

// --- Graph Conversion Logic ---
const convertStatus = reactive({
    status: 'idle', // idle, running, completed, failed
    progress: 0,
    message: '',
    jobId: null
});

let pollInterval = null;

const convertTableToGraph = async () => {
    if (!selectedTable.value) return;
    
    convertStatus.status = 'running';
    convertStatus.progress = 0;
    convertStatus.message = '正在启动任务...';
    
    try {
        const res = await fetch(`/api/v1/data_query/table/${selectedTable.value}/convert_to_graph`, {
            method: 'POST'
        });
        if (res.ok) {
            const data = await res.json();
            convertStatus.jobId = data.job_id;
            startPolling();
        } else {
            const err = await res.json();
            throw new Error(err.detail || '启动失败');
        }
    } catch (e) {
        convertStatus.status = 'failed';
        convertStatus.message = e.message;
        message.error('转换任务启动失败: ' + e.message);
    }
};

const startPolling = () => {
    if (pollInterval) clearInterval(pollInterval);
    
    pollInterval = setInterval(async () => {
        if (!convertStatus.jobId) return;
        
        try {
            const res = await fetch(`/api/v1/data_query/conversion_status/${convertStatus.jobId}`);
            if (res.ok) {
                const data = await res.json();
                convertStatus.status = data.status;
                convertStatus.progress = data.progress;
                convertStatus.message = data.message;
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    if (data.status === 'completed') {
                        message.success('图谱转换成功！');
                    } else {
                        message.error('转换失败: ' + data.message);
                    }
                }
            }
        } catch (e) {
            console.error("Poll failed", e);
        }
    }, 1000);
};

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
});
</script>
