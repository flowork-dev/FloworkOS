//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\vite.config.js total lines 67 
//#######################################################################

import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [
      vue({
        template: { transformAssetUrls }
      }),
      vuetify({
        autoImport: true,
        styles: {
          configFile: 'src/styles/settings.scss',
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@mdi/font': path.resolve(__dirname, 'node_modules/@mdi/font'),
      },
    },
    publicDir: 'public',
    server: {
      host: '127.0.0.1',
      port: 5173,
      allowedHosts: ['flowork.cloud'],
      hmr: {
        protocol: 'ws',
        host: '127.0.0.1',
        port: 5173,
      },
      proxy: {
        '/api/socket.io': {
          target: env.VITE_GATEWAY_URL || 'http://localhost:8000',
          ws: true, // WAJIB: Memberitahu Vite untuk mem-proxy koneksi WebSocket
          changeOrigin: true,
          secure: false,
        },
        '/api': {
          target: env.VITE_GATEWAY_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true, // Hapus console.log di production build
          drop_debugger: true,
        },
      },
    },
  };
});
