<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as monaco from 'monaco-editor';

// Configure worker environment for Monaco (simplified)
// In a real Vite setup, you might use a plugin or specific worker config
// self.MonacoEnvironment = {
//   getWorker: function (workerId, label) {
//     return new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
//   }
// };

const props = defineProps<{
  modelValue: string;
  language?: string;
  theme?: string;
  readOnly?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
}>();

const editorContainer = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

onMounted(() => {
  if (editorContainer.value) {
    editor = monaco.editor.create(editorContainer.value, {
      value: props.modelValue,
      language: props.language || 'sql',
      theme: props.theme || 'vs-dark', // 'vs', 'vs-dark', 'hc-black'
      readOnly: props.readOnly || false,
      automaticLayout: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      fontSize: 12,
      lineNumbers: 'on',
      renderLineHighlight: 'all',
      tabSize: 2,
    });

    editor.onDidChangeModelContent(() => {
      const value = editor?.getValue() || '';
      emit('update:modelValue', value);
      emit('change', value);
    });
  }
});

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (editor && newValue !== editor.getValue()) {
    editor.setValue(newValue);
  }
});

// Watch for language changes
watch(() => props.language, (newLang) => {
  if (editor) {
    monaco.editor.setModelLanguage(editor.getModel()!, newLang || 'sql');
  }
});

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose();
  }
});
</script>

<template>
  <div ref="editorContainer" class="w-full h-full min-h-[150px] border rounded-md overflow-hidden"></div>
</template>