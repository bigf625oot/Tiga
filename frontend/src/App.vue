<template>
  <div class="flex h-screen w-full bg-background font-sans text-foreground antialiased overflow-hidden selection:bg-primary/20">
    <!-- Mobile Menu Button & Sheet -->
    <div class="md:hidden fixed bottom-6 right-6 z-50">
      <Sheet v-model:open="mobileMenuOpen">
        <SheetTrigger as-child>
          <Button 
            size="icon" 
            class="h-14 w-14 rounded-full shadow-lg shadow-primary/30 transition-all active:scale-95"
          >
            <Menu v-if="!mobileMenuOpen" class="h-6 w-6" />
            <X v-else class="h-6 w-6" />
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" class="h-[85vh] rounded-t-[20px] p-0 flex flex-col">
           <div class="p-6 pb-2">
              <Button @click="createNewChat(); mobileMenuOpen = false" class="w-full h-12 text-lg font-medium shadow-md">
                <Plus class="mr-2 h-5 w-5" /> 新建任务
              </Button>
           </div>
           
           <div class="flex-1 overflow-y-auto px-6 py-2 space-y-6">
              <!-- Task Section -->
              <div class="space-y-3">
                <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">任务</h4>
                <div @click="mobileMenuClick('chat')" class="flex items-center gap-4 p-3 rounded-xl bg-muted/50 active:scale-[0.98] transition-all">
                   <div class="h-10 w-10 rounded-lg bg-indigo-500/10 text-indigo-500 flex items-center justify-center">
                     <MessageSquare class="h-5 w-5" />
                   </div>
                   <span class="font-medium">智能问答</span>
                </div>
                <div @click="allSessionsModalVisible = true; mobileMenuOpen = false" class="flex items-center gap-4 p-3 rounded-xl bg-muted/50 active:scale-[0.98] transition-all">
                   <div class="h-10 w-10 rounded-lg bg-muted text-muted-foreground flex items-center justify-center">
                     <Clock class="h-5 w-5" />
                   </div>
                   <span class="font-medium">历史记录</span>
                </div>
              </div>

              <div class="h-px bg-border/50 w-full" />

              <!-- Agent Apps -->
              <div class="space-y-3">
                 <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">智能体应用</h4>
                 <div v-for="(item, index) in [
                    { name: '智能爬取', icon: Search, action: 'search', color: 'text-blue-500', bg: 'bg-blue-500/10' },
                    { name: '录音纪要', icon: Mic, action: 'list', color: 'text-orange-500', bg: 'bg-orange-500/10' },
                    { name: '指标提取', icon: BarChart, action: 'metrics', color: 'text-green-500', bg: 'bg-green-500/10' },
                    { name: '批量提取', icon: Box, action: 'batch_metrics', color: 'text-purple-500', bg: 'bg-purple-500/10' },
                    { name: '指标管理', icon: Calculator, action: 'indicators', color: 'text-pink-500', bg: 'bg-pink-500/10' },
                    { name: '智能问数', icon: LayoutGrid, action: 'data_query', color: 'text-cyan-500', bg: 'bg-cyan-500/10' }
                 ]" :key="index" @click="mobileMenuClick(item.action)" class="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/50 active:scale-[0.98] transition-all cursor-pointer">
                    <div :class="['h-10 w-10 rounded-lg flex items-center justify-center', item.bg, item.color]">
                       <component :is="item.icon" class="h-5 w-5" />
                    </div>
                    <span class="font-medium">{{ item.name }}</span>
                 </div>
              </div>

              <div class="h-px bg-border w-full" />

              <!-- Knowledge Center -->
              <div class="space-y-3">
                 <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">知识中心</h4>
                 <div v-for="(item, index) in [
                    { name: '知识图谱', icon: Network, action: 'knowledge_graph', color: 'text-amber-500', bg: 'bg-amber-500/10' },
                    { name: '关系修复', icon: Share2, action: 'relation_fix', color: 'text-amber-500', bg: 'bg-amber-500/10' },
                    { name: '知识库', icon: Database, action: 'knowledge', color: 'text-amber-500', bg: 'bg-amber-500/10' },
                    { name: '数据库', icon: Database, action: 'database', color: 'text-amber-500', bg: 'bg-amber-500/10' },
                    { name: '音视频库', icon: Film, action: 'media_library', color: 'text-amber-500', bg: 'bg-amber-500/10' }
                 ]" :key="index" @click="mobileMenuClick(item.action)" class="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/50 active:scale-[0.98] transition-all cursor-pointer">
                    <div :class="['h-10 w-10 rounded-lg flex items-center justify-center', item.bg, item.color]">
                       <component :is="item.icon" class="h-5 w-5" />
                    </div>
                    <span class="font-medium">{{ item.name }}</span>
                 </div>
              </div>
           </div>
        </SheetContent>
      </Sheet>
    </div>

    <!-- Desktop Sidebar -->
    <aside 
      class="hidden md:flex flex-col border-r dark:border-none bg-card dark:bg-transparent glass-sidebar transition-all duration-300 ease-in-out relative z-20"
      :class="isSidebarCollapsed ? 'w-[72px]' : 'w-[280px]'"
    >
      <!-- Header / Logo -->
      <div class="pt-6 pb-6 flex items-center transition-all duration-300 border-b border-border dark:border-none dark:shadow-[0_1px_0_0_rgba(255,255,255,0.05)]" :class="isSidebarCollapsed ? 'px-0 justify-center' : 'p-4 justify-between'">
         <div v-if="!isSidebarCollapsed" class="flex items-center gap-4 overflow-hidden flex-shrink-0 ml-1">
            <img :src="isLightMode ? '/logo_light.svg' : '/logo_dark.svg'" alt="TiGA Logo" class="h-6 w-auto flex-shrink-0" />
         </div>
         <Button variant="ghost" size="icon" @click="isSidebarCollapsed = !isSidebarCollapsed" class="p-1.5 rounded-lg hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10 text-muted-foreground transition-colors flex-shrink-0">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
               <path d="M7.77782 3.33325V16.6666M6.88893 3.33325H13.1112C14.3557 3.33325 14.978 3.33325 15.4534 3.57546C15.8715 3.78851 16.2114 4.12847 16.4245 4.54661C16.6667 5.02197 16.6667 5.64425 16.6667 6.88881V13.111C16.6667 14.3556 16.6667 14.9779 16.4245 15.4532C16.2114 15.8714 15.8715 16.2113 15.4534 16.4244C14.978 16.6666 14.3557 16.6666 13.1112 16.6666H6.88893C5.64437 16.6666 5.02209 16.6666 4.54673 16.4244C4.12859 16.2113 3.78863 15.8714 3.57558 15.4532C3.33337 14.9779 3.33337 14.3556 3.33337 13.111V6.88881C3.33337 5.64425 3.33337 5.02197 3.57558 4.54661C3.78863 4.12847 4.12859 3.78851 4.54673 3.57546C5.02209 3.33325 5.64437 3.33325 6.88893 3.33325Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
         </Button>
      </div>

      <!-- New Chat Action -->
      <div class="p-4">
         <TooltipProvider :delay-duration="0">
           <Tooltip>
             <TooltipTrigger as-child>
               <Button 
                 @click="createNewChat" 
                 :variant="isSidebarCollapsed ? 'ghost' : 'default'"
                 :size="isSidebarCollapsed ? 'icon' : 'default'"
                 class="w-full justify-start gap-2 shadow-sm transition-all dark:bg-transparent dark:border dark:border-blue-500 dark:text-blue-500 dark:shadow-[0_0_10px_rgba(59,130,246,0.5)] dark:hover:bg-blue-600 dark:hover:text-white dark:hover:shadow-[0_0_20px_rgba(59,130,246,0.6)]"
                 :class="isSidebarCollapsed ? 'h-10 w-10 justify-center p-0' : ''"
               >
                 <Plus class="h-5 w-5" />
                <span v-if="!isSidebarCollapsed">新建任务</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" v-if="isSidebarCollapsed">新建任务</TooltipContent>
           </Tooltip>
         </TooltipProvider>
      </div>

      <!-- Navigation Tabs -->
      <div class="px-3 flex items-center gap-2 mb-2" v-if="!isSidebarCollapsed">
         <Button 
           v-for="tab in ['task', 'agent', 'knowledge']" 
           :key="tab"
           variant="ghost" 
           size="sm"
           @click="sidebarTab = tab; if(tab === 'task') currentView = 'chat'; else if(tab === 'knowledge') currentView = 'knowledge'; else if(tab === 'agent') currentView = 'agent'"
          class="flex-1 capitalize text-xs font-medium text-muted-foreground data-[active=true]:bg-muted data-[active=true]:text-foreground transition-all"
          :data-active="sidebarTab === tab"
        >
          {{ tab === 'task' ? '任务' : tab === 'agent' ? '智能体' : '知识中心' }}
        </Button>
      </div>
      <div v-else class="flex flex-col items-center gap-2 px-2">
         <TooltipProvider v-for="tab in [
             { id: 'task', icon: MessageSquare, label: '任务' },
             { id: 'agent', icon: Box, label: '智能体' },
             { id: 'knowledge', icon: Database, label: '知识中心' }
         ]" :key="tab.id" :delay-duration="0">
           <Tooltip>
             <TooltipTrigger as-child>
               <Button 
                 variant="ghost" 
                 size="icon" 
                 @click="sidebarTab = tab.id; if(tab.id === 'task') currentView = 'chat'; else if(tab.id === 'knowledge') currentView = 'knowledge'; else if(tab.id === 'agent') currentView = 'agent'"
                 class="h-10 w-10 rounded-xl"
                 :class="sidebarTab === tab.id ? 'bg-muted text-foreground' : 'text-muted-foreground'"
               >
                 <component :is="tab.icon" class="h-5 w-5" />
               </Button>
             </TooltipTrigger>
             <TooltipContent side="right">{{ tab.label }}</TooltipContent>
           </Tooltip>
         </TooltipProvider>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
         <!-- Task List -->
         <template v-if="sidebarTab === 'task'">
            <div v-if="isSessionsLoading" class="space-y-3 px-1">
               <div v-for="i in 3" :key="i" class="flex items-center gap-3" :class="isSidebarCollapsed ? 'justify-center' : ''">
                  <Skeleton class="h-8 w-8 rounded-full flex-shrink-0" />
                  <div v-if="!isSidebarCollapsed" class="space-y-1 flex-1">
                     <Skeleton class="h-3 w-3/4" />
                     <Skeleton class="h-2 w-1/2" />
                  </div>
               </div>
            </div>
            <div v-else-if="sessions.length === 0 && !isSidebarCollapsed" class="flex flex-col items-center justify-center h-full text-center p-4">
               <div class="bg-muted/50 p-4 rounded-full mb-3">
                  <MessageSquare class="h-8 w-8 text-muted-foreground/50" />
               </div>
               <h3 class="font-medium text-sm text-foreground">暂无任务记录</h3>
               <p class="text-xs text-muted-foreground mt-1 max-w-[12rem]">
                  点击左上角“新建任务”开始新的对话
               </p>
            </div>
            <div v-else class="space-y-1">
               <template v-for="(group, gIndex) in groupedSessions" :key="group.agent.id">
                   <Collapsible
                       :open="isSidebarCollapsed || groupsState[group.agent.id]"
                       @update:open="(val) => groupsState[group.agent.id] = val"
                       class="space-y-1"
                   >
                       <!-- Group Header -->
                       <div v-if="!isSidebarCollapsed" class="px-2 pt-3 pb-1 flex items-center justify-between group/header select-none">
                           <CollapsibleTrigger class="flex items-center gap-2 w-full text-left hover:text-foreground transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background rounded-sm group/trigger cursor-pointer">
                               <component 
                                  :is="groupsState[group.agent.id] ? ChevronDown : ChevronRight" 
                                  class="h-3 w-3 text-muted-foreground/50 transition-transform duration-200 group-hover/trigger:text-muted-foreground" 
                               />
                               <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider truncate flex-1">
                                   {{ group.agent.name || '默认助手' }}
                               </h4>
                           </CollapsibleTrigger>
                           <span class="text-[10px] text-muted-foreground/70 bg-muted/50 px-1.5 py-0.5 rounded-md opacity-0 group-hover/header:opacity-100 transition-opacity">
                               {{ group.sessions.length }}
                           </span>
                       </div>
                       <Separator v-else-if="gIndex > 0" class="my-2 bg-border/30 mx-2" />

                       <CollapsibleContent class="data-[state=open]:animate-collapsible-down data-[state=closed]:animate-collapsible-up overflow-hidden">
                           <div class="space-y-0.5">
                               <div 
                                 v-for="session in group.sessions" 
                                 :key="session.id"
                                 @click="selectSession(session.id)"
                                 class="group relative flex flex-col gap-1.5 p-2 rounded-lg cursor-pointer transition-all duration-300 border border-transparent hover:bg-muted/50 dark:hover:bg-white/5"
                                 :class="[
                                    currentSessionId === session.id && currentView === 'chat' ? 'bg-muted dark:bg-white/10 shadow-sm' : '',
                                    isSidebarCollapsed ? 'justify-center items-center' : ''
                                 ]"
                               >
                                  <div class="flex items-center gap-2.5 w-full" :class="isSidebarCollapsed ? 'justify-center' : ''">
                                      <!-- Simple Avatar -->
                                      <div class="h-7 w-7 rounded-full overflow-hidden border border-black/5 dark:border-white/10 shadow-sm flex-shrink-0 bg-white dark:bg-slate-800 flex items-center justify-center">
                                          <img 
                                             v-if="getAgentIcon(session.agent_id)" 
                                             :src="getAgentIcon(session.agent_id)" 
                                             :alt="session.title" 
                                             class="h-full w-full object-cover"
                                          />
                                          <img v-else src="/tiga.svg" class="h-full w-full object-cover opacity-80" />
                                      </div>

                                      <!-- Content -->
                                      <div v-if="!isSidebarCollapsed" class="flex-1 min-w-0">
                                         <div class="flex items-center justify-between gap-1">
                                            <span class="text-sm font-medium truncate text-foreground/90 leading-tight">{{ session.title || '新对话' }}</span>
                                            
                                            <!-- Delete Button (Only visible on hover) -->
                                             <button 
                                               @click.stop="confirmDeleteSession(session.id)"
                                               class="text-muted-foreground/50 hover:text-destructive transition-colors opacity-0 group-hover:opacity-100 p-0.5 rounded-md hover:bg-destructive/10"
                                             >
                                                <Trash2 class="h-3 w-3" />
                                             </button>
                                         </div>
                                         <div class="flex items-center justify-between mt-0.5">
                                             <span class="text-[10px] text-muted-foreground/60 leading-none">{{ formatDate(session.updated_at).split(' ')[0] }}</span>
                                             <span v-if="session.mode === 'workflow' || session.mode === 'auto_task'" class="text-[10px] text-muted-foreground/60 leading-none">{{ getSessionProgress(session) }}%</span>
                                         </div>
                                      </div>
                                  </div>

                                  <!-- Progress Bar -->
                                  <div v-if="!isSidebarCollapsed && (session.mode === 'workflow' || session.mode === 'auto_task')" class="w-full h-0.5 bg-secondary/50 rounded-full overflow-hidden mt-0.5">
                                      <div 
                                        class="h-full bg-blue-500 transition-all duration-500 ease-out" 
                                        :style="{ width: `${getSessionProgress(session)}%` }"
                                      ></div>
                                  </div>
                               </div>
                           </div>
                       </CollapsibleContent>
                   </Collapsible>
               </template>
            </div>
         </template>

         <!-- Agent/Apps List -->
         <template v-else-if="sidebarTab === 'agent' || sidebarTab === 'knowledge'">
             <div class="space-y-1">
                 <template v-for="item in currentSidebarItems" :key="item.id || item.type || item.label">
                    
                    <div v-if="item.type === 'separator'" class="h-px bg-border my-2 mx-1" />

                    <div v-else-if="item.type === 'group'" class="px-3 py-2 mt-2 first:mt-0">
                       <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2" v-if="!isSidebarCollapsed">
                          {{ item.label }}
                          <span v-if="item.badge" class="px-1.5 py-0.5 rounded-md text-[10px] bg-blue-500/10 text-blue-500 font-bold border border-blue-500/20 leading-none">{{ item.badge }}</span>
                       </h4>
                       <div v-else class="h-px bg-border my-2 mx-1" />
                    </div>
                    
                    <TooltipProvider v-else :delay-duration="0">
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <div 
                            @click="handleSidebarItemClick(item)"
                            class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all hover:bg-muted/60"
                            :class="[
                               currentView === item.id ? 'bg-muted text-foreground font-medium dark:glass-sidebar-item-active dark:bg-transparent' : 'text-muted-foreground',
                               isSidebarCollapsed ? 'justify-center px-0' : ''
                            ]"
                          >
                             <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
                             <span v-if="!isSidebarCollapsed" class="text-sm truncate">{{ item.label }}</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="right" v-if="isSidebarCollapsed">{{ item.label }}</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                 </template>
             </div>
         </template>
      </div>

      <!-- User Profile -->
      <div class="p-4 border-t border-border dark:border-none dark:shadow-[0_-1px_0_0_rgba(255,255,255,0.05)] mt-auto">
         <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group" :class="isSidebarCollapsed ? 'justify-center p-0' : ''">
            <div class="h-9 w-9 rounded-full bg-muted overflow-hidden border border-border dark:border-none shadow-sm dark:avatar-breathing">
               <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Admin" alt="Avatar" class="h-full w-full object-cover" />
            </div>
            <div v-if="!isSidebarCollapsed" class="flex-1 min-w-0">
               <p class="text-sm font-medium truncate">管理员</p>
               <p class="text-xs text-muted-foreground truncate">数字化转型部</p>
            </div>
            <ThemeToggle v-if="!isSidebarCollapsed" />
         </div>
         <div v-if="isSidebarCollapsed" class="mt-2 flex justify-center">
             <ThemeToggle />
         </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col overflow-hidden relative bg-background">
       <!-- Header/Breadcrumbs could go here -->
       
       <div class="flex-1 overflow-hidden relative">
          <SmartQA 
            v-if="currentView === 'chat' || currentView === 'smart_qa'" 
            :session-id="currentSessionId" 
            @refresh-sessions="fetchSessions" 
            class="w-full h-full"
          />

          <div v-else class="h-full overflow-y-auto custom-scrollbar w-full">
             <component 
               :is="currentViewComponent" 
               v-bind="currentViewProps" 
               @back="handleBack"
               @view-detail="viewDetail"
               @navigate="currentView = $event"
               @navigate-to-extraction="handleNavigateToExtraction"
               @create="currentView = 'etl_pipeline'"
               @edit="currentView = 'etl_pipeline'"
             />
          </div>
       </div>
    </main>

    <!-- Global Toaster -->
    <Toaster />

    <!-- All Sessions Dialog -->
    <Dialog v-model:open="allSessionsModalVisible">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>全部任务记录</DialogTitle>
          <DialogDescription>查看并管理您的历史对话任务。</DialogDescription>
        </DialogHeader>
        <div class="py-4 space-y-4">
          <div class="relative">
            <Search class="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input v-model="sessionSearchKeyword" placeholder="搜索任务名称..." class="pl-9" />
          </div>
          <div class="h-[300px] overflow-y-auto custom-scrollbar space-y-1 pr-2">
            <div v-if="filteredSessions.length === 0" class="flex flex-col items-center justify-center h-full text-muted-foreground text-sm">
               未找到相关任务
            </div>
            <div 
              v-for="session in filteredSessions" 
              :key="session.id"
              @click="selectSession(session.id)"
              class="flex items-center justify-between p-3 rounded-lg hover:bg-muted cursor-pointer group transition-all"
              :class="currentSessionId === session.id ? 'bg-muted' : ''"
            >
               <div class="flex items-center gap-3 overflow-hidden">
                  <div class="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                     <MessageSquare class="h-4 w-4" />
                  </div>
                  <div class="min-w-0">
                     <p class="text-sm font-medium truncate">{{ session.title || '新对话' }}</p>
                     <p class="text-xs text-muted-foreground">{{ formatDate(session.updated_at) }}</p>
                  </div>
               </div>
               <Button 
                 @click.stop="confirmDeleteSession(session.id)"
                 variant="ghost" 
                 size="icon" 
                 class="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
               >
                 <Trash2 class="h-4 w-4" />
               </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:open="isDeleteDialogOpen">
       <DialogContent class="sm:max-w-[400px]">
          <DialogHeader>
             <DialogTitle>确认删除任务？</DialogTitle>
             <DialogDescription>此操作无法撤销。这将永久删除该任务记录。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
             <Button variant="outline" @click="isDeleteDialogOpen = false">取消</Button>
             <Button variant="destructive" @click="handleDeleteConfirm">删除</Button>
          </DialogFooter>
       </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, defineAsyncComponent, reactive, watch } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import { Skeleton } from '@/components/ui/skeleton';
import { useTheme } from '@/composables/useTheme';
import { useToast } from '@/components/ui/toast/use-toast';
import { Toaster } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import SmartQA from '@/features/qa/components/SmartQA.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import AgentIcon from '@/shared/components/atoms/AgentIcon/AgentIcon.vue';

// Icons
import {
  Menu, X, Plus, MessageSquare, Clock, Search, Mic, BarChart, Calculator,
  LayoutGrid, Database, Film, Box, Workflow, Network, Share2,
  Trash2, Settings, Cpu, MoreHorizontal, ChevronRight, ChevronDown
} from 'lucide-vue-next';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

// Initialize Theme
const { isLightMode } = useTheme();
const { toast } = useToast();

// Async Components
const RecordingList = defineAsyncComponent(() => import('@/features/recording/components/RecordingList.vue'));
const RecordingDetail = defineAsyncComponent(() => import('@/features/recording/components/RecordingDetail.vue'));
const MediaLibrary = defineAsyncComponent(() => import('@/features/recording/components/MediaLibrary.vue'));
const SearchAgent = defineAsyncComponent(() => import('@/features/search/components/SearchAgent.vue'));
const MetricsExtraction = defineAsyncComponent(() => import('@/features/analytics/components/MetricsExtraction.vue'));
const BatchExtraction = defineAsyncComponent(() => import('@/features/analytics/components/BatchExtraction.vue'));
const IndicatorManagement = defineAsyncComponent(() => import('@/features/analytics/components/IndicatorList.vue'));
const SmartDataQuery = defineAsyncComponent(() => import('@/features/analytics/components/SmartDataQuery.vue'));
const KnowledgeBase = defineAsyncComponent(() => import('@/features/knowledge/components/KnowledgeBase.vue'));
const KnowledgeGraphView = defineAsyncComponent(() => import('@/features/knowledge/components/KnowledgeGraphView.vue'));
const RelationFix = defineAsyncComponent(() => import('@/features/relation_fix/RelationFix.vue'));
const ModelManagement = defineAsyncComponent(() => import('@/features/system/components/ModelManagement.vue'));
const DatabaseManagement = defineAsyncComponent(() => import('@/features/system/components/DatabaseManagement.vue'));
const AgentManagement = defineAsyncComponent(() => import('@/features/agent/components/AgentManagement.vue'));
const ServiceMarket = defineAsyncComponent(() => import('@/features/agent/components/ServiceMarket.vue'));
const WorkflowManagement = defineAsyncComponent(() => import('@/features/workflow/components/WorkflowManagement.vue'));
const DataDashboard = defineAsyncComponent(() => import('@/features/data_etl/DataDashboard.vue'));
const DataSourceManagement = defineAsyncComponent(() => import('@/features/data_etl/DataSourceManagement.vue'));
const EtlPipelineList = defineAsyncComponent(() => import('@/features/data_etl/EtlPipelineList.vue'));
const EditorLayout = defineAsyncComponent(() => import('@/features/etl_editor/EditorLayout.vue'));
const SystemSettings = defineAsyncComponent(() => import('@/features/data_etl/SystemSettings.vue'));

// Setup Axios
const api = axios.create({
    baseURL: '/api/v1'
});

const workflowStore = useWorkflowStore();
const agents = ref<any[]>([]);

const fetchAgents = async () => {
    try {
        const res = await api.get('/agents/');
        agents.value = res.data;
    } catch (e) {
        console.error("Failed to fetch agents", e);
    }
};

const getAgentIcon = (agentId: any) => {
    if (!agentId) return null;
    const agent = agents.value.find((a: any) => a.id === agentId);
    return agent ? (agent.icon || agent.icon_url) : null;
};

const getSessionProgress = (session: any) => {
    if (session.id === currentSessionId.value) {
        return workflowStore.progress;
    }
    return session.progress || 0;
};

// State
const isSidebarCollapsed = ref(false);
const mobileMenuOpen = ref(false);
const currentView = ref('chat');
const sidebarTab = ref('task');

// Component Mapping
const componentMap: Record<string, any> = {
    'metrics': MetricsExtraction,
    'batch_metrics': BatchExtraction,
    'indicators': IndicatorManagement,
    'data_query': SmartDataQuery,
    'search': SearchAgent,
    'knowledge': KnowledgeBase,
    'knowledge_graph': KnowledgeGraphView,
    'relation_fix': RelationFix,
    'database': DatabaseManagement,
    'media_library': MediaLibrary,
    'model': ModelManagement,
    'agent': AgentManagement,
    'service_market': ServiceMarket,
    'workflow': WorkflowManagement,
    'data_dashboard': DataDashboard,
    'data_source': DataSourceManagement,
    'etl_list': EtlPipelineList,
    'etl_pipeline': EditorLayout,
    'etl_settings': SystemSettings,
    'list': RecordingList,
    'detail': RecordingDetail
};

const currentViewComponent = computed(() => {
    return componentMap[currentView.value] || null;
});

// Dynamic Props
const selectedRecording = ref<any>();
const prefilledIndicator = ref<any>();

const currentViewProps = computed(() => {
    if (currentView.value === 'detail') return { recording: selectedRecording.value };
    if (currentView.value === 'metrics') return { prefilledIndicator: prefilledIndicator.value };
    if (currentView.value === 'knowledge_graph') return { initialScope: 'global' };
    return {};
});

// Session Management
const sessions = ref<any[]>([]);
const currentSessionId = ref<string>();
const allSessionsModalVisible = ref(false);
const sessionSearchKeyword = ref('');
const isSessionsLoading = ref(true);
const deleteSessionId = ref<string | null>(null);
const isDeleteDialogOpen = ref(false);

const fetchSessions = async () => {
    try {
        isSessionsLoading.value = true;
        const res = await api.get('/chat/sessions');
        sessions.value = res.data;
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    } finally {
        isSessionsLoading.value = false;
    }
};

const confirmDeleteSession = (id: string) => {
    deleteSessionId.value = id;
    isDeleteDialogOpen.value = true;
};

const handleDeleteConfirm = async () => {
    if (deleteSessionId.value) {
        await deleteSession(deleteSessionId.value);
        isDeleteDialogOpen.value = false;
        deleteSessionId.value = null;
    }
};

const selectSession = (id: any) => {
    currentSessionId.value = id;
    currentView.value = 'chat';
    allSessionsModalVisible.value = false;
};

const deleteSession = async (id: any) => {
    try {
        await api.delete(`/chat/sessions/${id}`);
        sessions.value = sessions.value.filter(s => s.id !== id);
        
        if (currentSessionId.value === id || !sessions.value.find(s => s.id === currentSessionId.value)) {
            currentSessionId.value = undefined;
        }
        
        toast({ title: "删除成功" });
    } catch (e) {
        console.error("Delete session error:", e);
        toast({ variant: "destructive", title: "删除失败" });
        fetchSessions();
    }
};

const groupedSessions = computed(() => {
    // 1. Sort sessions by date first
    const sortedSessions = [...sessions.value].sort((a, b) => 
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );

    // 2. Group by agent
    const groups: Record<string, { agent: any, sessions: any[] }> = {};
    const defaultAgent = { id: 'default', name: '默认助手', icon: '/tiga.svg' };
    
    sortedSessions.forEach(session => {
        const agentId = session.agent_id || 'default';
        
        if (!groups[agentId]) {
            let agent = agents.value.find((a: any) => a.id === agentId);
            if (!agent) {
                 agent = agentId === 'default' ? defaultAgent : { id: agentId, name: '未知智能体', icon: '/tiga.svg' };
            }
            
            groups[agentId] = {
                agent,
                sessions: []
            };
        }
        groups[agentId].sessions.push(session);
    });

    // 3. Sort groups by latest session time
    return Object.values(groups).sort((a, b) => {
        const timeA = a.sessions.length > 0 ? new Date(a.sessions[0].updated_at).getTime() : 0;
        const timeB = b.sessions.length > 0 ? new Date(b.sessions[0].updated_at).getTime() : 0;
        return timeB - timeA;
    });
});

const topSessions = computed(() => sessions.value.slice(0, 5));
const filteredSessions = computed(() => {
    if (!sessionSearchKeyword.value) return sessions.value;
    const kw = sessionSearchKeyword.value.toLowerCase();
    return sessions.value.filter(s => (s.title || '新对话').toLowerCase().includes(kw));
});

const createNewChat = async () => {
    try {
        const res = await api.post('/chat/sessions', { 
            title: '新任务',
            agent_id: null 
        });
        const newSession = res.data;
        sessions.value.unshift(newSession);
        currentSessionId.value = newSession.id;
        currentView.value = 'chat';
        sidebarTab.value = 'task';
    } catch (e) {
        toast({ variant: "destructive", title: "创建任务失败" });
    }
};

const mobileMenuClick = (view: any) => {
    currentView.value = view;
    if (view === 'knowledge') sidebarTab.value = 'knowledge';
    mobileMenuOpen.value = false;
};

const handleSidebarItemClick = (item: any) => {
    if (item.id) {
        currentView.value = item.id;
    }
};

const viewDetail = async (file: any) => {
    try {
        const res = await api.get(`/recordings/${file.id}`);
        selectedRecording.value = res.data;
        currentView.value = 'detail';
    } catch (e: any) {
        if (e.response && e.response.status === 404) {
            toast({ variant: "destructive", title: "文件不存在或数据库已重置" });
        } else {
            toast({ variant: "destructive", title: "获取详情失败" });
        }
    }
};

const formatDate = (date: any) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

const handleNavigateToExtraction = (indicator: any) => {
    prefilledIndicator.value = indicator;
    currentView.value = 'metrics';
};

interface SidebarItem {
    id?: string;
    label?: string;
    icon?: any;
    type?: 'group' | 'separator';
    badge?: string;
}

const agentSidebarItems: SidebarItem[] = [
    { id: 'agent', label: '智能体中心', icon: Box },
    { id: 'service_market', label: '工具市场', icon: LayoutGrid },
    { type: 'separator' },
    { id: 'search', label: '智能爬取', icon: Search },
    { id: 'metrics', label: '指标提取', icon: BarChart },
    { id: 'batch_metrics', label: '批量提取', icon: Box },
    { id: 'indicators', label: '指标管理', icon: Calculator },
    { id: 'list', label: '录音纪要', icon: Mic },
    { id: 'data_query', label: '智能问数', icon: Database },
    { id: 'model', label: '模型管理', icon: Cpu },
    { id: 'workflow', label: '工作流', icon: Workflow }
];

const knowledgeSidebarItems: SidebarItem[] = [
    { type: 'group', label: '知识图谱' },
    { id: 'knowledge_graph', label: '知识图谱', icon: Network },
    { id: 'relation_fix', label: '图谱治理', icon: Share2 },
    { type: 'group', label: '资源中心' },
    { id: 'knowledge', label: '知识库', icon: Database },
    { id: 'database', label: '数据库', icon: Database },
    { id: 'media_library', label: '音视频库', icon: Film },
    { type: 'group', label: '流水线', badge: 'Beta' },
    { id: 'data_dashboard', label: '数据大屏', icon: BarChart },
    { id: 'data_source', label: '数据源', icon: Database },
    { id: 'etl_list', label: 'ETL流水线', icon: Workflow },
    { id: 'etl_settings', label: '系统设置', icon: Settings }
];

const currentSidebarItems = computed<SidebarItem[]>(() => {
    return sidebarTab.value === 'agent' ? agentSidebarItems : knowledgeSidebarItems;
});

const handleBack = () => {
    if (currentView.value === 'detail') {
        currentView.value = 'list';
    } else {
        currentView.value = 'etl_list';
    }
};

const groupsState = reactive<Record<string, boolean>>({});

watch(() => groupedSessions.value, (newVal) => {
    newVal.forEach(group => {
        if (groupsState[group.agent.id] === undefined) {
            groupsState[group.agent.id] = true;
        }
    });
}, { immediate: true });

onMounted(() => {
    fetchSessions();
    fetchAgents();
});
</script>

<style>
/* Custom Scrollbar for Webkit */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--muted));
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}

/* Glassmorphism Sidebar Styles */
.dark .glass-sidebar {
  background: rgba(15, 23, 42, 0.6); /* Slate-900 with opacity */
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: none;
  box-shadow: 1px 0 0 0 rgba(255, 255, 255, 0.05);
}

.dark .glass-sidebar-item-active {
  background: rgba(255, 255, 255, 0.03);
  color: #00D1FF;
  box-shadow: 0 0 15px rgba(0, 209, 255, 0.15), inset 0 0 0 1px rgba(0, 209, 255, 0.1);
  text-shadow: 0 0 10px rgba(0, 209, 255, 0.3);
}

.dark .glass-sidebar-item-active svg {
  color: #00D1FF;
  filter: drop-shadow(0 0 2px rgba(0, 209, 255, 0.5));
}

.dark .glass-separator {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  border: none;
}

/* Breathing Avatar Animation */
@keyframes breathing-light {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 209, 255, 0.1);
  }
  50% {
    box-shadow: 0 0 10px 2px rgba(0, 209, 255, 0.3);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 209, 255, 0.1);
  }
}

.dark .avatar-breathing {
  animation: breathing-light 3s infinite ease-in-out;
}
</style>
