# Terminal Access API

This document describes the API for accessing the sandbox terminal with full shell capabilities (login, completion, history).

## WebSocket Endpoint

**URL:** `ws://<host>/api/sandbox/ws/terminal/{session_id}`

### Protocol

The communication uses a simple JSON-based protocol or raw binary stream depending on configuration. For compatibility with `xterm.js` and `xterm-addon-attach`, we recommend a simple message format.

#### Client -> Server

1.  **Resize Terminal**
    ```json
    {
      "type": "resize",
      "cols": 80,
      "rows": 24
    }
    ```

2.  **Input Data** (Keystrokes, commands)
    ```json
    {
      "type": "data",
      "content": "ls -la\r"
    }
    ```

#### Server -> Client

1.  **Output Data**
    ```json
    {
      "type": "data",
      "content": "total 16\r\ndrwxr-xr-x 2 user user 4096 ..."
    }
    ```

### Example Usage (Frontend)

```javascript
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';

const term = new Terminal();
const fitAddon = new FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('terminal'));

const socket = new WebSocket('ws://localhost:8000/api/sandbox/ws/terminal/my-session-id');

socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'data') {
        term.write(msg.content);
    }
};

term.onData((data) => {
    socket.send(JSON.stringify({ type: 'data', content: data }));
});

term.onResize((size) => {
    socket.send(JSON.stringify({
        type: 'resize',
        cols: size.cols,
        rows: size.rows
    }));
});
```

## Backend Implementation Note

The backend should use the E2B SDK's `Terminal` class:

```python
# Pseudo-code for backend
sandbox = Sandbox.connect(session_id)
terminal = sandbox.terminal.start(
    on_data=lambda data: websocket.send_json({"type": "data", "content": data}),
    cols=80, 
    rows=24
)

# Handle incoming WebSocket messages
while True:
    msg = await websocket.receive_json()
    if msg["type"] == "data":
        terminal.send(msg["content"])
    elif msg["type"] == "resize":
        terminal.resize(msg["cols"], msg["rows"])
```
