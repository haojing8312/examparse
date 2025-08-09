import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tauriProxy from './src-tauri-proxy';

export default defineConfig({
  plugins: [react(), tauriProxy()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});


