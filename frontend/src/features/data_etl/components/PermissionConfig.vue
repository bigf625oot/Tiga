<script setup lang="ts">
import { computed, ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/toast/use-toast';
import { AlertCircle, Save, Undo, ShieldAlert } from 'lucide-vue-next';

import { useRBAC } from '../composables/useRBAC';
import { usePermissionFilter } from '../composables/usePermissionFilter';
import PermissionToolbar from './PermissionToolbar.vue';
import PermissionTable from './PermissionTable.vue';

const { toast } = useToast();

const {
  roles,
  activeRoleId,
  activeRole,
  hasUnsavedChanges,
  selectRole,
  hasPermission,
  togglePermission,
  replaceActiveRolePermissions,
  bulkTogglePermissions,
  saveConfig,
  discardChanges,
  MODULES
} = useRBAC();

const activeTab = ref(MODULES[0]?.id ?? 'system');

const {
  query,
  showGrantedOnly,
  actionFilter,
  availableActions,
  toggleAction,
  clearActionFilter,
  resourcesForModule,
  getVisiblePermissionCodesInModule,
} = usePermissionFilter(MODULES, hasPermission);

const isLockedRole = computed(() => !!activeRole.value?.isSystem || !!activeRole.value?.permissions.includes('*'));

const allPermissionCodes = computed(() => {
  const codes: string[] = [];
  for (const m of MODULES) {
    for (const r of m.resources) {
      for (const a of r.actions) {
        codes.push(`${r.id}:${a.id}`);
      }
    }
  }
  return codes;
});

const grantedPermissionCount = computed(() => {
  const role = activeRole.value;
  if (!role) return 0;
  if (role.permissions.includes('*')) return allPermissionCodes.value.length;
  return new Set(role.permissions).size;
});

const totalPermissionCount = computed(() => allPermissionCodes.value.length);

const handleSelectRole = (id: string) => {
  try {
    selectRole(id);
  } catch (e: any) {
    if (e.message === 'UNSAVED_CHANGES') {
      toast({
        title: '无法切换角色',
        description: '您有未保存的更改，请先保存或撤销后再切换角色。',
        variant: 'destructive',
      });
    }
  }
};

const handleSave = async () => {
  await saveConfig();
  toast({ title: '保存成功', description: '权限配置已更新' });
};

const handleDiscard = () => {
  discardChanges();
  toast({ title: '已撤销', description: '所有未保存的更改已撤销' });
};

// 弹窗状态
const confirmOpen = ref(false);
const pendingApply = ref<null | { title: string; description: string; permissions: string[] }>(null);

const openConfirmApply = (payload: { title: string; description: string; permissions: string[] }) => {
  if (isLockedRole.value) return;
  pendingApply.value = payload;
  confirmOpen.value = true;
};

const applyPending = () => {
  if (!pendingApply.value) return;
  replaceActiveRolePermissions(pendingApply.value.permissions);
  toast({ title: '已应用', description: pendingApply.value.description });
  confirmOpen.value = false;
  pendingApply.value = null;
};

// 批量与高级操作
const handleApplyBulk = (checked: boolean) => {
  if (isLockedRole.value) return;
  const codes = getVisiblePermissionCodesInModule(activeTab.value);
  if (codes.length === 0) {
    toast({ title: '当前视图无可用权限', variant: 'destructive' });
    return;
  }
  bulkTogglePermissions(codes, checked);
  toast({
    title: checked ? '批量勾选完成' : '批量取消完成',
    description: `已${checked ? '勾选' : '取消'}当前模块视图内 ${codes.length} 项权限`,
  });
};

const handleApplyTemplate = (templateId: 'readonly' | 'editor' | 'admin') => {
  const readOnly = new Set(['read', 'export']);
  const editor = new Set(['read', 'write', 'export', 'execute']);

  let codes: string[] = [];
  if (templateId === 'admin') {
    codes = allPermissionCodes.value;
  } else {
    const allowed = templateId === 'readonly' ? readOnly : editor;
    for (const m of MODULES) {
      for (const r of m.resources) {
        for (const a of r.actions) {
          if (allowed.has(a.id)) codes.push(`${r.id}:${a.id}`);
        }
      }
    }
  }

  const labels = { readonly: '只读模板', editor: '编辑模板', admin: '管理员模板' };
  openConfirmApply({
    title: `应用${labels[templateId]}`,
    description: `将当前角色权限替换为模板（共 ${codes.length} 项）`,
    permissions: codes,
  });
};

const handleCopyFromRole = (roleId: string) => {
  const src = roles.value.find((r) => r.id === roleId);
  if (!src) return;
  const codes = src.permissions.includes('*') ? allPermissionCodes.value : src.permissions;
  openConfirmApply({
    title: `复制权限：${src.name}`,
    description: `将当前角色权限替换为“${src.name}”（共 ${codes.length} 项）`,
    permissions: codes,
  });
};

// 表格单行操作
const isRowFullySelectedInView = (resourceId: string, visibleActionIds: string[]) => {
  if (!activeRole.value) return false;
  if (activeRole.value.permissions.includes('*')) return true;
  if (visibleActionIds.length === 0) return false;
  return visibleActionIds.every((a) => hasPermission(resourceId, a));
};

const handleToggleRow = (resourceId: string, visibleActionIds: string[], checked: boolean) => {
  if (isLockedRole.value) return;
  const codes = visibleActionIds.map((a) => `${resourceId}:${a}`);
  bulkTogglePermissions(codes, checked);
};
</script>

<template>
  <div class="space-y-6 max-w-[1400px] mx-auto">
    <!-- 顶部全局上下文区 -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">

      <div class="flex items-center gap-3 w-full sm:w-auto bg-muted/30 p-1.5 rounded-lg border dark:bg-slate-900/50 dark:border-slate-800">
        <div class="flex items-center gap-2 px-2">
          <span class="text-sm font-medium text-muted-foreground whitespace-nowrap">当前角色:</span>
          <Select :model-value="activeRoleId" @update:model-value="handleSelectRole">
            <SelectTrigger class="w-[180px] h-8 border-transparent bg-transparent hover:bg-muted font-semibold">
              <SelectValue placeholder="请选择角色" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem v-for="role in roles" :key="role.id" :value="role.id">
                  <div class="flex items-center gap-2">
                    {{ role.name }}
                    <ShieldAlert v-if="role.isSystem" class="w-3 h-3 text-amber-500" />
                  </div>
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <div class="h-6 w-px bg-border mx-1"></div>

        <div class="flex items-center gap-2 pr-1">
          <Badge v-if="hasUnsavedChanges" variant="destructive" class="flex items-center gap-1 animate-in fade-in zoom-in">
            <AlertCircle class="w-3 h-3" /> 未保存
          </Badge>
          <Button v-if="hasUnsavedChanges" variant="ghost" size="sm" class="h-8" @click="handleDiscard">
            <Undo class="w-4 h-4 mr-1.5" />
            撤销
          </Button>
          <Button size="sm" class="h-8" :disabled="!hasUnsavedChanges" @click="handleSave">
            <Save class="w-4 h-4 mr-1.5" />
            保存
          </Button>
        </div>
      </div>
    </div>

    <!-- 锁定提示 -->
    <div v-if="isLockedRole" class="flex items-center gap-3 px-4 py-3 rounded-md bg-amber-50 border border-amber-200 text-amber-800 dark:bg-amber-950/30 dark:border-amber-900/50 dark:text-amber-300">
      <ShieldAlert class="w-5 h-5 shrink-0 text-amber-500" />
      <div class="text-sm">
        <span class="font-semibold">系统内置角色或超级权限：</span>
        该角色拥有全局预设权限，当前视图仅供查看，不支持修改。
      </div>
    </div>

    <!-- 中间工具栏（视图控制与高级操作） -->
    <PermissionToolbar
      v-model:query="query"
      v-model:showGrantedOnly="showGrantedOnly"
      :actionFilter="actionFilter"
      :availableActions="availableActions"
      :isLockedRole="isLockedRole"
      :grantedCount="grantedPermissionCount"
      :totalCount="totalPermissionCount"
      :roles="roles"
      @toggleAction="toggleAction"
      @clearActionFilter="clearActionFilter"
      @applyBulk="handleApplyBulk"
      @applyTemplate="handleApplyTemplate"
      @copyFromRole="handleCopyFromRole"
    />

    <!-- 底部内容区（模块Tabs与权限矩阵） -->
    <Card class="border-none shadow-sm ring-1 ring-slate-200 dark:ring-slate-800">
      <CardContent class="p-0">
        <Tabs v-model="activeTab" class="flex flex-col w-full">
          <div class="px-6 border-b bg-muted/10 dark:bg-slate-900/20 dark:border-slate-800">
            <TabsList class="h-14 bg-transparent p-0 gap-8">
              <TabsTrigger
                v-for="module in MODULES"
                :key="module.id"
                :value="module.id"
                class="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary rounded-none px-1 h-full font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {{ module.name }}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea class="h-[calc(100vh-26rem)] min-h-[400px]">
            <div class="p-6">
              <TabsContent
                v-for="module in MODULES"
                :key="module.id"
                :value="module.id"
                class="m-0 focus-visible:outline-none"
              >
                <PermissionTable
                  :resources="resourcesForModule(module.id)"
                  :isLockedRole="isLockedRole"
                  :hasPermission="hasPermission"
                  :isRowFullySelected="isRowFullySelectedInView"
                  @togglePermission="togglePermission"
                  @toggleRow="handleToggleRow"
                />
              </TabsContent>
            </div>
          </ScrollArea>
        </Tabs>
      </CardContent>
    </Card>

    <!-- 确认弹窗 -->
    <Dialog v-model:open="confirmOpen">
      <DialogContent class="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{{ pendingApply?.title }}</DialogTitle>
          <DialogDescription class="pt-2">
            {{ pendingApply?.description }}
            <div v-if="hasUnsavedChanges" class="mt-2 text-destructive font-medium flex items-center gap-1.5">
              <AlertCircle class="w-4 h-4" /> 警告：将覆盖您当前的未保存更改
            </div>
          </DialogDescription>
        </DialogHeader>
        <div class="text-sm text-muted-foreground bg-muted/50 p-3 rounded-md">
          操作应用后将进入未保存状态，您可以继续微调，或使用顶部“撤销”按钮恢复。
        </div>
        <DialogFooter class="mt-4">
          <Button variant="outline" @click="confirmOpen = false">取消</Button>
          <Button @click="applyPending">确认应用</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
