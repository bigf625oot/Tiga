<template>
  <div class="flex h-screen bg-white overflow-hidden relative">
    
    <!-- Mobile Menu Button -->
    <div class="md:hidden absolute bottom-6 right-6 z-50">
        <button 
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="w-14 h-14 bg-blue-600 rounded-full shadow-lg shadow-blue-600/30 flex items-center justify-center text-white active:scale-95 transition-transform"
        >
            <svg v-if="!mobileMenuOpen" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
        
        <!-- Mobile Menu Overlay -->
        <div 
            v-if="mobileMenuOpen" 
            class="absolute bottom-16 right-0 bg-white rounded-2xl shadow-2xl border border-slate-100 py-3 min-w-[220px] max-h-[70vh] overflow-y-auto origin-bottom-right transition-all animate-in fade-in zoom-in duration-200 custom-scrollbar z-50"
        >
            <!-- New Task Section -->
            <div class="px-3 mb-2">
                <button 
                    @click="createNewChat(); mobileMenuOpen = false"
                    class="w-full flex items-center gap-3 py-3 bg-blue-600 text-white rounded-xl transition-all active:scale-95 justify-center"
                >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"></path></svg>
                    <span class="text-sm font-bold">新建任务</span>
                </button>
            </div>

            <div class="px-4 py-1 text-xs font-bold text-slate-400 uppercase tracking-widest">任务</div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('chat')"
            >
                <div class="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-500 flex items-center justify-center text-xs">💬</div>
                <span class="text-sm font-semibold">智能问答</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="allSessionsModalVisible = true; mobileMenuOpen = false"
            >
                <div class="w-7 h-7 rounded-lg bg-slate-50 text-slate-500 flex items-center justify-center text-xs">⏳</div>
                <span class="text-sm font-semibold">历史记录</span>
            </div>

            <div class="h-px bg-slate-100 my-2"></div>
            <div class="px-4 py-1 text-xs font-bold text-slate-400 uppercase tracking-widest">智能体应用</div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('search')"
            >
                <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-xs">🕷️</div>
                <span class="text-sm font-semibold">智能爬取</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('list')"
            >
                <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-xs">🎙️</div>
                <span class="text-sm font-semibold">录音纪要</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('metrics')"
            >
                <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-xs">📊</div>
                <span class="text-sm font-semibold">指标提取</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('indicators')"
            >
                <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-xs">📐</div>
                <span class="text-sm font-semibold">指标管理</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('data_query')"
            >
                <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-sm">📈</div>
                <span class="text-sm font-semibold">智能问数</span>
            </div>

            <div class="h-px bg-slate-100 my-2"></div>
            <div class="px-4 py-1 text-xs font-bold text-slate-400 uppercase tracking-widest">智能体平台</div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('agent')"
            >
                <div class="w-7 h-7 rounded-lg bg-purple-50 text-purple-500 flex items-center justify-center text-xs">⚙️</div>
                <span class="text-sm font-semibold">智能体管理</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('model')"
            >
                <div class="w-7 h-7 rounded-lg bg-purple-50 text-purple-500 flex items-center justify-center text-xs">🤖</div>
                <span class="text-sm font-semibold">模型管理</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('workflow')"
            >
                <div class="w-7 h-7 rounded-lg bg-purple-50 text-purple-500 flex items-center justify-center text-xs">🔗</div>
                <span class="text-sm font-semibold">工作流</span>
            </div>

            <div class="h-px bg-slate-100 my-2"></div>
            <div class="px-4 py-1 text-xs font-bold text-slate-400 uppercase tracking-widest">知识中心</div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('knowledge_graph')"
            >
                <div class="w-7 h-7 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-xs">🕸️</div>
                <span class="text-sm font-semibold">知识图谱</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('knowledge')"
            >
                <div class="w-7 h-7 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-xs">📚</div>
                <span class="text-sm font-semibold">知识库</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('database')"
            >
                <div class="w-7 h-7 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-xs">🗄️</div>
                <span class="text-sm font-semibold">数据库</span>
            </div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('media_library')"
            >
                <div class="w-7 h-7 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-xs">🎬</div>
                <span class="text-sm font-semibold">音视频库</span>
            </div>
        </div>
    </div>

    <!-- Desktop Sidebar -->
    <div 
        class="hidden md:flex flex-shrink-0 bg-figma-bg text-slate-800 transition-all duration-300 flex-col border-r border-figma-border relative z-20"
        :class="isSidebarCollapsed ? 'w-[64px]' : 'w-[256px]'"
    >
        <!-- Logo Area -->
        <div class="pt-6 pb-6 flex items-center transition-all duration-300" :class="isSidebarCollapsed ? 'px-0 justify-center' : 'px-3 justify-between'">
            <div v-if="!isSidebarCollapsed" class="flex items-center gap-3 overflow-hidden flex-shrink-0 ml-1">
                <!-- Figma Logo (TiGA) -->
                <svg width="71" height="24" viewBox="0 0 71 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="flex-shrink-0">
                    <rect x="0.0421143" y="0.0422363" width="23.9158" height="23.9158" rx="11.9579" fill="url(#paint0_linear_logo)"/>
                    <path d="M19.6916 10.475C20.0943 10.1874 20.5538 9.31541 20.6688 8.80754C20.7354 8.51431 21.0427 6.23939 18.9151 5.56877C16.7882 4.89815 15.287 6.7143 15.287 6.7143C14.5687 7.43262 13.2793 9.77769 13.2793 9.77769C13.353 6.31094 14.5694 5.18786 15.3193 4.7803C14.3028 4.37694 13.1952 4.15527 12.0349 4.15527C10.8746 4.15527 9.73332 4.38396 8.70494 4.79854C9.44712 5.21592 10.6074 6.33269 10.7077 9.64371C10.4713 9.23123 9.37977 7.35195 8.74142 6.7136C8.74142 6.7136 7.24024 4.89745 5.11333 5.56807C2.98642 6.23869 3.29367 8.51361 3.35961 8.80683C3.47465 9.31471 3.93343 10.1867 4.33678 10.4743C4.33678 10.4743 2.94784 12.5486 3.37154 14.9329C3.82049 17.4625 7.60501 18.0679 8.19426 19.9079C8.19426 19.9079 9.75437 17.2429 7.28864 13.3104C5.01793 9.6886 4.80958 10.012 4.27154 8.67075C4.27154 8.67075 3.92501 7.53293 4.9604 6.74727C5.9951 5.9616 7.07819 6.89107 7.07819 6.89107C7.07819 6.89107 6.32129 7.94541 6.11996 8.51993C9.6772 8.00994 10.5134 10.9828 10.5653 11.8064C10.7091 14.0771 10.2068 16.4587 9.80417 17.5368C9.40152 18.615 8.99957 19.7072 9.84696 20.5841C10.6951 21.461 11.802 21.4897 11.9956 21.4897C12.1892 21.4897 13.2969 21.461 14.1443 20.5841C14.9924 19.7072 14.5897 18.615 14.1871 17.5368C13.7844 16.4587 13.3249 14.1304 13.4687 11.8597C13.5206 11.0362 14.723 7.96224 18.2802 8.47222C17.806 7.47541 16.9509 6.89107 16.9509 6.89107C16.9509 6.89107 18.034 5.9616 19.0687 6.74727C20.1034 7.53293 19.7576 8.67075 19.7576 8.67075C19.2202 10.012 19.0112 9.6886 16.7405 13.3104C14.2755 17.2422 15.8349 19.9079 15.8349 19.9079C16.4241 18.0679 20.2079 17.4625 20.6576 14.9329C21.0813 12.5486 19.6923 10.4743 19.6923 10.4743L19.6916 10.475ZM13.8132 19.4105C13.8132 20.0054 13.1187 21.1018 12.0195 21.1018C10.9202 21.1018 10.2258 20.0054 10.2258 19.4105C10.2258 18.8157 11.029 18.333 12.0195 18.333C13.01 18.333 13.8132 18.8157 13.8132 19.4105Z" fill="#F7F7F7"/>
                    <path d="M9.17554 14.2129C9.4599 14.2129 9.69043 13.9824 9.69043 13.698C9.69043 13.4136 9.4599 13.1831 9.17554 13.1831C8.89117 13.1831 8.66064 13.4136 8.66064 13.698C8.66064 13.9824 8.89117 14.2129 9.17554 14.2129Z" fill="#F7F7F7"/>
                    <path d="M14.8888 14.2129C15.1732 14.2129 15.4037 13.9824 15.4037 13.698C15.4037 13.4136 15.1732 13.1831 14.8888 13.1831C14.6044 13.1831 14.3739 13.4136 14.3739 13.698C14.3739 13.9824 14.6044 14.2129 14.8888 14.2129Z" fill="#F7F7F7"/>
                    <path d="M37.0544 3.73682H28.0323C27.8613 3.73682 27.7227 3.87544 27.7227 4.04644V6.12478C27.7227 6.29577 27.8613 6.4344 28.0323 6.4344H30.8852C31.0562 6.4344 31.1948 6.57303 31.1948 6.74402V19.7788C31.1948 19.9498 31.3335 20.0885 31.5045 20.0885H33.5828C33.7538 20.0885 33.8924 19.9498 33.8924 19.7788V6.74348C33.8924 6.57249 34.031 6.43386 34.202 6.43386H37.055C37.226 6.43386 37.3646 6.29523 37.3646 6.12424V4.04644C37.3646 3.87544 37.226 3.73682 37.055 3.73682H37.0544Z" fill="#171717"/>
                    <path d="M42.7927 7.52148H40.7149C40.5439 7.52148 40.4053 7.66011 40.4053 7.83111V19.8691C40.4053 20.0401 40.5439 20.1787 40.7149 20.1787H42.7927C42.9637 20.1787 43.1023 20.0401 43.1023 19.8691V7.83111C43.1023 7.66011 42.9637 7.52148 42.7927 7.52148Z" fill="#171717"/>
                    <path d="M42.7927 3.73682H40.7149C40.5439 3.73682 40.4053 3.87544 40.4053 4.04644V6.19868C40.4053 6.36968 40.5439 6.5083 40.7149 6.5083H42.7927C42.9637 6.5083 43.1023 6.36968 43.1023 6.19868V4.04644C43.1023 3.87544 42.9637 3.73682 42.7927 3.73682Z" fill="#171717"/>
                    <path d="M50.5831 20.1769C48.1347 20.1769 46.1427 18.1935 46.1427 15.7559V8.15781C46.1427 5.72022 48.1347 3.73682 50.5831 3.73682C53.0315 3.73682 55.0235 5.72022 55.0235 8.15781V8.95344C55.0235 9.12444 54.8849 9.26306 54.7139 9.26306H52.6356C52.4646 9.26306 52.3259 9.12444 52.3259 8.95344V8.15781C52.3259 7.20738 51.5438 6.43386 50.5826 6.43386C49.6214 6.43386 48.8392 7.20738 48.8392 8.15781V15.7559C48.8392 16.7064 49.6214 17.4799 50.5826 17.4799C51.5438 17.4799 52.3259 16.7064 52.3259 15.7559V14.0897C52.3259 13.9187 52.1873 13.7801 52.0163 13.7801H50.8917C50.7207 13.7801 50.582 13.6414 50.582 13.4705V11.3921C50.582 11.2211 50.7207 11.0825 50.8917 11.0825H54.7134C54.8844 11.0825 55.023 11.2211 55.023 11.3921V15.7554C55.023 18.193 53.031 20.1764 50.5826 20.1764L50.5831 20.1769Z" fill="#171717"/>
                    <path d="M62.0781 3.97399L58.073 19.6784C58.0234 19.8742 58.1712 20.064 58.3729 20.064H60.5176C60.6589 20.064 60.7825 19.968 60.8175 19.831L63.3635 9.84762C63.4428 9.53746 63.883 9.53692 63.9628 9.84654L66.5439 19.8321C66.579 19.9686 66.7025 20.064 66.8433 20.064H68.9896C69.1919 20.064 69.3397 19.8731 69.289 19.6773L65.2304 3.97291C65.1954 3.83644 65.0718 3.74097 64.9311 3.74097H62.378C62.2367 3.74097 62.1132 3.83698 62.0781 3.97399Z" fill="#171717"/>
                    <defs>
                        <linearGradient id="paint0_linear_logo" x1="0.0421142" y1="10.8406" x2="25.2166" y2="10.8406" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#A940FF"/>
                            <stop offset="1" stop-color="#0056E8"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <!-- Sidebar Toggle -->
            <button @click="isSidebarCollapsed = !isSidebarCollapsed" class="p-1.5 rounded-lg hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10 text-figma-notation transition-colors flex-shrink-0">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M7.77782 3.33325V16.6666M6.88893 3.33325H13.1112C14.3557 3.33325 14.978 3.33325 15.4534 3.57546C15.8715 3.78851 16.2114 4.12847 16.4245 4.54661C16.6667 5.02197 16.6667 5.64425 16.6667 6.88881V13.111C16.6667 14.3556 16.6667 14.9779 16.4245 15.4532C16.2114 15.8714 15.8715 16.2113 15.4534 16.4244C14.978 16.6666 14.3557 16.6666 13.1112 16.6666H6.88893C5.64437 16.6666 5.02209 16.6666 4.54673 16.4244C4.12859 16.2113 3.78863 15.8714 3.57558 15.4532C3.33337 14.9779 3.33337 14.3556 3.33337 13.111V6.88881C3.33337 5.64425 3.33337 5.02197 3.57558 4.54661C3.78863 4.12847 4.12859 3.78851 4.54673 3.57546C5.02209 3.33325 5.64437 3.33325 6.88893 3.33325Z" stroke="#495363" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        </div>

        <!-- New Task Button -->
        <div class="px-3 mb-5">
            <button 
                v-if="!isSidebarCollapsed"
                @click="createNewChat"
                class="w-full flex items-center gap-2 py-2 bg-figma-gray hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10 text-figma-text rounded-lg transition-all duration-200 group px-2 h-[38px]"
            >
                <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 8H13" stroke="#171717" stroke-width="1.3" stroke-linecap="round"/>
                        <path d="M8.005 3.005L8.005 13.005" stroke="#171717" stroke-width="1.3" stroke-linecap="round"/>
                    </svg>
                </div>
                <span class="text-[14px] font-medium">新任务</span>
            </button>
            <div v-else class="flex justify-center">
                <button 
                    @click="createNewChat"
                    class="w-10 h-10 bg-figma-gray hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10 text-figma-text rounded-xl flex items-center justify-center transition-all duration-200"
                >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 8H13" stroke="#171717" stroke-width="1.5" stroke-linecap="round"/>
                        <path d="M8 3V13" stroke="#171717" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        </div>

        <!-- Main Tabs -->
        <div class="px-3 mb-5">
            <div v-if="!isSidebarCollapsed" class="flex items-center justify-between">
                <!-- Task Tab -->
                <div 
                    @click="sidebarTab = 'task'; currentView = 'chat'"
                    class="flex flex-col items-center justify-center w-[60px] h-[60px] rounded-[14px] cursor-pointer transition-all duration-200 gap-1.5"
                    :class="sidebarTab === 'task' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                >
                    <div class="w-4 h-4 flex items-center justify-center">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M6 7.33333L7.33333 8.66667L10.3333 5.66667M6.6 12.8L7.57333 14.0978C7.71808 14.2908 7.79045 14.3873 7.87918 14.4218C7.95689 14.452 8.04311 14.452 8.12082 14.4218C8.20955 14.3873 8.28192 14.2908 8.42667 14.0978L9.4 12.8C9.59543 12.5394 9.69315 12.4091 9.81234 12.3097C9.97126 12.177 10.1589 12.0832 10.3603 12.0357C10.5114 12 10.6743 12 11 12C11.9319 12 12.3978 12 12.7654 11.8478C13.2554 11.6448 13.6448 11.2554 13.8478 10.7654C14 10.3978 14 9.93188 14 9V5.2C14 4.0799 14 3.51984 13.782 3.09202C13.5903 2.71569 13.2843 2.40973 12.908 2.21799C12.4802 2 11.9201 2 10.8 2H5.2C4.0799 2 3.51984 2 3.09202 2.21799C2.71569 2.40973 2.40973 2.71569 2.21799 3.09202C2 3.51984 2 4.07989 2 5.2V9C2 9.93188 2 10.3978 2.15224 10.7654C2.35523 11.2554 2.74458 11.6448 3.23463 11.8478C3.60218 12 4.06812 12 5 12C5.32572 12 5.48858 12 5.63967 12.0357C5.84113 12.0832 6.02874 12.177 6.18766 12.3097C6.30685 12.4091 6.40457 12.5394 6.6 12.8Z" stroke="#2A2F3C" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="text-[12px] leading-none" :class="sidebarTab === 'task' ? 'text-figma-text font-medium' : 'text-figma-notation'">任务</span>
                </div>

                <!-- Agent Tab -->
                <div 
                    @click="sidebarTab = 'agent'"
                    class="flex flex-col items-center justify-center w-[60px] h-[60px] rounded-[14px] cursor-pointer transition-all duration-200 gap-1.5"
                    :class="sidebarTab === 'agent' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                >
                    <div class="w-4 h-4 flex items-center justify-center">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <g clip-path="url(#clip0_30_4444)">
                                <path d="M13.0556 4.81815H2.94445C2.51489 4.81815 2.16667 5.19803 2.16667 5.66663V14.1515C2.16667 14.6201 2.51489 15 2.94445 15H13.0556C13.4851 15 13.8333 14.6201 13.8333 14.1515V5.66663C13.8333 5.19803 13.4851 4.81815 13.0556 4.81815Z" stroke="#2A2F3C" stroke-width="1.3"/>
                                <path d="M8.00001 4.81818V1.92899L5.66667 1" stroke="#2A2F3C" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M13.8333 9.90929H15" stroke="#2A2F3C" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M10.3333 8.63629L10.3333 11.1817" stroke="#2A2F3C" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M5.66667 8.63629L5.66667 11.1817" stroke="#2A2F3C" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M1 9.90929H2.16667" stroke="#2A2F3C" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            </g>
                            <defs>
                                <clipPath id="clip0_30_4444">
                                    <rect width="16" height="16" fill="white"/>
                                </clipPath>
                            </defs>
                        </svg>
                    </div>
                    <span class="text-[12px] leading-none" :class="sidebarTab === 'agent' ? 'text-figma-text font-medium' : 'text-figma-notation'">智能体</span>
                </div>

                <!-- Knowledge Tab -->
                <div 
                    @click="sidebarTab = 'knowledge'; currentView = 'knowledge'"
                    class="flex flex-col items-center justify-center w-[60px] h-[60px] rounded-[14px] cursor-pointer transition-all duration-200 gap-1.5"
                    :class="sidebarTab === 'knowledge' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                >
                    <div class="w-4 h-4 flex items-center justify-center">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M10.6667 2H7.33334V14H10.6667V2Z" stroke="#333333" stroke-width="1.3" stroke-linejoin="round"/>
                            <path d="M14 2H10.6667V14H14V2Z" stroke="#333333" stroke-width="1.3" stroke-linejoin="round"/>
                            <path d="M3.33333 2L6 2.33333L4.83333 14L2 13.6667L3.33333 2Z" stroke="#333333" stroke-width="1.3" stroke-linejoin="round"/>
                            <path d="M12.3333 6V5" stroke="#333333" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M9 6V5" stroke="#333333" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="text-[12px] leading-none whitespace-nowrap" :class="sidebarTab === 'knowledge' ? 'text-figma-text font-medium' : 'text-figma-notation'">知识中心</span>
                </div>
            </div>
            <div v-else class="flex flex-col items-center gap-6 pt-2">
                <!-- Task Icon -->
                <div 
                    @click="sidebarTab = 'task'; currentView = 'chat'"
                    class="w-10 h-10 flex items-center justify-center cursor-pointer rounded-xl transition-colors"
                    :class="sidebarTab === 'task' ? 'bg-white border border-figma-line shadow-sm text-figma-text' : 'text-figma-notation hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                >
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 7.33333L7.33333 8.66667L10.3333 5.66667M6.6 12.8L7.57333 14.0978C7.71808 14.2908 7.79045 14.3873 7.87918 14.4218C7.95689 14.452 8.04311 14.452 8.12082 14.4218C8.20955 14.3873 8.28192 14.2908 8.42667 14.0978L9.4 12.8C9.59543 12.5394 9.69315 12.4091 9.81234 12.3097C9.97126 12.177 10.1589 12.0832 10.3603 12.0357C10.5114 12 10.6743 12 11 12C11.9319 12 12.3978 12 12.7654 11.8478C13.2554 11.6448 13.6448 11.2554 13.8478 10.7654C14 10.3978 14 9.93188 14 9V5.2C14 4.0799 14 3.51984 13.782 3.09202C13.5903 2.71569 13.2843 2.40973 12.908 2.21799C12.4802 2 11.9201 2 10.8 2H5.2C4.0799 2 3.51984 2 3.09202 2.21799C2.71569 2.40973 2.40973 2.71569 2.21799 3.09202C2 3.51984 2 4.07989 2 5.2V9C2 9.93188 2 10.3978 2.15224 10.7654C2.35523 11.2554 2.74458 11.6448 3.23463 11.8478C3.60218 12 4.06812 12 5 12C5.32572 12 5.48858 12 5.63967 12.0357C5.84113 12.0832 6.02874 12.177 6.18766 12.3097C6.30685 12.4091 6.40457 12.5394 6.6 12.8Z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <!-- Agent Icon -->
                <div 
                    @click="sidebarTab = 'agent'"
                    class="w-10 h-10 flex items-center justify-center cursor-pointer rounded-xl transition-colors"
                    :class="sidebarTab === 'agent' ? 'bg-white border border-figma-line shadow-sm text-figma-text' : 'text-figma-notation hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                >
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clip-path="url(#clip0_30_4444_collapsed)">
                            <path d="M13.0556 4.81815H2.94445C2.51489 4.81815 2.16667 5.19803 2.16667 5.66663V14.1515C2.16667 14.6201 2.51489 15 2.94445 15H13.0556C13.4851 15 13.8333 14.6201 13.8333 14.1515V5.66663C13.8333 5.19803 13.4851 4.81815 13.0556 4.81815Z" stroke="currentColor" stroke-width="1.3"/>
                            <path d="M8.00001 4.81818V1.92899L5.66667 1" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M13.8333 9.90929H15" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M10.3333 8.63629L10.3333 11.1817" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M5.66667 8.63629L5.66667 11.1817" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M1 9.90929H2.16667" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                        </g>
                        <defs>
                            <clipPath id="clip0_30_4444_collapsed">
                                <rect width="16" height="16" fill="white"/>
                            </clipPath>
                        </defs>
                    </svg>
                </div>
                <!-- Knowledge Icon -->
                <div 
                    @click="sidebarTab = 'knowledge'; currentView = 'knowledge'"
                    class="w-10 h-10 flex items-center justify-center cursor-pointer rounded-xl transition-colors"
                    :class="sidebarTab === 'knowledge' ? 'bg-white border border-figma-line shadow-sm text-figma-text' : 'text-figma-notation hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                >
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10.6667 2H7.33334V14H10.6667V2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                        <path d="M14 2H10.6667V14H14V2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                        <path d="M3.33333 2L6 2.33333L4.83333 14L2 13.6667L3.33333 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                        <path d="M12.3333 6V5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M9 6V5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
            </div>
        </div>

        <!-- Tab Content Area -->
        <div class="flex-1 py-2 flex flex-col gap-1 overflow-y-auto custom-scrollbar" :class="isSidebarCollapsed ? 'px-2' : 'px-4'">
             <!-- Task Tab Content -->
             <template v-if="sidebarTab === 'task'">
                <div v-if="!isSidebarCollapsed" class="flex flex-col gap-0.5">
                    <div v-if="sessions.length === 0" class="px-4 py-8 text-center text-slate-300 italic text-[14px]">暂无任务记录</div>
                    <div 
                        v-for="session in topSessions" 
                        :key="session.id"
                        @click="selectSession(session.id)"
                        class="group transition-all cursor-pointer relative rounded-lg"
                        :class="[
                            currentSessionId === session.id && currentView === 'chat' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            'px-2 py-1.5 mx-1'
                        ]"
                    >
                        <div class="flex items-center gap-2">
                            <!-- Status Icon -->
                            <div class="relative flex-shrink-0">
                                <div class="w-[18px] h-[18px] rounded-full bg-figma-gray flex items-center justify-center">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-figma-notation"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                                </div>
                            </div>

                            <div class="flex flex-col overflow-hidden flex-1 min-w-0">
                                <span class="text-[14px] leading-tight text-figma-notation truncate group-hover:text-figma-text transition-colors" :class="currentSessionId === session.id && currentView === 'chat' ? 'text-figma-text font-medium' : ''">{{ session.title || '新对话' }}</span>
                                <span class="text-xs text-figma-disable mt-0.5">{{ formatDate(session.updated_at).split(' ')[0] }}</span>
                            </div>
                            
                            <button 
                                @click.stop="deleteSession(session.id)"
                                class="p-1 text-figma-disable hover:text-red-500 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                            >
                                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path></svg>
                            </button>
                        </div>
                    </div>

                    <!-- View More Button -->
                    <div 
                        v-if="sessions.length > 5" 
                        @click="allSessionsModalVisible = true"
                        class="mx-1 px-2 py-2.5 flex items-center gap-1 cursor-pointer hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5 rounded-lg transition-colors mt-1"
                    >
                        <div class="w-3 h-3 flex items-center justify-center ml-0.5">
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M2 4H14M2 8H14M2 12H14" stroke="#2A2F3C" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <span class="text-[14px] text-figma-heading font-medium">查看更多</span>
                    </div>
                </div>
                
        <!-- Collapsed state sessions -->
                <div v-if="isSidebarCollapsed" class="flex flex-col gap-2 px-2">
                     <div 
                        v-for="session in topSessions" 
                        :key="session.id"
                        @click="selectSession(session.id)"
                        class="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer transition-all duration-200 relative group"
                        :class="currentSessionId === session.id && currentView === 'chat' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10'"
                        :title="session.title"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="currentSessionId === session.id && currentView === 'chat' ? 'text-figma-text' : 'text-figma-notation'"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    </div>
                </div>
             </template>

             <!-- Agent Tab Content -->
             <template v-else-if="sidebarTab === 'agent'">
                <div class="flex flex-col gap-1 overflow-y-auto custom-scrollbar" :class="isSidebarCollapsed ? 'items-center px-2' : ''">
                    <!-- Agent Center -->
                    <div 
                        @click="currentView = 'agent'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px] flex-shrink-0"
                        :class="[
                            currentView === 'agent' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            isSidebarCollapsed ? 'w-10 justify-center' : 'px-2 mx-1 gap-2'
                        ]"
                    >
                        <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M13.0556 4.81815H2.94445C2.51489 4.81815 2.16667 5.19803 2.16667 5.66663V14.1515C2.16667 14.6201 2.51489 15 2.94445 15H13.0556C13.4851 15 13.8333 14.6201 13.8333 14.1515V5.66663C13.8333 5.19803 13.4851 4.81815 13.0556 4.81815Z" :stroke="currentView === 'agent' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M8.00001 4.81818V1.92899L5.66667 1" :stroke="currentView === 'agent' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M13.8333 9.90929H15" :stroke="currentView === 'agent' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M1 9.90929H2.16667" :stroke="currentView === 'agent' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <span v-if="!isSidebarCollapsed" class="text-[14px] transition-colors" :class="currentView === 'agent' ? 'text-figma-text font-medium' : 'text-figma-notation group-hover:text-figma-text'">智能体中心</span>
                    </div>

                    <div v-if="!isSidebarCollapsed" class="mx-3 my-2 h-px bg-[#F0F0F0] flex-shrink-0"></div>

                    <!-- Smart Apps Group -->
                    <div class="flex flex-col gap-0.5">
                        <div v-if="!isSidebarCollapsed" class="px-3 h-[38px] flex items-center gap-2 flex-shrink-0">
                            <div class="w-4 h-4 flex items-center justify-center">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M8 1L14 4V12L8 15L2 12V4L8 1Z" stroke="#171717" stroke-width="1.3" stroke-linejoin="round"/>
                                    <path d="M8 5L11 6.5V9.5L8 11L5 9.5V6.5L8 5Z" stroke="#171717" stroke-width="1.3" stroke-linejoin="round"/>
                                </svg>
                            </div>
                            <span class="text-[14px] font-medium text-figma-text">智能应用</span>
                        </div>

                        <!-- Intelligent Crawling (Moved) -->
                        <div 
                            @click="currentView = 'search'"
                            class="h-[38px] flex items-center rounded-lg transition-all cursor-pointer mt-0.5"
                            :class="[
                                currentView === 'search' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                                isSidebarCollapsed ? 'w-10 justify-center' : 'px-3 ml-6'
                            ]"
                        >
                            <span v-if="!isSidebarCollapsed" class="text-[14px] transition-colors" :class="currentView === 'search' ? 'text-figma-text font-medium' : 'text-figma-notation'">智能爬取</span>
                            <div v-else class="w-1.5 h-1.5 rounded-full" :class="currentView === 'search' ? 'bg-blue-500' : 'bg-figma-disable'"></div>
                        </div>

                        <!-- Doc Processing Group -->
                        <div class="flex flex-col">
                            <div 
                                @click="isDocProcessingExpanded = !isDocProcessingExpanded"
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5 rounded-lg group flex-shrink-0"
                                v-if="!isSidebarCollapsed"
                            >
                                <span class="text-[14px] text-figma-notation group-hover:text-figma-text transition-colors ml-6">文档处理</span>
                                <svg class="w-3 h-3 text-figma-notation transition-transform duration-300" :class="isDocProcessingExpanded ? '' : '-rotate-90'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            
                            <div v-show="isDocProcessingExpanded || isSidebarCollapsed" class="flex flex-col gap-0.5" :class="isSidebarCollapsed ? '' : 'ml-11'">
                                <div v-for="item in [
                                    {name: '文档阅读', view: 'read'}, 
                                    {name: '文档审查', view: 'review'}, 
                                    {name: '文档对比', view: 'compare'}, 
                                    {name: '指标提取', view: 'metrics'},
                                    {name: '指标管理', view: 'indicators'}
                                ]" :key="item.name"
                                    @click="currentView = item.view"
                                    class="h-[38px] flex items-center rounded-lg transition-all cursor-pointer"
                                    :class="[
                                        currentView === item.view ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                                        isSidebarCollapsed ? 'w-10 justify-center' : 'px-2'
                                    ]"
                                >
                                    <span v-if="!isSidebarCollapsed" class="text-[14px] transition-colors" :class="currentView === item.view ? 'text-figma-text font-medium' : 'text-figma-notation'">{{ item.name }}</span>
                                    <div v-else class="w-1.5 h-1.5 rounded-full" :class="currentView === item.view ? 'bg-blue-500' : 'bg-figma-disable'"></div>
                                </div>
                            </div>
                        </div>

                        <!-- Content Creation Group -->
                        <div class="flex flex-col mt-1">
                            <div 
                                @click="isContentCreationExpanded = !isContentCreationExpanded"
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5 rounded-lg group flex-shrink-0"
                                v-if="!isSidebarCollapsed"
                            >
                                <span class="text-[14px] text-figma-notation group-hover:text-figma-text transition-colors ml-6">内容创作</span>
                                <svg class="w-3 h-3 text-figma-notation transition-transform duration-300" :class="isContentCreationExpanded ? '' : '-rotate-90'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            
                            <div v-show="isContentCreationExpanded || isSidebarCollapsed" class="flex flex-col gap-0.5" :class="isSidebarCollapsed ? '' : 'ml-11'">
                                <div v-for="item in [
                                    {name: '录音纪要', view: 'list'},
                                    {name: '智能纪要', view: 'summary'}, 
                                    {name: 'PPT创作', view: 'ppt'}
                                ]" :key="item.name"
                                    @click="currentView = item.view"
                                    class="h-[38px] flex items-center rounded-lg transition-all cursor-pointer"
                                    :class="[
                                        (currentView === item.view || (item.view === 'list' && currentView === 'detail')) ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                                        isSidebarCollapsed ? 'w-10 justify-center' : 'px-2'
                                    ]"
                                >
                                    <span v-if="!isSidebarCollapsed" class="text-[14px] transition-colors" :class="(currentView === item.view || (item.view === 'list' && currentView === 'detail')) ? 'text-figma-text font-medium' : 'text-figma-notation'">{{ item.name }}</span>
                                    <div v-else class="w-1.5 h-1.5 rounded-full" :class="(currentView === item.view || (item.view === 'list' && currentView === 'detail')) ? 'bg-blue-500' : 'bg-figma-disable'"></div>
                                </div>
                            </div>
                        </div>

                        <!-- Data Analytics Group (Restored) -->
                        <div class="flex flex-col mt-1">
                            <div 
                                @click="isDataAnalyticsExpanded = !isDataAnalyticsExpanded"
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5 rounded-lg group flex-shrink-0"
                                v-if="!isSidebarCollapsed"
                            >
                                <span class="text-[14px] text-figma-notation group-hover:text-figma-text transition-colors ml-6">智能问数</span>
                                <svg class="w-3 h-3 text-figma-notation transition-transform duration-300" :class="isDataAnalyticsExpanded ? '' : '-rotate-90'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path></svg>
                            </div>

                            <div v-show="isDataAnalyticsExpanded || isSidebarCollapsed" class="flex flex-col gap-0.5" :class="isSidebarCollapsed ? '' : 'ml-11'">
                                <div 
                                    @click="currentView = 'data_query'"
                                    class="h-[38px] flex items-center rounded-lg transition-all cursor-pointer"
                                    :class="[
                                        currentView === 'data_query' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                                        isSidebarCollapsed ? 'w-10 justify-center' : 'px-2'
                                    ]"
                                >
                                    <span v-if="!isSidebarCollapsed" class="text-[14px] transition-colors" :class="currentView === 'data_query' ? 'text-figma-text font-medium' : 'text-figma-notation'">智能问数</span>
                                    <div v-else class="w-1.5 h-1.5 rounded-full" :class="currentView === 'data_query' ? 'bg-blue-500' : 'bg-figma-disable'"></div>
                                </div>
                            </div>
                        </div>

                        <!-- Platform Group (Restored) -->
                        <div class="flex flex-col mt-1">
                            <div 
                                @click="isPlatformManagementExpanded = !isPlatformManagementExpanded"
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5 rounded-lg group flex-shrink-0"
                                v-if="!isSidebarCollapsed"
                            >
                                <span class="text-[14px] text-figma-notation group-hover:text-figma-text transition-colors ml-6">基础配置</span>
                                <svg class="w-3 h-3 text-figma-notation transition-transform duration-300" :class="isPlatformManagementExpanded ? '' : '-rotate-90'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path></svg>
                            </div>

                            <div v-show="isPlatformManagementExpanded || isSidebarCollapsed" class="flex flex-col gap-0.5" :class="isSidebarCollapsed ? '' : 'ml-11'">
                                <div v-for="item in [
                                    {name: '模型管理', view: 'model'},
                                    {name: '工作流', view: 'workflow'}
                                ]" :key="item.name"
                                    @click="currentView = item.view"
                                    class="h-[38px] flex items-center rounded-lg transition-all cursor-pointer"
                                    :class="[
                                        currentView === item.view ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                                        isSidebarCollapsed ? 'w-10 justify-center' : 'px-2'
                                    ]"
                                >
                                    <span v-if="!isSidebarCollapsed" class="text-[14px] transition-colors" :class="currentView === item.view ? 'text-figma-text font-medium' : 'text-figma-notation'">{{ item.name }}</span>
                                    <div v-else class="w-1.5 h-1.5 rounded-full" :class="currentView === item.view ? 'bg-blue-500' : 'bg-figma-disable'"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
             </template>

             <!-- Knowledge Tab Content -->
             <template v-else-if="sidebarTab === 'knowledge'">
                <div class="flex flex-col gap-1" :class="isSidebarCollapsed ? 'items-center' : ''">
                    <!-- Knowledge Graph -->
                    <div 
                        @click="currentView = 'knowledge_graph'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px]"
                        :class="[
                            currentView === 'knowledge_graph' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            isSidebarCollapsed ? 'w-10 justify-center' : 'px-2 mx-1 gap-2'
                        ]"
                    >
                        <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="4" cy="4" r="2" :stroke="currentView === 'knowledge_graph' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <circle cx="12" cy="5" r="2" :stroke="currentView === 'knowledge_graph' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <circle cx="8" cy="12" r="2" :stroke="currentView === 'knowledge_graph' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M5.5 5L10.5 5.5" :stroke="currentView === 'knowledge_graph' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M5 5.5L7 10.5" :stroke="currentView === 'knowledge_graph' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M11 6L9 10.5" :stroke="currentView === 'knowledge_graph' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                            </svg>
                        </div>
                        <span v-if="!isSidebarCollapsed" class="text-[14px] leading-none transition-colors" :class="currentView === 'knowledge_graph' ? 'text-figma-text font-medium' : 'text-figma-notation group-hover:text-figma-text'">知识图谱</span>
                    </div>

                    <div 
                        @click="currentView = 'knowledge'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px]"
                        :class="[
                            currentView === 'knowledge' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            isSidebarCollapsed ? 'w-10 justify-center' : 'px-2 mx-1 gap-2'
                        ]"
                    >
                        <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M10.6667 2H7.33334V14H10.6667V2Z" :stroke="currentView === 'knowledge' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linejoin="round"/>
                                <path d="M14 2H10.6667V14H14V2Z" :stroke="currentView === 'knowledge' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linejoin="round"/>
                                <path d="M3.33333 2L6 2.33333L4.83333 14L2 13.6667L3.33333 2Z" :stroke="currentView === 'knowledge' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linejoin="round"/>
                                <path d="M12.3333 6V5" :stroke="currentView === 'knowledge' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M9 6V5" :stroke="currentView === 'knowledge' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <span v-if="!isSidebarCollapsed" class="text-[14px] leading-none transition-colors" :class="currentView === 'knowledge' ? 'text-figma-text font-medium' : 'text-figma-notation group-hover:text-figma-text'">知识库</span>
                    </div>

                    <!-- Database -->
                    <div 
                        @click="currentView = 'database'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px]"
                        :class="[
                            currentView === 'database' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            isSidebarCollapsed ? 'w-10 justify-center' : 'px-2 mx-1 gap-2'
                        ]"
                    >
                        <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <ellipse cx="8" cy="4" rx="6" ry="2" :stroke="currentView === 'database' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M2 4V12C2 13.1046 4.68629 14 8 14C11.3137 14 14 13.1046 14 12V4" :stroke="currentView === 'database' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M2 8C2 9.10457 4.68629 10 8 10C11.3137 10 14 9.10457 14 8" :stroke="currentView === 'database' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                            </svg>
                        </div>
                        <span v-if="!isSidebarCollapsed" class="text-[14px] leading-none transition-colors" :class="currentView === 'database' ? 'text-figma-text font-medium' : 'text-figma-notation group-hover:text-figma-text'">数据库</span>
                    </div>

                    <!-- Audio/Video Library -->
                    <div 
                        @click="currentView = 'media_library'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px]"
                        :class="[
                            currentView === 'media_library' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            isSidebarCollapsed ? 'w-10 justify-center' : 'px-2 mx-1 gap-2'
                        ]"
                    >
                        <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect x="2" y="3" width="12" height="10" rx="2" :stroke="currentView === 'media_library' ? '#171717' : '#858B9B'" stroke-width="1.3"/>
                                <path d="M7 6L10 8L7 10V6Z" :fill="currentView === 'media_library' ? '#171717' : '#858B9B'"/>
                            </svg>
                        </div>
                        <span v-if="!isSidebarCollapsed" class="text-[14px] leading-none transition-colors" :class="currentView === 'media_library' ? 'text-figma-text font-medium' : 'text-figma-notation group-hover:text-figma-text'">音视频库</span>
                    </div>

                    <!-- Graph Export -->
                    <div 
                        @click="currentView = 'graph_export'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px]"
                        :class="[
                            currentView === 'graph_export' ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10' : 'hover:bg-gradient-to-r hover:from-blue-500/5 hover:to-indigo-500/5',
                            isSidebarCollapsed ? 'w-10 justify-center' : 'px-2 mx-1 gap-2'
                        ]"
                    >
                        <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M14 10V12.6667C14 13.403 13.403 14 12.6667 14H3.33333C2.59695 14 2 13.403 2 12.6667V10" :stroke="currentView === 'graph_export' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M8 10V2" :stroke="currentView === 'graph_export' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M5.33334 4.66667L8.00001 2L10.6667 4.66667" :stroke="currentView === 'graph_export' ? '#171717' : '#858B9B'" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <span v-if="!isSidebarCollapsed" class="text-[14px] leading-none transition-colors" :class="currentView === 'graph_export' ? 'text-figma-text font-medium' : 'text-figma-notation group-hover:text-figma-text'">图谱导入</span>
                    </div>
                </div>
             </template>

        </div>

        <!-- User Profile -->
        <div class="mt-auto border-t border-figma-line p-3">
            <div 
                class="flex items-center transition-all duration-300"
                :class="isSidebarCollapsed ? 'justify-center' : 'px-2 py-2 rounded-xl hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-indigo-500/10 cursor-pointer group gap-3'"
            >
                <!-- Avatar -->
                <div 
                    class="w-10 h-10 flex items-center justify-center flex-shrink-0 overflow-hidden transition-all duration-300"
                    :class="isSidebarCollapsed ? 'rounded-xl bg-figma-avatar-bg' : 'rounded-full bg-slate-100 border-2 border-white shadow-sm'"
                >
                    <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Admin" alt="avatar" class="w-full h-full object-cover" />
                </div>
                
                <!-- Info -->
                <div v-if="!isSidebarCollapsed" class="flex flex-col overflow-hidden flex-1 gap-[5px]">
                    <span class="text-[14px] font-bold text-figma-text truncate">管理员</span>
                    <span class="text-xs text-figma-notation truncate">数字化转型研发部</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto bg-white custom-scrollbar">
      <div class="max-w-[1200px] mx-auto px-10 py-12" :class="{
        'h-full flex flex-col !p-0 !max-w-none': currentView === 'chat',
        'h-full flex flex-col': currentView === 'knowledge',
        'h-full flex flex-col !p-4 !max-w-none': false,
        'h-full flex flex-col !p-0 !max-w-none': currentView === 'media_library' || currentView === 'database' || currentView === 'knowledge_graph' || currentView === 'knowledge'
      }">
        <!-- Main Content Area -->
        <RecordingList v-if="currentView === 'list'" @view-detail="viewDetail" />

<!-- File List Removed -->

<!-- Modals Removed -->

    <!-- Detail View -->
    <RecordingDetail v-else-if="currentView === 'detail'" :recording="selectedRecording" @back="currentView = 'list'" />

    <!-- Metrics View -->
    <MetricsExtraction v-else-if="currentView === 'metrics'" :prefilled-indicator="prefilledIndicator" />

    <!-- Indicator Management View -->
    <IndicatorManagement v-else-if="currentView === 'indicators'" @navigate-to-extraction="handleNavigateToExtraction" />

    <!-- Data Query View -->
    <SmartDataQuery v-else-if="currentView === 'data_query'" />
                
    <SmartQA v-else-if="currentView === 'chat'" :session-id="currentSessionId" @refresh-sessions="fetchSessions" />

    <KnowledgeBase v-else-if="currentView === 'knowledge'" />

    <KnowledgeGraphView v-else-if="currentView === 'knowledge_graph'" initial-scope="global" />

    <DatabaseManagement v-else-if="currentView === 'database'" />

    <MediaLibrary v-else-if="currentView === 'media_library'" />

    <GraphExportConfig v-else-if="currentView === 'graph_export'" />

    <ModelManagement v-else-if="currentView === 'model'" />
    
    <!-- Search View -->
    <SearchAgent v-else-if="currentView === 'search'" />

    <!-- Agent Management View -->
    <AgentManagement v-else-if="currentView === 'agent'" />

    <!-- Workflow Integration View -->
    <WorkflowManagement v-else-if="currentView === 'workflow'" />

<!-- Recorder Removed -->

    <!-- All Sessions Modal -->
    <a-modal 
        v-model:open="allSessionsModalVisible" 
        title="全部任务记录" 
        :footer="null"
        width="600px"
        destroyOnClose
    >
        <div class="py-4 flex flex-col gap-4">
            <a-input 
                v-model:value="sessionSearchKeyword" 
                placeholder="搜索任务名称..." 
                allow-clear
            >
                <template #prefix>
                    <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                </template>
            </a-input>
            
            <div class="max-h-[400px] overflow-y-auto custom-scrollbar flex flex-col gap-1 pr-1">
                <div v-if="filteredSessions.length === 0" class="text-center py-10 text-slate-400 italic">
                    未找到相关任务
                </div>
                <div 
                    v-for="session in filteredSessions" 
                    :key="session.id"
                    @click="selectSession(session.id)"
                    class="px-4 py-3 rounded-xl border border-transparent transition-all cursor-pointer flex items-center justify-between group"
                    :class="currentSessionId === session.id ? 'bg-blue-50 border-blue-100 text-blue-700' : 'hover:bg-slate-50 text-slate-600'"
                >
                    <div class="flex items-center gap-3 overflow-hidden">
                        <svg class="w-4 h-4 flex-shrink-0" :class="currentSessionId === session.id ? 'text-blue-500' : 'text-slate-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                        <span class="text-sm font-medium truncate">{{ session.title || '新对话' }}</span>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">{{ formatDate(session.updated_at) }}</span>
                        <button 
                            @click.stop="deleteSession(session.id)"
                            class="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                        >
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path></svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </a-modal>

    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineAsyncComponent } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';

// Async Components
const RecordingList = defineAsyncComponent(() => import('@/features/recording/components/RecordingList.vue'));
const RecordingDetail = defineAsyncComponent(() => import('@/features/recording/components/RecordingDetail.vue'));
const MediaLibrary = defineAsyncComponent(() => import('@/features/recording/components/MediaLibrary.vue'));
const SearchAgent = defineAsyncComponent(() => import('@/features/search/components/SearchAgent.vue'));
const MetricsExtraction = defineAsyncComponent(() => import('@/features/analytics/components/MetricsExtraction.vue'));
const IndicatorManagement = defineAsyncComponent(() => import('@/features/analytics/components/IndicatorManagement.vue'));
const SmartDataQuery = defineAsyncComponent(() => import('@/features/analytics/components/SmartDataQuery.vue'));
const SmartQA = defineAsyncComponent(() => import('@/features/qa/components/SmartQA.vue'));
const KnowledgeBase = defineAsyncComponent(() => import('@/features/knowledge/components/KnowledgeBase.vue'));
const KnowledgeGraphView = defineAsyncComponent(() => import('@/features/knowledge/components/KnowledgeGraphView.vue'));
const GraphExportConfig = defineAsyncComponent(() => import('@/features/knowledge/components/GraphExportConfig.vue'));
const ModelManagement = defineAsyncComponent(() => import('@/features/system/components/ModelManagement.vue'));
const DatabaseManagement = defineAsyncComponent(() => import('@/features/system/components/DatabaseManagement.vue'));
const AgentManagement = defineAsyncComponent(() => import('@/features/agent/components/AgentManagement.vue'));
const WorkflowManagement = defineAsyncComponent(() => import('@/features/workflow/components/WorkflowManagement.vue'));

// Setup Axios
const api = axios.create({
    baseURL: '/api/v1'
});

const getPageTitle = computed(() => {
    switch (currentView.value) {
        case 'metrics': return '指标提取';
        case 'indicators': return '指标管理';
        case 'data_query': return '智能问数';
        case 'search': return '智能爬取';
        case 'chat': return '智能问答';
        case 'knowledge': return '知识库';
        case 'knowledge_graph': return '知识图谱';
        case 'graph_export': return '图谱导入';
        case 'database': return '数据库';
        case 'media_library': return '音视频库';
        case 'model': return '模型管理';
        case 'agent': return '智能体管理';
        case 'workflow': return '工作流集成';
        case 'list': return '录音纪要';
        case 'detail': return '录音详情';
        default: return '智能应用';
    }
});

const getPageSubtitle = computed(() => {
    switch (currentView.value) {
        case 'metrics': return '自动化数据洞察与分析';
        case 'indicators': return '统一管理和维护业务指标体系';
        case 'data_query': return '数据智能查询与分析';
        case 'search': return '自动化智能网页数据爬取与分析';
        case 'chat': return '您的专属 AI 智能助手';
        case 'knowledge': return '企业级知识沉淀与管理';
        case 'knowledge_graph': return '可视化展示知识关联';
        case 'graph_export': return '结构化数据导入图谱';
        case 'database': return '统一数据存储与管理';
        case 'media_library': return '音视频资源集中管理';
        case 'model': return '配置和管理大语言模型';
        case 'agent': return '基于 Agno 框架构建和管理智能体';
        case 'workflow': return '集成 N8N 流程引擎实现自动化工作流';
        case 'list': return '智能识别整理，会议提效神器';
        case 'detail': return '查看录音详情与转写结果';
        default: return '赋能工作，智享生活';
    }
});

const isSidebarCollapsed = ref(false);
const mobileMenuOpen = ref(false);
const currentView = ref('chat');
const sidebarTab = ref('task');
const isAppsExpanded = ref(true);
const isAgentAppsExpanded = ref(true);
const isDocProcessingExpanded = ref(true);
const isContentCreationExpanded = ref(true);
const isDataAnalyticsExpanded = ref(true);
const isPlatformManagementExpanded = ref(true);
const isAgentPlatformExpanded = ref(false);

// Session Management
const sessions = ref([]);
const currentSessionId = ref(null);
const allSessionsModalVisible = ref(false);
const sessionSearchKeyword = ref('');

const fetchSessions = async () => {
    try {
        const res = await api.get('/chat/sessions');
        sessions.value = res.data;
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    }
};

const selectSession = (id) => {
    currentSessionId.value = id;
    currentView.value = 'chat';
    allSessionsModalVisible.value = false;
};

const deleteSession = async (id) => {
    try {
        await api.delete(`/chat/sessions/${id}`);
        sessions.value = sessions.value.filter(s => s.id !== id);
        if (currentSessionId.value === id) {
            currentSessionId.value = null;
        }
        message.success("删除成功");
    } catch (e) {
        message.error("删除失败");
    }
};

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
        message.error("创建任务失败");
    }
};

const selectedRecording = ref(null);
const prefilledIndicator = ref(null);

const mobileMenuClick = (view) => {
    currentView.value = view;
    if (view === 'knowledge') {
        sidebarTab.value = 'knowledge';
    }
    mobileMenuOpen.value = false;
};

const viewDetail = async (file) => {
    try {
        const res = await api.get(`/recordings/${file.id}`);
        selectedRecording.value = res.data;
        currentView.value = 'detail';
    } catch (e) {
        if (e.response && e.response.status === 404) {
            message.warning("文件不存在或数据库已重置");
        } else {
            message.error("获取详情失败");
        }
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

const handleNavigateToExtraction = (indicator) => {
    prefilledIndicator.value = indicator;
    currentView.value = 'metrics';
};

onMounted(() => {
    fetchSessions();
});
</script>

<style>
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 10px;
}

.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: #E2E8F0;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #CBD5E0;
}
</style>
