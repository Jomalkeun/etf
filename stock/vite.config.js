import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite';
import { PrimeVueResolver } from '@primevue/auto-import-resolver';

// https://vite.dev/config/
export default defineConfig({
  base: '/stock/',
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router'], // ref, reactive 등 자동 import
      dts: 'src/auto-imports.d.ts',  // 타입 지원 파일 생성
    }),
    Components({
      resolvers: [PrimeVueResolver()], // PrimeVue 컴포넌트 자동 인식
      dts: 'src/components.d.ts',      // 타입 지원 파일 생성
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
})