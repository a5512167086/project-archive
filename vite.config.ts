import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import basicSsl from '@vitejs/plugin-basic-ssl'
import svgr from 'vite-plugin-svgr'

export default defineConfig({
  base: '/',
  plugins: [react(), basicSsl(), svgr()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
})
