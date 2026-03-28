<template>
  <div class="ascii-art-container my-4 p-4 bg-zinc-900 text-green-400 rounded-lg border border-zinc-800 overflow-x-auto shadow-inner">
    <pre class="m-0 p-0 font-mono text-[10px] sm:text-xs leading-none" style="font-family: 'Courier New', Courier, monospace; letter-spacing: 0;"><code>{{ code }}</code></pre>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  code: string;
}>();
</script>