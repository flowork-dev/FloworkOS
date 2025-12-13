//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\AppBar.vue total lines 261 
//#######################################################################

<template>
  <v-app-bar flat class="app-bar" app>
    <template v-if="isDesignerPage">
      <v-btn icon @click="uiStore.toggleToolbox" class="ml-2">
        <v-icon>{{ uiStore.isToolboxOpen ? 'mdi-menu-open' : 'mdi-menu' }}</v-icon>
      </v-btn>
    </template>

    <v-toolbar-title class="logo-title" @click="goToDesigner" :class="{ 'ml-4': !isDesignerPage }">
      FLOWORK <span v-if="isDesktop" class="text-caption text-cyan ml-2 border px-1 rounded">LITE</span>
    </v-toolbar-title>

    <div v-if="isDesignerPage" class="mode-selector-container d-none d-md-flex align-center gap-2">
        <v-btn-toggle v-model="uiStore.designerMode" mandatory variant="outlined" density="compact" class="mode-selector" @update:model-value="onModeChange">
            <v-btn value="logic" :disabled="isReadOnly" class="mode-btn"><v-icon start>mdi-sitemap-outline</v-icon>Logic</v-btn>
            <v-btn value="data" :disabled="isReadOnly" class="mode-btn"><v-icon start>mdi-database-eye-outline</v-icon>Dataflow</v-btn>
            <v-btn value="debugger" :disabled="isReadOnly" class="mode-btn"><v-icon start>mdi-bug-check-outline</v-icon>Debugger</v-btn>
            <v-btn value="logs" :disabled="isReadOnly" class="mode-btn"><v-icon start>mdi-math-log</v-icon>Logs</v-btn>
        </v-btn-toggle>
    </div>

    <v-spacer></v-spacer>

    <v-btn
      v-if="authStore.isAuthenticated || isDesktop"
      icon class="header-btn mr-2" color="red-accent-2" title="Clean System Cache" @click="showCleanDialog = true"
    >
      <v-icon>mdi-broom</v-icon>
    </v-btn>

    <v-menu
      v-if="authStore.isAuthenticated || isDesktop"
      v-model="isMenuOpen"
      :close-on-content-click="false"
      content-class="app-grid-menu"
      location="bottom end"
      offset="10"
    >
      <template v-slot:activator="{ props }">
        <v-btn v-bind="props" icon class="header-btn glow-trigger" title="Main Menu">
            <v-icon size="large" color="cyan-accent-2">mdi-apps</v-icon>
        </v-btn>
      </template>

      <v-card class="app-grid-menu-card" color="#161625">
        <v-container fluid class="pa-2">
            <div class="menu-group-title mb-2">APPLICATIONS</div>
            <v-row dense>
                <v-col cols="6" v-for="item in mainApps" :key="item.title">
                    <v-card :to="item.to" class="menu-grid-card" hover @click="closeMenu">
                        <v-icon :icon="item.icon" :color="item.color" size="large" class="mb-2"></v-icon>
                        <div class="text-caption font-weight-bold text-white">{{ item.title }}</div>
                    </v-card>
                </v-col>
            </v-row>

            <v-divider class="my-3 border-dashed"></v-divider>

            <div class="menu-group-title mb-2">SYSTEM CONTROL</div>
            <v-row dense>
                 <v-col cols="6" v-for="item in systemApps" :key="item.title">
                    <v-card :to="item.to" class="menu-grid-card" hover @click="closeMenu">
                        <v-icon :icon="item.icon" :color="item.color" size="large" class="mb-2"></v-icon>
                        <div class="text-caption font-weight-bold text-white">{{ item.title }}</div>
                    </v-card>
                </v-col>
            </v-row>
        </v-container>
      </v-card>
    </v-menu>

    <template v-if="!authStore.isAuthenticated && !isDesktop">
        <v-btn to="/login" variant="tonal" class="mx-2 orbitron-font" color="cyan" prepend-icon="mdi-login-variant">Login</v-btn>
    </template>

    <v-progress-linear :active="authStore.isLoading" indeterminate color="cyan" absolute location="bottom"></v-progress-linear>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="top">{{ snackbar.text }}</v-snackbar>

    <v-dialog v-model="showCleanDialog" max-width="500">
      <v-card color="#1E1E2E" class="border-glow">
        <v-card-title class="text-h5 orbitron-font text-red-accent-2">
          <v-icon start icon="mdi-alert-octagon-outline" color="red-accent-2"></v-icon> System Cleanup
        </v-card-title>
        <v-card-text class="pt-4">
          <p class="text-body-1 mb-2">Are you sure you want to purge <strong>All System Cache & History?</strong></p>
          <v-alert type="warning" variant="tonal" density="compact" class="mb-2" border="start">This action is irreversible.</v-alert>
        </v-card-text>
        <v-card-actions class="pb-4 px-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey" @click="showCleanDialog = false">Cancel</v-btn>
          <v-btn color="red-accent-2" variant="flat" :loading="isCleaning" prepend-icon="mdi-delete-forever" @click="cleanSystemCache">Purge All</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app-bar>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUiStore } from '@/store/ui';
import { useAuthStore } from '@/store/auth';
import { useSocketStore } from '@/store/socket';
import { useWorkflowStore } from '@/store/workflow';
import { storeToRefs } from 'pinia';
import api from '@/api';

const uiStore = useUiStore();
const authStore = useAuthStore();
const socketStore = useSocketStore();
const workflowStore = useWorkflowStore();
const router = useRouter();
const route = useRoute();
const { isReadOnly } = storeToRefs(workflowStore);

const isDesktop = import.meta.env.VITE_APP_MODE === 'desktop';
const isDesignerPage = computed(() => route.name === 'Designer');
const isMenuOpen = ref(false);

watch(route, () => { isMenuOpen.value = false; });
function closeMenu() { isMenuOpen.value = false; }

const showCleanDialog = ref(false);
const isCleaning = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' });

const mainApps = [
    { title: 'Designer', icon: 'mdi-sitemap-outline', to: { name: 'Designer' }, color: 'cyan-accent-3' },
    { title: 'Dashboard', icon: 'mdi-view-dashboard-outline', to: { name: 'Dashboard' }, color: 'purple-accent-3' },
    { title: 'Quick Tools', icon: 'mdi-flash-outline', to: { name: 'QuickTools' }, color: 'amber-accent-3' },
    { title: 'Marketplace', icon: 'mdi-store-outline', to: { name: 'Marketplace' }, color: 'green-accent-3' },
];

const systemApps = [
    { title: 'Settings', icon: 'mdi-cog-outline', to: { name: 'Settings' }, color: 'grey-lighten-1' },
    { title: 'Diagnostics', icon: 'mdi-hospital-box-outline', to: { name: 'Diagnostics' }, color: 'red-accent-2' },
];

function onModeChange(newMode) {
    uiStore.setDesignerMode(newMode);
    uiStore.closeRightPanel();
}

function goToDesigner() {
    router.push('/');
}

async function cleanSystemCache() {
    isCleaning.value = true;
    try {
        const res = await api.post('/api/v1/system/clear-cache');
        console.log("Cleanup Stats:", res.data.stats);
        showCleanDialog.value = false;
        snackbar.value = { show: true, text: `SUCCESS! Deleted ${res.data.stats.files_deleted} Files.`, color: 'success' };
        if (route.name === 'Dashboard') window.location.reload();
    } catch (error) {
        console.error("Cleanup Failed:", error);
        snackbar.value = { show: true, text: 'Cleanup failed.', color: 'error' };
    } finally {
        isCleaning.value = false;
    }
}
</script>

<style scoped>
.app-bar {
  background-color: rgba(10, 15, 30, 0.7) !important;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-glow-soft) !important;
  color: var(--text-primary);
}
.app-bar :deep(.v-btn .v-icon) {
  color: var(--text-primary) !important;
  opacity: 1;
}
.app-bar :deep(.v-btn:hover .v-icon) {
  color: var(--neon-cyan) !important;
}
.border-glow {
    border: 1px solid rgba(255, 82, 82, 0.3);
    box-shadow: 0 0 15px rgba(255, 82, 82, 0.1);
}
.logo-title {
  font-family: 'Orbitron', monospace;
  font-weight: 700;
  color: var(--neon-cyan);
  cursor: pointer;
  letter-spacing: 1px;
}
.mode-selector-container {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
}
.mode-selector {
    background-color: rgba(0,0,0,0.2);
    border: 1px solid var(--border-glow-soft);
}
.mode-btn {
    color: var(--text-secondary);
    font-family: 'Orbitron', monospace;
    letter-spacing: 0.5px;
}
.mode-btn.v-btn--active {
    color: var(--neon-cyan);
    background-color: rgba(0, 245, 255, 0.1);
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
}

/* MENU KOTAK STYLING */
.app-grid-menu-card {
  background-color: rgba(18, 18, 24, 0.98) !important;
  border: 1px solid var(--border-glow-soft);
  padding: 12px;
  min-width: 320px;
  backdrop-filter: blur(20px);
}
.menu-group-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.7rem;
    font-weight: bold;
    color: var(--text-secondary);
    letter-spacing: 1px;
    padding-left: 4px;
}
.menu-grid-card {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 16px;
    transition: all 0.2s ease;
    cursor: pointer;
}
.menu-grid-card:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border-color: rgba(0, 245, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.border-dashed {
    border-color: rgba(255, 255, 255, 0.1) !important;
}
.glow-trigger {
    transition: all 0.3s ease;
}
.glow-trigger:hover {
    background-color: rgba(0, 229, 255, 0.1);
    transform: scale(1.05);
}
</style>
