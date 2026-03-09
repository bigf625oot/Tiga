<template>
  <div class="h-full flex bg-background text-foreground overflow-hidden font-sans">
    <!-- Sidebar -->
    <div 
      class="bg-card border-r flex flex-col flex-shrink-0 transition-all duration-300 relative z-20"
      :style="{ width: leftWidth + 'px' }"
    >
      <div class="p-4 pb-2">
        <Tabs v-model="leftTab" class="w-full">
          <TabsList class="grid w-full grid-cols-2">
            <TabsTrigger value="sessions">会话列表</TabsTrigger>
            <TabsTrigger value="config">连接配置</TabsTrigger>
          </TabsList>
          
          <!-- Sessions Tab -->
          <TabsContent value="sessions" class="mt-4 h-[calc(100vh-140px)] outline-none">
            <div class="flex items-center gap-2 mb-4">
              <div class="relative flex-1">
                <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  v-model="sessionSearch" 
                  placeholder="搜索会话..." 
                  class="pl-9 h-9"
                />
              </div>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button variant="outline" size="icon" class="h-9 w-9" @click="handleCreateSession">
                      <Plus class="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>新建会话</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <ScrollArea class="h-full pr-4 -mr-4">
              <div v-if="filteredSessions.length === 0" class="text-center text-sm text-muted-foreground py-8">
                暂无会话
              </div>
              <div class="space-y-1 pr-4">
                <div
                  v-for="s in filteredSessions"
                  :key="s.id"
                  @click="selectSession(s.id)"
                  class="group flex flex-col gap-1 rounded-lg border p-3 text-sm transition-all hover:bg-accent cursor-pointer relative"
                  :class="activeSessionId === s.id ? 'bg-accent border-primary/50 shadow-sm' : 'border-transparent'"
                >
                  <div class="flex items-center justify-between font-medium">
                    <div class="flex items-center gap-2 truncate pr-6">
                      <Star v-if="s.is_pinned" class="h-3 w-3 fill-amber-400 text-amber-400 flex-shrink-0" />
                      <span class="truncate">{{ s.title || '未命名会话' }}</span>
                      <Badge v-if="s.is_archived" variant="secondary" class="text-[10px] h-4 px-1">归档</Badge>
                    </div>
                  </div>
                  
                  <div class="text-xs text-muted-foreground line-clamp-1">
                    {{ s.last_message_preview || '暂无消息' }}
                  </div>
                  
                  <div class="flex items-center justify-between text-[10px] text-muted-foreground mt-1">
                    <span>{{ formatRelative(s.updated_at || s.created_at) }}</span>
                  </div>

                  <!-- Context Menu -->
                  <div class="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <DropdownMenu>
                      <DropdownMenuTrigger as-child>
                        <Button variant="ghost" size="icon" class="h-6 w-6">
                          <MoreVertical class="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem @click.stop="handleRenameSession(s)">
                          <Edit2 class="mr-2 h-3 w-3" />重命名
                        </DropdownMenuItem>
                        <DropdownMenuItem @click.stop="togglePin(s)">
                          <Star class="mr-2 h-3 w-3" :class="{ 'fill-current': s.is_pinned }" />{{ s.is_pinned ? '取消置顶' : '置顶' }}
                        </DropdownMenuItem>
                        <DropdownMenuItem @click.stop="toggleArchive(s)">
                          <Archive class="mr-2 h-3 w-3" />{{ s.is_archived ? '取消归档' : '归档' }}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem @click.stop="handleDeleteSession(s)" class="text-destructive focus:text-destructive">
                          <Trash2 class="mr-2 h-3 w-3" />删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          <!-- Config Tab -->
          <TabsContent value="config" class="mt-4 h-[calc(100vh-140px)] outline-none">
            <ScrollArea class="h-full pr-4 -mr-4">
              <div class="space-y-6 pr-4 pb-8">
                <div class="space-y-4">
                  <div class="space-y-2">
                    <Label>数据库类型</Label>
                    <Select v-model="config.type" @update:modelValue="handleTypeChange">
                      <SelectTrigger>
                        <SelectValue placeholder="选择数据库类型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sqlite">SQLite</SelectItem>
                        <SelectItem value="postgresql">PostgreSQL</SelectItem>
                        <SelectItem value="mysql">MySQL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <template v-if="config.type === 'sqlite'">
                    <div class="space-y-2">
                      <Label>文件路径</Label>
                      <Input v-model="config.path" placeholder="e.g. /data/app.db" />
                      <p class="text-[10px] text-muted-foreground">请输入 SQLite 数据库文件的绝对路径</p>
                    </div>
                  </template>

                  <template v-else>
                    <div class="grid grid-cols-3 gap-4">
                      <div class="col-span-2 space-y-2">
                        <Label>主机地址</Label>
                        <Input v-model="config.host" placeholder="localhost" />
                      </div>
                      <div class="space-y-2">
                        <Label>端口</Label>
                        <Input type="number" v-model.number="config.port" />
                      </div>
                    </div>
                    
                    <div class="space-y-2">
                      <Label>用户名</Label>
                      <Input v-model="config.user" placeholder="root" />
                    </div>
                    
                    <div class="space-y-2">
                      <Label>密码</Label>
                      <Input type="password" v-model="config.password" placeholder="••••••••" />
                    </div>

                    <Collapsible v-model:open="showAdvanced" class="space-y-2">
                      <CollapsibleTrigger as-child>
                        <Button variant="ghost" size="sm" class="p-0 h-auto font-normal text-xs text-primary hover:bg-transparent">
                          <Settings class="h-3 w-3 mr-1" />
                          更多高级配置
                          <ChevronRight class="h-3 w-3 ml-1 transition-transform" :class="{ 'rotate-90': showAdvanced }" />
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent class="space-y-4 pt-2 animate-in slide-in-from-top-2">
                        <div class="space-y-2">
                          <Label>数据库名称</Label>
                          <Input v-model="config.database" placeholder="选填，默认连接" />
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-2">
                            <Label>连接超时 (秒)</Label>
                            <Input type="number" v-model.number="config.timeout" />
                          </div>
                          <div class="space-y-2">
                            <Label>连接池大小</Label>
                            <Input type="number" v-model.number="config.pool_size" />
                          </div>
                        </div>
                        <div v-if="config.type === 'mysql'" class="space-y-2">
                          <Label>字符集</Label>
                          <Select v-model="config.charset">
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="utf8mb4">utf8mb4</SelectItem>
                              <SelectItem value="utf8">utf8</SelectItem>
                              <SelectItem value="latin1">latin1</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div v-if="config.type === 'postgresql'" class="space-y-2">
                          <Label>SSL 模式</Label>
                          <Select v-model="config.ssl_mode">
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="disable">Disable</SelectItem>
                              <SelectItem value="require">Require</SelectItem>
                              <SelectItem value="verify-ca">Verify CA</SelectItem>
                              <SelectItem value="verify-full">Verify Full</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </template>
                </div>

                <div class="space-y-3 pt-2">
                  <Button variant="outline" class="w-full" @click="testConnection" :disabled="testing || connecting">
                    <Loader2 v-if="testing" class="mr-2 h-4 w-4 animate-spin" />
                    <Play v-else class="mr-2 h-4 w-4" />
                    测试连接
                  </Button>
                  <Button class="w-full" @click="saveAndConnect" :disabled="testing || connecting">
                    <Loader2 v-if="connecting" class="mr-2 h-4 w-4 animate-spin" />
                    <Save v-else class="mr-2 h-4 w-4" />
                    保存并连接
                  </Button>
                </div>

                <!-- Status Feedback -->
                <div v-if="testResult" 
                  class="rounded-lg border p-3 text-sm flex items-start gap-3"
                  :class="testResult.success ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'"
                >
                  <CheckCircle2 v-if="testResult.success" class="h-5 w-5 flex-shrink-0" />
                  <XCircle v-else class="h-5 w-5 flex-shrink-0" />
                  <span class="break-all text-xs">{{ testResult.message }}</span>
                </div>

                <!-- Help Card -->
                <Card class="bg-muted/50 border-none shadow-none">
                  <CardContent class="p-4 text-xs space-y-2 text-muted-foreground">
                    <div class="font-medium flex items-center gap-1.5 text-foreground">
                      <Info class="h-3.5 w-3.5" />
                      使用提示
                    </div>
                    <p>连接成功后，您可以直接使用自然语言查询数据。</p>
                    <ul class="list-disc list-inside space-y-1 pl-1">
                      <li>"查询最近10笔销售记录"</li>
                      <li>"统计各类目的销售总额"</li>
                      <li>"绘制月度销售趋势图"</li>
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>
    </div>
    
    <!-- Resize Handle -->
    <div 
      class="w-1 hover:bg-primary/20 cursor-col-resize flex-shrink-0 transition-colors z-30"
      :class="isResizing ? 'bg-primary/20' : 'bg-border/30'"
      @mousedown="startResizing"
    ></div>
      
    <!-- Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-background relative z-10 min-w-0">
      <!-- Header -->
      <div class="h-14 border-b flex items-center justify-between px-6 bg-background/95 backdrop-blur z-20">
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="p-1.5 bg-primary/10 rounded-md">
            <Database class="h-4 w-4 text-primary" />
          </div>
          <div class="flex flex-col min-w-0">
            <span class="text-sm font-semibold truncate">{{ currentSession?.title || '未选择会话' }}</span>
            <span class="text-[10px] text-muted-foreground truncate">
              {{ currentSession ? `最近更新: ${formatRelative(currentSession.updated_at || currentSession.created_at)}` : '请选择或创建会话' }}
            </span>
          </div>
        </div>
        
        <div v-if="currentSession" class="flex items-center gap-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <Button variant="ghost" size="icon" @click="handleRenameSession(currentSession)">
                  <Edit2 class="h-4 w-4 text-muted-foreground" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>重命名</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger as-child>
                <Button variant="ghost" size="icon" @click="togglePin(currentSession)">
                  <Star class="h-4 w-4" :class="currentSession.is_pinned ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground'" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>{{ currentSession.is_pinned ? '取消置顶' : '置顶' }}</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger as-child>
                <Button variant="ghost" size="icon" @click="handleDeleteSession(currentSession)" class="hover:text-destructive hover:bg-destructive/10">
                  <Trash2 class="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>删除会话</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-hidden relative">
        <ScrollArea class="h-full px-6" ref="messagesContainer">
          <div class="py-6 space-y-8 max-w-4xl mx-auto">
            <div v-if="messages.length === 0" class="h-[60vh] flex flex-col items-center justify-center text-muted-foreground">
              <div class="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-6">
                <Database class="h-8 w-8 text-muted-foreground/50" />
              </div>
              <h3 class="text-lg font-semibold text-foreground mb-2">智能问数助手</h3>
              <p class="text-sm max-w-xs text-center leading-relaxed">
                连接数据库，然后开始提问。<br>我会为您生成 SQL、查询数据并可视化结果。
              </p>
            </div>

            <div v-for="(msg, index) in messages" :key="msg._id || index" 
                 :class="['flex gap-4 group', msg.role === 'user' ? 'flex-row-reverse' : '']">
              
              <!-- Avatar -->
              <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border shadow-sm"
                   :class="msg.role === 'user' ? 'bg-primary text-primary-foreground border-primary' : 'bg-background text-muted-foreground'">
                <span v-if="msg.role === 'user'" class="text-xs font-bold">ME</span>
                <Database v-else class="h-4 w-4" />
              </div>

              <!-- Message Content -->
              <div :class="['flex flex-col max-w-[90%]', msg.role === 'user' ? 'items-end' : 'items-start w-full']">
                
                <!-- Bubble -->
                <div :class="[
                  'rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-sm',
                  msg.role === 'user' 
                    ? 'bg-primary text-primary-foreground rounded-tr-sm' 
                    : 'bg-card border text-card-foreground rounded-tl-sm w-full'
                ]">
                  
                  <div v-if="msg.role === 'assistant'" class="space-y-4">
                    <!-- Thinking Process -->
                    <Collapsible 
                      v-if="msg.steps && msg.steps.length > 0"
                      :defaultOpen="false"
                      class="border rounded-lg bg-muted/30 overflow-hidden"
                    >
                      <CollapsibleTrigger class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted/50 transition-colors">
                        <div class="flex items-center gap-2">
                          <Loader2 v-if="isStreaming && index === messages.length - 1" class="h-3 w-3 animate-spin text-primary" />
                          <CheckCircle2 v-else class="h-3 w-3 text-green-500" />
                          <span>思考过程 ({{ msg.steps.length }} 步骤)</span>
                        </div>
                        <ChevronDown class="h-3 w-3 transition-transform duration-200" />
                      </CollapsibleTrigger>
                      <CollapsibleContent class="px-3 pb-3 pt-0 space-y-3 border-t bg-muted/10">
                        <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="relative pl-4 pt-3 last:pb-0">
                          <div class="absolute left-0 top-4 w-1.5 h-1.5 rounded-full bg-primary/40"></div>
                          <div v-if="sIdx < msg.steps.length - 1" class="absolute left-[2.5px] top-6 bottom-[-12px] w-[1px] bg-border"></div>
                          
                          <div class="text-xs font-medium flex justify-between">
                            <span>步骤 {{ step.step }}</span>
                            <span class="text-[10px] text-muted-foreground font-mono">{{ formatRelative(step.timestamp) }}</span>
                          </div>
                          <div v-if="step.content" class="mt-1 text-[11px] font-mono bg-background border rounded p-2 text-muted-foreground overflow-x-auto">
                            {{ typeof step.content === 'object' ? JSON.stringify(step.content, null, 2) : step.content.trim() }}
                          </div>
                        </div>
                      </CollapsibleContent>
                    </Collapsible>

                    <!-- Main Content / Tabs -->
                    <div v-if="msg.content || msg.sql_query">
                      <Tabs :defaultValue="getMsgViewMode(msg._id)" class="w-full" @update:modelValue="(v) => setMsgViewMode(msg._id, v)">
                        <div class="flex items-center justify-between mb-2" v-if="msg.sql_query">
                          <span class="text-xs font-medium text-muted-foreground">查询结果</span>
                          <TabsList class="h-7">
                            <TabsTrigger value="table" class="h-5 text-[10px] px-2">
                              <TableIcon class="h-3 w-3 mr-1" />表格
                            </TabsTrigger>
                            <TabsTrigger value="sql" class="h-5 text-[10px] px-2">
                              <Code class="h-3 w-3 mr-1" />SQL
                            </TabsTrigger>
                          </TabsList>
                        </div>

                        <TabsContent value="table" class="mt-0">
                          <div 
                            v-if="msg.content"
                            class="markdown-body prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 prose-pre:bg-transparent"
                            v-html="renderMarkdown(getMessageText(msg.content))"
                            @click="handleContentClick"
                          ></div>
                          <div v-else-if="isStreaming" class="space-y-2">
                            <Skeleton class="h-4 w-3/4" />
                            <Skeleton class="h-4 w-1/2" />
                          </div>
                        </TabsContent>

                        <TabsContent value="sql" class="mt-0">
                          <div class="relative group/sql">
                            <pre class="p-4 text-xs font-mono bg-muted rounded-lg border overflow-x-auto text-foreground"><code>{{ msg.sql_query }}</code></pre>
                            <Button 
                              variant="secondary" 
                              size="icon" 
                              class="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover/sql:opacity-100 transition-opacity"
                              @click="copySql(msg.sql_query)"
                            >
                              <span class="sr-only">复制</span>
                              <FileText class="h-3 w-3" />
                            </Button>
                          </div>
                        </TabsContent>
                      </Tabs>
                    </div>

                    <!-- Chart -->
                    <div v-if="msg.chart_config || getMessageChart(msg.content)" class="pt-2 border-t mt-4">
                      <div class="flex items-center gap-2 mb-3">
                        <BarChart2 class="h-4 w-4 text-primary" />
                        <span class="text-xs font-semibold">可视化图表</span>
                      </div>
                      <div class="h-80 w-full bg-card rounded-lg border shadow-sm p-4">
                        <ChartFrame class="chart" :option="processChartOption(msg.chart_config || getMessageChart(msg.content))" />
                      </div>
                    </div>
                  </div>
                  
                  <div v-else>{{ msg.content }}</div>
                </div>
              </div>
            </div>

            <!-- Loading Indicator -->
            <div v-if="isLoading && !isStreaming" class="flex gap-4 max-w-4xl">
               <div class="w-8 h-8 rounded-full bg-background border flex items-center justify-center shadow-sm">
                 <Loader2 class="h-4 w-4 animate-spin text-primary" />
               </div>
               <div class="bg-card border rounded-lg px-4 py-3 shadow-sm flex items-center gap-1">
                 <span class="text-xs text-muted-foreground">思考中...</span>
               </div>
            </div>
            
            <div class="h-4"></div>
          </div>
        </ScrollArea>
      </div>

      <!-- Input Area -->
      <div class="p-4 bg-background border-t z-20">
        <div class="max-w-4xl mx-auto relative">
          <div class="relative rounded-xl border bg-card shadow-sm focus-within:ring-1 focus-within:ring-primary transition-all">
            <Textarea 
              v-model="input"
              @keydown.enter.exact.prevent="sendMessage"
              ref="textareaRef"
              placeholder="输入您的问题，例如：'统计上个月的销售总额'..."
              class="min-h-[60px] max-h-[200px] w-full resize-none border-0 bg-transparent focus-visible:ring-0 px-4 py-3 pr-24"
              :disabled="isLoading"
            />
            
            <div class="absolute right-2 bottom-2 flex items-center gap-1">
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-primary">
                    <LayoutPanelLeft class="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="w-64">
                  <DropdownMenuLabel>推荐图表查询</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    v-for="t in templates" 
                    :key="t.name"
                    @click="insertTemplate(t.content)"
                    class="cursor-pointer"
                  >
                    {{ t.name }}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Button 
                @click="sendMessage" 
                size="icon"
                class="h-8 w-8 transition-all"
                :disabled="isLoading || !input.trim()"
                :class="input.trim() ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'"
              >
                <Send class="h-4 w-4" />
              </Button>
            </div>
          </div>
          <div class="flex justify-between mt-2 px-1">
            <span class="text-[10px] text-muted-foreground">智能问数 · Tiga AI 驱动</span>
            <span class="text-[10px] text-muted-foreground">{{ input.length }}/2000</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Dialogs -->
  <Dialog v-model:open="createModalOpen">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>新建会话</DialogTitle>
        <DialogDescription>
          创建一个新的会话以开始查询数据。
        </DialogDescription>
      </DialogHeader>
      <div class="py-4">
        <Label class="mb-2 block">会话标题</Label>
        <Input v-model="createForm.title" placeholder="请输入会话标题" @keydown.enter="confirmCreateSession" />
      </div>
      <DialogFooter>
        <Button variant="outline" @click="closeCreateModal">取消</Button>
        <Button @click="confirmCreateSession" :disabled="createLoading">
          <Loader2 v-if="createLoading" class="mr-2 h-4 w-4 animate-spin" />
          创建
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <Dialog v-model:open="renameModalOpen">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>重命名会话</DialogTitle>
      </DialogHeader>
      <div class="py-4">
        <Label class="mb-2 block">新标题</Label>
        <Input v-model="renameForm.title" placeholder="请输入新标题" @keydown.enter="confirmRenameSession" />
      </div>
      <DialogFooter>
        <Button variant="outline" @click="closeRenameModal">取消</Button>
        <Button @click="confirmRenameSession" :disabled="renameLoading">
          <Loader2 v-if="renameLoading" class="mr-2 h-4 w-4 animate-spin" />
          保存
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <AlertDialog v-model:open="deleteModalOpen">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>确定要删除该会话吗？</AlertDialogTitle>
        <AlertDialogDescription>
          此操作不可恢复。该会话及其所有历史记录将被永久删除。
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel @click="closeDeleteModal">取消</AlertDialogCancel>
        <AlertDialogAction @click="confirmDeleteSession" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
          <Loader2 v-if="deleteLoading" class="mr-2 h-4 w-4 animate-spin" />
          删除
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>

  <Toaster />
</template>

<script setup>
import { ref, nextTick, onMounted, reactive, computed, watch } from 'vue';
import { marked } from 'marked';
import ChartFrame from './ChartFrame.vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';
import 'dayjs/locale/zh-cn';

// UI Components
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Toaster } from '@/components/ui/toast';
import { useToast } from '@/components/ui/toast/use-toast';

// Icons
import {
  Search, Plus, MoreVertical, Star, Archive, Trash2, Edit2, Settings,
  Database, ChevronRight, ChevronDown, Play, Save, Info,
  Send, BarChart2, Table as TableIcon, Code,
  Loader2, FileText, CheckCircle2, XCircle, LayoutPanelLeft
} from 'lucide-vue-next';

const { toast } = useToast();

dayjs.extend(relativeTime);
dayjs.extend(utc);
dayjs.locale('zh-cn');

// State
const leftTab = ref('sessions');
const sessions = ref([]);
const sessionSearch = ref('');
const activeSessionId = ref(null);
const sessionsLoading = ref(false);
const msgViewModes = reactive({});

const config = ref({
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
const input = ref('');
const messages = ref([]);
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);
const currentController = ref(null);
const textareaRef = ref(null);

// Resizable left pane
const leftWidth = ref(340);
const isResizing = ref(false);
const startX = ref(0);
const startWidth = ref(leftWidth.value);

const templates = [
    { name: '📊 统计表数据量', content: '统计数据库中各表的数据量，并绘制柱状图' },
    { name: '📈 销售趋势分析', content: '查询 orders 表中最近 7 天的订单数量趋势，绘制折线图' },
    { name: '🥧 用户分布统计', content: '统计 users 表中不同地区的用户分布，绘制饼图' }
];

// Modals state
const createModalOpen = ref(false);
const createLoading = ref(false);
const createForm = reactive({ title: '新的会话' });
const renameModalOpen = ref(false);
const renameLoading = ref(false);
const renameForm = reactive({ title: '' });
const deleteModalOpen = ref(false);
const deleteLoading = ref(false);
const targetSession = ref(null);

// Computed
const filteredSessions = computed(() => {
    const q = (sessionSearch.value || '').toLowerCase();
    const base = sessions.value.slice().filter(s =>
        !q ||
        (s.title || '').toLowerCase().includes(q) ||
        (s.last_message_preview || '').toLowerCase().includes(q)
    );
    base.sort((a, b) => {
        if (a.is_pinned !== b.is_pinned) return b.is_pinned ? 1 : -1;
        const ta = dayjs(a.updated_at || a.created_at).valueOf();
        const tb = dayjs(b.updated_at || b.created_at).valueOf();
        return tb - ta;
    });
    return base;
});

const currentSession = computed(() => 
    sessions.value.find(s => s.id === activeSessionId.value) || null
);

// Methods
const formatRelative = (ts) => {
    if (!ts) return '';
    return dayjs.utc(ts).local().fromNow();
};

const getMsgViewMode = (id) => msgViewModes[id] || 'table';
const setMsgViewMode = (id, mode) => { msgViewModes[id] = mode; };

const insertTemplate = (text) => {
    const cur = input.value || '';
    input.value = cur ? (cur.endsWith('\n') ? cur + text : cur + '\n' + text) : text;
};

// Resizing logic
const startResizing = (e) => {
    isResizing.value = true;
    startX.value = e.clientX;
    startWidth.value = leftWidth.value;
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', stopResizing);
    document.body.style.userSelect = 'none';
};

const onMouseMove = (e) => {
    if (!isResizing.value) return;
    const dx = e.clientX - startX.value;
    leftWidth.value = Math.min(Math.max(startWidth.value + dx, 280), 600);
};

const stopResizing = () => {
    isResizing.value = false;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', stopResizing);
    document.body.style.userSelect = '';
};

const handleTypeChange = (val) => {
    if (val === 'postgresql') config.value.port = 5432;
    if (val === 'mysql') config.value.port = 3306;
    if (val === 'sqlite') config.value.port = null;
    testResult.value = null;
};

// API Calls
const fetchConfig = async () => {
    try {
        const res = await fetch('/api/v1/data_query/config');
        if (res.ok) {
            const data = await res.json();
            if (Object.keys(data).length > 0) config.value = { ...config.value, ...data };
        }
    } catch (e) {
        console.error("Failed to load config", e);
    }
};

const testConnection = async () => {
    testResult.value = null;
    if (!validateConfig()) return;
    
    testing.value = true;
    try {
        const res = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (res.ok) {
            testResult.value = { success: true, message: '连接测试成功！' };
            toast({ title: '连接成功', description: '数据库连接测试通过', duration: 3000 });
        } else {
            const err = await res.json();
            testResult.value = { success: false, message: '连接失败: ' + (err.detail || '未知错误') };
            toast({ title: '连接失败', description: err.detail || '未知错误', variant: 'destructive' });
        }
    } catch (e) {
        testResult.value = { success: false, message: '网络错误: ' + e.message };
        toast({ title: '连接错误', description: e.message, variant: 'destructive' });
    } finally {
        testing.value = false;
    }
};

const saveAndConnect = async () => {
    if (!validateConfig()) return;
    
    connecting.value = true;
    testResult.value = null;
    
    try {
        // Connect
        const connRes = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (!connRes.ok) {
            const err = await connRes.json();
            throw new Error(err.detail || '连接失败');
        }
        
        // Save
        await fetch('/api/v1/data_query/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        toast({ title: '保存成功', description: '配置已保存并连接成功', duration: 3000 });
        testResult.value = { success: true, message: '已连接并就绪' };
        
    } catch (e) {
        testResult.value = { success: false, message: e.message };
        toast({ title: '操作失败', description: e.message, variant: 'destructive' });
    } finally {
        connecting.value = false;
    }
};

const validateConfig = () => {
    if (!config.value.type) {
        toast({ title: '配置错误', description: '请选择数据库类型', variant: 'destructive' });
        return false;
    }
    if (config.value.type === 'sqlite' && !config.value.path) {
        toast({ title: '配置错误', description: '请输入数据库文件路径', variant: 'destructive' });
        return false;
    }
    if (config.value.type !== 'sqlite') {
        if (!config.value.host || !config.value.user) {
            toast({ title: '配置错误', description: '请填写主机地址和用户名', variant: 'destructive' });
            return false;
        }
    }
    return true;
};

// Session Management
const fetchSessions = async () => {
    sessionsLoading.value = true;
    try {
        const res = await fetch('/api/v1/data_query/sessions?status=active&limit=100&offset=0&user_id=default_user');
        if (res.ok) {
            const data = await res.json();
            sessions.value = Array.isArray(data.items) ? data.items : [];
        }
    } catch (e) {
        console.error('Failed to fetch sessions', e);
    } finally {
        sessionsLoading.value = false;
    }
};

const handleCreateSession = () => {
    createForm.title = '新的会话';
    createModalOpen.value = true;
};

const confirmCreateSession = async () => {
    createLoading.value = true;
    try {
        const res = await fetch('/api/v1/data_query/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: createForm.title, user_id: 'default_user' })
        });
        if (!res.ok) throw new Error('创建失败');
        const created = await res.json();
        if (created && created.id) {
            sessions.value.unshift(created);
            selectSession(created.id);
        }
        toast({ title: '创建成功', description: '已创建新会话' });
        createModalOpen.value = false;
        leftTab.value = 'sessions';
    } catch (e) {
        toast({ title: '创建失败', description: e.message, variant: 'destructive' });
    } finally {
        createLoading.value = false;
    }
};

const closeCreateModal = () => { createModalOpen.value = false; };

const handleRenameSession = (s) => {
    targetSession.value = s;
    renameForm.title = s.title;
    renameModalOpen.value = true;
};
const closeRenameModal = () => { renameModalOpen.value = false; targetSession.value = null; };

const confirmRenameSession = async () => {
    if (!targetSession.value) return;
    renameLoading.value = true;
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${targetSession.value.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: renameForm.title })
        });
        if (!res.ok) throw new Error('重命名失败');
        const updated = await res.json();
        const idx = sessions.value.findIndex(it => it.id === targetSession.value.id);
        if (idx >= 0) sessions.value[idx] = updated;
        toast({ title: '已重命名', description: `会话已重命名为 "${updated.title}"` });
        closeRenameModal();
    } catch (e) {
        toast({ title: '操作失败', description: e.message, variant: 'destructive' });
    } finally {
        renameLoading.value = false;
    }
};

const togglePin = async (s) => {
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${s.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_pinned: !s.is_pinned })
        });
        if (!res.ok) throw new Error('操作失败');
        const updated = await res.json();
        const idx = sessions.value.findIndex(it => it.id === s.id);
        if (idx >= 0) sessions.value[idx] = updated;
        toast({ title: updated.is_pinned ? '已置顶' : '已取消置顶' });
    } catch (e) {
        toast({ title: '操作失败', description: e.message, variant: 'destructive' });
    }
};

const toggleArchive = async (s) => {
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${s.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_archived: !s.is_archived })
        });
        if (!res.ok) throw new Error('操作失败');
        const updated = await res.json();
        const idx = sessions.value.findIndex(it => it.id === s.id);
        if (idx >= 0) sessions.value[idx] = updated;
        toast({ title: updated.is_archived ? '已归档' : '已取消归档' });
    } catch (e) {
        toast({ title: '操作失败', description: e.message, variant: 'destructive' });
    }
};

const handleDeleteSession = (s) => {
    targetSession.value = s;
    deleteModalOpen.value = true;
};
const closeDeleteModal = () => { deleteModalOpen.value = false; targetSession.value = null; };

const confirmDeleteSession = async () => {
    if (!targetSession.value) return;
    deleteLoading.value = true;
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${targetSession.value.id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('删除失败');
        sessions.value = sessions.value.filter(it => it.id !== targetSession.value.id);
        if (activeSessionId.value === targetSession.value.id) {
            activeSessionId.value = null;
            messages.value = [];
        }
        toast({ title: '已删除', description: '会话已删除' });
        closeDeleteModal();
    } catch (e) {
        toast({ title: '删除失败', description: e.message, variant: 'destructive' });
    } finally {
        deleteLoading.value = false;
    }
};

// Chat Logic
const selectSession = async (id) => {
    activeSessionId.value = id;
    await loadSessionMessages(id);
};

const loadSessionMessages = async (id) => {
    try {
        const res = await fetch(`/api/v1/data_query/sessions/${id}/messages`);
        if (!res.ok) throw new Error('加载消息失败');
        const data = await res.json();
        const items = Array.isArray(data.items) ? data.items : [];
        messages.value = items.map(m => ({
            _id: m.id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: m.role,
            content: m.content || '',
            sql_query: m.sql_query || null,
            chart_config: m.chart_config || null
        }));
        await nextTick();
        scrollToBottom();
    } catch (e) {
        toast({ title: '加载失败', description: e.message, variant: 'destructive' });
    }
};

const sendMessage = async () => {
    if (!input.value.trim() || isLoading.value) return;
    const userMsg = input.value;
    input.value = '';
    
    messages.value.push({ _id: `msg_${Date.now()}_user`, role: 'user', content: userMsg });
    isLoading.value = true;
    scrollToBottom();
    
    // Add placeholder
    messages.value.push({ 
        _id: `msg_${Date.now()}_assistant`, 
        role: 'assistant', 
        content: '',
        steps: [],
        currentStep: 0
    });
    const assistantMsg = messages.value[messages.value.length - 1];

    try {
        if (!activeSessionId.value) {
            // Auto create session
            try {
                const title = userMsg.slice(0, 20);
                const resCreate = await fetch('/api/v1/data_query/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, user_id: 'default_user' })
                });
                if (resCreate.ok) {
                    const created = await resCreate.json();
                    if (created && created.id) {
                        sessions.value.unshift(created);
                        activeSessionId.value = created.id;
                    }
                }
            } catch (_) {}
        }
        
        currentController.value = new AbortController();
        const response = await fetch('/api/v1/data_query/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userMsg, session_id: activeSessionId.value || null }),
            signal: currentController.value.signal
        });
        
        if (!response.ok) throw new Error(response.statusText);
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        isStreaming.value = true;
        
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const stepData = JSON.parse(line);
                     if (stepData.step && stepData.content) {
                        stepData.timestamp = Date.now();
                        assistantMsg.steps.push(stepData);
                        assistantMsg.currentStep = stepData.step;
                        
                        if (['data', 'chart', 'error'].includes(stepData.type)) {
                             assistantMsg.content += stepData.content;
                        }
                        if (stepData.type === 'sql') {
                            assistantMsg.sql_query = stepData.content.replace(/```sql|```/g, '').trim();
                        }
                    }
                } catch (e) {
                    console.warn('Failed to parse step', e);
                }
            }
            scrollToBottom();
        }
    } catch (e) {
        if (!assistantMsg.content) assistantMsg.content = 'Error: ' + e.message;
        else assistantMsg.content += '\n\n[System Error]: ' + e.message;
    } finally {
        isLoading.value = false;
        isStreaming.value = false;
        currentController.value = null;
        scrollToBottom();
    }
};

const scrollToBottom = () => {
    nextTick(() => {
        if (messagesContainer.value) {
            const viewport = messagesContainer.value.$el?.querySelector('[data-radix-scroll-area-viewport]');
            if (viewport) viewport.scrollTop = viewport.scrollHeight;
        }
    });
};

const getMessageText = (content) => content.replace(/::: echarts[\s\S]*?:::/, '').trim();

const getMessageChart = (content) => {
    if (!content) return null;
    const match = content.match(/::: echarts([\s\S]*?):::/);
    if (match && match[1]) {
        try { return JSON.parse(match[1].trim()); } catch (e) { return null; }
    }
    return null;
};

const processChartOption = (raw) => raw; // Hook for chart optimization if needed

const copySql = (sql) => {
    navigator.clipboard.writeText(sql);
    toast({ title: '已复制', description: 'SQL 已复制到剪贴板' });
};

const renderMarkdown = (text) => {
    if (!text) return '';
    // Basic markdown processing, can be enhanced
    return marked.parse(text);
};

onMounted(() => {
    fetchConfig();
    fetchSessions();
});
</script>

<style scoped>
.markdown-body :deep(table) {
    @apply w-full border-collapse border border-border rounded-md overflow-hidden text-sm my-4;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
    @apply border border-border p-2 px-3;
}
.markdown-body :deep(th) {
    @apply bg-muted font-medium text-left text-muted-foreground;
}
.markdown-body :deep(tr:hover) {
    @apply bg-muted/50;
}
</style>
