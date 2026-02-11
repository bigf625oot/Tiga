<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header -->
    <div class="px-10 pt-12 pb-6">
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">数据库</h2>
          <p class="text-[#86868B] text-lg font-medium">管理数据库连接配置，支持 MySQL, PostgreSQL 等多种数据库。</p>
        </div>
        <button 
          @click="openCreateModal" 
          class="bg-[#0071e3] text-white px-5 py-2.5 rounded-full hover:bg-[#0077ED] transition-all shadow-sm hover:shadow-md font-medium flex items-center gap-2 active:scale-95 text-sm"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
          新建连接
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-hidden px-10 pb-10 bg-white">
      
      <!-- Connection List -->
      <div class="h-full flex flex-col w-full">
        <div class="bg-white rounded-xl  overflow-hidden flex-1 flex flex-col p-4">
           <!-- Header -->
           <div class="flex items-center bg-[#f9f9fa] h-[38px] rounded px-3 text-[14px] font-medium text-[#2a2f3c]">
              <div class="flex-1 flex items-center gap-2 relative">
                  <span>连接名称/Host</span>
                  <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
              </div>
              <div class="w-[100px] px-3 relative">
                  <span>类型</span>
                  <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
              </div>
              <div class="w-[80px] px-3 relative">
                  <span>端口</span>
                  <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
              </div>
              <div class="w-[120px] px-3 relative">
                  <span>用户</span>
                  <div class="absolute right-0 top-3 bottom-3 w-[1px] bg-[#e5e6eb]"></div>
              </div>
              <div class="w-[220px] px-3 text-right">
                  <span>操作</span>
              </div>
           </div>
           
           <!-- List Content -->
           <div class="overflow-y-auto flex-1 mt-2">
             <div v-if="loading" class="flex flex-col px-3">
                <div v-for="i in 3" :key="i" class="flex items-center border-b border-slate-50 py-4 gap-4">
                    <a-skeleton-avatar active size="small" shape="square" />
                    <a-skeleton active :title="false" :paragraph="{ rows: 1, width: '100%' }" class="flex-1" />
                </div>
             </div>
             <!-- Mock Data or Real Data if available. Since backend seems to have single config, we show it if exists -->
             <div v-else-if="!currentConfig.host && !currentConfig.path" class="flex flex-col items-center justify-center py-20 text-[#86868B]">
                <div class="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 border border-slate-100">
                    <svg class="w-8 h-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                </div>
                <span class="text-sm font-medium opacity-80">暂无连接配置</span>
             </div>
             <div v-else class="flex flex-col">
                <div class="flex items-center border-b border-slate-50 hover:bg-[#eeeeee] transition-colors py-2 px-3 text-sm text-[#2a2f3c] group">
                   <div class="flex-1 flex items-center gap-2 overflow-hidden">
                        <div class="w-6 h-6 flex items-center justify-center bg-white rounded">
                            <svg class="w-3 h-3 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                        </div>
                        <span class="truncate text-[14px]">{{ currentConfig.name || currentConfig.host || currentConfig.path }}</span>
                   </div>
                   <div class="w-[100px] px-3">
                      <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-xs border border-slate-200">{{ currentConfig.type }}</span>
                   </div>
                   <div class="w-[80px] px-3 text-slate-500">{{ currentConfig.port || '-' }}</div>
                   <div class="w-[120px] px-3 text-slate-500">{{ currentConfig.user || '-' }}</div>
                   <div class="w-[220px] px-3 flex justify-end items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <a-button type="text" size="small" @click="viewTables" class="!px-0 !h-auto !text-slate-500 hover:!text-blue-600">查看表</a-button>
                      <a-button type="text" size="small" @click="editConfig" class="!px-0 !h-auto !text-slate-500 hover:!text-blue-600">编辑</a-button>
                      <a-button type="text" size="small" danger class="!px-0 !h-auto">删除</a-button>
                   </div>
                </div>
             </div>
           </div>
        </div>
      </div>
    </div>

    <!-- Tables Preview Modal -->
    <a-modal 
        v-model:open="showTablesModal" 
        title="数据库表预览" 
        width="1200px" 
        :footer="null"
        class="tables-preview-modal"
    >
        <div class="flex h-[600px] -mx-6 -mb-6 mt-2 border-t border-slate-100">
            <!-- Table List Sidebar -->
            <div class="w-[240px] border-r border-slate-100 overflow-y-auto bg-slate-50 p-2">
                <div v-if="loadingTables" class="flex justify-center py-10">
                    <a-spin />
                </div>
                <div v-else-if="tables.length === 0" class="text-center py-10 text-slate-400 text-sm">
                    暂无数据表
                </div>
                <div v-else class="space-y-0.5">
                    <div 
                        v-for="t in tables" :key="t"
                        @click="fetchTableData(t)"
                        class="px-3 py-2 cursor-pointer rounded-lg text-sm truncate transition-colors"
                        :class="selectedTable === t ? 'bg-white shadow-sm text-blue-600 font-medium' : 'text-slate-600 hover:bg-slate-100'"
                    >
                        {{ t }}
                    </div>
                </div>
            </div>
            
            <!-- Data View -->
            <div class="flex-1 flex flex-col overflow-hidden bg-white">
                <div v-if="!selectedTable" class="flex-1 flex flex-col items-center justify-center text-slate-400">
                    <svg class="w-12 h-12 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                    <span>请选择左侧数据表查看详情</span>
                </div>
                <div v-else class="flex-1 flex flex-col overflow-hidden">
                    <div class="px-4 py-3 border-b border-slate-100 flex justify-between items-center bg-white">
                        <div class="flex items-center gap-3">
                            <h3 class="font-medium text-base text-slate-800">{{ selectedTable }}</h3>
                            
                            <!-- Graph Conversion Button -->
                            <div class="flex items-center gap-2">
                                <a-tooltip :title="convertStatus.status === 'completed' ? '转换完成' : '转换为图谱'">
                                    <button 
                                        @click="convertTableToGraph"
                                        class="p-1.5 rounded-md transition-all relative group flex items-center justify-center border"
                                        :class="[
                                            convertStatus.status === 'running' ? 'bg-blue-50 border-blue-100 text-blue-600' : 
                                            convertStatus.status === 'completed' ? 'bg-green-50 border-green-100 text-green-600' :
                                            convertStatus.status === 'failed' ? 'bg-red-50 border-red-100 text-red-600' :
                                            'bg-white border-slate-200 text-slate-400 hover:text-blue-600 hover:border-blue-200'
                                        ]"
                                        :disabled="convertStatus.status === 'running'"
                                    >
                                        <!-- Loading Icon -->
                                        <svg v-if="convertStatus.status === 'running'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        
                                        <!-- Success Icon -->
                                        <svg v-else-if="convertStatus.status === 'completed'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                        </svg>
                                        
                                        <!-- Error Icon -->
                                        <svg v-else-if="convertStatus.status === 'failed'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                        </svg>

                                        <!-- Default Graph Icon -->
                                        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
                                        </svg>
                                    </button>
                                </a-tooltip>
                                
                                <!-- Status Text -->
                                <div v-if="convertStatus.status !== 'idle'" class="flex flex-col">
                                    <div class="text-xs font-medium" 
                                        :class="[
                                            convertStatus.status === 'running' ? 'text-blue-600' : 
                                            convertStatus.status === 'completed' ? 'text-green-600' : 
                                            'text-red-600'
                                        ]">
                                        {{ convertStatus.status === 'running' ? '转换中' : convertStatus.status === 'completed' ? '转换完成' : '转换失败' }}
                                        <span v-if="convertStatus.status === 'running'">{{ convertStatus.progress }}%</span>
                                    </div>
                                    <!-- Optional: Show message on hover or always if it's short -->
                                </div>
                                
                                <!-- View Graph Button (only when completed) -->
                                <a-button 
                                    v-if="convertStatus.status === 'completed'" 
                                    type="link" 
                                    size="small" 
                                    class="!px-0 !h-auto text-xs"
                                    @click="$emit('navigate', 'knowledge_graph')"
                                >
                                    查看图谱 &rarr;
                                </a-button>
                            </div>
                        </div>
                        <span class="text-xs text-slate-400" v-if="tableData.length > 0">显示前 {{ tableData.length }} 条记录</span>
                    </div>
                    <div class="flex-1 overflow-hidden p-0 relative">
                        <a-table 
                            :columns="tableColumns" 
                            :dataSource="tableData" 
                            :loading="loadingTableData"
                            :scroll="{ x: 'max-content', y: 500 }" 
                            size="small" 
                            :pagination="false"
                            class="h-full"
                        />
                    </div>
                </div>
            </div>
        </div>
    </a-modal>

    <!-- Create/Edit Modal -->
    <a-modal 
        v-model:open="showCreateModal" 
        :title="isEdit ? '编辑数据库配置' : '新建数据库配置'" 
        :footer="null" 
        width="600px"
        destroyOnClose
    >
        <div class="py-4">
             <a-form 
                ref="formRef"
                :model="configForm" 
                :rules="rules"
                layout="vertical" 
                class="space-y-4"
            >
                <a-form-item label="连接名称" name="name">
                    <a-input v-model:value="configForm.name" placeholder="请输入连接名称（选填）" />
                </a-form-item>

                <a-form-item label="数据库类型" name="type">
                    <a-select v-model:value="configForm.type" @change="handleTypeChange">
                        <a-select-option value="sqlite">SQLite</a-select-option>
                        <a-select-option value="postgresql">PostgreSQL</a-select-option>
                        <a-select-option value="mysql">MySQL</a-select-option>
                    </a-select>
                </a-form-item>
                
                <template v-if="configForm.type === 'sqlite'">
                    <a-form-item label="文件路径" name="path" help="请输入SQLite数据库文件的绝对路径">
                        <a-input v-model:value="configForm.path" placeholder="e.g. C:/data/app.db" />
                    </a-form-item>
                </template>
                
                <template v-else>
                    <div class="grid grid-cols-3 gap-3">
                        <div class="col-span-2">
                            <a-form-item label="主机地址" name="host">
                                <a-input v-model:value="configForm.host" placeholder="localhost" />
                            </a-form-item>
                        </div>
                        <div>
                            <a-form-item label="端口" name="port">
                                <a-input-number v-model:value="configForm.port" class="w-full" :controls="false" />
                            </a-form-item>
                        </div>
                    </div>
                    
                    <a-form-item label="用户名" name="user">
                        <a-input v-model:value="configForm.user" placeholder="root" />
                    </a-form-item>
                    
                    <a-form-item label="密码" name="password">
                        <a-input-password v-model:value="configForm.password" placeholder="请输入密码" />
                    </a-form-item>

                    <!-- Advanced Options Toggle -->
                    <div class="pt-2">
                        <div 
                            @click="showAdvanced = !showAdvanced" 
                            class="flex items-center gap-1 text-xs text-blue-600 cursor-pointer hover:text-blue-700 select-none font-medium"
                        >
                            <span>更多连接配置</span>
                            <svg class="w-3 h-3 transition-transform duration-200" :class="showAdvanced ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                        
                        <div v-show="showAdvanced" class="mt-4 space-y-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
                            <a-form-item label="数据库名称" name="database">
                                <a-input v-model:value="configForm.database" placeholder="选填，默认连接postgres/mysql" />
                            </a-form-item>
                            
                            <div class="grid grid-cols-2 gap-3">
                                <a-form-item label="连接超时 (秒)" name="timeout">
                                    <a-input-number v-model:value="configForm.timeout" class="w-full" :min="1" />
                                </a-form-item>
                                <a-form-item label="连接池大小" name="pool_size">
                                    <a-input-number v-model:value="configForm.pool_size" class="w-full" :min="1" />
                                </a-form-item>
                            </div>
                            
                            <a-form-item v-if="configForm.type === 'mysql'" label="字符集" name="charset">
                                <a-select v-model:value="configForm.charset">
                                    <a-select-option value="utf8mb4">utf8mb4</a-select-option>
                                    <a-select-option value="utf8">utf8</a-select-option>
                                    <a-select-option value="latin1">latin1</a-select-option>
                                </a-select>
                            </a-form-item>
                            
                            <a-form-item v-if="configForm.type === 'postgresql'" label="SSL 模式" name="ssl_mode">
                                <a-select v-model:value="configForm.ssl_mode">
                                    <a-select-option value="disable">Disable</a-select-option>
                                    <a-select-option value="require">Require</a-select-option>
                                    <a-select-option value="verify-ca">Verify CA</a-select-option>
                                    <a-select-option value="verify-full">Verify Full</a-select-option>
                                </a-select>
                            </a-form-item>
                        </div>
                    </div>
                </template>
                
                <!-- Buttons -->
                <div class="flex flex-col gap-3 pt-4 border-t border-slate-100 mt-4">
                    <a-button @click="testConnection" :loading="testing" class="w-full" :disabled="connecting">
                        <template #icon>
                            <svg class="w-4 h-4 mr-2 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        </template>
                        测试连接
                    </a-button>
                    
                    <a-button type="primary" @click="saveAndConnect" :loading="connecting" class="w-full h-10 font-medium bg-blue-600" :disabled="testing">
                        保存配置并连接
                    </a-button>
                </div>
            </a-form>

             <!-- Status Messages -->
            <div v-if="testResult" class="mt-4 p-3 rounded-lg text-xs flex items-start gap-2" :class="testResult.success ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'">
                <span class="mt-0.5 text-lg leading-none">{{ testResult.success ? '✓' : '✗' }}</span>
                <span class="break-all">{{ testResult.message }}</span>
            </div>
        </div>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, onMounted, reactive, onUnmounted } from 'vue';
import { message } from 'ant-design-vue';

const showCreateModal = ref(false);
const isEdit = ref(false);
const loading = ref(false);
const emit = defineEmits(['navigate']);
const currentConfig = ref({}); // Stores the fetched config

// Form State
const formRef = ref();
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
const exporting = ref(false);
const testResult = ref(null);

const rules = {
    type: [{ required: true, message: '请选择数据库类型' }],
    path: [{ required: true, message: '请输入文件路径', trigger: 'blur' }],
    host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
    port: [{ required: true, message: '请输入端口号' }],
    user: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
};

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
                // If editing, we would load this into configForm
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
    // Reset form
    configForm.value = {
        name: '',
        type: 'mysql', // Default to MySQL as per screenshot
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
    // Check if connected first? For now assume user can click button only if connection exists
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
    // Reset conversion status when switching tables
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
            // Transform for Ant Design Table
            if (data.columns && data.columns.length > 0) {
                tableColumns.value = data.columns.map(col => ({ 
                    title: col, 
                    dataIndex: col, 
                    key: col, 
                    width: 150, 
                    ellipsis: true,
                    resizable: true,
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

// --- Actions from SmartDataQuery ---

const testConnection = async () => {
    testResult.value = null;
    try {
        await formRef.value.validate();
    } catch (error) {
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
            message.success('连接测试成功');
        } else {
            const err = await res.json();
            testResult.value = { success: false, message: '连接失败: ' + (err.detail || '未知错误') };
            message.error('连接测试失败');
        }
    } catch (e) {
        testResult.value = { success: false, message: '网络错误: ' + e.message };
        message.error('连接测试失败');
    } finally {
        testing.value = false;
    }
};

const saveAndConnect = async () => {
    try {
        await formRef.value.validate();
    } catch (error) {
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
            fetchConfig(); // Refresh list
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