<script setup lang="ts">
import { ref, computed } from 'vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import { Pencil, Shield, Trash2, Plus } from 'lucide-vue-next';

// 1. 数据模型定义 (Data Models)
interface Role {
  id: string;
  name: string;
}

interface User {
  id: string;
  name: string;
}

interface Menu {
  id: string;
  name: string;
  path: string;
  icon: string;
  order: number;
  status: boolean;
  roles: string[]; // 授权的角色ID列表
  users: string[]; // 授权的用户ID列表
}

// 2. 模拟数据 (Mock Data)
const roles = ref<Role[]>([
  { id: 'r1', name: '超级管理员' },
  { id: 'r2', name: '部门主管' },
  { id: 'r3', name: '普通员工' },
]);

const users = ref<User[]>([
  { id: 'u1', name: '张三' },
  { id: 'u2', name: '李四' },
  { id: 'u3', name: '王五' },
]);

const menus = ref<Menu[]>([
  { id: '1', name: '系统设置', path: '/settings', icon: 'Settings', order: 1, status: true, roles: ['r1'], users: [] },
  { id: '2', name: '用户管理', path: '/users', icon: 'Users', order: 2, status: true, roles: ['r1', 'r2'], users: ['u1'] },
  { id: '3', name: '部门管理', path: '/departments', icon: 'Building', order: 3, status: true, roles: ['r1', 'r2'], users: [] },
  { id: '4', name: '角色管理', path: '/roles', icon: 'Shield', order: 4, status: true, roles: ['r1'], users: [] },
  { id: '5', name: '权限配置', path: '/permissions', icon: 'Lock', order: 5, status: false, roles: ['r1'], users: [] },
]);

const { toast } = useToast();

// 3. 状态管理 (State Management)
// 3.1 菜单编辑对话框 (Menu Edit Dialog)
const isMenuDialogOpen = ref(false);
const editingMenuId = ref<string | null>(null);
const menuForm = ref<Omit<Menu, 'id' | 'roles' | 'users'>>({
  name: '',
  path: '',
  icon: 'Settings',
  order: 1,
  status: true,
});

// 3.2 授权对话框 (Authorization Dialog)
const isAuthDialogOpen = ref(false);
const activeAuthMenuId = ref<string | null>(null);
const authForm = ref<{ roles: string[]; users: string[] }>({ roles: [], users: [] });

// 3.3 删除确认对话框 (Delete Alert Dialog)
const isDeleteDialogOpen = ref(false);
const deletingMenuId = ref<string | null>(null);

// 4. 计算属性 (Computed Properties)
const activeAuthMenuName = computed(() => {
  return menus.value.find(m => m.id === activeAuthMenuId.value)?.name || '';
});

const isMenuFormValid = computed(() => {
  return menuForm.value.name.trim() !== '' && menuForm.value.path.trim() !== '';
});

// 5. 动作处理器 (Action Handlers)
// 5.1 菜单管理 (Menu Management)
const openAddMenuDialog = () => {
  editingMenuId.value = null;
  menuForm.value = {
    name: '',
    path: '',
    icon: 'Settings',
    order: menus.value.length + 1,
    status: true,
  };
  isMenuDialogOpen.value = true;
};

const openEditMenuDialog = (menu: Menu) => {
  editingMenuId.value = menu.id;
  menuForm.value = {
    name: menu.name,
    path: menu.path,
    icon: menu.icon,
    order: menu.order,
    status: menu.status,
  };
  isMenuDialogOpen.value = true;
};

const saveMenu = () => {
  if (!isMenuFormValid.value) return;

  if (editingMenuId.value) {
    const idx = menus.value.findIndex(m => m.id === editingMenuId.value);
    if (idx !== -1) {
      menus.value[idx] = { ...menus.value[idx], ...menuForm.value };
      toast({ title: '保存成功', description: `菜单 [${menuForm.value.name}] 已更新` });
    }
  } else {
    const newMenu: Menu = {
      ...menuForm.value,
      id: String(Date.now()),
      roles: [],
      users: [],
    };
    menus.value.push(newMenu);
    toast({ title: '创建成功', description: `菜单 [${menuForm.value.name}] 已创建` });
  }
  isMenuDialogOpen.value = false;
};

// 5.2 状态切换 (Toggle Status)
const toggleMenuStatus = (menu: Menu, newStatus: boolean) => {
  menu.status = newStatus;
  toast({
    title: '状态已更新',
    description: `菜单 [${menu.name}] 已${newStatus ? '启用' : '禁用'}`,
  });
};

// 5.3 授权管理 (Authorization Management)
const openAuthDialog = (menu: Menu) => {
  activeAuthMenuId.value = menu.id;
  authForm.value = { roles: [...menu.roles], users: [...menu.users] };
  isAuthDialogOpen.value = true;
};

const saveAuth = () => {
  if (activeAuthMenuId.value) {
    const idx = menus.value.findIndex(m => m.id === activeAuthMenuId.value);
    if (idx !== -1) {
      menus.value[idx].roles = [...authForm.value.roles];
      menus.value[idx].users = [...authForm.value.users];
      toast({ title: '授权成功', description: `已更新 [${menus.value[idx].name}] 的访问权限` });
    }
  }
  isAuthDialogOpen.value = false;
};

const handleRoleChange = (roleId: string, checked: boolean) => {
  if (checked) {
    if (!authForm.value.roles.includes(roleId)) authForm.value.roles.push(roleId);
  } else {
    authForm.value.roles = authForm.value.roles.filter(id => id !== roleId);
  }
};

const handleUserChange = (userId: string, checked: boolean) => {
  if (checked) {
    if (!authForm.value.users.includes(userId)) authForm.value.users.push(userId);
  } else {
    authForm.value.users = authForm.value.users.filter(id => id !== userId);
  }
};

// 5.4 删除菜单 (Delete Menu)
const confirmDeleteMenu = (menuId: string) => {
  deletingMenuId.value = menuId;
  isDeleteDialogOpen.value = true;
};

const deleteMenu = () => {
  if (deletingMenuId.value) {
    const idx = menus.value.findIndex(m => m.id === deletingMenuId.value);
    if (idx !== -1) {
      const name = menus.value[idx].name;
      menus.value.splice(idx, 1);
      toast({ title: '删除成功', description: `菜单 [${name}] 已删除` });
    }
  }
  isDeleteDialogOpen.value = false;
  deletingMenuId.value = null;
};

// 6. 辅助函数 (Helpers)
const getRoleNames = (roleIds: string[]) => {
  return roleIds.map(id => roles.value.find(r => r.id === id)?.name).filter(Boolean).join(', ');
};

const getUserNames = (userIds: string[]) => {
  return userIds.map(id => users.value.find(u => u.id === id)?.name).filter(Boolean).join(', ');
};
</script>

<template>
  <div class="space-y-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader class="flex flex-row items-center justify-between">
        <div>
          <CardTitle class="dark:text-slate-50 text-lg font-bold">菜单配置</CardTitle>
          <CardDescription class="dark:text-slate-400 mt-2">管理系统导航菜单与路由配置，并分配角色和用户权限。</CardDescription>
        </div>
        <Button @click="openAddMenuDialog">
          <Plus class="w-4 h-4 mr-2" />
          新增菜单
        </Button>
      </CardHeader>
      <CardContent>
        <div class="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader class="bg-muted/50 dark:bg-slate-900">
              <TableRow>
                <TableHead>菜单名称</TableHead>
                <TableHead>路由路径</TableHead>
                <TableHead>图标</TableHead>
                <TableHead>排序</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>授权信息</TableHead>
                <TableHead class="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody class="divide-y dark:divide-slate-800">
              <TableRow v-for="menu in menus" :key="menu.id" class="dark:hover:bg-slate-900/50">
                <TableCell class="font-medium dark:text-slate-300">{{ menu.name }}</TableCell>
                <TableCell class="font-mono text-xs text-muted-foreground">{{ menu.path }}</TableCell>
                <TableCell class="dark:text-slate-300">{{ menu.icon }}</TableCell>
                <TableCell class="dark:text-slate-300">{{ menu.order }}</TableCell>
                <TableCell>
                  <Switch
                    :checked="menu.status"
                    @update:checked="val => toggleMenuStatus(menu, val)"
                  />
                </TableCell>
                <TableCell>
                  <div class="flex flex-col gap-1">
                    <TooltipProvider v-if="menu.roles.length > 0">
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Badge variant="outline" class="w-fit cursor-help">
                            {{ menu.roles.length }} 个角色
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{{ getRoleNames(menu.roles) }}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <TooltipProvider v-if="menu.users.length > 0">
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Badge variant="secondary" class="w-fit cursor-help">
                            {{ menu.users.length }} 个用户
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{{ getUserNames(menu.users) }}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <span v-if="menu.roles.length === 0 && menu.users.length === 0" class="text-xs text-muted-foreground">
                      未授权
                    </span>
                  </div>
                </TableCell>
                <TableCell class="text-right">
                  <div class="flex items-center justify-end gap-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button variant="ghost" size="icon" @click="openAuthDialog(menu)">
                            <Shield class="w-4 h-4 text-blue-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>分配权限</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button variant="ghost" size="icon" @click="openEditMenuDialog(menu)">
                            <Pencil class="w-4 h-4 text-amber-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>编辑菜单</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button variant="ghost" size="icon" @click="confirmDeleteMenu(menu.id)">
                            <Trash2 class="w-4 h-4 text-red-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>删除菜单</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow v-if="menus.length === 0">
                <TableCell colspan="7" class="h-24 text-center text-muted-foreground">
                  暂无菜单数据
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>

    <!-- 菜单编辑/新增弹窗 -->
    <Dialog v-model:open="isMenuDialogOpen">
      <DialogContent class="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{{ editingMenuId ? '编辑菜单' : '新增菜单' }}</DialogTitle>
          <DialogDescription>
            填写菜单的基本信息，如名称、路径等。带 * 的为必填项。
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="name" class="text-right">菜单名称 <span class="text-red-500">*</span></Label>
            <Input id="name" v-model="menuForm.name" class="col-span-3" placeholder="例如：用户管理" />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="path" class="text-right">路由路径 <span class="text-red-500">*</span></Label>
            <Input id="path" v-model="menuForm.path" class="col-span-3" placeholder="例如：/users" />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="icon" class="text-right">图标</Label>
            <Input id="icon" v-model="menuForm.icon" class="col-span-3" placeholder="Lucide 图标名称" />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="order" class="text-right">排序</Label>
            <Input id="order" type="number" v-model.number="menuForm.order" class="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isMenuDialogOpen = false">取消</Button>
          <Button @click="saveMenu" :disabled="!isMenuFormValid">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 授权弹窗 -->
    <Dialog v-model:open="isAuthDialogOpen">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>分配权限 - {{ activeAuthMenuName }}</DialogTitle>
          <DialogDescription>
            选择哪些角色和用户可以访问该菜单。
          </DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="roles" class="w-full mt-4">
          <TabsList class="grid w-full grid-cols-2">
            <TabsTrigger value="roles">按角色授权</TabsTrigger>
            <TabsTrigger value="users">按用户授权</TabsTrigger>
          </TabsList>
          <TabsContent value="roles" class="space-y-4 py-4">
            <div v-for="role in roles" :key="role.id" class="flex items-center space-x-2">
              <Checkbox
                :id="`role-${role.id}`"
                :checked="authForm.roles.includes(role.id)"
                @update:checked="(val) => handleRoleChange(role.id, !!val)"
              />
              <Label :for="`role-${role.id}`" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                {{ role.name }}
              </Label>
            </div>
            <div v-if="roles.length === 0" class="text-sm text-muted-foreground">暂无角色数据</div>
          </TabsContent>
          <TabsContent value="users" class="space-y-4 py-4">
            <div v-for="user in users" :key="user.id" class="flex items-center space-x-2">
              <Checkbox
                :id="`user-${user.id}`"
                :checked="authForm.users.includes(user.id)"
                @update:checked="(val) => handleUserChange(user.id, !!val)"
              />
              <Label :for="`user-${user.id}`" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                {{ user.name }}
              </Label>
            </div>
            <div v-if="users.length === 0" class="text-sm text-muted-foreground">暂无用户数据</div>
          </TabsContent>
        </Tabs>
        <DialogFooter>
          <Button variant="outline" @click="isAuthDialogOpen = false">取消</Button>
          <Button @click="saveAuth">保存授权</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除确认弹窗 -->
    <AlertDialog v-model:open="isDeleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除？</AlertDialogTitle>
          <AlertDialogDescription>
            此操作无法撤销。这将永久删除该菜单及其所有相关的权限配置。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="isDeleteDialogOpen = false">取消</AlertDialogCancel>
          <AlertDialogAction class="bg-red-500 hover:bg-red-600" @click="deleteMenu">
            确认删除
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>
