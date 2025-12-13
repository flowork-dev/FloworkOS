//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\router\index.js total lines 121 
//#######################################################################

import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const Designer = () => import('@/views/Designer.vue');
const Dashboard = () => import('@/views/Dashboard.vue');
const Settings = () => import('@/views/Settings.vue');
const QuickTools = () => import('@/views/QuickTools.vue');
const Diagnostics = () => import('@/views/Diagnostics.vue');
const Marketplace = () => import('@/views/Marketplace.vue');
const MarketplaceItem = () => import('@/views/MarketplaceItem.vue');

const isDesktopMode = import.meta.env.VITE_APP_MODE === 'desktop';

let routes = [
    { path: '/', redirect: { name: 'Designer' } },

    { path: '/login', redirect: { name: 'Designer' } },

    {
        path: '/designer',
        name: 'Designer',
        component: Designer,
        meta: { requiresAuth: true, title: 'Designer' }
    },

    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true, title: 'Dashboard' }
    },

    {
        path: '/quick-tools',
        name: 'QuickTools',
        component: QuickTools,
        meta: { requiresAuth: true, title: 'Quick Tools' }
    },

    {
        path: '/marketplace',
        name: 'Marketplace',
        component: Marketplace,
        meta: { requiresAuth: false, title: 'Marketplace' }
    },
    {
        path: '/marketplace/item/:id',
        name: 'MarketplaceItem',
        component: MarketplaceItem,
        props: true,
        meta: { requiresAuth: false }
    },

    {
        path: '/settings',
        name: 'Settings',
        component: Settings,
        meta: { requiresAuth: true, title: 'Settings' }
    },

    {
        path: '/diagnostics',
        name: 'Diagnostics',
        component: Diagnostics,
        meta: { requiresAuth: true, title: 'Diagnostics' }
    }
];

if (isDesktopMode) {
    console.log("🔥 [Router] DESKTOP MODE - Strict Routing Active.");
    const WHITELIST = [
        'Designer', 'Dashboard', 'QuickTools',
        'Marketplace', 'MarketplaceItem', 'Settings', 'Diagnostics'
    ];
    routes = routes.filter(r => WHITELIST.includes(r.name) || r.path === '/');
}

const router = createRouter({
  history: isDesktopMode ? createWebHashHistory() : createWebHistory(),
  routes,
});

function updateMetaTag(name, content) {
    let el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    if (!el) {
        el = document.createElement('meta');
        if (name.startsWith('og:')) el.setAttribute('property', name);
        else el.setAttribute('name', name);
        document.head.appendChild(el);
    }
    el.setAttribute('content', content || '');
}

router.beforeEach((to, from, next) => {
    if (isDesktopMode && (!to.name || ['Lander', 'Login'].includes(to.name))) {
         return next({ name: 'Designer' });
    }

    const nearestWithTitle = to.matched.slice().reverse().find(r => r.meta && r.meta.title);
    if(nearestWithTitle) document.title = nearestWithTitle.meta.title + " - Flowork";

    const authStore = useAuthStore();

    if (isDesktopMode) {
        return next();
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        return next({ name: 'Settings' });
    }

    next();
});

export default router;
