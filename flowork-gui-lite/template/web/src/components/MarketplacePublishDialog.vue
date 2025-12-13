//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\MarketplacePublishDialog.vue total lines 248 
//#######################################################################

<template>
  <v-dialog :model-value="modelValue" @update:modelValue="$emit('update:modelValue', $event)" max-width="600px" persistent>
    <v-card class="dialog-card">
      <v-card-title class="orbitron-font d-flex align-center">
        <v-icon :color="isEditMode ? 'yellow' : 'cyan'" start size="large">
            {{ isEditMode ? 'mdi-file-document-edit-outline' : 'mdi-store-plus-outline' }}
        </v-icon>
        {{ dialogTitle }}
      </v-card-title>

      <v-card-text>
        <p class="text-caption text-grey-lighten-1 mb-4">
          {{ isEditMode
            ? 'Update the details of your existing item.'
            : 'Publish your content to the public Flowork marketplace.'
          }}
        </p>

        <v-alert
          v-if="isSmartPackage"
          type="success"
          variant="tonal"
          class="mb-4 border-success"
          icon="mdi-package-variant-closed"
        >
          <div class="d-flex flex-column">
            <strong>Smart Package Ready</strong>
            <span class="text-caption">Module has been auto-zipped by Flowork Engine. No browsing needed.</span>
          </div>
        </v-alert>

        <v-text-field
          v-if="isEditMode"
          v-model="formData.id"
          label="Item ID (Read-Only)"
          variant="outlined"
          density="compact"
          class="hacker-input mb-4"
          readonly
          disabled
        ></v-text-field>

        <v-text-field
          v-model="formData.name"
          label="Item Name"
          placeholder="e.g., AI YouTube Short Video Generator"
          variant="outlined"
          density="compact"
          class="hacker-input mb-4"
          :rules="[v => !!v || 'Name is required']"
          :readonly="isSmartPackage"
        ></v-text-field>

        <v-textarea
          v-model="formData.desc"
          label="Description"
          placeholder="Describe what this item does..."
          variant="outlined"
          density="compact"
          rows="4"
          class="hacker-input mb-4"
          hide-details
        ></v-textarea>

        <v-alert type="info" variant="tonal" density="compact" class="mb-2">
           During the beta phase, all published items are <strong>Free</strong>.
        </v-alert>

      </v-card-text>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="$emit('update:modelValue', false)" :disabled="isPublishing">
          Cancel
        </v-btn>

        <v-btn
          :color="isEditMode ? 'yellow' : 'cyan'"
          variant="flat"
          @click="handlePublish"
          :loading="isPublishing"
          :disabled="!formData.name"
          class="action-button"
        >
          {{ submitButtonText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useMarketplaceStore } from '@/store/marketplace';
import { useWorkflowStore } from '@/store/workflow';
import { storeToRefs } from 'pinia';

const props = defineProps({
  modelValue: Boolean,
  existingItem: {
      type: Object,
      default: null
  }
});
const emit = defineEmits(['update:modelValue', 'published']);

const marketplaceStore = useMarketplaceStore();
const workflowStore = useWorkflowStore();
const { isPublishing } = storeToRefs(marketplaceStore);
const { currentPresetName } = storeToRefs(workflowStore);

const isSmartPackage = computed(() => !!props.existingItem && props.existingItem.source === 'smart_package');
const isEditMode = computed(() => !!props.existingItem && props.existingItem.source !== 'smart_package');

const dialogTitle = computed(() => {
    if (isEditMode.value) return 'Edit Marketplace Item';
    if (isSmartPackage.value) return `Publish ${props.existingItem.componentType || 'Item'}`;
    return 'Publish Workflow Preset';
});

const submitButtonText = computed(() => {
    if (isEditMode.value) return 'Update Item';
    if (isSmartPackage.value) return 'Publish Smart Package';
    return 'Publish Now';
});

const formData = ref({
  id: '',
  name: '',
  desc: '',
  price: 0,
  zip_data: null
});

watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    if (props.existingItem) {
        if (props.existingItem.source === 'smart_package') {
            const data = props.existingItem.data;
            formData.value = {
                id: '',
                name: data.name || data.id,
                desc: data.description || '',
                price: 0,
                zip_data: data.zip_data // The Base64 Zip
            };
        } else {
            formData.value = {
                id: props.existingItem.id,
                name: props.existingItem.name,
                desc: props.existingItem.desc || props.existingItem.description || '',
                price: props.existingItem.price || 0,
                zip_data: null
            };
        }
    } else {
        formData.value = {
            id: '',
            name: currentPresetName.value || '',
            desc: '',
            price: 0,
            zip_data: null
        };
    }
  }
});

async function handlePublish() {
  formData.value.price = 0;
  let success = false;

  if (isSmartPackage.value) {
      const payload = {
          type: props.existingItem.componentType, // e.g., 'module'
          name: formData.value.name,
          description: formData.value.desc,
          price: 0,
          zip_file: formData.value.zip_data // Base64 content
      };
      success = await marketplaceStore.publishSmartPackage(payload);

  } else if (isEditMode.value) {
      const payload = {
          id: formData.value.id,
          type: props.existingItem.type || 'preset',
          name: formData.value.name,
          desc: formData.value.desc,
          price: 0,
          data: props.existingItem.data
      };
      success = await marketplaceStore.publishComponent(payload);

  } else {
      success = await marketplaceStore.publishCurrentWorkflow(formData.value);
  }

  if (success) {
    emit('update:modelValue', false);
    emit('published');
  }
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

.hacker-input :deep(.v-field) {
    background-color: rgba(42, 42, 74, 0.7) !important;
    color: var(--text-primary) !important;
}
.hacker-input :deep(.v-field__outline) {
    border-color: rgba(100, 255, 218, 0.3) !important;
}
.hacker-input :deep(.v-field--active .v-field__outline) {
    border-color: var(--neon-cyan) !important;
    border-width: 1px !important;
}
.hacker-input :deep(input),
.hacker-input :deep(textarea) {
    color: var(--text-primary) !important;
}
.hacker-input :deep(.v-label) {
    color: var(--text-secondary) !important;
    opacity: 1 !important;
}
.hacker-input :deep(.v-field--active .v-label) {
    color: var(--neon-cyan) !important;
}
.border-success {
    border-color: #4caf50 !important;
}
</style>
