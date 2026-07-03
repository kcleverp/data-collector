import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 개발 시(npm run dev): 프론트는 5173, /api 요청은 백엔드(8000)로 프록시.
// 배포 시(npm run build): dist/ 를 백엔드가 그대로 서빙.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: { outDir: 'dist' },
})
