import { defineConfig } from 'vite';

export default defineConfig({
  publicDir: 'web/public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
