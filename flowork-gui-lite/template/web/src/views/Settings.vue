//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\Settings.vue total lines 268 
//#######################################################################

<template>
  <div class="settings-layout">
    <div class="tech-grid-bg"></div>
    <NeuralCanvasBackground class="subtle-neural" />

    <v-navigation-drawer permanent class="settings-sidebar" width="280" color="#050505" elevation="0">
      <div class="pa-6 pb-4 header-animate">
        <div class="d-flex align-center">
          <v-icon icon="mdi-console-network" color="amber-accent-3" size="large" class="mr-3 icon-pulse-gold"></v-icon>
          <div>
            <div class="text-h6 font-weight-bold text-white orbitron-font tracking-wide">SYSTEM</div>
            <div class="text-caption text-cyan-lighten-2 text-uppercase tracking-widest" style="font-size: 0.7rem !important;">
              Configuration /// <span class="text-gold">V2.1</span>
            </div>
          </div>
        </div>
      </div>
      <v-divider class="border-cyan-dim mb-4 mx-4"></v-divider>
      <v-list nav class="px-4 bg-transparent">
        <v-list-item
          v-for="(item, index) in navItems"
          :key="item.value"
          :value="item.value"
          @click="settingsStore.setActiveSection(item.value)"
          rounded="0"
          class="mb-1 nav-item animated-item"
          :class="{ 'active-item': activeSection === item.value }"
          :style="{ animationDelay: `${index * 50}ms` }"
          :ripple="false"
        >
          <template v-slot:prepend>
            <v-icon :icon="item.icon" size="small" class="nav-icon" :class="{ 'active-icon': activeSection === item.value }"></v-icon>
          </template>
          <v-list-item-title class="font-weight-medium text-caption text-uppercase" :class="activeSection === item.value ? 'text-white' : 'text-grey-lighten-1'">
            {{ loc(item.titleKey) || item.fallbackTitle }}
          </v-list-item-title>
          <div v-if="activeSection === item.value" class="active-indicator" :class="item.value === 'variables' ? 'bg-gold' : 'bg-cyan'"></div>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <div class="settings-content custom-scrollbar">
      <div class="settings-header mb-8">
        <v-container class="content-container">
            <div class="d-flex align-end justify-space-between pb-4 border-bottom-mixed">
                <div>
                    <h1 class="text-h4 font-weight-regular text-white orbitron-font mb-1">{{ getActiveTitle() }}</h1>
                    <div class="d-flex align-center text-caption text-grey font-mono">
                        <v-icon icon="mdi-subdirectory-arrow-right" size="small" class="mr-2 text-gold"></v-icon>
                        root/user/preferences/<span class="text-cyan ml-1">{{ activeSection }}</span>
                    </div>
                </div>
            </div>
        </v-container>
      </div>

      <v-container class="content-container pt-0">
        <transition name="slide-fade" mode="out-in">
            <div :key="activeSection" class="section-wrapper">

                <div v-if="activeSection === 'variables'">
                    <div class="holo-card gold-variant pa-8 card-entrance">
                        <div class="d-flex align-start mb-6">
                            <div class="hex-icon-box gold-hex mr-5">
                                <v-icon icon="mdi-shield-lock-outline" size="32" color="amber-accent-3"></v-icon>
                            </div>
                            <div>
                                <h3 class="text-h6 text-amber-accent-3 font-weight-bold orbitron-font">SECURE VAULT ACCESS</h3>
                                <p class="text-caption text-grey-lighten-1 mt-2 font-mono">Encrypted storage for global environment variables.</p>
                            </div>
                        </div>
                        <v-divider class="border-gold-dim mb-6"></v-divider>
                        <v-btn color="amber-accent-3" variant="outlined" class="text-amber-accent-3 font-weight-bold px-6 border-gold hover-glow-gold" @click="isVariableManagerOpen = true" height="48" prepend-icon="mdi-console" rounded="0">
                            INITIALIZE VAULT MANAGER
                        </v-btn>
                    </div>
                </div>

                <div v-else-if="isLoading" class="d-flex flex-column justify-center align-center py-16">
                    <v-progress-circular indeterminate color="cyan" width="2" size="48"></v-progress-circular>
                    <p class="mt-4 text-cyan font-mono text-caption blink-text">DECRYPTING CONFIG...</p>
                </div>

                <v-form v-else class="settings-form">
                    <div v-if="activeSection === 'general'">
                         <div class="holo-card pa-8 card-entrance">
                            <div class="card-label">INTERFACE PARAMS</div>
                            <SettingsField :label="loc('settings_general_language_label')" hint="Primary Communication Protocol">
                                <v-select v-model="localSettings.language" :items="['en', 'id']" variant="underlined" density="comfortable" class="terminal-input" menu-icon="mdi-chevron-down" color="cyan"></v-select>
                            </SettingsField>
                         </div>
                    </div>

                    <div v-if="activeSection === 'advanced'">
                         <div class="holo-card pa-8 card-entrance">
                             <div class="d-flex align-center justify-space-between mb-8">
                                <div class="card-label text-error">FAIL-SAFE PROTOCOLS</div>
                                 <v-btn icon="mdi-refresh" variant="plain" color="cyan" size="x-small" @click="refreshPresets" :loading="arePresetsLoading" class="spin-on-click"></v-btn>
                             </div>
                             <div class="d-flex align-center justify-space-between mb-6 py-2">
                                 <div>
                                     <div class="text-body-1 text-white font-weight-medium font-mono">Global Error Handler</div>
                                     <div class="text-caption text-grey mt-1">Execute recovery workflow upon system failure.</div>
                                 </div>
                                 <v-switch v-model="localSettings.global_error_handler_enabled" color="amber-accent-3" inset hide-details class="gold-switch"></v-switch>
                             </div>
                             <v-expand-transition>
                                 <div v-if="localSettings.global_error_handler_enabled" class="pl-4 mt-6 border-l-gold">
                                     <SettingsField :label="loc('settings_advanced_error_preset_label')" hint="Select Recovery Workflow">
                                         <v-select v-model="localSettings.global_error_workflow_preset" :items="presetItems" variant="underlined" density="comfortable" class="terminal-input" placeholder="Select preset..." :loading="arePresetsLoading" @click="refreshPresets" menu-icon="mdi-chevron-down" color="amber-accent-3"></v-select>
                                     </SettingsField>
                                 </div>
                             </v-expand-transition>
                         </div>
                    </div>

                    <div class="d-flex justify-end mt-10 button-entrance">
                        <v-btn color="amber-accent-3" variant="flat" @click="handleSave" :loading="isLoading" class="text-black font-weight-black px-10 text-none glow-button-gold" size="large" rounded="0" elevation="0" height="50" prepend-icon="mdi-content-save-settings">
                            {{ loc('settings_save_button') }}
                        </v-btn>
                    </div>
                </v-form>
            </div>
        </transition>
      </v-container>
    </div>
    <VariableManagerDialog v-model="isVariableManagerOpen" />
  </div>
</template>

<script setup>
import VariableManagerDialog from '@/components/VariableManagerDialog.vue';
import SettingsField from '@/components/settings/SettingsField.vue';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';
import { ref, onMounted, watch, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useSettingsStore } from '@/store/settings';
import { useLocaleStore } from '@/store/locale';
import { apiClient } from '@/api';
import { useUiStore } from '@/store/ui';

const settingsStore = useSettingsStore();
const localeStore = useLocaleStore();
const uiStore = useUiStore();

const { settings, isLoading, activeSection } = storeToRefs(settingsStore);
const { loc } = storeToRefs(localeStore);

const isVariableManagerOpen = ref(false);
const arePresetsLoading = ref(false);
const availablePresets = ref([]);
const localSettings = ref({});

const navItems = [
  { titleKey: 'settings_server_manage_variables_button', fallbackTitle: 'Variables (Vault)', value: 'variables', icon: 'mdi-shield-key-outline' },
  { titleKey: 'settings_section_general', fallbackTitle: 'General', value: 'general', icon: 'mdi-tune' },
  { titleKey: 'settings_section_advanced', fallbackTitle: 'Advanced', value: 'advanced', icon: 'mdi-console-line' },
];

const presetItems = computed(() => {
    if (!Array.isArray(availablePresets.value)) return [];
    return availablePresets.value.map(p => ({
        title: p.name || p.id || 'Unknown Preset',
        value: p.id
    }));
});

function getActiveTitle() {
    const activeItem = navItems.find(i => i.value === activeSection.value);
    return activeItem ? (loc.value(activeItem.titleKey) || activeItem.fallbackTitle) : 'Settings';
}

watch(settings, (newVal) => {
    if (newVal && Object.keys(newVal).length) localSettings.value = JSON.parse(JSON.stringify(newVal));
}, { deep: true, immediate: true });

async function handleSave() {
    Object.assign(settings.value, localSettings.value);
    await settingsStore.saveSettingsAction();
    uiStore.showNotification({ text: 'Configuration saved successfully.', color: 'amber-accent-3', textColor: 'black' });
}

async function refreshPresets() {
    arePresetsLoading.value = true;
    try {
        const response = await apiClient.get('/presets');
        availablePresets.value = Array.isArray(response.data) ? response.data : [];
    } catch (error) {
        console.error("Failed to load presets:", error);
    } finally {
        arePresetsLoading.value = false;
    }
}

onMounted(() => {
    settingsStore.fetchSettings();
    refreshPresets();
});
</script>

<style scoped>
/* STYLE ASLI 100% - NO CHANGE */
.settings-layout { display: flex; height: 100%; overflow: hidden; position: relative; background-color: #050505; color: #e0e0e0; font-family: 'Inter', sans-serif; }
.tech-grid-bg { position: absolute; inset: 0; background-image: linear-gradient(rgba(0, 245, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 245, 255, 0.03) 1px, transparent 1px); background-size: 40px 40px; z-index: 0; pointer-events: none; }
.subtle-neural { opacity: 0.3; pointer-events: none; z-index: 0; }
.settings-sidebar { background: #050505 !important; border-right: 1px solid rgba(0, 245, 255, 0.1) !important; z-index: 5; }
.settings-content { flex: 1; overflow-y: auto; z-index: 1; position: relative; }
.content-container { max-width: 1000px; margin: 0 auto; padding-bottom: 100px; }
.settings-header { background: linear-gradient(180deg, rgba(5,5,5,0.9) 0%, rgba(5,5,5,0) 100%); padding-top: 40px; }
.border-bottom-mixed { border-bottom: 1px solid rgba(0, 245, 255, 0.15); }
.holo-card { background: rgba(10, 15, 25, 0.6); border: 1px solid rgba(0, 245, 255, 0.15); backdrop-filter: blur(5px); position: relative; overflow: hidden; transition: all 0.3s ease; }
.holo-card:hover { border-color: rgba(0, 245, 255, 0.4); box-shadow: 0 0 20px rgba(0, 245, 255, 0.05); }
.holo-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #00F5FF; opacity: 0; transition: opacity 0.3s; }
.holo-card:hover::before { opacity: 1; }
.holo-card.gold-variant { border-color: rgba(255, 215, 0, 0.15); }
.holo-card.gold-variant:hover { border-color: rgba(255, 215, 0, 0.4); box-shadow: 0 0 20px rgba(255, 215, 0, 0.05); }
.holo-card.gold-variant::before { background: #FFD700; }
.card-label { position: absolute; top: 0; right: 0; background: rgba(0, 245, 255, 0.1); color: #00F5FF; font-size: 0.6rem; padding: 2px 8px; font-family: 'Orbitron', monospace; border-bottom-left-radius: 4px; }
.terminal-input :deep(.v-field__input) { font-family: 'JetBrains Mono', 'Courier New', monospace; color: #00F5FF !important; }
.terminal-input :deep(.v-label) { color: rgba(255, 255, 255, 0.5) !important; font-family: 'Inter', sans-serif; }
.terminal-input :deep(.v-field__outline::before) { border-color: rgba(255, 255, 255, 0.15) !important; }
.terminal-input :deep(.v-field--focused .v-field__outline::after) { border-color: #00F5FF !important; border-width: 1px; }
.text-cyan { color: #00F5FF !important; }
.text-gold { color: #FFD700 !important; }
.bg-cyan { background-color: #00F5FF !important; box-shadow: 0 0 10px #00F5FF; }
.bg-gold { background-color: #FFD700 !important; box-shadow: 0 0 10px #FFD700; }
.border-gold { border-color: #FFD700 !important; }
.border-cyan-dim { border-color: rgba(0, 245, 255, 0.1) !important; }
.border-gold-dim { border-color: rgba(255, 215, 0, 0.1) !important; }
.border-l-gold { border-left: 2px solid rgba(255, 215, 0, 0.5); }
.hex-icon-box { width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: rgba(0, 245, 255, 0.05); clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); border: 1px solid rgba(0, 245, 255, 0.2); }
.hex-icon-box.gold-hex { background: rgba(255, 215, 0, 0.05); border-color: rgba(255, 215, 0, 0.3); }
.glow-button-gold { box-shadow: 0 0 15px rgba(255, 215, 0, 0.3); transition: all 0.3s ease; }
.glow-button-gold:hover { box-shadow: 0 0 25px rgba(255, 215, 0, 0.6); transform: translateY(-2px); }
.nav-item { transition: all 0.2s ease; border-left: 2px solid transparent; }
.nav-item:hover { background: rgba(255, 255, 255, 0.03); }
.active-item { background: rgba(0, 245, 255, 0.03) !important; }
.active-indicator { position: absolute; left: 0; top: 0; bottom: 0; width: 2px; }
.nav-icon { opacity: 0.5; transition: 0.3s; }
.active-icon { opacity: 1; color: #fff !important; text-shadow: 0 0 8px rgba(255, 255, 255, 0.3); }
.orbitron-font { font-family: 'Orbitron', sans-serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }
.visualizer .bar { width: 4px; animation: equalizer 1s infinite ease-in-out; }
.cyan-bar { background: #00F5FF; }
.gold-bar { background: #FFD700; }
@keyframes equalizer { 0%, 100% { height: 10%; opacity: 0.3; } 50% { height: 100%; opacity: 1; } }
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.3s ease-out; }
.slide-fade-enter-from { opacity: 0; transform: translateX(10px); }
.slide-fade-leave-to { opacity: 0; transform: translateX(-10px); }
.card-entrance { animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; transform: translateY(20px); animation-delay: 0.1s; }
@keyframes fadeInUp { to { opacity: 1; transform: translateY(0); } }
.blink-text { animation: blink 1.5s infinite; }
.blink-gold { width: 6px; height: 6px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 5px #FFD700; animation: blink 2s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
.icon-pulse-gold { animation: pulse-gold 3s infinite; }
@keyframes pulse-gold { 0% { text-shadow: 0 0 0 rgba(255, 215, 0, 0); } 50% { text-shadow: 0 0 15px rgba(255, 215, 0, 0.5); } 100% { text-shadow: 0 0 0 rgba(255, 215, 0, 0); } }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 245, 255, 0.2); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.tracking-wide { letter-spacing: 0.05em; }
.tracking-widest { letter-spacing: 0.2em; }
</style>
