import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { CodeInspectorPlugin } from 'code-inspector-plugin'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    CodeInspectorPlugin({
      bundler: 'vite',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'vue': 'vue/dist/vue.esm-bundler.js',
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        configure: (proxy, options) => {
          // 拦截并静默处理 HMR 或页面刷新导致的 WebSocket 连接重置错误，避免污染控制台
          proxy.on('error', (err, req, res) => {
            if (err.code === 'ECONNRESET') {
              return;
            }
            console.error('[vite] proxy error:', err);
          });
        }
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            if (err.code === 'ECONNRESET') {
              return;
            }
            console.error('[vite] proxy error:', err);
          });
        }
      }
    }
  }
})
