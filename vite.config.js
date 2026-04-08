import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: 'src/frontend',
  envDir: '../../',
  server: {
    port: 3000,
    proxy: {
      '/tasks': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: '../../tests/frontend/setup.js',
    include: ['../../tests/frontend/**/*.{test,spec}.{js,jsx}'],
  },
});
