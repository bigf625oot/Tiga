<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue
} from '@/components/ui/select';
import {
  Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle
} from '@/components/ui/sheet';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger
} from '@/components/ui/alert-dialog';
import { useToast } from '@/components/ui/toast/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Search, Plus, Pencil, Trash2, KeyRound, Download, Upload, RefreshCw, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, MoreHorizontal, ShieldCheck, UserX, CheckCircle2, XCircle, Users } from 'lucide-vue-next';

interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
}

interface Department {
  id: number;
  name: string;
  parent_id?: number;
}

interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  role: Role;
  role_id: number;
  department?: Department;
  department_id?: number;
  status: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

interface UserFormData {
  id?: number;
  username: string;
  email: string;
  phone: string;
  role_id: string | undefined;
  department_id: string | undefined;
  password?: string;
}

interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

const { toast } = useToast();

const roles = ref<Role[]>([
  { id: 1, name: '超级管理员', code: 'super_admin', description: '系统最高权限' },
  { id: 2, name: '管理员', code: 'admin', description: '管理权限' },
  { id: 3, name: '普通用户', code: 'user', description: '常规操作' },
  { id: 4, name: '访客', code: 'guest', description: '只读权限' },
]);

const departments = ref<Department[]>([
  { id: 1, name: '技术研发部' },
  { id: 2, name: '产品设计部' },
  { id: 3, name: '市场营销部' },
  { id: 4, name: '人力资源部' },
]);

const mockUsers: User[] = [
  { id: 1, username: 'admin', email: 'admin@example.com', phone: '13800138000', role: roles.value[0], role_id: 1, department: departments.value[0], department_id: 1, status: true, last_login_at: '2026-03-20 14:30:00', created_at: '2025-01-15 08:00:00', updated_at: '2026-03-15 10:20:00' },
  { id: 2, username: 'zhang_san', email: 'zhangsan@example.com', phone: '13800138001', role: roles.value[2], role_id: 3, department: departments.value[0], department_id: 1, status: true, last_login_at: '2026-03-21 09:15:00', created_at: '2025-03-10 14:30:00', updated_at: '2026-03-10 14:30:00' },
  { id: 3, username: 'li_si', email: 'lisi@example.com', phone: '13800138002', role: roles.value[2], role_id: 3, department: departments.value[1], department_id: 2, status: true, last_login_at: '2026-03-19 16:45:00', created_at: '2025-04-20 09:00:00', updated_at: '2026-03-19 16:45:00' },
  { id: 4, username: 'wang_wu', email: 'wangwu@example.com', phone: '13800138003', role: roles.value[3], role_id: 4, department: departments.value[2], department_id: 3, status: false, created_at: '2025-06-01 11:00:00', updated_at: '2026-02-28 15:30:00' },
  { id: 5, username: 'zhao_liu', email: 'zhaoliu@example.com', phone: '13800138004', role: roles.value[1], role_id: 2, department: departments.value[0], department_id: 1, status: true, last_login_at: '2026-03-21 11:00:00', created_at: '2025-02-15 10:00:00', updated_at: '2026-03-20 09:30:00' },
];

const users = ref<User[]>([...mockUsers]);
const selectedUsers = ref<number[]>([]);
const isLoading = ref(false);
const searchQuery = ref('');
const statusFilter = ref<'all' | 'active' | 'inactive'>('all');
const roleFilter = ref<string>('all');

const pagination = reactive<PaginationState>({
  page: 1,
  pageSize: 10,
  total: 0,
});

const isDialogOpen = ref(false);
const isDeleteDialogOpen = ref(false);
const isResetPasswordDialogOpen = ref(false);
const isBulkDeleteDialogOpen = ref(false);
const isBulkStatusDialogOpen = ref(false);
const currentUser = ref<User | null>(null);
const bulkNewStatus = ref(true);

const userForm = reactive<UserFormData>({
  username: '',
  email: '',
  phone: '',
  role_id: undefined,
  department_id: undefined,
  password: '',
});

const formErrors = reactive<Partial<Record<keyof UserFormData, string>>>({});

const filteredUsers = computed(() => {
  let result = users.value;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(u =>
      u.username.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query) ||
      (u.phone && u.phone.includes(query))
    );
  }

  if (statusFilter.value !== 'all') {
    result = result.filter(u => statusFilter.value === 'active' ? u.status : !u.status);
  }

  if (roleFilter.value !== 'all') {
    result = result.filter(u => u.role_id === Number(roleFilter.value));
  }

  return result;
});

const paginatedUsers = computed(() => {
  const start = (pagination.page - 1) * pagination.pageSize;
  const end = start + pagination.pageSize;
  pagination.total = filteredUsers.value.length;
  return filteredUsers.value.slice(start, end);
});

const totalPages = computed(() => Math.ceil(pagination.total / pagination.pageSize));

const isAllSelected = computed(() =>
  paginatedUsers.value.length > 0 &&
  paginatedUsers.value.every(u => selectedUsers.value.includes(u.id))
);

const selectedUsersData = computed(() =>
  users.value.filter(u => selectedUsers.value.includes(u.id))
);

function resetForm() {
  userForm.id = undefined;
  userForm.username = '';
  userForm.email = '';
  userForm.phone = '';
  userForm.role_id = undefined;
  userForm.department_id = undefined;
  userForm.password = '';
  Object.keys(formErrors).forEach(key => delete formErrors[key as keyof UserFormData]);
}

function validateForm(): boolean {
  let isValid = true;
  Object.keys(formErrors).forEach(key => delete formErrors[key as keyof UserFormData]);

  if (!userForm.username || userForm.username.length < 3) {
    formErrors.username = '用户名至少3个字符';
    isValid = false;
  }
  if (!userForm.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userForm.email)) {
    formErrors.email = '请输入有效的邮箱地址';
    isValid = false;
  }
  if (userForm.phone && !/^1[3-9]\d{9}$/.test(userForm.phone)) {
    formErrors.phone = '请输入有效的手机号码';
    isValid = false;
  }
  if (!userForm.id && (!userForm.password || userForm.password.length < 8)) {
    formErrors.password = '密码至少8个字符';
    isValid = false;
  }
  if (!userForm.role_id) {
    formErrors.role_id = '请选择角色';
    isValid = false;
  }

  return isValid;
}

function openCreateDialog() {
  resetForm();
  isDialogOpen.value = true;
}

function openEditDialog(user: User) {
  resetForm();
  userForm.id = user.id;
  userForm.username = user.username;
  userForm.email = user.email;
  userForm.phone = user.phone || '';
  userForm.role_id = String(user.role_id);
  userForm.department_id = user.department_id ? String(user.department_id) : undefined;
  isDialogOpen.value = true;
}

function openDeleteDialog(user: User) {
  currentUser.value = user;
  isDeleteDialogOpen.value = true;
}

function openResetPasswordDialog(user: User) {
  currentUser.value = user;
  isResetPasswordDialogOpen.value = true;
}

function openBulkDeleteDialog() {
  isBulkDeleteDialogOpen.value = true;
}

function openBulkStatusDialog(newStatus: boolean) {
  bulkNewStatus.value = newStatus;
  isBulkStatusDialogOpen.value = true;
}

async function handleSaveUser() {
  if (!validateForm()) return;

  isLoading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));

    if (userForm.id) {
      const index = users.value.findIndex(u => u.id === userForm.id);
      if (index !== -1) {
        const role = roles.value.find(r => r.id === Number(userForm.role_id));
        const dept = departments.value.find(d => d.id === Number(userForm.department_id));
        users.value[index] = {
          ...users.value[index],
          username: userForm.username,
          email: userForm.email,
          phone: userForm.phone,
          role_id: Number(userForm.role_id),
          role: role!,
          department_id: userForm.department_id ? Number(userForm.department_id) : undefined,
          department: dept,
          updated_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
        };
      }
      toast({ title: '更新成功', description: `用户 ${userForm.username} 信息已更新`, variant: 'default' });
    } else {
      const role = roles.value.find(r => r.id === Number(userForm.role_id));
      const dept = departments.value.find(d => d.id === Number(userForm.department_id));
      const newUser: User = {
        id: Math.max(...users.value.map(u => u.id)) + 1,
        username: userForm.username,
        email: userForm.email,
        phone: userForm.phone,
        role: role!,
        role_id: Number(userForm.role_id),
        department: dept,
        department_id: userForm.department_id ? Number(userForm.department_id) : undefined,
        status: true,
        created_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
        updated_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
      };
      users.value.unshift(newUser);
      toast({ title: '创建成功', description: `用户 ${userForm.username} 已创建`, variant: 'default' });
    }

    isDialogOpen.value = false;
    resetForm();
  } catch {
    toast({ title: '操作失败', description: '请稍后重试', variant: 'destructive' });
  } finally {
    isLoading.value = false;
  }
}

async function handleDeleteUser() {
  if (!currentUser.value) return;

  isLoading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 300));
    users.value = users.value.filter(u => u.id !== currentUser.value!.id);
    selectedUsers.value = selectedUsers.value.filter(id => id !== currentUser.value!.id);
    toast({ title: '删除成功', description: `用户 ${currentUser.value!.username} 已删除`, variant: 'default' });
    isDeleteDialogOpen.value = false;
    currentUser.value = null;
  } finally {
    isLoading.value = false;
  }
}

async function handleResetPassword() {
  if (!currentUser.value) return;

  isLoading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    toast({ title: '密码重置成功', description: `已生成随机密码并发送至 ${currentUser.value!.email}`, variant: 'default' });
    isResetPasswordDialogOpen.value = false;
    currentUser.value = null;
  } finally {
    isLoading.value = false;
  }
}

async function handleToggleStatus(user: User) {
  const originalStatus = user.status;
  user.status = !user.status;

  try {
    await new Promise(resolve => setTimeout(resolve, 200));
    toast({
      title: user.status ? '已启用' : '已禁用',
      description: `用户 ${user.username} 状态已更新`,
      variant: 'default'
    });
  } catch {
    user.status = originalStatus;
    toast({ title: '操作失败', description: '状态更新失败', variant: 'destructive' });
  }
}

async function handleBulkDelete() {
  if (selectedUsers.value.length === 0) return;

  isLoading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    const usernames = selectedUsersData.value.map(u => u.username).join(', ');
    users.value = users.value.filter(u => !selectedUsers.value.includes(u.id));
    selectedUsers.value = [];
    toast({ title: '批量删除成功', description: `已删除 ${usernames}`, variant: 'default' });
    isBulkDeleteDialogOpen.value = false;
  } finally {
    isLoading.value = false;
  }
}

async function handleBulkStatusToggle() {
  if (selectedUsers.value.length === 0) return;

  isLoading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 300));
    selectedUsers.value.forEach(id => {
      const user = users.value.find(u => u.id === id);
      if (user) user.status = bulkNewStatus.value;
    });
    const action = bulkNewStatus.value ? '启用' : '禁用';
    toast({ title: `批量${action}成功`, description: `已更新 ${selectedUsers.value.length} 个用户的状态`, variant: 'default' });
    isBulkStatusDialogOpen.value = false;
  } finally {
    isLoading.value = false;
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedUsers.value = selectedUsers.value.filter(id => !paginatedUsers.value.some(u => u.id === id));
  } else {
    const newSelected = [...new Set([...selectedUsers.value, ...paginatedUsers.value.map(u => u.id)])];
    selectedUsers.value = newSelected;
  }
}

function toggleSelectUser(id: number) {
  const index = selectedUsers.value.indexOf(id);
  if (index === -1) {
    selectedUsers.value.push(id);
  } else {
    selectedUsers.value.splice(index, 1);
  }
}

function handleSearch() {
  pagination.page = 1;
}

function handlePageChange(newPage: number) {
  pagination.page = newPage;
}

function handlePageSizeChange(newSize: number) {
  pagination.pageSize = newSize;
  pagination.page = 1;
}

function goToFirstPage() {
  pagination.page = 1;
}

function goToLastPage() {
  pagination.page = totalPages.value;
}

function handleExport() {
  const dataToExport = filteredUsers.value;
  const csvContent = [
    ['用户名', '邮箱', '手机', '角色', '部门', '状态', '最后登录', '创建时间'].join(','),
    ...dataToExport.map(u => [
      u.username,
      u.email,
      u.phone || '',
      u.role.name,
      u.department?.name || '',
      u.status ? '启用' : '禁用',
      u.last_login_at || '从未登录',
      u.created_at,
    ].join(','))
  ].join('\n');

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
  link.click();
  URL.revokeObjectURL(url);

  toast({ title: '导出成功', description: `已导出 ${dataToExport.length} 条用户数据`, variant: 'default' });
}

function handleImport() {
  toast({ title: '导入功能', description: '请使用标准CSV格式，支持字段: 用户名,邮箱,手机,角色,部门', variant: 'default' });
}

function refreshData() {
  isLoading.value = true;
  setTimeout(() => {
    isLoading.value = false;
    toast({ title: '刷新成功', description: '用户数据已更新', variant: 'default' });
  }, 500);
}

onMounted(() => {
  pagination.total = users.value.length;
});
</script>

<template>
  <div class="space-y-6">
    <Card class="dark:bg-slate-950 dark:border-slate-800">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="dark:text-slate-50 text-lg font-bold">用户管理</CardTitle>
            <CardDescription class="dark:text-slate-400">管理系统用户账号、角色与访问权限</CardDescription>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" @click="refreshData" :disabled="isLoading">
              <RefreshCw class="w-4 h-4 mr-1" :class="{ 'animate-spin': isLoading }" />
              刷新
            </Button>
            <Button variant="outline" size="sm" @click="handleImport">
              <Upload class="w-4 h-4 mr-1" />
              导入
            </Button>
            <Button variant="outline" size="sm" @click="handleExport">
              <Download class="w-4 h-4 mr-1" />
              导出
            </Button>
            <Button size="sm" @click="openCreateDialog">
              <Plus class="w-4 h-4 mr-1" />
              新建用户
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent class="space-y-4">
        <div class="flex flex-col sm:flex-row gap-3">
          <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              placeholder="搜索用户名、邮箱或手机..."
              class="pl-9"
              @keyup.enter="handleSearch"
            />
          </div>
          <Select v-model="statusFilter" @update:modelValue="handleSearch">
            <SelectTrigger class="w-[140px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>状态筛选</SelectLabel>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="active">已启用</SelectItem>
                <SelectItem value="inactive">已禁用</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
          <Select v-model="roleFilter" @update:modelValue="handleSearch">
            <SelectTrigger class="w-[160px]">
              <SelectValue placeholder="角色" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>角色筛选</SelectLabel>
                <SelectItem value="all">全部角色</SelectItem>
                <SelectItem v-for="role in roles" :key="role.id" :value="String(role.id)">
                  {{ role.name }}
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <div v-if="selectedUsers.length > 0" class="flex items-center gap-3 p-3 bg-muted/50 dark:bg-slate-900 rounded-lg">
          <span class="text-sm text-muted-foreground">已选择 {{ selectedUsers.length }} 项</span>
          <Button variant="outline" size="sm" @click="openBulkStatusDialog(true)">
            <CheckCircle2 class="w-4 h-4 mr-1" />
            批量启用
          </Button>
          <Button variant="outline" size="sm" @click="openBulkStatusDialog(false)">
            <XCircle class="w-4 h-4 mr-1" />
            批量禁用
          </Button>
          <Button variant="destructive" size="sm" @click="openBulkDeleteDialog">
            <Trash2 class="w-4 h-4 mr-1" />
            批量删除
          </Button>
          <Button variant="ghost" size="sm" @click="selectedUsers = []">
            清除选择
          </Button>
        </div>

        <div class="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow class="dark:bg-slate-900 dark:border-slate-800">
                <TableHead class="w-[40px]">
                  <input
                    type="checkbox"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                    class="rounded border-input"
                  />
                </TableHead>
                <TableHead class="dark:text-slate-200">用户名</TableHead>
                <TableHead class="dark:text-slate-200">邮箱</TableHead>
                <TableHead class="dark:text-slate-200">手机</TableHead>
                <TableHead class="dark:text-slate-200">角色</TableHead>
                <TableHead class="dark:text-slate-200">部门</TableHead>
                <TableHead class="dark:text-slate-200">状态</TableHead>
                <TableHead class="dark:text-slate-200">最后登录</TableHead>
                <TableHead class="dark:text-slate-200 w-[120px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="user in paginatedUsers"
                :key="user.id"
                :class="cn('dark:hover:bg-slate-900/50 dark:border-slate-800', selectedUsers.includes(user.id) && 'bg-muted/30')"
              >
                <TableCell>
                  <input
                    type="checkbox"
                    :checked="selectedUsers.includes(user.id)"
                    @change="toggleSelectUser(user.id)"
                    class="rounded border-input"
                  />
                </TableCell>
                <TableCell class="font-medium dark:text-slate-200">
                  <div class="flex items-center gap-2">
                    {{ user.username }}
                    <Badge v-if="user.role.code === 'super_admin'" variant="destructive" class="text-xs">SUPER</Badge>
                    <Badge v-else-if="user.role.code === 'admin'" variant="default" class="text-xs">ADMIN</Badge>
                  </div>
                </TableCell>
                <TableCell class="dark:text-slate-300">{{ user.email }}</TableCell>
                <TableCell class="dark:text-slate-300">{{ user.phone || '-' }}</TableCell>
                <TableCell>
                  <Badge :variant="user.role.code === 'super_admin' ? 'destructive' : 'secondary'" class="text-xs">
                    {{ user.role.name }}
                  </Badge>
                </TableCell>
                <TableCell class="dark:text-slate-300">{{ user.department?.name || '-' }}</TableCell>
                <TableCell>
                  <Switch :checked="user.status" @update:checked="handleToggleStatus(user)" />
                </TableCell>
                <TableCell class="dark:text-slate-300 text-xs">
                  {{ user.last_login_at || '从未登录' }}
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-1">
                    <Button variant="ghost" size="icon" class="h-8 w-8" @click="openEditDialog(user)" title="编辑">
                      <Pencil class="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" class="h-8 w-8" @click="openResetPasswordDialog(user)" title="重置密码">
                      <KeyRound class="w-4 h-4" />
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger as-child>
                        <Button variant="ghost" size="icon" class="h-8 w-8 text-red-500 hover:text-red-400" title="删除">
                          <Trash2 class="w-4 h-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>确认删除</AlertDialogTitle>
                          <AlertDialogDescription>
                            确定要删除用户 <strong>{{ user.username }}</strong> 吗？此操作不可恢复。
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>取消</AlertDialogCancel>
                          <AlertDialogAction @click="handleDeleteUser" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            删除
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow v-if="paginatedUsers.length === 0">
                <TableCell colspan="9" class="text-center py-8 text-muted-foreground">
                  暂无数据
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div class="flex items-center justify-between">
          <div class="text-sm text-muted-foreground">
            共 {{ pagination.total }} 条记录，第 {{ pagination.page }} / {{ totalPages }} 页
          </div>
          <div class="flex items-center gap-2">
            <Select :modelValue="String(pagination.pageSize)" @update:modelValue="(v) => handlePageSizeChange(Number(v))">
              <SelectTrigger class="w-[100px]">
                <SelectValue>{{ pagination.pageSize }} 条/页</SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5 条/页</SelectItem>
                <SelectItem value="10">10 条/页</SelectItem>
                <SelectItem value="20">20 条/页</SelectItem>
                <SelectItem value="50">50 条/页</SelectItem>
              </SelectContent>
            </Select>
            <div class="flex items-center gap-1">
              <Button variant="outline" size="icon" class="h-8 w-8" @click="goToFirstPage" :disabled="pagination.page <= 1">
                <ChevronsLeft class="w-4 h-4" />
              </Button>
              <Button variant="outline" size="icon" class="h-8 w-8" @click="handlePageChange(pagination.page - 1)" :disabled="pagination.page <= 1">
                <ChevronLeft class="w-4 h-4" />
              </Button>
              <span class="px-2 text-sm">第 {{ pagination.page }} 页</span>
              <Button variant="outline" size="icon" class="h-8 w-8" @click="handlePageChange(pagination.page + 1)" :disabled="pagination.page >= totalPages">
                <ChevronRight class="w-4 h-4" />
              </Button>
              <Button variant="outline" size="icon" class="h-8 w-8" @click="goToLastPage" :disabled="pagination.page >= totalPages">
                <ChevronsRight class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <Sheet v-model:open="isDialogOpen">
        <SheetContent side="right" class="w-[480px] sm:max-w-[480px] flex flex-col">
          <SheetHeader>
            <div class="flex items-center gap-2">
              <Users class="w-5 h-5 text-primary" />
              <SheetTitle>{{ userForm.id ? '编辑用户' : '新建用户' }}</SheetTitle>
            </div>
            <SheetDescription>
              {{ userForm.id ? '修改用户信息' : '创建一个新的用户账号' }}
            </SheetDescription>
          </SheetHeader>

          <ScrollArea class="flex-1 mt-4">
            <div class="space-y-4 pr-4">
              <div class="grid gap-2">
                <Label for="username">用户名 <span class="text-destructive">*</span></Label>
                <Input
                  id="username"
                  v-model="userForm.username"
                  placeholder="请输入用户名"
                  :class="{ 'border-destructive': formErrors.username }"
                />
                <p v-if="formErrors.username" class="text-xs text-destructive">{{ formErrors.username }}</p>
              </div>
              <div class="grid gap-2">
                <Label for="email">邮箱 <span class="text-destructive">*</span></Label>
                <Input
                  id="email"
                  type="email"
                  v-model="userForm.email"
                  placeholder="请输入邮箱"
                  :class="{ 'border-destructive': formErrors.email }"
                />
                <p v-if="formErrors.email" class="text-xs text-destructive">{{ formErrors.email }}</p>
              </div>
              <div class="grid gap-2">
                <Label for="phone">手机号码</Label>
                <Input
                  id="phone"
                  v-model="userForm.phone"
                  placeholder="请输入手机号码"
                  :class="{ 'border-destructive': formErrors.phone }"
                />
                <p v-if="formErrors.phone" class="text-xs text-destructive">{{ formErrors.phone }}</p>
              </div>
              <div class="grid gap-2">
                <Label for="role">角色 <span class="text-destructive">*</span></Label>
                <Select v-model="userForm.role_id">
                  <SelectTrigger>
                    <SelectValue placeholder="请选择角色" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>系统角色</SelectLabel>
                      <SelectItem v-for="role in roles" :key="role.id" :value="String(role.id)">
                        {{ role.name }} - {{ role.description }}
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
                <p v-if="formErrors.role_id" class="text-xs text-destructive">{{ formErrors.role_id }}</p>
              </div>
              <div class="grid gap-2">
                <Label for="department">部门</Label>
                <Select v-model="userForm.department_id">
                  <SelectTrigger id="department">
                    <SelectValue placeholder="请选择部门" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>组织部门</SelectLabel>
                      <SelectItem v-for="dept in departments" :key="dept.id" :value="String(dept.id)">
                        {{ dept.name }}
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>
              <div class="grid gap-2" v-if="!userForm.id">
                <Label for="password">密码 <span class="text-destructive">*</span></Label>
                <Input
                  id="password"
                  type="password"
                  v-model="userForm.password"
                  placeholder="请输入密码（至少8位）"
                  :class="{ 'border-destructive': formErrors.password }"
                />
                <p v-if="formErrors.password" class="text-xs text-destructive">{{ formErrors.password }}</p>
              </div>
            </div>
          </ScrollArea>

          <SheetFooter class="gap-2 sm:gap-4 mt-4 pt-4 border-t">
            <Button variant="outline" @click="isDialogOpen = false">取消</Button>
            <Button @click="handleSaveUser" :disabled="isLoading">
              {{ isLoading ? '保存中...' : (userForm.id ? '保存修改' : '创建用户') }}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

    <AlertDialog v-model:open="isDeleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除用户</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除用户 <strong>{{ currentUser?.username }}</strong> 吗？此操作将同时移除该用户的所有权限。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction @click="handleDeleteUser" class="bg-destructive text-destructive-foreground hover:bg-destructive/90" :disabled="isLoading">
            确认删除
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog v-model:open="isResetPasswordDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>重置用户密码</AlertDialogTitle>
          <AlertDialogDescription>
            即将为用户 <strong>{{ currentUser?.username }}</strong> 重置密码。系统将生成随机密码并发送至其邮箱 <strong>{{ currentUser?.email }}</strong>。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction @click="handleResetPassword" :disabled="isLoading">
            确认重置
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog v-model:open="isBulkDeleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>批量删除用户</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除选中的 <strong>{{ selectedUsers.length }} 个用户</strong> 吗？此操作不可恢复。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction @click="handleBulkDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90" :disabled="isLoading">
            确认删除
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog v-model:open="isBulkStatusDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>批量更新用户状态</AlertDialogTitle>
          <AlertDialogDescription>
            确定要{{ bulkNewStatus ? '启用' : '禁用' }}选中的 <strong>{{ selectedUsers.length }} 个用户</strong> 吗？
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction @click="handleBulkStatusToggle" :disabled="isLoading">
            确认{{ bulkNewStatus ? '启用' : '禁用' }}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>
