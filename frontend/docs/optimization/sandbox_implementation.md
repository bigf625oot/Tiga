# Sandbox & Terminal Implementation Guide

## 1. SandboxTerminal.vue Upgrade

### Key Changes
- **WebSocket Integration**: Replace direct API calls (if any) with a WebSocket connection for true PTY interaction.
- **Resize Handler**: Send `resize` events to the backend to ensure correct line wrapping.
- **Theme Sync**: Dynamic theme updating based on global store.

### Code Snippet (Frontend)

```vue
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { AttachAddon } from 'xterm-addon-attach'; // New: WebSocket attachment

const props = defineProps<{
  url: string; // WebSocket URL
}>();

const terminalRef = ref<HTMLElement | null>(null);
let term: Terminal | null = null;
let socket: WebSocket | null = null;

const initTerminal = () => {
  if (!terminalRef.value) return;

  term = new Terminal({
    cursorBlink: true,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#0f172a',
      foreground: '#e2e8f0',
    }
  });

  const fitAddon = new FitAddon();
  term.loadAddon(fitAddon);

  // WebSocket Connection
  socket = new WebSocket(props.url);
  socket.onopen = () => {
    const attachAddon = new AttachAddon(socket!);
    term?.loadAddon(attachAddon);
    fitAddon.fit();
  };

  term.open(terminalRef.value);
  
  // Resize Observer
  const resizeObserver = new ResizeObserver(() => {
    fitAddon.fit();
    if (socket && socket.readyState === WebSocket.OPEN) {
        // Custom protocol message for resize, e.g., JSON
        socket.send(JSON.stringify({ 
            type: 'resize', 
            cols: term?.cols, 
            rows: term?.rows 
        }));
    }
  });
  resizeObserver.observe(terminalRef.value);
};
</script>
```

## 2. SandboxFileManager.vue (New Component)

### Features
- Tree view of the `/workspace` directory.
- Context menu for Download/Delete.
- Drag-and-drop upload zone.

### Implementation Logic
1.  **Fetch**: `GET /api/v2/sandbox/{id}/files?path=/`
2.  **Upload**: `POST /api/v2/sandbox/{id}/upload` (Multipart)
3.  **UI**: Use `el-tree` or `a-tree` customized with file icons.

## 3. SandboxResourceManager.vue (New Component)

### Features
- Real-time CPU/Memory usage charts.
- Process list table.

### Implementation Logic
- **Poll/SSE**: Receive metrics every 2s.
- **Charts**: Use `echarts` or `chart.js` for lightweight rendering.
- **Metrics**:
    - `cpu_percent`
    - `memory_mb`
    - `disk_usage_mb`

## 4. API Contract Updates

### WebSocket Protocol (Terminal)
- **Client -> Server**:
    - Raw text: Stdin input.
    - JSON `{type: 'resize', ...}`: Resize event.
- **Server -> Client**:
    - Raw text: Stdout/Stderr output.
    - JSON `{type: 'error', message: '...'}`: System errors (e.g., Command Blocked).

### SSE Events (Resource Monitor)
- Event: `sandbox_metrics`
- Payload:
```json
{
  "cpu": 12.5,
  "memory": 256,
  "processes": [
    { "pid": 1, "cmd": "python app.py", "cpu": 10.0 }
  ]
}
```
