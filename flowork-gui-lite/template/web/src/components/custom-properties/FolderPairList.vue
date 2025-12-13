//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\custom-properties\FolderPairList.vue total lines 244 
//#######################################################################

<template>
  <div class="folder-pair-list">
    <div class="list-header">
      <label class="v-label text-caption">{{ label }}</label>
      <v-btn @click="addPair" size="x-small" color="cyan" variant="tonal" prepend-icon="mdi-plus-circle">
        Add Layer
      </v-btn>
    </div>

    <div class="pairs-container">
      <div v-if="localPairs.length === 0" class="empty-list text-center text-caption text-grey pa-4">
        No items defined. Click 'Add Layer' to start.
      </div>

      <div v-for="(pair, index) in localPairs" :key="index" class="pair-item-wrapper">
        <v-card variant="outlined" class="mb-2 pair-card" :class="{ 'active-card': activeIndex === index }">
          <div class="d-flex align-center pa-2">
            <div class="pair-inputs flex-grow-1">

              <template v-if="isStitcherMode">

                <div class="d-flex gap-2 mb-1">
                   <v-text-field
                    v-model="pair.video_folder"
                    @update:modelValue="updatePair(index, 'video_folder', $event)"
                    :label="leftLabel || 'Primary Input'"
                    variant="outlined" density="compact" hide-details class="flex-grow-1"
                    prepend-inner-icon="mdi-folder-open"
                  >
                    <template #append-inner>
                      <v-icon @click="openFileBrowser(index, 'video_folder')" color="cyan" class="cursor-pointer">mdi-folder-search</v-icon>
                    </template>
                  </v-text-field>

                  <v-text-field
                    v-model="pair.audio_folder"
                    @update:modelValue="updatePair(index, 'audio_folder', $event)"
                    :label="rightLabel || 'Secondary Input'"
                    variant="outlined" density="compact" hide-details class="flex-grow-1"
                    prepend-inner-icon="mdi-folder-text-outline"
                  >
                    <template #append-inner>
                      <v-icon @click="openFileBrowser(index, 'audio_folder')" color="cyan" class="cursor-pointer">mdi-folder-search</v-icon>
                    </template>
                  </v-text-field>
                </div>

                <div class="d-flex gap-2 mb-3 px-1">
                    <div class="flex-grow-1 text-caption font-weight-bold d-flex align-center" style="color: #FFD700; width: 50%;">
                        <v-icon v-if="leftHint" size="x-small" color="#FFD700" class="mr-1">mdi-information-outline</v-icon>
                        {{ leftHint }}
                    </div>
                    <div class="flex-grow-1 text-caption font-weight-bold d-flex align-center" style="color: #FFD700; width: 50%;">
                        <v-icon v-if="rightHint" size="x-small" color="#FFD700" class="mr-1">mdi-information-outline</v-icon>
                        {{ rightHint }}
                    </div>
                </div>

                <v-text-field
                  v-model="pair.output_folder"
                  @update:modelValue="updatePair(index, 'output_folder', $event)"
                  label="Output Destination"
                  variant="outlined" density="compact" hide-details prepend-inner-icon="mdi-folder-download"
                >
                  <template #append-inner>
                    <v-icon @click="openFileBrowser(index, 'output_folder')" color="cyan" class="cursor-pointer">mdi-folder-search</v-icon>
                  </template>
                </v-text-field>
              </template>

              <template v-else-if="isSequenceMode">
                <div class="d-flex gap-2">
                  <v-text-field
                    v-model="pair.folder_path"
                    @update:modelValue="updatePair(index, 'folder_path', $event)"
                    label="Source Folder"
                    placeholder="Select folder..."
                    variant="outlined" density="compact" hide-details class="flex-grow-1" prepend-inner-icon="mdi-folder-outline"
                  >
                    <template #append-inner>
                      <v-icon @click="openFileBrowser(index, 'folder_path')" color="cyan" class="cursor-pointer">mdi-folder-search-outline</v-icon>
                    </template>
                  </v-text-field>
                </div>
              </template>

              <template v-else>
                <div class="d-flex gap-2">
                  <v-text-field
                    v-model="pair.source"
                    @update:modelValue="updatePair(index, 'source', $event)"
                    :label="leftLabel || 'Source Folder'"
                    variant="outlined" density="compact" hide-details class="flex-grow-1"
                    prepend-inner-icon="mdi-folder-open"
                  >
                    <template #append-inner>
                      <v-icon @click="openFileBrowser(index, 'source')" color="cyan" class="cursor-pointer">mdi-folder-search-outline</v-icon>
                    </template>
                  </v-text-field>

                  <v-text-field
                    v-model="pair.output"
                    @update:modelValue="updatePair(index, 'output', $event)"
                    :label="rightLabel || 'Output Folder'"
                    variant="outlined" density="compact" hide-details class="flex-grow-1"
                    prepend-inner-icon="mdi-folder-download-outline"
                  >
                    <template #append-inner>
                      <v-icon @click="openFileBrowser(index, 'output')" color="cyan" class="cursor-pointer">mdi-folder-search-outline</v-icon>
                    </template>
                  </v-text-field>
                </div>
              </template>

            </div>
            <v-btn @click="removePair(index)" icon="mdi-trash-can-outline" size="small" variant="text" color="red" class="ml-2"></v-btn>
          </div>
        </v-card>
      </div>
    </div>

    <div class="v-messages__message text-caption mt-1 text-grey">{{ hint }}</div>

    <FileBrowserModal
        v-model="isModalOpen"
        :initial-path="initialModalPath"
        :selection-mode="currentSelectionMode"
        @select="onFolderSelected"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import FileBrowserModal from './FileBrowserModal.vue';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: String,
  hint: String,
  leftLabel: String,
  rightLabel: String,
  leftHint: String,
  rightHint: String
});

const emit = defineEmits(['update:modelValue']);
const localPairs = ref([]);
const isModalOpen = ref(false);
const initialModalPath = ref('');
const editingIndex = ref(null);
const editingKey = ref(null);
const activeIndex = ref(null);
const currentSelectionMode = ref('folder');

const isStitcherMode = computed(() => {
  return props.label && (
    (props.label.toLowerCase().includes('stitch') && !props.label.toLowerCase().includes('sequence')) ||
    props.label.toLowerCase().includes('job')
  );
});

const isSequenceMode = computed(() => {
  if (props.leftLabel || props.rightLabel) return false;
  return props.label && (
    props.label.toLowerCase().includes('sequence') ||
    props.label.toLowerCase().includes('storyboard')
  );
});

watch(() => props.modelValue, (newValue) => {
  localPairs.value = JSON.parse(JSON.stringify(newValue || []));
}, { deep: true, immediate: true });

function addPair() {
  const newPairs = [...localPairs.value];
  if (isStitcherMode.value) {
    newPairs.push({ video_folder: '', audio_folder: '', output_folder: '' });
  } else if (isSequenceMode.value) {
    newPairs.push({ folder_path: '' });
  } else {
    newPairs.push({ source: '', output: '' });
  }
  emit('update:modelValue', newPairs);
}

function removePair(index) {
  const newPairs = [...localPairs.value];
  newPairs.splice(index, 1);
  emit('update:modelValue', newPairs);
}

function updatePair(index, key, value) {
  const newPairs = [...localPairs.value];
  if (newPairs[index]) {
    newPairs[index][key] = value;
    localPairs.value = newPairs;
    emit('update:modelValue', newPairs);
  }
}

function openFileBrowser(index, key) {
    editingIndex.value = index;
    editingKey.value = key;
    initialModalPath.value = (localPairs.value[index] && localPairs.value[index][key]) ? localPairs.value[index][key] : '';

    const isAudioContext = props.label && (props.label.toLowerCase().includes('audio') || props.label.toLowerCase().includes('job'));

    if (isAudioContext) {
        if (key === 'video_folder' || key === 'audio_folder' || key === 'source') {
            currentSelectionMode.value = 'file'; // Minta File (Audio/Script)
        } else {
            currentSelectionMode.value = 'folder'; // Minta Output Folder
        }
    } else {
        currentSelectionMode.value = 'folder'; // Default Folder Mode (Stitcher)
    }

    isModalOpen.value = true;
}

function onFolderSelected(selectedPath) {
    if (editingIndex.value !== null && editingKey.value !== null) {
        updatePair(editingIndex.value, editingKey.value, selectedPath);
    }
    isModalOpen.value = false;
}
</script>

<style scoped>
.folder-pair-list { margin-bottom: 16px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.pair-card { border-color: rgba(255,255,255,0.1); background-color: rgba(255,255,255,0.02); transition: all 0.2s; }
.pair-card:hover { border-color: rgba(0, 229, 255, 0.5); background-color: rgba(0, 229, 255, 0.05); }
.gap-2 { gap: 8px; }
.cursor-pointer { cursor: pointer; opacity: 0.7; }
.cursor-pointer:hover { opacity: 1; }
</style>
