<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Clock, HelpCircle, CalendarClock } from 'lucide-vue-next';
import { ScheduleConfig } from '../types/pipeline';
import dayjs from 'dayjs';

const props = defineProps<{
  open: boolean;
  config?: ScheduleConfig;
}>();

const emit = defineEmits(['update:open', 'save']);

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
});

const enabled = ref(false);
const type = ref<'cron' | 'interval' | 'visual'>('visual');
const cronValue = ref('0 0 * * *');
const intervalValue = ref(1);
const intervalUnit = ref('h');

// Visual Builder State
const visualFrequency = ref<'daily' | 'weekly' | 'monthly' | 'hourly'>('daily');
const visualTime = ref('09:00');
const visualWeekDay = ref('1'); // 0-6 (Sun-Sat) or 1-7 (Mon-Sun) - standard cron is 0-6 (Sun-Sat) or 1-7 (Mon-Sun)? Cron 0=Sun. Let's use 1=Mon...7=Sun for UI
const visualMonthDay = ref(1);
const visualMinute = ref(0);

// Initialize from props
watch(() => props.open, (val) => {
  if (val && props.config) {
    enabled.value = props.config.enabled;
    type.value = (props.config.type as any) === 'visual' ? 'visual' : props.config.type; // Backwards compat
    
    // If incoming type is cron, try to reverse engineer visual state? 
    // For now, if it's cron, default to cron mode.
    if (props.config.type === 'cron') {
        cronValue.value = props.config.value;
        // Simple heuristic to switch to visual if it matches common patterns could be added here
        type.value = 'cron';
    } else if (props.config.type === 'interval') {
      type.value = 'interval';
      const match = props.config.value.match(/(\d+)([mhd])/);
      if (match) {
        intervalValue.value = parseInt(match[1]);
        intervalUnit.value = match[2];
      }
    }
  } else if (val && !props.config) {
    // Defaults
    enabled.value = false;
    type.value = 'visual'; // Default to visual for new configs
    cronValue.value = '0 0 * * *';
  }
});

// Generate cron from visual state
const generatedCron = computed(() => {
  const [hour, minute] = visualTime.value.split(':').map(Number);
  
  if (visualFrequency.value === 'hourly') {
    return `${visualMinute.value} * * * *`;
  }
  if (visualFrequency.value === 'daily') {
    return `${minute} ${hour} * * *`;
  }
  if (visualFrequency.value === 'weekly') {
    // Cron day of week: 0-6 (Sun-Sat) or 1-7 (Mon-Sun). 
    // Let's assume standard linux cron: 0 - 6 (Sunday=0 or 7).
    // Our UI: 1=Mon ... 7=Sun.
    // Map UI (1-7) to Cron (1-7 or 1-0). 
    // Standard Cron: 1=Mon, 0=Sun.
    let cronDay = parseInt(visualWeekDay.value);
    if (cronDay === 7) cronDay = 0; 
    return `${minute} ${hour} * * ${cronDay}`;
  }
  if (visualFrequency.value === 'monthly') {
    return `${minute} ${hour} ${visualMonthDay.value} * *`;
  }
  return '* * * * *';
});

const nextRunPreview = computed(() => {
  if (!enabled.value) return '未启用';
  
  if (type.value === 'cron') {
    return '根据 Cron 表达式计算...'; 
  } else if (type.value === 'visual') {
     return `预览: ${generatedCron.value}`;
  } else {
    const now = dayjs();
    let next = now;
    if (intervalUnit.value === 'm') next = now.add(intervalValue.value, 'minute');
    if (intervalUnit.value === 'h') next = now.add(intervalValue.value, 'hour');
    if (intervalUnit.value === 'd') next = now.add(intervalValue.value, 'day');
    return next.format('YYYY-MM-DD HH:mm:ss');
  }
});

const save = () => {
  let value = cronValue.value;
  let saveType = type.value;
  let description = '';

  if (type.value === 'interval') {
    value = `${intervalValue.value}${intervalUnit.value}`;
    description = `每 ${intervalValue.value} ${intervalUnit.value === 'm' ? '分钟' : intervalUnit.value === 'h' ? '小时' : '天'}`;
  } else if (type.value === 'visual') {
    value = generatedCron.value;
    saveType = 'cron'; // Save as cron to backend
    
    // Generate description
    const time = visualTime.value;
    if (visualFrequency.value === 'daily') description = `每天 ${time}`;
    if (visualFrequency.value === 'weekly') {
        const days = ['日', '一', '二', '三', '四', '五', '六', '日'];
        let dayIdx = parseInt(visualWeekDay.value); 
        if(dayIdx === 7) dayIdx = 0; // for array lookup if 0=Sun
        // Actually UI: 1=Mon..7=Sun. 
        // Let's map directly:
        const map = { '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '日' };
        description = `每周${map[visualWeekDay.value as keyof typeof map]} ${time}`;
    }
    if (visualFrequency.value === 'monthly') description = `每月 ${visualMonthDay.value}号 ${time}`;
    if (visualFrequency.value === 'hourly') description = `每小时第 ${visualMinute.value} 分`;
  } else {
    description = 'Cron 自定义调度';
  }

  const config: ScheduleConfig = {
    enabled: enabled.value,
    type: saveType as any,
    value,
    description,
    next_run_at: nextRunPreview.value
  };

  emit('save', config);
  isOpen.value = false;
};

const openCronHelp = () => {
  window.open('https://crontab.guru/', '_blank');
};
</script>

<template>
  <Dialog :open="isOpen" @update:open="isOpen = $event">
    <DialogContent class="sm:max-w-[450px]">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <CalendarClock class="h-5 w-5 text-primary" />
          定时调度配置
        </DialogTitle>
        <DialogDescription>
          配置流水线的自动运行计划。支持 Cron 表达式或固定间隔设置。
        </DialogDescription>
      </DialogHeader>

      <div class="grid gap-6 py-4">
        <!-- Enable Switch -->
        <div class="flex items-center justify-between space-x-2 border p-3 rounded-lg bg-muted/20">
          <Label for="schedule-enabled" class="flex flex-col space-y-1 cursor-pointer">
            <span class="font-medium">启用自动调度</span>
            <span class="font-normal text-xs text-muted-foreground">开启后流水线将按计划自动触发执行</span>
          </Label>
          <Switch id="schedule-enabled" :checked="enabled" @update:checked="enabled = $event" />
        </div>

        <div v-if="enabled" class="space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <!-- Type Select -->
          <div class="grid gap-2">
            <Label>调度模式</Label>
            <Select v-model="type">
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="visual">简易配置 (推荐)</SelectItem>
                <SelectItem value="interval">固定间隔</SelectItem>
                <SelectItem value="cron">Cron 表达式 (高级)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Visual Builder -->
          <div v-if="type === 'visual'" class="space-y-4">
            <div class="grid gap-2">
              <Label>执行频率</Label>
              <Select v-model="visualFrequency">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">每小时</SelectItem>
                  <SelectItem value="daily">每天</SelectItem>
                  <SelectItem value="weekly">每周</SelectItem>
                  <SelectItem value="monthly">每月</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Time Selection -->
            <div class="grid grid-cols-2 gap-4">
               <div v-if="visualFrequency === 'hourly'" class="grid gap-2">
                 <Label>分钟 (0-59)</Label>
                 <Input type="number" v-model="visualMinute" min="0" max="59" />
               </div>

               <div v-if="['daily', 'weekly', 'monthly'].includes(visualFrequency)" class="grid gap-2">
                 <Label>时间</Label>
                 <Input type="time" v-model="visualTime" />
               </div>

               <div v-if="visualFrequency === 'weekly'" class="grid gap-2">
                 <Label>星期</Label>
                 <Select v-model="visualWeekDay">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">周一</SelectItem>
                    <SelectItem value="2">周二</SelectItem>
                    <SelectItem value="3">周三</SelectItem>
                    <SelectItem value="4">周四</SelectItem>
                    <SelectItem value="5">周五</SelectItem>
                    <SelectItem value="6">周六</SelectItem>
                    <SelectItem value="7">周日</SelectItem>
                  </SelectContent>
                </Select>
               </div>

               <div v-if="visualFrequency === 'monthly'" class="grid gap-2">
                 <Label>日期 (1-31)</Label>
                 <Input type="number" v-model="visualMonthDay" min="1" max="31" />
               </div>
            </div>
            
            <div class="text-xs text-muted-foreground bg-muted/30 p-2 rounded">
              生成的 Cron 表达式: <span class="font-mono text-primary">{{ generatedCron }}</span>
            </div>
          </div>

          <!-- Cron Input -->
          <div v-if="type === 'cron'" class="grid gap-2">
            <Label class="flex items-center justify-between">
              Cron 表达式
              <span class="text-xs text-muted-foreground font-normal">分 时 日 月 周</span>
            </Label>
            <div class="flex gap-2">
              <Input v-model="cronValue" placeholder="* * * * *" class="font-mono bg-muted/50" />
              <Button variant="outline" size="icon" title="Cron 表达式生成器" @click="openCronHelp">
                <HelpCircle class="h-4 w-4" />
              </Button>
            </div>
            <div class="flex gap-2 mt-1">
              <span class="text-[10px] px-1.5 py-0.5 bg-muted rounded text-muted-foreground">0 9 * * * (每天9点)</span>
              <span class="text-[10px] px-1.5 py-0.5 bg-muted rounded text-muted-foreground">*/30 * * * * (每30分)</span>
            </div>
          </div>

          <!-- Interval Input -->
          <div v-if="type === 'interval'" class="grid gap-2">
            <Label>执行间隔</Label>
            <div class="flex gap-2 items-center">
              <span class="text-sm text-muted-foreground">每</span>
              <Input type="number" v-model="intervalValue" min="1" class="w-24" />
              <Select v-model="intervalUnit">
                <SelectTrigger class="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="m">分钟</SelectItem>
                  <SelectItem value="h">小时</SelectItem>
                  <SelectItem value="d">天</SelectItem>
                </SelectContent>
              </Select>
              <span class="text-sm text-muted-foreground">执行一次</span>
            </div>
          </div>

          <!-- Preview -->
          <div class="rounded-md bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900 p-3 text-sm flex items-start gap-3">
            <Clock class="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 shrink-0" />
            <div class="flex flex-col gap-0.5">
              <span class="font-medium text-blue-900 dark:text-blue-200">预计下次运行时间</span>
              <span class="text-blue-700 dark:text-blue-300 font-mono text-xs">{{ nextRunPreview }}</span>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="isOpen = false">取消</Button>
        <Button @click="save">保存配置</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
