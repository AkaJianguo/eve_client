import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 自动向所有组件注入全局变量，无需手动 @import
        additionalData: `@import "@/assets/styles/variables.scss";`
      }
    }
  }
})