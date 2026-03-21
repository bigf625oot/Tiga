<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Search, MoreHorizontal, CheckSquare, Square, Wand2, Copy } from 'lucide-vue-next';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ref } from 'vue';
import type { Role } from '../composables/useRBAC';

const props = defineProps<{
  query: string;
  showGrantedOnly: boolean;
  actionFilter: string[];
  availableActions: { id: string; name: string }[];
  isLockedRole: boolean;
  grantedCount: number;
  totalCount: number;
  roles: Role[];
}>();

const emit = defineEmits<{
  (e: 'update:query', val: string): void;
  (e: 'update:showGrantedOnly', val: boolean): void;
  (e: 'toggleAction', id: string): void;
  (e: 'clearActionFilter'): void;
  (e: 'applyBulk', checked: boolean): void;
  (e: 'applyTemplate', templateId: 'readonly' | 'editor' | 'admin'): void;
  (e: 'copyFromRole', roleId: string): void;
}>();

const selectedTemplate = ref<'readonly' | 'editor' | 'admin'>('readonly');
const selectedCopyRole = ref<string>('');
</script>

<template>
  <div class="flex flex-col gap-4 bg-muted/30 p-4 rounded-lg border dark:bg-slate-900/50 dark:border-slate-800">
    <!-- 上排：主要搜索与过滤 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex-1 max-w-md relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input 
          :model-value="query" 
          @update:model-value="(val) => emit('update:query', val as string)" 
          class="pl-9 bg-background" 
          placeholder="搜索资源、操作或模块..." 
        />
      </div>

      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2">
          <Switch 
            id="granted-only"
            :checked="showGrantedOnly" 
            @update:checked="(val) => emit('update:showGrantedOnly', val)" 
          />
          <label for="granted-only" class="text-sm font-medium cursor-pointer select-none">
            仅看已授权
          </label>
        </div>

        <div class="text-sm text-right min-w-[100px]">
          <span class="font-bold text-primary">{{ grantedCount }}</span>
          <span class="text-muted-foreground"> / {{ totalCount }}</span>
        </div>

        <!-- 高级操作收敛到下拉菜单 -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" :disabled="isLockedRole" class="gap-2">
              <MoreHorizontal class="w-4 h-4" />
              高级操作
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-56">
            <DropdownMenuLabel>批量处理</DropdownMenuLabel>
            <DropdownMenuItem @click="emit('applyBulk', true)">
              <CheckSquare class="w-4 h-4 mr-2" /> 勾选当前筛选结果
            </DropdownMenuItem>
            <DropdownMenuItem @click="emit('applyBulk', false)">
              <Square class="w-4 h-4 mr-2" /> 取消当前筛选结果
            </DropdownMenuItem>
            
            <DropdownMenuSeparator />
            <DropdownMenuLabel>快速应用</DropdownMenuLabel>
            
            <!-- 模板应用 -->
            <div class="px-2 py-1.5 space-y-2">
              <Select v-model="selectedTemplate">
                <SelectTrigger class="h-8 text-xs">
                  <SelectValue placeholder="选择预设模板" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel>权限模板</SelectLabel>
                    <SelectItem value="readonly">只读权限</SelectItem>
                    <SelectItem value="editor">编辑权限</SelectItem>
                    <SelectItem value="admin">全量管理员</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
              <Button size="sm" class="w-full h-8 text-xs" @click="emit('applyTemplate', selectedTemplate)">
                <Wand2 class="w-3 h-3 mr-2" /> 应用模板
              </Button>
            </div>

            <DropdownMenuSeparator />
            <DropdownMenuLabel>复制权限</DropdownMenuLabel>
            
            <!-- 复制角色 -->
            <div class="px-2 py-1.5 space-y-2">
              <Select v-model="selectedCopyRole">
                <SelectTrigger class="h-8 text-xs">
                  <SelectValue placeholder="选择来源角色" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel>可选角色</SelectLabel>
                    <SelectItem v-for="role in roles" :key="role.id" :value="role.id">
                      {{ role.name }}
                    </SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
              <Button 
                size="sm" 
                variant="secondary" 
                class="w-full h-8 text-xs" 
                :disabled="!selectedCopyRole"
                @click="emit('copyFromRole', selectedCopyRole)"
              >
                <Copy class="w-3 h-3 mr-2" /> 复制并覆盖
              </Button>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- 下排：操作类型快速过滤 -->
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-sm font-medium text-muted-foreground mr-2">操作过滤：</span>
      <Badge
        v-for="a in availableActions"
        :key="a.id"
        :variant="actionFilter.includes(a.id) ? 'default' : 'secondary'"
        class="cursor-pointer hover:bg-primary/80 transition-colors"
        @click="emit('toggleAction', a.id)"
      >
        {{ a.name }}
      </Badge>
      <Button 
        v-if="actionFilter.length > 0" 
        size="sm" 
        variant="ghost" 
        class="h-6 px-2 text-xs text-muted-foreground"
        @click="emit('clearActionFilter')"
      >
        清空过滤
      </Button>
    </div>
  </div>
</template>
