<template>
  <div class="h-full w-full flex flex-col p-0 gap-0 overflow-hidden bg-background transition-all duration-200">
      
      <!-- Header Area (Always visible) -->
      <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">智能团队</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-xs text-muted-foreground m-0">
            集中管理您的智能代理团队，监控与配置多智能体协作模式。
          </p>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 overflow-hidden relative bg-card/50">

        <!-- List View (Always rendered) -->
        <div class="h-full flex flex-col">
          <!-- Search & Filter Bar -->
          <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
             <!-- Left: Empty placeholder to balance flex layout -->
             <div class="hidden md:block w-full md:w-64"></div>
             
             <!-- Center: View Tabs -->
             <div class="flex items-center justify-center flex-1">
               <Tabs v-model="currentTab" class="w-[200px]" @update:modelValue="fetchTeams">
                 <TabsList class="grid w-full grid-cols-2 h-9 bg-muted/80 p-1 rounded-lg border border-border/50 items-center">
                   <TabsTrigger value="instances" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">自定义</TabsTrigger>
                   <TabsTrigger value="templates" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">模板</TabsTrigger>
                 </TabsList>
               </Tabs>
             </div>

             <!-- Right: Actions -->
             <div class="flex items-center gap-3 w-full md:w-auto justify-end">
                 <div class="relative w-full md:w-64 group">
                    <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    <Input v-model="teamSearchQuery" placeholder="搜索团队名称或描述..." class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50" />
                 </div>

                 <div class="h-4 w-px bg-border hidden md:block mx-1"></div>

                 <!-- Mode Filter -->
                 <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="outline" class="gap-2 h-9" size="sm">
                      <Filter class="w-3.5 h-3.5" />
                      {{ selectedModeFilter === 'all' ? '所有模式' : getModeLabel(selectedModeFilter) }}
                      <ChevronDown class="w-3.5 h-3.5 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-48">
                    <DropdownMenuLabel>按模式筛选</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem @click="selectedModeFilter = 'all'">
                      <div class="flex items-center justify-between w-full">
                        全部
                        <CheckIcon v-if="selectedModeFilter === 'all'" class="w-4 h-4" />
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      v-for="mode in ['coordinate', 'route', 'broadcast', 'tasks']" 
                      :key="mode"
                      @click="selectedModeFilter = mode"
                    >
                      <div class="flex items-center justify-between w-full">
                        <span>{{ getModeLabel(mode) }}</span>
                        <CheckIcon v-if="selectedModeFilter === mode" class="w-4 h-4" />
                      </div>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                <Button @click="fetchTeams" variant="outline" size="icon" class="h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95 flex-shrink-0" title="刷新列表">
                  <RefreshCw class="h-4 w-4 text-muted-foreground" :class="{ 'animate-spin': loading }" />
                </Button>

                <Button size="sm" @click="startCreate" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
                  <Plus class="h-3.5 w-3.5" /> 创建团队
                </Button>
             </div>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col">
            <div v-if="loading && filteredTeams.length === 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              <div v-for="n in 8" :key="n" class="border rounded-xl p-4 bg-card h-[180px] flex flex-col space-y-3 shadow-sm">
                <div class="flex gap-3">
                  <Skeleton class="h-10 w-10 rounded-lg" />
                  <div class="space-y-2 flex-1 pt-1">
                    <Skeleton class="h-4 w-1/2" />
                    <Skeleton class="h-3 w-1/4" />
                  </div>
                </div>
                <div class="space-y-2 flex-1 pt-2">
                  <Skeleton class="h-3 w-full" />
                  <Skeleton class="h-3 w-5/6" />
                </div>
                <div class="pt-3 border-t flex justify-between items-center mt-auto">
                  <Skeleton class="h-3 w-20" />
                  <Skeleton class="h-7 w-16 rounded-md" />
                </div>
              </div>
            </div>

            <div v-else-if="filteredTeams.length === 0" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto text-muted-foreground animate-in fade-in duration-300">
              <div class="w-24 h-24 bg-muted/50 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
                 <Search v-if="teamSearchQuery" class="w-10 h-10 text-muted-foreground/50" />
                 <Users v-else class="w-10 h-10 text-muted-foreground/50" />
              </div>
              <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">{{ teamSearchQuery ? '未找到相关团队' : '暂无团队' }}</h3>
              <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">{{ teamSearchQuery ? '请尝试调整搜索关键词或筛选条件。' : '当前暂无智能团队，您可以点击下方按钮创建一个新的智能团队。' }}</p>
              <Button v-if="!teamSearchQuery && currentTab !== 'templates'" 
                  @click="startCreate"
                  class="px-8 shadow-sm hover:scale-105 transition-transform"
              >
                  <Plus class="w-4 h-4 mr-2" />
                  立即创建
              </Button>
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <TeamCard 
                v-for="team in filteredTeams" 
                :key="team.id" 
                :team="team"
                :agents="agents"
                @click="editTeam(team)"
                @edit="editTeam(team)"
                @delete="confirmDelete(team)"
              >
                <template #actions>
                    <DropdownMenuItem v-if="!team.is_template" @click.stop="saveAsTemplate(team)">
                        <span class="flex items-center gap-2 w-full">
                            <Copy class="w-4 h-4" /> 保存为模板
                        </span>
                    </DropdownMenuItem>
                    <DropdownMenuItem v-if="team.is_template" @click.stop="createFromTemplate(team)">
                        <span class="flex items-center gap-2 w-full">
                            <Plus class="w-4 h-4" /> 从模板创建
                        </span>
                    </DropdownMenuItem>
                </template>
              </TeamCard>
            </div>
          </div>
        </div>

        <!-- Sheet (Drawer) for Create/Edit -->
        <Sheet v-model:open="isSheetOpen" :modal="false">
          <SheetContent 
            :overlay="false" 
            :resizable="true" 
            :default-width="600"
            class="flex flex-col h-full overflow-hidden p-0 border-l shadow-2xl"
          >
             <SheetHeader class="px-6 py-4 border-b">
               <SheetTitle>{{ isEdit ? '编辑团队配置' : '创建新团队' }}</SheetTitle>
               <SheetDescription>
                  请根据业务需求配置团队的基础信息、协作模式及成员构成。
               </SheetDescription>
             </SheetHeader>
             
             <div class="flex-1 overflow-y-auto custom-scrollbar px-6 pb-6 pt-2">
                <!-- Form Content -->
                <div class="space-y-8">
                  <!-- Basic Info Section -->
                  <section class="space-y-4">
                    <div class="flex items-center gap-2 pb-2 border-b">
                      <div class="h-8 w-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                         <Settings class="h-4 w-4" />
                      </div>
                      <div>
                         <h4 class="text-sm font-semibold text-foreground">基本信息</h4>
                      </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-[1fr,auto] gap-5 pl-1">
                      <div class="flex flex-col space-y-2">
                        <Label class="text-xs font-medium flex items-center gap-1">
                          团队名称 <span class="text-destructive">*</span>
                        </Label>
                        <Input 
                          v-model="formData.name" 
                          placeholder="例如：市场情报分析组" 
                          class="h-9 transition-colors focus-visible:ring-primary/20" 
                          :class="{'border-destructive focus-visible:ring-destructive/20': errors.name}"
                          @input="errors.name = ''"
                        />
                        <span v-if="errors.name" class="text-xs text-destructive animate-in slide-in-from-top-1 block">{{ errors.name }}</span>
                      </div>
                      
                      <div class="flex flex-col space-y-2">
                         <Label class="text-xs font-medium">团队图标</Label>
                         <Popover>
                            <PopoverTrigger as-child>
                               <Button variant="outline" class="w-full md:w-[140px] justify-between h-9 px-3">
                                  <div class="flex items-center gap-2 overflow-hidden">
                                     <component :is="getIconComponent(formData.icon)" class="h-4 w-4 flex-shrink-0" :class="formData.icon ? 'text-primary' : 'text-muted-foreground'" />
                                     <span class="truncate text-xs">{{ formData.icon || '默认图标' }}</span>
                                  </div>
                                  <ChevronDown class="h-3.5 w-3.5 opacity-50 flex-shrink-0 ml-2" />
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent class="w-[320px] p-3" align="end">
                               <div class="grid grid-cols-6 gap-2">
                                  <div 
                                    v-for="icon in availableIcons" 
                                    :key="icon.name"
                                    class="flex items-center justify-center p-2 rounded-md hover:bg-muted cursor-pointer transition-all hover:scale-110"
                                    :class="formData.icon === icon.name ? 'bg-primary/10 text-primary ring-1 ring-primary/20' : 'text-muted-foreground'"
                                    @click="formData.icon = icon.name"
                                    :title="icon.name"
                                  >
                                    <component :is="icon.component" class="h-5 w-5" />
                                  </div>
                               </div>
                            </PopoverContent>
                         </Popover>
                      </div>
                    </div>
                      <div class="space-y-2 pl-1">
                        <Label class="text-xs font-medium">团队描述</Label>
                        <Textarea v-model="formData.description" placeholder="请详细描述该团队的主要职责、目标及预期产出..." class="resize-none min-h-[80px] text-sm focus-visible:ring-primary/20" />
                      </div>
                  </section>

                  <!-- Mode Configuration -->
                  <section class="space-y-4">
                    <div class="flex items-center gap-2 pb-2 border-b">
                      <div class="h-8 w-8 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-500">
                         <Workflow class="h-4 w-4" />
                      </div>
                      <div>
                         <h4 class="text-sm font-semibold text-foreground">协作模式</h4>
                         <p class="text-xs text-muted-foreground">定义智能体之间的交互与任务分发逻辑</p>
                      </div>
                    </div>

                    <div class="pl-1">
                       <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div 
                            v-for="modeOption in [
                              { val: 'coordinate', label: '协调模式', desc: 'Leader 拆解任务并分发，最后汇总结果', icon: Network },
                              { val: 'route', label: '路由模式', desc: 'Leader 识别意图，精确转发给单一专家', icon: GitFork },
                              { val: 'broadcast', label: '广播模式', desc: '全员并发处理，Leader 汇总所有回复', icon: Radio },
                              { val: 'tasks', label: '任务模式', desc: '生成任务清单，按序执行复杂流程', icon: ListTodo }
                            ]"
                            :key="modeOption.val"
                            @click="formData.mode = modeOption.val"
                            class="relative flex items-start gap-4 p-4 rounded-xl border transition-all cursor-pointer hover:shadow-md"
                            :class="formData.mode === modeOption.val ? 'border-primary bg-primary/5 ring-1 ring-primary/20 shadow-sm' : 'border-border bg-card hover:border-primary/50'"
                          >
                             <div class="mt-0.5 h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors" 
                                  :class="formData.mode === modeOption.val ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground group-hover:bg-muted/80'">
                                <component :is="modeOption.icon" class="h-5 w-5" />
                             </div>
                             <div class="flex-1 min-w-0">
                                <div class="flex items-center justify-between mb-1">
                                    <p class="text-sm font-medium transition-colors" :class="formData.mode === modeOption.val ? 'text-primary' : 'text-foreground'">{{ modeOption.label }}</p>
                                    <div class="h-4 w-4 rounded-full border flex items-center justify-center transition-colors"
                                         :class="formData.mode === modeOption.val ? 'border-primary bg-primary text-primary-foreground' : 'border-muted-foreground/30'">
                                        <div v-if="formData.mode === modeOption.val" class="h-1.5 w-1.5 rounded-full bg-white" />
                                    </div>
                                </div>
                                <p class="text-xs text-muted-foreground leading-snug">{{ modeOption.desc }}</p>
                             </div>
                          </div>
                       </div>
                    </div>
                  </section>

                  <!-- Members Selection (New Dual-Pane Design) -->
                  <section class="space-y-4 flex-1 flex flex-col min-h-0">
                    <div class="flex items-center justify-between pb-2 border-b flex-shrink-0">
                      <div class="flex items-center gap-2">
                         <div class="h-8 w-8 rounded-full bg-orange-500/10 flex items-center justify-center text-orange-500">
                            <Users class="h-4 w-4" />
                         </div>
                         <div>
                            <h4 class="text-sm font-semibold text-foreground">团队成员配置 <span v-if="errors.members" class="text-destructive text-xs ml-2 font-normal">{{ errors.members }}</span></h4>
                            <p class="text-xs text-muted-foreground">从左侧资源库选择智能体，并在右侧指定团队负责人 (Leader)</p>
                         </div>
                      </div>
                    </div>
                    
                    <div class="flex-1 flex flex-col lg:flex-row gap-4 min-h-[400px] lg:h-[500px]">
                       <!-- Left Pane: Source (Agent Library) -->
                       <div class="flex-1 flex flex-col border rounded-lg bg-card overflow-hidden shadow-sm">
                          <div class="p-3 border-b bg-muted/20 flex flex-col gap-3">
                             <div class="flex items-center justify-between">
                                <h5 class="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                   <Database class="h-3.5 w-3.5" /> 智能体资源库 ({{ filteredAgents.length }})
                                </h5>
                                <!-- Category Filter Tabs (Removed) -->
                             </div>
                             <div class="relative">
                                <Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                                <Popover v-model:open="showSuggestions">
                                   <PopoverTrigger as-child>
                                      <Input 
                                         v-model="agentSearchQuery" 
                                         placeholder="搜索智能体名称、描述..." 
                                         class="h-8 pl-8 text-xs bg-background" 
                                         @focus="showSuggestions = !!agentSearchQuery"
                                         @input="showSuggestions = !!agentSearchQuery"
                                      />
                                   </PopoverTrigger>
                                   <PopoverContent 
                                      v-if="suggestions.length > 0" 
                                      class="p-0 w-[250px]" 
                                      align="start" 
                                      side="bottom"
                                      :style="{ width: 'var(--radix-popover-trigger-width)' }"
                                      @open-auto-focus.prevent
                                   >
                                      <Command>
                                         <CommandList>
                                            <CommandGroup heading="相关智能体">
                                               <CommandItem 
                                                  v-for="agent in suggestions" 
                                                  :key="agent.id"
                                                  :value="agent.name"
                                                  @select="selectSuggestion(agent)"
                                                  class="text-xs cursor-pointer flex items-center gap-2"
                                               >
                                                  <div class="h-4 w-4 rounded-full overflow-hidden flex-shrink-0 bg-muted">
                                                     <img :src="getAgentIcon(agent.id)" class="h-full w-full object-cover" />
                                                  </div>
                                                  <span>{{ agent.name }}</span>
                                                  <Badge variant="outline" class="ml-auto text-[9px] px-1 h-3.5 font-normal text-muted-foreground border-muted-foreground/20">
                                                     {{ getCategoryLabel(getAgentCategory(agent)) }}
                                                  </Badge>
                                               </CommandItem>
                                            </CommandGroup>
                                         </CommandList>
                                      </Command>
                                   </PopoverContent>
                                </Popover>
                             </div>
                          </div>
                          
                          <div class="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2 bg-muted/5">
                             <div 
                                v-for="agent in filteredAgents" 
                                :key="agent.id" 
                                class="group flex items-start gap-3 p-2.5 rounded-md border bg-card transition-all cursor-pointer hover:shadow-md hover:border-primary/30"
                                :class="formData.members.includes(agent.id) ? 'opacity-50 grayscale-[0.5] pointer-events-none bg-muted' : ''"
                                @click="!formData.members.includes(agent.id) && addMember(agent.id)"
                             >
                                <div class="h-8 w-8 rounded-md bg-muted border flex-shrink-0 overflow-hidden">
                                   <img :src="getAgentIcon(agent.id)" class="h-full w-full object-cover" />
                                </div>
                                <div class="flex-1 min-w-0">
                                   <div class="flex justify-between items-start gap-2">
                                      <span class="text-sm font-medium truncate text-foreground/90 flex-1 min-w-0">{{ agent.name }}</span>
                                      <Badge variant="outline" class="text-[9px] px-1 h-4 font-normal bg-muted/50 text-muted-foreground whitespace-nowrap border-muted-foreground/20">
                                         {{ getCategoryLabel(getAgentCategory(agent)) }}
                                      </Badge>
                                      <Plus class="h-3.5 w-3.5 text-primary opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                                   </div>
                                   <p class="text-xs text-muted-foreground line-clamp-2 mt-0.5">{{ agent.description || '暂无描述' }}</p>
                                </div>
                             </div>
                             
                             <div v-if="filteredAgents.length === 0" class="flex flex-col items-center justify-center h-32 text-muted-foreground text-xs gap-2">
                                <Search class="h-6 w-6 opacity-20" />
                                <span>未找到匹配的智能体</span>
                             </div>
                          </div>
                       </div>

                       <!-- Mobile Divider -->
                       <div class="lg:hidden flex justify-center text-muted-foreground">
                          <ChevronDown class="h-5 w-5 animate-bounce" />
                       </div>

                       <!-- Right Pane: Target (Selected Members) -->
                       <div class="flex-1 flex flex-col border rounded-lg bg-card overflow-hidden shadow-sm">
                          <div class="p-3 border-b bg-muted/20 flex items-center justify-between h-[88px]">
                             <div class="space-y-1">
                                <h5 class="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                   <Users class="h-3.5 w-3.5" /> 已选成员 ({{ formData.members.length }})
                                </h5>
                                <p class="text-[10px] text-muted-foreground/70">
                                   点击 <Crown class="h-3 w-3 inline text-amber-500" /> 图标设置负责人
                                </p>
                             </div>
                             <Button 
                                variant="ghost" 
                                size="sm" 
                                class="h-7 text-xs text-destructive hover:text-destructive hover:bg-destructive/10"
                                @click="clearMembers"
                                :disabled="formData.members.length === 0"
                             >
                                清空
                             </Button>
                          </div>
                          
                          <div class="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2 bg-muted/5">
                             <!-- Leader Card (Pinned) -->
                             <div 
                                v-if="leaderMember" 
                                class="group flex items-center gap-3 p-2 rounded-md border border-amber-500/50 bg-amber-50/50 transition-all shadow-sm mb-2"
                             >
                                <div class="p-1 -ml-1 text-amber-500/30 cursor-not-allowed" title="Leader 固定置顶">
                                   <Crown class="h-4 w-4" />
                                </div>

                                <div class="relative h-9 w-9 flex-shrink-0">
                                   <img :src="getAgentIcon(leaderMember)" class="h-full w-full object-cover rounded-md border" />
                                   <div class="absolute -top-1.5 -right-1.5 bg-amber-500 text-white rounded-full p-0.5 shadow-sm border border-white z-10">
                                      <Crown class="h-2.5 w-2.5" />
                                   </div>
                                </div>
                                
                                <div class="flex-1 min-w-0">
                                   <span class="text-sm font-medium truncate block text-amber-700">
                                      {{ getAgentName(leaderMember) }}
                                   </span>
                                   <div class="flex items-center gap-2 mt-1">
                                      <span class="text-[10px] font-bold text-amber-600 bg-amber-100 px-1.5 rounded-sm">Leader</span>
                                   </div>
                                </div>

                                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity focus-within:opacity-100">
                                   <Button 
                                      size="icon" 
                                      variant="ghost" 
                                      class="h-7 w-7 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                      @click="removeMember(leaderMember)"
                                   >
                                      <X class="h-3.5 w-3.5" />
                                   </Button>
                                </div>
                             </div>

                             <draggable 
                                v-model="draggableMembers" 
                                item-key="id"
                                ghost-class="ghost"
                                handle=".drag-handle"
                                :animation="200"
                                class="space-y-2"
                             >
                                <template #item="{ element: memberId }">
                                   <div 
                                      class="group flex items-center gap-3 p-2 rounded-md border bg-card transition-all hover:shadow-sm border-border"
                                   >
                                      <!-- Drag Handle -->
                                      <div class="drag-handle cursor-grab active:cursor-grabbing p-1 -ml-1 text-muted-foreground/30 hover:text-muted-foreground transition-colors">
                                         <GripVertical class="h-4 w-4" />
                                      </div>

                                      <div class="relative h-9 w-9 flex-shrink-0">
                                         <img :src="getAgentIcon(memberId)" class="h-full w-full object-cover rounded-md border" />
                                      </div>
                                      
                                      <div class="flex-1 min-w-0">
                                         <span class="text-sm font-medium truncate block">
                                            {{ getAgentName(memberId) }}
                                         </span>
                                         <div class="flex items-center gap-2 mt-1">
                                            <span class="text-[10px] text-muted-foreground">成员</span>
                                         </div>
                                      </div>

                                      <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity focus-within:opacity-100">
                                         <TooltipProvider :delay-duration="100">
                                            <Tooltip>
                                               <TooltipTrigger as-child>
                                                  <Button 
                                                     size="icon" 
                                                     variant="ghost" 
                                                     class="h-7 w-7 rounded-md text-muted-foreground hover:text-amber-500 hover:bg-amber-50"
                                                     @click="setLeader(memberId)"
                                                  >
                                                     <Crown class="h-3.5 w-3.5" />
                                                  </Button>
                                               </TooltipTrigger>
                                               <TooltipContent side="top">设为负责人</TooltipContent>
                                            </Tooltip>
                                         </TooltipProvider>
                                         
                                         <Button 
                                            size="icon" 
                                            variant="ghost" 
                                            class="h-7 w-7 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                            @click="removeMember(memberId)"
                                         >
                                            <X class="h-3.5 w-3.5" />
                                         </Button>
                                      </div>
                                   </div>
                                </template>
                             </draggable>

                             <div v-if="formData.members.length === 0" class="flex flex-col items-center justify-center h-full text-muted-foreground text-xs gap-3 min-h-[120px] border-2 border-dashed rounded-lg border-muted/50 bg-muted/10">
                                <div class="h-10 w-10 rounded-full bg-muted/30 flex items-center justify-center">
                                   <Users class="h-5 w-5 opacity-30" />
                                </div>
                                <p>暂无成员，请从左侧添加</p>
                             </div>
                          </div>
                       </div>
                    </div>
                    <span v-if="errors.leader" class="text-xs text-destructive animate-in slide-in-from-top-1 block text-right px-1">{{ errors.leader }}</span>
                  </section>
                </div>
             </div>

             <SheetFooter class="p-6 border-t bg-muted/10 sm:justify-between sm:space-x-0">
               <div class="text-xs text-muted-foreground flex items-center">
                  <span v-if="hasUnsavedChanges" class="flex items-center gap-1.5 text-amber-500 font-medium animate-pulse">
                     <div class="h-1.5 w-1.5 rounded-full bg-amber-500"></div>
                     有未保存的修改
                  </span>
               </div>
               <div class="flex gap-3">
                  <Button variant="outline" @click="handleCancel" :disabled="saving">取消</Button>
                  <Button @click="saveTeam" :disabled="saving" class="min-w-[100px] shadow-sm">
                     <span v-if="saving" class="flex items-center gap-2">
                       <div class="animate-spin h-3.5 w-3.5 border-b-2 border-current rounded-full"></div>
                       保存中...
                     </span>
                     <span v-else>确认保存</span>
                  </Button>
               </div>
             </SheetFooter>
          </SheetContent>
        </Sheet>
      </div>

      <!-- Unsaved Changes Alert -->
      <AlertDialog :open="showUnsavedAlert" @update:open="showUnsavedAlert = $event">
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{{ alertTitle }}</AlertDialogTitle>
            <AlertDialogDescription>
              {{ alertDesc }}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel @click="cancelNavigation">取消</AlertDialogCancel>
            <AlertDialogAction @click="confirmNavigation">{{ alertActionText }}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import Command from '@/components/ui/command/Command.vue'
import CommandEmpty from '@/components/ui/command/CommandEmpty.vue'
import CommandGroup from '@/components/ui/command/CommandGroup.vue'
import CommandInput from '@/components/ui/command/CommandInput.vue'
import CommandItem from '@/components/ui/command/CommandItem.vue'
import CommandList from '@/components/ui/command/CommandList.vue'
import { 
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter
} from '@/components/ui/sheet';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { 
  Edit2, Trash2, Plus, Users, Settings, Workflow, 
  Shield, Search, Network, GitFork, Radio, ListTodo, Filter, Check as CheckIcon, ChevronDown, Crown, Database, X, GripVertical,
  Briefcase, Building, Globe, Star, Activity, Code, Server, Cpu, MessageSquare, Zap, Target, Rocket, Copy, RefreshCw
} from 'lucide-vue-next';
import draggable from 'vuedraggable/src/vuedraggable';

import { useToast } from '@/components/ui/toast/use-toast';
import TeamCard from './TeamCard.vue';
import agentPublicSvgIcons from '@/generated/agentPublicIcons';

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

const { toast } = useToast();

const availableIcons = [
  { name: 'Users', component: Users },
  { name: 'Briefcase', component: Briefcase },
  { name: 'Building', component: Building },
  { name: 'Globe', component: Globe },
  { name: 'Shield', component: Shield },
  { name: 'Star', component: Star },
  { name: 'Activity', component: Activity },
  { name: 'Code', component: Code },
  { name: 'Database', component: Database },
  { name: 'Server', component: Server },
  { name: 'Cpu', component: Cpu },
  { name: 'MessageSquare', component: MessageSquare },
  { name: 'Search', component: Search },
  { name: 'Workflow', component: Workflow },
  { name: 'Network', component: Network },
  { name: 'Zap', component: Zap },
  { name: 'Target', component: Target },
  { name: 'Rocket', component: Rocket },
];

const getIconComponent = (iconName: string) => {
  if (!iconName) return Users;
  const icon = availableIcons.find(i => i.name === iconName);
  return icon ? icon.component : Users;
};

const view = ref<'list' | 'create' | 'edit'>('list');
const teams = ref<any[]>([]);
const agents = ref<any[]>([]);
const loading = ref(false);
const saving = ref(false);
const isEdit = computed(() => view.value === 'edit');
const isSheetOpen = computed({
  get: () => view.value === 'create' || view.value === 'edit',
  set: (val) => {
    if (!val) handleCancel();
  }
});

// Alert Dialog State
const showUnsavedAlert = ref(false);
const pendingNavigation = ref<'list' | null>(null);
const alertTitle = ref('');
const alertDesc = ref('');
const alertActionText = ref('');

// Search & Filter
const teamSearchQuery = ref('');
const agentSearchQuery = ref('');
const selectedModeFilter = ref('all');
const selectedAgentFilter = ref('all');
const selectedCategory = ref('all');

const currentTab = ref('instances'); // instances | templates

const formData = ref({
  id: null as number | null,
  name: '',
  description: '',
  icon: '',
  mode: 'coordinate',
  leader_id: null as string | null,
  members: [] as string[],
  is_template: false
});

const errors = ref({
   name: '',
   leader: '',
   members: ''
});

// Original data for change detection
const originalFormData = ref<string>('');

const api = axios.create({
  baseURL: '/api/v1'
});

const filteredTeams = computed(() => {
   let result = teams.value;
   
   // Mode Filter
   if (selectedModeFilter.value !== 'all') {
      result = result.filter(t => t.mode === selectedModeFilter.value);
   }

   // Agent Filter
   if (selectedAgentFilter.value !== 'all') {
      result = result.filter(t => t.members.includes(selectedAgentFilter.value));
   }

   // Search
   if (teamSearchQuery.value) {
      const q = teamSearchQuery.value.toLowerCase();
      result = result.filter(t => 
          t.name.toLowerCase().includes(q) || 
          (t.description && t.description.toLowerCase().includes(q))
      );
   }
   
   return result;
});

const showSuggestions = ref(false);
const suggestions = computed(() => {
   if (!agentSearchQuery.value) return [];
   const q = agentSearchQuery.value.toLowerCase();
   return agents.value.filter(a => 
      a.name.toLowerCase().includes(q)
   ).slice(0, 5); // Limit to top 5 suggestions
});

const selectSuggestion = (agent: any) => {
   agentSearchQuery.value = agent.name;
   showSuggestions.value = false;
   // Ensure category filter doesn't hide the selected result if it's different
   if (selectedCategory.value !== 'all' && getAgentCategory(agent) !== selectedCategory.value) {
      selectedCategory.value = 'all';
   }
};
const getCategoryLabel = (cat: string) => {
   const map: Record<string, string> = {
      'all': '全部',
      'analysis': '分析',
      'dev': '开发',
      'design': '设计',
      'other': '其他'
   };
   return map[cat] || cat;
};

// Mock function to assign random categories based on ID (since backend might not have it yet)
const getAgentCategory = (agent: any) => {
   if (agent.category) return agent.category;
   const idNum = parseInt(agent.id.replace(/\D/g, '') || '0');
   if (idNum % 3 === 0) return 'analysis';
   if (idNum % 3 === 1) return 'dev';
   return 'design';
};

const filteredAgents = computed(() => {
   let result = agents.value;
   
   // Category Filter
   if (selectedCategory.value !== 'all') {
      result = result.filter(a => getAgentCategory(a) === selectedCategory.value);
   }

   if (agentSearchQuery.value) {
      const q = agentSearchQuery.value.toLowerCase();
      result = result.filter(a => 
         a.name.toLowerCase().includes(q) || 
         (a.description && a.description.toLowerCase().includes(q))
      );
   }
   
   return result;
});

const leaderMember = computed(() => {
   if (!formData.value.leader_id) return null;
   return formData.value.leader_id;
});

const draggableMembers = computed({
   get: () => {
      // Exclude leader from draggable list
      return formData.value.members.filter(id => id !== formData.value.leader_id);
   },
   set: (val: string[]) => {
      // Reconstruct full list: Leader first, then others in new order
      const leader = formData.value.leader_id;
      if (leader) {
         formData.value.members = [leader, ...val];
      } else {
         formData.value.members = val;
      }
   }
});

const hasUnsavedChanges = computed(() => {
   if (view.value === 'list') return false;
   return JSON.stringify(formData.value) !== originalFormData.value;
});

const fetchTeams = async () => {
  loading.value = true;
  try {
    const isTemplate = currentTab.value === 'templates';
    const res = await api.get('/teams/', { params: { is_template: isTemplate } });
    teams.value = res.data;
  } catch (e) {
    toast({ variant: 'destructive', title: '获取团队列表失败', description: '无法连接到服务器，请稍后重试。' });
  } finally {
    loading.value = false;
  }
};

const fetchAgents = async () => {
  try {
    const res = await api.get('/agents/');
    agents.value = res.data;
  } catch (e) {
    console.error("Failed to fetch agents", e);
  }
};

const getModeLabel = (mode: string) => {
  const map: Record<string, string> = {
    'coordinate': '协调模式',
    'route': '路由模式',
    'broadcast': '广播模式',
    'tasks': '任务模式'
  };
  return map[mode] || mode;
};

const getTeamIcon = (team: any) => {
  if (team.is_readonly) return Shield;
  if (team.icon) return getIconComponent(team.icon);
  return Users;
};

const getAgentName = (agentId: string) => {
  const agent = agents.value.find(a => a.id === agentId);
  return agent ? agent.name : agentId;
};

const isImageSrc = (icon: unknown) => {
  if (!icon || typeof icon !== 'string') return false;
  const value = icon.trim();
  if (!value) return false;
  if (value.startsWith('data:image')) return true;
  if (value.startsWith('blob:')) return true;
  if (/^https?:\/\//i.test(value)) return true;
  if (value.startsWith('/') || value.startsWith('./') || value.startsWith('../')) return true;
  return /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i.test(value);
};

const getFallbackAgentIcon = (agentLike?: { id?: any; name?: any }) => {
  if (!agentPublicSvgIcons?.length) return '/tiga.svg';
  const key = String(agentLike?.id ?? agentLike?.name ?? '');
  if (!key) return agentPublicSvgIcons[Math.floor(Math.random() * agentPublicSvgIcons.length)];
  let hash = 0;
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
  return agentPublicSvgIcons[hash % agentPublicSvgIcons.length];
};

const getAgentIcon = (agentId: string) => {
  const agent = agents.value.find(a => a.id === agentId);
  const icon = agent?.icon || agent?.icon_url;
  if (isImageSrc(icon)) return icon;
  return getFallbackAgentIcon(agent ?? { id: agentId });
};

const startCreate = () => {
  formData.value = {
    id: null,
    name: '',
    description: '',
    icon: '',
    mode: 'coordinate',
    leader_id: null,
    members: [],
    is_template: currentTab.value === 'templates'
  };
  errors.value = { name: '', leader: '', members: '' };
  // Wait for DOM update before capturing original state
  setTimeout(() => {
    originalFormData.value = JSON.stringify(formData.value);
  }, 0);
  view.value = 'create';
};

const editTeam = (team: any) => {
  formData.value = {
    id: team.id,
    name: team.name,
    description: team.description,
    icon: team.icon || '',
    mode: team.mode,
    leader_id: team.leader_id,
    members: [...team.members],
    is_template: team.is_template || false
  };
  errors.value = { name: '', leader: '', members: '' };
  originalFormData.value = JSON.stringify(formData.value);
  view.value = 'edit';
};

const addMember = (agentId: string) => {
   if (!formData.value.members.includes(agentId)) {
      formData.value.members.push(agentId);
   }
   // Auto-select leader if first member
   if (!formData.value.leader_id) {
       formData.value.leader_id = agentId;
   }
   if (formData.value.members.length > 0) errors.value.members = '';
   if (formData.value.leader_id) errors.value.leader = '';
};

const removeMember = (agentId: string) => {
   formData.value.members = formData.value.members.filter(id => id !== agentId);
   // Clear leader if removed
   if (formData.value.leader_id === agentId) {
       formData.value.leader_id = formData.value.members.length > 0 ? formData.value.members[0] : null;
   }
   if (formData.value.members.length === 0) {
      // Optional: Add warning or validation state immediately
   }
};

const setLeader = (agentId: string) => {
   formData.value.leader_id = agentId;
   errors.value.leader = '';
};

const clearMembers = () => {
   formData.value.members = [];
   formData.value.leader_id = null;
};

const validateForm = () => {
   let isValid = true;
   errors.value = { name: '', leader: '', members: '' };
   
   if (!formData.value.name.trim()) {
      errors.value.name = '团队名称不能为空';
      isValid = false;
   } else if (formData.value.name.length > 50) {
      errors.value.name = '团队名称不能超过50个字符';
      isValid = false;
   }

   if (!formData.value.leader_id) {
      errors.value.leader = '请指定团队 Leader';
      isValid = false;
   }
   
   if (formData.value.members.length === 0) {
      errors.value.members = '请至少选择一名团队成员';
      isValid = false;
   }
   
   return isValid;
};

const saveTeam = async () => {
  if (!validateForm()) {
     toast({ variant: 'destructive', title: '表单校验失败', description: '请检查并修复标记的错误项。' });
     return;
  }

  saving.value = true;
  try {
    if (isEdit.value && formData.value.id) {
      await api.put(`/teams/${formData.value.id}`, formData.value);
      toast({ title: '更新成功', description: `团队 "${formData.value.name}" 已更新。` });
    } else {
      await api.post('/teams/', formData.value);
      toast({ title: '创建成功', description: `新团队 "${formData.value.name}" 已创建。` });
    }
    view.value = 'list';
    fetchTeams();
  } catch (e) {
    toast({ variant: 'destructive', title: '保存失败', description: '服务器处理请求时出错，请重试。' });
  } finally {
    saving.value = false;
  }
};

const confirmDelete = async (team: any) => {
  if (confirm(`确定要删除团队 "${team.name}" 吗? 此操作无法撤销。`)) {
    try {
      await api.delete(`/teams/${team.id}`);
      toast({ title: '删除成功', description: `团队 "${team.name}" 已被移除。` });
      fetchTeams();
    } catch (e) {
      toast({ variant: 'destructive', title: '删除失败' });
    }
  }
};

const saveAsTemplate = async (team: any) => {
  const newTeam = {
    ...team,
    id: undefined,
    name: `${team.name} (模板)`,
    is_template: true,
    is_readonly: false
  };
  try {
    await api.post('/teams/', newTeam);
    toast({ title: '保存成功', description: `已将 "${team.name}" 保存为模板。` });
    if (currentTab.value === 'templates') {
        fetchTeams();
    }
  } catch (e) {
    toast({ variant: 'destructive', title: '保存失败', description: '无法保存为模板。' });
  }
};

const createFromTemplate = (team: any) => {
  formData.value = {
    id: null,
    name: `${team.name} (副本)`,
    description: team.description,
    icon: team.icon || '',
    mode: team.mode,
    leader_id: team.leader_id,
    members: [...team.members],
    is_template: false
  };
  errors.value = { name: '', leader: '', members: '' };
  originalFormData.value = JSON.stringify(formData.value);
  view.value = 'create';
};

const handleSheetOpenUpdate = (val: boolean) => {
  if (val) {
     // Do nothing if trying to open, state is managed by view
  } else {
     // Only trigger cancel logic if closing
     handleCancel();
  }
};

const handleCancel = () => {
   if (hasUnsavedChanges.value) {
      alertTitle.value = '放弃未保存的修改？';
      alertDesc.value = '您有未保存的修改，确定要返回列表吗？您的更改将会丢失。';
      alertActionText.value = '放弃修改';
      pendingNavigation.value = 'list';
      showUnsavedAlert.value = true;
      return;
   }
   view.value = 'list';
};

const confirmNavigation = () => {
   if (pendingNavigation.value === 'list') {
      view.value = 'list';
   }
   showUnsavedAlert.value = false;
   pendingNavigation.value = null;
};

const cancelNavigation = () => {
   showUnsavedAlert.value = false;
   pendingNavigation.value = null;
};

onMounted(() => {
   fetchAgents();
   fetchTeams();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--muted));
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}

</style>
