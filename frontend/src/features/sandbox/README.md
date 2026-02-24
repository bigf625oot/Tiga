# Sandbox Result Viewer Component

`SandboxResultViewer` is a Vue 3 component for executing code in a secure sandbox and displaying the results (text, markdown, images, files).

## Usage

```vue
<template>
  <div class="h-[600px] w-full p-4">
    <SandboxResultViewer
      v-model:code="code"
      language="python"
      title="Data Analysis Task"
      :auto-run="false"
      @complete="handleComplete"
      @error="handleError"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import SandboxResultViewer from '@/features/sandbox/components/SandboxResultViewer.vue';

const code = ref(`
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
plt.plot(x, np.sin(x))
plt.title('Sine Wave')
plt.show()
`);

const handleComplete = (result) => {
  console.log('Execution finished:', result);
};

const handleError = (error) => {
  console.error('Execution failed:', error);
};
</script>
```

## Features

- **Code Editor**: Monaco Editor integration for editing code before execution.
- **Visualizations**:
  - **Text/Markdown**: Renders console output with support for Markdown formatting.
  - **Images**: Automatically detects generated images (PNG/JPG) and displays them in Grid or Carousel mode.
- **Controls**:
  - **Run/Cancel**: Execute code or cancel running tasks.
  - **Export**: Download results as Markdown, JSON, or ZIP (for images).
  - **Copy**: One-click copy for output.
- **Status Indication**: Clear loading, success, and error states.

## API Integration

The component uses `SandboxService` to communicate with the backend `/api/v1/sandbox/run` endpoint.
Ensure the backend is running and the `codebox` service is deployed.
