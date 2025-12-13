//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\ControlsFooter.vue total lines 1020 
//#######################################################################

<template>
  <div class="footer-area-wrapper">

    <div
      class="mini-prompt-container"
      :class="{ 'is-visible': !isFooterVisible && !isPinned && !isMenuOpen }"
    >
      <v-sheet class="mini-prompt-sheet d-flex flex-column" elevation="10" rounded="xl" :style="{ borderColor: promptMode === 'architect' ? 'rgba(213, 0, 249, 0.3)' : 'rgba(255,255,255,0.08)' }">

        <div class="mode-switcher d-flex justify-center pt-1">
            <div class="pill-switch bg-grey-darken-4 rounded-pill d-flex pa-1 border-thin">
                <div
                    class="pill-option"
                    :class="{ active: promptMode === 'chat' }"
                    @click="promptMode = 'chat'"
                >
                    <v-icon icon="mdi-chat-outline" size="10" class="mr-1"></v-icon> CHAT
                </div>
                <div
                    class="pill-option"
                    :class="{ active: promptMode === 'architect' }"
                    @click="promptMode = 'architect'"
                >
                    <v-icon icon="mdi-sitemap-outline" size="10" class="mr-1"></v-icon> ARCHITECT
                </div>
            </div>
        </div>

        <v-text-field
          v-model="quickPrompt"
          :placeholder="promptMode === 'chat' ? 'Send instant prompt to Agent...' : 'Describe workflow logic (e.g. Scrape BTC price...)'"
          variant="solo"
          density="compact"
          hide-details
          bg-color="rgba(20, 20, 20, 0.95)"
          class="mini-prompt-input"
          @keyup.enter="handleFooterSubmit"
          @focus="handlePromptFocus"
          @blur="handlePromptBlur"
        >
          <template v-slot:prepend-inner>
             <v-btn icon="mdi-chevron-up" size="x-small" variant="text" color="grey" @click="isFooterVisible = true" title="Show Controls"></v-btn>
          </template>

          <template v-slot:append-inner>
            <v-btn
              :icon="promptMode === 'chat' ? 'mdi-send' : 'mdi-creation'"
              size="small"
              variant="text"
              :color="promptMode === 'chat' ? 'cyan-accent-3' : 'purple-accent-3'"
              @click="handleFooterSubmit"
              :loading="isSendingPrompt"
            ></v-btn>
          </template>
        </v-text-field>
      </v-sheet>
    </div>

    <div
      class="controls-footer-container"
      :class="{ 'is-visible': isFooterVisible || isMouseOverFooter || isPinned || isMenuOpen || isPresetDropdownOpen }"
      @mouseover="isMouseOverFooter = true"
      @mouseleave="isMouseOverFooter = false"
    >
      <div class="cockpit-wrapper">

        <div class="cockpit-main-row">

            <div class="section-left">
                <div class="custom-dropdown-wrapper" ref="presetDropdownRef">
                    <div class="dropdown-trigger" @click="togglePresetDropdown">
                        <span class="trigger-label" :class="{'placeholder': !currentPresetName}">
                            {{ currentPresetName || 'Load Preset...' }}
                        </span>
                        <v-icon size="small" color="rgba(255,255,255,0.3)">mdi-chevron-down</v-icon>
                    </div>

                    <div v-if="isPresetDropdownOpen" class="custom-dropdown-menu">
                         <div v-if="presets.length === 0" class="dropdown-empty">No Presets Found</div>
                         <div
                            v-for="preset in presets"
                            :key="preset.id"
                            class="dropdown-item"
                            @click="selectPreset(preset.id)"
                         >
                            <span class="item-text">{{ preset.name }}</span>
                            <div class="item-actions">
                                <v-icon
                                    size="x-small"
                                    :color="favoritePresets.includes(preset.id) ? 'yellow-darken-2' : 'grey-darken-3'"
                                    @click.stop="workflowStore.toggleFavorite(preset.id)"
                                    class="action-icon"
                                >mdi-star</v-icon>
                                <v-icon
                                    size="x-small"
                                    color="red-darken-3"
                                    @click.stop="handleDeletePreset(preset.id)"
                                    class="action-icon"
                                >mdi-delete-outline</v-icon>
                            </div>
                         </div>
                    </div>
                </div>
            </div>

            <div class="section-center">
                <div class="execution-group">
                    <button
                        class="btn-exec btn-simulate"
                        @click="handleExecution('SIMULATE')"
                        :disabled="workflowStore.isExecuting || !canExecute"
                        title="Simulate"
                    >
                        SIMULATE
                    </button>

                    <template v-if="!workflowStore.isExecuting">
                        <button
                            class="btn-exec btn-run"
                            @click="handleExecution('EXECUTE')"
                            :disabled="!canExecute"
                        >
                            <v-icon size="small">mdi-play</v-icon>
                            <span>RUN FLOW</span>
                        </button>
                    </template>
                    <template v-else>
                        <button
                            class="btn-exec btn-stop"
                            @click="workflowStore.stopCurrentWorkflow()"
                        >
                            <v-icon size="small">mdi-square</v-icon>
                            <span>STOP</span>
                        </button>

                        <button
                            v-if="!workflowStore.isPaused"
                            class="btn-exec btn-pause"
                            @click="workflowStore.pauseCurrentWorkflow()"
                            title="Pause"
                        >
                            <v-icon size="small">mdi-pause</v-icon>
                        </button>
                        <button
                            v-else
                            class="btn-exec btn-resume"
                            @click="workflowStore.resumeCurrentWorkflow()"
                            title="Resume"
                        >
                             <v-icon size="small">mdi-play</v-icon>
                        </button>
                    </template>
                </div>
            </div>

            <div class="section-right">

                <div class="vitals-pill" @click="attemptReconnect" :title="connectionChipTooltip">
                    <div class="led-indicator">
                         <span class="led-core" :class="connectionStatusClass"></span>
                         <span class="led-ring" :class="connectionStatusClass"></span>
                    </div>
                    <template v-if="isConnected">
                        <span class="vital-label">CPU</span>
                        <span class="vital-val">{{ currentEngineStatus.cpuPercent?.toFixed(0) ?? '0' }}%</span>
                        <div class="vital-sep"></div>
                        <span class="vital-label">RAM</span>
                        <span class="vital-val">{{ currentEngineStatus.memoryPercent?.toFixed(0) ?? '0' }}%</span>
                    </template>
                    <template v-else>
                        <span class="vital-label text-error">DISCONNECTED</span>
                    </template>
                </div>

                <div class="divider-vertical"></div>

                <div class="tools-group">
                    <button class="icon-btn" @click="handleSave" title="Quick Save">
                        <v-icon size="small">mdi-content-save-outline</v-icon>
                    </button>
                    <button class="icon-btn" @click="handleAutoLayout" title="Auto Layout" :disabled="layoutWorkerStore.isWorking">
                        <v-icon size="small" :class="{'spin': layoutWorkerStore.isWorking}">mdi-auto-fix</v-icon>
                    </button>
                     <button class="icon-btn danger" @click="workflowStore.clearCanvas" title="Clear Canvas">
                        <v-icon size="small">mdi-delete-sweep-outline</v-icon>
                    </button>
                </div>

                <div class="divider-vertical"></div>

                <button
                    class="icon-btn toggle-btn"
                    :class="{ 'active': showAdvancedConfig }"
                    @click="showAdvancedConfig = !showAdvancedConfig"
                    title="Settings & Engine Info"
                >
                    <v-icon size="small">mdi-tune</v-icon>
                </button>

                 <button
                    class="icon-btn"
                    :class="{ 'active': isPinned }"
                    @click="uiStore.setFooterPin(!isPinned)"
                    title="Pin Footer"
                >
                    <v-icon size="small" style="font-size: 14px;">{{ isPinned ? 'mdi-pin' : 'mdi-pin-outline' }}</v-icon>
                </button>
            </div>
        </div>

        <div v-if="showAdvancedConfig" class="cockpit-config-row">

             <div class="config-section">
                 <div class="switch-group">
                     <input
                        type="checkbox"
                        id="loop-check"
                        v-model="globalLoopConfig.isEnabled"
                        :disabled="isReadOnly"
                     />
                     <label for="loop-check">REPEAT</label>
                 </div>
                 <input
                    v-model.number="globalLoopConfig.iterations"
                    type="number"
                    class="compact-input"
                    :disabled="!globalLoopConfig.isEnabled || isReadOnly"
                    placeholder="#"
                    title="Iterations"
                 />
             </div>

             <div class="config-divider"></div>

             <div class="config-section">
                 <div class="switch-group">
                     <input
                        type="checkbox"
                        id="delay-check"
                        v-model="globalLoopConfig.isDelayEnabled"
                        :disabled="!globalLoopConfig.isEnabled || isReadOnly"
                     />
                     <label for="delay-check">DELAY</label>
                 </div>

                <div class="radio-pill-group" :class="{ disabled: !globalLoopConfig.isEnabled || !globalLoopConfig.isDelayEnabled }">
                    <div
                        class="radio-pill"
                        :class="{ active: globalLoopConfig.delayType === 'static' }"
                        @click="!isReadOnly && (globalLoopConfig.delayType = 'static')"
                    >FIX</div>
                    <div
                        class="radio-pill"
                        :class="{ active: globalLoopConfig.delayType === 'random_range' }"
                        @click="!isReadOnly && (globalLoopConfig.delayType = 'random_range')"
                    >RND</div>
                </div>

                <template v-if="globalLoopConfig.delayType === 'static'">
                    <input
                        v-model.number="globalLoopConfig.delayStatic"
                        type="number"
                        class="compact-input"
                        style="width: 45px"
                        :disabled="!globalLoopConfig.isEnabled || !globalLoopConfig.isDelayEnabled || isReadOnly"
                    />
                    <span class="unit-text">s</span>
                </template>

                <template v-else>
                    <input
                        v-model.number="globalLoopConfig.delayRandomMin"
                        type="number"
                        class="compact-input"
                        style="width: 35px"
                        placeholder="min"
                        :disabled="!globalLoopConfig.isEnabled || !globalLoopConfig.isDelayEnabled || isReadOnly"
                    />
                    <span class="unit-text">-</span>
                    <input
                        v-model.number="globalLoopConfig.delayRandomMax"
                        type="number"
                        class="compact-input"
                        style="width: 35px"
                        placeholder="max"
                        :disabled="!globalLoopConfig.isEnabled || !globalLoopConfig.isDelayEnabled || isReadOnly"
                    />
                    <span class="unit-text">s</span>
                </template>
             </div>

             <v-spacer></v-spacer>

             <div class="engine-name-display">
                 <span class="eng-label">TARGET:</span>
                 <span class="eng-name">{{ selectedEngine ? selectedEngine.name : 'N/A' }}</span>
             </div>

             <div class="config-divider"></div>

             <div class="extra-actions">
                <button class="icon-btn" @click="handleSaveAs" title="Save As New Preset">
                    <v-icon size="small">mdi-content-save-edit-outline</v-icon>
                </button>
                <button class="icon-btn" @click="openPublishDialog" :disabled="!currentPresetName" title="Publish to Marketplace">
                    <v-icon size="small">mdi-publish</v-icon>
                </button>
                <button class="icon-btn" @click="handleShare" :disabled="!currentPresetName" title="Share Workflow">
                    <v-icon size="small">mdi-share-variant-outline</v-icon>
                </button>
             </div>
        </div>

      </div>

      <v-dialog v-model="isSaveAsDialogOpen" max-width="500px" persistent>
          <v-card class="dialog-card">
              <v-card-title class="orbitron-font">Save Workflow As</v-card-title> <v-card-text>
                  <v-text-field
                      v-model="newPresetName"
                      label="Preset Name" placeholder="my-awesome-workflow" variant="outlined"
                      autofocus
                      @keyup.enter="confirmSaveAs"
                  ></v-text-field>
              </v-card-text>
              <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn variant="text" @click="isSaveAsDialogOpen = false">Cancel</v-btn> <v-btn color="cyan" variant="flat" @click="confirmSaveAs" class="action-button">Save</v-btn> </v-card-actions>
          </v-card>
      </v-dialog>

      <MarketplacePublishDialog v-model="isPublishDialogOpen" />
    </div>
  </div>
</template>

<script setup>
import MarketplacePublishDialog from '@/components/MarketplacePublishDialog.vue';
import { useMarketplaceStore } from '@/store/marketplace';
import { onMounted, onUnmounted, computed, ref } from 'vue';
import { useWorkflowStore } from '@/store/workflow';
import { useUiStore } from '@/store/ui';
import { useShareStore } from '@/store/share';
import { storeToRefs } from 'pinia';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'vue-router';
import { useLayoutWorkerStore } from '@/store/layoutWorker';
import { useSocketStore } from '@/store/socket';
import { useLocaleStore } from '@/store/locale';
import { useSettingsStore } from '@/store/settings';
import api from '@/api';

const workflowStore = useWorkflowStore();
const uiStore = useUiStore();
const shareStore = useShareStore();
const authStore = useAuthStore();
const router = useRouter();
const layoutWorkerStore = useLayoutWorkerStore();
const socketStore = useSocketStore();
const marketplaceStore = useMarketplaceStore();
const localeStore = useLocaleStore();
const settingsStore = useSettingsStore();
const { loc } = storeToRefs(localeStore);

const { presets, currentPresetName, globalLoopConfig, isReadOnly, canExecute, favoritePresets } = storeToRefs(workflowStore);
const { isConnected, isConnecting, connectionError, currentEngineStatus } = storeToRefs(socketStore);

const selectedEngine = computed(() => {
    return socketStore.isConnected ? { name: 'Local Desktop' } : null;
});

const { isFooterPinned: isPinned } = storeToRefs(uiStore);
const { isModified } = storeToRefs(workflowStore);

const selectedPreset = computed(() => currentPresetName.value);

const isFooterVisible = ref(false);
const isMouseOverFooter = ref(false);
const isMenuOpen = ref(false);
const isPublishDialogOpen = ref(false);
const isSaveAsDialogOpen = ref(false);
const newPresetName = ref('');
const showAdvancedConfig = ref(false);
const isPresetDropdownOpen = ref(false);
const presetDropdownRef = ref(null);

const quickPrompt = ref('');
const isSendingPrompt = ref(false);
const isPromptFocused = ref(false);
const promptMode = ref('chat');

function handlePromptFocus() {
    isPromptFocused.value = true;
    isFooterVisible.value = false;
}

function handlePromptBlur() {
    setTimeout(() => { isPromptFocused.value = false; }, 200);
}

async function handleFooterSubmit() {
    if (!quickPrompt.value.trim()) return;

    if (promptMode.value === 'chat') {
        await sendQuickPrompt();
    } else {
        await generateBlueprint();
    }
}

async function sendQuickPrompt() {
    isSendingPrompt.value = true;
    try {
        await socketStore.sendAgentInput(quickPrompt.value);
        uiStore.showNotification({ text: "Message sent to Agent!", color: "cyan" });
        quickPrompt.value = "";
    } catch (e) {
        uiStore.showNotification({ text: "Failed to send prompt.", color: "error" });
    } finally {
        isSendingPrompt.value = false;
    }
}

async function generateBlueprint() {
    isSendingPrompt.value = true;
    try {
        uiStore.showNotification({ text: "Architecting solution...", color: "purple-accent-2" });

        const response = await api.post('/ai-architect/generate', {
            prompt: quickPrompt.value
        });

        if (response.data && response.data.error) throw new Error(response.data.error);

        const result = response.data.data || response.data;
        if (!result.nodes || !result.connections) throw new Error("Invalid Blueprint Format");

        workflowStore.loadGraph(result);
        uiStore.showNotification({ text: "Blueprint Generated Successfully!", color: "success" });

        setTimeout(() => layoutWorkerStore.runAutoLayout(), 500);

        quickPrompt.value = "";

    } catch (e) {
        console.error("Architect Error:", e);
        uiStore.showNotification({ text: `Architect Failed: ${e.message}`, color: "error" });
    } finally {
        isSendingPrompt.value = false;
    }
}

const handleAutoLayout = () => {
    layoutWorkerStore.runAutoLayout();
};

function handleExecution(mode) {
    if (!socketStore.isConnected) {
        uiStore.showConnectEngineDialog();
        return;
    }

    if (canExecute.value && !authStore.isAuthenticated) {
        uiStore.showNotification({ text: 'Please login to run or simulate workflows.', color: 'warning' });
        router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } });
        return;
    }

    if (mode === 'SIMULATE') {
        workflowStore.simulateCurrentWorkflow();
    } else {
        workflowStore.executeCurrentWorkflow();
    }
}

const handleMouseMove = (event) => {
  if (isPinned.value) {
    return;
  }
  if (isPromptFocused.value) {
      isFooterVisible.value = false;
      return;
  }
  const triggerZoneHeight = 15;
  const mouseY = event.clientY;
  const windowHeight = window.innerHeight;

  if (windowHeight - mouseY < triggerZoneHeight) {
      isFooterVisible.value = true;
  } else if (!isMouseOverFooter.value && !isPresetDropdownOpen.value) {
      isFooterVisible.value = false;
  }
};

const handleClickOutside = (event) => {
    if (presetDropdownRef.value && !presetDropdownRef.value.contains(event.target)) {
        isPresetDropdownOpen.value = false;
    }
};

onMounted(async () => {
  window.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('click', handleClickOutside);
  window.addEventListener('beforeunload', (event) => {
      if (isModified.value) {
          event.preventDefault();
          event.returnValue = 'You have unsaved changes! Are you sure you want to leave?';
      }
  });
  layoutWorkerStore.initWorker();

  try {
      await settingsStore.fetchSettings();
      const savedPinState = settingsStore.settings['ui_footer_pinned'];
      if (savedPinState !== undefined) {
          uiStore.setFooterPin(savedPinState);
      }
  } catch (e) {
      console.error("Settings load error", e);
  }
});

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('beforeunload', (event) => {
      if (isModified.value) {
          event.preventDefault();
          event.returnValue = 'You have unsaved changes! Are you sure you want to leave?';
      }
  });
});

const presetItems = computed(() => presets.value.map(p => ({ title: p.name, value: p.id })));

const togglePresetDropdown = () => {
    isPresetDropdownOpen.value = !isPresetDropdownOpen.value;
};

const selectPreset = (id) => {
    workflowStore.loadWorkflow(id);
    isPresetDropdownOpen.value = false;
};

const handleSave = () => {
    if (!socketStore.isConnected) {
        uiStore.showConnectEngineDialog();
        return;
    }
    if (currentPresetName.value) {
        workflowStore.saveCurrentWorkflow(currentPresetName.value);
    } else {
        handleSaveAs();
    }
};
const handleSaveAs = () => {
  if (!socketStore.isConnected) {
    uiStore.showConnectEngineDialog();
    return;
  }
  newPresetName.value = currentPresetName.value || 'new-preset';
  isSaveAsDialogOpen.value = true;
};

function openPublishDialog() {
    if (!currentPresetName.value) {
        uiStore.showNotification({ text: 'Please save your workflow with a name before publishing.', color: 'warning' });
        handleSaveAs();
        return;
    }
    if (isModified.value) {
        uiStore.showNotification({ text: 'You have unsaved changes. Please save before publishing.', color: 'warning' });
        handleSave();
        return;
    }
    isPublishDialogOpen.value = true;
}

const handleShare = () => {
    if (!currentPresetName.value) {
        uiStore.showNotification({ text: 'Please save the workflow before sharing.', color: 'warning' });
        return;
    }
    shareStore.openShareModal({ name: currentPresetName.value });
};

const confirmSaveAs = () => {
    if (newPresetName.value && newPresetName.value.trim()) {
        workflowStore.saveCurrentWorkflow(newPresetName.value.trim());
    }
    isSaveAsDialogOpen.value = false;
};

async function handleDeletePreset(presetId) {
    const preset = presets.value.find(p => p.id === presetId);
    if (preset) {
        const confirmed = await uiStore.showConfirmation({
            title: 'Delete Preset',
            text: `Are you sure you want to delete the preset "${preset.name}"? This cannot be undone.`,
            color: 'error',
            confirmText: 'Delete'
        });
        if (confirmed) {
            workflowStore.deletePresetAction(presetId);
        }
    }
}

function handlePresetSelection(presetId) {
    if (presetId) {
        workflowStore.loadWorkflow(presetId);
    }
}

const connectionStatusClass = computed(() => {
  if (isConnecting.value) return 'connecting';
  if (isConnected.value) return 'online';
  if (connectionError.value) return 'error';
  return 'offline';
});

const connectionChipTooltip = computed(() => {
    if (isConnected.value) return `Connected to engine: ${selectedEngine.value?.name || 'N/A'}`;
    if (connectionError.value) return connectionError.value;
    return 'Not connected to any engine';
});

function attemptReconnect() {
    if (connectionError.value && !isConnecting.value) {
        console.log("[ControlsFooter] Attempting manual reconnect...");
        socketStore.connect();
    }
}
</script>

<style scoped>
/* Global Wrapper */
.footer-area-wrapper {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 850px;
  z-index: 10;
  pointer-events: none;
}

/* Mini Prompt */
.mini-prompt-container {
  position: absolute;
  bottom: 24px;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  pointer-events: auto;
  transform: translateY(100px);
  opacity: 0;
  transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.3s ease-in;
}
.mini-prompt-container.is-visible {
  transform: translateY(0);
  opacity: 1;
}
.mini-prompt-sheet {
  width: 100%;
  max-width: 500px;
  backdrop-filter: blur(12px);
  background-color: rgba(24, 24, 24, 0.95) !important;
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  transition: border-color 0.3s ease;
}
.mini-prompt-input :deep(.v-field__input) {
  color: #fff !important;
  font-size: 0.95rem;
}

/* Mode Switcher Pills */
.pill-switch {
    background-color: #1a1a1a;
    border: 1px solid rgba(255,255,255,0.1);
}
.pill-option {
    padding: 2px 12px;
    font-size: 9px;
    font-family: 'Orbitron', monospace;
    font-weight: bold;
    border-radius: 12px;
    cursor: pointer;
    color: #666;
    transition: all 0.2s;
    display: flex;
    align-items: center;
}
.pill-option.active {
    color: #000;
    background-color: #fff;
}
.pill-option:first-child.active { background-color: #00E5FF; }
.pill-option:last-child.active { background-color: #D500F9; color: #fff; }

/* Main Cockpit Footer */
.controls-footer-container {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%) translateY(150%);
  width: 98%;
  max-width: 850px;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1);
  z-index: 20;
  pointer-events: none;
}
.controls-footer-container.is-visible {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
  pointer-events: auto;
}

/* Sleek Dark Theme */
.cockpit-wrapper {
    background: #181818;
    border: 1px solid #333;
    border-radius: 8px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    padding: 4px;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow: visible;
}

/* --- TOP ROW --- */
.cockpit-main-row {
    display: flex;
    align-items: center;
    height: 46px;
    padding: 0 8px;
    gap: 10px;
}

/* Section Left: Presets */
.section-left {
    flex: 1;
    min-width: 0;
}

.custom-dropdown-wrapper {
    position: relative;
    width: 180px;
    height: 34px;
}
.dropdown-trigger {
    background: transparent;
    border: 1px solid transparent;
    color: #e0e0e0;
    height: 100%;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}
.dropdown-trigger:hover { background: #252525; border-color: #444; }
.trigger-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.trigger-label.placeholder { color: #777; }

.custom-dropdown-menu {
    position: absolute;
    bottom: calc(100% + 6px);
    left: 0;
    width: 240px;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 6px;
    max-height: 250px;
    overflow-y: auto;
    z-index: 100;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8);
}
.dropdown-item {
    padding: 8px 12px;
    font-size: 0.85rem;
    color: #ccc;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    border-bottom: 1px solid #2a2a2a;
}
.dropdown-item:hover { background: #2a2a2a; color: #fff; }
.dropdown-item:last-child { border-bottom: none; }
.action-icon { opacity: 0.4; transition: opacity 0.2s; margin-left: 8px; }
.action-icon:hover { opacity: 1; }
.dropdown-empty { padding: 16px; text-align: center; color: #666; font-size: 0.8rem; }

/* Section Center: Controls */
.section-center {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
}

.execution-group {
    display: flex;
    background: #111;
    padding: 2px;
    border-radius: 6px;
    gap: 1px;
    height: 34px;
    border: 1px solid #2a2a2a;
}
.btn-exec {
    border: none;
    padding: 0 14px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #ccc;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    height: 100%;
    background: transparent;
}
.btn-simulate { color: #666; border-radius: 4px 0 0 4px; }
.btn-simulate:hover:not(:disabled) { background: #222; color: #fff; }
.btn-simulate:disabled { opacity: 0.3; cursor: not-allowed; }

.btn-run {
    color: #fff;
    min-width: 100px;
    justify-content: center;
    border-radius: 0 4px 4px 0;
    background: #1f2937;
}
.btn-run:hover:not(:disabled) { background: #00bd7e; color: #000; }
.btn-run:disabled { opacity: 0.3; background: #222; color: #555; cursor: not-allowed; }

.btn-stop { color: #ef4444; min-width: 80px; justify-content: center; background: #222; }
.btn-stop:hover { background: #ef4444; color: #fff; }

.btn-pause, .btn-resume { color: #ccc; padding: 0 10px; background: #222; }
.btn-pause:hover { color: #fff; background: #333; }
.btn-resume:hover { color: #00bd7e; background: #333; }

/* Section Right: Vitals + Tools */
.section-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    flex: 1;
}

/* Vitals Pill (Top) */
.vitals-pill {
    display: flex;
    align-items: center;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 0 10px;
    gap: 8px;
    height: 34px;
    cursor: pointer;
    transition: border-color 0.2s;
}
.vitals-pill:hover { border-color: #444; }
.vital-item { display: flex; align-items: center; gap: 4px; font-family: monospace; font-size: 0.7rem; }
.vital-label { color: #666; font-size: 0.65rem; font-weight: 700; }
.vital-val { color: #00bd7e; font-size: 0.75rem; font-weight: 600; font-family: monospace; }
.vital-sep { width: 1px; height: 12px; background: #333; }
.text-error { color: #666; font-size: 0.65rem; }

/* LED Indicator (Inside Vitals Pill) */
.led-indicator {
    position: relative;
    width: 10px;
    height: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.led-core {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #555;
    z-index: 2;
}
.led-ring {
    position: absolute;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: transparent;
    z-index: 1;
    opacity: 0.4;
}
/* Status Colors */
.led-core.online { background-color: #00bd7e; box-shadow: 0 0 6px #00bd7e; animation: breathe 3s infinite ease-in-out; }
.led-core.connecting { background-color: #fbbf24; animation: blink 0.5s infinite; }
.led-core.error { background-color: #ef4444; }

.tools-group { display: flex; align-items: center; gap: 2px; }
.divider-vertical { width: 1px; height: 20px; background: #333; margin: 0 4px; }

.icon-btn {
    background: transparent;
    border: none;
    color: #666;
    width: 28px;
    height: 28px;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}
.icon-btn:hover { color: #fff; background: #252525; }
.icon-btn.active { color: #00bd7e; background: rgba(0, 189, 126, 0.1); }
.icon-btn.danger:hover { color: #ef4444; background: rgba(239, 68, 68, 0.1); }
.spin { animation: spin 1s linear infinite; }

/* --- BOTTOM ROW (DRAWER) --- */
.cockpit-config-row {
    background: #111;
    border-top: 1px solid #252525;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-radius: 0 0 8px 8px;
    animation: slideDown 0.2s ease-out;
}

.config-section { display: flex; align-items: center; gap: 10px; }
.switch-group { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.switch-group label { font-size: 0.7rem; color: #777; font-weight: 700; cursor: pointer; }
.switch-group input[type="checkbox"] { accent-color: #00bd7e; cursor: pointer; }

.compact-input {
    background: #1e1e1e;
    border: 1px solid #333;
    color: #ccc;
    height: 24px;
    font-size: 0.75rem;
    text-align: center;
    border-radius: 3px;
}
.compact-input:focus { outline: none; border-color: #00bd7e; }
.compact-input:disabled { opacity: 0.3; cursor: not-allowed; }

.config-divider { width: 1px; height: 20px; background: #333; }
.unit-text { color: #555; font-size: 0.7rem; }

.radio-pill-group { display: flex; background: #1e1e1e; border-radius: 3px; overflow: hidden; border: 1px solid #333; }
.radio-pill-group.disabled { opacity: 0.3; pointer-events: none; }
.radio-pill {
    padding: 2px 8px;
    font-size: 0.7rem;
    cursor: pointer;
    color: #777;
    transition: all 0.2s;
}
.radio-pill.active { background: #333; color: #fff; }
.radio-pill:hover { color: #fff; }

/* Engine Name in Drawer */
.engine-name-display {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #666;
    font-size: 0.75rem;
    font-family: monospace;
}
.eng-label { font-weight: 700; color: #444; }
.eng-name { color: #aaa; }

/* Extra Actions (Icons) */
.extra-actions { display: flex; align-items: center; gap: 4px; }

@keyframes breathe {
    0% { box-shadow: 0 0 2px rgba(0, 189, 126, 0.5); }
    50% { box-shadow: 0 0 8px rgba(0, 189, 126, 0.8); }
    100% { box-shadow: 0 0 2px rgba(0, 189, 126, 0.5); }
}
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); margin-top: -40px; z-index: -1; }
    to { opacity: 1; transform: translateY(0); margin-top: 0; z-index: 0; }
}

.dialog-card {
    background: #1e1e1e !important;
    border: 1px solid #333;
    color: #fff !important;
}
.dialog-card :deep(.v-card-title) { color: #fff; }
.dialog-card :deep(.v-field__input) { color: #fff !important; }
</style>
