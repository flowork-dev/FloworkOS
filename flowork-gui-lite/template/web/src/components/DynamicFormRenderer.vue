//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\DynamicFormRenderer.vue total lines 340 
//#######################################################################

<template>
  <div class="dynamic-form-renderer">
    <div v-for="field in schema" :key="field.id" class="mb-4 form-field-anim">

      <div v-if="field.component === 'header'" class="settings-header mt-6 mb-2">
        <v-divider class="mb-3 border-opacity-25" color="cyan"></v-divider>
        <div class="d-flex align-center text-cyan-accent-3">
          <v-icon icon="mdi-tune" size="small" start class="mr-2"></v-icon>
          <h3 class="text-subtitle-2 text-uppercase font-weight-bold" style="letter-spacing: 1.5px;">
            {{ field.label }}
          </h3>
        </div>
      </div>

      <div v-else-if="field.component === 'ai_provider_select'">
        <div class="field-label">{{ field.label }} <span v-if="field.required" class="text-red">*</span></div>
        <v-autocomplete
          v-model="modelValue[field.id]"
          :items="aiProviders"
          item-title="name"
          item-value="id"
          :placeholder="field.placeholder || 'Select AI Model'"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
          prepend-inner-icon="mdi-brain"
          clearable
        >
            <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" :subtitle="item.raw.id" class="text-caption"></v-list-item>
            </template>
        </v-autocomplete>
      </div>

      <div v-else-if="field.component === 'prompt_selector'">
        <div class="field-label">{{ field.label }}</div>
        <v-combobox
          v-model="modelValue[field.id]"
          :items="prompts"
          item-title="title"
          :placeholder="field.placeholder || 'Select Prompt Template OR type variable path'"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
          prepend-inner-icon="mdi-text-box-search-outline"
          clearable
        >
            <template v-slot:selection="{ item }">
                <span class="text-truncate text-caption font-weight-bold text-white">
                    {{ (typeof item.raw === 'object' ? item.raw.title : item.raw) || item.title }}
                </span>
            </template>

            <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" :title="item.raw.title" class="prompt-list-item">
                    <template v-slot:subtitle>
                        <div class="text-caption text-grey-darken-1 text-truncate">
                            {{ item.raw.content ? item.raw.content.substring(0, 60) + '...' : 'No content' }}
                        </div>
                    </template>
                </v-list-item>
            </template>
        </v-combobox>
        <div class="text-caption text-grey mt-1 ml-1" style="font-size: 10px;">
            Select a saved template OR type a variable path (e.g. <code>data.prompt</code>).
        </div>
      </div>

      <div v-else-if="field.component === 'folder_picker' || field.type === 'folderpath'">
        <div class="field-label">{{ field.label }} <span v-if="field.required" class="text-red">*</span></div>
        <v-text-field
          v-model="modelValue[field.id]"
          :placeholder="field.placeholder || '/path/to/folder'"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
          prepend-inner-icon="mdi-folder-outline"
        >
          <template #append-inner>
            <v-icon @click="openGlobalFileBrowser(field.id, 'folder')" color="cyan" class="cursor-pointer">
              mdi-folder-search
            </v-icon>
          </template>
        </v-text-field>
      </div>

      <div v-else-if="field.component === 'file_picker' || field.type === 'file' || field.type === 'filepath'">
        <div class="field-label">{{ field.label }} <span v-if="field.required" class="text-red">*</span></div>
        <v-text-field
          v-model="modelValue[field.id]"
          :placeholder="field.placeholder || '/path/to/file.ext'"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
          prepend-inner-icon="mdi-file-video-outline"
        >
          <template #append-inner>
            <v-icon @click="openGlobalFileBrowser(field.id, 'file')" color="cyan" class="cursor-pointer">
              mdi-file-search
            </v-icon>
          </template>
        </v-text-field>
      </div>

      <div v-else-if="field.component === 'select' || field.type === 'select' || field.type === 'enum'">
        <div class="field-label">{{ field.label }}</div>
        <v-select
          v-model="modelValue[field.id]"
          :items="field.options"
          item-title="label"
          item-value="value"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
          menu-icon="mdi-chevron-down"
        ></v-select>
      </div>

      <div v-else-if="field.type === 'text' || field.type === 'string'">
        <div class="field-label">{{ field.label }} <span v-if="field.required" class="text-red">*</span></div>

        <v-text-field
          v-if="field.component === 'color_picker'"
          v-model="modelValue[field.id]"
          :placeholder="field.placeholder"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
        >
          <template #append>
            <div :style="{ backgroundColor: modelValue[field.id], width: '24px', height: '24px', borderRadius: '4px', border: '1px solid #555' }"></div>
          </template>
        </v-text-field>

        <v-text-field
          v-else
          v-model="modelValue[field.id]"
          :placeholder="field.placeholder"
          :prepend-inner-icon="field.icon || 'mdi-pencil'"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
        ></v-text-field>
      </div>

      <div v-else-if="field.type === 'number' || field.type === 'integer'">
        <div class="field-label">{{ field.label }}</div>
        <v-text-field
          v-model.number="modelValue[field.id]"
          type="number"
          :prepend-inner-icon="field.icon || 'mdi-numeric'"
          variant="outlined"
          density="compact"
          hide-details="auto"
          class="hacker-input"
        ></v-text-field>
      </div>

      <div v-else-if="field.type === 'toggle' || field.type === 'boolean'">
        <v-switch
          v-model="modelValue[field.id]"
          :label="field.label"
          color="cyan"
          inset
          hide-details
          class="mt-2"
        ></v-switch>
      </div>

      <div v-else-if="field.type === 'list'">
        <div class="field-label mb-1" v-if="field.component !== 'FolderPairList'">{{ field.label }}</div>
        <FolderPairList
          v-model="modelValue[field.id]"
          :label="field.label"
          :hint="field.description"
          :left-label="field.left_label"
          :right-label="field.right_label"
        />
      </div>

      <div v-else-if="field.type === 'textarea'">
        <div class="field-label">{{ field.label }}</div>
        <v-textarea
          v-model="modelValue[field.id]"
          variant="outlined"
          rows="3"
          density="compact"
          class="hacker-input"
        ></v-textarea>
      </div>

      <div v-else-if="field.type === 'code'">
        <div class="field-label">{{ field.label }}</div>
        <v-textarea
          v-model="modelValue[field.id]"
          variant="outlined"
          rows="10"
          density="compact"
          class="hacker-input font-mono"
        ></v-textarea>
      </div>

      <div v-else class="text-caption text-red border-thin pa-2">
        [Unknown Field Type: {{ field.type }}]
      </div>

      <div v-if="field.description && field.component !== 'header'" class="text-caption text-grey mt-1 ml-1">
        {{ field.description }}
      </div>
    </div>

    <FileBrowserModal
        v-model="isGlobalBrowserOpen"
        :initial-path="globalBrowserPath"
        :selection-mode="globalBrowserMode"
        @select="onGlobalFileSelected"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import FolderPairList from '@/components/custom-properties/FolderPairList.vue';
import FileBrowserModal from '@/components/custom-properties/FileBrowserModal.vue';

const props = defineProps({
  schema: { type: Array, required: true, default: () => [] },
  modelValue: { type: Object, required: true, default: () => ({}) },
  aiProviders: { type: Array, default: () => [] },
  prompts: { type: Array, default: () => [] }
});

const emit = defineEmits(['update:modelValue']);

const isGlobalBrowserOpen = ref(false);
const globalBrowserTargetId = ref(null);
const globalBrowserPath = ref('');
const globalBrowserMode = ref('folder');

function openGlobalFileBrowser(fieldId, mode = 'folder') {
  globalBrowserTargetId.value = fieldId;
  globalBrowserMode.value = mode;
  globalBrowserPath.value = props.modelValue[fieldId] || '';
  isGlobalBrowserOpen.value = true;
}

function onGlobalFileSelected(path) {
  if (globalBrowserTargetId.value) {
    const newData = { ...props.modelValue };
    newData[globalBrowserTargetId.value] = path;
    emit('update:modelValue', newData);
  }
  isGlobalBrowserOpen.value = false;
}

onMounted(() => {
  const initialData = { ...props.modelValue };
  let hasChanges = false;

  props.schema.forEach(field => {
    if (field.component === 'header') return;
    if (initialData[field.id] === undefined && field.default !== undefined) {
      initialData[field.id] = field.default;
      hasChanges = true;
    }
    if (field.type === 'list' && !Array.isArray(initialData[field.id])) {
        initialData[field.id] = [];
        hasChanges = true;
    }
  });

  if (hasChanges) {
    emit('update:modelValue', initialData);
  }
});
</script>

<style scoped>
.field-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-family: 'Orbitron', monospace;
}

.font-mono :deep(textarea) {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.85rem;
}

.hacker-input :deep(.v-field) {
  background-color: rgba(30, 30, 45, 0.6) !important;
  border-radius: 8px;
  color: #fff !important;
  transition: all 0.3s ease;
}

.hacker-input :deep(.v-field__outline) {
  --v-field-border-opacity: 0.3;
  border-color: var(--neon-cyan) !important;
}

.hacker-input :deep(.v-field--focused) {
  box-shadow: 0 0 10px rgba(0, 245, 255, 0.2);
}

.hacker-input :deep(.v-field--focused .v-field__outline) {
  --v-field-border-opacity: 1;
  border-color: var(--neon-cyan) !important;
}

.form-field-anim {
  animation: slideIn 0.3s ease-out forwards;
  opacity: 0;
}

.prompt-list-item {
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

@keyframes slideIn {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
