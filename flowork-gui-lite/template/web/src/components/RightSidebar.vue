//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\RightSidebar.vue total lines 76 
//#######################################################################

<template>
  <div class="right-sidebar" :class="{ 'is-open': !!uiStore.activeRightPanel }">
    <div v-if="uiStore.activeRightPanel === 'properties'" class="sidebar-panel">
      <PropertiesPanel />
    </div>

    <div v-if="uiStore.activeRightPanel === 'log'" class="sidebar-panel log-panel-wrapper">
      <LogPanel />
    </div>

    <div v-if="uiStore.activeRightPanel === 'promptSender'" class="sidebar-panel">
      <h3 class="panel-title">Prompt Sender</h3>
      <v-textarea label="Enter your prompt here..." variant="outlined" rows="5"></v-textarea>
      <v-btn color="primary" block>Send Prompt</v-btn>
    </div>
  </div>
</template>

<script setup>
import { useUiStore } from '@/store/ui';
import PropertiesPanel from './PropertiesPanel.vue';
import LogPanel from './panels/LogPanel.vue';

const uiStore = useUiStore();
</script>

<style scoped>
.right-sidebar {
  position: fixed; /* Changed to fixed to float above everything */
  top: 64px; /* Assuming standard AppBar height, can use var(--v-layout-top) if set */
  right: 0;
  /* [GEMINI] WIDENED SIDEBAR TO 500px */
  width: 500px;
  height: calc(100vh - 64px);
  background-color: #1e1e1e;
  border-left: 1px solid #333;
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 900; /* High z-index to sit above canvas but below dialogs */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.5); /* Added shadow for depth */
}

.right-sidebar.is-open {
  transform: translateX(0);
}

.sidebar-panel {
  padding: 20px; /* More padding for breathing room */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.log-panel-wrapper {
  padding: 0;
  height: 100%;
}

.panel-title {
  color: #00f5ff;
  font-family: 'Orbitron', sans-serif;
  margin-bottom: 16px;
  font-size: 1.1rem;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
}
</style>
