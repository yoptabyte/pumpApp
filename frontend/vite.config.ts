import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  cacheDir: '/tmp/pumpapp-vite',
  server: {
    host: '0.0.0.0',
    port: 3000,
  },
  build: {
    outDir: 'build',
    assetsDir: 'static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined;
          }

          const parts = id.split('node_modules/')[1].split('/');
          const packageName = parts[0].startsWith('@') ? `${parts[0]}/${parts[1]}` : parts[0];
          return `vendor-${packageName.replace('@', '').replace('/', '-')}`;
        },
      },
    },
  },
  preview: {
    port: 4173,
  },
});
