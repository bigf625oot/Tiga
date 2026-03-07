<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  LayoutDashboard, 
  Database, 
  Bell, 
  Settings, 
  RotateCcw, 
  X 
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/toast/use-toast';

import ModelConfig from './components/ModelConfig.vue';
import DatabaseConnectionConfig from './components/DatabaseConnectionConfig.vue';
import AlertRulesConfig from './components/AlertRulesConfig.vue';

const { toast } = useToast();

const activeTab = ref('model');

const menuItems = [
  { 
    id: 'model', 
    label: '模型配置', 
    subLabel: 'LLM & Embedding',
    icon: LayoutDashboard 
  },
  { 
    id: 'database', 
    label: '数据库连接', 
    subLabel: 'Neo4j & Vector DB',
    icon: Database 
  },
  { 
    id: 'alert', 
    label: '告警规则', 
    subLabel: '系统监控告警',
    icon: Bell 
  },
];

const currentTabLabel = computed(() => {
  return menuItems.find(i => i.id === activeTab.value)?.label || '设置';
});

const handleReset = () => {
  toast({
    title: '重置配置',
    description: '配置已重置为默认值',
  });
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
            <p class="text-[10px] text-muted-foreground">System Settings</p>
          </div>
        </div>
      </div>

      <!-- Menu Items -->
      <ScrollArea class="flex-1 py-4">
        <div class="space-y-1 px-2">
          <Button
            v-for="item in menuItems"
            :key="item.id"
            variant="ghost"
            class="w-full justify-start h-auto py-3 px-4 relative overflow-hidden transition-all duration-200"
            :class="{ 
              'bg-primary/10 text-primary hover:bg-primary/15': activeTab === item.id,
              'text-muted-foreground hover:bg-muted': activeTab !== item.id
            }"
            @click="activeTab = item.id"
          >
            <!-- Active Indicator -->
            <div v-if="activeTab === item.id" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-primary"></div>
            
            <component :is="item.icon" class="w-5 h-5 mr-3 shrink-0" />
            
            <div class="flex flex-col items-start text-left overflow-hidden">
              <span class="text-sm font-medium leading-none mb-1">{{ item.label }}</span>
              <span class="text-[10px] opacity-70 truncate w-full">{{ item.subLabel }}</span>
            </div>
          </Button>
        </div>
      </ScrollArea>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-full overflow-hidden relative bg-muted/10">
      <!-- Top Bar -->
      <div class="h-16 px-8 flex items-center justify-between shrink-0 bg-background/50 backdrop-blur border-b z-10">
        <div class="flex items-center gap-4">
          <h2 class="text-lg font-semibold">{{ currentTabLabel }}</h2>
          <Badge variant="secondary" class="font-mono text-[10px] tracking-wider uppercase">Admin</Badge>
        </div>
        
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="sm" class="text-muted-foreground hover:text-primary gap-2" @click="handleReset">
            <RotateCcw class="w-3.5 h-3.5" />
            重置配置
          </Button>
          <Separator orientation="vertical" class="h-6 mx-2" />
          <Button variant="ghost" size="icon" class="text-muted-foreground hover:text-destructive">
            <X class="w-5 h-5" />
          </Button>
        </div>
      </div>

      <!-- Content Scroll -->
      <ScrollArea class="flex-1">
        <div class="p-8 max-w-5xl mx-auto pb-20">
          <div class="space-y-6 animate-in fade-in-50 duration-500 slide-in-from-bottom-2">
            
            <ModelConfig v-if="activeTab === 'model'" />
            <DatabaseConnectionConfig v-if="activeTab === 'database'" />
            <AlertRulesConfig v-if="activeTab === 'alert'" />

          </div>
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
