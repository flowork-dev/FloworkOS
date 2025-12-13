//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\GlobalConfirmationDialog.vue total lines 79 
//#######################################################################

<template>
  <v-dialog
    :model-value="confirmation.visible"
    @update:modelValue="cancel"
    max-width="500px"
    persistent
  >
    <v-card class="dialog-card">
      <v-card-title class="orbitron-font d-flex align-center">
        <v-icon :color="confirmation.color || 'warning'" start size="large">{{ confirmation.icon || 'mdi-alert-outline' }}</v-icon>
        {{ confirmation.title }}
      </v-card-title>
      <v-card-text class="pa-5 text-body-1 text-grey-lighten-1">
        {{ confirmation.text }}
      </v-card-text>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="cancel"
        >
          {{ confirmation.cancelText || 'Cancel' }}
        </v-btn>
        <v-btn
          :color="confirmation.color || 'warning'"
          variant="flat"
          @click="confirm"
          class="action-button"
        >
          {{ confirmation.confirmText || 'Confirm' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';

const uiStore = useUiStore();
const { confirmation } = storeToRefs(uiStore);

function confirm() {
  uiStore.answerConfirmation(true);
}

function cancel() {
  uiStore.answerConfirmation(false);
}
</script>

<style scoped>
.dialog-card {
  background-color: #2a2a4a;
  border: 1px solid var(--v-theme-warning);
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
  color: var(--v-theme-warning);
}
.action-button {
  font-weight: bold;
  color: #010c03 !important;
}
/* Style kustom jika warnanya error */
.dialog-card.error-border {
    border-color: var(--v-theme-error);
}
.orbitron-font.error-title {
    color: var(--v-theme-error);
}
</style>
