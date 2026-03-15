<template>
  <Card 
    class="group relative overflow-hidden transition-all duration-300 cursor-pointer flex flex-col h-full min-h-[180px]" 
    :class="[
      'border-muted hover:shadow-lg hover:border-primary/40 bg-gradient-to-br from-card to-muted/10 hover:-translate-y-1'
    ]"
    @click="$emit('click', team)"
  >
    <CardHeader class="p-5 pb-3 space-y-0 relative z-10">
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-center gap-4 w-full overflow-hidden">
           <!-- Icon -->
           <div 
             class="h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden transition-all bg-primary/10 text-primary group-hover:scale-105"
           >
               <component :is="getTeamIcon(team)" class="h-6 w-6" />
           </div>
           
           <div class="space-y-1.5 flex-1 min-w-0 relative">
              <div class="flex items-center justify-between">
                <CardTitle class="text-base font-bold leading-tight tracking-tight truncate pr-8" :title="team.name">
                    {{ team.name }}
                </CardTitle>
                
                <!-- Actions (Dropdown) -->
                <div v-if="!team.is_readonly" @click.stop class="absolute right-[-8px] top-[-4px] opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <DropdownMenu>
                        <DropdownMenuTrigger as-child>
                            <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80">
                                <MoreVertical class="h-4 w-4 text-muted-foreground" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <slot name="actions"></slot>
                            <DropdownMenuItem @click="$emit('edit', team)" class="cursor-pointer">
                                <Edit2 class="mr-2 h-4 w-4" /> 编辑
                            </DropdownMenuItem>
                            <DropdownMenuItem @click="$emit('delete', team)" class="text-destructive focus:text-destructive cursor-pointer">
                                <Trash2 class="mr-2 h-4 w-4" /> 删除
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                 <Badge 
                   variant="secondary" 
                   class="text-[10px] font-medium px-1.5 py-0 h-5 rounded-md bg-secondary/50 text-secondary-foreground" 
                 >
                   {{ getModeLabel(team.mode) }}
                 </Badge>
                 <Badge 
                   v-if="team.is_readonly"
                   variant="outline" 
                   class="text-[10px] font-medium px-1.5 py-0 h-5 rounded-md text-muted-foreground bg-muted/50 border-0 flex items-center gap-1" 
                 >
                   <Shield class="h-3 w-3" /> 系统预设
                 </Badge>
              </div>
           </div>
        </div>
      </div>
    </CardHeader>
    
    <CardContent class="p-5 pt-2 pb-4 min-h-[5rem]">
       <p class="text-xs text-muted-foreground/80 line-clamp-3 leading-relaxed">
         {{ team.description || '暂无描述信息...' }}
       </p>
    </CardContent>
    
    <CardFooter class="p-5 pt-0 mt-auto border-t border-border/30 pt-3">
        <div class="w-full flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs text-muted-foreground">
              <span class="font-medium opacity-70">成员</span>
              <div class="flex -space-x-2 overflow-hidden py-0.5 pl-1">
                <div 
                  v-for="(memberId, idx) in team.members.slice(0, 5)" 
                  :key="idx"
                  class="h-6 w-6 rounded-full ring-2 flex items-center justify-center overflow-hidden transition-transform hover:scale-110 hover:z-10 relative"
                  :class="memberId === team.leader_id ? 'ring-amber-400 z-10' : 'ring-background'"
                  :title="getAgentName(memberId) + (memberId === team.leader_id ? ' (Leader)' : '')"
                >
                  <img :src="getAgentIcon(memberId)" class="h-full w-full object-cover" />
                  <div v-if="memberId === team.leader_id" class="absolute inset-0 bg-black/20 flex items-center justify-center">
                     <Crown class="h-3.5 w-3.5 text-amber-400 fill-amber-400 drop-shadow-md" />
                  </div>
                </div>
                <div v-if="team.members.length > 5" class="h-6 w-6 rounded-full ring-2 ring-background bg-muted flex items-center justify-center text-[9px] font-bold text-muted-foreground">
                  +{{ team.members.length - 5 }}
                </div>
              </div>
            </div>
            
            <span v-if="team.is_readonly" class="text-[10px] text-muted-foreground/40 font-mono">
                不可编辑
            </span>
        </div>
    </CardFooter>
  </Card>
</template>

<script setup>
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { MoreVertical, Edit2, Trash2, Shield, Crown, Users, Briefcase, Building, Globe, Star, Activity, Code, Database, Server, Cpu, MessageSquare, Search, Workflow, Network, Zap, Target, Rocket } from 'lucide-vue-next';

const props = defineProps({
  team: {
    type: Object,
    required: true
  },
  agents: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['click', 'edit', 'delete']);

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

const getIconComponent = (iconName) => {
  if (!iconName) return Users;
  const icon = availableIcons.find(i => i.name === iconName);
  return icon ? icon.component : Users;
};

const getTeamIcon = (team) => {
  if (team.is_readonly) return Shield;
  if (team.icon) return getIconComponent(team.icon);
  return Users;
};

const getModeLabel = (mode) => {
  const map = {
    'coordinate': '协调模式',
    'route': '路由模式',
    'broadcast': '广播模式',
    'tasks': '任务模式'
  };
  return map[mode] || mode;
};

const getAgentName = (agentId) => {
  const agent = props.agents.find(a => a.id === agentId);
  return agent ? agent.name : agentId;
};

const getAgentIcon = (agentId) => {
  const agent = props.agents.find(a => a.id === agentId);
  return agent && (agent.icon || agent.icon_url) ? (agent.icon || agent.icon_url) : '/tiga.svg'; 
};
</script>
