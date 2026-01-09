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
            class="absolute bottom-16 right-0 bg-white rounded-xl shadow-xl border border-slate-100 py-2 min-w-[160px] overflow-hidden origin-bottom-right transition-all animate-in fade-in zoom-in duration-200"
        >
            <div 
                class="px-4 py-3 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('list')"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 11H5m14-7a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h14zM5 21h14"></path></svg>
                <span class="font-medium">录音纪要</span>
            </div>
            <div 
                class="px-4 py-3 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('metrics')"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"></path><path d="M12 20V4"></path><path d="M6 20v-6"></path></svg>
                <span class="font-medium">指标提取</span>
            </div>
            <div 
                class="px-4 py-3 hover:bg-slate-50 flex items-center gap-3 text-slate-700 cursor-pointer"
                @click="mobileMenuClick('search')"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span class="font-medium">网络检索</span>
            </div>
        </div>
    </div>

    <!-- Desktop Sidebar -->
    <div 
        class="hidden md:flex flex-shrink-0 bg-slate-900 text-white transition-all duration-300 flex-col"
        :class="isSidebarCollapsed ? 'w-16' : 'w-64'"
    >
        <!-- Logo Area -->
        <div class="h-16 flex items-center px-4 border-b border-slate-800">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-1.07 3.97-2.9 5.4z"/></svg>
            </div>
            <span v-if="!isSidebarCollapsed" class="ml-3 font-bold text-lg tracking-tight whitespace-nowrap overflow-hidden">智能应用</span>
        </div>

        <!-- Menu Items -->
        <div class="flex-1 py-6 overflow-y-auto">
             <div 
                class="px-3 py-2 mx-2 rounded-lg flex items-center cursor-pointer transition-colors group"
                :class="currentView === 'list' || currentView === 'detail' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
                @click="currentView = 'list'"
             >
                <div class="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 11H5m14-7a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h14zM5 21h14"></path></svg>
                </div>
                <span v-if="!isSidebarCollapsed" class="ml-3 font-medium whitespace-nowrap overflow-hidden">录音纪要</span>
             </div>
             
             <div 
                class="px-3 py-2 mx-2 rounded-lg flex items-center cursor-pointer transition-colors group"
                :class="currentView === 'metrics' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
                @click="currentView = 'metrics'"
             >
                <div class="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"></path><path d="M12 20V4"></path><path d="M6 20v-6"></path></svg>
                </div>
                <span v-if="!isSidebarCollapsed" class="ml-3 font-medium whitespace-nowrap overflow-hidden">指标提取</span>
             </div>
             
             <div 
                class="px-3 py-2 mx-2 rounded-lg flex items-center cursor-pointer transition-colors group"
                :class="currentView === 'search' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
                @click="currentView = 'search'"
             >
                <div class="w-6 h-6 flex items-center justify-center flex-shrink-0">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                </div>
                <span v-if="!isSidebarCollapsed" class="ml-3 font-medium whitespace-nowrap overflow-hidden">网络检索</span>
             </div>
        </div>

        <!-- Collapse Toggle -->
        <div class="p-4 border-t border-slate-800">
             <button @click="isSidebarCollapsed = !isSidebarCollapsed" class="w-full flex items-center justify-center p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors">
                <svg v-if="!isSidebarCollapsed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
             </button>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto bg-slate-50">
      <div class="max-w-[1200px] mx-auto px-10 py-12">
        <header class="mb-12 flex items-baseline gap-4">
        <h1 class="text-2xl font-extrabold text-slate-900 m-0 tracking-tight">{{ getPageTitle }}</h1>
        <span class="text-sm text-slate-400 font-medium">{{ getPageSubtitle }}</span>
        </header>

        <!-- Main Content Area -->
        <div v-if="currentView === 'list'">
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

            <div class="grid grid-cols-12 gap-6 px-6 py-4 bg-slate-50 rounded-t-xl text-xs font-semibold text-slate-400 tracking-wide uppercase">
                <div class="col-span-4 pl-2">文件名称</div>
                <div class="col-span-2">时长</div>
                <div class="col-span-2">状态</div>
                <div class="col-span-2">创建时间</div>
                <div class="col-span-2">操作</div>
            </div>
            
            <div v-if="loading" class="text-center py-10 text-slate-400">加载中...</div>
            <div v-else-if="files.length === 0" class="flex flex-col items-center justify-center py-16 text-slate-300">
                <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="opacity-50"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
                </div>
                <span class="text-xs font-medium">暂无文件</span>
            </div>
            
            <div v-for="file in files" :key="file.id" class="grid grid-cols-12 gap-6 px-6 py-5 border-b border-slate-100 hover:bg-slate-50/80 transition-colors items-center group">
                <div class="col-span-4 flex items-center gap-4">
                    <div v-if="file.is_folder" class="w-10 h-10 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center flex-shrink-0 border border-amber-100">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    </div>
                    <div v-else class="w-10 h-10 rounded-lg bg-green-50 text-green-500 flex items-center justify-center flex-shrink-0 border border-green-100">
                         <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                    </div>
                    <span class="text-sm font-medium text-slate-700 truncate cursor-pointer hover:text-blue-600" @click="handleItemClick(file)">{{ file.filename }}</span>
                </div>
                <div class="col-span-2 text-sm text-slate-500 font-medium font-din">{{ file.is_folder ? '-' : formatDuration(file.duration) }}</div>
                <div class="col-span-2 flex flex-col gap-1.5">
                    <span v-if="file.is_folder">-</span>
                    <template v-else>
                         <!-- Upload Status -->
                         <div class="flex items-center gap-2">
                            <span class="text-[10px] text-slate-400 w-8 font-medium">上传</span>
                            <span v-if="file.upload_status === 'completed'" class="flex items-center justify-center w-2 h-2 rounded-full bg-green-100 text-green-600">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            </span>
                            <span v-else-if="file.upload_status === 'failed'" class="flex items-center justify-center w-2 h-2 rounded-full bg-red-100 text-red-600">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </span>
                            <span v-else class="flex items-center justify-center w-2 h-2 rounded-full bg-blue-100 text-blue-600 animate-pulse">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle></svg>
                            </span>
                         </div>
                         
                         <!-- ASR Status -->
                         <div class="flex items-center gap-2">
                            <span class="text-[10px] text-slate-400 w-8 font-medium">转写</span>
                            <span v-if="file.asr_status === 'completed'" class="flex items-center justify-center w-2 h-2 rounded-full bg-green-100 text-green-600">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            </span>
                            <span v-else-if="file.asr_status === 'failed'" class="flex items-center justify-center w-2 h-2 rounded-full bg-red-100 text-red-600">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </span>
                            <span v-else-if="file.asr_status === 'processing'" class="flex items-center justify-center w-2 h-2 rounded-full bg-blue-100 text-blue-600 animate-pulse">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                            </span>
                            <span v-else class="flex items-center justify-center w-2 h-2 rounded-full bg-slate-100 text-slate-300">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle></svg>
                            </span>
                         </div>
                         
                         <!-- Summary Status -->
                         <div class="flex items-center gap-2">
                            <span class="text-[10px] text-slate-400 w-8 font-medium">摘要</span>
                            <span v-if="file.summary_status === 'completed'" class="flex items-center justify-center w-2 h-2 rounded-full bg-green-100 text-green-600">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            </span>
                            <span v-else-if="file.summary_status === 'failed'" class="flex items-center justify-center w-2 h-2 rounded-full bg-red-100 text-red-600">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </span>
                            <span v-else-if="file.summary_status === 'processing'" class="flex items-center justify-center w-2 h-2 rounded-full bg-blue-100 text-blue-600 animate-pulse">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                            </span>
                            <span v-else class="flex items-center justify-center w-2 h-2 rounded-full bg-slate-100 text-slate-300">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle></svg>
                            </span>
                         </div>
                    </template>
                </div>
                <div class="col-span-2 text-sm text-slate-400 font-din tabular-nums tracking-tight">{{ formatDate(file.created_at) }}</div>
                <div class="col-span-2 flex gap-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button v-if="!file.is_folder" class="text-slate-400 hover:text-blue-500 transition-colors" title="查看详情" @click="viewDetail(file)">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    </button>
                    <button class="text-slate-400 hover:text-blue-500 transition-colors" title="重命名" @click="openRenameModal(file)">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button class="text-slate-400 hover:text-blue-500 transition-colors" title="移动" @click="openMoveModal(file)">
                         <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="5 9 2 12 5 15"></polyline><polyline points="9 5 12 2 15 5"></polyline><polyline points="19 9 22 12 19 15"></polyline><polyline points="14 19 11 22 8 19"></polyline><line x1="2" y1="12" x2="22" y2="12"></line><line x1="12" y1="2" x2="12" y2="22"></line></svg>
                    </button>
                    <a-popconfirm
                        title="确定要删除吗?"
                        ok-text="确认"
                        cancel-text="取消"
                        @confirm="deleteRecording(file.id)"
                    >
                        <button class="text-slate-400 hover:text-red-500 transition-colors" title="删除">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        </button>
                    </a-popconfirm>
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
    <MetricsExtraction v-else-if="currentView === 'metrics'" />
    
    <!-- Search View -->
    <SearchAgent v-else-if="currentView === 'search'" />

    <!-- Recorder Component -->
    <Recorder v-if="showRecorder" @close="showRecorder = false" @finish="handleFinish" />

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

// Setup Axios
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1' // Adjust port if needed (uvicorn default 8000)
});

const getPageTitle = computed(() => {
    switch (currentView.value) {
        case 'metrics': return '指标提取';
        case 'search': return '网络检索';
        default: return '录音纪要';
    }
});

const getPageSubtitle = computed(() => {
    switch (currentView.value) {
        case 'metrics': return '自动化数据洞察与分析';
        case 'search': return '全网信息实时搜寻与聚合';
        default: return '智能识别整理，会议提效神器';
    }
});

const isSidebarCollapsed = ref(false);
const mobileMenuOpen = ref(false);
const currentView = ref('list'); // 'list' | 'detail'
const showRecorder = ref(false);
const files = ref([]);
const loading = ref(false);
const fileInput = ref(null);
const selectedRecording = ref(null);

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

onMounted(() => {
    fetchRecordings();
});
</script>
