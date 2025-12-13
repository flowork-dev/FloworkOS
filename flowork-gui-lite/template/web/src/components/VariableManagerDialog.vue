//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\VariableManagerDialog.vue total lines 396 
//#######################################################################

<template>
  <v-dialog
    v-model="dialog"
    fullscreen
    transition="dialog-bottom-transition"
    class="vault-dialog"
  >
    <v-card class="vault-card">

      <v-toolbar color="black" class="vault-toolbar px-4" height="80">
         <div class="d-flex align-center">
             <div class="gold-icon-box mr-4">
                <v-icon icon="mdi-safe" color="#FFD700" size="24"></v-icon>
             </div>
             <div>
                 <v-toolbar-title class="font-weight-bold text-white text-h6" style="letter-spacing: 2px;">
                    VAULT <span class="text-gold">MANAGER</span>
                 </v-toolbar-title>
                 <div class="text-caption text-grey-darken-1 mt-n1">SECURE ENCRYPTED STORAGE</div>
             </div>
         </div>
         <v-spacer></v-spacer>
         <v-btn icon="mdi-close" variant="outlined" color="#FFD700" class="close-btn" @click="closeDialog"></v-btn>
      </v-toolbar>

      <v-divider class="border-gold-subtle"></v-divider>

      <v-card-text class="vault-content custom-scrollbar pa-0">
        <v-container class="pa-8" style="max-width: 1200px;">

            <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
                <v-progress-circular indeterminate color="#FFD700" size="64" width="2"></v-progress-circular>
                <span class="text-caption text-gold mt-4 tracking-widest blink">SYNCING VAULT DATA...</span>
            </div>

            <div v-else>
                <transition-group name="list" tag="div">
                    <div v-for="(item, index) in localVariables" :key="index" class="variable-row mb-6 gold-panel pa-6 rounded-xl">

                        <div class="d-flex align-center gap-4 mb-4">
                            <div class="status-indicator" :class="{ 'active': item.is_enabled }"></div>

                            <v-text-field
                                v-model="item.name"
                                label="KEY NAME"
                                variant="outlined"
                                density="comfortable"
                                hide-details
                                class="gold-input flex-grow-1 font-mono font-weight-bold"
                                :readonly="item.isOriginal || item.is_protected"
                                bg-color="#0a0a0a"
                            >
                                <template v-slot:prepend-inner>
                                    <v-icon :icon="item.is_protected ? 'mdi-shield-lock' : 'mdi-key-variant'" :color="item.is_protected ? '#FFD700' : 'grey'"></v-icon>
                                </template>
                            </v-text-field>

                            <v-select
                                v-model="item.mode"
                                :items="['single', 'random', 'sequential']"
                                label="MODE"
                                variant="outlined"
                                density="comfortable"
                                hide-details
                                class="gold-input"
                                style="max-width: 180px;"
                                bg-color="#0a0a0a"
                            ></v-select>

                            <div class="d-flex align-center px-4 border-l-gold">
                                <v-switch v-model="item.is_enabled" color="#FFD700" hide-details inset density="compact" class="mr-4 gold-switch"></v-switch>
                                <v-btn
                                    icon="mdi-trash-can-outline"
                                    variant="text"
                                    :color="item.is_protected ? 'grey-darken-3' : 'red-accent-2'"
                                    :disabled="item.is_protected"
                                    @click="confirmDelete(item)"
                                    class="hover-danger"
                                ></v-btn>
                            </div>
                        </div>

                        <div class="value-container">
                            <div class="multi-value-box">
                                <div class="d-flex align-center justify-space-between mb-2">
                                    <div class="text-caption text-gold font-weight-bold d-flex align-center">
                                        <v-icon icon="mdi-code-brackets" size="small" class="mr-2"></v-icon>
                                        {{ item.mode === 'single' ? 'VALUE' : 'VALUES LIST (One per line)' }}
                                    </div>
                                    <div class="text-caption text-grey-darken-1" v-if="item.mode !== 'single'">
                                        Strategy: <span class="text-white">{{ item.mode.toUpperCase() }}</span> selection.
                                    </div>
                                </div>

                                <v-textarea
                                    v-model="item.valueDisplay"
                                    variant="outlined"
                                    bg-color="#050505"
                                    :rows="item.mode === 'single' ? 2 : 5"
                                    auto-grow
                                    hide-details
                                    class="gold-textarea font-mono text-body-2"
                                    :placeholder="getPlaceholder(item.mode)"
                                ></v-textarea>
                            </div>
                        </div>
                    </div>
                </transition-group>

                <v-btn
                    block
                    variant="outlined"
                    color="grey-darken-1"
                    class="mt-8 border-dashed-gold py-6 text-white hover-gold-text"
                    @click="addNewVariable"
                    rounded="xl"
                >
                    <v-icon start color="#FFD700">mdi-plus-circle</v-icon>
                    ADD NEW ENTRY
                </v-btn>
            </div>

        </v-container>
      </v-card-text>

      <div class="vault-footer">
        <v-btn @click="closeDialog" variant="text" color="grey" size="large" class="mr-4 hover-white">Cancel</v-btn>
        <v-btn
            @click="saveChanges"
            color="#FFD700"
            variant="flat"
            :loading="isSaving"
            size="large"
            class="text-black font-weight-black px-8"
            rounded="lg"
        >
            <v-icon start>mdi-content-save</v-icon>
            SAVE CHANGES
        </v-btn>
      </div>

    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useVariablesStore } from '@/store/variables';
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';

const props = defineProps({ modelValue: Boolean });
const emit = defineEmits(['update:modelValue']);

const variablesStore = useVariablesStore();
const uiStore = useUiStore();
const { variables, isLoading } = storeToRefs(variablesStore);
const localVariables = ref([]);
const variablesToDelete = ref([]);
const isSaving = ref(false);

const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

watch(dialog, (isOpen) => {
  if (isOpen) variablesStore.fetchVariables();
});

watch(variables, (newVars) => {
    localVariables.value = (newVars || []).map(v => {
        let displayVal = '';
        let rawVal = v.value;

        if (typeof rawVal === 'object' && rawVal !== null && !Array.isArray(rawVal) && 'value' in rawVal) {
             rawVal = rawVal.value; // Ambil isinya aja
        }

        if (Array.isArray(rawVal)) {
            displayVal = rawVal.join('\n');
        } else if (typeof rawVal === 'object' && rawVal !== null) {
            try {
                displayVal = JSON.stringify(rawVal, null, 2);
            } catch (e) {
                displayVal = String(rawVal);
            }
        } else {
            displayVal = String(rawVal || '');
        }

        return {
            ...JSON.parse(JSON.stringify(v)),
            value: v.value, // Simpan referensi asli (optional)
            valueDisplay: displayVal, // Ini yang ditampilkan bersih di Textarea
            mode: v.mode || 'single',
            isOriginal: true,
            is_protected: v.is_protected || false
        };
    });
    variablesToDelete.value = [];
});

function getPlaceholder(mode) {
    if (mode === 'single') return 'Paste your API Key or Secret here...';
    return 'sk-api-key-1\nsk-api-key-2\nsk-api-key-3';
}

function addNewVariable() {
    localVariables.value.push({
        name: '',
        is_enabled: true,
        is_secret: true,
        mode: 'single',
        value: '',
        valueDisplay: '',
        isOriginal: false
    });
}

async function confirmDelete(item) {
    if (item.is_protected) {
        uiStore.showNotification({ text: 'System variables cannot be deleted.', color: 'warning' });
        return;
    }

    const confirmed = await uiStore.showConfirmation({
        title: 'Delete Variable',
        text: `Are you sure you want to delete "${item.name}"?`,
        confirmText: 'Delete Forever',
        color: 'error',
        icon: 'mdi-delete-forever'
    });

    if (confirmed) {
        if (item.isOriginal) variablesToDelete.value.push(item.name);
        localVariables.value = localVariables.value.filter(v => v !== item);
    }
}

async function saveChanges() {
    isSaving.value = true;
    try {
        for (const name of variablesToDelete.value) await variablesStore.removeVariable(name);

        for (const item of localVariables.value) {
            if (item.name) {
                let finalVal;

                if (item.mode === 'random' || item.mode === 'sequential') {
                    if (item.valueDisplay) {
                        finalVal = item.valueDisplay.split('\n').map(s => s.trim()).filter(s => s !== '');
                    } else {
                        finalVal = [];
                    }
                } else {
                    finalVal = item.valueDisplay;
                }

                const payload = {
                    ...item,
                    value: finalVal
                };
                delete payload.valueDisplay;
                delete payload.isOriginal;

                await variablesStore.saveVariable(item.name, payload);
            }
        }

        uiStore.showNotification({ text: 'Vault updated successfully!', color: 'black bg-gold' }); // Custom class styling via store logic if possible, or standard success
        closeDialog();
    } catch (e) {
        uiStore.showNotification({ text: 'Vault Sync Failed: ' + e.message, color: 'error' });
    } finally {
        isSaving.value = false;
    }
}

function closeDialog() { emit('update:modelValue', false); }
</script>

<style scoped>
/* --- BLACK GOLD THEME --- */
.vault-dialog { background: #000; }
.vault-card { background: #000; color: white; display: flex; flex-direction: column; height: 100vh; }

/* HEADER */
.vault-toolbar {
    background: #050505;
    border-bottom: 1px solid rgba(255, 215, 0, 0.1);
}
.gold-icon-box {
    width: 40px; height: 40px;
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255, 215, 0, 0.05);
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.1);
}
.text-gold { color: #FFD700 !important; }
.border-gold-subtle { border-color: rgba(255, 215, 0, 0.1) !important; opacity: 1; }

/* CONTENT */
.vault-content { flex-grow: 1; overflow-y: auto; background-color: #000; }

/* PANELS */
.gold-panel {
    background: #080808;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.gold-panel:hover {
    border-color: rgba(255, 215, 0, 0.3);
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.05);
}
/* Aksen garis emas di kiri panel */
.gold-panel::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
    background: linear-gradient(to bottom, transparent, #FFD700, transparent);
    opacity: 0.5;
}

.status-indicator {
    width: 6px; height: 6px; border-radius: 50%;
    background: #333; box-shadow: 0 0 5px rgba(0,0,0,0.5);
}
.status-indicator.active { background: #FFD700; box-shadow: 0 0 8px rgba(255, 215, 0, 0.8); }

/* INPUTS (Custom Gold Style) */
.gold-input :deep(.v-field) {
    border-radius: 8px;
    border-color: rgba(255, 255, 255, 0.1) !important;
    background: #0a0a0a !important;
}
.gold-input :deep(.v-field--focused) {
    border-color: #FFD700 !important;
    box-shadow: 0 0 0 1px rgba(255, 215, 0, 0.3);
}
.gold-input :deep(input), .gold-input :deep(.v-select__selection-text) {
    color: #e0e0e0 !important;
    font-family: 'Fira Code', monospace;
}
.gold-input :deep(.v-label) { color: rgba(255, 255, 255, 0.4) !important; }

/* TEXTAREA SPECIFIC */
.multi-value-box {
    background: rgba(255, 215, 0, 0.02);
    padding: 16px;
    border-radius: 8px;
    border: 1px dashed rgba(255, 215, 0, 0.15);
}
.gold-textarea :deep(.v-field__input) {
    color: #FFD700 !important; /* Teks API Key jadi Emas */
    line-height: 1.6;
}

/* UTILS */
.border-dashed-gold { border: 1px dashed rgba(255, 215, 0, 0.2) !important; }
.hover-gold-text:hover { color: #FFD700 !important; border-color: #FFD700 !important; background: rgba(255, 215, 0, 0.05); }
.border-l-gold { border-left: 1px solid rgba(255, 255, 255, 0.1); }
.hover-danger:hover { color: #FF5252 !important; }
.close-btn:hover { background: rgba(255, 215, 0, 0.1); border-color: #FFD700; }
.hover-white:hover { color: white !important; }

.gold-switch :deep(.v-switch__track) { background-color: rgba(255, 255, 255, 0.2) !important; opacity: 1 !important; }
.gold-switch :deep(.v-selection-control--dirty .v-switch__track) { background-color: #FFD700 !important; }
.gold-switch :deep(.v-switch__thumb) { background-color: #000 !important; color: #FFD700 !important; }

/* FOOTER */
.vault-footer {
    padding: 24px 48px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    display: flex; justify-content: flex-end;
    background: #050505;
}

/* SCROLLBAR */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 215, 0, 0.2); border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #000; }

/* TRANSITIONS */
.list-enter-active, .list-leave-active { transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.list-enter-from, .list-leave-to { opacity: 0; transform: translateY(20px); }
.blink { animation: blink-gold 2s infinite; }
@keyframes blink-gold { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
</style>
