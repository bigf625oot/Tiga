<template>
    <div v-if="visible"
        class="fixed top-0 right-0 h-full w-[650px] bg-background shadow-2xl z-50 border-l border-border animate-slide-in-right flex flex-col font-sans">
        
        <!-- Drawer Header -->
        <div class="px-6 py-4 border-b border-border flex justify-between items-center bg-background shrink-0">
            <div class="flex items-center gap-2">
                <h3 class="text-lg font-semibold text-foreground">{{ drawerTitle }}</h3>
            </div>
            <Button variant="ghost" size="icon" @click="closeDrawer">
                <X class="w-4 h-4" />
            </Button>
        </div>

        <!-- Drawer Body with Tabs -->
        <Tabs default-value="basic" class="flex-1 flex flex-col overflow-hidden">
            <div class="px-6 py-2 border-b bg-muted/5 shrink-0">
                <TabsList class="grid w-full grid-cols-3">
                    <TabsTrigger value="basic">基础设定</TabsTrigger>
                    <TabsTrigger value="capabilities">能力扩展</TabsTrigger>
                    <TabsTrigger value="scripts">用户剧本</TabsTrigger>
                </TabsList>
            </div>

            <ScrollArea class="flex-1 bg-muted/10">
                <div class="p-6 min-h-full flex flex-col">
                    <!-- Tab: Basic Settings -->
                    <TabsContent value="basic" class="mt-0 flex flex-col gap-4 pb-4 animate-fade-in">
                        <!-- Identity Section -->
                        <Card class="p-4 border-border/40 shadow-sm bg-muted/5 shrink-0">
                            <div class="flex gap-5">
                                <!-- Left: Icon -->
                                <div class="shrink-0 flex flex-col items-center gap-2 pt-1">
                                    <div class="w-20 h-20 rounded-xl border-2 border-dashed border-border/60 flex items-center justify-center overflow-hidden bg-background relative group transition-all shadow-sm"
                                        :class="isReadOnly ? 'cursor-default' : 'cursor-pointer hover:border-primary/50 hover:bg-primary/5'"
                                        @click="!isReadOnly && triggerIconUpload()"
                                        :title="isReadOnly ? '' : '点击更换图标'">
                                        <img v-if="isImageIcon(form.icon)" :src="form.icon" class="w-full h-full object-cover" />
                                        <img v-else-if="!form.icon" src="/tiga.svg" class="w-8 h-8 object-contain opacity-40 group-hover:opacity-20 transition-opacity" />
                                        <component v-else :is="getIconComponent(form.icon)" class="w-8 h-8 text-muted-foreground group-hover:text-primary/50" />
                                        
                                        <div v-if="!isReadOnly" class="absolute inset-0 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/5 backdrop-blur-[1px]">
                                            <Upload class="w-5 h-5 text-primary drop-shadow-sm mb-0.5" />
                                            <span class="text-xs font-medium text-primary bg-background/80 px-1.5 py-0.5 rounded-full">更换</span>
                                        </div>
                                    </div>
                                    <input type="file" ref="iconInput" class="hidden" accept="image/*" @change="handleIconUpload">
                                </div>

                                <!-- Right: Identity Fields -->
                                <div class="flex-1 flex flex-col gap-3">
                                    <!-- Name -->
                                    <div class="grid gap-1.5">
                                        <div class="flex justify-between items-center">
                                            <Label for="name" class="text-xs font-medium">名称 <span class="text-red-500">*</span></Label>
                                            <span class="text-xs text-muted-foreground">{{ form.name.length }}/50</span>
                                        </div>
                                        <Input id="name" v-model="form.name" :readonly="isReadOnly" maxlength="50" placeholder="智能体名称..." 
                                        class="h-8 text-sm bg-muted/20 border-border/30 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300" />
                                    </div>

                                    <!-- Description -->
                                    <div class="grid gap-1.5">
                                        <div class="flex justify-between items-center">
                                            <Label for="desc" class="text-xs font-medium">简介</Label>
                                            <span class="text-xs text-muted-foreground">{{ form.description.length }}/200</span>
                                        </div>
                                        <Textarea id="desc" v-model="form.description" :readonly="isReadOnly" maxlength="200" placeholder="简短描述它的功能..." 
                                            class="min-h-[60px] text-sm bg-muted/20 border-border/30 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300 resize-none" rows="2" />
                                    </div>
                                </div>
                            </div>
                        </Card>

                        <!-- Model Configuration Section -->
                        <Card class="p-4 border-border/40 shadow-sm bg-muted/5 shrink-0 flex flex-col gap-3">
                            <div class="flex items-center gap-2 border-b border-border/40 pb-2">
                                <div class="p-1 bg-blue-100/50 text-blue-600 rounded-md">
                                    <Bot class="w-3.5 h-3.5" />
                                </div>
                                <h4 class="font-semibold text-sm text-foreground">模型配置</h4>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-4">
                                <!-- Model Select -->
                                <div class="col-span-1 grid gap-1.5">
                                    <Label class="text-xs font-medium">基座模型</Label>
                                    <Select v-model="form.model_config.model_id" :disabled="isReadOnly">
                                        <SelectTrigger class="h-8 text-sm bg-muted/20 border-border/20 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all">
                                            <SelectValue placeholder="选择模型..." />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="default_no_selection">
                                                <span class="text-muted-foreground">不指定 (默认)</span>
                                            </SelectItem>
                                            <SelectItem v-for="m in availableModels" :key="m.model_id" :value="m.model_id">
                                                <div class="flex items-center justify-between w-full gap-2">
                                                    <span class="truncate">{{ m.name }}</span>
                                                    <Badge variant="outline" class="text-xs h-3.5 px-1 text-muted-foreground font-normal border-border/50">
                                                        {{ m.provider }}
                                                    </Badge>
                                                </div>
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <!-- Reasoning Switch -->
                                <div class="col-span-1 flex flex-col justify-end pb-1.5">
                                    <div class="flex items-center gap-2">
                                        <Switch id="reasoning" :disabled="isReadOnly" :checked="form.model_config.reasoning" @update:checked="(val) => form.model_config.reasoning = val" 
                                            class="scale-75 origin-left data-[state=checked]:bg-blue-500 hover:data-[state=checked]:bg-blue-600 transition-all shadow-sm" />
                                        <Label for="reasoning" class="text-xs text-muted-foreground cursor-pointer hover:text-foreground transition-colors select-none flex items-center gap-1.5">
                                            启用推理模式 (Chain of Thought)
                                        </Label>
                                    </div>
                                </div>
                            </div>
                        </Card>

                        <!-- System Prompt (Auto-fill) -->
                        <Card class="flex flex-col border-border/20 shadow-sm bg-blue-50/30 dark:bg-slate-900/20 backdrop-blur-sm overflow-hidden min-h-[400px] shadow-[inset_0_0_20px_rgba(0,0,0,0.02)]">
                            <div class="px-4 py-2 border-b border-border/40 bg-muted/5 flex items-center justify-between shrink-0">
                                <div class="flex items-center gap-2">
                                    <div class="p-1 bg-indigo-100/50 text-indigo-600 rounded-md">
                                        <MessageSquareCode class="w-3.5 h-3.5" />
                                    </div>
                                    <h4 class="font-semibold text-sm text-foreground">角色设定</h4>
                                </div>
                                <div class="flex items-center gap-1">
                                    <Button v-if="!isReadOnly" variant="ghost" size="sm" class="h-6 px-2 text-xs gap-1.5 text-muted-foreground hover:text-primary" title="AI 优化">
                                        <Wand2 class="w-3.5 h-3.5" />
                                        <span class="sr-only sm:not-sr-only sm:inline">优化</span>
                                    </Button>
                                    <Button variant="ghost" size="icon" class="h-6 w-6 text-muted-foreground hover:text-primary" title="复制内容">
                                        <Copy class="w-3.5 h-3.5" />
                                    </Button>
                                </div>
                            </div>
                            <div class="relative group min-h-[400px]">
                                <Textarea v-model="form.system_prompt"
                                    :readonly="isReadOnly"
                                    class="h-full min-h-[400px] w-full font-mono text-sm resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0 rounded-none bg-transparent p-4 pb-10 leading-relaxed selection:bg-primary/20"
                                    placeholder="你是一个专业的助手，请遵循以下规则：&#10;1. 始终保持礼貌&#10;2. 回答要简洁明了..." />
                                <div class="absolute bottom-2 right-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                                    <Badge variant="secondary" class="text-xs h-4 bg-muted/50 backdrop-blur-sm border-border/50">支持Markdown</Badge>
                                    <span class="text-xs text-muted-foreground">{{ form.system_prompt.length }} chars</span>
                                </div>
                            </div>
                        </Card>
                    </TabsContent>

                    <!-- Tab: Capabilities -->
                    <TabsContent value="capabilities" class="mt-0 space-y-6 animate-fade-in pb-10">
                        
                        <!-- Knowledge Base -->
                        <Card class="p-5 border-border/40 shadow-sm bg-muted/5 space-y-4">
                            <div class="flex items-center justify-between pb-2 border-b border-border/40">
                                <div class="flex items-center gap-2">
                                    <div class="p-1.5 bg-purple-100/50 text-purple-600 rounded-md">
                                        <Database class="w-4 h-4" />
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-sm text-foreground">知识库</h4>
                                        <p class="text-xs text-muted-foreground">关联文档以增强回答能力</p>
                                    </div>
                                </div>
                                <div class="flex items-center gap-2 bg-background px-3 py-1.5 rounded-full border border-border/40">
                                    <div class="flex items-center gap-1.5">
                                        <Label class="text-sm text-muted-foreground cursor-pointer" for="strict-mode">严格模式</Label>
                                        <TooltipProvider>
                                            <Tooltip :delay-duration="100">
                                                <TooltipTrigger>
                                                    <HelpCircle class="w-3 h-3 text-muted-foreground/60 hover:text-primary transition-colors cursor-help" />
                                                </TooltipTrigger>
                                                <TooltipContent class="max-w-[260px] p-3 text-xs leading-relaxed bg-popover text-popover-foreground shadow-xl border border-border/50">
                                                    <p class="font-medium mb-1 text-primary">什么是严格模式？</p>
                                                    <p>开启后，AI 将<span class="font-bold text-foreground">仅使用</span>知识库中的内容回答问题，不会使用其自带的通用知识。</p>
                                                    <p class="mt-1.5 text-muted-foreground opacity-80">适用于客服、合规查询等需要精确可控回答的场景。</p>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <Switch id="strict-mode" v-model:checked="form.knowledge_config.strict_only" class="scale-75 origin-right" />
                                </div>
                            </div>

                            <ScrollArea class="h-[180px] w-full pr-4">
                                <div v-if="knowledgeBases.length === 0" class="flex flex-col items-center justify-center h-32 text-center border-2 border-dashed border-border/40 rounded-xl bg-muted/5 text-muted-foreground">
                                    <Database class="w-8 h-8 mb-2 opacity-20" />
                                    <p class="text-sm">暂无可用知识库</p>
                                    <Button variant="link" size="sm" class="text-xs h-6 text-primary">去创建</Button>
                                </div>
                                <div v-else class="grid grid-cols-1 gap-2">
                                    <div v-for="kb in knowledgeBases" :key="kb.id"
                                        class="flex items-center justify-between p-3 rounded-lg border border-transparent bg-background hover:border-primary/20 hover:shadow-sm transition-all cursor-pointer group"
                                        :class="{ 'ring-1 ring-primary/20 bg-primary/5': form.knowledge_config.document_ids.includes(kb.id) }"
                                        @click="toggleKb(kb.id)">
                                        <div class="flex items-center gap-3 overflow-hidden">
                                            <div class="p-2 rounded-md bg-muted/20 text-muted-foreground group-hover:text-primary transition-colors">
                                                <FileText class="w-4 h-4" />
                                            </div>
                                            <div class="grid gap-0.5">
                                                <label class="text-sm font-medium leading-none cursor-pointer truncate max-w-[200px]">{{ kb.filename }}</label>
                                                <p class="text-xs text-muted-foreground">{{ formatSize(kb.file_size) }}</p>
                                            </div>
                                        </div>
                                        <Checkbox :id="kb.id" :checked="form.knowledge_config.document_ids.includes(kb.id)" @click.stop="toggleKb(kb.id)" 
                                            class="data-[state=checked]:bg-primary data-[state=checked]:border-primary" />
                                    </div>
                                </div>
                            </ScrollArea>
                        </Card>

                        <!-- Tools & Skills -->
                        <Card class="p-5 border-border/40 shadow-sm bg-muted/5 space-y-4">
                            <div class="flex items-center justify-between pb-2 border-b border-border/40">
                                <div class="flex items-center gap-2">
                                    <div class="p-1.5 bg-orange-100/50 text-orange-600 rounded-md">
                                        <Wrench class="w-4 h-4" />
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-sm text-foreground">工具箱</h4>
                                        <p class="text-xs text-muted-foreground">扩展智能体的操作能力</p>
                                    </div>
                                </div>
                                <Button variant="outline" size="sm" class="h-7 text-xs border-dashed border-primary/30 text-primary hover:bg-primary/5 hover:border-primary/50" @click="openToolSelector('skill')">
                                    <Plus class="w-3.5 h-3.5 mr-1" /> 添加技能
                                </Button>
                            </div>

                            <div class="grid gap-3">
                                <!-- Built-in Tools -->
                                <div v-for="tool in defaultTools" :key="tool.value" 
                                    class="flex items-start space-x-3 p-3 rounded-lg border border-transparent bg-background hover:border-primary/20 transition-all cursor-pointer"
                                    :class="{ 'ring-1 ring-primary/20 bg-primary/5': form.tools_config.includes(tool.value) }"
                                    @click="!form.tools_config.includes(tool.value) ? form.tools_config.push(tool.value) : (form.tools_config = form.tools_config.filter(t => t !== tool.value))">
                                    <Checkbox :id="tool.value" :checked="form.tools_config.includes(tool.value)" class="mt-1 data-[state=checked]:bg-primary" @click.stop />
                                    <div class="grid gap-1">
                                        <label :for="tool.value" class="text-sm font-medium leading-none cursor-pointer text-foreground">
                                            {{ tool.label }}
                                        </label>
                                        <p class="text-xs text-muted-foreground leading-snug">
                                            {{ tool.desc }}
                                        </p>
                                    </div>
                                </div>

                                <!-- External Skills -->
                                <div v-if="skillTools.length > 0" class="grid grid-cols-2 gap-3 mt-2">
                                    <div v-for="(tool, idx) in skillTools" :key="idx"
                                        class="flex items-center justify-between p-2.5 border border-border/40 rounded-lg bg-background group hover:border-red-200 hover:bg-red-50/30 transition-colors">
                                        <div class="flex items-center gap-2.5 overflow-hidden">
                                            <div class="p-1.5 bg-green-100/50 text-green-600 rounded-md shrink-0">
                                                <Blocks class="w-3.5 h-3.5" />
                                            </div>
                                            <div class="grid gap-0.5 min-w-0">
                                                <span class="text-xs font-medium truncate">{{ tool.name }}</span>
                                                <span class="text-xs text-muted-foreground">v{{ tool.version || '1.0' }}</span>
                                            </div>
                                        </div>
                                        <Button variant="ghost" size="icon" class="h-6 w-6 text-muted-foreground hover:text-red-500 hover:bg-red-100/50 opacity-0 group-hover:opacity-100 transition-opacity" @click="removeSkill(tool)">
                                            <Trash2 class="w-3 h-3" />
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </Card>

                        <!-- MCP Servers -->
                        <Card class="p-5 border-border/40 shadow-sm bg-muted/5 space-y-4">
                            <div class="flex items-center justify-between pb-2 border-b border-border/40">
                                <div class="flex items-center gap-2">
                                    <div class="p-1.5 bg-teal-100/50 text-teal-600 rounded-md">
                                        <Server class="w-4 h-4" />
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-sm text-foreground">MCP 服务</h4>
                                        <p class="text-xs text-muted-foreground">连接本地或远程 MCP 协议服务</p>
                                    </div>
                                </div>
                                <div class="flex gap-2">
                                    <Button variant="outline" size="sm" class="h-7 text-xs border-border/40 hover:bg-muted/50" @click="addMcp">
                                        <Plus class="w-3 h-3 mr-1" /> 手动
                                    </Button>
                                    <Button variant="outline" size="sm" class="h-7 text-xs text-purple-600 border-purple-200/50 hover:bg-purple-50 hover:border-purple-200" @click="openToolSelector('mcp')">
                                        <ShoppingBag class="w-3 h-3 mr-1" /> 市场
                                    </Button>
                                </div>
                            </div>

                            <div v-if="form.mcp_config.length === 0" class="flex flex-col items-center justify-center py-8 border-2 border-dashed border-border/40 rounded-xl bg-background/50 text-muted-foreground">
                                <Server class="w-8 h-8 mb-2 opacity-20" />
                                <p class="text-sm">暂未配置 MCP 服务</p>
                                <p class="text-xs opacity-60 mt-1">添加服务以扩展更多能力</p>
                            </div>
                            
                            <div v-else class="space-y-3">
                                <div v-for="(mcp, idx) in form.mcp_config" :key="idx" class="border border-border/40 rounded-xl overflow-hidden bg-background shadow-sm group transition-all hover:shadow-md hover:border-primary/20">
                                    <div class="bg-muted/30 px-3 py-2 border-b border-border/40 flex items-center justify-between group-hover:bg-muted/40 transition-colors">
                                        <div class="flex items-center gap-2 flex-1">
                                            <Badge variant="secondary" class="text-xs h-5 px-1.5 font-mono bg-background border-border/50 text-muted-foreground shadow-sm">
                                                {{ mcp.type.toUpperCase() }}
                                            </Badge>
                                            <Input v-model="mcp.name" class="h-7 text-sm font-medium border-transparent hover:border-border/30 focus:border-blue-500 bg-transparent w-40 px-1 focus:ring-2 focus:ring-blue-500/10 focus:bg-white transition-all" placeholder="服务名称" />
                                        </div>
                                        <div class="flex items-center gap-1">
                                            <div class="w-2 h-2 rounded-full bg-yellow-400/80 animate-pulse" title="待连接"></div>
                                            <Button variant="ghost" size="icon" class="h-7 w-7 text-muted-foreground hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity" @click="removeMcp(idx)">
                                                <Trash2 class="w-3.5 h-3.5" />
                                            </Button>
                                        </div>
                                    </div>
                                    
                                    <div class="p-3 grid gap-2">
                                        <!-- Command Row -->
                                        <div class="flex items-center gap-2">
                                            <div class="w-16 shrink-0 text-xs text-muted-foreground font-medium text-right">命令/URL</div>
                                            <div class="relative flex-1">
                                                <div class="absolute inset-y-0 left-2 flex items-center pointer-events-none opacity-50">
                                                    <span class="text-xs font-mono text-muted-foreground">>_</span>
                                                </div>
                                                <Input v-model="mcp.command" class="font-mono text-xs h-7 pl-6 bg-muted/20 border-border/20 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all" placeholder="Enter command or URL..." />
                                            </div>
                                        </div>
                                        
                                        <!-- Args Row -->
                                        <div class="flex items-center gap-2">
                                            <div class="w-16 shrink-0 text-xs text-muted-foreground font-medium text-right">参数</div>
                                            <Input v-model="mcp.args" class="flex-1 font-mono text-xs h-7 bg-muted/20 border-border/20 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all" placeholder='["arg1", "arg2"]' />
                                        </div>
                                    </div>

                                    <div class="px-3 py-1.5 bg-muted/5 border-t border-border/40 flex justify-between items-center">
                                        <div class="text-xs text-muted-foreground flex items-center gap-1.5 opacity-60">
                                            <Info class="w-3 h-3" />
                                            <span>保存后生效</span>
                                        </div>
                                        <Button variant="ghost" size="sm" class="h-6 text-xs text-teal-600 hover:text-teal-700 hover:bg-teal-50 px-2 group-hover:pr-1 transition-all" @click="viewMcpTools(mcp)">
                                            查看工具列表 <ChevronRight class="w-3 h-3 ml-1 transition-transform group-hover:translate-x-0.5" />
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </TabsContent>

                    <!-- Tab: Scripts -->
                    <TabsContent value="scripts" class="mt-0 animate-fade-in flex flex-col pb-6">
                        <Card class="flex flex-col border-border/40 shadow-sm bg-muted/5 overflow-hidden min-h-[500px]">
                             <div class="px-5 py-3 border-b border-border/40 bg-background flex items-center justify-between shrink-0">
                                <div class="flex items-center gap-2">
                                    <div class="p-1.5 bg-pink-100/50 text-pink-600 rounded-md">
                                        <FileText class="w-4 h-4" />
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-sm text-foreground">用户剧本</h4>
                                        <p class="text-xs text-muted-foreground">编排复杂的对话流程</p>
                                    </div>
                                </div>
                                <div class="flex gap-2" v-if="!isReadOnly">
                                    <Button variant="outline" size="sm" class="h-7 text-xs border-dashed border-primary/30 text-primary hover:bg-primary/5" @click="() => scriptsEditorRef?.openCreate()">
                                        <Plus class="w-3.5 h-3.5 mr-1" /> 新建剧本
                                    </Button>
                                </div>
                            </div>
                            
                            <div class="relative bg-background min-h-[500px]">
                                <UserScriptsEditor ref="scriptsEditorRef" :agentId="activeAgentId" :readonly="isReadOnly" class="h-full w-full" />
                            </div>
                        </Card>
                    </TabsContent>
                </div>
            </ScrollArea>
        </Tabs>

        <!-- Drawer Footer -->
        <div class="px-6 py-4 border-t border-border bg-background flex justify-between items-center shrink-0">
            <!-- Normal Edit/Create Mode -->
            <template v-if="!isReadOnly">
                <div class="flex gap-2">
                    <Button variant="outline" size="icon" @click="exportConfig" title="导出配置">
                        <Download class="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="icon" @click="triggerImport" title="导入配置">
                        <Upload class="w-4 h-4" />
                    </Button>
                    <input type="file" ref="importInput" class="hidden" accept=".json" @change="handleImportConfig">
                </div>
                <div class="flex gap-3">
                    <Button variant="ghost" @click="closeDrawer">取消</Button>
                    <Button @click="() => saveAgent(true)" :disabled="isSaving" 
                        class="min-w-[100px] hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md hover:shadow-lg border-0">
                        <Loader2 v-if="isSaving" class="w-4 h-4 mr-2 animate-spin" />
                        {{ isSaving ? '保存中' : '保存配置' }}
                    </Button>
                </div>
            </template>
            
            <!-- Template Preview Mode -->
            <template v-else>
                <div class="flex items-center text-sm text-muted-foreground gap-2">
                    <Info class="w-4 h-4" />
                    <span>预览模式：仅查看，不可编辑</span>
                </div>
                <div class="flex gap-3">
                    <Button variant="ghost" @click="closeDrawer">关闭</Button>
                    <Button @click="useTemplate" class="min-w-[120px] bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all">
                        <Copy class="w-4 h-4 mr-2" />
                        立即使用
                    </Button>
                </div>
            </template>
        </div>
    </div>

    <!-- Tools List Modal -->
    <Dialog v-model:open="showToolsModal">
        <DialogContent class="sm:max-w-[700px] max-h-[85vh] flex flex-col p-0 gap-0">
            <DialogHeader class="px-6 py-4 border-b shrink-0 flex flex-col gap-4 space-y-0 bg-background/95 backdrop-blur z-10">
                <div class="flex items-center justify-between w-full">
                    <div class="flex items-center gap-2">
                        <div class="p-1.5 bg-teal-100/50 text-teal-600 rounded-md">
                            <Server class="w-4 h-4" />
                        </div>
                        <div class="flex flex-col gap-0.5">
                            <DialogTitle class="text-base font-semibold">{{ currentMcpName }}</DialogTitle>
                            <DialogDescription class="text-xs">可用工具列表</DialogDescription>
                        </div>
                    </div>
                    <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground" @click="showToolsModal = false">
                        <X class="w-4 h-4" />
                    </Button>
                </div>
                
                <!-- Search Bar -->
                <div class="relative w-full">
                    <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input v-model="mcpToolSearchQuery" placeholder="搜索工具名称或描述..." class="pl-9 h-9 bg-muted/50 focus:bg-background transition-all" />
                </div>
            </DialogHeader>

            <ScrollArea class="flex-1 bg-muted/5">
                <div v-if="isFetchingTools" class="flex flex-col items-center justify-center py-20 gap-4">
                    <Loader2 class="w-8 h-8 text-teal-500 animate-spin" />
                    <span class="text-muted-foreground text-sm">正在连接 MCP 服务获取工具...</span>
                </div>
                
                <div v-else-if="filteredMcpTools.length === 0" class="flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <div class="w-16 h-16 rounded-full bg-muted/30 flex items-center justify-center mb-4">
                        <Search class="w-8 h-8 opacity-40" />
                    </div>
                    <p class="font-medium">未找到相关工具</p>
                    <p class="text-xs opacity-60 mt-1" v-if="mcpToolSearchQuery">请尝试更换关键词</p>
                    <p class="text-xs opacity-60 mt-1" v-else>该服务暂未提供任何工具或连接失败</p>
                </div>

                <div v-else class="p-6 space-y-4">
                    <Card v-for="(tool, idx) in filteredMcpTools" :key="idx" class="overflow-hidden border bg-card hover:border-primary/20 transition-all shadow-sm">
                        <!-- Tool Header -->
                        <div class="px-4 py-3 bg-muted/10 border-b flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <Badge variant="outline" class="font-mono text-xs bg-background border-primary/20 text-primary font-semibold">
                                    {{ tool.name }}
                                </Badge>
                            </div>
                            <Button variant="ghost" size="sm" class="h-6 w-6 p-0 text-muted-foreground hover:text-primary" title="复制工具名" @click="copyText(tool.name)">
                                <Copy class="w-3 h-3" />
                            </Button>
                        </div>
                        
                        <div class="p-4 space-y-4">
                            <!-- Description -->
                            <p class="text-sm text-muted-foreground leading-relaxed">
                                {{ tool.description || '暂无描述信息' }}
                            </p>
                            
                            <!-- Schema Table -->
                            <div class="rounded-md border border-border/50 overflow-hidden">
                                <div class="bg-muted/30 px-3 py-1.5 border-b border-border/50 flex items-center gap-2">
                                    <Cpu class="w-3 h-3 text-muted-foreground" />
                                    <span class="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">输入参数 (Input Schema)</span>
                                </div>
                                
                                <div v-if="formatSchema(tool.inputSchema).length === 0" class="p-4 text-center text-xs text-muted-foreground bg-background">
                                    无需输入参数
                                </div>
                                
                                <div v-else class="overflow-x-auto bg-background">
                                    <table class="w-full text-xs">
                                        <thead>
                                            <tr class="border-b border-border/50 bg-muted/5 text-left">
                                                <th class="h-8 px-3 font-medium text-muted-foreground w-1/4">参数名</th>
                                                <th class="h-8 px-3 font-medium text-muted-foreground w-1/6">类型</th>
                                                <th class="h-8 px-3 font-medium text-muted-foreground w-1/6">必填</th>
                                                <th class="h-8 px-3 font-medium text-muted-foreground">描述</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-border/30">
                                            <tr v-for="param in formatSchema(tool.inputSchema)" :key="param.name" class="hover:bg-muted/5 transition-colors">
                                                <td class="p-3 font-mono font-medium text-foreground">{{ param.name }}</td>
                                                <td class="p-3 text-muted-foreground font-mono">{{ param.type }}</td>
                                                <td class="p-3">
                                                    <Badge v-if="param.required" variant="destructive" class="h-4 px-1 text-[10px] font-normal">Required</Badge>
                                                    <span v-else class="text-muted-foreground opacity-50">-</span>
                                                </td>
                                                <td class="p-3 text-muted-foreground break-words max-w-[200px]">{{ param.desc }}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </ScrollArea>
        </DialogContent>
    </Dialog>

    <!-- Tool Selector Modal -->
    <Dialog v-model:open="showToolSelector">
        <DialogContent class="sm:max-w-[900px] h-[85vh] flex flex-col p-0 gap-0">
            <DialogHeader class="px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10 flex flex-row items-center justify-between space-y-0">
                <div class="flex flex-col gap-1">
                    <DialogTitle class="text-lg font-semibold">选择组件</DialogTitle>
                    <DialogDescription class="text-xs text-muted-foreground">
                        浏览并添加 MCP 服务或 Agent 技能来扩展智能体的能力。
                    </DialogDescription>
                </div>
                <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground" @click="showToolSelector = false">
                    <X class="w-4 h-4" />
                </Button>
            </DialogHeader>
            
            <div class="flex-1 overflow-hidden flex flex-col bg-muted/5">
                <Tabs v-model="activeToolTab" class="flex-1 flex flex-col h-full">
                    <div class="px-6 py-3 shrink-0 bg-background border-b flex items-center justify-between gap-4">
                        <TabsList class="grid w-[300px] grid-cols-2">
                            <TabsTrigger value="mcp">MCP 服务</TabsTrigger>
                            <TabsTrigger value="skill">智能体技能</TabsTrigger>
                        </TabsList>
                        
                        <div class="relative w-64">
                            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input v-model="toolSearchQuery" placeholder="搜索组件..." class="pl-9 h-9 bg-muted/50" />
                        </div>
                    </div>

                    <!-- Category Filter -->
                    <div v-if="availableCategories.length > 1" class="px-6 py-2 border-b bg-muted/10 flex items-center gap-2 overflow-x-auto no-scrollbar shrink-0">
                        <div class="flex items-center gap-2 pr-4">
                            <Filter class="w-3.5 h-3.5 text-muted-foreground" />
                            <span class="text-xs text-muted-foreground whitespace-nowrap">分类筛选:</span>
                        </div>
                        <Badge 
                            v-for="cat in availableCategories" 
                            :key="cat"
                            variant="outline"
                            class="cursor-pointer transition-all whitespace-nowrap hover:border-primary/50"
                            :class="selectedCategory === cat ? 'bg-primary/10 border-primary text-primary' : 'bg-background text-muted-foreground border-border/60'"
                            @click="selectedCategory = cat"
                        >
                            {{ getCategoryLabel(cat) }}
                        </Badge>
                    </div>

                    <ScrollArea class="flex-1">
                        <div class="p-6 min-h-full">
                             <div v-if="isLoadingTools" class="flex flex-col items-center justify-center py-20 gap-4">
                                <Loader2 class="w-8 h-8 text-primary animate-spin" />
                                <span class="text-muted-foreground text-sm">加载组件库中...</span>
                            </div>
                            
                            <div v-else-if="filteredMarketTools.length === 0" class="flex flex-col items-center justify-center py-20 text-muted-foreground">
                                <div class="w-16 h-16 rounded-full bg-muted/30 flex items-center justify-center mb-4">
                                    <Search class="w-8 h-8 opacity-40" />
                                </div>
                                <p class="font-medium">未找到相关组件</p>
                                <p class="text-xs opacity-60 mt-1">请尝试更换关键词或切换分类</p>
                            </div>

                            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
                                <Card v-for="tool in filteredMarketTools" :key="tool.id" 
                                    class="flex flex-col transition-all hover:shadow-md hover:border-primary/30 group bg-card border-border/60"
                                    :class="{'ring-1 ring-primary/20 bg-primary/5': isToolSelected(tool)}">
                                    <div class="p-5 flex flex-col h-full gap-3">
                                        <div class="flex justify-between items-start">
                                            <div class="flex items-center gap-3 overflow-hidden">
                                                <div class="p-2 rounded-lg shrink-0 border shadow-sm" 
                                                    :class="tool.type === 'mcp' ? 'bg-purple-50 border-purple-100 text-purple-600' : 'bg-green-50 border-green-100 text-green-600'">
                                                    <Server v-if="tool.type === 'mcp'" class="w-5 h-5" />
                                                    <Blocks v-else class="w-5 h-5" />
                                                </div>
                                                <div class="grid gap-0.5 min-w-0">
                                                    <span class="font-semibold text-sm truncate text-foreground" :title="tool.name">{{ tool.name }}</span>
                                                    <Badge variant="secondary" class="w-fit text-[10px] h-4 px-1 font-mono text-muted-foreground border-border/50 bg-muted/50">
                                                        v{{ tool.version || '1.0.0' }}
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <p class="text-xs text-muted-foreground line-clamp-2 leading-relaxed h-8">
                                            {{ tool.description || '暂无描述信息' }}
                                        </p>
                                        
                                        <div class="mt-auto pt-3 flex items-center justify-between border-t border-dashed border-border/50">
                                            <div class="flex items-center gap-1.5">
                                                 <template v-if="!checkCompatibility(tool)">
                                                     <div class="w-1.5 h-1.5 rounded-full bg-amber-500"></div>
                                                     <span class="text-[10px] text-amber-600 font-medium">版本风险</span>
                                                 </template>
                                                 <template v-else>
                                                     <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                                                     <span class="text-[10px] text-emerald-600 font-medium">兼容</span>
                                                 </template>
                                            </div>

                                            <Button size="sm" 
                                                :variant="isToolSelected(tool) ? 'secondary' : 'default'" 
                                                class="h-7 text-xs px-3 shadow-sm transition-all"
                                                :class="isToolSelected(tool) ? 'bg-muted/80 text-muted-foreground hover:bg-muted' : ''"
                                                :disabled="isToolSelected(tool) || (tool.is_active === false)"
                                                @click="selectToolFromMarket(tool)">
                                                <span v-if="isToolSelected(tool)" class="flex items-center gap-1">
                                                    <Check class="w-3 h-3" /> 已添加
                                                </span>
                                                <span v-else-if="tool.is_active === false">不可用</span>
                                                <span v-else>添加</span>
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            </div>
                        </div>
                    </ScrollArea>
                </Tabs>
            </div>
        </DialogContent>
    </Dialog>
</template>

<script setup>
import { ref, computed, watch, h } from 'vue';
import { message } from 'ant-design-vue';
import UserScriptsEditor from './UserScriptsEditor.vue';
import { 
    X, Save, Upload, Download, Plus, Trash2, Settings2, Database, Wrench, 
    FileText, Bot, ChevronRight, Search, Check, AlertCircle, Loader2,
    MessageSquareCode, Cpu, Server, Blocks, ShoppingBag,
    Sparkles, Copy, Wand2, Info, HelpCircle, Filter
} from 'lucide-vue-next';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

const props = defineProps({
    visible: Boolean,
    agent: Object,
    mode: {
        type: String,
        default: 'edit', // 'create', 'edit', 'preview'
    },
    knowledgeBases: {
        type: Array,
        default: () => []
    },
    availableModels: {
        type: Array,
        default: () => []
    }
});

const emit = defineEmits(['close', 'saved']);

// --- Icons Helper ---
const createIcon = (d) => ({
    render: () => h('svg', {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '1.5',
        stroke: 'currentColor'
    }, [
        h('path', {
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            d: d
        })
    ])
});
const GlobeAltIcon = createIcon('M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S12 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S12 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418');
const availableIcons = { 'globe': GlobeAltIcon };

// --- State ---
const isEditing = ref(false);
const currentMode = ref('edit'); // 'create', 'edit', 'preview'
const isReadOnly = computed(() => currentMode.value === 'preview');

const drawerTitle = computed(() => {
    if (currentMode.value === 'create') return '新建智能体';
    if (currentMode.value === 'edit') return '编辑智能体';
    if (currentMode.value === 'preview') return '模版详情';
    return '智能体配置';
});

const isSaving = ref(false);
const showToolsModal = ref(false);
const currentMcpTools = ref([]);
const isFetchingTools = ref(false);
const currentMcpName = ref('');
const mcpToolSearchQuery = ref('');
const showToolSelector = ref(false);
const activeToolTab = ref('mcp');
const marketTools = ref([]);
const isLoadingTools = ref(false);
const toolSearchQuery = ref('');
const iconInput = ref(null);
const importInput = ref(null);
const scriptsEditorRef = ref(null);

const defaultSkillsConfig = {
    environment: { type: 'local', image: 'python:3.9-slim' },
    python: { enabled: false, safe_mode: true, allowed_modules: [] },
    filesystem: { enabled: false, base_dir: '/tmp', allow_write: false },
    browser: { enabled: false, headless: true, search_engine: 'duckduckgo' }
};

const defaultTools = [
    { label: 'DuckDuckGo Search', value: 'duckduckgo', desc: '网络搜索工具，支持实时信息检索' },
    { label: 'Calculator', value: 'calculator', desc: '数学计算工具，支持复杂运算' },
    { label: 'N8N Workflow', value: 'n8n', desc: '工作流自动化，连接外部服务' }
];

const form = ref({
    id: null,
    name: '',
    description: '',
    icon: '/tiga.svg',
    system_prompt: '',
    model_config: { model_id: '', reasoning: false },
    tools_config: [],
    mcp_config: [],
    skills_config: defaultSkillsConfig,
    knowledge_config: { document_ids: [], strict_only: false }
});

const activeAgentId = computed(() => form.value.id || '');
const selectedCategory = ref('全部');

const categoryMap = {
    'productivity': '生产力',
    'development': '开发工具',
    'communication': '社交通信',
    'analysis': '数据分析',
    'utilities': '实用工具',
    'finance': '金融财经',
    'design': '设计创作',
    'education': '教育学习',
    'entertainment': '娱乐休闲',
    'news': '新闻资讯',
    'medical': '医疗健康',
    'travel': '旅行交通',
    'other': '其他',
    'uncategorized': '未分类',
    'default': '默认'
};

const getCategoryLabel = (cat) => {
    if (cat === '全部') return '全部';
    if (!cat) return '未分类';
    // If it's already Chinese (likely if backend returns Chinese or defaulted to '未分类'), return it
    if (/[\u4e00-\u9fa5]/.test(cat)) return cat;
    
    const lower = cat.toLowerCase();
    return categoryMap[lower] || cat;
};

const filteredMcpTools = computed(() => {
    if (!mcpToolSearchQuery.value) return currentMcpTools.value;
    const q = mcpToolSearchQuery.value.toLowerCase();
    return currentMcpTools.value.filter(t => 
        t.name.toLowerCase().includes(q) || 
        (t.description || '').toLowerCase().includes(q)
    );
});

const filteredMarketTools = computed(() => {
    return marketTools.value.filter(t => {
        const matchesTab = t.type === activeToolTab.value;
        if (!matchesTab) return false;

        // Category Filter
        const toolCategory = t.category || '未分类';
        if (selectedCategory.value !== '全部' && toolCategory !== selectedCategory.value) {
            return false;
        }

        if (!toolSearchQuery.value) return true;
        const query = toolSearchQuery.value.toLowerCase();
        return t.name.toLowerCase().includes(query) || (t.description || '').toLowerCase().includes(query);
    });
});

const availableCategories = computed(() => {
    const tools = marketTools.value.filter(t => t.type === activeToolTab.value);
    if (tools.length === 0) return [];
    
    const categories = new Set(tools.map(t => t.category || '未分类'));
    // If only '未分类' exists (size=1), and we don't want to show filter if it's useless
    // But let's show it so user knows they can categorize
    const sorted = Array.from(categories).sort();
    if (sorted.length === 1 && sorted[0] === '未分类') return []; // Hide if no real categories
    return ['全部', ...sorted];
});

watch(activeToolTab, () => {
    selectedCategory.value = '全部';
    toolSearchQuery.value = '';
});

const skillTools = computed(() => form.value.tools_config.filter(t => typeof t === 'object'));
const pendingScripts = ref([]);

const useTemplate = async () => {
    // 1. Fetch template scripts to clone later
    pendingScripts.value = [];
    if (form.value.id) {
        try {
            const res = await fetch(`/api/v1/user_scripts?agent_id=${form.value.id}`);
            if (res.ok) {
                const scripts = await res.json();
                // Prepare clean script objects (remove IDs)
                pendingScripts.value = scripts.map(s => ({
                    title: s.title,
                    content: s.content,
                    description: s.description,
                    sort_order: s.sort_order
                }));
            }
        } catch (e) {
            console.warn("Failed to fetch template scripts for cloning", e);
        }
    }

    // 2. Convert template to new agent
    form.value.id = null;
    form.value.is_template = false;
    // Optional: Add (Copy) suffix? No, user can rename.
    // form.value.name = `${form.value.name} (副本)`; 
    
    currentMode.value = 'create';
    isEditing.value = false;
    message.success("已加载模版，您可以修改后保存为新智能体");
};

// --- Watchers ---
watch(() => props.agent, (newAgent) => {
    pendingScripts.value = []; // Reset pending scripts
    if (newAgent) {
        form.value = buildAgentPayload(newAgent);
        if (props.mode === 'preview') {
            currentMode.value = 'preview';
            isEditing.value = false;
        } else {
            currentMode.value = 'edit';
            isEditing.value = true;
        }
    } else {
        currentMode.value = 'create';
        isEditing.value = false;
        resetForm();
        pendingScripts.value = [];
    }
}, { immediate: true });

watch(() => props.mode, (newMode) => {
    currentMode.value = newMode || 'create';
    isReadOnly.value = newMode === 'preview';
});

// --- Methods ---
function resetForm() {
    form.value = {
        id: null,
        name: '',
        description: '',
        icon: 'globe',
        system_prompt: '',
        model_config: { model_id: '', reasoning: false },
        tools_config: [],
        mcp_config: [],
        skills_config: defaultSkillsConfig,
        knowledge_config: { document_ids: [], strict_only: false }
    };
}

function buildAgentPayload(agentLike) {
    const payload = {
        name: agentLike?.name || '',
        description: agentLike?.description || '',
        icon: agentLike?.icon || 'globe',
        system_prompt: agentLike?.system_prompt || '',
        model_config: agentLike?.model_config || { model_id: '', reasoning: false },
        tools_config: Array.isArray(agentLike?.tools_config) ? agentLike.tools_config : [],
        mcp_config: Array.isArray(agentLike?.mcp_config) ? agentLike.mcp_config : [],
        skills_config: agentLike?.skills_config || defaultSkillsConfig,
        knowledge_config: agentLike?.knowledge_config || { document_ids: [], strict_only: false }
    };

    if (agentLike?.id) payload.id = agentLike.id;
    if (typeof agentLike?.is_template === 'boolean') payload.is_template = agentLike.is_template;
    if (typeof agentLike?.is_active === 'boolean') payload.is_active = agentLike.is_active;

    return payload;
}

const closeDrawer = () => emit('close');
const getIconComponent = (iconName) => availableIcons[iconName] || GlobeAltIcon;

const isImageIcon = (icon) => {
    if (!icon || typeof icon !== 'string') return false;
    const value = icon.trim();
    if (!value) return false;
    if (value.startsWith('data:image') || value.startsWith('blob:') || /^https?:\/\//i.test(value)) return true;
    if (value.startsWith('/') || value.startsWith('./') || value.startsWith('../')) return true;
    return /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i.test(value);
};

const triggerIconUpload = () => iconInput.value.click();

const handleIconUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 100 * 1024) {
        message.warning("图标文件过大，建议小于 100KB");
        return;
    }
    const reader = new FileReader();
    reader.onload = (e) => { form.value.icon = e.target.result; };
    reader.readAsDataURL(file);
};

const formatSize = (bytes) => {
    if (!bytes && bytes !== 0) return '0 B';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatSchema = (schema) => {
    if (!schema || !schema.properties) return [];
    return Object.entries(schema.properties).map(([key, value]) => ({
        name: key,
        type: value.type || 'any',
        desc: value.description || '-',
        required: schema.required?.includes(key) || false
    }));
};

const copyText = async (text) => {
    try {
        await navigator.clipboard.writeText(text);
        message.success("已复制");
    } catch (e) {
        message.error("复制失败");
    }
};

const toggleKb = (id) => {
    if (form.value.knowledge_config.document_ids.includes(id)) {
        form.value.knowledge_config.document_ids = form.value.knowledge_config.document_ids.filter(i => i !== id);
    } else {
        form.value.knowledge_config.document_ids.push(id);
    }
};

const addMcp = () => {
    form.value.mcp_config.push({ name: '', type: 'stdio', command: '', args: '[]' });
};

const removeMcp = (index) => {
    form.value.mcp_config.splice(index, 1);
};

const viewMcpTools = async (mcp) => {
    currentMcpName.value = mcp.name || 'Unknown MCP';
    currentMcpTools.value = [];
    showToolsModal.value = true;
    isFetchingTools.value = true;
    try {
        let parsedArgs = [];
        try { parsedArgs = JSON.parse(mcp.args || '[]'); } catch (e) { console.warn(e); parsedArgs = []; }
        const config = { type: mcp.type, command: mcp.command, args: parsedArgs, env: {} };
        const res = await fetch('/api/v1/mcp/fetch_tools', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (res.ok) {
            currentMcpTools.value = await res.json();
        } else {
            const err = await res.json();
            message.error("获取工具失败: " + (err.detail || 'Unknown error'));
        }
    } catch (e) {
        message.error("连接 MCP 服务失败");
    } finally {
        isFetchingTools.value = false;
    }
};

const removeSkill = (tool) => {
    const index = form.value.tools_config.findIndex(t => t === tool || (typeof t === 'object' && t.name === tool.name));
    if (index > -1) form.value.tools_config.splice(index, 1);
};

const openToolSelector = (tab = 'mcp') => {
    activeToolTab.value = tab;
    showToolSelector.value = true;
    fetchMarketTools();
};

const fetchMarketTools = async () => {
    if (marketTools.value.length > 0) return;
    isLoadingTools.value = true;
    try {
        const [mcpRes, skillRes] = await Promise.all([
            fetch('/api/v1/mcp/'),
            fetch('/api/v1/skills/')
        ]);
        const mcps = mcpRes.ok ? await mcpRes.json() : [];
        const skills = skillRes.ok ? await skillRes.json() : [];
        marketTools.value = [
            ...mcps.map(m => ({ ...m, type: 'mcp' })),
            ...skills.map(s => ({ ...s, type: 'skill' }))
        ];
    } catch (e) {
        message.error("获取组件列表失败");
    } finally {
        isLoadingTools.value = false;
    }
};

const checkCompatibility = (tool) => {
    if (tool.version && tool.version.startsWith('2.')) return false;
    return true;
};

const isToolSelected = (tool) => {
    if (tool.type === 'mcp') {
        return form.value.mcp_config.some(m => m.name === tool.name);
    } else {
        return form.value.tools_config.some(t => {
            if (typeof t === 'string') return t === tool.name;
            return t.id === tool.id || t.name === tool.name;
        });
    }
};

const selectToolFromMarket = (tool) => {
    if (tool.type === 'mcp') {
        let config = {
            name: tool.name,
            type: tool.mcp_type || 'stdio',
            command: 'python',
            args: '[]'
        };
        if (tool.config) {
            config = { ...config, ...tool.config, name: tool.name };
            if (Array.isArray(config.args)) config.args = JSON.stringify(config.args);
        }
        form.value.mcp_config.push(config);
        message.success(`已添加 MCP 服务: ${tool.name}`);
    } else {
        form.value.tools_config.push({
            type: 'skill',
            id: tool.id,
            name: tool.name,
            content: tool.content,
            version: tool.version
        });
        message.success(`已添加技能: ${tool.name}`);
    }
};

const exportConfig = () => {
    const dataStr = JSON.stringify(form.value, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-${form.value.name || 'config'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success("配置已导出");
};

const triggerImport = () => importInput.value.click();

const handleImportConfig = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            if (!data.name && !data.model_config) throw new Error("Invalid config format");
            form.value = { ...form.value, ...data };
            form.value.id = isEditing.value ? activeAgentId.value : null;
            message.success("配置已导入");
        } catch (err) {
            message.error("导入失败: 配置文件格式错误");
        }
    };
    reader.readAsText(file);
    event.target.value = '';
};

const saveAgent = async (shouldClose = true) => {
    if (!form.value.name) {
        message.error("请输入智能体名称");
        return;
    }
    isSaving.value = true;
    try {
        const url = isEditing.value ? `/api/v1/agents/${form.value.id}` : '/api/v1/agents/';
        const method = isEditing.value ? 'PUT' : 'POST';
        const payload = buildAgentPayload(form.value);
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const savedAgent = await res.json();
            
            // Clone scripts if needed (from template)
            if (pendingScripts.value.length > 0 && savedAgent.id) {
                try {
                    await Promise.all(pendingScripts.value.map(s => 
                        fetch('/api/v1/user_scripts', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ ...s, agent_id: savedAgent.id })
                        })
                    ));
                } catch (e) {
                    console.error("Failed to clone scripts", e);
                }
                pendingScripts.value = [];
            }
            
            // Save newly created local scripts (no ID yet)
            if (scriptsEditorRef.value && savedAgent.id) {
                 await scriptsEditorRef.value.savePendingScripts(savedAgent.id);
            }

            emit('saved');
            
            if (shouldClose) {
                closeDrawer();
            } else {
                // If not closing (e.g. creating first, then adding scripts),
                // we need to switch to edit mode
                form.value.id = savedAgent.id;
                currentMode.value = 'edit';
                isEditing.value = true;
                // Also update form with saved data to be in sync
                const updatedPayload = buildAgentPayload(savedAgent);
                form.value = { ...form.value, ...updatedPayload };
            }
            
            message.success("保存成功");
        } else {
            const err = await res.json();
            message.error("保存失败: " + JSON.stringify(err));
        }
    } catch (e) {
        message.error("保存错误: " + e.message);
    } finally {
        isSaving.value = false;
    }
};
</script>

<style scoped>
@keyframes slide-in-right {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
.animate-slide-in-right {
    animation: slide-in-right 0.3s ease-out forwards;
}
@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}
.animate-fade-in {
    animation: fade-in 0.2s ease-out forwards;
}
</style>