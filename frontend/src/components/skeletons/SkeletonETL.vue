<script setup lang="ts">
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'

interface Props {
  rows?: number
  height?: string
  animated?: boolean
}

withDefaults(defineProps<Props>(), {
  rows: 5,
  height: 'h-16',
  animated: true
})
</script>

<template>
  <div class="rounded-md border">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead class="w-[50px]"><Skeleton class="h-4 w-4" /></TableHead>
          <TableHead><Skeleton class="h-4 w-[150px]" /></TableHead>
          <TableHead><Skeleton class="h-4 w-[100px]" /></TableHead>
          <TableHead><Skeleton class="h-4 w-[120px]" /></TableHead>
          <TableHead><Skeleton class="h-4 w-[80px]" /></TableHead>
          <TableHead class="text-right"><Skeleton class="h-4 w-[100px] ml-auto" /></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="i in rows" :key="i">
          <TableCell><Skeleton class="h-4 w-4" /></TableCell>
          <TableCell>
            <div class="flex items-center gap-4">
              <Skeleton class="h-10 w-10 rounded-lg" />
              <div class="space-y-2">
                <Skeleton class="h-4 w-[200px]" />
                <Skeleton class="h-3 w-[120px]" />
              </div>
            </div>
          </TableCell>
          <TableCell><Skeleton class="h-5 w-[80px] rounded-full" /></TableCell>
          <TableCell>
            <div class="space-y-2">
              <Skeleton class="h-3 w-[80px]" />
              <Skeleton class="h-3 w-[60px]" />
            </div>
          </TableCell>
          <TableCell><Skeleton class="h-4 w-[60px]" /></TableCell>
          <TableCell class="text-right">
            <div class="flex justify-end gap-2">
              <Skeleton class="h-8 w-8 rounded-md" />
              <Skeleton class="h-8 w-8 rounded-md" />
              <Skeleton class="h-8 w-8 rounded-md" />
            </div>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
