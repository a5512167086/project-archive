import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import svgr from 'vite-plugin-svgr'

export default defineConfig({
  base: '/',
  plugins: [react(), svgr()],
  optimizeDeps: {
    include: [
      '@fullcalendar/core',
      '@fullcalendar/react',
      '@fullcalendar/daygrid'
    ]
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})
