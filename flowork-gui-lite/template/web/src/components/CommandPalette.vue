//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\CommandPalette.vue total lines 131 
//#######################################################################

<template>
  <v-dialog
    v-model="uiStore.isCommandPaletteVisible"
    max-width="600px"
    @keydown.esc="uiStore.hideCommandPalette()"
    @click:outside="uiStore.hideCommandPalette()"
    class="command-palette-dialog"
  >
    <v-card class="command-palette-card">
      <v-text-field
        v-model="search"
        placeholder="Type a command or search..."
        prepend-inner-icon="mdi-magnify"
        variant="solo-filled"
        flat
        autofocus
        hide-details
        class="command-input"
        ref="searchInput"
      ></v-text-field>

      <v-divider></v-divider>

      <v-list v-if="filteredItems.length > 0" class="command-list" lines="one">
        <v-list-item
          v-for="(item, index) in filteredItems"
          :key="item.id"
          @click="runCommand(item)"
          :class="{ 'v-list-item--active': index === selectedIndex }"
        >
          <template v-slot:prepend>
            <v-icon :icon="item.icon" :color="item.color || 'grey'"></v-icon>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
          <v-list-item-subtitle>{{ item.description }}</v-list-item-subtitle>
        </v-list-item>
      </v-list>
      <div v-else class="no-results">
        No results found.
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useUiStore } from '@/store/ui';
import { useWorkflowStore } from '@/store/workflow';
import { useRouter } from 'vue-router';

const uiStore = useUiStore();
const workflowStore = useWorkflowStore();
const router = useRouter();

const search = ref('');
const selectedIndex = ref(0); // For keyboard navigation
const searchInput = ref(null); // Ref to focus the input

const allCommands = computed(() => [
  { id: 'nav_designer', title: 'Go to Designer', icon: 'mdi-sitemap-outline', action: () => router.push({ name: 'Designer' }) },
  { id: 'nav_dashboard', title: 'Go to Dashboard', icon: 'mdi-view-dashboard-outline', action: () => router.push({ name: 'Dashboard' }) },
  { id: 'nav_settings', title: 'Go to Settings', icon: 'mdi-cog-outline', action: () => router.push({ name: 'Settings' }) },
  { id: 'nav_my_engines', title: 'Manage Engines', icon: 'mdi-key-chain', action: () => router.push({ name: 'MyEngines' }) },
  { id: 'nav_ai_center', title: 'Go to AI Center', icon: 'mdi-brain', action: () => router.push({ name: 'AiCenter' }) },
  { id: 'nav_ai_trainer', title: 'Go to AI Trainer', icon: 'mdi-school-outline', action: () => router.push({ name: 'AiTrainer' }) },

  { id: 'wf_run', title: 'Run Workflow', icon: 'mdi-play', color: 'success', action: () => workflowStore.executeCurrentWorkflow() },
  { id: 'wf_sim', title: 'Simulate Workflow', icon: 'mdi-play-outline', color: 'info', action: () => workflowStore.simulateCurrentWorkflow() },
  { id: 'wf_save', title: 'Save Workflow', icon: 'mdi-content-save', color: 'cyan', action: () => document.dispatchEvent(new CustomEvent('flowork-save-request')) },
  { id: 'wf_clear', title: 'Clear Canvas', icon: 'mdi-delete-sweep-outline', color: 'error', action: () => workflowStore.clearCanvas() },
]);

const filteredItems = computed(() => {
    if (!search.value) {
        return allCommands.value;
    }
    const s = search.value.toLowerCase();
    return allCommands.value.filter(item =>
        item.title.toLowerCase().includes(s) ||
        (item.description && item.description.toLowerCase().includes(s))
    );
});

function runCommand(item) {
  if (item && item.action) {
    item.action();
  }
  uiStore.hideCommandPalette();
}

watch(() => uiStore.isCommandPaletteVisible, (isVisible) => {
  if (isVisible) {
    search.value = '';
    selectedIndex.value = 0;
    setTimeout(() => {
        searchInput.value?.focus();
    }, 100);
  }
});
</script>

<style scoped>
.command-palette-card {
  background-color: #161625;
  border: 1px solid rgba(0, 245, 255, 0.3);
}
.command-input :deep(.v-field) {
  background-color: #161625 !important;
  color: white !important;
}
.command-list {
  background-color: transparent !important;
  max-height: 400px;
  overflow-y: auto;
}
.command-list .v-list-item--active {
  background-color: rgba(0, 245, 255, 0.1) !important;
  border-left: 3px solid #00f5ff;
}
.no-results {
  padding: 16px;
  text-align: center;
  color: #B0BEC5;
}
</style>
