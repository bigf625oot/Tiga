<template>
  <Dialog :open="isArtifactOpen" @update:open="handleOpenChange">
    <DialogContent class="max-w-[90vw] w-[1200px] h-[85vh] p-0 overflow-hidden flex flex-col gap-0 border-border/50 shadow-2xl">
      <DialogHeader class="px-4 py-3 border-b border-border bg-muted/30 flex-none">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
              <FileCode2 class="w-4 h-4 text-primary" />
            </div>
            <div>
              <DialogTitle class="text-sm font-semibold leading-none">{{ activeArtifact?.title || '生成产物' }}</DialogTitle>
              <DialogDescription class="text-xs text-muted-foreground mt-1">
                {{ activeArtifact?.language || '代码' }} 预览与编辑
              </DialogDescription>
            </div>
          </div>
          <!-- DialogClose is handled natively by the X button provided by DialogContent, 
               but we can add custom actions here -->
        </div>
      </DialogHeader>

      <div class="flex-1 overflow-hidden flex flex-col min-h-0 relative bg-background">
        <ArtifactEditor 
          class="flex-1 min-h-0"
          v-if="activeArtifact"
          :value="activeArtifact.content"
          :language="activeArtifact.language || activeArtifact.type"
          :fileType="activeArtifact.type"
          @update:value="handleContentUpdate"
          @run="handleRunCode"
        />

        <!-- Run Output Panel -->
        <div v-if="runOutput !== null" class="h-48 flex-none border-t border-border bg-zinc-950 text-green-400 p-4 font-mono text-sm overflow-y-auto relative z-10 shadow-[0_-4px_10px_rgba(0,0,0,0.1)]">
          <div class="absolute right-2 top-2 flex items-center gap-2">
            <button @click="runOutput = null" class="text-zinc-500 hover:text-white transition-colors" title="关闭输出">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>
          <div class="font-bold text-zinc-500 mb-2 select-none border-b border-zinc-800 pb-1 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>
            终端输出
          </div>
          <div v-if="isRunning" class="text-yellow-400 flex items-center gap-2 mt-2">
            <div class="w-3.5 h-3.5 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
            正在执行代码...
          </div>
          <pre v-else class="whitespace-pre-wrap break-all leading-relaxed">{{ runOutput || '执行成功，无输出' }}</pre>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useArtifact } from '@/features/chat/context/ArtifactContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { FileCode2 } from 'lucide-vue-next';
import ArtifactEditor from './ArtifactEditor.vue';
import { SandboxService } from '@/features/sandbox/api/sandbox';
import { useToast } from '@/components/ui/toast/use-toast';

const { isArtifactOpen, activeArtifact, closeArtifact } = useArtifact();
const { toast } = useToast();

const runOutput = ref<string | null>(null);
const isRunning = ref(false);

const handleOpenChange = (open: boolean) => {
  if (!open) {
    closeArtifact();
    runOutput.value = null;
  }
};

const handleContentUpdate = (newContent: string) => {
  if (activeArtifact.value) {
    activeArtifact.value.content = newContent;
  }
};

const handleRunCode = async (code: string) => {
  if (!activeArtifact.value) return;
  const lang = (activeArtifact.value.language || activeArtifact.value.type).toLowerCase();
  
  if (['vue', 'html', 'markdown'].includes(lang)) {
    toast({ title: '提示', description: `${lang.toUpperCase()} 代码已在左侧实时预览，无需手动运行` });
    return;
  }

  runOutput.value = '';
  isRunning.value = true;
  
  if (['javascript', 'js', 'typescript', 'ts'].includes(lang)) {
    // 前端直接沙箱执行 JS
    try {
      let logs: string[] = [];
      const originalConsoleLog = console.log;
      const proxyConsole = {
        log: (...args: any[]) => {
          logs.push(args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' '));
          originalConsoleLog(...args);
        },
        error: (...args: any[]) => {
          logs.push('[Error] ' + args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' '));
          console.error(...args);
        },
        warn: (...args: any[]) => {
          logs.push('[Warn] ' + args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' '));
          console.warn(...args);
        }
      };

      const fun = new Function('console', `
        try {
          ${code}
        } catch(e) {
          console.error(e.message);
        }
      `);
      
      fun(proxyConsole);
      runOutput.value = logs.join('\n') || '执行成功，无输出';
    } catch (e: any) {
      runOutput.value = `执行失败: ${e.message}`;
    } finally {
      isRunning.value = false;
    }
  } else {
    // 后端沙箱执行 (Python, Shell etc)
    try {
      const res = await SandboxService.runCode({
        language: lang,
        code: code
      });
      if (res.status === 'success' && res.result) {
        runOutput.value = res.result.content || '执行成功，无输出';
      } else {
        runOutput.value = `执行失败:\n${res.result?.content || res.status}`;
      }
    } catch (e: any) {
      runOutput.value = `执行错误:\n${e.message || '网络连接失败'}`;
    } finally {
      isRunning.value = false;
    }
  }
};
</script>
