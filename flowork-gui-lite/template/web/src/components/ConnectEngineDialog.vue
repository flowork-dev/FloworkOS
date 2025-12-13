//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\ConnectEngineDialog.vue total lines 69 
//#######################################################################

<template>
  <v-dialog :model-value="uiStore.isConnectEngineDialogVisible" @update:modelValue="closeDialog" max-width="500px" persistent>
    <v-card class="dialog-card">
      <v-card-title class="orbitron-font d-flex align-center">
        <v-icon color="warning" start size="large">mdi-server-network-off</v-icon>
        Engine Connection Required
      </v-card-title>
      <v-card-text class="pa-5">
        <p class="text-body-1 text-grey-lighten-1 mb-4">
          You are currently in **Offline/Example Mode**.
        </p>
        <p class="text-body-2 text-grey-lighten-2">
          To run, simulate, or save workflows, you must first connect to your local Flowork Engine. Please ensure your engine is running and that your identity is correctly configured.
        </p>
      </v-card-text>
      <v-card-actions class="pa-4">
        <v-btn variant="text" @click="closeDialog">Close</v-btn>
        <v-spacer></v-spacer>
        <v-btn
          color="cyan"
          variant="flat"
          @click="goToEngineConfig"
          class="action-button"
          prepend-icon="mdi-key-chain"
        >
          Configure Identity & Engine
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { useUiStore } from '@/store/ui';
import { useRouter } from 'vue-router';

const uiStore = useUiStore();
const router = useRouter();

function closeDialog() {
  uiStore.hideConnectEngineDialog();
}

function goToEngineConfig() {
  uiStore.hideConnectEngineDialog();
  router.push('/my-engines');
}
</script>

<style scoped>
.dialog-card {
  background-color: #2a2a4a;
  border: 1px solid #ff9800; /* Warning color */
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
  color: #ff9800;
}
.action-button {
  font-weight: bold;
  color: #010c03 !important;
}
</style>
