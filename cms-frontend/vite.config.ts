import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src')  // ✅ 必须有这一行
        }
    },
    plugins: [vue()],
    server: {
        port: 3000,
        open: true
    }
})