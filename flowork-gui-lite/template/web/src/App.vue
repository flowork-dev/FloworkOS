//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\App.vue total lines 156 
//#######################################################################

<template>
  <v-app>
    <AppBar />

    <v-main class="main-content" :class="{ 'no-padding-main': isDesignerPage }">
      <NeuralCanvasBackground />

      <router-view v-slot="{ Component }">
        <transition name="luxury-zoom" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </v-main>

    <div class="notification-container">
      <TransitionGroup name="slide-x-reverse" tag="div">
        <v-alert
          v-for="notification in uiStore.notifications"
          :key="notification.id"
          v-model="notification.model"
          :color="notification.color"
          variant="tonal"
          closable
          @click:close="uiStore.removeNotification(notification.id)"
          class="notification-alert"
          :icon="`mdi-${notification.color === 'success' ? 'check-circle' : notification.color === 'error' ? 'alert-circle' : 'information'}-outline`"
          prominent
          border="start"
        >
          {{ notification.text }}
        </v-alert>
      </TransitionGroup>
    </div>

    <CommandPalette />
    <GlobalConfirmationDialog />
    <GlobalTokenDialog />
    </v-app>
</template>

<script setup>
import { onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import { useUiStore } from '@/store/ui';
import { useWorkflowStore } from '@/store/workflow';

import AppBar from '@/components/AppBar.vue';
import CommandPalette from '@/components/CommandPalette.vue';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';
import GlobalConfirmationDialog from '@/components/GlobalConfirmationDialog.vue';
import GlobalTokenDialog from '@/components/GlobalTokenDialog.vue';

const route = useRoute();
const authStore = useAuthStore();
const uiStore = useUiStore();
const workflowStore = useWorkflowStore();

const isDesktop = import.meta.env.VITE_APP_MODE === 'desktop';
const isDesignerPage = computed(() => route.name === 'Designer');

const handleKeyDown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    uiStore.isCommandPaletteVisible ? uiStore.hideCommandPalette() : uiStore.showCommandPalette();
  }
};

onMounted(async () => {
  window.addEventListener('keydown', handleKeyDown);

  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  if (token) {
    authStore.setToken(token);
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  window.addEventListener('beforeunload', (event) => {
      if (workflowStore.isModified) {
        event.preventDefault();
        event.returnValue = '';
      }
  });
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<style scoped>
.main-content {
  position: relative;
  height: 100vh;
  overflow-y: auto;
  background-color: var(--bg-dark);
}

.main-content.no-padding-main {
  padding-top: 0 !important;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-dark);
}

.notification-container {
  position: fixed; bottom: 16px; right: 16px; z-index: 10000;
  width: 100%; max-width: 350px;
}
.notification-alert {
  margin-top: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  border-width: 2px !important;
}

.slide-x-reverse-enter-active,
.slide-x-reverse-leave-active {
  transition: all 0.3s ease;
}
.slide-x-reverse-enter-from,
.slide-x-reverse-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>

<style>
/* GLOBAL STYLES */
.v-application {
  --v-theme-on-surface-variant: var(--text-secondary) !important;
  color: var(--text-primary) !important;
}
.v-list-item-subtitle, .v-label, .v-field__hint, .v-messages__message {
  color: var(--text-secondary) !important;
  opacity: 1 !important;
}
.text-grey, .text-grey-lighten-1, .text-grey-lighten-2, .text-grey-darken-1, .text-grey-darken-2, .text-grey-darken-3, .text-grey-darken-4 {
  color: var(--text-secondary) !important;
}
.empty-state, .placeholder-view {
  color: var(--text-secondary) !important;
}
.v-toolbar-title, .orbitron-font {
  color: var(--text-primary) !important;
}
h1.orbitron-font, h2.orbitron-font, h3.orbitron-font, .v-toolbar-title.orbitron-font, .v-card-title.orbitron-font, .app-bar .logo-title.orbitron-font {
  color: var(--neon-cyan) !important;
}
/* Lander Header style dihapus karena komponennya udah gak ada */
</style>
