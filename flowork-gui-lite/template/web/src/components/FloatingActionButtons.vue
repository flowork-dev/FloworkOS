//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\FloatingActionButtons.vue total lines 48 
//#######################################################################

<template>
  <div class="fab-container">
    <v-btn
      icon
      class="fab-item"
      @click="uiStore.setActiveRightPanel('log')"
      :color="uiStore.activeRightPanel === 'log' ? 'primary' : 'grey-darken-3'"
    >
      <v-icon>mdi-math-log</v-icon>
    </v-btn>
    <v-btn
      icon
      class="fab-item"
      @click="uiStore.setActiveRightPanel('promptSender')"
      :color="uiStore.activeRightPanel === 'promptSender' ? 'primary' : 'grey-darken-3'"
    >
      <v-icon>mdi-send</v-icon>
    </v-btn>
  </div>
</template>

<script setup>
import { useUiStore } from '@/store/ui';

const uiStore = useUiStore();
</script>

<style scoped>
.fab-container {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 20;
}

.fab-item {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}
</style>
