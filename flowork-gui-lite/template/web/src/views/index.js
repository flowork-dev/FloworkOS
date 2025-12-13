//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\index.js total lines 41 
//#######################################################################

import { createRouter, createWebHistory } from 'vue-router';
import Designer from '@/views/Designer.vue';
import Dashboard from '@/views/Dashboard.vue';
import AiCenter from '@/views/AiCenter.vue';
import Settings from '@/views/Settings.vue';

const routes = [
  {
    path: '/',
    name: 'Designer',
    component: Designer,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/ai-center',
    name: 'AICenter',
    component: AiCenter,
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
