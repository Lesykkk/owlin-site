import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Lets the dev server answer requests that arrive through the ngrok tunnel.
    allowedHosts: ['video-cornbread-whoopee.ngrok-free.dev'],
  },
})
