<template>
  <DynamicGridBackground 
    class="h-full overflow-hidden relative bg-background"
    :grid-size="30"
    :grid-color="isDark ? '#333' : '#e5e7eb'"
    :blob-count="3"
    :blob-colors="blobColors"
    :animation-speed="20"
    :show-grid="!useTaskUI"
  >
    <div v-if="useTaskUI" class="h-full flex flex-col">
      <!-- Header -->
      <div class="flex-none px-4 py-3 border-b bg-background/80 backdrop-blur-md z-30 flex justify-between items-center supports-[backdrop-filter]:bg-background/60">
          <div class="flex items-center gap-4 min-w-0">
              <div class="relative w-9 h-9 flex items-center justify-center shrink-0">
                  <!-- Custom Progress Ring -->
                  <div class="absolute inset-0 rounded-full border-2 border-muted"></div>
                  <svg class="absolute inset-0 w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
                    <circle
                      cx="18"
                      cy="18"
                      r="16"
                      fill="none"
                      class="stroke-primary transition-all duration-500 ease-in-out"
                      stroke-width="2"
                      stroke-dasharray="100"
                      :stroke-dashoffset="100 - (workflowStore.progress || 0)"
                    />
                  </svg>
                  
                  <div class="absolute inset-0 m-auto w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm overflow-hidden">
                      <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-full h-full object-cover" alt="Agent" />
                      <BaseIcon v-else icon="mdi:file-document-outline" class="text-white" :size="14" />
                  </div>
              </div>

              <div class="min-w-0">
                  <h2 class="font-semibold text-sm leading-tight truncate text-foreground">
                      {{ currentSession?.title || '新任务' }}
                  </h2>
                  <div class="flex items-center gap-1 text-xs text-muted-foreground truncate" v-if="currentAgent">
                      <span>当前智能体:</span>
                      <span class="font-medium text-primary truncate">{{ currentAgent.name }}</span>
                  </div>
              </div>
          </div>

          <div class="flex items-center gap-1 shrink-0">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground" @click="openTaskLogs">
                      <BaseIcon icon="lucide:code" :size="16" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>查看系统日志</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground" @click="toggleLeftPane">
                      <BaseIcon v-if="!isLeftCollapsed" icon="lucide:panel-left-close" :size="16" />
                      <BaseIcon v-else icon="lucide:panel-left-open" :size="16" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>折叠/展开聊天区</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground" @click="toggleRightPane">
                      <BaseIcon v-if="!isRightCollapsed" icon="lucide:panel-right-close" :size="16" />
                      <BaseIcon v-else icon="lucide:panel-right-open" :size="16" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>折叠/展开任务区</TooltipContent>
                </Tooltip>
              </TooltipProvider>
          </div>
      </div>

      <div ref="splitContainerRef" class="flex-1 min-h-0 flex flex-col xl:flex-row bg-transparent overflow-hidden">
        <div v-show="!isLeftCollapsed" class="flex flex-col min-w-0 flex-1 bg-background/50 backdrop-blur-sm relative transition-all duration-150" :style="leftPaneStyle">
        <!-- Messages List -->
        <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center px-4 py-8 overflow-y-auto relative custom-scrollbar">
             <div class="w-full max-w-2xl flex flex-col items-center gap-8">
                <div class="flex flex-col items-center gap-4">
                    <div class="w-24 h-24 flex items-center justify-center mb-2 bg-muted/20 rounded-full p-4">
                        <img src="/bot.svg" alt="Robot" class="w-full h-full object-contain opacity-90" />
                    </div>
                    <h1 class="text-3xl font-bold tracking-tight text-foreground text-center">让我们创造点厉害的东西！</h1>
                </div>
                
                <!-- Centered Input Area -->
                <div class="w-full relative flex flex-col gap-2 border bg-background/50 backdrop-blur focus-within:ring-2 focus-within:ring-ring focus-within:border-primary transition-all shadow-lg rounded-xl p-3">
                    <!-- Attachments Preview -->
                    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-1 pt-1">
                        <Badge 
                          v-for="(att, idx) in selectedAttachments" 
                          :key="idx" 
                          variant="secondary"
                          class="flex items-center gap-1 px-2 py-1"
                        >
                            <Paperclip class="w-3 h-3" />
                            <span class="max-w-[100px] truncate">{{ att.name }}</span>
                            <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive ml-1" @click="removeAttachment(idx)" />
                        </Badge>
                    </div>

                    <textarea 
                        ref="textareaRef"
                        v-model="input" 
                        @keydown="onInputKeydown"
                        rows="1"
                        :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm bg-transparent min-h-[40px] max-h-[200px] custom-scrollbar placeholder:text-muted-foreground"
                        :disabled="isLoading"
                        @input="adjustHeight"
                    ></textarea>

                    <div class="flex justify-between items-center pt-2">
                         <div class="flex items-center gap-2">
                             <TooltipProvider>
                               <Tooltip>
                                 <TooltipTrigger as-child>
                                   <Button variant="ghost" size="icon" class="h-8 w-8 rounded-full" @click="openAttachmentModal">
                                      <Paperclip class="w-4 h-4" />
                                   </Button>
                                 </TooltipTrigger>
                                 <TooltipContent>添加附件</TooltipContent>
                               </Tooltip>
                             </TooltipProvider>
                             
                             <Separator orientation="vertical" class="h-4" />
                             
                             <DropdownMenu>
                                <DropdownMenuTrigger as-child>
                                  <Button variant="ghost" size="sm" class="h-8 gap-2 px-2 font-normal text-muted-foreground hover:text-foreground">
                                    <MessageSquare v-if="mode === 'chat'" class="w-4 h-4 text-primary" />
                                    <Kanban v-else-if="mode === 'workflow'" class="w-4 h-4 text-primary" />
                                    <img v-else-if="mode === 'auto_task'" src="/openclaw.svg" class="w-4 h-4" />
                                    <span>
                                        {{ mode === 'chat' ? '对话模式' : (mode === 'workflow' ? '智能规划' : 'Openclaw') }}
                                    </span>
                                    <ChevronDown class="w-3 h-3 opacity-50" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="start">
                                  <DropdownMenuItem @click="handleModeChange('chat')">
                                    <MessageSquare class="w-4 h-4 mr-2" /> 对话模式
                                  </DropdownMenuItem>
                                  <DropdownMenuItem @click="handleModeChange('workflow')">
                                    <Kanban class="w-4 h-4 mr-2" /> 智能规划
                                  </DropdownMenuItem>
                                  <DropdownMenuItem @click="handleModeChange('auto_task')">
                                    <img src="/openclaw.svg" class="w-4 h-4 mr-2" /> Openclaw
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                             </DropdownMenu>

                             <template v-if="mode !== 'auto_task'">
                               <Separator orientation="vertical" class="h-4" />
                               <div class="flex items-center gap-2 cursor-pointer select-none px-2" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                  <Switch :checked="isNetworkSearchEnabled" class="pointer-events-none scale-75" />
                                  <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-primary' : 'text-muted-foreground'">联网搜索</span>
                               </div>
                             </template>
                         </div>
                         
                         <div class="flex items-center gap-3">
                             <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-muted/50 hover:bg-muted transition-colors cursor-pointer border border-transparent" @click="toggleAgentSelect">
                                <Avatar class="w-5 h-5">
                                  <AvatarImage v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" />
                                  <AvatarFallback>
                                    <img src="/tiga.svg" class="w-full h-full p-1" />
                                  </AvatarFallback>
                                </Avatar>
                                <Select 
                                    v-model="selectedAgentId" 
                                    @update:modelValue="handleAgentChange"
                                    :open="agentSelectOpen"
                                    @update:open="val => agentSelectOpen = val"
                                >
                                  <SelectTrigger class="w-[110px] h-6 border-0 bg-transparent p-0 text-xs focus:ring-0 shadow-none">
                                    <SelectValue placeholder="选择智能体" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</SelectItem>
                                  </SelectContent>
                                </Select>
                             </div>
                             
                             <Button 
                                @click="sendMessage" 
                                size="icon"
                                class="h-8 w-8 rounded-full shadow-md transition-all active:scale-95"
                                :variant="(input.trim() || isTaskRunning) ? 'default' : 'secondary'"
                                :disabled="(!input.trim() && !isTaskRunning) || isStopping"
                             >
                                <Loader2 v-if="isStopping" class="w-4 h-4 animate-spin" />
                                <Square v-else-if="isTaskRunning" class="w-3 h-3 fill-current" />
                                <ArrowUp v-else class="w-4 h-4" />
                             </Button>
                         </div>
                    </div>
                </div>

                <!-- Scripts Section -->
                <div v-if="userScripts.length > 0" class="flex flex-col gap-4 w-full animate-fade-in-up">
                    <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">快捷指令</span>
                    <ScrollArea class="w-full whitespace-nowrap pb-4">
                      <div class="flex w-max space-x-4 p-1">
                        <Card
                            v-for="s in userScripts" 
                            :key="s.id" 
                            class="w-[240px] h-[140px] flex flex-col justify-between p-5 cursor-pointer hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm"
                            @click="sendQuickMessage(s.content)"
                        >
                            <div class="absolute -right-8 -top-8 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors"></div>
                            <div class="flex flex-col gap-2 relative z-10">
                                <p class="text-xs text-muted-foreground group-hover:text-foreground line-clamp-3 leading-relaxed whitespace-normal transition-colors">
                                    {{ s.content }}
                                </p>
                            </div>
                            <div class="relative z-10 flex items-center justify-between pt-4 border-t border-border/50 group-hover:border-primary/20 transition-colors">
                                <span class="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">{{ s.title }}</span>
                            </div>
                        </Card>
                      </div>
                      <ScrollBar orientation="horizontal" />
                    </ScrollArea>
                </div>
             </div>
        </div>
        <MessageList 
            v-else 
            ref="messagesContainer"
            :messages="messages" 
            :current-agent="currentAgent" 
            :is-loading="isLoading"
            @locate-node="handleLocateNode"
            @show-doc-summary="handleDocSummary"
            @open-doc-space="handleOpenDocSpace"
        />

        <!-- Input Area (Fixed Bottom for Chat) -->
        <div v-if="messages.length > 0" class="flex-none w-full p-4 bg-background/80 backdrop-blur-sm z-30 border-t border-border shadow-sm">
            <div class="max-w-4xl mx-auto relative">
                <div class="relative flex flex-col gap-2 border bg-background focus-within:ring-2 focus-within:ring-ring focus-within:border-primary transition-all rounded-xl p-3 shadow-sm">
                    <!-- Attachments Preview -->
                    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-1 pt-1">
                        <Badge 
                          v-for="(att, idx) in selectedAttachments" 
                          :key="idx" 
                          variant="secondary"
                          class="flex items-center gap-1 px-2 py-1"
                        >
                            <Paperclip class="w-3 h-3" />
                            <span class="max-w-[100px] truncate">{{ att.name }}</span>
                            <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive ml-1" @click="removeAttachment(idx)" />
                        </Badge>
                    </div>

                    <textarea 
                        ref="textareaRef"
                        v-model="input" 
                        @keydown="onInputKeydown"
                        rows="1"
                        :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm bg-transparent min-h-[40px] max-h-[200px] custom-scrollbar placeholder:text-muted-foreground"
                        :disabled="isLoading"
                        @input="adjustHeight"
                    ></textarea>

                    <div class="flex justify-between items-center pt-2">
                         <div class="flex items-center gap-2 h-8">
                             <div v-if="mode !== 'auto_task'" class="flex items-center gap-2 cursor-pointer select-none h-full px-2" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                <Switch :checked="isNetworkSearchEnabled" class="pointer-events-none scale-75" />
                                <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-primary' : 'text-muted-foreground'">联网搜索</span>
                             </div>
                         </div>
                         <div class="flex items-center gap-4 h-8">
                             <Button 
                                @click="sendMessage" 
                                size="icon"
                                class="h-8 w-8 rounded-full shadow-md transition-all active:scale-95"
                                :variant="(input.trim() || isTaskRunning) ? 'default' : 'secondary'"
                                :disabled="(!input.trim() && !isTaskRunning) || isStopping"
                             >
                                <Loader2 v-if="isStopping" class="w-4 h-4 animate-spin" />
                                <Square v-else-if="isTaskRunning" class="w-3 h-3 fill-current" />
                                <ArrowUp v-else class="w-4 h-4" />
                             </Button>
                         </div>
                    </div>
                </div>
            </div>
        </div>
      </div>

      <div
        v-if="isDesktop && !isLeftCollapsed && !isRightCollapsed"
        class="hidden xl:flex w-1 shrink-0 items-center justify-center cursor-col-resize bg-transparent z-50 relative group hover:bg-primary/10 transition-colors"
        @mousedown="startResize"
      >
        <!-- Visual Line -->
        <div class="w-[1px] h-full bg-border group-hover:bg-primary group-hover:w-[2px] transition-all"></div>
      </div>

      <div v-show="!isRightCollapsed" class="w-full h-[420px] xl:h-auto xl:flex-1 xl:min-w-0 xl:w-auto flex-shrink-0 bg-muted/30 z-20 transition-all duration-150 flex flex-col overflow-hidden" :style="rightPaneStyle">
        <AutoTaskPanel 
            v-if="isAutoTaskMode" 
            @run-task="handleRunTask" 
            @close="isRightCollapsed = true"
        />
        <WorkspaceTabs
            v-else
            ref="workspaceTabsRef"
            :sessionId="currentSessionId || ''"
            :agentName="currentAgent?.name || ''"
            :isWorkflowMode="isWorkflowMode"
            :attachmentsCount="selectedAttachments.length"
        />
      </div>
    </div>
    </div>

    <!-- Standalone Chat UI (No Task/Workflow) -->
    <div v-else class="h-full flex flex-col bg-background overflow-hidden relative">
      <div class="flex-1 flex flex-col h-full relative min-w-0">
          <div v-if="messages.length > 0 && !embedded" class="px-4 py-3 border-b border-border flex justify-between items-center bg-background/80 backdrop-blur-sm z-10">
              <div class="flex items-center gap-4 group flex-1">
                  <div class="relative w-9 h-9 flex items-center justify-center">
                    <div class="absolute inset-0 rounded-full border-2 border-muted"></div>
                    <svg class="absolute inset-0 w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
                        <circle
                        cx="18"
                        cy="18"
                        r="16"
                        fill="none"
                        class="stroke-primary transition-all duration-500 ease-in-out"
                        stroke-width="2"
                        stroke-dasharray="100"
                        :stroke-dashoffset="100 - (workflowStore.progress || 0)"
                        />
                    </svg>
                      <div class="absolute inset-0 m-auto w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm overflow-hidden">
                          <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-full h-full object-cover" alt="Agent" />
                          <BaseIcon v-else icon="mdi:file-document-outline" class="text-white" :size="14" />
                      </div>
                  </div>
                  <div class="min-w-0">
                      <h2 class="font-semibold text-sm leading-tight truncate text-foreground">
                          {{ currentSession?.title || '新任务' }}
                      </h2>
                      <div class="flex items-center gap-1 text-xs text-muted-foreground truncate" v-if="currentAgent">
                          <span>当前智能体:</span>
                          <span class="font-medium text-primary truncate">{{ currentAgent.name }}</span>
                      </div>
                  </div>
              </div>
          </div>

          <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center px-4 py-8 overflow-y-auto relative custom-scrollbar">
               <div class="w-full max-w-2xl flex flex-col items-center gap-8">
                  <div class="flex flex-col items-center gap-4">
                      <div class="w-24 h-24 flex items-center justify-center mb-2 bg-muted/20 rounded-full p-4">
                          <img src="/bot.svg" alt="Robot" class="w-full h-full object-contain opacity-90" />
                      </div>
                      <h1 v-if="!embedded" class="text-3xl font-bold tracking-tight text-foreground text-center">让我们创造点厉害的东西！</h1>
                      <h1 v-else class="text-xl font-semibold text-foreground text-center">有什么可以帮您？</h1>
                  </div>
                  
                  <div class="w-full relative flex flex-col gap-2 border bg-background/50 backdrop-blur focus-within:ring-2 focus-within:ring-ring focus-within:border-primary transition-all rounded-xl p-3 shadow-lg">
                      <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-1 pt-1">
                        <Badge 
                          v-for="(att, idx) in selectedAttachments" 
                          :key="idx" 
                          variant="secondary"
                          class="flex items-center gap-1 px-2 py-1"
                        >
                            <Paperclip class="w-3 h-3" />
                            <span class="max-w-[100px] truncate">{{ att.name }}</span>
                            <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive ml-1" @click="removeAttachment(idx)" />
                        </Badge>
                      </div>

                      <textarea 
                          ref="textareaRef"
                          v-model="input" 
                          @keydown="onInputKeydown"
                          rows="1"
                          :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm bg-transparent min-h-[40px] max-h-[200px] custom-scrollbar placeholder:text-muted-foreground"
                        :disabled="isLoading"
                          @input="adjustHeight"
                      ></textarea>

                      <div class="flex justify-between items-center pt-2">
                           <div class="flex items-center gap-2 h-8">
                               <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger as-child>
                                    <Button variant="ghost" size="icon" class="h-8 w-8 rounded-full" @click="openAttachmentModal">
                                        <Paperclip class="w-4 h-4" />
                                    </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>添加附件</TooltipContent>
                                </Tooltip>
                               </TooltipProvider>

                               <Separator orientation="vertical" class="h-4" />
                               
                               <DropdownMenu v-if="!embedded">
                                <DropdownMenuTrigger as-child>
                                  <Button variant="ghost" size="sm" class="h-8 gap-2 px-2 font-normal text-muted-foreground hover:text-foreground">
                                    <MessageSquare v-if="mode === 'chat'" class="w-4 h-4 text-primary" />
                                    <Kanban v-else-if="mode === 'workflow'" class="w-4 h-4 text-primary" />
                                    <img v-else-if="mode === 'auto_task'" src="/openclaw.svg" class="w-4 h-4" />
                                    <span>
                                        {{ mode === 'chat' ? '对话模式' : (mode === 'workflow' ? '智能规划' : 'Openclaw') }}
                                    </span>
                                    <ChevronDown class="w-3 h-3 opacity-50" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="start">
                                  <DropdownMenuItem @click="handleModeChange('chat')">
                                    <MessageSquare class="w-4 h-4 mr-2" /> 对话模式
                                  </DropdownMenuItem>
                                  <DropdownMenuItem @click="handleModeChange('workflow')">
                                    <Kanban class="w-4 h-4 mr-2" /> 智能规划
                                  </DropdownMenuItem>
                                  <DropdownMenuItem @click="handleModeChange('auto_task')">
                                    <img src="/openclaw.svg" class="w-4 h-4 mr-2" /> Openclaw
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                               </DropdownMenu>

                               <template v-if="mode !== 'auto_task' && !embedded">
                                   <Separator orientation="vertical" class="h-4" />
                                   <div class="flex items-center gap-2 cursor-pointer select-none px-2" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                      <Switch :checked="isNetworkSearchEnabled" class="pointer-events-none scale-75" />
                                      <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-primary' : 'text-muted-foreground'">联网搜索</span>
                                   </div>
                               </template>
                           </div>
                           
                           <div class="flex items-center gap-3 h-8">
                               <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-muted/50 hover:bg-muted transition-colors cursor-pointer border border-transparent" @click="toggleAgentSelect">
                                  <Avatar class="w-5 h-5">
                                    <AvatarImage v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" />
                                    <AvatarFallback>
                                        <img src="/tiga.svg" class="w-full h-full p-1" />
                                    </AvatarFallback>
                                  </Avatar>
                                  <Select 
                                      v-model="selectedAgentId" 
                                      @update:modelValue="handleAgentChange"
                                      :open="agentSelectOpen"
                                      @update:open="val => agentSelectOpen = val"
                                  >
                                    <SelectTrigger class="w-[110px] h-6 border-0 bg-transparent p-0 text-xs focus:ring-0 shadow-none">
                                        <SelectValue placeholder="选择智能体" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</SelectItem>
                                    </SelectContent>
                                  </Select>
                               </div>

                               <Button 
                                  @click="sendMessage" 
                                  size="icon"
                                  class="h-8 w-8 rounded-full shadow-md transition-all active:scale-95"
                                  :variant="(input.trim() || isTaskRunning) ? 'default' : 'secondary'"
                                  :disabled="(!input.trim() && !isTaskRunning) || isStopping"
                               >
                                  <Loader2 v-if="isStopping" class="w-4 h-4 animate-spin" />
                                  <Square v-else-if="isTaskRunning" class="w-3 h-3 fill-current" />
                                  <ArrowUp v-else class="w-4 h-4" />
                               </Button>
                           </div>
                      </div>
                  </div>

                  <div v-if="userScripts.length > 0" class="flex flex-col gap-4 w-full animate-fade-in-up">
                      <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">快捷指令</span>
                      <ScrollArea class="w-full whitespace-nowrap pb-4">
                        <div class="flex w-max space-x-4 p-1">
                          <Card
                              v-for="s in userScripts" 
                              :key="s.id" 
                              class="w-[240px] h-[140px] flex flex-col justify-between p-5 cursor-pointer hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm"
                              @click="sendQuickMessage(s.content)"
                          >
                              <div class="absolute -right-8 -top-8 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors"></div>
                              <div class="flex flex-col gap-2 relative z-10">
                                  <p class="text-xs text-muted-foreground group-hover:text-foreground line-clamp-3 leading-relaxed whitespace-normal transition-colors">
                                      {{ s.content }}
                                  </p>
                              </div>
                              <div class="relative z-10 flex items-center justify-between pt-4 border-t border-border/50 group-hover:border-primary/20 transition-colors">
                                  <span class="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">{{ s.title }}</span>
                              </div>
                          </Card>
                        </div>
                        <ScrollBar orientation="horizontal" />
                      </ScrollArea>
                  </div>
               </div>
          </div>

          <MessageList 
              v-else 
              ref="messagesContainer"
              :messages="messages" 
              :current-agent="currentAgent" 
              :is-loading="isLoading"
              @locate-node="handleLocateNode"
              @show-doc-summary="handleDocSummary"
              @open-doc-space="handleOpenDocSpace"
          />

          <div v-if="messages.length > 0" class="flex-none w-full p-4 bg-background/80 backdrop-blur-sm z-30 border-t border-border shadow-sm">
              <div class="max-w-4xl mx-auto relative">
                  <div class="relative flex flex-col gap-2 border bg-background focus-within:ring-2 focus-within:ring-ring focus-within:border-primary transition-all rounded-xl p-3 shadow-sm">
                      <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-1 pt-1">
                        <Badge 
                          v-for="(att, idx) in selectedAttachments" 
                          :key="idx" 
                          variant="secondary"
                          class="flex items-center gap-1 px-2 py-1"
                        >
                            <Paperclip class="w-3 h-3" />
                            <span class="max-w-[100px] truncate">{{ att.name }}</span>
                            <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive ml-1" @click="removeAttachment(idx)" />
                        </Badge>
                      </div>

                      <textarea 
                          ref="textareaRef"
                          v-model="input" 
                          @keydown="onInputKeydown"
                          rows="1"
                          :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm bg-transparent min-h-[40px] max-h-[200px] custom-scrollbar placeholder:text-muted-foreground"
                        :disabled="isLoading"
                          @input="adjustHeight"
                      ></textarea>

                      <div class="flex justify-between items-center pt-2">
                           <div class="flex items-center gap-2 h-8">
                               <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger as-child>
                                    <Button variant="ghost" size="icon" class="h-8 w-8 rounded-full" @click="openAttachmentModal">
                                        <Paperclip class="w-4 h-4" />
                                    </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>添加附件</TooltipContent>
                                </Tooltip>
                               </TooltipProvider>

                               <Separator orientation="vertical" class="h-4" />
                               <div class="flex items-center gap-2 cursor-pointer select-none px-2" @click="toggleWorkflowMode" v-if="!embedded">
                                  <Switch :checked="isWorkflowMode" class="pointer-events-none scale-75" />
                                  <span class="text-xs font-medium" :class="isWorkflowMode ? 'text-primary' : 'text-muted-foreground'">任务模式</span>
                               </div>
                               
                               <template v-if="mode !== 'auto_task' && !embedded">
                                   <Separator orientation="vertical" class="h-4" />
                                   <div class="flex items-center gap-2 cursor-pointer select-none px-2" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                      <Switch :checked="isNetworkSearchEnabled" class="pointer-events-none scale-75" />
                                      <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-primary' : 'text-muted-foreground'">联网搜索</span>
                                   </div>
                               </template>
                           </div>

                           <div class="flex items-center gap-3 h-8">
                               <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-muted/50 hover:bg-muted transition-colors cursor-pointer border border-transparent" @click="toggleAgentSelect">
                                  <Avatar class="w-5 h-5">
                                    <AvatarImage v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" />
                                    <AvatarFallback>
                                        <img src="/tiga.svg" class="w-full h-full p-1" />
                                    </AvatarFallback>
                                  </Avatar>
                                  <Select 
                                      v-model="selectedAgentId" 
                                      @update:modelValue="handleAgentChange"
                                      :open="agentSelectOpen"
                                      @update:open="val => agentSelectOpen = val"
                                  >
                                    <SelectTrigger class="w-[110px] h-6 border-0 bg-transparent p-0 text-xs focus:ring-0 shadow-none">
                                        <SelectValue placeholder="选择智能体" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</SelectItem>
                                    </SelectContent>
                                  </Select>
                               </div>

                               <Button 
                                  @click="sendMessage" 
                                  size="icon"
                                  class="h-8 w-8 rounded-full shadow-md transition-all active:scale-95"
                                  :variant="(input.trim() || isTaskRunning) ? 'default' : 'secondary'"
                                  :disabled="(!input.trim() && !isTaskRunning) || isStopping"
                               >
                                  <Loader2 v-if="isStopping" class="w-4 h-4 animate-spin" />
                                  <Square v-else-if="isTaskRunning" class="w-3 h-3 fill-current" />
                                  <ArrowUp v-else class="w-4 h-4" />
                               </Button>
                           </div>
                      </div>
                  </div>
              </div>
          </div>
      </div>
    </div>

    <!-- Attachment Modal -->
    <Dialog v-model:open="attachmentModalVisible">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>选择附件</DialogTitle>
        </DialogHeader>
        
        <Tabs v-model="activeAttachmentTab" class="w-full">
            <TabsList class="grid w-full grid-cols-2">
                <TabsTrigger value="local">本地文件</TabsTrigger>
                <TabsTrigger value="knowledge">知识库文档</TabsTrigger>
            </TabsList>
            
            <TabsContent value="local" class="py-4">
                <div 
                    class="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer"
                    @click="$refs.fileInput.click()"
                    @drop.prevent="handleDrop"
                    @dragover.prevent
                >
                    <input type="file" ref="fileInput" class="hidden" multiple @change="handleFileChange" />
                    <div class="flex flex-col items-center gap-2 text-muted-foreground">
                        <Upload class="w-10 h-10 mb-2 text-muted-foreground/50" />
                        <p class="text-sm font-medium">点击或拖拽文件到此区域上传</p>
                        <p class="text-xs">支持 PDF, DOCX, PPTX, XLSX, TXT 格式，最大 50MB</p>
                    </div>
                </div>

                <div v-if="localFileList.length > 0" class="mt-4 max-h-40 overflow-y-auto space-y-2 custom-scrollbar pr-2">
                    <div v-for="file in localFileList" :key="file.uid" class="flex items-center justify-between p-2 bg-muted/30 rounded border border-border">
                        <div class="flex items-center gap-2 truncate">
                            <Paperclip class="w-4 h-4 text-muted-foreground" />
                            <span class="text-sm text-foreground truncate max-w-[300px]">{{ file.name }}</span>
                            <span class="text-xs text-muted-foreground">({{ (file.size / 1024).toFixed(1) }} KB)</span>
                        </div>
                        <Button variant="ghost" size="icon" class="h-6 w-6 text-muted-foreground hover:text-destructive" @click="removeLocalFile(file)">
                            <Trash2 class="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </TabsContent>
            
            <TabsContent value="knowledge" class="py-4">
                <div class="flex flex-col gap-4 h-[400px]">
                    <div class="flex gap-2">
                        <div class="relative flex-1">
                            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input v-model="knowledgeSearchKeyword" placeholder="搜索文档名称..." class="pl-9" />
                        </div>
                        <Button variant="outline" :disabled="knowledgeLoading" @click="fetchKnowledgeDocs">
                            <Loader2 v-if="knowledgeLoading" class="w-4 h-4 animate-spin mr-2" />
                            刷新
                        </Button>
                    </div>
                    
                    <div class="border rounded-md flex-1 overflow-hidden">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead class="w-[40px]"></TableHead>
                                    <TableHead>文档名称</TableHead>
                                    <TableHead>大小</TableHead>
                                    <TableHead class="text-right">修改时间</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <TableRow v-for="doc in filteredKnowledgeDocs" :key="doc.id">
                                    <TableCell>
                                        <input 
                                            type="checkbox" 
                                            :checked="selectedKnowledgeRowKeys.includes(doc.id)"
                                            @change="(e) => toggleKnowledgeSelection(doc.id, e.target.checked)"
                                            class="rounded border-gray-300 text-primary focus:ring-primary"
                                        />
                                    </TableCell>
                                    <TableCell class="font-medium">{{ doc.filename }}</TableCell>
                                    <TableCell>{{ (doc.file_size / 1024).toFixed(2) }} KB</TableCell>
                                    <TableCell class="text-right">{{ new Date(doc.updated_at).toLocaleDateString() }}</TableCell>
                                </TableRow>
                                <TableRow v-if="filteredKnowledgeDocs.length === 0">
                                    <TableCell colspan="4" class="h-24 text-center text-muted-foreground">
                                        暂无文档
                                    </TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </TabsContent>
        </Tabs>

        <DialogFooter>
            <Button variant="outline" @click="attachmentModalVisible = false">取消</Button>
            <Button @click="handleAttachmentOk">确认 ({{ localFileList.length + selectedKnowledgeRowKeys.length }})</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </DynamicGridBackground>
</template>

<script setup>
/**
 * @场景    多智能体问答入口，支持对话、智能规划与自动任务协同处理
 * @功能    提供会话管理、SSE流式消息、附件上传、模式切换与任务面板联动
 * @依赖    Vue3、Ant Design Vue、workflow.store、/api/v1/chat 与 /openclaw 接口
 * @备注    UI Refactored to shadcn/ui
 */
import { ref, nextTick, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { api } from '@/core/api/client';
import MessageList from './MessageList.vue';
import ReferencesTable from './ReferencesTable.vue';
import ReferencesCards from './ReferencesCards.vue';
import AutoTaskPanel from './AutoTaskPanel.vue';
import WorkspaceTabs from '@/features/workflow/components/WorkspaceTabs.vue';
import BaseIcon from '@/shared/components/atoms/BaseIcon';
import DynamicGridBackground from '@/shared/components/molecules/DynamicGridBackground.vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import { useTheme } from '@/composables/useTheme';
import { useToast } from '@/components/ui/toast/use-toast';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Separator } from '@/components/ui/separator';

// Icons
import { 
    Paperclip, 
    Trash2, 
    Upload, 
    Search, 
    ArrowUp, 
    Square, 
    Loader2, 
    Kanban, 
    MessageSquare, 
    ChevronDown, 
    Check 
} from 'lucide-vue-next';

const props = defineProps({
    sessionId: { type: String, default: null },
    embedded: { type: Boolean, default: false }
});
const emit = defineEmits(['refresh-sessions']);

const workflowStore = useWorkflowStore();
const { isLightMode } = useTheme();
const { toast } = useToast();
const isDark = computed(() => !isLightMode.value);
const blobColors = computed(() => isDark.value 
    ? ['rgba(99, 102, 241, 0.15)', 'rgba(59, 130, 246, 0.15)', 'rgba(168, 85, 247, 0.15)'] 
    : ['rgba(99, 102, 241, 0.12)', 'rgba(59, 130, 246, 0.12)', 'rgba(168, 85, 247, 0.12)']);

const mode = ref('chat'); // 'chat', 'workflow', 'auto_task'
const isWorkflowMode = computed(() => mode.value === 'workflow');
const isAutoTaskMode = computed(() => mode.value === 'auto_task');
const isNetworkSearchEnabled = ref(true); // Network search toggle
const useTaskUI = computed(() => isWorkflowMode.value || isAutoTaskMode.value || workflowStore.isRunning || (workflowStore.tasks?.length || 0) > 0);
const input = ref('');
const messages = ref([]);
const currentSession = ref(null);
const agents = ref([]);
const currentSessionId = ref(props.sessionId);
const selectedAgentId = ref('');
const agentSelectOpen = ref(false);
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);
const textareaRef = ref(null);
const abortController = ref(null);
const isStopping = ref(false);

const isTaskRunning = computed(() => isLoading.value || workflowStore.isRunning || isStreaming.value);

// Attachment Refs
const attachmentModalVisible = ref(false);
const activeAttachmentTab = ref('local');
const localFileList = ref([]);
const knowledgeDocs = ref([]);
const selectedKnowledgeRowKeys = ref([]);
const knowledgeSearchKeyword = ref('');
const knowledgeLoading = ref(false);
const selectedAttachments = ref([]);

const currentAgent = computed(() => agents.value.find(a => a.id === selectedAgentId.value));
const viewMode = ref('table');
const cardsLayout = ref('grid');

const splitContainerRef = ref(null);
const isLeftCollapsed = ref(false);
const isRightCollapsed = ref(false);
const isDesktop = ref(false);
const splitRatio = ref(0.6);
const workspaceTabsRef = ref(null);
const fileInput = ref(null);

const readSplitRatio = () => {
    try {
        const raw = localStorage.getItem('smartqa-split-ratio');
        const val = raw ? Number(raw) : NaN;
        if (!Number.isFinite(val)) return 0.6;
        return Math.min(0.8, Math.max(0.2, val));
    } catch {
        return 0.6;
    }
};

const writeSplitRatio = (val) => {
    try { localStorage.setItem('smartqa-split-ratio', String(val)); } catch {}
};

const updateIsDesktop = () => {
    if (typeof window === 'undefined') return;
    isDesktop.value = window.matchMedia('(min-width: 1280px)').matches;
};

const leftPaneStyle = computed(() => {
    if (!isDesktop.value) return {};
    if (isLeftCollapsed.value || isRightCollapsed.value) return {};
    const pct = Math.round(splitRatio.value * 10000) / 100;
    return { flex: `0 0 ${pct}%`, width: `${pct}%`, maxWidth: `${pct}%` };
});

const rightPaneStyle = computed(() => {
    if (!isDesktop.value) return {};
    if (isLeftCollapsed.value || isRightCollapsed.value) return {};
    const pct = Math.round((1 - splitRatio.value) * 10000) / 100;
    return { flex: `0 0 ${pct}%`, width: `${pct}%`, maxWidth: `${pct}%` };
});

const handleModeChange = async (newMode) => {
    mode.value = newMode;
    if (newMode === 'workflow' || newMode === 'auto_task') {
        isRightCollapsed.value = false;
        // Auto-disable network search in auto_task mode
        if (newMode === 'auto_task') {
            isNetworkSearchEnabled.value = false;
        }
    }
    
    // Update session mode if session exists
    if (currentSessionId.value) {
        try {
            await fetch(`/api/v1/chat/sessions/${currentSessionId.value}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: newMode })
            });
        } catch (e) {
            console.error("Failed to update session mode", e);
        }
    }
};

const handleRunTask = async (prompt) => {
    // Switch to a capable agent if current one is knowledge-only
    const currentAgentName = currentAgent.value?.name || '';
    if (currentAgentName.includes('知识') || currentAgentName.includes('查询')) {
        // Find 'General' agent explicitly, ignoring user preference
        const generalAgent = agents.value.find(a => a.name && (a.name === '通用' || a.name.includes('通用')));
        // Fallback: any agent that isn't the current one
        const targetAgent = generalAgent || agents.value.find(a => a.id !== selectedAgentId.value);
        
        if (targetAgent && targetAgent.id !== selectedAgentId.value) {
            selectedAgentId.value = targetAgent.id;
            
            // Force update session agent if session exists
            if (currentSessionId.value) {
                 try {
                    await fetch(`/api/v1/chat/sessions/${currentSessionId.value}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ agent_id: targetAgent.id })
                    });
                    if (currentSession.value) currentSession.value.agent_id = targetAgent.id;
                    toast({ description: `已切换至"${targetAgent.name}"以执行任务` });
                } catch (e) {
                    console.error("Failed to force update session agent", e);
                }
            } else {
                 toast({ description: `已切换至"${targetAgent.name}"以执行任务` });
            }
        }
    }

    input.value = prompt;
    nextTick(() => {
        sendMessage({ enableSearch: false });
    });
};

const toggleLeftPane = () => {
    if (isLeftCollapsed.value) {
        isLeftCollapsed.value = false;
        return;
    }
    if (isRightCollapsed.value) isRightCollapsed.value = false;
    isLeftCollapsed.value = true;
};

const toggleRightPane = () => {
    if (isRightCollapsed.value) {
        isRightCollapsed.value = false;
        return;
    }
    if (isLeftCollapsed.value) isLeftCollapsed.value = false;
    isRightCollapsed.value = true;
};

let isResizing = false;
let resizeStartX = 0;
let resizeStartRatio = 0.6;

const startResize = (e) => {
    if (!isDesktop.value || isLeftCollapsed.value || isRightCollapsed.value) return;
    const el = splitContainerRef.value;
    if (!el) return;
    e.preventDefault();
    isResizing = true;
    resizeStartX = e.clientX;
    resizeStartRatio = splitRatio.value;
    window.addEventListener('mousemove', onResizeMove);
    window.addEventListener('mouseup', stopResize);
};

const onResizeMove = (e) => {
    if (!isResizing) return;
    const el = splitContainerRef.value;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const delta = e.clientX - resizeStartX;
    const next = resizeStartRatio + (delta / rect.width);
    splitRatio.value = Math.min(0.8, Math.max(0.2, next));
};

const stopResize = () => {
    if (!isResizing) return;
    isResizing = false;
    window.removeEventListener('mousemove', onResizeMove);
    window.removeEventListener('mouseup', stopResize);
    writeSplitRatio(splitRatio.value);
};

const getPopupContainerForSelect = () => {
    return document.body;
};

const openTaskLogs = () => {
    if (isAutoTaskMode.value) {
        toast({ description: 'Openclaw模式下的日志请直接在对话流中查看工具调用详情' });
    } else {
        workspaceTabsRef.value?.openTaskLogs?.();
    }
};

const getDefaultAgentId = (list) => {
    let saved = '';
    try { saved = localStorage.getItem('defaultAgentId') || ''; } catch {}
    if (saved && list.some(a => a.id === saved)) return saved;
    const generic = list.find(a => a.name && (a.name === '通用' || a.name.includes('通用')));
    return generic ? generic.id : (list.length ? list[0].id : '');
};

onMounted(() => {
    try {
        const saved = localStorage.getItem('isNetworkSearchEnabled');
        if (saved !== null) {
            isNetworkSearchEnabled.value = saved === 'true';
        }
    } catch (e) {}

    splitRatio.value = readSplitRatio();
    updateIsDesktop();
    window.addEventListener('resize', updateIsDesktop);
    fetchAgents();
    if (currentSessionId.value) {
        fetchSessionDetails(currentSessionId.value);
    }
    fetchUserScripts(selectedAgentId.value);
    nextTick(() => {
        const ta = document.querySelector('textarea');
        if (ta) ta.focus();
    });
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', updateIsDesktop);
    stopResize();
});

watch(() => props.sessionId, (newId) => {
    currentSessionId.value = newId;
    mode.value = 'chat';
    isRightCollapsed.value = true;
    workflowStore.resetWorkflow();
    
    if (newId) {
        fetchSessionDetails(newId);
    } else {
        currentSession.value = null;
        messages.value = [];
        selectedAttachments.value = [];
        input.value = '';
    }
});


watch(() => workflowStore.currentStep, (newStep, oldStep) => {
    if (newStep === 'plan' && oldStep !== 'plan') {
        messages.value.push({ role: 'assistant', content: '## 任务规划' });
        scrollToBottom();
    } else if (newStep === 'execute' && oldStep !== 'execute') {
        messages.value.push({ role: 'assistant', content: '## 智能执行' });
        scrollToBottom();
    }
});

const userScripts = ref([]);
const userScriptsLoading = ref(false);
const userScriptsError = ref('');
const fetchUserScripts = async (aid) => {
    userScriptsError.value = '';
    userScriptsLoading.value = true;
    if (!aid) { userScripts.value = []; userScriptsLoading.value = false; return; }
    try {
        const res = await fetch(`/api/v1/user_scripts?agent_id=${aid}`);
        if (res.ok) {
            userScripts.value = await res.json();
        } else {
            userScriptsError.value = '请求失败';
            userScripts.value = [];
        }
    } catch (e) {
        userScriptsError.value = '加载失败';
        userScripts.value = [];
    } finally {
        userScriptsLoading.value = false;
    }
};

watch(selectedAgentId, (nv) => {
    fetchUserScripts(nv);
    try { if (nv) localStorage.setItem('defaultAgentId', nv); } catch {}
});

watch(isNetworkSearchEnabled, (val) => {
    try { localStorage.setItem('isNetworkSearchEnabled', String(val)); } catch {}
});

const adjustHeight = (e) => {
    const el = e?.target || textareaRef.value;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.max(el.scrollHeight, 36) + 'px';
};

watch(input, () => {
    nextTick(() => adjustHeight());
});

const onInputKeydown = (e) => {
    if (e.key === 'Enter') {
        if (e.shiftKey) return;
        e.preventDefault();
        sendMessage();
    }
};

const sendQuickMessage = (text) => {
    input.value = text;
    nextTick(() => {
        const ta = document.querySelector('textarea');
        if (ta) {
            ta.focus();
            ta.style.height = 'auto';
            ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
        }
    });
};

// Attachment Methods
const openAttachmentModal = () => {
    attachmentModalVisible.value = true;
    if (activeAttachmentTab.value === 'knowledge') {
        fetchKnowledgeDocs();
    }
};

const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => handleLocalUpload(file));
    // reset input
    if (fileInput.value) fileInput.value.value = '';
};

const handleDrop = (e) => {
    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => handleLocalUpload(file));
};

const handleLocalUpload = (file) => {
    const isLt50M = file.size / 1024 / 1024 < 50;
    if (!isLt50M) { toast({ description: '文件大小不能超过 50MB!', variant: 'destructive' }); return false; }
    const acceptedTypes = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt'];
    const fileExt = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!acceptedTypes.includes(fileExt)) { toast({ description: '不支持的文件类型!', variant: 'destructive' }); return false; }
    localFileList.value = [...localFileList.value, file];
    return false;
};
const removeLocalFile = (file) => {
    const index = localFileList.value.indexOf(file);
    const newFileList = localFileList.value.slice();
    newFileList.splice(index, 1);
    localFileList.value = newFileList;
};
const fetchKnowledgeDocs = async () => {
    knowledgeLoading.value = true;
    try {
        const res = await fetch('/api/v1/knowledge/list');
        if (res.ok) {
            let docs = await res.json();
            if (currentAgent.value?.knowledge_config?.document_ids?.length > 0) {
                docs = docs.filter(d => currentAgent.value.knowledge_config.document_ids.includes(d.id));
            }
            knowledgeDocs.value = docs;
        } else { toast({ description: '获取知识库文档失败', variant: 'destructive' }); }
    } catch (e) { console.error(e); toast({ description: '获取知识库文档出错', variant: 'destructive' }); } finally { knowledgeLoading.value = false; }
};
const filteredKnowledgeDocs = computed(() => {
    if (!knowledgeSearchKeyword.value) return knowledgeDocs.value;
    return knowledgeDocs.value.filter(d => d.filename.toLowerCase().includes(knowledgeSearchKeyword.value.toLowerCase()));
});

const toggleKnowledgeSelection = (id, checked) => {
    if (checked) {
        if (!selectedKnowledgeRowKeys.value.includes(id)) selectedKnowledgeRowKeys.value.push(id);
    } else {
        selectedKnowledgeRowKeys.value = selectedKnowledgeRowKeys.value.filter(k => k !== id);
    }
};

const handleAttachmentOk = () => {
    const localAtts = localFileList.value.map(f => ({ type: 'local', name: f.name, size: f.size, file: f }));
    const knowledgeAtts = knowledgeDocs.value
        .filter(d => selectedKnowledgeRowKeys.value.includes(d.id))
        .map(d => ({ type: 'knowledge', name: d.filename, size: d.file_size, id: d.id, file: null }));
    selectedAttachments.value = [...localAtts, ...knowledgeAtts];
    attachmentModalVisible.value = false;
    toast({ description: `已选择 ${selectedAttachments.value.length} 个附件` });
};
const removeAttachment = (index) => { selectedAttachments.value.splice(index, 1); };

// API Helpers
const fetchAgents = async () => {
    try {
        const res = await fetch('/api/v1/agents/');
        if (res.ok) {
            const data = await res.json();
            agents.value = data;
            if (!selectedAgentId.value && data.length > 0) {
                const did = getDefaultAgentId(data);
                selectedAgentId.value = did;
                fetchUserScripts(did);
            }
        }
    } catch (e) { console.error("Failed to fetch agents", e); }
};

const fetchSessionDetails = async (id) => {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${id}`);
        if (res.ok) {
            const data = await res.json();
            currentSession.value = data;
            selectedAgentId.value = data.agent_id || '';
            messages.value = data.messages || [];
            
            // Set mode from session
            if (data.mode) {
                mode.value = data.mode;
                if (mode.value === 'auto_task' || mode.value === 'workflow') {
                    isRightCollapsed.value = false;
                }
            } else {
                mode.value = 'chat';
            }
            
            // Initialize workflow state (prefer backend state, fallback to local storage)
            workflowStore.initWorkflow(id, data.workflow_state);
            
            scrollToBottom();
            if (!selectedAgentId.value && agents.value.length > 0) {
                selectedAgentId.value = getDefaultAgentId(agents.value);
            }
            nextTick(() => {
                messages.value.forEach((msg, idx) => {
                    if (msg.role === 'assistant' && isAmisJSON(msg.content)) renderAmis(idx, msg.content);
                });
            });
        }
    } catch (e) { console.error("Failed to fetch session details", e); }
};

const handleAgentChange = async (val) => {
    // val might be event or value depending on component
    // With shadcn Select, it's value
    const newValue = val;
    selectedAgentId.value = newValue;

    if (messages.value.length === 0 && currentSessionId.value) {
        try {
            const res = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: newValue || null })
            });
            if (res.ok && currentSession.value) currentSession.value.agent_id = newValue;
        } catch (e) { console.error("Failed to update session agent", e); }
    }
};

const sendMessage = async (options = {}) => {
    if (isTaskRunning.value) {
        // Handle stop action
        isStopping.value = true;
        try {
            if (workflowStore.isRunning) {
                workflowStore.stopWorkflow();
            }
            if (abortController.value) {
                abortController.value.abort();
                abortController.value = null;
            }
        } finally {
            // Delay to show loading state if needed
            setTimeout(() => {
                isStopping.value = false;
                isLoading.value = false;
                isStreaming.value = false;
            }, 300);
        }
        return;
    }

    if (!input.value.trim() || isLoading.value) return;
    isLoading.value = true;
    abortController.value = new AbortController();
    
    // Upload attachments
    let attachmentIds = [];
    if (selectedAttachments.value.length > 0) {
        const localFiles = selectedAttachments.value.filter(a => a.type === 'local');
        const knowledgeFiles = selectedAttachments.value.filter(a => a.type === 'knowledge');
        knowledgeFiles.forEach(att => attachmentIds.push(att.id));
        
        for (const att of localFiles) {
            const formData = new FormData();
            formData.append('file', att.file);
            try {
            const res = await fetch('/api/v1/knowledge/upload', { 
                method: 'POST', 
                body: formData,
                signal: abortController.value.signal 
            });
            if (res.ok) {
                const doc = await res.json();
                attachmentIds.push(doc.id);
            } else { toast({ description: `附件上传失败: ${att.name}`, variant: 'destructive' }); }
        } catch (e) {
            if (e.name === 'AbortError') return;
            toast({ description: `附件上传出错: ${att.name}`, variant: 'destructive' });
        }
    }
}
    
    const userMsg = input.value;
    input.value = '';
    selectedAttachments.value = [];
    
    if (textareaRef.value) {
        textareaRef.value.style.height = 'auto';
        textareaRef.value.style.height = '36px';
    }

    messages.value.push({ role: 'user', content: userMsg, timestamp: new Date().toISOString(), status: 'sending' });
    isStreaming.value = false;
    scrollToBottom();
    
    // Create session if needed
    if (!currentSessionId.value) {
        try {
            const res = await fetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                title: (userMsg && userMsg.slice(0, 20)) || '新对话',
                agent_id: selectedAgentId.value || null,
                mode: mode.value
            }),
            signal: abortController.value.signal
        });
        if (res.ok) {
            const newSession = await res.json();
            emit('refresh-sessions');
            currentSessionId.value = newSession.id;
            currentSession.value = newSession;
        } else { throw new Error("Failed to create session"); }
    } catch (e) {
        if (e.name === 'AbortError') return;
        console.error(e);
            messages.value[messages.value.length - 1].status = 'error'; // Update status
            messages.value.push({ role: 'assistant', content: "Error: 会话创建失败", timestamp: new Date().toISOString() });
            isLoading.value = false;
            return;
        }
    }
    
    // Workflow Mode
    if (isWorkflowMode.value) {
        workflowStore.initWorkflow(currentSessionId.value);
        workflowStore.runWorkflow(userMsg, selectedAgentId.value, attachmentIds);
        // Add a system-like message to indicate task start
        messages.value.push({ 
            role: 'assistant', 
            content: '已启动任务规划模式。请在右侧面板查看任务拆解与执行进度。',
            isSystem: true,
            timestamp: new Date().toISOString()
        });
        isLoading.value = false;
        return;
    }

    // Auto Task Mode
    if (isAutoTaskMode.value) {
        try {
            const res = await api.post('/openclaw/create_task', { prompt: userMsg });
            
            if (res.data && res.data.status === 'SKIPPED') {
                 const chatResponse = res.data.chat_response || res.data.message || '收到，但我不知道该说什么。';
                 messages.value.push({ 
                    role: 'assistant', 
                    content: chatResponse,
                    timestamp: new Date().toISOString()
                });
            } else {
                messages.value.push({ 
                    role: 'assistant', 
                    content: '任务已创建成功！正在后台执行中，请在右侧面板查看实时状态。',
                    timestamp: new Date().toISOString()
                });
                // Trigger refresh in AutoTaskPanel via event bus or store if needed
                // But for now, user can manually refresh or wait for polling
                isRightCollapsed.value = false; // Auto open right pane
            }
        } catch (e) {
            console.error(e);
            let errorMsg = '系统错误：无法连接到任务服务。';
            if (e.response && e.response.data && e.response.data.detail) {
                 errorMsg = `创建任务失败: ${e.response.data.detail}`;
            }
            messages.value.push({ 
                role: 'assistant', 
                content: errorMsg,
                timestamp: new Date().toISOString()
            });
        } finally {
            isLoading.value = false;
        }
        return;
    }

    // Chat Mode
    try {
        const payload = { 
            message: userMsg, 
            attachments: attachmentIds,
            enable_search: options.enableSearch !== undefined ? options.enableSearch : isNetworkSearchEnabled.value 
        };
        const response = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: abortController.value.signal
        });
        
        if (!response.ok) throw new Error(response.statusText);
        
        // Update user message status to sent
        const userMsgIdx = messages.value.findIndex(m => m.content === userMsg && m.role === 'user');
        if (userMsgIdx !== -1) messages.value[userMsgIdx].status = 'sent';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        messages.value.push({ role: 'assistant', content: '', reasoning: '', timestamp: new Date().toISOString() });
        const assistantMsg = messages.value[messages.value.length - 1];
        const assistantMsgIndex = messages.value.length - 1;
        isStreaming.value = true;
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            // Process SSE events (separated by double newline)
            const parts = buffer.split('\n\n');
            buffer = parts.pop() || ''; // Keep the last partial chunk
            
            for (const part of parts) {
                const lines = part.split('\n');
                let eventType = 'message';
                let data = '';
                
                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        eventType = line.substring(7).trim();
                    } else if (line.startsWith('data: ')) {
                        data = line.substring(6);
                    }
                }
                
                if (data) {
                    try {
                        const parsedData = JSON.parse(data);
                        
                        switch (eventType) {
                            case 'meta':
                                if (parsedData && parsedData.msg_type) {
                                    assistantMsg.type = parsedData.msg_type;
                                }
                                break;
                            case 'think':
                                assistantMsg.reasoning = (assistantMsg.reasoning || '') + normalizeThink(parsedData);
                                break;
                            case 'text':
                                {
                                    let textChunk = parsedData;
                                    if (typeof textChunk !== 'string') {
                                        textChunk = normalizeThink(textChunk);
                                    }
                                    assistantMsg.content = (assistantMsg.content || '') + textChunk;
                                }
                                break;
                            case 'chart':
                                // Append chart block to content
                                const chartBlock = `\n::: echarts\n${JSON.stringify(parsedData, null, 2)}\n:::\n`;
                                assistantMsg.content = (assistantMsg.content || '') + chartBlock;
                                break;
                            case 'sources':
                                assistantMsg.sources = parsedData;
                                break;
                            case 'file':
                                // Append file card block
                                const fileBlock = `\n::: file\n${JSON.stringify(parsedData)}\n:::\n`;
                                assistantMsg.content = (assistantMsg.content || '') + fileBlock;
                                break;
                            case 'error':
                                assistantMsg.content += `\n**System Error**: ${parsedData}`;
                                break;
                            case 'done':
                                // Stream finished signal
                                break;
                        }
                    } catch (e) {
                        console.warn('Failed to parse SSE event data', e);
                    }
                }
            }
            scrollToBottom();
        }
        if (isAmisJSON(assistantMsg.content)) nextTick(() => renderAmis(assistantMsgIndex, assistantMsg.content));
    } catch (e) {
        if (e.name === 'AbortError') {
            messages.value.push({ role: 'assistant', content: "[任务已停止]", timestamp: new Date().toISOString() });
        } else {
            console.error(e);
            messages.value.push({ role: 'assistant', content: "Error: " + e.message });
        }
    } finally {
        isLoading.value = false;
        isStreaming.value = false;
        scrollToBottom();
    }
};

const scrollToBottom = () => {
    nextTick(() => {
        if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    });
};

const normalizeThink = (data) => {
    if (data == null) return '';
    if (typeof data === 'string') return data;

    const safeString = (val) => {
        if (typeof val === 'string') return val;
        if (typeof val === 'object' && val !== null) {
            try { return JSON.stringify(val, null, 2); } catch { return String(val); }
        }
        return String(val);
    };

    if (Array.isArray(data)) {
        return data.map(item => {
            if (typeof item === 'string') return item;
            if (item && typeof item === 'object') {
                if (item.message || item.text) return safeString(item.message || item.text);
                if (item.step || item.status || item.description) {
                    const parts = [item.step, item.status, item.description].filter(Boolean);
                    return parts.join(' ');
                }
                return safeString(item);
            }
            return safeString(item);
        }).join('\n');
    }
    if (typeof data === 'object') {
        if (data.message || data.text) return safeString(data.message || data.text);
        if (data.steps && Array.isArray(data.steps)) {
            return data.steps.map(s => s.description || s.title || s.status || safeString(s)).join('\n');
        }
        return safeString(data);
    }
    return safeString(data);
};

const isAmisJSON = (text) => {
    if (!text || !text.trim().startsWith('```json')) return false;
    return text.includes('"type": "page"') || text.includes('"type": "chart"');
};

const renderAmis = (index, content) => {
    const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
    if (jsonMatch && jsonMatch[1]) {
        try {
            const schema = JSON.parse(jsonMatch[1]);
            const container = document.getElementById('amis-' + index);
            if (container && window.amis) window.amis.embed(container, schema);
        } catch (e) { console.error("Amis render error", e); }
    }
};

const toggleAgentSelect = (e) => {
    // handled by Select v-model:open
};

const handleLocateNode = (item) => {
    if (isRightCollapsed.value) {
        isRightCollapsed.value = false;
    }
    const nid = item.nodeId || item.title; 
    workspaceTabsRef.value?.locateNode?.(nid, item.docId);
};

const handleDocSummary = (item) => {
    console.log("View doc summary:", item);
};

const handleOpenDocSpace = (docId) => {
    if (isRightCollapsed.value) {
        isRightCollapsed.value = false;
    }
    workspaceTabsRef.value?.openDocSpace?.(docId);
};

const toggleWorkflowMode = () => {
    handleModeChange(isWorkflowMode.value ? 'chat' : 'workflow');
};
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { height: 6px; width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: transparent; border-radius: 10px; }
.custom-scrollbar:hover::-webkit-scrollbar-thumb { background: hsl(var(--muted)); }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: hsl(var(--muted-foreground)); }

.markdown-body { font-size: 13px; line-height: 1.7; color: hsl(var(--foreground)); }

.markdown-body p { margin-bottom: 0.75em; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body strong { font-weight: 600; color: hsl(var(--foreground)); }
.markdown-body em { font-style: italic; }
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 { font-weight: 600; color: hsl(var(--foreground)); margin-top: 1.5em; margin-bottom: 0.5em; line-height: 1.3; }
.markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid hsl(var(--border)); padding-bottom: 0.3em; }

.markdown-body pre { background: hsl(var(--muted)); padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 1em; border: 1px solid hsl(var(--border)); }
.markdown-body code { font-family: monospace; background: hsl(var(--muted)); padding: 2px 5px; border-radius: 4px; font-size: 0.9em; }

:deep(.entity-citation) { color: hsl(var(--primary)); background-color: hsl(var(--primary) / 0.1); padding: 0px 4px; border-radius: 4px; border-bottom: 1px dashed hsl(var(--primary)); cursor: pointer; font-weight: 500; transition: all 0.2s; }

:deep(.chunk-citation) { color: hsl(var(--primary)); font-weight: bold; cursor: help; margin-left: 2px; padding: 0 2px; }
</style>