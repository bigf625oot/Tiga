<template>
  <Card 
    class="group relative overflow-hidden transition-all duration-300 cursor-pointer flex flex-col h-full min-h-[180px]" 
    :class="[
      selected 
        ? 'border-primary shadow-md bg-primary/5 ring-1 ring-primary' 
        : 'border-muted hover:shadow-lg hover:border-primary/40 bg-gradient-to-br from-card to-muted/10 hover:-translate-y-1'
    ]"
    @click="$emit('click', agent)"
  >
    <!-- Background Gradient for Templates -->
    <div v-if="isTemplate" class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-bl-full -mr-8 -mt-8 transition-opacity opacity-50 group-hover:opacity-100"></div>

    <CardHeader class="p-5 pb-3 space-y-0 relative z-10">
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-center gap-4 w-full overflow-hidden">
           <!-- Icon -->
           <div 
             class="h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden  transition-all"
             :class="isTemplate ? 'bg-gradient-to-br from-muted/50 to-muted' : 'bg-white dark:bg-transparent'"
           >
               <img v-if="isImage" :src="agent.icon" class="h-full w-full object-cover" />
               <component v-else :is="agent.iconComponent" class="h-6 w-6 text-foreground/80" />
           </div>
           
           <div class="space-y-1.5 flex-1 min-w-0 relative">
              <div class="flex items-center justify-between">
                <CardTitle class="text-base font-bold leading-tight tracking-tight truncate pr-8" :title="agent.name">
                    {{ agent.name }}
                </CardTitle>
                
                <!-- Actions (Dropdown) -->
                <div v-if="!isTemplate" @click.stop class="absolute right-[-8px] top-[-4px] opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <DropdownMenu>
                        <DropdownMenuTrigger as-child>
                            <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80">
                                <MoreVertical class="h-4 w-4 text-muted-foreground" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem @click="$emit('edit', agent)" class="cursor-pointer">
                                <Edit class="mr-2 h-4 w-4" /> 编辑
                            </DropdownMenuItem>
                            <DropdownMenuItem @click="$emit('delete', agent)" class="text-destructive focus:text-destructive cursor-pointer">
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
                   v-if="isTemplate"
                 >
                   模版
                 </Badge>
                 <Badge 
                   variant="outline" 
                   class="text-[10px] font-medium px-1.5 py-0 h-5 rounded-md text-primary bg-primary/5 border-primary/20" 
                   v-else
                 >
                   我的助手
                 </Badge>
                 <span v-if="agent.category" class="text-[10px] text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded-md truncate max-w-[80px]">
                    {{ agent.category }}
                 </span>
              </div>
           </div>
        </div>
      </div>
    </CardHeader>
    
    <CardContent class="p-5 pt-2 pb-4 min-h-[5rem]">
       <p class="text-xs text-muted-foreground/80 line-clamp-3 leading-relaxed">
         {{ agent.description || '暂无描述信息...' }}
       </p>
    </CardContent>
    
    <CardFooter class="p-5 pt-0 flex items-center justify-between mt-auto border-t border-border/30 pt-3">
        <div class="flex items-center gap-2">
            <div class="relative flex h-2 w-2">
              <span v-if="agent.is_active !== false" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" :class="agent.is_active !== false ? 'bg-green-500' : 'bg-slate-300'"></span>
            </div>
            <span class="text-[10px] text-muted-foreground font-medium">{{ agent.is_active !== false ? '运行中' : '未启用' }}</span>
        </div>
        <span class="text-[10px] text-muted-foreground/40 font-mono opacity-0 group-hover:opacity-100 transition-opacity">ID: {{ agent.id ? agent.id.substring(0, 6) : '---' }}</span>
    </CardFooter>
  </Card>
</template>

<script setup>
import { computed } from 'vue';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { MoreVertical, Edit, Trash2 } from 'lucide-vue-next';

const props = defineProps({
  agent: {
    type: Object,
    required: true
  },
  selected: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['click', 'edit', 'delete']);

const isTemplate = computed(() => props.agent.is_template);

const isImage = computed(() => {
    const icon = props.agent.icon;
    if (!icon || typeof icon !== 'string') return false;
    const value = icon.trim();
    if (!value) return false;
    if (value.startsWith('data:image')) return true;
    if (value.startsWith('blob:')) return true;
    if (/^https?:\/\//i.test(value)) return true;
    if (value.startsWith('/') || value.startsWith('./') || value.startsWith('../')) return true;
    return /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i.test(value);
});
</script>
