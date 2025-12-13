//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\GlobalTokenDialog.vue total lines 88 
//#######################################################################

<template>
  <v-dialog
    :model-value="tokenDialog.visible"
    @update:modelValue="close"
    max-width="700px"
    persistent
  >
    <v-card class="dialog-card">
      <v-card-title class="orbitron-font d-flex align-center">
        <v-icon color="cyan" start size="large">mdi-key-variant</v-icon>
        {{ tokenDialog.title }}
      </v-card-title>
      <v-card-text class="pa-5">
        <p class="text-body-2 text-grey-lighten-1 mb-4">
          {{ tokenDialog.text }}
        </p>

        <div v-for="item in tokenDialog.items" :key="item.label" class="mb-3">
            <v-label class="text-caption">{{ item.label }}</v-label>
            <v-text-field
                :model-value="item.value"
                readonly
                variant="solo-filled"
                density="compact"
                hide-details
                append-inner-icon="mdi-content-copy"
                @click:append-inner="copyToClipboard(item.value)"
                class="token-field"
            ></v-text-field>
        </div>

      </v-card-text>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          color="cyan"
          variant="flat"
          @click="close"
          class="action-button"
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';

const uiStore = useUiStore();
const { tokenDialog } = storeToRefs(uiStore);

function close() {
  uiStore.hideTokenDialog();
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
  uiStore.showNotification({ text: 'Copied to clipboard!', color: 'success' });
}
</script>

<style scoped>
.dialog-card {
  background-color: #2a2a4a;
  border: 1px solid var(--neon-cyan);
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
  color: var(--neon-cyan);
}
.action-button {
  font-weight: bold;
  color: #010c03 !important;
}
.token-field :deep(input) {
    font-family: monospace;
    font-size: 0.9rem;
}
</style>
