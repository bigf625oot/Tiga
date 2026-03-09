<template>
  <div class="h-full w-full flex flex-col bg-background text-foreground transition-colors duration-300">
    <!-- Header -->
    <div class="px-4 py-3 flex items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold tracking-tight">数据源管理</h2>
        <div class="h-4 w-px bg-border"></div>
        <p class="text-muted-foreground text-xs truncate">
          管理外部数据源连接配置
        </p>
      </div>
      <div class="flex items-center gap-4">
        <!-- Theme Toggle could go here -->
      </div>
    </div>

    <!-- Toolbar -->
    <div class="px-8 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-4 w-full md:w-auto">
        <div class="relative flex-1 md:w-96">
          <div class="absolute inset-y-0 left-0 p-4 flex items-center pointer-events-none">
            <Search class="w-4 h-4 text-muted-foreground" />
          </div>
          <Input 
            v-model="searchQuery"
            placeholder="搜索数据源名称或类型..." 
            class="pl-10"
          />
        </div>
        <span class="text-sm text-muted-foreground">
          共 <span class="font-semibold text-foreground">{{ dataSourceList.length }}</span> 个数据源
        </span>
      </div>

      <div class="flex items-center gap-4 w-full md:w-auto justify-end">
        <!-- Filter -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" class="gap-2">
              <Filter class="w-4 h-4" />
              {{ filterOptions.find(o => o.value === selectedType)?.label || '筛选' }}
              <ChevronDown class="w-4 h-4 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>按类型筛选</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              v-for="option in filterOptions" 
              :key="option.value"
              @click="selectedType = option.value"
            >
              <div class="flex items-center justify-between w-full">
                {{ option.label }}
                <Check v-if="selectedType === option.value" class="w-4 h-4" />
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <!-- Group -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" class="gap-2">
              {{ groupOptions.find(o => o.value === selectedGroup)?.label || '不分组' }}
              <ChevronDown class="w-4 h-4 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>分组显示</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              v-for="option in groupOptions" 
              :key="option.value"
              @click="selectedGroup = option.value"
            >
              <div class="flex items-center justify-between w-full">
                {{ option.label }}
                <Check v-if="selectedGroup === option.value" class="w-4 h-4" />
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <!-- Add Button -->
        <Button @click="openAddModal" class="gap-2">
          <Plus class="w-4 h-4" />
          添加数据源
        </Button>
      </div>
    </div>

    <!-- Content Grid -->
    <ScrollArea class="flex-1">
      <div class="px-8 pb-8 space-y-8">
      
      <!-- Loading Skeleton -->
      <div v-if="isLoading">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <SkeletonDataSource v-for="i in 8" :key="i" />
        </div>
      </div>

      <template v-else>
        <div v-for="group in groupedDataSources" :key="group.title">
          <h2 v-if="group.title" class="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            {{ group.title }}
            <Badge variant="secondary" class="rounded-full px-2">{{ group.items.length }}</Badge>
          </h2>
          
          <div v-if="group.items.length === 0" class="flex flex-col items-center justify-center min-h-[60vh] text-muted-foreground">
            <div class="bg-muted/50 p-6 rounded-full mb-4">
              <Search class="w-8 h-8 opacity-50" />
            </div>
            <p>没有找到相关数据源</p>
            <Button variant="link" @click="openAddModal" class="mt-2">立即创建</Button>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <Card 
              v-for="item in group.items" 
              :key="item.id"
              class="group cursor-pointer hover:border-primary/50 transition-all duration-300 overflow-hidden flex flex-col justify-between"
              @click="openDrawer(item)"
            >
            <CardContent class="p-6">
              <!-- Header -->
              <div class="flex justify-between items-start mb-4">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                    :class="getIconBgColor(item.type)"
                  >
                    <component :is="getIconComponent(item.type)" class="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 class="font-medium text-base text-foreground line-clamp-1" :title="item.name">{{ item.name }}</h3>
                    <div class="flex items-center gap-1.5 mt-1">
                      <div class="w-1.5 h-1.5 rounded-full" :class="getStatusColor(item.status)"></div>
                      <span class="text-xs text-muted-foreground">{{ getStatusText(item.status) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Metrics -->
              <div v-if="item.type === 'crawler'" class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div class="text-xs text-muted-foreground">今日抓取</div>
                  <div class="text-xl font-semibold text-green-600 leading-none mt-1">
                    {{ item.metrics?.today_count || 0 }} <span class="text-xs font-normal text-muted-foreground">条</span>
                  </div>
                </div>
                <div>
                  <div class="text-xs text-muted-foreground">成功率</div>
                  <div class="text-xl font-semibold text-foreground leading-none mt-1">
                    {{ item.metrics?.success_rate || 0 }} <span class="text-xs font-normal text-muted-foreground">%</span>
                  </div>
                </div>
              </div>

              <div v-else-if="item.type === 'sftp'" class="mb-4">
                <div class="flex justify-between items-end mb-2">
                    <div>
                      <div class="text-xs text-muted-foreground mb-0.5">今日接收文件</div>
                      <div class="text-xl font-semibold text-primary leading-none">
                        {{ item.metrics?.today_files || 0 }} <span class="text-xs font-normal text-muted-foreground">个</span>
                      </div>
                    </div>
                </div>
                <div class="bg-muted/50 rounded px-2 py-1.5 flex items-center gap-2 border border-border truncate" v-if="item.metrics?.current_file">
                    <div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shrink-0"></div>
                    <div class="text-xs text-muted-foreground truncate flex-1 font-mono" :title="item.metrics.current_file">
                        {{ item.metrics.current_file }}
                    </div>
                </div>
                <div v-else class="h-[26px] bg-muted/30 rounded border border-border flex items-center px-2 text-xs text-muted-foreground">
                    暂无接收任务
                </div>
              </div>

              <div v-else-if="item.type === 'database'" class="mb-4">
                <div class="grid grid-cols-2 gap-4 m-4">
                  <div>
                    <div class="text-xs text-muted-foreground mb-0.5">数据表</div>
                    <div class="text-xl font-semibold text-purple-600 leading-none">
                      {{ item.metrics?.table_count || 0 }} <span class="text-xs font-normal text-muted-foreground">张</span>
                    </div>
                  </div>
                  <div>
                    <div class="text-xs text-muted-foreground mb-0.5">总记录数</div>
                    <div class="text-xl font-semibold text-foreground leading-none" :title="item.metrics?.total_records?.toLocaleString()">
                      {{ formatNumber(item.metrics?.total_records || 0) }}
                    </div>
                  </div>
                </div>
                <div>
                    <Badge variant="outline" class="gap-1.5 text-xs font-medium text-muted-foreground">
                      <Database class="w-3.5 h-3.5" />
                      {{ item.metrics?.db_type || '未知类型' }}
                    </Badge>
                </div>
              </div>

              <div v-else-if="item.type === 'api'" class="mb-4">
                <div class="grid grid-cols-2 gap-4 m-4">
                  <div>
                    <div class="text-xs text-muted-foreground mb-0.5">接口调用</div>
                    <div class="text-xl font-semibold text-amber-500 leading-none">
                      {{ formatNumber(item.metrics?.api_calls || 0) }} <span class="text-xs font-normal text-muted-foreground">次</span>
                    </div>
                  </div>
                  <div>
                    <div class="text-xs text-muted-foreground mb-0.5">接入数据量</div>
                    <div class="text-xl font-semibold text-foreground leading-none">
                      {{ item.metrics?.data_volume || 0 }} <span class="text-xs font-normal text-muted-foreground">GB</span>
                    </div>
                  </div>
                </div>
                <div class="w-full bg-muted rounded-full h-1.5 mb-1.5 overflow-hidden">
                    <div class="bg-amber-500 h-1.5 rounded-full" style="width: 65%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-muted-foreground">
                    <span>配额使用率</span>
                    <span>65%</span>
                </div>
              </div>

              <div v-else class="flex justify-between items-end mb-4">
                <span class="text-xs text-muted-foreground">实时吞吐</span>
                <span class="text-xl font-semibold text-blue-400 leading-none">{{ item.throughput || '0/s' }}</span>
              </div>
            </CardContent>

            <!-- Action Footer -->
            <CardFooter class="p-0 border-t bg-muted/10">
              <Button 
                variant="ghost" 
                class="flex-1 h-9 rounded-none rounded-bl-lg text-muted-foreground hover:text-primary"
                @click.stop="editDataSource(item)"
              >
                <Pencil class="w-3.5 h-3.5 mr-2" />
                编辑
              </Button>
              <div class="w-px h-full bg-border"></div>
              <Button 
                variant="ghost" 
                class="flex-1 h-9 rounded-none rounded-br-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                @click.stop="confirmDelete(item)"
              >
                <Trash2 class="w-3.5 h-3.5 mr-2" />
                删除
              </Button>
            </CardFooter>
          </Card></div>
        </div>
      </template>
      </div>
    </ScrollArea>

    <!-- Right Drawer (Sheet) -->
    <Sheet v-model:open="showDrawer">
      <SheetContent class="w-[480px] sm:w-[540px] overflow-y-auto">
        <SheetHeader class="mb-6">
          <SheetTitle>{{ activeDataSource?.name }}</SheetTitle>
          <SheetDescription>
             ID: {{ activeDataSource?.id }} · {{ dataSourceTypes.find(t => t.value === activeDataSource?.type)?.label }}
          </SheetDescription>
        </SheetHeader>

        <div class="space-y-6">
           <div>
            <h4 class="text-sm font-semibold m-4 flex items-center gap-2">
              <Activity class="w-4 h-4 text-primary" />
              活跃流水线 ({{ relatedPipelines?.length || 0 }})
            </h4>
            
            <div class="space-y-3">
              <div 
                v-for="pipeline in relatedPipelines" 
                :key="pipeline.id"
                @click="navigateToEtlDetail(pipeline)"
                class="group p-4 rounded-lg border bg-card hover:border-primary/50 cursor-pointer transition-all relative overflow-hidden"
              >
                <div class="flex justify-between items-start mb-2">
                  <div class="font-medium group-hover:text-primary transition-colors">{{ pipeline.name }}</div>
                  <Badge 
                    :variant="pipeline.status === 'error' ? 'destructive' : 'secondary'"
                    class="uppercase"
                  >
                    {{ pipeline.status }}
                  </Badge>
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-xs text-muted-foreground m-4">
                  <div>
                    <div class="mb-0.5 opacity-70">已处理数据</div>
                    <div class="font-semibold text-foreground">{{ pipeline.processed.toLocaleString() }}</div>
                  </div>
                  <div>
                    <div class="mb-0.5 opacity-70">最后运行</div>
                    <div class="font-medium text-foreground">{{ pipeline.last_run }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions / Info -->
          <Alert class="bg-primary/10/50 border-blue-100">
            <Info class="w-4 h-4 text-primary" />
            <AlertTitle class="text-blue-900">数据源概览</AlertTitle>
            <AlertDescription class="text-blue-700">
              该数据源当前运行平稳，所有关联流水线均处于正常状态。最近一次同步发生在 2 分钟前。建议定期检查连接配置以确保稳定性。
            </AlertDescription>
          </Alert>
        </div>

        <SheetFooter class="mt-8">
           <Button @click="editDataSource(activeDataSource); showDrawer = false" class="w-full">
             <Settings2 class="w-4 h-4 mr-2" />
             编辑配置
           </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>

    <!-- Edit/Add Modal (Dialog) -->
    <Dialog v-model:open="showModal">
      <DialogContent class="sm:max-w-[600px] max-h-[90vh] overflow-hidden flex flex-col p-0 gap-0">
        <DialogHeader class="px-6 py-4 border-b">
          <DialogTitle>{{ currentStep === 1 ? '配置新数据源' : (isEditing ? '编辑数据源' : '完善数据源信息') }}</DialogTitle>
          <DialogDescription>
            {{ currentStep === 1 ? '选择数据源类型，然后配置连接参数' : '填写基本信息并上传相关截图' }}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea class="flex-1">
          <div class="p-6">
          <!-- Step 1: Select Type -->
          <div v-if="currentStep === 1" class="grid grid-cols-2 gap-4">
            <div 
              v-for="type in dataSourceTypes" 
              :key="type.value"
              @click="selectType(type.value)"
              class="relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 group flex flex-col h-32 justify-between hover:border-primary/50 hover:bg-muted/50"
              :class="[
                form.type === type.value 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted bg-card'
              ]"
            >
              <div v-if="form.type === type.value" class="absolute top-3 right-3 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                <Check class="w-3 h-3 text-primary-foreground" />
              </div>

              <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="type.iconBg">
                <component :is="type.icon" class="w-6 h-6 text-white" />
              </div>

              <div>
                <h4 class="font-semibold text-sm mb-0.5">{{ type.label }}</h4>
                <p class="text-xs text-muted-foreground leading-tight">{{ type.desc }}</p>
              </div>
            </div>
          </div>

          <!-- Step 2: Form Fields -->
          <div v-if="currentStep === 2" class="space-y-5">
             <!-- SFTP Form -->
             <template v-if="form.type === 'sftp'">
                <div class="space-y-4">
                  <div class="space-y-2">
                    <Label>数据源名称 <span class="text-destructive">*</span></Label>
                    <Input v-model="form.name" placeholder="例如：财务部每晚结算文件" />
                  </div>

                  <div class="space-y-2">
                    <Label>服务商类型</Label>
                    <Select v-model="form.sftpProvider">
                       <SelectTrigger>
                         <SelectValue />
                       </SelectTrigger>
                       <SelectContent>
                         <SelectItem value="custom">
                            <div class="flex items-center gap-2">
                               <HardDrive class="w-4 h-4 text-blue-500" />
                               通用 SFTP 服务器
                            </div>
                         </SelectItem>
                         <SelectItem value="aws_transfer">
                            <div class="flex items-center gap-2">
                               <img src="https://cdn.worldvectorlogo.com/logos/aws-2.svg" class="w-4 h-4 object-contain" alt="AWS" />
                               AWS Transfer Family
                            </div>
                         </SelectItem>
                         <SelectItem value="ali_oss_sftp">
                            <div class="flex items-center gap-2">
                               <img src="https://cdn.worldvectorlogo.com/logos/alibaba-cloud-1.svg" class="w-4 h-4 object-contain" alt="Aliyun" />
                               阿里云 OSS SFTP
                            </div>
                         </SelectItem>
                         <SelectItem value="azure_blob_sftp">
                            <div class="flex items-center gap-2">
                               <img src="https://cdn.worldvectorlogo.com/logos/azure-1.svg" class="w-4 h-4 object-contain" alt="Azure" />
                               Azure Blob Storage SFTP
                            </div>
                         </SelectItem>
                       </SelectContent>
                    </Select>
                  </div>

                  <div class="grid grid-cols-4 gap-4">
                    <div class="col-span-3 space-y-2">
                        <Label>主机地址 (Host) <span class="text-destructive">*</span></Label>
                        <Input v-model="form.host" placeholder="192.168.1.100 或 sftp.example.com" />
                    </div>
                    <div class="space-y-2">
                        <Label>端口</Label>
                        <Input v-model="form.port" type="number" />
                    </div>
                  </div>

                  <div class="border rounded-lg p-4 bg-muted/30">
                    <div class="flex items-center justify-between mb-4">
                        <Label>认证配置</Label>
                        <div class="flex bg-muted rounded-lg p-0.5">
                            <Button 
                                variant="ghost"
                                size="sm"
                                @click="form.authType = 'password'"
                                :class="form.authType === 'password' ? 'bg-background shadow-sm' : 'text-muted-foreground'"
                            >密码认证</Button>
                            <Button 
                                variant="ghost"
                                size="sm"
                                @click="form.authType = 'key'"
                                :class="form.authType === 'key' ? 'bg-background shadow-sm' : 'text-muted-foreground'"
                            >私钥认证</Button>
                        </div>
                    </div>

                    <div class="space-y-4">
                        <div class="space-y-2">
                            <Label>用户名 <span class="text-destructive">*</span></Label>
                            <Input v-model="form.username" />
                        </div>

                        <div v-if="form.authType === 'password'" class="space-y-2 animate-in fade-in">
                            <Label>密码 <span class="text-destructive">*</span></Label>
                            <div class="relative">
                                <Input :type="showPassword ? 'text' : 'password'" v-model="form.password" />
                                <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full p-4" @click="showPassword = !showPassword">
                                    <Eye v-if="showPassword" class="w-4 h-4" />
                                    <EyeOff v-else class="w-4 h-4" />
                                </Button>
                            </div>
                        </div>

                        <div v-else class="space-y-4 animate-in fade-in">
                            <div class="space-y-2">
                                <div class="flex justify-between items-center">
                                    <Label>私钥 (Private Key) <span class="text-destructive">*</span></Label>
                                    <Label class="text-primary cursor-pointer hover:underline flex items-center gap-1">
                                        <Upload class="w-3 h-3" />
                                        上传文件
                                        <input type="file" class="hidden" @change="handleKeyFileUpload">
                                    </Label>
                                </div>
                                <textarea 
                                  v-model="form.privateKey" 
                                  rows="4" 
                                  class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                  :class="privateKeyError ? 'border-destructive ring-destructive/20' : ''"
                                  placeholder="-----BEGIN OPENSSH PRIVATE KEY-----..."
                                ></textarea>
                                <p v-if="privateKeyError" class="text-xs text-destructive mt-1">{{ privateKeyError }}</p>
                            </div>
                            <div class="space-y-2">
                                <Label>私钥密码 (Passphrase)</Label>
                                <Input type="password" v-model="form.passphrase" placeholder="如果私钥未加密可留空" />
                            </div>
                        </div>
                    </div>
                  </div>
                  
                  <!-- File Handling -->
                  <div class="space-y-4 border rounded-lg p-4 bg-muted/10">
                      <h4 class="text-sm font-medium">文件处理规则</h4>
                      <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                              <Label>远程路径 (Remote Path)</Label>
                              <Input v-model="form.sftpRemotePath" placeholder="/" />
                          </div>
                          <div class="space-y-2">
                              <Label>文件匹配模式 (Glob)</Label>
                              <Input v-model="form.sftpFilePattern" placeholder="*.csv" />
                          </div>
                      </div>
                      <div class="flex items-center gap-6">
                          <div class="flex items-center space-x-2">
                            <Checkbox id="sftp-rec" :checked="form.sftpRecursive" @update:checked="(v) => form.sftpRecursive = v" />
                            <label for="sftp-rec" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">递归子目录</label>
                          </div>
                          <div class="flex items-center space-x-2">
                            <Checkbox id="sftp-del" :checked="form.sftpDeleteAfter" @update:checked="(v) => form.sftpDeleteAfter = v" />
                            <label for="sftp-del" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">下载后删除远程文件</label>
                          </div>
                      </div>
                  </div>
                </div>
             </template>
             
             <!-- Crawler Form -->
             <template v-else-if="form.type === 'crawler'">
                <div class="space-y-4">
                  <div class="space-y-2">
                    <Label>数据源名称 <span class="text-destructive">*</span></Label>
                    <Input v-model="form.name" placeholder="例如：某政府网站政策爬虫" />
                  </div>

                  <!-- Provider Switch -->
                  <div class="space-y-2">
                    <Label>服务商</Label>
                    <Tabs v-model="form.crawlerProvider" class="w-full">
                      <TabsList class="grid w-full grid-cols-2">
                        <TabsTrigger value="tavily">Tavily AI</TabsTrigger>
                        <TabsTrigger value="ali_opensearch">Alibaba OpenSearch</TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>

                  <!-- Common Crawler Fields -->
                  <div class="space-y-2">
                      <Label>目标 URL (Start URLs)</Label>
                      <textarea 
                        v-model="form.targetUrl" 
                        rows="3" 
                        class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                        placeholder="https://example.com/news&#10;https://another-site.com/data"
                      ></textarea>
                      <p class="text-xs text-muted-foreground">每行一个 URL</p>
                  </div>

                  <div class="space-y-2">
                      <Label>搜索关键词 (Query Params)</Label>
                      <Input v-model="form.searchKeywords" placeholder="例如：category=finance&tags=report" />
                      <p class="text-xs text-muted-foreground">OpenSearch: 输入查询子句 (query clause) | Tavily: 输入搜索关键词</p>
                  </div>

                  <div class="overflow-hidden transition-all duration-300 ease-in-out">
                    <!-- Tavily AI Config -->
                    <div v-if="form.crawlerProvider === 'tavily'" class="space-y-4 pt-2 animate-in fade-in slide-in-from-top-2 duration-300">
                          <div class="space-y-2">
                              <Label>API 密钥 <span class="text-destructive">*</span></Label>
                              <div class="relative">
                                  <Input :type="showPassword ? 'text' : 'password'" v-model="form.tavilyApiKey" placeholder="tvly-xxxxxxxx" />
                                  <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full p-4" @click="showPassword = !showPassword">
                                      <Eye v-if="showPassword" class="w-4 h-4" />
                                      <EyeOff v-else class="w-4 h-4" />
                                  </Button>
                              </div>
                          </div>

                          <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-2">
                               <Label>搜索深度</Label>
                               <Select v-model="form.tavilySearchDepth">
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="basic">基础 (标准)</SelectItem>
                                    <SelectItem value="advanced">高级 (深度)</SelectItem>
                                  </SelectContent>
                               </Select>
                            </div>
                            <div class="space-y-2">
                               <Label>单次搜索上限</Label>
                               <Input v-model="form.tavilyMaxResults" type="number" min="1" max="20" />
                            </div>
                          </div>

                          <div class="space-y-2">
                              <Label>结果包含项</Label>
                              <div class="flex flex-col gap-2 border rounded-md p-4 bg-muted/20">
                                 <div class="flex items-center space-x-2">
                                    <Checkbox id="inc-images" :checked="form.tavilyInclusions.includes('images')" @update:checked="(checked) => { if(checked) form.tavilyInclusions.push('images'); else form.tavilyInclusions = form.tavilyInclusions.filter(i => i !== 'images') }" />
                                    <label for="inc-images" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">包含图片</label>
                                 </div>
                                 <div class="flex items-center space-x-2">
                                    <Checkbox id="inc-raw" :checked="form.tavilyInclusions.includes('raw_content')" @update:checked="(checked) => { if(checked) form.tavilyInclusions.push('raw_content'); else form.tavilyInclusions = form.tavilyInclusions.filter(i => i !== 'raw_content') }" />
                                    <label for="inc-raw" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">包含原始内容</label>
                                 </div>
                                 <div class="flex items-center space-x-2">
                                    <Checkbox id="inc-answer" :checked="form.tavilyInclusions.includes('answer')" @update:checked="(checked) => { if(checked) form.tavilyInclusions.push('answer'); else form.tavilyInclusions = form.tavilyInclusions.filter(i => i !== 'answer') }" />
                                    <label for="inc-answer" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">包含问答摘要</label>
                                 </div>
                              </div>
                          </div>

                      <div class="space-y-2">
                          <Label>搜索频率 (Cron)</Label>
                          <div class="flex gap-2">
                             <Input v-model="form.cronExpression" class="font-mono" />
                             <Button variant="outline" size="icon" title="重置为每日零点">
                                <RefreshCw class="w-4 h-4" @click="form.cronExpression = '0 0 * * *'" />
                             </Button>
                          </div>
                      </div>
                    </div>

                    <!-- Alibaba OpenSearch Config -->
                    <div v-else-if="form.crawlerProvider === 'ali_opensearch'" class="space-y-4 pt-2 animate-in fade-in slide-in-from-top-2 duration-300">
                       <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                              <Label>AccessKey ID <span class="text-destructive">*</span></Label>
                              <Input v-model="form.aliAccessKeyId" />
                          </div>
                          <div class="space-y-2">
                              <Label>API 密钥 <span class="text-destructive">*</span></Label>
                          <div class="relative">
                              <Input :type="showPassword ? 'text' : 'password'" v-model="form.aliAccessKeySecret" />
                              <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full p-4" @click="showPassword = !showPassword">
                                  <Eye v-if="showPassword" class="w-4 h-4" />
                                  <EyeOff v-else class="w-4 h-4" />
                              </Button>
                          </div>
                      </div>
                   </div>

                   <div class="space-y-2">
                       <Label>服务接入点 (Endpoint) <span class="text-destructive">*</span></Label>
                       <!-- Simple input for now, could be combobox -->
                       <Input v-model="form.aliEndpoint" placeholder="opensearch-cn-hangzhou.aliyuncs.com" />
                   </div>

                   <div class="grid grid-cols-2 gap-4">
                      <div class="space-y-2">
                          <Label>应用名称 (App Name) <span class="text-destructive">*</span></Label>
                          <Input v-model="form.aliAppName" />
                      </div>
                      <div class="space-y-2">
                          <Label>索引表名称 <span class="text-destructive">*</span></Label>
                          <Input v-model="form.aliIndexName" />
                      </div>
                   </div>

                   <div class="space-y-2">
                       <Label>返回字段 (Fetch Fields)</Label>
                       <Input v-model="form.aliFetchFields" placeholder="例如：id,title,body,timestamp (留空返回所有)" />
                   </div>

                   <div class="grid grid-cols-2 gap-4">
                      <div class="space-y-2">
                          <Label>过滤子句 (Filter)</Label>
                          <Input v-model="form.aliFilterClause" placeholder="例如：price > 100 AND stock > 0" />
                      </div>
                      <div class="space-y-2">
                          <Label>排序子句 (Sort)</Label>
                          <Input v-model="form.aliSortClause" placeholder="例如：-create_time;+rank" />
                      </div>
                   </div>

                   <div class="space-y-2">
                       <Label>Config 子句</Label>
                       <Input v-model="form.aliConfigClause" placeholder="例如：start:0,hit:10,format:json" />
                   </div>

                       <div class="space-y-2">
                          <Label>检索协议</Label>
                          <RadioGroup v-model="form.aliProtocol" class="flex gap-4">
                             <div class="flex items-center space-x-2">
                               <RadioGroupItem id="proto-https" value="https" />
                               <Label for="proto-https">HTTPS</Label>
                             </div>
                             <div class="flex items-center space-x-2">
                               <RadioGroupItem id="proto-http" value="http" />
                               <Label for="proto-http">HTTP</Label>
                             </div>
                          </RadioGroup>
                       </div>
                    </div>
                  </div>
                </div>
             </template>

             <!-- Database Form -->
             <template v-else-if="form.type === 'database'">
                <div class="space-y-2">
                  <Label>数据源名称 <span class="text-destructive">*</span></Label>
                  <Input v-model="form.name" placeholder="例如：ERP 生产库从库" />
                </div>
                <div class="space-y-2">
                   <Label>数据库类型</Label>
                   <Select v-model="form.dbType">
                      <SelectTrigger>
                        <SelectValue placeholder="选择类型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem v-for="db in databaseTypes" :key="db.value" :value="db.value">
                          <div class="flex items-center gap-2">
                             <img :src="db.icon" class="w-4 h-4 object-contain" :alt="db.label" />
                             {{ db.label }}
                          </div>
                        </SelectItem>
                      </SelectContent>
                   </Select>
                </div>
                <div class="grid grid-cols-3 gap-4">
                    <div class="col-span-2 space-y-2">
                        <Label>主机地址 (Host) <span class="text-destructive">*</span></Label>
                        <Input v-model="form.dbHost" placeholder="127.0.0.1" />
                    </div>
                    <div class="space-y-2">
                        <Label>端口 (Port)</Label>
                        <Input v-model="form.dbPort" type="number" />
                    </div>
                </div>
                <div class="space-y-2">
                    <Label>数据库名 (Schema) <span class="text-destructive">*</span></Label>
                    <Input v-model="form.dbName" placeholder="production_db" />
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-2">
                        <Label>用户名</Label>
                        <Input v-model="form.dbUsername" />
                    </div>
                    <div class="space-y-2">
                        <Label>密码</Label>
                        <Input v-model="form.dbPassword" type="password" />
                    </div>
                </div>

                <Accordion type="single" collapsible class="w-full border rounded-lg bg-muted/10">
                  <AccordionItem value="advanced" class="border-b-0">
                    <AccordionTrigger class="px-4 py-2 text-sm hover:no-underline">
                      高级设置 (Advanced Settings)
                    </AccordionTrigger>
                    <AccordionContent class="px-4 pb-4 pt-2 space-y-4">
                      <!-- 1. SSL -->
                      <div class="space-y-3 border-b pb-4">
                        <div class="flex items-center justify-between">
                          <Label class="text-base">连接加密 (SSL)</Label>
                          <Switch :checked="form.dbSsl" @update:checked="(v) => form.dbSsl = v" />
                        </div>
                        <div v-if="form.dbSsl" class="space-y-3 animate-in fade-in slide-in-from-top-2">
                           <div class="space-y-2">
                              <Label>CA 证书</Label>
                              <div class="flex items-center gap-2">
                                <Input type="file" class="text-xs file:mr-4 file:py-1 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90" />
                              </div>
                           </div>
                           <div class="grid grid-cols-2 gap-4">
                              <div class="space-y-2">
                                <Label>客户端证书 (Cert)</Label>
                                <Input type="file" class="text-xs file:text-xs" />
                              </div>
                              <div class="space-y-2">
                                <Label>客户端密钥 (Key)</Label>
                                <Input type="file" class="text-xs file:text-xs" />
                              </div>
                           </div>
                        </div>
                      </div>

                      <!-- 2. SSH Tunnel -->
                      <div class="space-y-3 border-b pb-4">
                        <div class="flex items-center justify-between">
                          <Label class="text-base">SSH 隧道 (SSH Tunnel)</Label>
                          <Switch :checked="form.dbSsh" @update:checked="(v) => form.dbSsh = v" />
                        </div>
                        <div v-if="form.dbSsh" class="space-y-3 animate-in fade-in slide-in-from-top-2">
                           <div class="grid grid-cols-3 gap-4">
                              <div class="col-span-2 space-y-2">
                                <Label>SSH 主机</Label>
                                <Input v-model="form.dbSshHost" placeholder="ssh.example.com" />
                              </div>
                              <div class="space-y-2">
                                <Label>SSH 端口</Label>
                                <Input v-model="form.dbSshPort" type="number" />
                              </div>
                           </div>
                           <div class="space-y-2">
                              <Label>SSH 用户名</Label>
                              <Input v-model="form.dbSshUser" />
                           </div>
                           <div class="space-y-2">
                              <Label>认证方式</Label>
                              <div class="flex items-center space-x-4 mb-2">
                                <div class="flex items-center space-x-2">
                                  <input type="radio" id="ssh-pwd" value="password" v-model="form.dbSshAuthType" class="accent-primary" />
                                  <label for="ssh-pwd" class="text-sm">密码</label>
                                </div>
                                <div class="flex items-center space-x-2">
                                  <input type="radio" id="ssh-key" value="key" v-model="form.dbSshAuthType" class="accent-primary" />
                                  <label for="ssh-key" class="text-sm">私钥</label>
                                </div>
                              </div>
                              
                              <Input v-if="form.dbSshAuthType === 'password'" type="password" v-model="form.dbSshPassword" placeholder="SSH Password" />
                              <textarea 
                                v-else 
                                v-model="form.dbSshKey" 
                                rows="3" 
                                class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                              ></textarea>
                           </div>
                        </div>
                      </div>

                      <!-- 3. Connection Pool -->
                      <div class="space-y-4 border-b pb-4">
                         <Label class="text-base">连接池设置</Label>
                         <div class="space-y-4 px-1">
                            <div class="space-y-3">
                               <div class="flex justify-between">
                                  <Label>最大连接数: {{ form.dbMaxConnections[0] }}</Label>
                               </div>
                               <Slider
                                  v-model="form.dbMaxConnections"
                                  :max="100"
                                  :min="1"
                                  :step="1"
                               />
                            </div>
                            <div class="space-y-2">
                               <Label>超时时间 (秒)</Label>
                               <Input v-model="form.dbTimeout" type="number" />
                            </div>
                         </div>
                      </div>

                      <!-- 4. Charset -->
                      <div class="space-y-2">
                         <Label>字符集 (Charset)</Label>
                         <Select v-model="form.dbCharset">
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="utf8mb4">utf8mb4 (Default)</SelectItem>
                              <SelectItem value="utf8">utf8</SelectItem>
                              <SelectItem value="latin1">latin1</SelectItem>
                              <SelectItem value="gbk">gbk</SelectItem>
                            </SelectContent>
                         </Select>
                      </div>

                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
             </template>

             <!-- API Form -->
             <template v-else-if="form.type === 'api'">
                <div class="space-y-4">
                  <div class="space-y-2">
                    <Label>数据源名称 <span class="text-destructive">*</span></Label>
                    <Input v-model="form.name" placeholder="例如：外部汇率接口" />
                  </div>

                  <div class="space-y-2">
                    <Label>API 类型</Label>
                    <Tabs v-model="form.apiProvider" class="w-full">
                      <TabsList class="grid w-full grid-cols-4">
                        <TabsTrigger value="custom">通用 API</TabsTrigger>
                        <TabsTrigger value="feishu">飞书</TabsTrigger>
                        <TabsTrigger value="dingtalk">钉钉</TabsTrigger>
                        <TabsTrigger value="seeyon">致远 OA</TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>

                  <!-- Custom API -->
                   <div v-if="form.apiProvider === 'custom'" class="space-y-4 animate-in fade-in slide-in-from-top-2">
                       <!-- Basic Request Info -->
                       <div class="space-y-3 p-4 border rounded-lg bg-muted/10">
                           <h4 class="text-sm font-medium">请求信息</h4>
                           <div class="grid grid-cols-4 gap-4">
                               <div class="col-span-1 space-y-2">
                                   <Label>方法 (Method)</Label>
                                   <Select v-model="form.apiMethod">
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="GET">GET</SelectItem>
                                        <SelectItem value="POST">POST</SelectItem>
                                        <SelectItem value="PUT">PUT</SelectItem>
                                      </SelectContent>
                                   </Select>
                               </div>
                               <div class="col-span-3 space-y-2">
                                   <Label>API URL <span class="text-destructive">*</span></Label>
                                   <Input v-model="form.apiUrl" placeholder="https://api.example.com/v1/data" />
                               </div>
                           </div>
                           
                           <div class="space-y-2">
                               <Label>查询参数 (Query Params JSON)</Label>
                               <textarea 
                                 v-model="form.apiParams" 
                                 rows="2" 
                                 class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                 placeholder='{"limit": 100, "sort": "desc"}'
                               ></textarea>
                           </div>

                           <div class="space-y-2">
                               <Label>请求头 (Headers JSON)</Label>
                               <textarea 
                                 v-model="form.apiHeaders" 
                                 rows="2" 
                                 class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                 placeholder='{"Content-Type": "application/json"}'
                               ></textarea>
                           </div>

                           <div v-if="form.apiMethod !== 'GET'" class="space-y-2">
                               <Label>请求体 (Body JSON)</Label>
                               <textarea 
                                 v-model="form.apiBody" 
                                 rows="3" 
                                 class="flex w-full rounded-md border border-input bg-background p-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                 placeholder='{"key": "value"}'
                               ></textarea>
                           </div>
                       </div>

                       <!-- Authentication -->
                       <div class="space-y-3 p-4 border rounded-lg bg-muted/10">
                           <h4 class="text-sm font-medium">鉴权配置 (Authentication)</h4>
                           <div class="space-y-2">
                               <Label>鉴权方式</Label>
                               <Select v-model="form.apiAuthType">
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="none">None (无鉴权)</SelectItem>
                                    <SelectItem value="basic">Basic Auth</SelectItem>
                                    <SelectItem value="bearer">Bearer Token</SelectItem>
                                    <SelectItem value="apikey">API Key</SelectItem>
                                  </SelectContent>
                               </Select>
                           </div>

                           <!-- Auth Fields -->
                           <div v-if="form.apiAuthType === 'basic'" class="grid grid-cols-2 gap-4 animate-in fade-in">
                               <div class="space-y-2">
                                   <Label>Username</Label>
                                   <Input v-model="form.apiAuthUsername" />
                               </div>
                               <div class="space-y-2">
                                   <Label>Password</Label>
                                   <Input type="password" v-model="form.apiAuthPassword" />
                               </div>
                           </div>
                           
                           <div v-if="form.apiAuthType === 'bearer'" class="space-y-2 animate-in fade-in">
                               <Label>Token</Label>
                               <Input type="password" v-model="form.apiAuthToken" placeholder="eyJhbGci..." />
                           </div>

                           <div v-if="form.apiAuthType === 'apikey'" class="space-y-3 animate-in fade-in">
                               <div class="grid grid-cols-2 gap-4">
                                   <div class="space-y-2">
                                       <Label>Key Name</Label>
                                       <Input v-model="form.apiAuthKeyName" placeholder="X-API-Key" />
                                   </div>
                                   <div class="space-y-2">
                                       <Label>Value</Label>
                                       <Input type="password" v-model="form.apiAuthKeyValue" />
                                   </div>
                               </div>
                               <div class="space-y-2">
                                   <Label>Add To</Label>
                                   <RadioGroup v-model="form.apiAuthKeyLocation" class="flex gap-4">
                                      <div class="flex items-center space-x-2">
                                        <RadioGroupItem id="loc-header" value="header" />
                                        <Label for="loc-header">Header</Label>
                                      </div>
                                      <div class="flex items-center space-x-2">
                                        <RadioGroupItem id="loc-query" value="query" />
                                        <Label for="loc-query">Query Params</Label>
                                      </div>
                                   </RadioGroup>
                               </div>
                           </div>
                       </div>

                       <!-- Pagination -->
                       <Accordion type="single" collapsible class="w-full border rounded-lg bg-muted/10">
                         <AccordionItem value="pagination" class="border-b-0">
                           <AccordionTrigger class="px-4 py-2 text-sm hover:no-underline">
                             分页配置 (Pagination)
                           </AccordionTrigger>
                           <AccordionContent class="px-4 pb-4 pt-2 space-y-4">
                               <div class="space-y-2">
                                   <Label>分页策略</Label>
                                   <Select v-model="form.apiPaginationType">
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="none">不分页 (单次请求)</SelectItem>
                                        <SelectItem value="page_param">Page Parameter (页码)</SelectItem>
                                        <SelectItem value="offset_limit">Offset / Limit (偏移量)</SelectItem>
                                        <SelectItem value="cursor">Cursor / Next Token (游标)</SelectItem>
                                      </SelectContent>
                                   </Select>
                               </div>

                               <div v-if="form.apiPaginationType === 'page_param'" class="grid grid-cols-2 gap-4 animate-in fade-in">
                                   <div class="space-y-2">
                                       <Label>页码参数名</Label>
                                       <Input v-model="form.apiPaginationPageParam" placeholder="page" />
                                   </div>
                                   <div class="space-y-2">
                                       <Label>每页条数参数名</Label>
                                       <Input v-model="form.apiPaginationSizeParam" placeholder="size" />
                                   </div>
                               </div>

                               <div v-if="form.apiPaginationType === 'offset_limit'" class="grid grid-cols-2 gap-4 animate-in fade-in">
                                   <div class="space-y-2">
                                       <Label>Offset 参数名</Label>
                                       <Input v-model="form.apiPaginationPageParam" placeholder="offset" />
                                   </div>
                                   <div class="space-y-2">
                                       <Label>Limit 参数名</Label>
                                       <Input v-model="form.apiPaginationSizeParam" placeholder="limit" />
                                   </div>
                               </div>

                               <div v-if="form.apiPaginationType === 'cursor'" class="space-y-2 animate-in fade-in">
                                   <Label>游标参数名 (Cursor Param)</Label>
                                   <Input v-model="form.apiPaginationCursorParam" placeholder="cursor" />
                                   <p class="text-xs text-muted-foreground">通常对应响应体中的 next_cursor 或 next_token 字段</p>
                               </div>

                               <div v-if="form.apiPaginationType !== 'none'" class="space-y-2">
                                   <Label>结果列表字段路径 (Data Field Path)</Label>
                                   <Input v-model="form.apiPaginationField" placeholder="data.items" />
                                   <p class="text-xs text-muted-foreground">JSON 路径，例如 `data` 或 `response.list`</p>
                               </div>
                           </AccordionContent>
                         </AccordionItem>
                       </Accordion>
                   </div>

                  <!-- Feishu -->
                  <div v-else-if="form.apiProvider === 'feishu'" class="space-y-4 animate-in fade-in slide-in-from-top-2">
                      <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                              <Label>App ID <span class="text-destructive">*</span></Label>
                              <Input v-model="form.feishuAppId" placeholder="cli_..." />
                          </div>
                          <div class="space-y-2">
                              <Label>App Secret <span class="text-destructive">*</span></Label>
                              <div class="relative">
                                  <Input :type="showPassword ? 'text' : 'password'" v-model="form.feishuAppSecret" />
                                  <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full p-4" @click="showPassword = !showPassword">
                                      <Eye v-if="showPassword" class="w-4 h-4" />
                                      <EyeOff v-else class="w-4 h-4" />
                                  </Button>
                              </div>
                          </div>
                      </div>

                      <div class="space-y-2">
                          <Label>同步对象</Label>
                          <Select v-model="form.feishuTarget">
                             <SelectTrigger>
                               <SelectValue />
                             </SelectTrigger>
                             <SelectContent>
                               <SelectItem value="docs">云文档 (Docs)</SelectItem>
                               <SelectItem value="sheets">电子表格 (Sheets)</SelectItem>
                               <SelectItem value="bitable">多维表格 (Bitable)</SelectItem>
                               <SelectItem value="wiki">知识库 (Wiki)</SelectItem>
                             </SelectContent>
                          </Select>
                      </div>

                      <div v-if="form.feishuTarget === 'wiki'" class="space-y-2 animate-in fade-in">
                          <Label>知识库 ID (Space ID)</Label>
                          <Input v-model="form.feishuSpaceId" placeholder="space_..." />
                      </div>

                      <div v-else class="space-y-2 animate-in fade-in">
                          <Label>文件夹 Token (可选)</Label>
                          <Input v-model="form.feishuFolderToken" placeholder="fld..." />
                          <p class="text-xs text-muted-foreground">指定同步某个文件夹下的内容，留空则同步应用可见范围内的所有文档</p>
                      </div>

                      <Alert>
                        <Info class="w-4 h-4" />
                        <AlertTitle>权限说明</AlertTitle>
                        <AlertDescription>
                          请确保应用已开通“云文档”、“通讯录”等读取权限。
                        </AlertDescription>
                      </Alert>
                  </div>

                  <!-- DingTalk -->
                  <div v-else-if="form.apiProvider === 'dingtalk'" class="space-y-4 animate-in fade-in slide-in-from-top-2">
                      <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                              <Label>AppKey <span class="text-destructive">*</span></Label>
                              <Input v-model="form.dingtalkAppKey" />
                          </div>
                          <div class="space-y-2">
                              <Label>AppSecret <span class="text-destructive">*</span></Label>
                              <div class="relative">
                                  <Input :type="showPassword ? 'text' : 'password'" v-model="form.dingtalkAppSecret" />
                                  <Button variant="ghost" size="icon" class="absolute right-0 top-0 h-full p-4" @click="showPassword = !showPassword">
                                      <Eye v-if="showPassword" class="w-4 h-4" />
                                      <EyeOff v-else class="w-4 h-4" />
                                  </Button>
                              </div>
                          </div>
                      </div>

                      <div class="space-y-2">
                          <Label>同步业务</Label>
                          <Select v-model="form.dingtalkTarget">
                             <SelectTrigger>
                               <SelectValue />
                             </SelectTrigger>
                             <SelectContent>
                               <SelectItem value="process">审批流数据 (Process)</SelectItem>
                               <SelectItem value="report">日志报表 (Report)</SelectItem>
                               <SelectItem value="smart_work">智能人事 (Smart Work)</SelectItem>
                             </SelectContent>
                          </Select>
                      </div>

                      <div v-if="form.dingtalkTarget === 'process'" class="space-y-2 animate-in fade-in">
                          <Label>审批流编码 (ProcessCode)</Label>
                          <Input v-model="form.dingtalkProcessCode" placeholder="PROC-..." />
                          <p class="text-xs text-muted-foreground">可在钉钉管理后台审批流设置中查看</p>
                      </div>

                      <div class="space-y-2">
                          <Label>起始时间 (Start Time)</Label>
                          <Input type="date" v-model="form.dingtalkStartTime" />
                      </div>
                  </div>

                  <!-- Seeyon OA -->
                  <div v-else-if="form.apiProvider === 'seeyon'" class="space-y-4 animate-in fade-in slide-in-from-top-2">
                      <div class="space-y-2">
                          <Label>OA 地址 (Base URL) <span class="text-destructive">*</span></Label>
                          <Input v-model="form.seeyonBaseUrl" placeholder="https://oa.example.com" />
                      </div>
                      <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                              <Label>REST 用户名</Label>
                              <Input v-model="form.seeyonUsername" />
                          </div>
                          <div class="space-y-2">
                              <Label>REST 密码</Label>
                              <Input type="password" v-model="form.seeyonPassword" />
                          </div>
                      </div>

                      <div class="space-y-2">
                          <Label>采集类型</Label>
                          <Select v-model="form.seeyonFetchType">
                             <SelectTrigger>
                               <SelectValue />
                             </SelectTrigger>
                             <SelectContent>
                               <SelectItem value="docs">公文/知识库 (Documents)</SelectItem>
                               <SelectItem value="collaboration">协同事项 (Collaboration)</SelectItem>
                               <SelectItem value="news">新闻公告 (News)</SelectItem>
                             </SelectContent>
                          </Select>
                      </div>

                      <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                              <Label>采集时间范围 (最近天数)</Label>
                              <Input type="number" v-model="form.seeyonTimeRange" />
                          </div>
                          <div class="space-y-2 flex flex-col justify-end pb-2">
                              <div class="flex items-center space-x-2">
                                <Checkbox id="seeyon-att" :checked="form.seeyonIncludeAttachments" @update:checked="(v) => form.seeyonIncludeAttachments = v" />
                                <label for="seeyon-att" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">下载附件 (PDF/Word)</label>
                              </div>
                          </div>
                      </div>

                      <div class="space-y-2">
                          <Label>指定部门 ID (可选)</Label>
                          <Input v-model="form.seeyonDeptIds" placeholder="多个部门ID用逗号分隔，留空则采集全员公开数据" />
                      </div>
                  </div>
                </div>
             </template>
          </div>
          </div>
        </ScrollArea>

        <DialogFooter class="px-6 py-4 border-t bg-muted/20 sm:justify-between">
          <div class="flex items-center gap-4">
             <Button 
                v-if="currentStep === 2"
                variant="outline"
                @click="testConnectionWrapper"
                :disabled="isTestingConnection"
             >
                <Loader2 v-if="isTestingConnection" class="w-4 h-4 mr-2 animate-spin" />
                <span v-else>测试连接</span>
             </Button>
          </div>
          
          <div class="flex gap-4">
            <Button v-if="currentStep === 1" variant="ghost" @click="showModal = false">取消</Button>
            <Button v-if="currentStep === 2" variant="ghost" @click="currentStep = 1">上一步</Button>
            <Button v-if="currentStep === 1" @click="currentStep = 2">下一步</Button>
            <Button v-if="currentStep === 2" @click="saveDataSource">保存</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    
    <!-- Global Toast -->
    <Toaster />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, h, onMounted } from 'vue';
import { 
  Search, Filter, ChevronDown, Check, Plus, Pencil, Trash2, 
  Database, Globe, File, Server, MoreVertical, X,
  Activity, Settings2, Info, Loader2, Eye, EyeOff, Upload,
  RefreshCw, Cloud, HardDrive
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Toaster, useToast } from '@/components/ui/toast';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Slider } from '@/components/ui/slider';
import { ScrollArea } from '@/components/ui/scroll-area';

import { SkeletonDataSource } from '@/components/skeletons';
import { dataSourceApi, type DataSourceCreate } from './api';

const { toast } = useToast();

// Mock Icons
const getIconComponent = (type: string) => {
  switch(type) {
    case 'crawler': return Globe;
    case 'sftp': return File;
    case 'database': return Database;
    case 'api': return Server;
    default: return Globe;
  }
};

const getIconBgColor = (type: string) => {
  switch(type) {
    case 'crawler': return 'bg-green-500';
    case 'sftp': return 'bg-blue-500';
    case 'database': return 'bg-purple-500';
    case 'api': return 'bg-amber-500';
    default: return 'bg-gray-500';
  }
};

// Data
const searchQuery = ref('');
const showModal = ref(false);
const showDrawer = ref(false);
const isEditing = ref(false);
const currentStep = ref(1);

// ... (Keep existing data structures)
const defaultFormState = {
  id: 0,
  name: '',
  type: 'crawler',
  description: '',
  status: 'running',
  throughput: '',
  host: '',
  port: 22,
  authType: 'password',
  username: '',
  password: '',
  privateKey: '',
  passphrase: '',
  // SFTP fields
  sftpProvider: 'custom', // 'custom' | 'aws_transfer' | 'ali_oss_sftp' | 'azure_blob_sftp'
  sftpRemotePath: '/',
  sftpFilePattern: '*', // e.g. *.csv
  sftpRecursive: false,
  sftpDeleteAfter: false,
  // Crawler fields
  searchKeywords: '',
  targetUrl: '',
  cronExpression: '0 0 * * *',
  // New Crawler fields
  crawlerProvider: 'tavily', // 'tavily' | 'ali_opensearch'
  // Tavily
  tavilyApiKey: '',
  tavilySearchDepth: 'basic', // 'basic' | 'advanced'
  tavilyInclusions: [] as string[], // ['images', 'raw_content', 'answer']
  tavilyMaxResults: 5,
  // Ali OpenSearch
  aliAccessKeyId: '',
  aliAccessKeySecret: '',
  aliEndpoint: 'opensearch-cn-hangzhou.aliyuncs.com',
  aliAppName: '',
  aliIndexName: '',
  aliProtocol: 'https',
  aliFetchFields: '', // fetch_fields
  aliQueryClause: '', // query=...
  aliFilterClause: '', // filter=...
  aliSortClause: '', // sort=...
  aliConfigClause: 'start:0,hit:10,format:json', // config=...
  
  // Database fields
  dbType: 'mysql',
  dbHost: '',
  dbPort: 3306,
  dbUsername: '',
  dbPassword: '',
  dbName: '',
  // Database Advanced
  dbSsl: false,
  dbSslCa: '',
  dbSslCert: '',
  dbSslKey: '',
  dbSsh: false,
  dbSshHost: '',
  dbSshPort: 22,
  dbSshUser: '',
  dbSshAuthType: 'password', // 'password' | 'key'
  dbSshPassword: '',
  dbSshKey: '',
  dbMaxConnections: [10],
  dbTimeout: 30,
  dbCharset: 'utf8mb4',
  
  // API fields
  apiProvider: 'custom', // 'custom' | 'feishu' | 'dingtalk' | 'seeyon'
  apiUrl: '',
  apiMethod: 'GET',
  apiHeaders: '',
  apiBody: '',
  apiParams: '', // query params
  apiAuthType: 'none', // 'none' | 'basic' | 'bearer' | 'apikey'
  apiAuthUsername: '',
  apiAuthPassword: '',
  apiAuthToken: '',
  apiAuthKeyName: '',
  apiAuthKeyValue: '',
  apiAuthKeyLocation: 'header', // 'header' | 'query'
  apiPaginationType: 'none', // 'none' | 'page_param' | 'offset_limit' | 'cursor'
  apiPaginationPageParam: 'page',
  apiPaginationSizeParam: 'size',
  apiPaginationSize: 20,
  apiPaginationCursorParam: 'cursor',
  apiPaginationField: 'data', // field containing the list
  // Feishu
  feishuAppId: '',
  feishuAppSecret: '',
  feishuTarget: 'docs', // 'docs' | 'sheets' | 'bitable' | 'wiki'
  feishuSpaceId: '',
  feishuFolderToken: '',
  // DingTalk
  dingtalkAppKey: '',
  dingtalkAppSecret: '',
  dingtalkTarget: 'process', // 'process' | 'report' | 'smart_work'
  dingtalkProcessCode: '',
  dingtalkStartTime: '',
  // Seeyon
  seeyonBaseUrl: '',
  seeyonUsername: '',
  seeyonPassword: '',
  seeyonFetchType: 'docs', // 'docs' | 'collaboration' | 'news'
  seeyonTimeRange: 30, // days
  seeyonDeptIds: '', // comma separated
  seeyonIncludeAttachments: false,
};

const form = ref({ ...defaultFormState });
const showPassword = ref(false);
const isTestingConnection = ref(false);

const filterOptions = [
  { label: '全部类型', value: 'all' },
  { label: '爬虫数据源', value: 'crawler' },
  { label: 'SFTP 数据源', value: 'sftp' },
  { label: '数据库', value: 'database' },
  { label: 'API 数据源', value: 'api' },
];
const selectedType = ref('all');

const groupOptions = [
  { label: '不分组', value: 'none' },
  { label: '按类型分组', value: 'type' },
  { label: '按状态分组', value: 'status' },
];
const selectedGroup = ref('none');

const dataSourceList = ref<any[]>([]);

const isLoading = ref(false);

const fetchDataSources = async () => {
  isLoading.value = true;
  try {
    const data = await dataSourceApi.list();
    
    // Mock Data (if empty)
    if (data.length === 0) {
      dataSourceList.value = [
        {
          id: 101,
          name: '示例 SFTP 数据源',
          type: 'sftp',
          status: 'running',
          throughput: '0/s',
          metrics: { today_files: 0, current_file: null }
        },
        {
          id: 102,
          name: '示例 政策法规爬虫',
          type: 'crawler',
          status: 'running',
          throughput: '0/s',
          metrics: { today_count: 0, success_rate: 0 }
        },
        {
          id: 103,
          name: '示例 生产数据库 (MySQL)',
          type: 'database',
          status: 'running',
          throughput: '0/s',
          metrics: { table_count: 0, total_records: 0, db_type: 'MySQL' }
        },
        {
          id: 104,
          name: '示例 外部汇率 API',
          type: 'api',
          status: 'running',
          throughput: '0/s',
          metrics: { api_calls: 0, data_volume: 0 }
        }
      ];
      return;
    }

    // Map backend data to frontend model if necessary, or just use as is
    // Backend returns snake_case, frontend uses mixed but mostly relies on item properties
    // Let's assume we use backend properties directly and adjust template if needed.
    // The template uses item.name, item.type, item.status, item.metrics
    // Backend doesn't return metrics yet (it's not in DataSourceOut schema), so we might need to mock or fetch separately
    // For now, let's just use what we get and maybe add default metrics
    dataSourceList.value = data.map(item => ({
      ...item,
      status: 'running', // Mock status for now as backend doesn't return it in list
      throughput: '0/s', // Mock
      metrics: {} // Mock
    }));
  } catch (error) {
    console.error('Failed to fetch data sources:', error);
    toast({
      title: "获取数据源失败",
      description: "无法连接到服务器",
      variant: "destructive"
    });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchDataSources();
});

// Computed
const filteredDataSourceList = computed(() => {
  let result = dataSourceList.value;
  if (selectedType.value !== 'all') {
    result = result.filter(item => item.type === selectedType.value);
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(item => item.name.toLowerCase().includes(q));
  }
  return result;
});

const groupedDataSources = computed<{ title: string; items: any[] }[]>(() => {
  const list = filteredDataSourceList.value;
  if (selectedGroup.value === 'none') {
    return [{ title: '', items: list }];
  }
  if (selectedGroup.value === 'type') {
     const types = ['crawler', 'sftp', 'database', 'api'];
     const typeLabels: Record<string, string> = {
       'crawler': '网络爬虫',
       'sftp': 'SFTP 文件流',
       'database': '结构化数据库',
       'api': '外部 API'
     };
     return types.reduce<{ title: string; items: any[] }[]>((acc, type) => {
        const items = list.filter(item => item.type === type);
        if (items.length) {
          acc.push({ title: typeLabels[type] || type.toUpperCase(), items });
        }
        return acc;
     }, []);
  }
  if (selectedGroup.value === 'status') {
     const statuses = ['running', 'stopped', 'error'];
     const statusLabels: Record<string, string> = {
       'running': '运行中',
       'stopped': '已停止',
       'error': '异常'
     };
     return statuses.reduce<{ title: string; items: any[] }[]>((acc, status) => {
        const items = list.filter(item => item.status === status);
        if (items.length) {
          acc.push({ title: statusLabels[status] || status.toUpperCase(), items });
        }
        return acc;
     }, []);
  }
  // Simplified logic
  return [{ title: '', items: list }];
});

const activeDataSource = ref<any>(null);
const relatedPipelines = ref<any[]>([]);

// Methods
const selectType = (type: string) => {
  form.value.type = type;
};

const openDrawer = (item: any) => {
  activeDataSource.value = item;
  relatedPipelines.value = [
    { id: 1, name: '数据清洗流程 A', status: 'running', processed: 1234, last_run: '1分钟前' },
    { id: 2, name: '归档流程 B', status: 'success', processed: 5678, last_run: '1小时前' }
  ];
  showDrawer.value = true;
};

const tryParseJson = (str: string) => {
  try {
    return str ? JSON.parse(str) : {};
  } catch (e) {
    return {};
  }
};

const mapFormToPayload = (formData: typeof form.value): DataSourceCreate => {
  const base = {
    name: formData.name,
    type: formData.type,
    description: formData.description,
  };

  if (formData.type === 'sftp') {
    return {
      ...base,
      host: formData.host,
      port: formData.port,
      username: formData.username,
      password: formData.authType === 'password' ? formData.password : undefined,
      private_key: formData.authType === 'key' ? formData.privateKey : undefined,
      config: {
        provider: formData.sftpProvider,
        path: formData.sftpRemotePath,
        pattern: formData.sftpFilePattern,
        recursive: formData.sftpRecursive,
        delete_after: formData.sftpDeleteAfter,
        passphrase: formData.passphrase,
        auth_type: formData.authType
      }
    };
  }
  
  if (formData.type === 'crawler') {
    return {
      ...base,
      url: formData.targetUrl.split('\n')[0],
      config: {
        urls: formData.targetUrl.split('\n').filter(u => u.trim()),
        subtype: formData.crawlerProvider,
        keywords: formData.searchKeywords,
        cron: formData.cronExpression,
        depth: formData.tavilySearchDepth,
        inclusions: formData.tavilyInclusions,
        max_results: formData.tavilyMaxResults,
        ali_access_key_id: formData.aliAccessKeyId,
        ali_access_key_secret: formData.aliAccessKeySecret,
        ali_endpoint: formData.aliEndpoint,
        ali_app_name: formData.aliAppName,
        ali_index_name: formData.aliIndexName,
        ali_fetch_fields: formData.aliFetchFields,
        ali_query_clause: formData.aliQueryClause,
        ali_filter_clause: formData.aliFilterClause,
        ali_sort_clause: formData.aliSortClause,
        ali_config_clause: formData.aliConfigClause,
        ali_protocol: formData.aliProtocol
      },
      api_key: formData.crawlerProvider === 'tavily' ? formData.tavilyApiKey : undefined
    };
  }

  if (formData.type === 'database') {
    return {
      ...base,
      host: formData.dbHost,
      port: formData.dbPort,
      username: formData.dbUsername,
      password: formData.dbPassword,
      database: formData.dbName,
      config: {
        type: formData.dbType,
        ssl: formData.dbSsl,
        ssh: formData.dbSsh,
        ssh_host: formData.dbSshHost,
        ssh_port: formData.dbSshPort,
        ssh_user: formData.dbSshUser,
        ssh_auth_type: formData.dbSshAuthType,
        ssh_password: formData.dbSshPassword,
        ssh_key: formData.dbSshKey,
        max_connections: formData.dbMaxConnections[0],
        timeout: formData.dbTimeout,
        charset: formData.dbCharset
      }
    };
  }

  if (formData.type === 'api') {
    return {
      ...base,
      url: formData.apiUrl,
      config: {
        provider: formData.apiProvider,
        method: formData.apiMethod,
        headers: tryParseJson(formData.apiHeaders),
        body: tryParseJson(formData.apiBody),
        params: tryParseJson(formData.apiParams),
        auth_type: formData.apiAuthType,
        auth_username: formData.apiAuthUsername,
        auth_password: formData.apiAuthPassword,
        auth_key_name: formData.apiAuthKeyName,
        auth_key_location: formData.apiAuthKeyLocation,
        pagination_type: formData.apiPaginationType,
        page_param: formData.apiPaginationPageParam,
        size_param: formData.apiPaginationSizeParam,
        size: formData.apiPaginationSize,
        cursor_param: formData.apiPaginationCursorParam,
        field_path: formData.apiPaginationField,
        feishu_app_id: formData.feishuAppId,
        feishu_app_secret: formData.feishuAppSecret,
        feishu_target: formData.feishuTarget,
        feishu_space_id: formData.feishuSpaceId,
        feishu_folder_token: formData.feishuFolderToken,
        dingtalk_app_key: formData.dingtalkAppKey,
        dingtalk_app_secret: formData.dingtalkAppSecret,
        dingtalk_target: formData.dingtalkTarget,
        dingtalk_process_code: formData.dingtalkProcessCode,
        dingtalk_start_time: formData.dingtalkStartTime,
        seeyon_base_url: formData.seeyonBaseUrl,
        seeyon_username: formData.seeyonUsername,
        seeyon_password: formData.seeyonPassword,
        seeyon_fetch_type: formData.seeyonFetchType,
        seeyon_time_range: formData.seeyonTimeRange,
        seeyon_dept_ids: formData.seeyonDeptIds,
        seeyon_include_attachments: formData.seeyonIncludeAttachments
      },
      token: formData.apiAuthType === 'bearer' ? formData.apiAuthToken : undefined,
      api_key: formData.apiAuthType === 'apikey' ? formData.apiAuthKeyValue : undefined
    };
  }

  return base as DataSourceCreate;
};

const mapItemToForm = (item: any) => {
  const formState = { ...defaultFormState, id: item.id, name: item.name, type: item.type, description: item.description };
  const cfg = item.config || {};

  if (item.type === 'sftp') {
    formState.host = item.host;
    formState.port = item.port || 22;
    formState.username = item.username;
    // Password usually not returned
    formState.authType = cfg.auth_type || (item.private_key ? 'key' : 'password');
    
    formState.sftpProvider = cfg.provider || 'custom';
    formState.sftpRemotePath = cfg.path || '/';
    formState.sftpFilePattern = cfg.pattern || '*';
    formState.sftpRecursive = cfg.recursive || false;
    formState.sftpDeleteAfter = cfg.delete_after || false;
  } else if (item.type === 'crawler') {
    formState.targetUrl = (cfg.urls || [item.url]).join('\n');
    formState.crawlerProvider = cfg.subtype || 'tavily';
    formState.searchKeywords = cfg.keywords || '';
    formState.cronExpression = cfg.cron || '0 0 * * *';
    
    if (formState.crawlerProvider === 'tavily') {
      formState.tavilySearchDepth = cfg.depth || 'basic';
      formState.tavilyInclusions = cfg.inclusions || [];
      formState.tavilyMaxResults = cfg.max_results || 5;
    } else {
      formState.aliAccessKeyId = cfg.ali_access_key_id;
      formState.aliEndpoint = cfg.ali_endpoint;
      formState.aliAppName = cfg.ali_app_name;
      formState.aliIndexName = cfg.ali_index_name;
      // ...
    }
  } else if (item.type === 'database') {
    formState.dbHost = item.host;
    formState.dbPort = item.port;
    formState.dbUsername = item.username;
    formState.dbName = item.database;
    formState.dbType = cfg.type || 'mysql';
    formState.dbSsl = cfg.ssl || false;
    formState.dbSsh = cfg.ssh || false;
    formState.dbMaxConnections = [cfg.max_connections || 10];
    formState.dbTimeout = cfg.timeout || 30;
    formState.dbCharset = cfg.charset || 'utf8mb4';
  } else if (item.type === 'api') {
    formState.apiUrl = item.url;
    formState.apiProvider = cfg.provider || 'custom';
    formState.apiMethod = cfg.method || 'GET';
    formState.apiHeaders = JSON.stringify(cfg.headers || {});
    formState.apiBody = JSON.stringify(cfg.body || {});
    formState.apiParams = JSON.stringify(cfg.params || {});
    formState.apiAuthType = cfg.auth_type || 'none';
    // ...
  }
  
  return formState;
};

const openAddModal = () => {
  isEditing.value = false;
  currentStep.value = 1;
  form.value = { ...defaultFormState };
  showModal.value = true;
};

const editDataSource = (item: any) => {
  isEditing.value = true;
  currentStep.value = 2;
  form.value = mapItemToForm(item);
  showModal.value = true;
};

const saveDataSource = async () => {
  if (!form.value.name) {
    toast({
      title: "验证失败",
      description: "请填写数据源名称",
      variant: "destructive"
    });
    return;
  }
  
  const payload = mapFormToPayload(form.value);
  
  try {
    if (isEditing.value) {
       await dataSourceApi.update(form.value.id, payload);
       toast({ title: "保存成功", description: "数据源已更新" });
    } else {
       await dataSourceApi.create(payload);
       toast({ title: "创建成功", description: "新数据源已添加" });
    }
    showModal.value = false;
    fetchDataSources();
  } catch (error: any) {
    console.error(error);
    toast({
      title: isEditing.value ? "更新失败" : "创建失败",
      description: error.response?.data?.detail || "操作发生错误",
      variant: "destructive"
    });
  }
};

const confirmDelete = async (item: any) => {
  // Use native confirm for now or implement AlertDialog
  if (confirm(`确定要删除 "${item.name}" 吗？`)) {
    try {
      await dataSourceApi.delete(item.id);
      toast({ title: "已删除", description: "数据源已移除" });
      fetchDataSources();
    } catch (error: any) {
      toast({
        title: "删除失败",
        description: error.response?.data?.detail || "操作发生错误",
        variant: "destructive"
      });
    }
  }
};

const testConnectionWrapper = async () => {
  isTestingConnection.value = true;
  try {
    const payload = mapFormToPayload(form.value);
    const result = await dataSourceApi.testConnection(payload);
    
    if (result.success) {
      toast({ title: "连接成功", description: result.message });
    } else {
      toast({ 
        title: "连接失败", 
        description: result.message,
        variant: "destructive" 
      });
    }
  } catch (error: any) {
    toast({
      title: "测试连接错误",
      description: error.response?.data?.detail || "无法连接到服务器",
      variant: "destructive"
    });
  } finally {
    isTestingConnection.value = false;
  }
};

const getStatusColor = (status: string) => {
  return status === 'running' ? 'bg-green-500' : 'bg-gray-500';
};
const getStatusText = (status: string) => status === 'running' ? '运行中' : '未知';

const formatNumber = (num: number) => num.toLocaleString();

const dataSourceTypes = [
  { value: 'sftp', label: 'SFTP 文件流', desc: 'Paramiko 连接，支持实时监控', icon: File, iconBg: 'bg-blue-500' },
  { value: 'crawler', label: 'Web 爬虫', desc: '网络数据抓取', icon: Globe, iconBg: 'bg-green-500' },
  { value: 'database', label: '结构化数据库', desc: 'SQLAlchemy 多数据库支持', icon: Database, iconBg: 'bg-purple-500' },
  { value: 'api', label: '外部 API', desc: 'REST API 数据采买', icon: Server, iconBg: 'bg-amber-500' }
];

const databaseTypes = [
  { value: 'mysql', label: 'MySQL', icon: 'https://upload.wikimedia.org/wikipedia/labs/8/8e/Mysql_logo.png' },
  { value: 'postgres', label: 'PostgreSQL', icon: 'https://cdn.worldvectorlogo.com/logos/postgresql.svg' },
  { value: 'sqlserver', label: 'SQL Server', icon: 'https://cdn.worldvectorlogo.com/logos/microsoft-sql-server-1.svg' },
  { value: 'oracle', label: 'Oracle', icon: 'https://cdn.worldvectorlogo.com/logos/oracle-6.svg' },
  { value: 'sqlite', label: 'SQLite', icon: 'https://cdn.worldvectorlogo.com/logos/sqlite.svg' },
  { value: 'mariadb', label: 'MariaDB', icon: 'https://cdn.worldvectorlogo.com/logos/mariadb.svg' },
  { value: 'mongodb', label: 'MongoDB', icon: 'https://cdn.worldvectorlogo.com/logos/mongodb-icon-1.svg' },
  { value: 'redis', label: 'Redis', icon: 'https://cdn.worldvectorlogo.com/logos/redis.svg' },
  { value: 'elasticsearch', label: 'Elasticsearch', icon: 'https://cdn.worldvectorlogo.com/logos/elasticsearch.svg' },
  { value: 'clickhouse', label: 'ClickHouse', icon: 'https://cdn.worldvectorlogo.com/logos/clickhouse-1.svg' },
  { value: 'hive', label: 'Hive', icon: 'https://upload.wikimedia.org/wikipedia/commons/b/bb/Apache_Hive_logo.svg' },
  { value: 'snowflake', label: 'Snowflake', icon: 'https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg' },
];

const privateKeyError = ref('');
const handleKeyFileUpload = () => {};
const navigateToEtlDetail = (pipeline: any) => {
  console.log('Navigate to pipeline:', pipeline);
};

</script>

<style scoped>
</style>
