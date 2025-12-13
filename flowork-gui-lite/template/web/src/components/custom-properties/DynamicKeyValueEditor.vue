//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\custom-properties\DynamicKeyValueEditor.vue total lines 108 
//#######################################################################

<template>
  <div class="key-value-editor">
    <div class="list-header">
      <label class="v-label text-caption">{{ label }}</label>
      <v-btn @click="addItem" size="x-small" color="cyan" variant="tonal" prepend-icon="mdi-plus-circle">
        Add Data
      </v-btn>
    </div>
    <div class="items-container">
      <div v-if="localItems.length === 0" class="empty-list text-center text-caption text-grey pa-4">
        No data defined.
      </div>
      <div v-for="(item, index) in localItems" :key="index" class="item-row">
        <v-text-field
          v-model="item.name"
          @update:modelValue="updateItem"
          label="Variable Name"
          variant="outlined"
          density="compact"
          hide-details
          class="flex-grow-1"
        ></v-text-field>
        <v-textarea
          v-model="item.value"
          @update:modelValue="updateItem"
          label="Value"
          variant="outlined"
          density="compact"
          rows="1"
          auto-grow
          hide-details
          class="flex-grow-2 mx-2"
        ></v-textarea>
        <v-btn @click="removeItem(index)" icon="mdi-close" size="x-small" variant="text" color="red"></v-btn>
      </div>
    </div>
    <div class="v-messages__message text-caption" style="padding-top: 4px;">{{ hint }}</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  label: String,
  hint: String,
});

const emit = defineEmits(['update:modelValue']);

const localItems = ref(JSON.parse(JSON.stringify(props.modelValue || [])));

watch(() => props.modelValue, (newValue) => {
  localItems.value = JSON.parse(JSON.stringify(newValue || []));
}, { deep: true });

function addItem() {
  localItems.value.push({ name: '', value: '', type: 'Text' }); // Type is kept for compatibility
  emit('update:modelValue', localItems.value);
}

function removeItem(index) {
  localItems.value.splice(index, 1);
  emit('update:modelValue', localItems.value);
}

function updateItem() {
  emit('update:modelValue', localItems.value);
}
</script>

<style scoped>
.key-value-editor {
  margin-bottom: 16px;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.items-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.item-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.flex-grow-1 {
  flex-grow: 1;
}
.flex-grow-2 {
  flex-grow: 2;
}
</style>
