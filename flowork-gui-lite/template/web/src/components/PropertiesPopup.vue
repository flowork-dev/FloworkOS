//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\PropertiesPopup.vue total lines 52 
//#######################################################################

<template>
  <v-dialog v-model="show" max-width="500px">
    <v-card>
      <v-card-title>
        <span class="text-h5">{{ node?.label }} Properties</span>
      </v-card-title>

      <v-card-text>
        <p><strong>Module ID:</strong> {{ node?.data.moduleInfo.id }}</p>
        <p class="mt-4 text-medium-emphasis">Configuration form will be rendered here.</p>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="blue-darken-1" variant="text" @click="close">Cancel</v-btn>
        <v-btn color="blue-darken-1" variant="text" @click="save">Save</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean, // Untuk v-model
  node: Object
})

const emit = defineEmits(['update:modelValue', 'save'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function close() {
  show.value = false
}

function save() {
  console.log("Saving properties for node:", props.node.id);
  emit('save');
  close();
}
</script>
