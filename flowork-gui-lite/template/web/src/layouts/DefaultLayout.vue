//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\layouts\DefaultLayout.vue total lines 156 
//#######################################################################

<template>
  <v-app class="flowork-app">
    <v-main class="flowork-main">
      <div class="layout-container">

        <div class="sidebar-area">
          <v-navigation-drawer
            rail
            permanent
            class="main-sidebar glass-effect"
            theme="dark"
          >
            <div class="d-flex flex-column align-center py-4 fill-height">
              <v-avatar size="40" class="mb-6 logo-glow cursor-pointer" @click="$router.push('/')">
                <v-img src="/favicon.svg" alt="Flowork"></v-img>
              </v-avatar>

              <v-list density="compact" nav class="flex-grow-1 w-100 px-2">
                <v-list-item
                  v-for="item in menuItems"
                  :key="item.value"
                  :value="item.value"
                  :to="item.to"
                  :prepend-icon="item.icon"
                  :active="isRouteActive(item.to)"
                  active-class="nav-active"
                  class="mb-2 rounded-lg nav-item"
                  variant="text"
                >
                  <v-tooltip activator="parent" location="right">{{ loc(item.title) }}</v-tooltip>
                </v-list-item>
              </v-list>

              <div class="mt-auto w-100 px-2 d-flex flex-column align-center gap-2">
                <v-btn icon variant="text" to="/settings" class="nav-btn">
                  <v-icon>mdi-cog-outline</v-icon>
                  <v-tooltip activator="parent" location="right">Settings</v-tooltip>
                </v-btn>
                <v-btn icon variant="text" @click="authStore.logout()" class="nav-btn mb-2">
                  <v-icon color="error">mdi-logout</v-icon>
                  <v-tooltip activator="parent" location="right">Logout</v-tooltip>
                </v-btn>
              </div>
            </div>
          </v-navigation-drawer>
        </div>

        <div class="content-area d-flex flex-column">

          <AppBar class="flex-shrink-0" />

          <div class="view-container flex-grow-1 position-relative overflow-hidden">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </div>
        </div>

        <RightSidebar />

      </div>
    </v-main>

    <GlobalConfirmationDialog />
    <GlobalTokenDialog />
    <ConnectEngineDialog />
    <DebugPopup />

    <v-snackbar
      v-model="uiStore.notification.show"
      :color="uiStore.notification.color"
      :timeout="3000"
      location="top right"
      class="mt-12 mr-4"
    >
      {{ uiStore.notification.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="uiStore.notification.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import { useUiStore } from '@/store/ui';
import { useLocaleStore } from '@/store/locale';
import { storeToRefs } from 'pinia';

import GlobalConfirmationDialog from '@/components/GlobalConfirmationDialog.vue';
import GlobalTokenDialog from '@/components/GlobalTokenDialog.vue';
import ConnectEngineDialog from '@/components/ConnectEngineDialog.vue';
import DebugPopup from '@/components/DebugPopup.vue';
import RightSidebar from '@/components/RightSidebar.vue';
import AppBar from '@/components/AppBar.vue';

const route = useRoute();
const authStore = useAuthStore();
const uiStore = useUiStore();
const localeStore = useLocaleStore();
const { loc } = storeToRefs(localeStore);

const menuItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard-outline', value: 'dashboard', to: '/dashboard' },
  { title: 'Marketplace', icon: 'mdi-store-outline', value: 'marketplace', to: '/marketplace' },
  { title: 'Widgets', icon: 'mdi-view-grid-plus-outline', value: 'widgets', to: '/widgets' }, // <--- INI BARIS PENTINGNYA
  { title: 'Quick Tools', icon: 'mdi-rocket-launch-outline', value: 'quick-tools', to: '/quick-tools' },
  { title: 'Designer', icon: 'mdi-vector-polyline', value: 'designer', to: '/design' },
  { title: 'My Engines', icon: 'mdi-server-network', value: 'engines', to: '/engines' },
  { title: 'AI Center', icon: 'mdi-brain', value: 'ai', to: '/ai-center' },
];

function isRouteActive(path) {
  return route.path === path;
}
</script>

<style scoped>
.flowork-app { background-color: #0F111A; color: #E0E0E0; font-family: 'Inter', sans-serif; }
.flowork-main { height: 100vh; overflow: hidden; }
.layout-container { display: flex; height: 100%; width: 100%; position: relative; }
.sidebar-area { width: 56px; flex-shrink: 0; z-index: 100; }
.content-area { flex-grow: 1; height: 100%; overflow: hidden; position: relative; }

/* Glass Sidebar */
.main-sidebar {
  background: rgba(20, 20, 30, 0.6) !important;
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-active { color: #00F5FF !important; background: rgba(0, 245, 255, 0.1); }
.logo-glow { filter: drop-shadow(0 0 8px rgba(0, 245, 255, 0.5)); transition: transform 0.3s; }
.logo-glow:hover { transform: rotate(180deg); }
.nav-btn:hover { color: #00F5FF; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.view-container {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
</style>
