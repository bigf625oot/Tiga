<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  Database, 
  Bell, 
  Settings, 
  RotateCcw, 
  X,
  BookOpen,
  Library,
  Wrench,
  HardDrive,
  Settings2,
  Network,
  LineChart,
  Brain,
  Users,
  Building,
  Shield,
  Bot,
  Menu,
  Palette
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/toast/use-toast';

import DatabaseConnectionConfig from './components/DatabaseConnectionConfig.vue';
import AlertRulesConfig from './components/AlertRulesConfig.vue';
import RagConfig from './components/RagConfig.vue';
import LlmToolsConfig from './components/LlmToolsConfig.vue';
import StorageConfig from './components/StorageConfig.vue';
import BasicSettingsConfig from './components/BasicSettingsConfig.vue';
import KnowledgeGraphConfig from './components/KnowledgeGraphConfig.vue';
import AgentEvaluationConfig from './components/AgentEvaluationConfig.vue';
import ContextMemoryConfig from './components/ContextMemoryConfig.vue';
import UserConfig from './components/UserConfig.vue';
import DeptConfig from './components/DeptConfig.vue';
import RoleConfig from './components/RoleConfig.vue';
import PermissionConfig from './components/PermissionConfig.vue';
import KnowledgeBaseConfig from './components/KnowledgeBaseConfig.vue';
import AgentConfig from './components/AgentConfig.vue';
import MenuConfig from './components/MenuConfig.vue';
import EnterpriseCustomizationConfig from './components/EnterpriseCustomizationConfig.vue';

const { toast } = useToast();

const activeTab = ref('basic');

const menuGroups = [
  {
    id: 'system',
    label: '系统基础',
    items: [
      { id: 'basic', label: '基础设置', subLabel: '配置系统本地化、日志与核心业务开关', icon: Settings2 },
      // { id: 'menu', label: '菜单管理', subLabel: '管理系统导航菜单与路由配置', icon: Menu },
      { id: 'storage', label: '外部存储', subLabel: '配置 S3 等外部存储服务的连接参数', icon: HardDrive },
      { id: 'database', label: '数据连接', subLabel: '配置图数据库和向量数据库的连接信息', icon: Database },
    ]
  },
  {
    id: 'access',
    label: '权限管理',
    items: [
      { id: 'user', label: '用户管理', subLabel: '管理系统用户账号与基本信息', icon: Users },
      { id: 'dept', label: '部门管理', subLabel: '管理组织架构与部门信息', icon: Building },
      { id: 'role', label: '角色管理', subLabel: '管理系统角色与权限角色', icon: Shield },
      { id: 'permission', label: '权限配置', subLabel: '管理细粒度权限与访问控制', icon: Shield },
    ]
  },
  {
    id: 'knowledge',
    label: '知识智能',
    items: [
      { id: 'rag', label: '知识检索', subLabel: '配置文档入库时的解析和切分参数及检索策略', icon: Library },
      { id: 'knowledge_base', label: '知识库', subLabel: '配置知识库检索与 Rag 相关参数', icon: Library },
      { id: 'knowledge_graph', label: '知识图谱', subLabel: '配置图谱抽取的策略和本体规则', icon: Network },
      { id: 'context_memory', label: '会话记忆', subLabel: '配置会话的上下文及记忆机制', icon: Brain },
    ]
  },
  {
    id: 'model',
    label: '模型工具',
    items: [
      { id: 'llm_tools', label: '模型工具', subLabel: '配置各模型供应商的访问密钥和插件工具密钥', icon: Wrench },
      { id: 'agent_eval', label: '智能评估', subLabel: '配置智能体的评估指标和测试集', icon: LineChart },
    ]
  },
  {
    id: 'operations_management',
    label: '运营管理',
    items: [
      { id: 'enterprise_customization', label: '企业个性化', subLabel: '配置系统名称、系统LOGO、登录页背景等个性化信息', icon: Palette },
    ]
  },
  {
    id: 'operations',
    label: '运维监控',
    items: [
      { id: 'alert', label: '告警规则', subLabel: '配置系统运行状态的监控和告警规则', icon: Bell },
      { id: 'manual', label: '操作手册', subLabel: '查看系统使用文档和操作指南', icon: BookOpen, isExternal: true },
    ]
  }
];

const menuItems = menuGroups.flatMap(group => group.items);

const currentTabLabel = computed(() => {
  return menuItems.find(i => i.id === activeTab.value)?.label || '设置';
});

const currentTabDesc = computed(() => {
  return menuItems.find(i => i.id === activeTab.value)?.subLabel || '';
});

const handleReset = () => {
  toast({
    title: '重置配置',
    description: '配置已重置为默认值',
  });
};

const openDocs = () => {
  window.open('/docs/', '_blank');
};
</script>

<template>
  <div class="flex h-full w-full bg-background text-foreground overflow-hidden relative z-0">
    
    <!-- Left Sidebar -->
    <div class="w-64 flex flex-col border-r bg-card/50 backdrop-blur-sm z-10">
      <!-- Sidebar Header -->
      <div class="h-16 flex items-center px-6 border-b">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
            <Settings class="w-5 h-5" />
          </div>
          <div>
            <h1 class="font-semibold text-sm leading-tight">系统设置</h1>
          </div>
        </div>
      </div>

      <!-- Menu Items -->
      <ScrollArea class="flex-1">
        <div class="space-y-4 px-3 py-2">
          <div v-for="group in menuGroups" :key="group.id">
            <div class="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
              {{ group.label }}
            </div>
            <div class="space-y-0.5">
            <div
                v-for="item in group.items"
                :key="item.id"
                @click="item.isExternal ? openDocs() : activeTab = item.id"
                class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all hover:bg-muted/60"
                :class="{
                  'bg-muted text-foreground font-medium dark:glass-sidebar-item-active dark:bg-transparent': activeTab === item.id && !item.isExternal,
                  'text-muted-foreground': activeTab !== item.id || item.isExternal
                }"
              >
                <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-sm truncate">{{ item.label }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-full overflow-hidden relative bg-muted/10">
      <!-- Top Bar -->
      <div class="h-16 px-8 flex items-center justify-between shrink-0 bg-background/50 backdrop-blur z-10 border-b border-border">
        <div class="flex items-center gap-3">
          <h2 class="text-sm font-semibold leading-tight">{{ currentTabLabel }}</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-xs text-muted-foreground">{{ currentTabDesc }}</p>
        </div>
      </div>

      <!-- Content Scroll -->
      <ScrollArea class="flex-1">
        <div class="pb-20 px-8 pt-6">
          <div class="space-y-6 animate-in fade-in-50 duration-500 slide-in-from-bottom-2">
            
            <BasicSettingsConfig v-if="activeTab === 'basic'" />
            <MenuConfig v-if="activeTab === 'menu'" />
            <UserConfig v-if="activeTab === 'user'" />
            <DeptConfig v-if="activeTab === 'dept'" />
            <RoleConfig v-if="activeTab === 'role'" />
            <PermissionConfig v-if="activeTab === 'permission'" />
            <LlmToolsConfig v-if="activeTab === 'llm_tools'" />
            <RagConfig v-if="activeTab === 'rag'" />
            <KnowledgeBaseConfig v-if="activeTab === 'knowledge_base'" />
            <ContextMemoryConfig v-if="activeTab === 'context_memory'" />
            <KnowledgeGraphConfig v-if="activeTab === 'knowledge_graph'" />
            <AgentEvaluationConfig v-if="activeTab === 'agent_eval'" />
            <StorageConfig v-if="activeTab === 'storage'" />
            <DatabaseConnectionConfig v-if="activeTab === 'database'" />
            <AlertRulesConfig v-if="activeTab === 'alert'" />
            <EnterpriseCustomizationConfig v-if="activeTab === 'enterprise_customization'" />

          </div>
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
