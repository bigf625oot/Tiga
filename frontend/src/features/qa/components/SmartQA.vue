<template>
  <DynamicGridBackground 
    class="h-full overflow-hidden relative"
    :grid-size="30"
    grid-color="#ffffff"
    :blob-count="3"
    :blob-colors="['rgba(99, 102, 241, 0.12)', 'rgba(59, 130, 246, 0.12)', 'rgba(168, 85, 247, 0.12)']"
    :animation-speed="20"
  >
    <div v-if="useTaskUI" class="h-full flex flex-col">
      <div class="flex-none px-6 py-3 border-b border-figma-border flex justify-between items-center bg-white/80 backdrop-blur-sm z-30">
          <div class="flex items-center gap-3 min-w-0">
              <div class="relative w-[36px] h-[36px] flex items-center justify-center shrink-0">
                  <a-progress type="circle" :percent="workflowStore.progress" :size="36" :strokeWidth="4" :showInfo="false" strokeColor="#6366f1" trailColor="#e2e8f0" class="!m-0 !p-0" />
                  <div class="absolute inset-0 m-auto w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm overflow-hidden">
                      <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-full h-full object-cover" alt="Agent" />
                      <BaseIcon v-else icon="mdi:file-document-outline" class="text-white" :size="14" />
                  </div>
              </div>

              <div class="min-w-0">
                  <h2 class="font-bold text-figma-text text-sm m-0 leading-tight truncate">
                      {{ currentSession?.title || '新任务' }}
                  </h2>
                  <div class="flex items-center gap-1 text-sm text-figma-notation truncate" v-if="currentAgent">
                      <span>当前智能体:</span>
                      <span class="font-medium text-blue-600 truncate">{{ currentAgent.name }}</span>
                  </div>
              </div>
          </div>

          <div class="flex items-center gap-2 shrink-0">
              <button
                  class="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 transition-colors flex items-center justify-center"
                  title="查看系统日志"
                  @click="openTaskLogs"
              >
                  <BaseIcon icon="lucide:code" :size="16" />
              </button>

              <button
                  class="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 transition-colors flex items-center justify-center"
                  title="折叠/展开聊天区"
                  @click="toggleLeftPane"
              >
                  <BaseIcon v-if="!isLeftCollapsed" icon="lucide:panel-left-close" :size="16" />
                  <BaseIcon v-else icon="lucide:panel-left-open" :size="16" />
              </button>

              <button
                  class="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 transition-colors flex items-center justify-center"
                  title="折叠/展开任务区"
                  @click="toggleRightPane"
              >
                  <BaseIcon v-if="!isRightCollapsed" icon="lucide:panel-right-close" :size="16" />
                  <BaseIcon v-else icon="lucide:panel-right-open" :size="16" />
              </button>
          </div>
      </div>

      <div ref="splitContainerRef" class="flex-1 min-h-0 flex flex-col xl:flex-row bg-transparent overflow-hidden">
        <div v-show="!isLeftCollapsed" class="flex flex-col min-w-0 flex-1 bg-white/60 backdrop-blur-sm relative transition-all duration-150" :style="leftPaneStyle">
        <!-- Messages List -->
        <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center px-4 pt-[20px] pb-[20px] bg-transparent overflow-y-auto relative custom-scrollbar">
             <div class="w-full max-w-[800px] flex flex-col items-center gap-8">
                <div class="flex flex-col items-center gap-4">
                    <div class="w-[94px] h-[94px] flex items-center justify-center mb-2">
                        <img src="/bot.svg" alt="Robot" class="w-full h-full object-contain" />
                    </div>
                    <h1 class="text-[32px] font-bold text-[#2A2F3C] text-center m-0">让我们创造点厉害的东西！</h1>
                </div>
                
                <!-- Centered Input Area -->
                <div class="w-full relative flex flex-col gap-2 border border-slate-200 rounded-xl p-2 bg-transparent focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-300 transition-all shadow-[0_4px_12px_rgba(0,0,0,0.05)]">
                    <!-- Attachments Preview -->
                    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-2 pt-2">
                        <div v-for="(att, idx) in selectedAttachments" :key="idx" class="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100">
                            <PaperClipOutlined />
                            <span class="max-w-[100px] truncate">{{ att.name }}</span>
                            <DeleteOutlined class="cursor-pointer hover:text-red-500 ml-1" @click="removeAttachment(idx)" />
                        </div>
                    </div>

                    <textarea 
                        ref="textareaRef"
                        v-model="input" 
                        @keydown="onInputKeydown"
                        rows="1"
                        :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm text-slate-700 placeholder:text-slate-400 bg-transparent min-h-[36px] max-h-[200px] custom-scrollbar"
                        :disabled="isLoading"
                        @input="adjustHeight"
                    ></textarea>

                    <div class="flex justify-between items-center px-2 pb-1">
                         <div class="flex items-center gap-2 h-8">
                             <button @click="openAttachmentModal" class="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors flex items-center justify-center" title="添加附件">
                                <PaperClipOutlined />
                             </button>
                             <div class="h-4 w-px bg-slate-200 mx-1"></div>
                             <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="toggleWorkflowMode">
                                <a-switch size="small" :checked="isWorkflowMode" class="pointer-events-none" />
                                <span class="text-xs font-medium" :class="isWorkflowMode ? 'text-indigo-600' : 'text-slate-500'">任务模式</span>
                             </div>
                             <div class="h-4 w-px bg-slate-200 mx-1"></div>
                             <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                <a-switch size="small" :checked="isNetworkSearchEnabled" class="pointer-events-none" />
                                <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-indigo-600' : 'text-slate-500'">联网搜索</span>
                             </div>
                         </div>
                         
                         <div class="flex items-center gap-3 h-8">
                             <div class="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-slate-50 cursor-pointer border border-transparent hover:border-slate-200 transition-all h-full" @click="toggleAgentSelect">
                                <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-4 h-4 object-cover rounded-full" />
                                <img v-else src="/tiga.svg" class="w-4 h-4" />
                                <a-select 
                                    v-model:value="selectedAgentId" 
                                    @change="handleAgentChange"
                                    class="agent-select-figma w-[100px]"
                                    :bordered="false"
                                    size="small"
                                    :open="agentSelectOpen"
                                    @dropdownVisibleChange="val => agentSelectOpen = val"
                                    :dropdownMatchSelectWidth="false"
                                    :getPopupContainer="getPopupContainerForSelect"
                                >
                                    <a-select-option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</a-select-option>
                                </a-select>
                             </div>
                             <button 
                                @click="sendMessage" 
                                class="w-8 h-8 flex items-center justify-center rounded-full transition-all active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-indigo-200"
                                :class="input.trim() ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-300'"
                                :disabled="!input.trim() || isLoading"
                             >
                                <ArrowUpOutlined class="text-sm font-bold" />
                             </button>
                         </div>
                    </div>
                </div>

                <!-- Scripts Section -->
                <div v-if="userScripts.length > 0" class="flex flex-col gap-3 px-1 w-full animate-fade-in-up">
                    <span class="text-sm font-medium text-[#495363] px-3">用户快捷提示语</span>
                    <div class="flex gap-4 overflow-x-auto py-4 custom-scrollbar px-2">
                        <div 
                            v-for="s in userScripts" 
                            :key="s.id" 
                            class="w-[220px] h-[140px] flex-shrink-0 flex flex-col justify-between p-5 bg-gradient-to-br from-white via-white to-indigo-50/60 rounded-2xl border border-slate-100 hover:border-indigo-100 shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_24px_rgba(99,102,241,0.12)] hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden" 
                            @click="sendQuickMessage(s.content)"
                        >
                            <div class="absolute -right-10 -top-10 w-32 h-32 bg-gradient-to-br from-blue-100/50 to-purple-100/50 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                            <div class="flex flex-col gap-2 relative z-10">
                                <p class="text-xs text-slate-500 group-hover:text-slate-600 line-clamp-3 leading-relaxed transition-colors duration-300">
                                    {{ s.content }}
                                </p>
                            </div>
                            <div class="relative z-10 flex items-center justify-between mt-1 pt-3 border-t border-slate-50 group-hover:border-slate-100 transition-colors duration-300">
                                <span class="text-sm font-bold text-slate-700 group-hover:text-indigo-600 transition-colors duration-300 truncate">{{ s.title }}</span>
                            </div>
                        </div>
                    </div>
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
        />

        <!-- Input Area (Fixed Bottom for Chat) -->
        <div v-if="messages.length > 0" class="flex-none w-full py-3 px-4 bg-white z-30 border-t border-slate-100 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]">
            <div class="max-w-4xl mx-auto relative">
                <div class="relative flex flex-col gap-2 border border-slate-200 rounded-xl p-2 bg-transparent focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-300 transition-all">
                    <!-- Attachments Preview -->
                    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-2 pt-2">
                        <div v-for="(att, idx) in selectedAttachments" :key="idx" class="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100">
                            <PaperClipOutlined />
                            <span class="max-w-[100px] truncate">{{ att.name }}</span>
                            <DeleteOutlined class="cursor-pointer hover:text-red-500 ml-1" @click="removeAttachment(idx)" />
                        </div>
                    </div>

                    <textarea 
                        ref="textareaRef"
                        v-model="input" 
                        @keydown="onInputKeydown"
                        rows="1"
                        :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm text-slate-700 placeholder:text-slate-400 bg-transparent min-h-[36px] max-h-[200px] custom-scrollbar"
                        :disabled="isLoading"
                        @input="adjustHeight"
                    ></textarea>

                    <div class="flex justify-between items-center px-2 pb-1">
                         <div class="flex items-center gap-2 h-8">
                             <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                <a-switch size="small" :checked="isNetworkSearchEnabled" class="pointer-events-none" />
                                <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-indigo-600' : 'text-slate-500'">联网搜索</span>
                             </div>
                         </div>
                         <div class="flex items-center gap-3 h-8">
                             <button 
                                @click="sendMessage" 
                                class="w-8 h-8 flex items-center justify-center rounded-full transition-all active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-indigo-200"
                                :class="input.trim() ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-300'"
                                :disabled="!input.trim() || isLoading"
                             >
                                <ArrowUpOutlined class="text-sm font-bold" />
                             </button>
                         </div>
                    </div>
                </div>
            </div>
        </div>
      </div>

      <div
        v-if="isDesktop && !isLeftCollapsed && !isRightCollapsed"
        class="hidden xl:flex w-2 shrink-0 items-stretch justify-center cursor-col-resize bg-slate-50 hover:bg-slate-100 transition-colors"
        @mousedown="startResize"
      >
        <div class="w-px bg-slate-200 my-2"></div>
      </div>

      <div v-show="!isRightCollapsed" class="w-full h-[420px] xl:h-auto xl:flex-1 xl:min-w-0 xl:w-auto flex-shrink-0 bg-slate-50 z-20 transition-all duration-150 flex flex-col overflow-hidden" :style="rightPaneStyle">
        <WorkspaceTabs
            ref="workspaceTabsRef"
            :sessionId="currentSessionId || ''"
            :agentName="currentAgent?.name || ''"
            :isWorkflowMode="isWorkflowMode"
            :attachmentsCount="selectedAttachments.length"
        />
      </div>
    </div>
    </div>

    <div v-else class="h-full flex flex-col bg-transparent overflow-hidden relative">
      <div class="flex-1 flex flex-col h-full bg-transparent relative min-w-0">
          <div v-if="messages.length > 0" class="px-6 py-3 border-b border-figma-border flex justify-between items-center bg-white/80 backdrop-blur-sm z-10">
              <div class="flex items-center gap-3 group flex-1">
                  <div class="relative w-[36px] h-[36px] flex items-center justify-center">
                      <a-progress type="circle" :percent="workflowStore.progress" :size="36" :strokeWidth="4" :showInfo="false" strokeColor="#6366f1" trailColor="#e2e8f0" class="!m-0 !p-0" />
                      <div class="absolute inset-0 m-auto w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm overflow-hidden">
                          <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-full h-full object-cover" alt="Agent" />
                          <BaseIcon v-else icon="mdi:file-document-outline" class="text-white" :size="14" />
                      </div>
                  </div>
                  <div class="min-w-0">
                      <h2 class="font-bold text-figma-text text-sm m-0 leading-tight truncate">
                          {{ currentSession?.title || '新任务' }}
                      </h2>
                      <div class="flex items-center gap-1 text-sm text-figma-notation truncate" v-if="currentAgent">
                          <span>当前智能体:</span>
                          <span class="font-medium text-blue-600 truncate">{{ currentAgent.name }}</span>
                      </div>
                  </div>
              </div>
          </div>

          <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center px-4 pt-[20px] pb-[20px] bg-transparent overflow-y-auto relative custom-scrollbar">
               <div class="w-full max-w-[800px] flex flex-col items-center gap-8">
                  <div class="flex flex-col items-center gap-4">
                      <div class="w-[94px] h-[94px] flex items-center justify-center mb-2">
                          <img src="/bot.svg" alt="Robot" class="w-full h-full object-contain" />
                      </div>
                      <h1 class="text-[32px] font-bold text-[#2A2F3C] text-center m-0">让我们创造点厉害的东西！</h1>
                  </div>
                  
                  <div class="w-full relative flex flex-col gap-2 border border-slate-200 rounded-xl p-2 bg-transparent focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-300 transition-all shadow-[0_4px_12px_rgba(0,0,0,0.05)]">
                      <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-2 pt-2">
                          <div v-for="(att, idx) in selectedAttachments" :key="idx" class="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100">
                              <PaperClipOutlined />
                              <span class="max-w-[100px] truncate">{{ att.name }}</span>
                              <DeleteOutlined class="cursor-pointer hover:text-red-500 ml-1" @click="removeAttachment(idx)" />
                          </div>
                      </div>

                      <textarea 
                          ref="textareaRef"
                          v-model="input" 
                          @keydown="onInputKeydown"
                          rows="1"
                          :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm text-slate-700 placeholder:text-slate-400 bg-transparent min-h-[36px] max-h-[200px] custom-scrollbar"
                        :disabled="isLoading"
                          @input="adjustHeight"
                      ></textarea>

                      <div class="flex justify-between items-center px-2 pb-1">
                           <div class="flex items-center gap-2 h-8">
                               <button @click="openAttachmentModal" class="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors flex items-center justify-center" title="添加附件">
                                  <PaperClipOutlined />
                               </button>
                               <div class="h-4 w-px bg-slate-200 mx-1"></div>
                               <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="toggleWorkflowMode">
                                  <a-switch size="small" :checked="isWorkflowMode" class="pointer-events-none" />
                                  <span class="text-xs font-medium" :class="isWorkflowMode ? 'text-indigo-600' : 'text-slate-500'">任务模式</span>
                               </div>
                               <div class="h-4 w-px bg-slate-200 mx-1"></div>
                               <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                  <a-switch size="small" :checked="isNetworkSearchEnabled" class="pointer-events-none" />
                                  <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-indigo-600' : 'text-slate-500'">联网搜索</span>
                               </div>
                           </div>
                           
                           <div class="flex items-center gap-3 h-8">
                               <div class="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-slate-50 cursor-pointer border border-transparent hover:border-slate-200 transition-all h-full" @click="toggleAgentSelect">
                                  <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-4 h-4 object-cover rounded-full" />
                                  <img v-else src="/tiga.svg" class="w-4 h-4" />
                                  <a-select 
                                      v-model:value="selectedAgentId" 
                                      @change="handleAgentChange"
                                      class="agent-select-figma w-[100px]"
                                      :bordered="false"
                                      size="small"
                                      :open="agentSelectOpen"
                                      @dropdownVisibleChange="val => agentSelectOpen = val"
                                      :dropdownMatchSelectWidth="false"
                                      :getPopupContainer="getPopupContainerForSelect"
                                  >
                                      <a-select-option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</a-select-option>
                                  </a-select>
                               </div>

                               <button 
                                  @click="sendMessage" 
                                  class="w-8 h-8 flex items-center justify-center rounded-full transition-all active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-indigo-200"
                                  :class="input.trim() ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-300'"
                                  :disabled="!input.trim() || isLoading"
                               >
                                  <ArrowUpOutlined class="text-sm font-bold" />
                               </button>
                           </div>
                      </div>
                  </div>

                  <div v-if="userScripts.length > 0" class="flex flex-col gap-3 px-1 w-full animate-fade-in-up">
                      <span class="text-sm font-medium text-[#495363] px-3">用户快捷提示语</span>
                      <div class="flex gap-4 overflow-x-auto py-4 custom-scrollbar px-2">
                        <div 
                            v-for="s in userScripts" 
                            :key="s.id" 
                            class="w-[220px] h-[140px] flex-shrink-0 flex flex-col justify-between p-5 bg-gradient-to-br from-white via-white to-indigo-50/60 rounded-2xl border border-slate-100 hover:border-indigo-100 shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_24px_rgba(99,102,241,0.12)] hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden" 
                            @click="sendQuickMessage(s.content)"
                        >
                            <div class="absolute -right-10 -top-10 w-32 h-32 bg-gradient-to-br from-blue-100/50 to-purple-100/50 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                            <div class="flex flex-col gap-2 relative z-10">
                                <p class="text-xs text-slate-500 group-hover:text-slate-600 line-clamp-3 leading-relaxed transition-colors duration-300">
                                    {{ s.content }}
                                </p>
                            </div>
                            <div class="relative z-10 flex items-center justify-between mt-1 pt-3 border-t border-slate-50 group-hover:border-slate-100 transition-colors duration-300">
                                <span class="text-sm font-bold text-slate-700 group-hover:text-indigo-600 transition-colors duration-300 truncate">{{ s.title }}</span>
                            </div>
                        </div>
                      </div>
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
          />

          <div v-if="messages.length > 0" class="flex-none w-full py-3 px-4 bg-white z-30 border-t border-slate-100 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]">
              <div class="max-w-4xl mx-auto relative">
                  <div class="relative flex flex-col gap-2 border border-slate-200 rounded-xl p-2 bg-transparent focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-300 transition-all">
                      <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-2 pt-2">
                          <div v-for="(att, idx) in selectedAttachments" :key="idx" class="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100">
                              <PaperClipOutlined />
                              <span class="max-w-[100px] truncate">{{ att.name }}</span>
                              <DeleteOutlined class="cursor-pointer hover:text-red-500 ml-1" @click="removeAttachment(idx)" />
                          </div>
                      </div>

                      <textarea 
                          ref="textareaRef"
                          v-model="input" 
                          @keydown="onInputKeydown"
                          rows="1"
                          :placeholder="'描述您的需求...'"
                        class="w-full p-2 resize-none outline-none text-sm text-slate-700 placeholder:text-slate-400 bg-transparent min-h-[36px] max-h-[200px] custom-scrollbar"
                        :disabled="isLoading"
                          @input="adjustHeight"
                      ></textarea>

                      <div class="flex justify-between items-center px-2 pb-1">
                           <div class="flex items-center gap-2 h-8">
                               <button @click="openAttachmentModal" class="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors flex items-center justify-center" title="添加附件">
                                  <PaperClipOutlined />
                               </button>
                               <div class="h-4 w-px bg-slate-200 mx-1"></div>
                               <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="toggleWorkflowMode">
                                  <a-switch size="small" :checked="isWorkflowMode" class="pointer-events-none" />
                                  <span class="text-xs font-medium" :class="isWorkflowMode ? 'text-indigo-600' : 'text-slate-500'">任务模式</span>
                               </div>
                               <div class="h-4 w-px bg-slate-200 mx-1"></div>
                               <div class="flex items-center gap-2 cursor-pointer select-none h-full" @click="isNetworkSearchEnabled = !isNetworkSearchEnabled">
                                  <a-switch size="small" :checked="isNetworkSearchEnabled" class="pointer-events-none" />
                                  <span class="text-xs font-medium" :class="isNetworkSearchEnabled ? 'text-indigo-600' : 'text-slate-500'">联网搜索</span>
                               </div>
                           </div>

                           <div class="flex items-center gap-3 h-8">
                               <div class="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-slate-50 cursor-pointer border border-transparent hover:border-slate-200 transition-all h-full" @click="toggleAgentSelect">
                                  <img v-if="currentAgent?.icon || currentAgent?.icon_url" :src="currentAgent?.icon || currentAgent?.icon_url" class="w-4 h-4 object-cover rounded-full" />
                                  <img v-else src="/tiga.svg" class="w-4 h-4" />
                                  <a-select 
                                      v-model:value="selectedAgentId" 
                                      @change="handleAgentChange"
                                      class="agent-select-figma w-[100px]"
                                      :bordered="false"
                                      size="small"
                                      :open="agentSelectOpen"
                                      @dropdownVisibleChange="val => agentSelectOpen = val"
                                      :dropdownMatchSelectWidth="false"
                                      :getPopupContainer="getPopupContainerForSelect"
                                  >
                                      <a-select-option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</a-select-option>
                                  </a-select>
                               </div>

                               <button 
                                  @click="sendMessage" 
                                  class="w-8 h-8 flex items-center justify-center rounded-full transition-all active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-indigo-200"
                                  :class="input.trim() ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-300'"
                                  :disabled="!input.trim() || isLoading"
                               >
                                  <ArrowUpOutlined class="text-sm font-bold" />
                               </button>
                           </div>
                      </div>
                  </div>
              </div>
          </div>
      </div>
    </div>

    <!-- Attachment Modal -->
    <a-modal v-model:open="attachmentModalVisible" title="选择附件" width="600px" @ok="handleAttachmentOk" destroyOnClose>
        <a-tabs v-model:activeKey="activeAttachmentTab" @change="handleAttachmentTabChange">
            <a-tab-pane key="local" tab="本地文件">
                <a-upload-dragger name="file" :multiple="true" :showUploadList="false" :beforeUpload="handleLocalUpload">
                    <p class="ant-upload-drag-icon"><InboxOutlined /></p>
                    <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p class="ant-upload-hint">支持 PDF, DOCX, PPTX, XLSX, TXT 格式，最大 50MB</p>
                </a-upload-dragger>
                <div v-if="localFileList.length > 0" class="mt-4 max-h-40 overflow-y-auto space-y-2 custom-scrollbar">
                    <div v-for="file in localFileList" :key="file.uid" class="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100">
                        <div class="flex items-center gap-2 truncate">
                            <PaperClipOutlined class="text-slate-400" />
                            <span class="text-sm text-slate-700 truncate max-w-[300px]">{{ file.name }}</span>
                            <span class="text-xs text-slate-400">({{ (file.size / 1024).toFixed(1) }} KB)</span>
                        </div>
                        <DeleteOutlined class="text-slate-400 hover:text-red-500 cursor-pointer" @click="removeLocalFile(file)" />
                    </div>
                </div>
            </a-tab-pane>
            <a-tab-pane key="knowledge" tab="知识库文档">
                <div class="flex flex-col gap-3 h-[400px]">
                    <div class="flex gap-2">
                        <a-input v-model:value="knowledgeSearchKeyword" placeholder="搜索文档名称..." allowClear>
                            <template #prefix><SearchOutlined /></template>
                        </a-input>
                        <a-button type="primary" :loading="knowledgeLoading" @click="fetchKnowledgeDocs">刷新</a-button>
                    </div>
                    <a-table
                        :dataSource="filteredKnowledgeDocs"
                        :columns="knowledgeColumns"
                        :rowKey="record => record.id"
                        :rowSelection="{ selectedRowKeys: selectedKnowledgeRowKeys, onChange: onKnowledgeSelectChange }"
                        :pagination="{ pageSize: 50, size: 'small' }"
                        :scroll="{ y: 300 }"
                        size="small"
                        :loading="knowledgeLoading"
                    />
                </div>
            </a-tab-pane>
        </a-tabs>
    </a-modal>
  </DynamicGridBackground>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { message } from 'ant-design-vue';
import MessageList from './MessageList.vue';
import ReferencesTable from './ReferencesTable.vue';
import ReferencesCards from './ReferencesCards.vue';
import WorkspaceTabs from '@/features/workflow/components/WorkspaceTabs.vue';
import BaseIcon from '@/shared/components/atoms/BaseIcon';
import DynamicGridBackground from '@/shared/components/molecules/DynamicGridBackground.vue';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import { 
    PaperClipOutlined,
    DeleteOutlined,
    InboxOutlined,
    SearchOutlined,
    ArrowUpOutlined
} from '@ant-design/icons-vue';

const props = defineProps({
    sessionId: { type: String, default: null }
});
const emit = defineEmits(['refresh-sessions']);

const workflowStore = useWorkflowStore();
const isWorkflowMode = ref(false); // Default to chat mode, but user can toggle
const isNetworkSearchEnabled = ref(true); // Network search toggle
const useTaskUI = computed(() => isWorkflowMode.value || workflowStore.isRunning || (workflowStore.tasks?.length || 0) > 0);
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

const toggleWorkflowMode = () => {
    isWorkflowMode.value = !isWorkflowMode.value;
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

// Knowledge Columns
const knowledgeColumns = [
    { title: '文档名称', dataIndex: 'filename', key: 'filename', sorter: (a, b) => a.filename.localeCompare(b.filename) },
    { title: '大小', dataIndex: 'file_size', key: 'file_size', customRender: ({ text }) => (text / 1024).toFixed(2) + ' KB', sorter: (a, b) => a.file_size - b.file_size },
    { title: '修改时间', dataIndex: 'updated_at', key: 'updated_at', sorter: (a, b) => new Date(a.updated_at) - new Date(b.updated_at) }
];

const getPopupContainerForSelect = () => {
    return document.body;
};

const openTaskLogs = () => {
    workspaceTabsRef.value?.openTaskLogs?.();
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
    if (newId) {
        fetchSessionDetails(newId);
    } else {
        currentSession.value = null;
        messages.value = [];
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

const structuredRefs = (msg) => {
    const sr = msg.meta_data?.structured_references || [];
    if (sr.length) return sr;
    const refs = msg.meta_data?.references || [];
    return refs.map((r, i) => ({
        id: i + 1,
        title: r.title || '',
        createTime: '',
        coverImage: r.url || '',
        summary: r.preview || '',
        tags: []
    }));
};

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
const handleAttachmentTabChange = (key) => {
    activeAttachmentTab.value = key;
    if (key === 'knowledge' && knowledgeDocs.value.length === 0) fetchKnowledgeDocs();
};
const handleLocalUpload = (file) => {
    const isLt50M = file.size / 1024 / 1024 < 50;
    if (!isLt50M) { message.error('文件大小不能超过 50MB!'); return false; }
    const acceptedTypes = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt'];
    const fileExt = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!acceptedTypes.includes(fileExt)) { message.error('不支持的文件类型!'); return false; }
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
        } else { message.error('获取知识库文档失败'); }
    } catch (e) { console.error(e); message.error('获取知识库文档出错'); } finally { knowledgeLoading.value = false; }
};
const filteredKnowledgeDocs = computed(() => {
    if (!knowledgeSearchKeyword.value) return knowledgeDocs.value;
    return knowledgeDocs.value.filter(d => d.filename.toLowerCase().includes(knowledgeSearchKeyword.value.toLowerCase()));
});
const onKnowledgeSelectChange = (selectedKeys) => { selectedKnowledgeRowKeys.value = selectedKeys; };
const handleAttachmentOk = () => {
    const localAtts = localFileList.value.map(f => ({ type: 'local', name: f.name, size: f.size, file: f }));
    const knowledgeAtts = knowledgeDocs.value
        .filter(d => selectedKnowledgeRowKeys.value.includes(d.id))
        .map(d => ({ type: 'knowledge', name: d.filename, size: d.file_size, id: d.id, file: null }));
    selectedAttachments.value = [...localAtts, ...knowledgeAtts];
    attachmentModalVisible.value = false;
    message.success(`已选择 ${selectedAttachments.value.length} 个附件`);
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

const handleAgentChange = async () => {
    if (messages.value.length === 0 && currentSessionId.value) {
        try {
            const res = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: selectedAgentId.value || null })
            });
            if (res.ok && currentSession.value) currentSession.value.agent_id = selectedAgentId.value;
        } catch (e) { console.error("Failed to update session agent", e); }
    }
};

const sendMessage = async () => {
    if (!input.value.trim() || isLoading.value) return;
    isLoading.value = true;
    
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
                const res = await fetch('/api/v1/knowledge/upload', { method: 'POST', body: formData });
                if (res.ok) {
                    const doc = await res.json();
                    attachmentIds.push(doc.id);
                } else { message.error(`附件上传失败: ${att.name}`); }
            } catch (e) { message.error(`附件上传出错: ${att.name}`); }
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
                    agent_id: selectedAgentId.value || null 
                })
            });
            if (res.ok) {
                const newSession = await res.json();
                emit('refresh-sessions');
                currentSessionId.value = newSession.id;
                currentSession.value = newSession;
            } else { throw new Error("Failed to create session"); }
        } catch (e) {
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

    // Chat Mode
    try {
        const payload = { 
            message: userMsg, 
            attachments: attachmentIds,
            enable_search: isNetworkSearchEnabled.value 
        };
        const response = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
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
        let fullBuffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            fullBuffer += chunk;
            
            // Check for hidden sources block
            const sourcesStart = fullBuffer.indexOf('__SOURCES__');
            let contentToProcess = fullBuffer;
            
            if (sourcesStart !== -1) {
                const jsonStr = fullBuffer.substring(sourcesStart + 11).trim();
                try {
                    if (jsonStr.endsWith('}')) { // Simple check if JSON might be complete
                        const sources = JSON.parse(jsonStr);
                        assistantMsg.sources = sources;
                    } else if (done) {
                         const sources = JSON.parse(jsonStr);
                         assistantMsg.sources = sources;
                    }
                } catch (e) {
                    // JSON might be incomplete during streaming
                }
                contentToProcess = fullBuffer.substring(0, sourcesStart);
            }

            const thinkStart = contentToProcess.indexOf('<think>');
            if (thinkStart !== -1) {
                const thinkEnd = contentToProcess.indexOf('</think>');
                if (thinkEnd !== -1) {
                    assistantMsg.reasoning = contentToProcess.substring(thinkStart + 7, thinkEnd).trim();
                    assistantMsg.content = (contentToProcess.substring(0, thinkStart) + contentToProcess.substring(thinkEnd + 8)).trim();
                } else {
                    assistantMsg.reasoning = contentToProcess.substring(thinkStart + 7);
                    assistantMsg.content = contentToProcess.substring(0, thinkStart);
                }
            } else {
                assistantMsg.content = contentToProcess;
            }
            scrollToBottom();
        }
        if (isAmisJSON(assistantMsg.content)) nextTick(() => renderAmis(assistantMsgIndex, assistantMsg.content));
    } catch (e) {
        console.error(e);
        messages.value.push({ role: 'assistant', content: "Error: " + e.message });
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

const renderMarkdown = (text, isAssistant = false) => {
    try {
        let inputText = (text || '').trim();
        let thinkHtml = '';
        if (isAssistant) {
            const thinkMatch = inputText.match(/<think>([\s\S]*?)<\/think>/);
            if (thinkMatch) {
                const thinkContent = thinkMatch[1];
                const parsedThink = marked.parse(thinkContent);
                thinkHtml = `<details class="mb-3 bg-amber-50/50 rounded-lg border border-amber-100 overflow-hidden group" ${inputText.includes('</think>') ? '' : 'open'}>
                    <summary class="px-3 py-1.5 text-xs font-medium text-amber-600/70 cursor-pointer hover:bg-amber-50 flex items-center gap-2 select-none transition-colors">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                        思考过程
                    </summary>
                    <div class="px-3 py-2 text-xs text-slate-600 border-t border-amber-100/50 bg-white/50 leading-relaxed">${parsedThink}</div>
                </details>`;
                inputText = inputText.replace(/<think>[\s\S]*?<\/think>/, '').trim();
            }
        }
        // ... (Cleanup logic same as before)
        inputText = inputText.replace(/doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?/gi, '');
        const refHeaderPattern = /\n+\s*(?:#+\s*)?(?:\*\*)?(References|Sources|参考来源|知识来源|引用|引用文献|Reference Document List)(:|\：)?(\*\*)?\s*(\n+|$)/gi;
        inputText = inputText.split(refHeaderPattern)[0];
        // ...
        let html = marked.parse(inputText);
        html = html.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, open, formula) => {
            try { return katex.renderToString(formula, { displayMode: true }); } catch { return match; }
        });
        html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try { return katex.renderToString(formula, { displayMode: false }); } catch { return match; }
        });
        html = html.replace(/<p>\s*<\/p>/g, '');
        return thinkHtml + html;
    } catch (e) { return text; }
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
    if (e.target.closest('.ant-select-selector')) return;
    agentSelectOpen.value = !agentSelectOpen.value;
};

const handleLocateNode = (item) => {
    // Open right pane if collapsed
    if (isRightCollapsed.value) {
        isRightCollapsed.value = false;
    }
    // Call workspaceTabs to locate node
    // item: { chunkId, docId, nodeId, ... }
    // If nodeId is present, use it. Else fall back to title or some other ID.
    // The requirement says "highlight node (nodeId binds to chunk metadata nodeId)".
    const nid = item.nodeId || item.title; 
    workspaceTabsRef.value?.locateNode?.(nid, item.docId);
};

const handleDocSummary = (item) => {
    console.log("View doc summary:", item);
    // Logic handled in SourcePanel usually, but if we need global overlay:
    // ...
};
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { height: 6px; width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: transparent; border-radius: 10px; }
.custom-scrollbar:hover::-webkit-scrollbar-thumb { background: #e5e6eb; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #bcc1cd; }

.markdown-body { font-size: 13px; line-height: 1.7; color: #334155; }
.markdown-body p { margin-bottom: 0.75em; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body strong { font-weight: 600; color: #1e293b; }
.markdown-body em { font-style: italic; }
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 { font-weight: 600; color: #0f172a; margin-top: 1.5em; margin-bottom: 0.5em; line-height: 1.3; }
.markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3em; }
.markdown-body h2 { font-size: 1.3em; }
.markdown-body h3 { font-size: 1.1em; }
.markdown-body ul, .markdown-body ol { padding-left: 1.5em; margin-bottom: 0.75em; }
.markdown-body ul { list-style-type: disc; }
.markdown-body ol { list-style-type: decimal; }
.markdown-body pre { background: #f1f5f9; padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 1em; border: 1px solid #e2e8f0; }
.markdown-body code { font-family: monospace; background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-size: 0.9em; }

:deep(.entity-citation) { color: #2563eb; background-color: #eff6ff; padding: 0px 4px; border-radius: 4px; border-bottom: 1px dashed #3b82f6; cursor: pointer; font-weight: 500; transition: all 0.2s; }
:deep(.entity-citation:hover) { background-color: #dbeafe; border-bottom-style: solid; }
:deep(.chunk-citation) { color: #6366f1; font-weight: bold; cursor: help; margin-left: 2px; padding: 0 2px; }
:deep(.chunk-citation:hover) { text-decoration: underline; }

:deep(.agent-select-figma .ant-select-selector) { padding: 0 !important; height: 24px !important; line-height: 24px !important; background: transparent !important; }
:deep(.agent-select-figma .ant-select-selection-item) { font-size: 13px !important; color: #475569 !important; font-weight: 500 !important; padding-inline-end: 4px !important; }
:deep(.agent-select-figma .ant-select-arrow) { display: none !important; }

.bubble-user { max-width: 85%; padding: 12px 16px; border-radius: 14px 14px 4px 14px; background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%); color: #ffffff; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2); font-size: 12px; line-height: 1.6; }
.bubble-assistant { max-width: 85%; padding: 16px 20px; border-radius: 14px 14px 14px 4px; background: #ffffff; border: 1px solid #f1f5f9; color: #334155; box-shadow: 0 2px 8px rgba(0,0,0,0.04); font-size: 12px; line-height: 1.6; }

.bg-animated::before {
    content: ""; position: absolute; inset: -20%;
    background: radial-gradient(circle at 20% 20%, rgba(99,102,241,0.08), transparent 60%), radial-gradient(circle at 80% 30%, rgba(59,130,246,0.08), transparent 55%), radial-gradient(circle at 30% 80%, rgba(16,185,129,0.05), transparent 55%);
    filter: blur(40px); pointer-events: none; z-index: 0;
}
</style>
