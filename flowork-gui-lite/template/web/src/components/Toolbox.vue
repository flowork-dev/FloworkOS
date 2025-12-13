//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\Toolbox.vue total lines 384 
//#######################################################################

<template>
  <div class="toolbox-container">
    <div class="pa-2 search-bar-container">
      <div class="d-flex align-center gap-2">
         <v-text-field
          v-model="searchTerm"
          :label="loc('toolbox_search_placeholder')"
          prepend-inner-icon="mdi-magnify"
          variant="solo-filled"
          density="compact"
          hide-details
          clearable
          class="search-field flex-grow-1"
        ></v-text-field>

        <input
            type="file"
            ref="folderInput"
            webkitdirectory
            directory
            style="display: none"
            @change="handleFolderSelect"
        />

        <v-btn
          icon="mdi-refresh"
          variant="text"
          density="comfortable"
          color="cyan"
          :loading="isLoading"
          @click="forceRefresh"
          title="Force Refresh Components"
        ></v-btn>
      </div>
    </div>

    <v-tabs v-model="activeTab" grow background-color="transparent" class="tabs-header">
      <v-tab v-for="tab in tabs" :key="tab.value" :value="tab.value" class="tab-title">
        <v-icon :icon="tab.icon" size="small" start></v-icon>
        {{ loc(tab.titleKey) }}
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab" class="toolbox-window">
      <v-window-item
        v-for="tab in tabs"
        :key="tab.value"
        :value="tab.value"
        class="fill-height"
      >
        <ComponentList
          :type="tab.value"
          :search-term="searchTerm"
          @item-click="handleItemClick"
          @upload-request="triggerItemUpload"
        />
      </v-window-item>
    </v-window>

    <div v-if="isLoading && !hasAnyItems" class="loading-overlay">
      <v-progress-circular indeterminate color="cyan"></v-progress-circular>
      <p class="mt-2 text-caption text-grey">{{ loc('toolbox_loading') }}</p>
    </div>

    <div v-else-if="error && !hasAnyItems" class="loading-overlay error-state">
      <v-icon icon="mdi-wifi-off" color="error" size="x-large"></v-icon>
      <p class="mt-2 text-error">{{ loc('toolbox_error_load') }}</p>
      <p class="text-caption text-grey">{{ loc('toolbox_error_check_connection') }}</p>
      <v-btn size="small" color="cyan" variant="tonal" class="mt-2" @click="forceRefresh">Retry</v-btn>
    </div>

    <v-dialog v-model="showPublishDialog" max-width="500px" persistent>
        <v-card class="publish-card">
            <v-card-title class="orbitron-font text-green-accent-3">
                <v-icon start>mdi-package-variant-closed</v-icon> Publish {{ pendingPackage?.manifest?.name }}
            </v-card-title>
            <v-card-text>
                <p class="text-grey-lighten-1 mb-3">
                   You are about to update/publish this component to the Marketplace.
                </p>

                <v-list density="compact" class="bg-transparent border rounded">
                    <v-list-item>
                        <template v-slot:prepend><v-icon color="cyan">mdi-file-code</v-icon></template>
                        <v-list-item-title>Files Packed</v-list-item-title>
                        <template v-slot:append><span class="text-cyan">{{ Object.keys(pendingPackage?.files || {}).length }}</span></template>
                    </v-list-item>
                     <v-list-item>
                        <template v-slot:prepend><v-icon color="yellow">mdi-tag-text</v-icon></template>
                        <v-list-item-title>Version</v-list-item-title>
                        <template v-slot:append><span class="text-yellow">{{ pendingPackage?.manifest?.version || '0.0.0' }}</span></template>
                    </v-list-item>
                </v-list>

                <v-alert v-if="!pendingPackage.manifest?.name" type="warning" density="compact" variant="tonal" class="mt-3">
                    Missing <code>manifest.json</code>! Please ensure you selected the correct folder.
                </v-alert>

            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn variant="text" @click="showPublishDialog = false">Cancel</v-btn>
                <v-btn
                    color="green-accent-3"
                    variant="flat"
                    :loading="isPublishing"
                    :disabled="!pendingPackage.manifest?.name"
                    @click="confirmPublish"
                    class="font-weight-bold text-black"
                >
                    Publish
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useComponentStore } from '@/store/components';
import { useLocaleStore } from '@/store/locale';
import { useMarketplaceStore } from '@/store/marketplace';
import { storeToRefs } from 'pinia';
import ComponentList from './ComponentList.vue';
import { useUiStore } from '@/store/ui';
import { useSocketStore } from '@/store/socket';

const componentStore = useComponentStore();
const localeStore = useLocaleStore();
const uiStore = useUiStore();
const socketStore = useSocketStore();
const marketplaceStore = useMarketplaceStore();

const { loc } = storeToRefs(localeStore);
const { isPublishing } = storeToRefs(marketplaceStore);

const isLoading = computed(() => componentStore[activeTab.value]?.isLoading ?? false);

const hasAnyItems = computed(() => {
    return componentStore.modules.items.length > 0 ||
           componentStore.plugins.items.length > 0 ||
           componentStore.triggers.items.length > 0;
});
const error = computed(() => componentStore.error);

const activeTab = ref('modules');
const searchTerm = ref('');
const folderInput = ref(null);
const showPublishDialog = ref(false);
const pendingPackage = ref({});
const targetItemForUpload = ref(null);

const tabs = ref([
    { titleKey: 'toolbox_tab_modules', value: 'modules', icon: 'mdi-cog-outline' },
    { titleKey: 'toolbox_tab_plugins', value: 'plugins', icon: 'mdi-power-plug-outline' },
    { titleKey: 'toolbox_tab_triggers', value: 'triggers', icon: 'mdi-flash' }
]);

onMounted(() => {
    componentStore.fetchAllComponents();
});

watch(() => socketStore.isConnected, (connected) => {
    if (connected) {
        componentStore.forceRefetchAllComponents();
    }
});


function forceRefresh() {
    uiStore.showNotification({ text: "Refreshing toolbox...", color: "info" });
    componentStore.forceRefetchAllComponents();
}

function handleItemClick(item) {
    if (!socketStore.isConnected) {
        uiStore.showConnectEngineDialog();
        return;
    }
    uiStore.showStandaloneRunner(item);
}


function triggerItemUpload(item) {
    targetItemForUpload.value = item;
    uiStore.showNotification({ text: `Please select the '${item.id}' folder to upload...`, color: 'info' });
    folderInput.value.click();
}

async function handleFolderSelect(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    console.log(`[SmartPackager] Processing ${files.length} files...`);

    const packageData = {
        manifest: {},
        files: {},
        type: activeTab.value.slice(0, -1)
    };

    const IGNORED_NAMES = [
        'node_modules', 'venv', '.git', '__pycache__', '.env', 'dist', 'build', 'coverage',
        '.DS_Store', 'Thumbs.db', '.idea', '.vscode'
    ];

    for (const file of files) {
        const path = file.webkitRelativePath;

        const pathParts = path.split('/');
        const hasIgnoredPart = pathParts.some(part => IGNORED_NAMES.includes(part));

        if (hasIgnoredPart) {
            continue;
        }

        try {
            const isBinary = /\.(png|jpg|jpeg|gif|webp|ico|pdf|zip|exe|dll|so)$/i.test(file.name);

            let content;
            if (isBinary) {
                 content = await readFileAsBase64(file);
            } else {
                 content = await file.text();
            }

            if (file.name === 'manifest.json') {
                try {
                    const manifest = JSON.parse(content);
                    packageData.manifest = manifest;
                } catch(e) {
                    console.error("Invalid manifest JSON");
                }
            }

            packageData.files[path] = content;

        } catch (e) {
            console.warn(`Failed to read file ${path}:`, e);
        }
    }

    if (targetItemForUpload.value) {
        if (packageData.manifest?.id !== targetItemForUpload.value.id) {
            uiStore.showNotification({
                text: `Mismatch! You selected '${packageData.manifest?.id || 'unknown'}' but clicked upload on '${targetItemForUpload.value.id}'.`,
                color: "warning",
                timeout: 6000
            });
        }
    }

    pendingPackage.value = packageData;
    showPublishDialog.value = true;

    event.target.value = ''; // Reset input
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

async function confirmPublish() {
    if (!pendingPackage.value.manifest?.name) {
        uiStore.showNotification({ text: "Cannot publish without a valid manifest.json", color: "error" });
        return;
    }

    const payload = {
        type: pendingPackage.value.type,
        name: pendingPackage.value.manifest.name,
        desc: pendingPackage.value.manifest.description || "No description",
        price: 0,
        data: pendingPackage.value,
        id: pendingPackage.value.manifest.id
    };

    const success = await marketplaceStore.publishComponent(payload);
    if (success) {
        showPublishDialog.value = false;
        pendingPackage.value = {};
        targetItemForUpload.value = null;
    }
}
</script>

<style scoped>
.toolbox-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: transparent;
  color: var(--text-primary);
  padding-top: 60px !important; /* FIX HEADER OVERLAP */
}

.search-bar-container, .tabs-header {
  flex-shrink: 0;
}
.search-bar-container {
  padding: 12px !important;
}
.search-field :deep(.v-field) {
  background-color: var(--surface) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
.search-field :deep(.v-field__outline) {
  border: none !important;
}
.tabs-header {
  border-bottom: 1px solid var(--border-glow-soft);
}
.tab-title {
  font-size: 0.75rem !important;
}
.v-tab {
  font-weight: bold;
  letter-spacing: 1px;
  color: var(--text-secondary) !important;
  transition: color 0.3s ease;
}
.v-tab--selected {
  color: var(--neon-cyan) !important;
}
.toolbox-window {
  flex-grow: 1;
  overflow-y: hidden;
  min-height: 0;
  position: relative;
  padding: 8px 0;
  height: 100%;
}
.toolbox-window .v-window-item {
    height: 100%;
    overflow-y: auto;
}
.toolbox-window .v-window-item {
  scrollbar-width: thin;
  scrollbar-color: #4F4F4F var(--bg-dark);
}
.toolbox-window .v-window-item::-webkit-scrollbar {
  width: 8px;
}
.toolbox-window .v-window-item::-webkit-scrollbar-track {
  background: var(--bg-dark);
}
.toolbox-window .v-window-item::-webkit-scrollbar-thumb {
  background-color: #4F4F4F;
  border-radius: 10px;
  border: 2px solid var(--bg-dark);
}
.loading-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    background-color: rgba(26, 26, 46, 0.8);
    z-index: 10;
}
.error-state {
    text-align: center;
    padding: 16px;
}
.gap-2 {
    gap: 8px;
}
.publish-card {
    background-color: #1E1E2E;
    border: 1px solid #00E676;
}
</style>
