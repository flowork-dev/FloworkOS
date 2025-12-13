//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\settings\SettingsField.vue total lines 48 
//#######################################################################

<template>
  <div>
    <v-row align="center" class="setting-row">
      <v-col cols="12" md="4">
        <label class="settings-label">{{ label }}</label>
        <div v-if="hint" class="settings-hint">
          {{ hint }}
        </div>
      </v-col>
      <v-col cols="12" md="8">
        <slot></slot>
      </v-col>
    </v-row>
    <v-divider class="my-4"></v-divider>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  hint: String,
});
</script>

<style scoped>
.settings-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
  display: block;
}

.settings-hint {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

.setting-row {
  min-height: 68px;
}
</style>
