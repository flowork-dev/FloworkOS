//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\custom-properties\CronEditor.vue total lines 92 
//#######################################################################

<template>
  <div class="cron-editor">
    <label class="v-label text-caption">{{ label }}</label>
    <div class="cron-inputs">
      <v-text-field
        label="Menit"
        v-model="parts[0]"
        @update:modelValue="updateCronString"
        variant="outlined"
        density="compact"
        hide-details
      ></v-text-field>
      <v-text-field
        label="Jam"
        v-model="parts[1]"
        @update:modelValue="updateCronString"
        variant="outlined"
        density="compact"
        hide-details
      ></v-text-field>
      <v-text-field
        label="Hari (Bln)"
        v-model="parts[2]"
        @update:modelValue="updateCronString"
        variant="outlined"
        density="compact"
        hide-details
      ></v-text-field>
      <v-text-field
        label="Bulan"
        v-model="parts[3]"
        @update:modelValue="updateCronString"
        variant="outlined"
        density="compact"
        hide-details
      ></v-text-field>
      <v-text-field
        label="Hari (Mgg)"
        v-model="parts[4]"
        @update:modelValue="updateCronString"
        variant="outlined"
        density="compact"
        hide-details
      ></v-text-field>
    </div>
    <div class="v-messages__message text-caption" style="padding-top: 4px;">{{ hint }}</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: '* * * * *'
  },
  label: String,
  hint: String,
});

const emit = defineEmits(['update:modelValue']);

const parts = ref(props.modelValue.split(' '));

watch(() => props.modelValue, (newValue) => {
  parts.value = newValue.split(' ');
});

function updateCronString() {
  const newCronString = parts.value.join(' ');
  emit('update:modelValue', newCronString);
}
</script>

<style scoped>
.cron-editor {
  margin-bottom: 16px;
}
.cron-inputs {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-top: 4px;
}
</style>
