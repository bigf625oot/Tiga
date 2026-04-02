<template>
  <div class="h-full flex flex-col bg-background overflow-hidden">
    <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold tracking-tight">数据源管理</h2>
        <div class="h-4 w-px bg-border"></div>
        <p class="text-xs text-muted-foreground m-0 truncate max-w-xl">管理外部数据源连接配置。</p>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar bg-muted/10 flex flex-col">
      <div class="w-full flex flex-col gap-8 flex-1">
        <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
          <div class="hidden md:block w-full md:w-64"></div>

          <div class="flex items-center gap-3 w-full md:w-auto justify-end">
            <div class="relative w-full md:w-64 group">
              <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              <Input v-model="searchQuery" placeholder="搜索数据源..." class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50" />
              <button v-if="searchQuery" @click="searchQuery = ''" class="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors" aria-label="清空搜索">
                <X class="h-4 w-4" />
              </button>
            </div>

            <div class="h-4 w-px bg-border hidden md:block mx-1"></div>

            <Button @click="fetchConfig" variant="outline" size="icon" class="h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95 flex-shrink-0" title="刷新列表">
              <RefreshCw class="h-4 w-4 text-muted-foreground" :class="{ 'animate-spin': loading }" />
            </Button>

            <Button @click="openCreateModal" size="sm" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
              <Plus class="w-3.5 h-3.5" />
              新建连接
            </Button>
          </div>
        </div>

        <div class="flex flex-col gap-8 px-6 pb-6 flex-1">
          <div v-if="searchQuery" class="flex items-center gap-2">
            <h3 class="text-lg font-semibold tracking-tight text-foreground">搜索结果</h3>
            <span class="text-sm text-muted-foreground">({{ displayConfigs.length }})</span>
          </div>

          <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <div v-for="i in 4" :key="i" class="h-[200px] rounded-xl border bg-card/50 animate-pulse"></div>
          </div>

          <div v-else-if="displayConfigs.length === 0" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto">
            <div class="w-12 h-12 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
              <Search v-if="searchQuery" class="w-10 h-10 text-muted-foreground/50" />
              <!-- <Database v-else class="w-10 h-10 text-muted-foreground/50" /> -->
              <img src="/Placeholder/null_file.svg" alt="Placeholder" class="w-full h-full object-cover" />
            </div>
            <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">{{ searchQuery ? '未找到相关数据源' : '暂无数据源连接' }}</h3>
            <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">{{ searchQuery ? '请尝试更换关键词搜索，或清空筛选条件。' : '当前暂无连接配置，您可以点击下方按钮创建一个新的数据源连接。' }}</p>
            <Button v-if="!searchQuery" @click="openCreateModal" class="px-8 shadow-sm hover:scale-105 transition-transform">
              <Plus class="w-4 h-4 mr-2" />
              立即创建
            </Button>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start">
            <Card v-for="(config, idx) in displayConfigs" :key="idx" class="group cursor-pointer hover:border-primary/50 transition-all duration-300 overflow-hidden flex flex-col justify-between h-[280px]" @click="viewTables(config)">
              <CardContent class="p-6">
                <div class="flex justify-between items-start mb-4">
                  <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-lg flex items-center justify-center shrink-0 bg-purple-500 shadow-sm">
                      <Database class="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 class="font-bold text-base text-foreground line-clamp-1" :title="config.name || config.host">
                        {{ config.name || config.host || '未命名连接' }}
                      </h3>
                      <div class="flex items-center gap-1.5 mt-1">
                        <div class="w-2 h-2 rounded-full" :class="config.host || config.path ? 'bg-green-500' : 'bg-gray-500'"></div>
                        <span class="text-xs text-muted-foreground font-medium">{{ config.host || config.path ? '运行中' : '未连接' }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4 m-1 mt-6">
                  <div>
                    <div class="text-xs text-muted-foreground mb-1">数据表</div>
                    <div class="flex items-baseline gap-1">
                      <span class="text-2xl font-bold text-purple-600 leading-none">{{ tables.length }}</span>
                      <span class="text-xs text-muted-foreground">张</span>
                    </div>
                  </div>
                  <div>
                    <div class="text-xs text-muted-foreground mb-1">总记录数</div>
                    <div class="flex items-baseline gap-1">
                      <span class="text-2xl font-bold text-foreground leading-none">{{ totalRecords }}</span>
                    </div>
                  </div>
                </div>

                <div class="mt-4">
                  <Badge variant="outline" class="gap-1.5 text-xs font-normal text-muted-foreground px-2.5 py-0.5 h-6 rounded-full bg-muted/30 uppercase">
                    <Database class="w-3 h-3" />
                    {{ config.type || '未知类型' }}
                  </Badge>
                </div>
              </CardContent>

              <CardFooter class="p-0 border-t bg-muted/5 h-10 min-h-[40px]">
                <Button variant="ghost" class="flex-1 h-full rounded-none text-xs text-muted-foreground hover:text-primary hover:bg-transparent" @click.stop="editConfig(config)">
                  <Pencil class="w-3.5 h-3.5 mr-2" />
                  编辑
                </Button>
                <div class="w-px h-4 bg-border my-auto"></div>
                <Button variant="ghost" class="flex-1 h-full rounded-none text-xs text-muted-foreground hover:text-destructive hover:bg-transparent" disabled>
                  <Trash2 class="w-3.5 h-3.5 mr-2" />
                  删除
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </div>
    </div>

    <!-- Tables Preview Modal -->
    <Dialog v-model:open="showTablesModal">
        <DialogContent class="max-w-[90vw] w-[1200px] h-[85vh] p-0 flex flex-col gap-0 overflow-hidden">
            <DialogHeader class="px-6 py-4 border-b border-border bg-card">
                <DialogTitle class="text-base flex items-center gap-2">
                    <Database class="w-4 h-4 text-primary" />
                    数据库表预览
                    <Badge variant="outline" class="ml-2 font-normal text-xs">{{ currentConfig.name || currentConfig.host }}</Badge>
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
                        <div v-else-if="tables.length === 0" class="flex flex-col items-center justify-center py-10 text-center">
                            <div class="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mb-4 ring-8 ring-muted/20">
                                <TableIcon class="w-7 h-7 text-muted-foreground/50" />
                            </div>
                            <div class="text-xs font-medium text-foreground">暂无数据表</div>
                            <div class="text-[11px] text-muted-foreground mt-1">请确认连接已可用，或稍后重试。</div>
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
                    <div v-if="!selectedTable" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto">
                        <div class="w-24 h-24 bg-muted/50 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
                            <TableIcon class="w-10 h-10 text-muted-foreground/50" />
                        </div>
                        <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">请选择数据表</h3>
                        <p class="text-muted-foreground text-sm max-w-sm mx-auto">从左侧列表选择一张表查看详情与转换状态。</p>
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
        <DialogContent class="sm:max-w-[600px] max-h-[90vh] overflow-hidden flex flex-col p-0 gap-0">
            <DialogHeader class="px-6 py-4 border-b">
                <DialogTitle>{{ isEdit ? '编辑数据库连接' : '新建数据库连接' }}</DialogTitle>
                <DialogDescription>
                    配置结构化数据库连接参数。
                </DialogDescription>
            </DialogHeader>
            
            <ScrollArea class="flex-1">
                <div class="p-6 space-y-4">
                    <div class="space-y-2">
                        <Label>连接名称 <span class="text-destructive">*</span></Label>
                        <Input v-model="configForm.name" placeholder="例如：生产环境从库" />
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
                                <!-- Add more types as needed -->
                            </SelectContent>
                        </Select>
                    </div>

                    <!-- SQLite Form -->
                    <template v-if="configForm.type === 'sqlite'">
                        <div class="space-y-2">
                            <Label>文件路径</Label>
                            <Input v-model="configForm.path" placeholder="e.g. /data/app.db" />
                            <p class="text-[10px] text-muted-foreground">请输入SQLite数据库文件的绝对路径</p>
                        </div>
                    </template>

                    <!-- Standard DB Form -->
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
                            <Label>数据库名 (Schema)</Label>
                            <Input v-model="configForm.database" placeholder="默认数据库" />
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-2">
                                <Label>用户名</Label>
                                <Input v-model="configForm.user" placeholder="root" />
                            </div>
                            <div class="space-y-2">
                                <Label>密码</Label>
                                <Input type="password" v-model="configForm.password" placeholder="••••••" />
                            </div>
                        </div>

                        <!-- Advanced Options (Accordion Style) -->
                        <Accordion type="single" collapsible class="w-full border rounded-lg bg-muted/10 mt-4">
                            <AccordionItem value="advanced" class="border-b-0">
                                <AccordionTrigger class="px-4 py-2 text-sm hover:no-underline">
                                    高级设置 (Advanced Settings)
                                </AccordionTrigger>
                                <AccordionContent class="px-4 pb-4 pt-2 space-y-4">
                                    <!-- 1. SSL -->
                                    <div class="space-y-3 border-b pb-4">
                                        <div class="flex items-center justify-between">
                                            <Label class="text-base">连接加密 (SSL)</Label>
                                            <Switch :checked="configForm.ssl" @update:checked="(v) => configForm.ssl = v" />
                                        </div>
                                        <div v-if="configForm.ssl" class="space-y-3 animate-in fade-in slide-in-from-top-2">
                                            <div class="space-y-2">
                                                <Label>SSL 模式</Label>
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

                                    <!-- 2. SSH Tunnel -->
                                    <div class="space-y-3 border-b pb-4">
                                        <div class="flex items-center justify-between">
                                            <Label class="text-base">SSH 隧道 (SSH Tunnel)</Label>
                                            <Switch :checked="configForm.ssh" @update:checked="(v) => configForm.ssh = v" />
                                        </div>
                                        <div v-if="configForm.ssh" class="space-y-3 animate-in fade-in slide-in-from-top-2">
                                            <div class="grid grid-cols-3 gap-4">
                                                <div class="col-span-2 space-y-2">
                                                    <Label>SSH 主机</Label>
                                                    <Input v-model="configForm.ssh_host" placeholder="ssh.example.com" />
                                                </div>
                                                <div class="space-y-2">
                                                    <Label>SSH 端口</Label>
                                                    <Input v-model="configForm.ssh_port" type="number" />
                                                </div>
                                            </div>
                                            <div class="space-y-2">
                                                <Label>SSH 用户名</Label>
                                                <Input v-model="configForm.ssh_user" />
                                            </div>
                                            <div class="space-y-2">
                                                <Label>认证方式</Label>
                                                <div class="flex items-center space-x-4 mb-2">
                                                    <div class="flex items-center space-x-2">
                                                        <input type="radio" id="ssh-pwd" value="password" v-model="configForm.ssh_auth_type" class="accent-primary" />
                                                        <label for="ssh-pwd" class="text-sm">密码</label>
                                                    </div>
                                                    <div class="flex items-center space-x-2">
                                                        <input type="radio" id="ssh-key" value="key" v-model="configForm.ssh_auth_type" class="accent-primary" />
                                                        <label for="ssh-key" class="text-sm">私钥</label>
                                                    </div>
                                                </div>
                                                
                                                <Input v-if="configForm.ssh_auth_type === 'password'" type="password" v-model="configForm.ssh_password" placeholder="SSH Password" />
                                                <textarea 
                                                    v-else 
                                                    v-model="configForm.ssh_key" 
                                                    rows="3" 
                                                    class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                                    placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                                                ></textarea>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- 3. Connection Pool -->
                                    <div class="space-y-4 pb-4">
                                        <Label class="text-base">连接池设置</Label>
                                        <div class="space-y-4 px-1">
                                            <div class="space-y-3">
                                                <div class="flex justify-between">
                                                    <Label>最大连接数: {{ configForm.pool_size }}</Label>
                                                </div>
                                                <Slider
                                                    v-model="configForm.pool_size_array"
                                                    :max="100"
                                                    :min="1"
                                                    :step="1"
                                                    @update:modelValue="(v) => configForm.pool_size = v[0]"
                                                />
                                            </div>
                                            <div class="space-y-2">
                                                <Label>超时时间 (秒)</Label>
                                                <Input v-model="configForm.timeout" type="number" />
                                            </div>
                                        </div>
                                    </div>
                                    
                                        <!-- 4. Charset -->
                                    <div v-if="configForm.type === 'mysql'" class="space-y-2 pb-4 border-b">
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

                                    <!-- 5. Security & Permissions -->
                                    <div class="space-y-3 pt-2">
                                        <div class="flex items-center gap-2 mb-2">
                                            <Shield class="w-4 h-4 text-muted-foreground" />
                                            <Label class="text-base">安全与权限设置</Label>
                                        </div>
                                        <div class="space-y-4 px-1">
                                            <div class="space-y-2">
                                                <Label>允许访问的表 (Allowed Tables)</Label>
                                                <Input v-model="configForm.allowed_tables_str" placeholder="如: users, orders (用逗号分隔，留空表示允许所有)" />
                                            </div>
                                            <div class="space-y-2">
                                                <Label>敏感字段脱敏 (Sensitive Fields)</Label>
                                                <Input v-model="configForm.sensitive_fields_str" placeholder="如: phone, email, id_card (用逗号分隔)" />
                                            </div>
                                        </div>
                                    </div>

                                </AccordionContent>
                            </AccordionItem>
                        </Accordion>
                    </template>

                    <!-- Status Message -->
                    <div v-if="testResult" class="p-3 rounded-md text-xs flex items-start gap-2" :class="testResult.success ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'">
                        <component :is="testResult.success ? Check : XCircle" class="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span class="break-all">{{ testResult.message }}</span>
                    </div>
                </div>
            </ScrollArea>

            <DialogFooter class="px-6 py-4 border-t bg-muted/20 sm:justify-between">
                <Button variant="outline" @click="testConnection" :disabled="testing || connecting">
                    <Loader2 v-if="testing" class="w-3.5 h-3.5 mr-2 animate-spin" />
                    测试连接
                </Button>
                <div class="flex gap-2">
                    <Button variant="ghost" @click="showCreateModal = false">取消</Button>
                    <Button @click="saveAndConnect" :disabled="testing || connecting">
                        <Loader2 v-if="connecting" class="w-3.5 h-3.5 mr-2 animate-spin" />
                        保存并连接
                    </Button>
                </div>
            </DialogFooter>
        </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, onUnmounted, computed } from 'vue';
import { message } from 'ant-design-vue';
// Icons
import { 
    Plus, 
    Database, 
    Table as TableIcon, 
    Edit2, 
    Trash2, 
    Loader2, 
    Search, 
    RefreshCw,
    X,
    ChevronDown, 
    Check, 
    XCircle,
    Share2,
    ArrowRight,
    Settings2,
    Pencil,
    Shield
} from 'lucide-vue-next';

// Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
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
import { Switch } from '@/components/ui/switch';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Slider } from '@/components/ui/slider';

const showCreateModal = ref(false);
const isEdit = ref(false);
const loading = ref(false);
const emit = defineEmits(['navigate']);
const currentConfig = ref({});
const searchQuery = ref('');

// Computed configs for list view
const displayConfigs = computed(() => {
    // Currently API only returns one config object
    // Transform it to array for consistent list rendering
    let list = [];
    if (currentConfig.value && (currentConfig.value.host || currentConfig.value.path)) {
        list = [currentConfig.value];
    }
    
    if (!searchQuery.value) return list;
    
    const query = searchQuery.value.toLowerCase();
    return list.filter(cfg => 
        (cfg.name && cfg.name.toLowerCase().includes(query)) ||
        (cfg.host && cfg.host.toLowerCase().includes(query)) ||
        (cfg.type && cfg.type.toLowerCase().includes(query))
    );
});

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
    pool_size_array: [5], // For Slider
    charset: 'utf8mb4',
    // Advanced fields matching DataSourceManagement
    ssl: false,
    ssl_mode: 'disable',
    ssh: false,
    ssh_host: '',
    ssh_port: 22,
    ssh_user: '',
    ssh_auth_type: 'password',
    ssh_password: '',
    ssh_key: ''
});

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
                // Also fetch tables to update metrics if connected
                if (data.host || data.path) {
                    await fetchTablesForMetrics();
                }
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
        pool_size_array: [5],
        charset: 'utf8mb4',
        ssl: false,
        ssl_mode: 'disable',
        ssh: false,
        ssh_host: '',
        ssh_port: 22,
        ssh_user: '',
        ssh_auth_type: 'password',
        ssh_password: '',
        ssh_key: '',
        allowed_tables_str: '',
        sensitive_fields_str: ''
    };
    testResult.value = null;
    showCreateModal.value = true;
};

const editConfig = (config) => {
    isEdit.value = true;
    const cfg = config || currentConfig.value;
    configForm.value = {
        ...cfg,
        pool_size_array: [cfg.pool_size || 5],
        // Default missing fields if not present
        ssl: cfg.ssl || false,
        ssh: cfg.ssh || false,
        ssh_port: cfg.ssh_port || 22,
        ssh_auth_type: cfg.ssh_auth_type || 'password',
        allowed_tables_str: (cfg.allowed_tables || []).join(', '),
        sensitive_fields_str: (cfg.sensitive_fields || []).join(', ')
    };
    testResult.value = null;
    showCreateModal.value = true;
};

// --- Table View Logic ---
const showTablesModal = ref(false);
const tables = ref([]);
const totalRecords = ref(0);
const loadingTables = ref(false);
const selectedTable = ref(null);
const tableData = ref([]);
const tableColumns = ref([]);
const loadingTableData = ref(false);

const fetchTablesForMetrics = async () => {
    try {
        const res = await fetch('/api/v1/data_query/tables');
        if (res.ok) {
            const data = await res.json();
            tables.value = data.tables || [];
            if (data.stats) {
                totalRecords.value = data.stats.total_records || 0;
            }
        }
    } catch (e) {
        console.error('Fetch tables error', e);
    }
};

const viewTables = async (config) => {
    if (config) {
        currentConfig.value = config;
    }
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
            if (data.stats) {
                totalRecords.value = data.stats.total_records || 0;
            }
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
    
    const payload = {
        ...configForm.value,
        allowed_tables: configForm.value.allowed_tables_str ? configForm.value.allowed_tables_str.split(',').map(s => s.trim()).filter(Boolean) : [],
        sensitive_fields: configForm.value.sensitive_fields_str ? configForm.value.sensitive_fields_str.split(',').map(s => s.trim()).filter(Boolean) : []
    };
    
    try {
        const res = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: payload })
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
    
    // Parse arrays
    const payload = {
        ...configForm.value,
        allowed_tables: configForm.value.allowed_tables_str ? configForm.value.allowed_tables_str.split(',').map(s => s.trim()).filter(Boolean) : [],
        sensitive_fields: configForm.value.sensitive_fields_str ? configForm.value.sensitive_fields_str.split(',').map(s => s.trim()).filter(Boolean) : []
    };
    
    try {
        // 1. Connect
        const connRes = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: payload })
        });
        
        if (!connRes.ok) {
            const err = await connRes.json();
            throw new Error(err.detail || '连接失败');
        }
        
        // 2. Save Config
        const saveRes = await fetch('/api/v1/data_query/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
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
