<template>
  <div class="xterm-container h-full w-full bg-slate-900 rounded-md overflow-hidden relative" ref="terminalRef">
    <div class="absolute top-2 right-2 z-10 flex gap-2">
      <a-tooltip title="Clear Terminal">
        <button @click="clear" class="text-slate-400 hover:text-white transition-colors">
          <ClearOutlined />
        </button>
      </a-tooltip>
      <a-tooltip title="Copy All">
        <button @click="copyAll" class="text-slate-400 hover:text-white transition-colors">
          <CopyOutlined />
        </button>
      </a-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { AttachAddon } from 'xterm-addon-attach';
import 'xterm/css/xterm.css';
import { ClearOutlined, CopyOutlined } from '@ant-design/icons-vue';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  theme?: 'dark' | 'light';
  fontSize?: number;
  initialContent?: string;
  readOnly?: boolean;
  url?: string; // WebSocket URL
}>();

const emit = defineEmits(['data', 'resize']);

const terminalRef = ref<HTMLElement | null>(null);
let term: Terminal | null = null;
let fitAddon: FitAddon | null = null;
let socket: WebSocket | null = null;
let attachAddon: AttachAddon | null = null;

const initTerminal = () => {
  if (!terminalRef.value) return;

  term = new Terminal({
    cursorBlink: true,
    fontSize: props.fontSize || 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: props.theme === 'light' ? {
      background: '#ffffff',
      foreground: '#333333',
      cursor: '#333333',
      selectionBackground: 'rgba(0, 0, 0, 0.1)'
    } : {
      background: '#0f172a', // slate-900
      foreground: '#e2e8f0', // slate-200
      cursor: '#e2e8f0',
      selectionBackground: 'rgba(255, 255, 255, 0.2)'
    },
    disableStdin: props.readOnly,
    convertEol: true, // Treat \n as \r\n
  });

  fitAddon = new FitAddon();
  term.loadAddon(fitAddon);
  term.loadAddon(new WebLinksAddon());

  term.open(terminalRef.value);
  
  try {
    fitAddon.fit();
  } catch (e) {
    console.warn("Fit addon failed initially", e);
  }

  // WebSocket Connection
  if (props.url) {
      socket = new WebSocket(props.url);
      socket.onopen = () => {
        attachAddon = new AttachAddon(socket!);
        term?.loadAddon(attachAddon);
        fitAddon?.fit();
        term?.writeln('\x1b[1;32mConnected to Sandbox Terminal\x1b[0m');
      };
      socket.onerror = (err) => {
          term?.writeln('\x1b[1;31mConnection Error\x1b[0m');
          console.error(err);
      };
      socket.onclose = () => {
          term?.writeln('\x1b[1;33mConnection Closed\x1b[0m');
      };
  } else {
      // Fallback or Local Echo
      term.onData(data => {
        emit('data', data);
        if (!props.url) term?.write(data); // Local echo if no socket
      });
  }

  term.onResize(size => {
    emit('resize', size);
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'resize', cols: size.cols, rows: size.rows }));
    }
  });

  if (props.initialContent) {
    term.write(props.initialContent);
  }

  if (!props.url) {
      // Welcome message only if not connected to backend yet
      term.writeln('\x1b[1;36mAI Autonomous Terminal Initialized\x1b[0m');
      term.writeln('\x1b[38;5;240mWaiting for deployment commands...\x1b[0m\r\n');
  }
};

const write = (data: string) => {
  term?.write(data);
};

const writeln = (data: string) => {
  term?.writeln(data);
};

const clear = () => {
  term?.clear();
};

const copyAll = () => {
  if (term) {
    term.selectAll();
    const text = term.getSelection();
    navigator.clipboard.writeText(text).then(() => {
      term?.clearSelection();
      ElMessage.success('Terminal content copied');
    });
  }
};

const fit = () => {
  nextTick(() => {
    try {
      fitAddon?.fit();
    } catch (e) {
      // ignore
    }
  });
};

// Expose methods
defineExpose({
  write,
  writeln,
  clear,
  fit,
  focus: () => term?.focus()
});

onMounted(() => {
  initTerminal();
  window.addEventListener('resize', fit);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', fit);
  term?.dispose();
});

watch(() => props.theme, (newTheme) => {
  if (!term) return;
  if (newTheme === 'light') {
    term.options.theme = {
      background: '#ffffff',
      foreground: '#333333',
      cursor: '#333333',
      selectionBackground: 'rgba(0, 0, 0, 0.1)'
    };
  } else {
    term.options.theme = {
      background: '#0f172a',
      foreground: '#e2e8f0',
      cursor: '#e2e8f0',
      selectionBackground: 'rgba(255, 255, 255, 0.2)'
    };
  }
});
</script>

<style scoped>
.xterm-container :deep(.xterm) {
  padding: 12px;
}
.xterm-container :deep(.xterm-viewport) {
  scrollbar-width: thin;
  scrollbar-color: #475569 transparent;
}
</style>
