//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\custom-properties\FileBrowserModal.vue total lines 319 
//#######################################################################

<template>
  <v-dialog v-model="dialog" max-width="700px" @click:outside="close">
    <v-card class="browser-card">
      <v-card-title class="d-flex align-center py-3 px-4 card-header">
        <v-icon :icon="selectionMode === 'file' ? 'mdi-file-document-outline' : 'mdi-folder-open'" class="mr-2" color="cyan"></v-icon>

        <span class="text-subtitle-1 font-weight-bold text-truncate">
          {{ selectionMode === 'file' ? 'Select File' : 'Select Folder' }}
        </span>

        <v-spacer></v-spacer>

        <v-tooltip text="Go to Drives" location="bottom">
          <template v-slot:activator="{ props }">
            <v-btn v-bind="props" icon="mdi-harddisk" variant="text" size="small" color="cyan" @click="fetchFiles('')" class="mr-1"></v-btn>
          </template>
        </v-tooltip>

        <v-tooltip text="Show All Drives" location="bottom">
          <template v-slot:activator="{ props }">
            <v-btn v-bind="props" icon="mdi-server-network" variant="text" size="small" color="amber" @click="fetchFiles('')" class="mr-1"></v-btn>
          </template>
        </v-tooltip>

        <v-btn icon="mdi-close" variant="text" size="small" @click="close"></v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <div class="px-4 py-2 bg-grey-darken-4 d-flex align-center">
        <v-btn
            icon="mdi-arrow-up"
            variant="text"
            size="small"
            @click="goUp"
            :disabled="!currentPath && currentPath !== ''"
            class="mr-2"
            color="grey-lighten-1"
            title="Up one level"
        ></v-btn>

        <v-text-field
          v-model="currentPath"
          variant="outlined"
          density="compact"
          hide-details
          class="path-input"
          placeholder="Path..."
          prepend-inner-icon="mdi-folder"
          @keyup.enter="fetchFiles(currentPath)"
        ></v-text-field>
      </div>

      <v-card-text class="file-list-container pa-0">
        <div v-if="loading" class="d-flex flex-column align-center justify-center fill-height py-10">
          <v-progress-circular indeterminate color="cyan" size="48"></v-progress-circular>
          <div class="mt-3 text-caption text-grey">Opening folder...</div>
        </div>

        <div v-else-if="error" class="d-flex flex-column align-center justify-center fill-height py-10">
          <v-icon icon="mdi-lock-alert" color="error" size="48" class="mb-2"></v-icon>
          <div class="text-body-2 text-error mb-2 px-4 text-center">{{ error }}</div>
          <v-btn size="small" variant="outlined" color="amber" @click="fetchFiles('')">Show Available Drives</v-btn>
        </div>

        <div v-else-if="items.length === 0" class="d-flex flex-column align-center justify-center fill-height py-10">
          <v-icon icon="mdi-folder-open-outline" color="grey-darken-2" size="64" class="mb-2"></v-icon>
          <div class="text-caption text-grey">Folder is empty</div>
        </div>

        <v-list v-else density="compact" class="bg-transparent py-0">
          <v-list-item
            v-for="item in items"
            :key="item.path"
            :value="item"
            @click="handleItemClick(item)"
            class="file-item"
            :class="{ 'bg-cyan-darken-4': isSelected(item) }"
            :ripple="false"
          >
            <template v-slot:prepend>
              <v-icon v-if="item.type === 'drive'" icon="mdi-harddisk" color="amber" class="mr-2"></v-icon>
              <v-icon v-else-if="item.is_dir" icon="mdi-folder" color="cyan-lighten-3" class="mr-2"></v-icon>
              <v-icon v-else icon="mdi-file-document-outline" :color="isSelected(item) ? 'white' : 'grey'" class="mr-2"></v-icon>
            </template>

            <v-list-item-title class="text-body-2 font-weight-medium text-grey-lighten-1">{{ item.name }}</v-list-item-title>

            <template v-slot:append>
               <v-icon v-if="item.is_dir" icon="mdi-chevron-right" size="small" color="grey-darken-3"></v-icon>
               <v-icon v-if="isSelected(item)" icon="mdi-check" size="small" color="cyan-accent-2"></v-icon>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4 bg-grey-darken-4">
        <div class="text-caption text-grey text-truncate mr-4" style="max-width: 350px;">
          <span v-if="selectionMode === 'file' && selectedFilePath">Selected: <span class="text-cyan">{{ selectedFilePath }}</span></span>
          <span v-else-if="currentPath">Current: <span class="text-cyan">{{ currentPath }}</span></span>
        </div>
        <v-spacer></v-spacer>
        <v-btn variant="text" color="grey" @click="close">Cancel</v-btn>

        <v-btn
            color="cyan"
            variant="flat"
            @click="confirmSelection"
            :disabled="loading || (selectionMode === 'folder' && !currentPath) || (selectionMode === 'file' && !selectedFilePath)"
        >
            {{ selectionMode === 'file' ? 'Select File' : 'Select Folder' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useSocketStore } from '@/store/socket';

const props = defineProps({
  modelValue: Boolean,
  initialPath: { type: String, default: '' },
  selectionMode: { type: String, default: 'folder' } // Default folder
});

const emit = defineEmits(['update:modelValue', 'select']);
const socketStore = useSocketStore();
const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const DEFAULT_PATH = '';
const RESTRICTED_NAMES = ['FLOWORK', '.ENV', '.GIT', 'NODE_MODULES'];

const currentPath = ref(DEFAULT_PATH);
const items = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedFilePath = ref(null);
let timeoutId = null;

function fetchFiles(path) {
  if (!socketStore.isConnected) {
      error.value = "Engine Disconnected";
      return;
  }
  loading.value = true;
  error.value = null;
  items.value = [];
  selectedFilePath.value = null;

  console.log('[FileBrowser] Fetching:', path || 'DRIVE_LIST');
  socketStore.sendMessage({
    type: 'filesystem_list_request',
    path: path
  });

  if (timeoutId) clearTimeout(timeoutId);
  timeoutId = setTimeout(() => {
      if (loading.value) {
          loading.value = false;
          error.value = "Timeout. Engine busy.";
      }
  }, 8000);
}

function handleResponseEvent(event) {
    const payload = event.detail;
    const data = payload.payload || payload;

    if (data.error) {
        loading.value = false;
        if (currentPath.value !== '') {
             console.warn("Path error, fallback to drives");
             error.value = data.error;
        } else {
             error.value = data.error;
        }
        return;
    }

    currentPath.value = data.path || '';

    let rawItems = data.items || [];
    items.value = rawItems.filter(item => {
        const nameUpper = item.name.toUpperCase();
        if (RESTRICTED_NAMES.some(restricted => nameUpper.includes(restricted))) {
            return false;
        }
        return true;
    });

    loading.value = false;
    if (timeoutId) clearTimeout(timeoutId);
}

function handleItemClick(item) {
  if (item.is_dir) {
    if (item.type === 'drive') {
        fetchFiles(item.path);
    } else {
        let newPath = currentPath.value;
        if (newPath) {
            if (!newPath.endsWith('/') && !newPath.endsWith('\\')) newPath += '/';
        }
        newPath += item.name;

        const nameUpper = item.name.toUpperCase();
        if (RESTRICTED_NAMES.some(restricted => nameUpper.includes(restricted))) {
             error.value = "Access Denied: Protected Folder";
             return;
        }

        fetchFiles(newPath);
    }
  } else {
      if (props.selectionMode === 'file') {
          let fullPath = currentPath.value;
          if (fullPath && !fullPath.endsWith('/') && !fullPath.endsWith('\\')) fullPath += '/';
          fullPath += item.name;

          selectedFilePath.value = fullPath;
      }
  }
}

function isSelected(item) {
    if (props.selectionMode !== 'file') return false;
    if (item.is_dir) return false;

    let itemFullPath = currentPath.value;
    if (itemFullPath && !itemFullPath.endsWith('/') && !itemFullPath.endsWith('\\')) itemFullPath += '/';
    itemFullPath += item.name;

    return selectedFilePath.value === itemFullPath;
}

function goUp() {
  if (!currentPath.value) return;

  let path = currentPath.value.replace(/\\/g, '/'); // Normalisasi slash
  if (path.endsWith('/')) path = path.slice(0, -1); // Buang trailing slash

  if (path === '' || path === '/' || path === '/app') {
      fetchFiles('');
      return;
  }

  const lastSlash = path.lastIndexOf('/');
  if (lastSlash < 0) {
      fetchFiles('');
  } else {
      let parentPath = path.substring(0, lastSlash);
      if (parentPath === '') parentPath = '/';
      fetchFiles(parentPath);
  }
}

function confirmSelection() {
  if (props.selectionMode === 'file') {
      if (selectedFilePath.value) {
          emit('select', selectedFilePath.value);
          close();
      }
  } else {
      emit('select', currentPath.value);
      close();
  }
}

function close() {
  dialog.value = false;
  selectedFilePath.value = null; // Reset
}

onMounted(() => {
    window.addEventListener('FILESYSTEM_DATA_READY', handleResponseEvent);
    fetchFiles(DEFAULT_PATH);
});

onUnmounted(() => {
    window.removeEventListener('FILESYSTEM_DATA_READY', handleResponseEvent);
    if (timeoutId) clearTimeout(timeoutId);
});

watch(() => props.modelValue, (val) => {
    if (val) {
        error.value = null;
        selectedFilePath.value = null; // Reset seleksi pas buka baru

        fetchFiles(DEFAULT_PATH);
    }
});
</script>

<style scoped>
.browser-card { background-color: #1e1e2e; color: #e0e0e0; border: 1px solid #333; }
.card-header { background-color: #2a2a3c; border-bottom: 1px solid rgba(255,255,255,0.05); }
.path-input :deep(.v-field__input) { font-family: monospace; font-size: 0.85rem; }
.path-input :deep(.v-field) { background-color: #13131a; color: #fff; border: 1px solid #444; }
.file-list-container { height: 450px; overflow-y: auto; background-color: #13131a; }
.file-item { border-bottom: 1px solid rgba(255,255,255,0.03); transition: background 0.1s; min-height: 48px; }
.file-item:hover { background-color: rgba(0, 229, 255, 0.08); }
.bg-cyan-darken-4 { background-color: rgba(0, 188, 212, 0.2) !important; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #13131a; }
::-webkit-scrollbar-thumb { background-color: #444; border-radius: 4px; }
</style>
