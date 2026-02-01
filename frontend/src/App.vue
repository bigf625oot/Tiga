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

            <div class="px-4 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">任务</div>
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
            <div class="px-4 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">智能体应用</div>
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
                <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-xs">📈</div>
                <span class="text-sm font-semibold">智能问数</span>
            </div>

            <div class="h-px bg-slate-100 my-2"></div>
            <div class="px-4 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">智能体平台</div>
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
            <div class="px-4 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">知识中心</div>
            <div 
                class="px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('knowledge')"
            >
                <div class="w-7 h-7 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-xs">📚</div>
                <span class="text-sm font-semibold">知识库</span>
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
            <button @click="isSidebarCollapsed = !isSidebarCollapsed" class="p-1.5 rounded-lg hover:bg-figma-hover text-figma-notation transition-colors flex-shrink-0">
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
                class="w-full flex items-center gap-2 py-2 bg-figma-gray hover:bg-[#DCDCDC] text-figma-text rounded-lg transition-all duration-200 group px-2 h-[38px]"
            >
                <div class="w-4 h-4 flex items-center justify-center flex-shrink-0">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 8H13" stroke="#171717" stroke-width="1.3" stroke-linecap="round"/>
                        <path d="M8.005 3.005L8.005 13.005" stroke="#171717" stroke-width="1.3" stroke-linecap="round"/>
                    </svg>
                </div>
                <span class="text-sm font-medium">新任务</span>
            </button>
            <div v-else class="flex justify-center">
                <button 
                    @click="createNewChat"
                    class="w-10 h-10 bg-figma-gray hover:bg-[#DCDCDC] text-figma-text rounded-xl flex items-center justify-center transition-all duration-200"
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
                    :class="sidebarTab === 'task' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-figma-hover'"
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
                    :class="sidebarTab === 'agent' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-figma-hover'"
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
                    :class="sidebarTab === 'knowledge' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-figma-hover'"
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
                    :class="sidebarTab === 'task' ? 'bg-white border border-figma-line shadow-sm text-figma-text' : 'text-figma-notation hover:bg-figma-hover'"
                >
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 7.33333L7.33333 8.66667L10.3333 5.66667M6.6 12.8L7.57333 14.0978C7.71808 14.2908 7.79045 14.3873 7.87918 14.4218C7.95689 14.452 8.04311 14.452 8.12082 14.4218C8.20955 14.3873 8.28192 14.2908 8.42667 14.0978L9.4 12.8C9.59543 12.5394 9.69315 12.4091 9.81234 12.3097C9.97126 12.177 10.1589 12.0832 10.3603 12.0357C10.5114 12 10.6743 12 11 12C11.9319 12 12.3978 12 12.7654 11.8478C13.2554 11.6448 13.6448 11.2554 13.8478 10.7654C14 10.3978 14 9.93188 14 9V5.2C14 4.0799 14 3.51984 13.782 3.09202C13.5903 2.71569 13.2843 2.40973 12.908 2.21799C12.4802 2 11.9201 2 10.8 2H5.2C4.0799 2 3.51984 2 3.09202 2.21799C2.71569 2.40973 2.40973 2.71569 2.21799 3.09202C2 3.51984 2 4.07989 2 5.2V9C2 9.93188 2 10.3978 2.15224 10.7654C2.35523 11.2554 2.74458 11.6448 3.23463 11.8478C3.60218 12 4.06812 12 5 12C5.32572 12 5.48858 12 5.63967 12.0357C5.84113 12.0832 6.02874 12.177 6.18766 12.3097C6.30685 12.4091 6.40457 12.5394 6.6 12.8Z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <!-- Agent Icon -->
                <div 
                    @click="sidebarTab = 'agent'"
                    class="w-10 h-10 flex items-center justify-center cursor-pointer rounded-xl transition-colors"
                    :class="sidebarTab === 'agent' ? 'bg-white border border-figma-line shadow-sm text-figma-text' : 'text-figma-notation hover:bg-figma-hover'"
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
                    :class="sidebarTab === 'knowledge' ? 'bg-white border border-figma-line shadow-sm text-figma-text' : 'text-figma-notation hover:bg-figma-hover'"
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
                    <div v-if="sessions.length === 0" class="px-4 py-8 text-center text-slate-300 italic text-sm">暂无任务记录</div>
                    <div 
                        v-for="session in topSessions" 
                        :key="session.id"
                        @click="selectSession(session.id)"
                        class="group transition-all cursor-pointer relative rounded-lg"
                        :class="[
                            currentSessionId === session.id && currentView === 'chat' ? 'bg-figma-hover' : 'hover:bg-figma-hover/50',
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
                                <span class="text-[13px] leading-tight text-figma-notation truncate group-hover:text-figma-text transition-colors" :class="currentSessionId === session.id && currentView === 'chat' ? 'text-figma-text font-medium' : ''">{{ session.title || '新对话' }}</span>
                                <span class="text-[11px] text-figma-disable mt-0.5">{{ formatDate(session.updated_at).split(' ')[0] }}</span>
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
                        class="mx-1 px-2 py-2.5 flex items-center gap-1 cursor-pointer hover:bg-figma-hover/50 rounded-lg transition-colors mt-1"
                    >
                        <div class="w-3 h-3 flex items-center justify-center ml-0.5">
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M2 4H14M2 8H14M2 12H14" stroke="#2A2F3C" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <span class="text-[13px] text-figma-heading font-medium">查看更多</span>
                    </div>
                </div>
                
        <!-- Collapsed state sessions -->
                <div v-if="isSidebarCollapsed" class="flex flex-col gap-2 px-2">
                     <div 
                        v-for="session in topSessions" 
                        :key="session.id"
                        @click="selectSession(session.id)"
                        class="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer transition-all duration-200 relative group"
                        :class="currentSessionId === session.id && currentView === 'chat' ? 'bg-white border border-figma-line shadow-sm' : 'hover:bg-figma-hover'"
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
                            currentView === 'agent' ? 'bg-figma-bg' : 'hover:bg-figma-hover/50',
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
                                currentView === 'search' ? 'bg-figma-gray' : 'hover:bg-figma-hover/50',
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
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-figma-hover/30 rounded-lg group flex-shrink-0"
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
                                        currentView === item.view ? 'bg-figma-gray' : 'hover:bg-figma-hover/50',
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
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-figma-hover/30 rounded-lg group flex-shrink-0"
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
                                        (currentView === item.view || (item.view === 'list' && currentView === 'detail')) ? 'bg-figma-gray' : 'hover:bg-figma-hover/50',
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
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-figma-hover/30 rounded-lg group flex-shrink-0"
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
                                        currentView === 'data_query' ? 'bg-figma-gray' : 'hover:bg-figma-hover/50',
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
                                class="px-3 h-[38px] flex items-center justify-between cursor-pointer hover:bg-figma-hover/30 rounded-lg group flex-shrink-0"
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
                                        currentView === item.view ? 'bg-figma-gray' : 'hover:bg-figma-hover/50',
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
                    <div 
                        @click="currentView = 'knowledge'"
                        class="group transition-all cursor-pointer flex items-center rounded-lg h-[38px]"
                        :class="[
                            currentView === 'knowledge' ? 'bg-figma-bg' : 'hover:bg-figma-hover/50',
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
                </div>
             </template>

        </div>

        <!-- User Profile -->
        <div class="mt-auto border-t border-figma-line p-3">
            <div 
                class="flex items-center transition-all duration-300"
                :class="isSidebarCollapsed ? 'justify-center' : 'px-2 py-2 rounded-xl hover:bg-figma-hover cursor-pointer group gap-3'"
            >
                <!-- Avatar -->
                <div 
                    class="w-10 h-10 flex items-center justify-center flex-shrink-0 overflow-hidden transition-all duration-300"
                    :class="isSidebarCollapsed ? 'rounded-xl bg-figma-avatar-bg' : 'rounded-full bg-slate-100 border-2 border-white shadow-sm'"
                >
                    <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Admin" alt="avatar" class="w-full h-full object-cover" />
                </div>
                
                <!-- Info -->
                <div v-if="!isSidebarCollapsed" class="flex flex-col overflow-hidden flex-1">
                    <span class="text-[13px] font-bold text-figma-text truncate">管理员</span>
                    <span class="text-[11px] text-figma-notation truncate">数字化转型研发部</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto bg-slate-50">
      <div class="max-w-[1200px] mx-auto px-10 py-12" :class="currentView === 'chat' ? 'h-full flex flex-col !p-0 !max-w-none' : ''">
        <!-- Main Content Area -->
        <div v-if="currentView === 'list'" class="flex-1">
        <div class="grid grid-cols-2 gap-6 mb-12 max-w-[840px]">
            <!-- Start Recording Card -->
            <div @click="openRecorder" class="relative group overflow-hidden bg-white rounded-[24px] p-8 border border-slate-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] hover:shadow-[0_20px_40px_rgba(59,130,246,0.1)] hover:border-blue-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col items-center justify-center gap-4 h-[200px]">
                <div class="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-110 group-hover:shadow-blue-500/40 transition-all duration-300 ring-4 ring-blue-50/50">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                </div>
                <div class="relative flex flex-col items-center gap-1.5">
                    <span class="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors tracking-tight">发起录音速记</span>
                </div>
            </div>

            <!-- Upload Audio Card -->
            <div @click="triggerUpload" class="relative group overflow-hidden bg-white rounded-[24px] p-8 border border-slate-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] hover:shadow-[0_20px_40px_rgba(59,130,246,0.1)] hover:border-blue-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col items-center justify-center gap-4 h-[200px]">
                <div class="relative w-16 h-16 rounded-2xl bg-white border border-slate-100 flex items-center justify-center shadow-sm group-hover:border-blue-200 group-hover:scale-110 transition-all duration-300">
                     <svg class="relative z-10 text-blue-500" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                </div>
                <div class="relative flex flex-col items-center gap-1.5">
                    <span class="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors tracking-tight">上传本地音频</span>
                </div>
                <input type="file" ref="fileInput" class="hidden" accept="audio/*" @change="handleFileUpload">
            </div>
        </div>

        <!-- File List -->
        <div class="w-full">
            <div class="flex justify-between items-center mb-3 px-2">
                <div class="flex items-center gap-3">
                    <button v-if="currentFolderId" @click="goUp" class="text-slate-500 hover:text-blue-600 flex items-center justify-center w-8 h-8 rounded-lg hover:bg-slate-100 transition-colors">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    </button>
                    <div class="h-4 w-px bg-slate-200" v-if="currentFolderId"></div>
                    <h2 class="text-base font-bold text-slate-800 leading-none mb-0">{{ currentFolderId ? currentFolderName : '全部文件' }}</h2>
                </div>
                <button @click="createFolder" class="text-sm bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 font-medium">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>
                    新建文件夹
                </button>
            </div>

            <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div class="grid grid-cols-12 gap-4 px-6 py-3.5 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div class="col-span-4 pl-2">文件名称</div>
                    <div class="col-span-1 text-center">时长</div>
                    <div class="col-span-3 text-center">处理流水线 (上传-转写-摘要)</div>
                    <div class="col-span-2 text-center">创建时间</div>
                    <div class="col-span-2 text-center">操作</div>
                </div>
                
                <div v-if="loading" class="text-center py-12 text-slate-400">
                    <svg class="animate-spin h-8 w-8 mx-auto mb-3 text-blue-500 opacity-50" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span class="text-sm font-medium">加载数据中...</span>
                </div>
                <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center py-20 text-slate-300 bg-white">
                    <div class="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 border border-slate-100">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-50"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
                    </div>
                    <span class="text-xs font-medium text-slate-400">暂无文件</span>
                </div>
                
                <div v-else class="divide-y divide-slate-50">
                    <div v-for="file in files" :key="file.id" class="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-slate-50 transition-all items-center group bg-white">
                        <!-- Name -->
                        <div class="col-span-4 flex items-center gap-3 overflow-hidden">
                            <div v-if="file.is_folder" class="w-9 h-9 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center flex-shrink-0 border border-amber-100 shadow-sm">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                            </div>
                            <div v-else class="w-9 h-9 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center flex-shrink-0 border border-blue-100 shadow-sm">
                                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                            </div>
                            <span class="text-sm font-medium text-slate-700 truncate cursor-pointer hover:text-blue-600 transition-colors" @click="handleItemClick(file)">{{ file.filename }}</span>
                        </div>
                        
                        <!-- Duration -->
                        <div class="col-span-1 text-center text-sm text-slate-500 font-din font-medium">{{ file.is_folder ? '-' : formatDuration(file.duration) }}</div>
                        
                        <!-- Pipeline Status -->
                        <div class="col-span-3 flex items-center justify-center gap-2">
                            <span v-if="file.is_folder" class="text-slate-300">-</span>
                            <template v-else>
                                <!-- Upload -->
                                <div class="relative group/tooltip">
                                    <div class="w-5 h-5 rounded-full flex items-center justify-center border transition-all" :class="[getStatusStyle(file.upload_status).bg, getStatusStyle(file.upload_status).text, getStatusStyle(file.upload_status).border]">
                                        <svg v-if="file.upload_status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        <svg v-else-if="file.upload_status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
                                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                                    </div>
                                    <!-- Tooltip -->
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">上传</div>
                                </div>
                                <!-- Arrow -->
                                <svg class="w-2.5 h-2.5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                                
                                <!-- ASR -->
                                <div class="relative group/tooltip">
                                    <div class="w-5 h-5 rounded-full flex items-center justify-center border transition-all" :class="[getStatusStyle(file.asr_status).bg, getStatusStyle(file.asr_status).text, getStatusStyle(file.asr_status).border]">
                                        <svg v-if="file.asr_status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        <svg v-else-if="file.asr_status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
                                    </div>
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">转写</div>
                                </div>
                                <!-- Arrow -->
                                <svg class="w-2.5 h-2.5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                                
                                <!-- Summary -->
                                <div class="relative group/tooltip">
                                    <div class="w-5 h-5 rounded-full flex items-center justify-center border transition-all" :class="[getStatusStyle(file.summary_status).bg, getStatusStyle(file.summary_status).text, getStatusStyle(file.summary_status).border]">
                                        <svg v-if="file.summary_status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        <svg v-else-if="file.summary_status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                                    </div>
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">摘要</div>
                                </div>
                            </template>
                        </div>
                        
                        <!-- Time -->
                        <div class="col-span-2 text-center text-xs text-slate-400 font-din">{{ formatDate(file.created_at) }}</div>
                        
                        <!-- Actions -->
                        <div class="col-span-2 flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button v-if="!file.is_folder" class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-blue-50 hover:text-blue-600 transition-all" title="查看详情" @click="viewDetail(file)">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            </button>
                            <button class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-blue-50 hover:text-blue-600 transition-all" title="重命名" @click="openRenameModal(file)">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            </button>
                            <a-popconfirm
                                title="确定要删除吗?"
                                ok-text="确认"
                                cancel-text="取消"
                                @confirm="deleteRecording(file.id)"
                            >
                                <button class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-red-50 hover:text-red-500 transition-all" title="删除">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                </button>
                            </a-popconfirm>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Folder Modal -->
        <a-modal v-model:open="createFolderModalVisible" title="新建文件夹" @ok="handleCreateFolderConfirm">
            <div class="py-4">
                <a-input 
                    v-model:value="newFolderName" 
                    placeholder="请输入文件夹名称" 
                    :status="folderNameError ? 'error' : ''"
                    @pressEnter="handleCreateFolderConfirm"
                    auto-focus
                />
                <div v-if="folderNameError" class="text-red-500 text-xs mt-1">{{ folderNameError }}</div>
            </div>
        </a-modal>

        <!-- Move Modal -->
        <a-modal v-model:open="moveModalVisible" title="移动到文件夹" @ok="handleMove">
            <div class="py-4">
                <p class="mb-2 text-gray-500">选择目标文件夹：</p>
                <a-select v-model:value="selectedTargetFolder" style="width: 100%">
                    <a-select-option :value="null">根目录 (Root)</a-select-option>
                    <a-select-option v-for="folder in availableFolders" :key="folder.id" :value="folder.id">{{ folder.filename }}</a-select-option>
                </a-select>
            </div>
        </a-modal>

        <!-- Rename Modal -->
        <a-modal v-model:open="renameModalVisible" title="重命名" @ok="handleRename">
            <div class="py-4">
                <a-input 
                    v-model:value="renameValue" 
                    placeholder="请输入新名称" 
                    @pressEnter="handleRename"
                    auto-focus
                />
            </div>
        </a-modal>
    </div>

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

    <ModelManagement v-else-if="currentView === 'model'" />
    
    <!-- Search View -->
    <SearchAgent v-else-if="currentView === 'search'" />

    <!-- Agent Management View -->
    <AgentManagement v-else-if="currentView === 'agent'" />

    <!-- Workflow Integration View -->
    <WorkflowManagement v-else-if="currentView === 'workflow'" />

    <!-- Recorder Component -->
    <Recorder v-if="showRecorder" @close="showRecorder = false" @finish="handleFinish" />

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
                        <span class="text-[11px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">{{ formatDate(session.updated_at) }}</span>
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
import { ref, onMounted, computed } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';
import Recorder from './components/Recorder.vue';
import RecordingDetail from './components/RecordingDetail.vue';
import SearchAgent from './components/SearchAgent.vue';
import MetricsExtraction from './components/MetricsExtraction.vue';
import SmartQA from './components/SmartQA.vue';
import KnowledgeBase from './components/KnowledgeBase.vue';
import ModelManagement from './components/ModelManagement.vue';
import AgentManagement from './components/AgentManagement.vue';
import WorkflowManagement from './components/WorkflowManagement.vue';
import IndicatorManagement from './components/IndicatorManagement.vue';
import SmartDataQuery from './components/SmartDataQuery.vue';

// Setup Axios
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1' // Adjust port if needed (uvicorn default 8000)
});

const getPageTitle = computed(() => {
    switch (currentView.value) {
        case 'metrics': return '指标提取';
        case 'indicators': return '指标管理';
        case 'data_query': return '智能问数';
        case 'search': return '智能爬取';
        case 'chat': return '智能问答';
        case 'knowledge': return '知识库';
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
const sidebarTab = ref('task'); // New state for sidebar tabs
const newChatCounter = ref(0);
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
        sidebarTab.value = 'task'; // Ensure task tab is active
    } catch (e) {
        message.error("创建任务失败");
    }
};
const showRecorder = ref(false);
const files = ref([]);
const loading = ref(false);
const fileInput = ref(null);
const selectedRecording = ref(null);
const prefilledIndicator = ref(null); // New state to pass indicator data

// Folder Logic
const currentFolderId = ref(null);
const currentFolderName = ref('');
const moveModalVisible = ref(false);
const createFolderModalVisible = ref(false);
const renameModalVisible = ref(false);
const newFolderName = ref('');
const folderNameError = ref('');
const itemToMove = ref(null);
const itemToRename = ref(null);
const renameValue = ref('');
const selectedTargetFolder = ref(null);
const allFolders = ref([]); // Cache all folders for move selector (simplified)

const mobileMenuClick = (view) => {
    currentView.value = view;
    if (view === 'knowledge') {
        sidebarTab.value = 'knowledge';
    }
    mobileMenuOpen.value = false;
};

const fetchRecordings = async () => {
    loading.value = true;
    try {
        const params = {};
        if (currentFolderId.value) params.parent_id = currentFolderId.value;
        const res = await api.get('/recordings/', { params });
        files.value = res.data;
        
        // Also fetch all folders for move list (not efficient for large scale but ok for demo)
        // In real app, this should be a separate API or cached
        // For now, we only show folders in CURRENT list + Root in the move modal
        // To do it properly, we should fetch all folders. 
        // Let's just fetch root folders for simplicity or implement a proper folder tree API.
        // Or simply: When opening move modal, fetch all folders.
    } catch (e) {
        message.error("获取列表失败");
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const handleItemClick = (file) => {
    if (file.is_folder) {
        currentFolderId.value = file.id;
        currentFolderName.value = file.filename;
        fetchRecordings();
    } else {
        viewDetail(file);
    }
};

const goUp = () => {
    // Ideally we should know parent of current folder. 
    // For now, simplified: just go to root. 
    // To support multi-level, we need to fetch folder details to get its parent_id.
    // Let's implement single level up if we track breadcrumbs, or just reset to root for now.
    currentFolderId.value = null; 
    currentFolderName.value = '';
    fetchRecordings();
};

const createFolder = () => {
    newFolderName.value = '';
    folderNameError.value = '';
    createFolderModalVisible.value = true;
};

const handleCreateFolderConfirm = async () => {
    const name = newFolderName.value.trim();
    
    // Validation: Empty
    if (!name) {
        folderNameError.value = "文件夹名称不能为空";
        return;
    }
    
    // Validation: Duplicate
    const isDuplicate = files.value.some(f => f.filename === name && f.is_folder);
    if (isDuplicate) {
        folderNameError.value = "该文件夹已存在";
        return;
    }
    
    try {
        await api.post('/recordings/folder', null, { params: { name, parent_id: currentFolderId.value } });
        message.success("文件夹创建成功");
        createFolderModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        message.error("创建失败");
    }
};

const openMoveModal = async (file) => {
    itemToMove.value = file;
    selectedTargetFolder.value = null;
    moveModalVisible.value = true;
    // Fetch available folders (exclude self if folder)
    try {
        const res = await api.get('/recordings/', { params: { limit: 1000 } }); // Fetch root folders for now
        // In a real app we need a recursive folder fetch. 
        // Here we just fetch root items and filter folders.
        availableFolders.value = res.data.filter(f => f.is_folder && f.id !== file.id);
    } catch(e) {}
};

const openRenameModal = (file) => {
    itemToRename.value = file;
    renameValue.value = file.filename;
    renameModalVisible.value = true;
};

const handleRename = async () => {
    if (!itemToRename.value || !renameValue.value.trim()) return;
    
    try {
        await api.put(`/recordings/${itemToRename.value.id}/rename`, null, { 
            params: { name: renameValue.value.trim() } 
        });
        message.success("重命名成功");
        renameModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        message.error("重命名失败");
    }
};

const availableFolders = ref([]);

const handleMove = async () => {
    if (!itemToMove.value) return;
    try {
        await api.put(`/recordings/${itemToMove.value.id}/move`, null, { 
            params: { target_parent_id: selectedTargetFolder.value } 
        });
        message.success("移动成功");
        moveModalVisible.value = false;
        fetchRecordings();
    } catch (e) {
        message.error("移动失败");
    }
};

const openRecorder = () => {
  showRecorder.value = true;
};

const handleFinish = async (recordData) => {
    // recordData: { blob, duration, fileName, createdAt, format }
    await uploadFileToBackend(recordData.blob, recordData.fileName, recordData.duration);
};

const triggerUpload = () => {
    fileInput.value.click();
};

const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
        // Get audio duration
        const duration = await getAudioDuration(file);
        await uploadFileToBackend(file, file.name, duration);
    }
};

const getAudioDuration = (file) => {
    return new Promise((resolve) => {
        const url = URL.createObjectURL(file);
        const audio = new Audio(url);
        audio.addEventListener('loadedmetadata', () => {
            const durationMs = Math.floor(audio.duration * 1000);
            URL.revokeObjectURL(url);
            resolve(durationMs);
        });
        audio.addEventListener('error', () => {
             URL.revokeObjectURL(url);
             resolve(0);
        });
    });
};

const uploadFileToBackend = async (fileBlob, fileName, duration) => {
    const formData = new FormData();
    // Ensure filename has extension
    formData.append('file', fileBlob, fileName); 
    formData.append('duration', duration);
    if (currentFolderId.value) {
        formData.append('parent_id', currentFolderId.value);
    }

    try {
        message.loading({ content: '上传处理中...', key: 'upload' });
        await api.post('/recordings/upload', formData);
        message.success({ content: '上传成功', key: 'upload' });
        fetchRecordings(); // Refresh list
    } catch (e) {
        message.error({ content: '上传失败', key: 'upload' });
        console.error(e);
    }
};

const deleteRecording = async (id) => {
    try {
        await api.delete(`/recordings/${id}`);
        message.success("删除成功");
        fetchRecordings();
    } catch (e) {
        message.error("删除失败");
    }
};

const viewDetail = async (file) => {
    try {
        const res = await api.get(`/recordings/${file.id}`);
        selectedRecording.value = res.data;
        currentView.value = 'detail';
    } catch (e) {
        if (e.response && e.response.status === 404) {
            message.warning("文件不存在或数据库已重置，正在刷新列表...");
            fetchRecordings();
        } else {
            message.error("获取详情失败");
        }
    }
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

const formatDuration = (ms) => {
    const durationSec = Math.floor(ms / 1000);
    const min = Math.floor(durationSec / 60);
    const sec = durationSec % 60;
    return (min > 0 ? min + "分" : "") + sec + "秒";
};

const handleNavigateToExtraction = (indicator) => {
    prefilledIndicator.value = indicator;
    currentView.value = 'metrics';
};

const statusConfig = {
    completed: { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200', icon: 'check' },
    processing: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200', icon: 'loader' },
    failed: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200', icon: 'x' },
    pending: { bg: 'bg-slate-50', text: 'text-slate-300', border: 'border-slate-200', icon: 'minus' }
};

const getStatusStyle = (status) => {
    return statusConfig[status] || statusConfig.pending;
};

onMounted(() => {
    fetchRecordings();
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
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #CBD5E0;
}
</style>
