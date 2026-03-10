<script setup lang="ts">
import { ref, watch } from 'vue';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { dataSourceApi } from '@/features/data_etl/api';
import { Loader2, RefreshCw } from 'lucide-vue-next';

const props = defineProps<{
  isOpen: boolean;
  dataSourceId: number | null;
  tableName?: string;
  query?: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const data = ref<any[]>([]);
const columns = ref<string[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

const fetchData = async () => {
  if (!props.dataSourceId) return;
  if (!props.tableName && !props.query) return;
  
  isLoading.value = true;
  error.value = null;
  data.value = [];
  columns.value = [];
  
  try {
    let result;
    if (props.query) {
      result = await dataSourceApi.previewQuery(props.dataSourceId, props.query, 10);
    } else if (props.tableName) {
      result = await dataSourceApi.previewTable(props.dataSourceId, props.tableName, 10);
    }
    
    if (result && result.length > 0) {
      columns.value = Object.keys(result[0]);
      data.value = result;
    } else {
      data.value = [];
    }
    
  } catch (e: any) {
    console.error('Preview failed', e);
    error.value = e.message || 'Failed to load data preview';
  } finally {
    isLoading.value = false;
  }
};

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchData();
  }
});

const onOpenChange = (open: boolean) => {
  if (!open) {
    emit('close');
  }
};
</script>

<template>
  <Dialog :open="isOpen" @update:open="onOpenChange">
    <DialogContent class="max-w-[900px] max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle class="flex items-center justify-between">
          <span>数据预览: {{ tableName }}</span>
          <Button variant="ghost" size="icon" @click="fetchData" :disabled="isLoading">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoading }" />
          </Button>
        </DialogTitle>
        <DialogDescription>
          预览前 10 条数据
        </DialogDescription>
      </DialogHeader>
      
      <div class="flex-1 overflow-auto border rounded-md min-h-[300px] relative">
        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
          <Loader2 class="w-8 h-8 animate-spin text-primary" />
        </div>
        
        <div v-if="error" class="absolute inset-0 flex items-center justify-center text-destructive p-4 text-center">
          {{ error }}
        </div>
        
        <div v-if="!isLoading && !error && data.length === 0" class="absolute inset-0 flex items-center justify-center text-muted-foreground">
          暂无数据
        </div>

        <Table v-if="data.length > 0">
          <TableHeader>
            <TableRow>
              <TableHead v-for="col in columns" :key="col" class="whitespace-nowrap">
                {{ col }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="(row, i) in data" :key="i">
              <TableCell v-for="col in columns" :key="col" class="max-w-[200px] truncate">
                {{ row[col] }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </DialogContent>
  </Dialog>
</template>