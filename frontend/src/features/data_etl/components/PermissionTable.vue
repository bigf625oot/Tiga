<script setup lang="ts">
import { Checkbox } from '@/components/ui/checkbox';
import type { ResourceDef, ActionDef } from '../composables/useRBAC';

const props = defineProps<{
  resources: { resource: ResourceDef; actions: ActionDef[] }[];
  isLockedRole: boolean;
  hasPermission: (resourceId: string, actionId: string) => boolean;
  isRowFullySelected: (resourceId: string, actionIds: string[]) => boolean;
}>();

const emit = defineEmits<{
  (e: 'togglePermission', resourceId: string, actionId: string, checked: boolean): void;
  (e: 'toggleRow', resourceId: string, actionIds: string[], checked: boolean): void;
}>();
</script>

<template>
  <div v-if="resources.length === 0" class="py-16 flex flex-col items-center justify-center text-muted-foreground border rounded-lg border-dashed dark:border-slate-800">
    <div class="text-lg font-medium mb-1">未找到匹配的权限项</div>
    <div class="text-sm">请尝试调整搜索词或清除过滤条件</div>
  </div>

  <div v-else class="border rounded-lg overflow-hidden dark:border-slate-800">
    <table class="w-full text-sm">
      <thead class="bg-muted/50 dark:bg-slate-900 border-b dark:border-slate-800">
        <tr>
          <th class="px-6 py-3.5 text-left font-semibold w-1/4 text-slate-700 dark:text-slate-200">资源</th>
          <th class="px-6 py-3.5 text-left font-semibold w-1/2 text-slate-700 dark:text-slate-200">操作权限</th>
          <th class="px-6 py-3.5 text-right font-semibold w-1/4 text-slate-700 dark:text-slate-200">行全选</th>
        </tr>
      </thead>
      <tbody class="divide-y dark:divide-slate-800/60 bg-card">
        <tr
          v-for="{ resource, actions } in resources"
          :key="resource.id"
          class="hover:bg-muted/30 dark:hover:bg-slate-900/50 transition-colors group"
        >
          <td class="px-6 py-4 align-top">
            <div class="space-y-1">
              <div class="font-medium text-slate-900 dark:text-slate-100">{{ resource.name }}</div>
              <div class="text-xs text-muted-foreground font-mono bg-muted/50 inline-block px-1.5 py-0.5 rounded">{{ resource.id }}</div>
            </div>
          </td>
          <td class="px-6 py-4">
            <div class="flex flex-wrap gap-x-8 gap-y-3">
              <label
                v-for="action in actions"
                :key="action.id"
                class="flex items-center gap-2 cursor-pointer group/label"
                :class="{ 'opacity-50 cursor-not-allowed': isLockedRole }"
              >
                <Checkbox
                  :checked="hasPermission(resource.id, action.id)"
                  @update:checked="(val) => emit('togglePermission', resource.id, action.id, val)"
                  :disabled="isLockedRole"
                  class="data-[state=checked]:bg-primary"
                />
                <span class="text-sm select-none text-slate-700 dark:text-slate-300 group-hover/label:text-primary transition-colors">
                  {{ action.name }}
                </span>
              </label>
            </div>
          </td>
          <td class="px-6 py-4 text-right align-top">
            <div class="inline-flex items-center justify-end">
              <Checkbox
                :checked="isRowFullySelected(resource.id, actions.map((a) => a.id))"
                @update:checked="(val) => emit('toggleRow', resource.id, actions.map((a) => a.id), val)"
                :disabled="isLockedRole"
                class="data-[state=checked]:bg-primary"
              />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
