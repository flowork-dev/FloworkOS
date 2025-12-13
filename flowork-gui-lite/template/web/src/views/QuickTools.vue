//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\QuickTools.vue total lines 1072 
//#######################################################################

<template>
  <div class="quick-tools-layout">
    <NeuralCanvasBackground />

    <div v-if="!selectedComponent" class="marketplace-view">
      <div class="marketplace-content scroll-y custom-scrollbar">

        <div class="d-flex flex-column align-center justify-center mb-10 mt-8">
          <h1 class="text-h2 font-weight-black text-white mb-2 orbitron-font text-center glow-text">
            SYSTEM <span class="text-yellow-accent-2">MODULES</span>
          </h1>
          <p class="text-grey-lighten-1 text-h6 font-weight-light mb-6 text-center" style="max-width: 600px;">
            Select a neural interface to begin configuration.
          </p>

          <div class="search-wrapper w-100" style="max-width: 700px;">
            <v-text-field
              v-model="searchTerm"
              placeholder="Search components..."
              prepend-inner-icon="mdi-magnify"
              variant="solo-filled"
              bg-color="rgba(20, 20, 30, 0.8)"
              class="rounded-xl search-input"
              hide-details
              clearable
            >
                <template v-slot:append-inner>
                    <v-tabs v-model="activeTab" density="compact" background-color="transparent" class="search-tabs">
                        <v-tab v-for="tab in tabs" :key="tab.value" :value="tab.value" class="text-caption text-white" color="yellow-accent-2">
                            {{ tab.title }}
                        </v-tab>
                    </v-tabs>
                </template>
            </v-text-field>
          </div>
        </div>

        <div class="bento-grid full-width-grid">
           <div
             v-for="item in filteredMarketplaceItems"
             :key="item.id || item.name"
             class="app-card"
             @click="handleToolClick(item)"
           >
              <div class="app-card-content">
                <div class="app-icon-wrapper">
                   <v-icon :icon="getCategoryIcon(activeTab)" color="white" size="32"></v-icon>
                </div>
                <div class="app-info">
                  <div class="d-flex justify-space-between align-start">
                    <div class="app-title text-truncate text-white">{{ item.name }}</div>
                    <v-chip size="x-small" color="yellow-accent-2" variant="tonal" class="ml-2 font-weight-bold">
                      v{{ item.version || '1.0' }}
                    </v-chip>
                  </div>
                  <div class="app-category text-caption text-grey mb-2">{{ activeTab.toUpperCase() }}</div>
                  <p class="app-desc text-caption text-grey-lighten-1 text-clamp-2">
                    {{ (item.manifest && item.manifest.description ? loc(item.manifest.description) : (item.description || 'System module ready for initialization.')) }}
                  </p>
                </div>
              </div>
              <div class="app-actions mt-4">
                 <v-btn
                    block
                    rounded="pill"
                    color="cyan-darken-3"
                    variant="flat"
                    class="font-weight-bold text-white action-btn"
                    height="36"
                 >
                    <v-icon start icon="mdi-power" size="small"></v-icon>
                    INITIALIZE
                 </v-btn>
              </div>
           </div>
        </div>

        <div v-if="filteredMarketplaceItems.length === 0" class="d-flex flex-column align-center justify-center text-grey py-16">
            <v-icon icon="mdi-cube-scan" size="80" class="mb-4 opacity-30"></v-icon>
            <div class="text-h5 text-grey-darken-1 font-mono">NO MODULES FOUND</div>
        </div>
      </div>
    </div>

    <div v-else class="workstation-view">

      <div class="workstation-grid">

        <div class="col-left">

            <v-card class="glass-panel border-thin pa-0 text-center position-relative overflow-hidden flex-shrink-0" style="height: 240px;">
                <div class="reactor-container d-flex align-center justify-center h-100 w-100" :class="{ 'reactor-active': isExecuting }">
                    <div class="reactor-ring ring-static"></div>
                    <div class="reactor-ring ring-outer-dashed"></div>
                    <div class="reactor-ring ring-middle-thin"></div>
                    <div class="reactor-ring ring-inner-orbit"></div>

                    <div class="reactor-core-glow"></div>
                    <div class="reactor-core-icon-wrapper">
                        <v-icon
                            :icon="isExecuting ? 'mdi-motion-sensor' : 'mdi-hexagon-slice-6'"
                            :color="isExecuting ? 'white' : 'yellow-accent-2'"
                            size="42"
                            class="reactor-icon-main"
                        ></v-icon>
                    </div>

                    <div class="reactor-scanline"></div>

                    <div class="reactor-status-wrapper">
                        <div class="reactor-status-indicator" :class="{ 'blink': isExecuting }"></div>
                        <div class="reactor-status-text font-mono text-yellow-accent-2">
                            {{ isExecuting ? (isSimulating ? 'SIMULATING DATA...' : 'PROCESSING...') : 'SYSTEM STANDBY' }}
                        </div>
                    </div>
                </div>
            </v-card>

            <v-card class="glass-panel border-thin flex-grow-1 d-flex flex-column overflow-hidden" style="min-height: 0;">
                <div class="panel-header-small px-3 py-2 border-bottom bg-grey-darken-4 d-flex align-center justify-space-between">
                    <span class="text-caption font-mono font-weight-bold text-yellow-accent-2 ml-1">AVAILABLE TOOLS</span>
                    <v-icon icon="mdi-toolbox-outline" size="small" color="grey"></v-icon>
                </div>

                <div class="toolbox-tabs border-bottom">
                    <v-tabs v-model="activeTab" density="compact" grow bg-color="transparent" slider-color="yellow-accent-2" height="40">
                        <v-tab v-for="tab in tabs" :key="tab.value" :value="tab.value" class="text-caption font-weight-bold text-white">
                            <v-icon start :icon="getCategoryIcon(tab.value)" size="x-small" class="mr-1"></v-icon>
                            {{ tab.title }}
                        </v-tab>
                    </v-tabs>
                </div>

                <div class="px-3 py-2 border-bottom">
                    <v-text-field
                      v-model="toolboxSearch"
                      placeholder="Filter list..."
                      prepend-inner-icon="mdi-filter-variant"
                      variant="outlined"
                      density="compact"
                      hide-details
                      bg-color="rgba(0,0,0,0.2)"
                      class="toolbox-search"
                    ></v-text-field>
                </div>

                <div class="panel-scroll-area custom-scrollbar pa-2">
                    <v-list density="compact" bg-color="transparent" class="component-list pa-2">
                        <div v-if="filteredFavorites.length > 0">
                            <v-list-subheader class="category-header favorites-header">
                                <v-icon size="x-small" class="mr-1" color="yellow-accent-2">mdi-star</v-icon>
                                FAVORITES
                            </v-list-subheader>
                            <v-list-item
                                v-for="item in filteredFavorites"
                                :key="item.id"
                                @dragstart="onDragStart($event, item)"
                                @click="handleToolClick(item)"
                                draggable="true"
                                class="toolbox-item mb-1 rounded"
                            >
                                <template v-slot:prepend>
                                    <v-icon :icon="getCategoryIcon(activeTab)" color="yellow-accent-2" size="small" class="mr-3"></v-icon>
                                </template>
                                <v-list-item-title class="text-caption font-weight-bold text-white">{{ loc(item.name) || item.name }}</v-list-item-title>
                                <template v-slot:append>
                                    <div class="d-flex align-center button-group">
                                        <v-btn
                                            v-if="item.is_installed"
                                            icon="mdi-star" variant="text" size="x-small" color="yellow-accent-2"
                                            @click.stop="componentStore.toggleFavorite(item.id)"
                                        ></v-btn>
                                        <v-btn
                                            v-else
                                            icon="mdi-download" variant="text" size="x-small" color="cyan"
                                            @click.stop="componentStore.installComponent(activeTab, item.id)"
                                        ></v-btn>
                                    </div>
                                </template>
                            </v-list-item>
                        </div>

                        <div v-for="(components, category) in groupedToolboxItems" :key="category">
                            <v-list-subheader class="category-header mt-2">{{ category }}</v-list-subheader>
                            <v-tooltip
                                v-for="item in components"
                                :key="item.id"
                                location="end"
                                content-class="ai-tooltip"
                                open-delay="500"
                            >
                                <template v-slot:activator="{ props }">
                                    <v-list-item
                                        v-bind="props"
                                        draggable="true"
                                        @dragstart="onDragStart($event, item)"
                                        @click="handleToolClick(item)"
                                        class="toolbox-item mb-1 rounded"
                                    >
                                        <template v-slot:prepend>
                                            <v-icon :icon="getCategoryIcon(activeTab)" color="white" size="small" class="mr-3 opacity-70"></v-icon>
                                        </template>

                                        <v-list-item-title class="text-caption text-white font-weight-medium">
                                            {{ loc(item.name) || item.name }}
                                        </v-list-item-title>

                                        <template v-slot:append>
                                            <div class="d-flex align-center button-group">
                                                <v-progress-circular
                                                    v-if="componentStore.installingComponentId === item.id || componentStore.uninstallingComponentId === item.id"
                                                    indeterminate size="16" width="2" color="yellow-accent-2" class="mr-2"
                                                ></v-progress-circular>
                                                <template v-else>
                                                    <v-btn
                                                        v-if="item.is_installed"
                                                        icon="mdi-delete-outline" variant="text" size="x-small" color="grey"
                                                        class="action-icon"
                                                        @click.stop="componentStore.uninstallComponent(activeTab, item.id)"
                                                    ></v-btn>
                                                    <v-btn
                                                        v-else
                                                        icon="mdi-download" variant="text" size="x-small" color="cyan"
                                                        class="action-icon"
                                                        @click.stop="componentStore.installComponent(activeTab, item.id)"
                                                    ></v-btn>
                                                    <v-btn
                                                        :icon="favoriteComponents.includes(item.id) ? 'mdi-star' : 'mdi-star-outline'"
                                                        variant="text"
                                                        size="x-small"
                                                        :color="favoriteComponents.includes(item.id) ? 'yellow-accent-2' : 'grey'"
                                                        class="action-icon ml-1"
                                                        @click.stop="componentStore.toggleFavorite(item.id)"
                                                    ></v-btn>
                                                </template>
                                            </div>
                                        </template>
                                    </v-list-item>
                                </template>
                                <div class="ai-tooltip-content">
                                    <div class="font-weight-bold mb-1 text-yellow-accent-2">{{ loc(item.name) || item.name }}</div>
                                    <div class="text-caption text-white">{{ loc(item.manifest?.description) || item.description }}</div>
                                    <v-divider class="my-2 border-dashed"></v-divider>
                                    <div class="text-caption font-mono" :class="item.is_installed ? 'text-green-accent-3' : 'text-grey'">
                                        {{ item.is_installed ? '>> INSTALLED' : '>> NOT INSTALLED' }}
                                    </div>
                                </div>
                            </v-tooltip>
                        </div>
                    </v-list>
                </div>
            </v-card>

        </div>

        <div class="col-center">
            <v-card class="center-panel-bg border-thin d-flex flex-column overflow-hidden fill-height position-relative">

                <div class="scanner-line"></div>
                <div class="scanner-overlay"></div>

                <div class="hacker-header-large d-flex position-relative" style="z-index: 5;">

                    <div class="header-left d-flex flex-column justify-space-between pa-5 position-relative">
                        <div class="header-info-container">
                            <div class="d-flex align-center mb-2" style="max-width: 100%;">
                                <v-btn
                                    icon="mdi-arrow-left"
                                    variant="outlined"
                                    density="comfortable"
                                    color="yellow-accent-2"
                                    class="mr-4 flex-shrink-0 hacker-btn-icon"
                                    @click="handleCloseModule"
                                    title="Back"
                                ></v-btn>
                                <v-icon icon="mdi-console-line" color="green-accent-3" class="mr-2 flex-shrink-0"></v-icon>
                                <div class="text-h5 font-mono font-weight-black text-white text-truncate module-title-anim" style="letter-spacing: 2px; min-width: 0;">
                                    [ {{ selectedComponent.name.toUpperCase() }} ]
                                </div>
                            </div>
                            <div class="text-caption font-mono text-cyan-darken-1 pl-12 text-truncate">
                                >> ID: {{ selectedComponent.id }}
                            </div>
                            <div class="text-caption text-grey-lighten-1 pl-12 mt-1 text-truncate" style="max-width: 400px;">
                                {{ selectedComponent.description }}
                            </div>
                        </div>

                        <div class="d-flex align-center pl-12 header-controls">
                            <v-chip v-if="jobStatus" :color="jobStatus.color" label class="font-mono font-weight-bold flex-shrink-0 mr-4 cyber-chip" variant="outlined">
                                <v-icon start :icon="jobStatus.icon" size="small"></v-icon> {{ jobStatus.text }}
                            </v-chip>
                            <v-chip v-else color="grey-darken-2" label variant="outlined" class="font-mono text-caption mr-4 cyber-chip-off">
                                STANDBY
                            </v-chip>

                            <v-menu location="bottom start" :close-on-content-click="false" content-class="cyber-menu">
                                <template v-slot:activator="{ props }">
                                    <v-btn
                                        v-bind="props"
                                        prepend-icon="mdi-floppy"
                                        variant="tonal"
                                        color="yellow-accent-2"
                                        size="small"
                                        class="font-weight-bold hacker-btn-small"
                                    >
                                        PRESETS
                                    </v-btn>
                                </template>
                                <v-card min-width="300" class="glass-panel border-neon bg-grey-darken-4 mt-2">
                                    <v-card-title class="text-caption font-weight-bold text-yellow-accent-2 border-bottom pa-3 font-mono">
                                        <v-icon start icon="mdi-memory" size="x-small"></v-icon>
                                        CONFIG_MEMORY
                                    </v-card-title>
                                    <v-card-text class="pa-3">
                                        <v-text-field
                                            v-model="newPresetName"
                                            label="New Config Name"
                                            variant="outlined"
                                            density="compact"
                                            hide-details
                                            class="mb-3 cyber-input-small"
                                            color="yellow-accent-2"
                                        >
                                            <template v-slot:append-inner>
                                                <v-btn icon="mdi-content-save" size="x-small" variant="text" color="green-accent-3" @click="savePreset"></v-btn>
                                            </template>
                                        </v-text-field>

                                        <div class="text-caption text-cyan-accent-2 mb-2 mt-1 font-mono">>> SAVED_DATA</div>

                                        <div class="preset-list-scroll custom-scrollbar">
                                            <v-list density="compact" bg-color="transparent" class="pa-0">
                                                <div v-if="savedPresets.length === 0" class="text-caption text-grey-darken-1 text-center py-2 font-italic font-mono">
                                                    [EMPTY_MEMORY]
                                                </div>
                                                <v-list-item
                                                    v-for="(preset, index) in savedPresets"
                                                    :key="index"
                                                    class="rounded mb-1 px-2 py-1 min-h-32 cyber-list-item"
                                                    @click="loadPreset(preset)"
                                                >
                                                    <template v-slot:prepend>
                                                        <v-icon icon="mdi-file-cog" size="x-small" color="cyan" class="mr-2"></v-icon>
                                                    </template>
                                                    <v-list-item-title class="text-caption font-mono text-white">{{ preset.name }}</v-list-item-title>
                                                    <template v-slot:append>
                                                        <v-btn icon="mdi-close" size="x-small" variant="text" color="red-darken-2" @click.stop="deletePreset(index)"></v-btn>
                                                    </template>
                                                </v-list-item>
                                            </v-list>
                                        </div>
                                    </v-card-text>
                                </v-card>
                            </v-menu>
                        </div>
                    </div>

                    <div class="header-right position-relative overflow-hidden d-flex align-center justify-center">
                        <div class="cyber-viz-wrapper">
                            <div class="perspective-grid"></div>

                            <div class="data-streams">
                                <div class="stream s1"></div>
                                <div class="stream s2"></div>
                                <div class="stream s3"></div>
                            </div>

                            <div class="holo-circle"></div>

                            <div class="viz-overlay-text text-right pa-3 font-mono text-caption text-green-accent-3">
                                <div>SYS.OP: ACTIVE</div>
                                <div>NET: SECURE</div>
                                <div class="blink">MONITORING...</div>
                            </div>
                        </div>
                    </div>

                </div>

                <div class="panel-scroll-area pa-6 custom-scrollbar position-relative" style="z-index: 2;">
                    <div v-if="injectionSchema.length > 0" class="cyber-form-inputs">
                       <DynamicFormRenderer
                          :schema="injectionSchema"
                          v-model="configValues"
                       />
                    </div>
                    <div v-else class="h-100 d-flex flex-column align-center justify-center text-grey opacity-50">
                        <v-icon icon="mdi-console-line" size="80" class="mb-6"></v-icon>
                        <div class="font-mono text-h6">NO CONFIGURATION REQUIRED</div>
                        <div class="font-mono text-caption mt-2">Ready for direct execution.</div>
                    </div>
                </div>
            </v-card>
        </div>

        <div class="col-right">

            <v-card class="glass-panel border-thin d-flex flex-column overflow-hidden" style="flex: 1; min-height: 0;">
                <div class="panel-header-small d-flex align-center px-4 py-2 border-bottom bg-grey-darken-4">
                    <v-icon icon="mdi-terminal" color="green-accent-3" size="small" class="mr-2"></v-icon>
                    <span class="text-caption font-mono font-weight-bold text-green-accent-3">SYSTEM OUTPUT</span>
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-delete-sweep" size="x-small" variant="text" color="grey" @click="logStore.clearLogs()"></v-btn>
                </div>
                <div class="log-content flex-grow-1 overflow-y-auto custom-scrollbar bg-black-transparent">
                    <LogPanelContent class="pa-2" />
                </div>
            </v-card>

            <v-card class="glass-panel border-thin d-flex flex-column pa-4 flex-shrink-0 bg-grey-darken-4" style="height: 240px;">
                <div class="text-caption font-mono text-grey mb-3 text-center">EXECUTION CONTROL</div>

                <div class="d-flex flex-column justify-center flex-grow-1 gap-3">
                    <v-btn
                      v-if="!isExecuting"
                      color="yellow-accent-2"
                      variant="flat"
                      class="hacker-btn-primary font-weight-black text-black"
                      block
                      size="large"
                      @click="handleExecute('EXECUTE')"
                      :loading="isRunning"
                      prepend-icon="mdi-play"
                    >
                        <span class="glitch-text">RUN SEQUENCE</span>
                    </v-btn>

                    <v-btn
                      v-else
                      color="red-accent-2"
                      variant="flat"
                      class="hacker-btn-danger font-weight-black text-black"
                      block
                      size="large"
                      @click="handleStop"
                      :loading="isStopping"
                      prepend-icon="mdi-stop"
                    >EMERGENCY STOP</v-btn>

                    <v-btn
                      variant="outlined"
                      @click="handleExecute('SIMULATE')"
                      :disabled="isExecuting"
                      :loading="isSimulating"
                      class="hacker-btn-outline font-mono"
                      block
                      prepend-icon="mdi-test-tube"
                      color="white"
                    >SIMULATE</v-btn>
                </div>
            </v-card>

        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useComponentStore } from '@/store/components';
import { useSocketStore } from '@/store/socket';
import { useLogStore } from '@/store/logs';
import { useLocaleStore } from '@/store/locale';
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';
import { v4 as uuidv4 } from 'uuid';
import LogPanelContent from '@/components/panels/LogPanelContent.vue';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';
import DynamicFormRenderer from '@/components/DynamicFormRenderer.vue';

const componentStore = useComponentStore();
const socketStore = useSocketStore();
const logStore = useLogStore();
const localeStore = useLocaleStore();
const uiStore = useUiStore();

const { loc } = storeToRefs(localeStore);
const { favoriteComponents } = storeToRefs(componentStore);

const activeTab = ref('modules');
const searchTerm = ref('');
const toolboxSearch = ref('');

const tabs = ref([
    { title: 'MODULES', value: 'modules' },
    { title: 'PLUGINS', value: 'plugins' },
    { title: 'TRIGGERS', value: 'triggers' },
]);

const selectedComponent = ref(null);
const configValues = ref({});

const currentJobId = ref(null);
const jobStatus = ref(null);
const isRunning = ref(false);
const isSimulating = ref(false);
const isStopping = ref(false);
const isExecuting = computed(() => isRunning.value || isSimulating.value);

const newPresetName = ref('');
const savedPresets = ref([]);
const STORAGE_PREFIX = 'fw_quick_preset_';

let offStatusListener = null;

const filteredMarketplaceItems = computed(() => {
  const currentTab = activeTab.value;
  let items = componentStore[currentTab]?.items || [];

  if (searchTerm.value) {
    const q = searchTerm.value.toLowerCase();
    items = items.filter(t =>
        (t.name && t.name.toLowerCase().includes(q)) ||
        (t.id && t.id.toLowerCase().includes(q)) ||
        (t.description && t.description.toLowerCase().includes(q))
    );
  }
  return items;
});

const toolboxItems = computed(() => {
    const currentTab = activeTab.value;
    let items = componentStore[currentTab]?.items || [];

    if (toolboxSearch.value) {
        const q = toolboxSearch.value.toLowerCase();
        items = items.filter(t =>
            (t.name && t.name.toLowerCase().includes(q)) ||
            (t.id && t.id.toLowerCase().includes(q))
        );
    }
    return items;
});

const filteredFavorites = computed(() => {
    return toolboxItems.value
        .filter(item => favoriteComponents.value.includes(item.id))
        .sort((a, b) => (a.name || '').localeCompare(b.name || ''));
});

const groupedToolboxItems = computed(() => {
  const nonFavoriteItems = toolboxItems.value.filter(item => !favoriteComponents.value.includes(item.id));
  const items = nonFavoriteItems || [];

  if (!items) return {};

  const grouped = items.reduce((groups, item) => {
    const category = item.manifest?.type?.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || 'General';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(item);
    return groups;
  }, {});

  const sortedCategories = Object.keys(grouped).sort();
  const sortedGrouped = {};
  sortedCategories.forEach(category => {
    sortedGrouped[category] = grouped[category].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  });
  return sortedGrouped;
});

const onDragStart = (event, item) => {
  if (event.dataTransfer) {
    if (!item.is_installed) {
        event.preventDefault();
        return;
    }
    const dataToTransfer = JSON.stringify({ ...item, componentType: activeTab.value });
    event.dataTransfer.setData('application/json', dataToTransfer);
    event.dataTransfer.effectAllowed = 'move';
  }
};

function getCategoryIcon(type) {
  if (type === 'modules') return 'mdi-cog-outline';
  if (type === 'plugins') return 'mdi-power-plug-outline';
  if (type === 'triggers') return 'mdi-flash';
  return 'mdi-cube-outline';
}

const injectionSchema = computed(() => {
  if (!selectedComponent.value || !selectedComponent.value.manifest) return [];

  if (selectedComponent.value.manifest.ui_schema) {
    return selectedComponent.value.manifest.ui_schema;
  }

  if (selectedComponent.value.manifest.properties) {
    return selectedComponent.value.manifest.properties.map(prop => ({
      id: prop.id,
      label: prop.label || prop.id,
      type: prop.type,
      default: prop.default,
      description: prop.description,
      options: prop.options
    }));
  }

  return [];
});

function handleToolClick(item) {
    if (!socketStore.isConnected) {
        socketStore.connect();
        uiStore.showNotification({ text: "Connecting to engine...", color: 'info' });
        return;
    }
    console.log("[QuickTools] Selected item:", item.name);
    selectedComponent.value = item;

    logStore.clearLogs();
    jobStatus.value = null;
    currentJobId.value = null;
    isRunning.value = false;
    isSimulating.value = false;
    configValues.value = {};
    toolboxSearch.value = '';

    loadPresetsFromStorage();
    const lastConfig = localStorage.getItem(`${STORAGE_PREFIX}${selectedComponent.value.id}_last`);
    if(lastConfig) {
        try {
            configValues.value = JSON.parse(lastConfig);
        } catch(e) { console.error("Error parsing last config", e); }
    }
}

function handleCloseModule() {
    selectedComponent.value = null;
    logStore.clearLogs();
}

async function handleExecute(mode) {
  if (!selectedComponent.value) return;

  localStorage.setItem(`${STORAGE_PREFIX}${selectedComponent.value.id}_last`, JSON.stringify(configValues.value));

  if (mode === 'EXECUTE') isRunning.value = true;
  if (mode === 'SIMULATE') isSimulating.value = true;

  logStore.clearLogs();
  const newJobId = `quickjob-${uuidv4()}`;
  currentJobId.value = newJobId;
  jobStatus.value = { text: 'Running...', color: 'info', icon: 'mdi-autorenew' };

  try {
    await socketStore.sendMessage({
      type: 'execute_standalone_node',
      job_id: newJobId,
      node_data: {
        module_id: selectedComponent.value.id,
        config_values: configValues.value
      },
      mode: mode
    });
  } catch (e) {
    uiStore.showNotification({ text: `Failed to start: ${e.message}`, color: 'error' });
    jobStatus.value = { text: 'Failed to Start', color: 'error', icon: 'mdi-alert-circle-outline' };
    isRunning.value = false;
    isSimulating.value = false;
  }
}

async function handleStop() {
    if (!currentJobId.value) return;
    isStopping.value = true;
    try {
        await socketStore.sendMessage({
            type: 'stop_workflow',
            job_id: currentJobId.value
        });
        uiStore.showNotification({ text: 'Stop signal sent.', color: 'warning' });
    } catch (e) {
        uiStore.showNotification({ text: `Failed to send stop signal: ${e.message}`, color: 'error' });
    } finally {
        isStopping.value = false;
    }
}

function loadPresetsFromStorage() {
    if(!selectedComponent.value) return;
    const key = `${STORAGE_PREFIX}${selectedComponent.value.id}_list`;
    const stored = localStorage.getItem(key);
    savedPresets.value = stored ? JSON.parse(stored) : [];
}

function savePreset() {
    if(!newPresetName.value.trim()) {
        uiStore.showNotification({ text: "Please enter a preset name", color: "warning" });
        return;
    }
    const preset = {
        name: newPresetName.value,
        data: { ...configValues.value }, // Clone data
        timestamp: Date.now()
    };
    savedPresets.value.push(preset);

    const key = `${STORAGE_PREFIX}${selectedComponent.value.id}_list`;
    localStorage.setItem(key, JSON.stringify(savedPresets.value));

    newPresetName.value = '';
    uiStore.showNotification({ text: "Preset saved locally", color: "success" });
}

function loadPreset(preset) {
    configValues.value = { ...preset.data };
    uiStore.showNotification({ text: `Loaded preset: ${preset.name}`, color: "info" });
}

function deletePreset(index) {
    savedPresets.value.splice(index, 1);
    const key = `${STORAGE_PREFIX}${selectedComponent.value.id}_list`;
    localStorage.setItem(key, JSON.stringify(savedPresets.value));
}

function setupStatusListener() {
    if (!socketStore.socket) return;
    const listener = (data) => {
        const payload = data.payload || data;
        if (payload.job_id === currentJobId.value) {
            const status = payload.status_data?.status;
            if (['SUCCEEDED', 'DONE', 'COMPLETED'].includes(status)) {
                jobStatus.value = { text: 'Succeeded', color: 'success', icon: 'mdi-check-circle-outline' };
                isRunning.value = false; isSimulating.value = false;
            } else if (['FAILED', 'ERROR'].includes(status)) {
                jobStatus.value = { text: 'Failed', color: 'error', icon: 'mdi-alert-circle-outline' };
                isRunning.value = false; isSimulating.value = false;
            } else if (['STOPPED', 'CANCELLED'].includes(status)) {
                jobStatus.value = { text: 'Stopped', color: 'warning', icon: 'mdi-stop-circle-outline' };
                isRunning.value = false; isSimulating.value = false;
            }
        }
    };
    socketStore.socket.on('WORKFLOW_EXECUTION_UPDATE', listener);
    return () => { if(socketStore.socket) socketStore.socket.off('WORKFLOW_EXECUTION_UPDATE', listener); };
}

watch(() => socketStore.isConnected, (connected) => {
    if (connected) {
        if (offStatusListener) offStatusListener();
        offStatusListener = setupStatusListener();
    }
});

onMounted(() => {
    if (!socketStore.isConnected && !socketStore.isConnecting) socketStore.connect();
    if (socketStore.isConnected) offStatusListener = setupStatusListener();
    if (componentStore.fetchAllComponents) componentStore.fetchAllComponents();
});

onUnmounted(() => {
    if (offStatusListener) offStatusListener();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&display=swap');

/* --- GLOBAL FIXED LAYOUT (NO PAGE SCROLL) --- */
.quick-tools-layout {
  position: fixed; top: 64px; left: 0; right: 0; bottom: 0;
  display: flex; background-color: var(--bg-dark); overflow: hidden; z-index: 5;
}
@media (max-width: 600px) { .quick-tools-layout { top: 56px; } }
.neural-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; opacity: 0.5; }

/* --- MARKETPLACE --- */
.marketplace-view { width: 100%; height: 100%; z-index: 1; display: flex; flex-direction: column; overflow: hidden; }
.marketplace-content { width: 100%; height: 100%; max-width: 100% !important; padding: 24px; overflow-y: auto; }
.full-width-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; width: 100%; padding-bottom: 60px; }

/* --- WORKSTATION FIXED LAYOUT --- */
.workstation-view { width: 100%; height: 100%; z-index: 2; background: rgba(10, 10, 15, 0.95); display: flex; flex-direction: column; padding: 16px; overflow: hidden; }
.workstation-grid { flex-grow: 1; display: flex; gap: 16px; overflow: hidden; height: 100%; }

/* COLUMN SETUP */
.col-left { width: 480px; display: flex; flex-direction: column; gap: 12px; flex-shrink: 0; overflow: hidden; height: 100%; }
.col-center { flex-grow: 1; display: flex; flex-direction: column; min-width: 0; overflow: hidden; height: 100%; }
.col-right { width: 400px; display: flex; flex-direction: column; gap: 12px; flex-shrink: 0; overflow: hidden; height: 100%; }

/* --- COMMON PANELS --- */
.glass-panel { background: rgba(20, 20, 25, 0.75) !important; backdrop-filter: blur(12px); border-radius: 12px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3); }

/* --- CENTER PANEL DISTINCT STYLE (FINAL TOUCH) --- */
.center-panel-bg {
    /* More distinct dark blue-grey background to separate from side glass */
    background: linear-gradient(135deg, rgba(15, 20, 25, 0.98) 0%, rgba(5, 8, 10, 1) 100%) !important;
    backdrop-filter: blur(20px);
    border-radius: 12px;
    /* Subtle Cyan Glow Border */
    border: 1px solid rgba(0, 255, 255, 0.15);
    box-shadow: 0 0 30px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 255, 255, 0.05);
    z-index: 10;
}

/* --- SCANNER EFFECT (NEW) --- */
.scanner-line {
    position: absolute; top: 0; left: 0; width: 100%; height: 5px;
    background: linear-gradient(to right, transparent, #00FFFF, transparent);
    box-shadow: 0 0 15px #00FFFF, 0 0 30px rgba(0, 255, 255, 0.5);
    opacity: 0.6; z-index: 1; pointer-events: none;
    animation: scan-vertical 4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}
.scanner-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(to bottom, rgba(0, 255, 255, 0.02) 0%, transparent 20%, transparent 100%);
    background-size: 100% 200%;
    animation: overlay-scroll 4s linear infinite; pointer-events: none; z-index: 0;
}
@keyframes scan-vertical {
    0% { top: -10%; opacity: 0; }
    10% { opacity: 0.8; }
    90% { opacity: 0.8; }
    100% { top: 110%; opacity: 0; }
}
@keyframes overlay-scroll { 0% { background-position: 0% 0%; } 100% { background-position: 0% 200%; } }

.border-thin { border: 1px solid rgba(255, 255, 255, 0.1); }
.border-bottom { border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.border-neon { border: 1px solid rgba(0, 255, 255, 0.3); box-shadow: 0 0 10px rgba(0, 255, 255, 0.1); }
.bg-grey-darken-4 { background-color: rgba(20, 20, 25, 0.95) !important; }
.bg-black-transparent { background-color: rgba(5, 5, 5, 0.5); }
.panel-scroll-area { flex-grow: 1; overflow-y: auto; min-height: 0; }

/* --- EXPANDED HACKER HEADER (BULLETPROOF) --- */
.hacker-header-large {
    background: linear-gradient(90deg, rgba(13, 17, 23, 0.95), rgba(10, 20, 30, 0.9));
    height: 220px;
    position: relative;
    border-bottom: 1px solid rgba(0, 255, 255, 0.2);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    flex-shrink: 0;
}

.header-left {
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    width: 60%;
    z-index: 2;
    min-width: 0;
    display: flex;
    flex-direction: column;
}

.header-info-container {
    flex-grow: 1;
    min-width: 0;
    overflow: hidden;
}

.header-controls {
    height: 50px;
}

.header-right {
    width: 40%;
    background: radial-gradient(circle at center, rgba(0, 50, 50, 0.3), transparent 80%);
    z-index: 1;
    overflow: hidden;
    border-top-right-radius: 12px;
}

/* FIX: Scrollable Preset List */
.preset-list-scroll { max-height: 200px; overflow-y: auto; }

/* --- CYBER ANIMATIONS & GLITCH EFFECTS --- */
.hacker-btn-primary {
    background: linear-gradient(45deg, #FFFF00, #FFD700);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
}
.hacker-btn-primary:hover {
    box-shadow: 0 0 20px rgba(255, 255, 0, 0.5);
    transform: translateY(-2px);
}
.hacker-btn-primary::after {
    content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.8), transparent);
    transform: rotate(45deg) translate(-100%, -100%);
    transition: transform 0s;
}
.hacker-btn-primary:hover::after {
    transition: transform 0.5s;
    transform: rotate(45deg) translate(100%, 100%);
}

.hacker-btn-danger { clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px); }
.hacker-btn-outline { border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(0,0,0,0.3); }
.hacker-btn-outline:hover { border-color: #00FFFF; color: #00FFFF !important; box-shadow: 0 0 10px rgba(0, 255, 255, 0.2); background: rgba(0, 255, 255, 0.05); }

/* Glitch Text Effect */
.glitch-text { position: relative; display: inline-block; }
.hacker-btn-primary:hover .glitch-text { animation: glitch-anim 0.3s infinite; }

@keyframes glitch-anim {
  0% { transform: translate(0) }
  20% { transform: translate(-2px, 2px) }
  40% { transform: translate(-2px, -2px) }
  60% { transform: translate(2px, 2px) }
  80% { transform: translate(2px, -2px) }
  100% { transform: translate(0) }
}

/* --- HACKER FORM INPUTS --- */
.cyber-form-inputs :deep(.v-field) {
    background-color: rgba(5, 10, 15, 0.6) !important;
    border: 1px solid rgba(0, 255, 255, 0.2);
    border-radius: 4px;
    transition: all 0.3s ease;
    color: #00FFFF !important;
    font-family: 'Fira Code', monospace;
    font-size: 0.85rem;
}
.cyber-form-inputs :deep(.v-field--focused) {
    border-color: #00FFFF !important;
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.2), inset 0 0 10px rgba(0, 255, 255, 0.1);
    animation: input-scan 2s infinite linear;
}
.cyber-form-inputs :deep(.v-label) {
    color: rgba(255, 255, 255, 0.7) !important;
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
}
.cyber-form-inputs :deep(.v-field--focused .v-label) {
    color: #FFFF00 !important;
    text-shadow: 0 0 5px #FFFF00;
}
@keyframes input-scan {
    0% { background-image: linear-gradient(0deg, transparent 95%, rgba(0, 255, 255, 0.2) 100%); background-size: 100% 20px; background-position: 0 0; }
    100% { background-position: 0 40px; }
}

/* --- CYBER SWITCHES & CHECKBOXES (NEW POLISH) --- */
.cyber-form-inputs :deep(.v-selection-control) { color: rgba(255, 255, 255, 0.7); }
.cyber-form-inputs :deep(.v-switch .v-selection-control__wrapper) { color: #00FFFF; }
.cyber-form-inputs :deep(.v-switch--inset .v-switch__track) {
    background-color: rgba(0, 0, 0, 0.6) !important;
    border: 1px solid rgba(0, 255, 255, 0.3);
    box-shadow: inset 0 0 5px rgba(0, 255, 255, 0.1); opacity: 1;
}
.cyber-form-inputs :deep(.v-switch.v-input--is-dirty .v-switch__track) {
    border-color: #00FF00; box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
}
.cyber-form-inputs :deep(.v-switch.v-input--is-dirty .v-selection-control__wrapper) {
    color: #00FF00; filter: drop-shadow(0 0 5px #00FF00);
}
.cyber-form-inputs :deep(.v-checkbox .v-icon) {
    color: rgba(0, 255, 255, 0.5); filter: drop-shadow(0 0 2px rgba(0,255,255,0.3));
}
.cyber-form-inputs :deep(.v-checkbox.v-input--is-dirty .v-icon) {
    color: #FFFF00 !important; filter: drop-shadow(0 0 5px #FFFF00);
}

/* --- CYBER DROPDOWNS (MENU) - SCOPED TO .cyber-menu --- */
/* FIX: Now specifically targets .cyber-menu to avoid breaking global header */
:global(.cyber-menu .v-list) {
    background-color: rgba(10, 15, 20, 0.95) !important;
    border: 1px solid #00FFFF;
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    font-family: 'Fira Code', monospace;
    padding: 0 !important;
}
:global(.cyber-menu .v-list-item) { color: #fff !important; }
:global(.cyber-menu .v-list-item:hover) { background-color: rgba(0, 255, 255, 0.15) !important; color: #FFFF00 !important; }
:global(.cyber-menu .v-list-item--active) { color: #FFFF00 !important; border-left: 3px solid #FFFF00; }

.cyber-menu .v-card {
    border: 1px solid #FFFF00 !important;
    box-shadow: 0 0 20px rgba(255, 255, 0, 0.2) !important;
}
.cyber-list-item:hover { background: rgba(255, 255, 0, 0.1); cursor: pointer; }

/* Chips */
.cyber-chip { border-color: #FFFF00 !important; color: #FFFF00 !important; box-shadow: 0 0 5px rgba(255, 255, 0, 0.2); }
.cyber-chip-off { border-color: rgba(255, 255, 255, 0.2) !important; opacity: 0.7; }

/* --- VIZ (UNCHANGED BUT ESSENTIAL) --- */
.cyber-viz-wrapper { width: 100%; height: 100%; position: relative; perspective: 500px; overflow: hidden; }
.perspective-grid {
    position: absolute; bottom: -50%; left: -50%; width: 200%; height: 100%;
    background-image: linear-gradient(rgba(0, 255, 255, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 255, 0.2) 1px, transparent 1px);
    background-size: 40px 40px; transform: rotateX(60deg); animation: grid-move 5s linear infinite; opacity: 0.3;
}
@keyframes grid-move { 0% { transform: rotateX(60deg) translateY(0); } 100% { transform: rotateX(60deg) translateY(40px); } }
.data-streams .stream { position: absolute; top: -100px; width: 2px; background: linear-gradient(to bottom, transparent, #00ff00, transparent); animation: stream-fall linear infinite; opacity: 0.6; }
.s1 { left: 20%; height: 100px; animation-duration: 3s; animation-delay: 0s; }
.s2 { left: 50%; height: 150px; animation-duration: 4s; animation-delay: 1s; }
.s3 { left: 80%; height: 80px; animation-duration: 2.5s; animation-delay: 2s; }
@keyframes stream-fall { 0% { top: -150px; opacity: 0; } 30% { opacity: 1; } 100% { top: 120%; opacity: 0; } }
.holo-circle {
    position: absolute; top: 50%; left: 50%; width: 100px; height: 100px; transform: translate(-50%, -50%);
    border: 2px dashed rgba(0, 255, 255, 0.3); border-radius: 50%; animation: spin-holo 10s linear infinite; box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
}
@keyframes spin-holo { 100% { transform: translate(-50%, -50%) rotate(360deg); } }
.viz-overlay-text { position: absolute; top: 10px; right: 10px; z-index: 10; font-size: 0.6rem; letter-spacing: 2px; text-shadow: 0 0 5px rgba(0, 255, 0, 0.8); }
.module-title-anim { animation: text-pulse 3s ease-in-out infinite; text-shadow: 0 0 5px rgba(255, 255, 255, 0.2); }
@keyframes text-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.8; text-shadow: 0 0 8px rgba(255, 255, 0, 0.4); } }

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: #333; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }

/* REACTOR (UNCHANGED) */
.reactor-container { position: relative; perspective: 1200px; overflow: hidden; background: radial-gradient(circle, rgba(255,255,0,0.02) 0%, rgba(0,0,0,0.3) 100%); }
.reactor-ring { position: absolute; border-radius: 50%; top: 50%; left: 50%; transform: translate(-50%, -50%); transition: all 0.5s ease-out; }
.ring-static { width: 190px; height: 190px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 0 20px rgba(0,0,0,0.5) inset; }
.ring-outer-dashed { width: 160px; height: 160px; border: 1px dashed rgba(255, 255, 0, 0.3); animation: rotate-slow 20s linear infinite; }
.ring-middle-thin { width: 125px; height: 125px; border-top: 2px solid rgba(255, 255, 255, 0.3); border-bottom: 2px solid rgba(255, 255, 255, 0.3); border-left: 2px solid transparent; border-right: 2px solid transparent; animation: rotate-rev-med 12s linear infinite; }
.ring-inner-orbit { width: 85px; height: 85px; border: 2px solid rgba(255, 255, 0, 0.5); border-left-color: transparent; border-right-color: transparent; box-shadow: 0 0 10px rgba(255, 255, 0, 0.2); animation: rotate-fast 8s linear infinite; }
.reactor-core-glow { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60px; height: 60px; border-radius: 50%; background: radial-gradient(circle, rgba(255,255,0,0.2) 0%, transparent 70%); filter: blur(10px); animation: pulse-idle 3s infinite ease-in-out; }
.reactor-core-icon-wrapper { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; }
.reactor-icon-main { transition: all 0.3s ease; filter: drop-shadow(0 0 5px rgba(255,255,0,0.5)); }
.reactor-scanline { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(to bottom, transparent 49%, rgba(255, 255, 0, 0.05) 50%, transparent 51%); background-size: 100% 8px; pointer-events: none; opacity: 0.3; }
.reactor-status-wrapper { position: absolute; bottom: 10px; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
.reactor-status-text { font-size: 0.75rem; letter-spacing: 3px; text-shadow: 0 0 5px rgba(255,255,0,0.5); font-weight: bold; }
.reactor-status-indicator { width: 6px; height: 6px; background-color: #FFFF00; border-radius: 50%; box-shadow: 0 0 8px #FFFF00; }
.blink { animation: blink-fast 0.5s infinite; background-color: #00FF00 !important; box-shadow: 0 0 10px #00FF00 !important; }
.reactor-active .ring-outer-dashed { border-color: rgba(255, 100, 0, 0.8); animation-duration: 4s; box-shadow: 0 0 20px rgba(255, 100, 0, 0.3); }
.reactor-active .ring-middle-thin { border-color: rgba(255, 255, 255, 0.9); animation-duration: 2s; }
.reactor-active .ring-inner-orbit { border-color: #00FF00; box-shadow: 0 0 20px #00FF00; width: 95px; height: 95px; animation-duration: 1s; }
.reactor-active .reactor-core-glow { background: radial-gradient(circle, rgba(0,255,0,0.5) 0%, transparent 70%); animation: pulse-active 0.8s infinite; width: 75px; height: 75px; }
.reactor-active .reactor-status-text { color: #00FF00 !important; text-shadow: 0 0 10px #00FF00; }
.reactor-active .reactor-icon-main { animation: shake-mild 0.2s infinite; color: #FFFFFF !important; filter: drop-shadow(0 0 15px #00FF00); }
@keyframes rotate-slow { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes rotate-rev-med { from { transform: translate(-50%, -50%) rotate(360deg); } to { transform: translate(-50%, -50%) rotate(0deg); } }
@keyframes rotate-fast { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes pulse-idle { 0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); } 50% { opacity: 0.8; transform: translate(-50%, -50%) scale(1.1); } }
@keyframes pulse-active { 0%, 100% { opacity: 0.8; transform: translate(-50%, -50%) scale(1); } 50% { opacity: 1; transform: translate(-50%, -50%) scale(1.3); } }
@keyframes blink-fast { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes shake-mild { 0% { transform: translate(1px, 1px) rotate(0deg); } 20% { transform: translate(-1px, 0px) rotate(1deg); } 40% { transform: translate(1px, -1px) rotate(-1deg); } 100% { transform: translate(0px, 0px) rotate(0deg); } }

/* APP CARD & UTILS */
.app-card { background: rgba(30, 30, 40, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 24px; display: flex; flex-direction: column; transition: all 0.2s ease; cursor: pointer; position: relative; overflow: hidden; }
.app-card:hover { background: rgba(40, 40, 55, 0.8); border-color: rgba(255, 255, 0, 0.3); transform: translateY(-4px); }
.app-card-content { display: flex; flex-direction: row; flex-grow: 1; }
.app-icon-wrapper { width: 56px; height: 56px; border-radius: 14px; background: linear-gradient(135deg, rgba(255, 255, 0, 0.15), rgba(100, 100, 0, 0.4)); display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-right: 16px; border: 1px solid rgba(255, 255, 0, 0.1); }
.app-info { flex-grow: 1; min-width: 0; }
.app-title { font-size: 1.1rem; font-weight: 800; color: white; line-height: 1.2; }
.app-desc { line-height: 1.4; margin-top: 4px; font-size: 0.85rem; }
.text-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.app-actions { margin-top: auto; }
.toolbox-item { transition: background-color 0.2s ease-in-out; cursor: pointer; }
.toolbox-item:hover { background-color: rgba(255, 255, 255, 0.05); }
.category-header { font-weight: bold; font-size: 0.7rem; color: #FFFF00; background-color: rgba(0,0,0,0.2); }
.favorites-header { color: #FFFF00; display: flex; align-items: center; }
.button-group { opacity: 0; transition: opacity 0.2s; }
.toolbox-item:hover .button-group { opacity: 1; }
.orbitron-font { font-family: 'Orbitron', monospace; }
.font-mono { font-family: 'Fira Code', monospace; }
.glow-text { text-shadow: 0 0 10px rgba(255, 255, 0, 0.5); }
.gap-3 { gap: 12px; }
.search-wrapper :deep(.v-field) { border: 1px solid rgba(255, 255, 0, 0.3); transition: all 0.3s; }
.search-wrapper :deep(.v-field--focused) { border-color: #FFFF00; box-shadow: 0 0 15px rgba(255,255,0,0.3); }
.toolbox-search :deep(.v-field__input) { font-size: 0.85rem; color: #ccc; font-family: 'Fira Code', monospace; }
.min-h-32 { min-height: 32px; }
</style>
