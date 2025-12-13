//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\FloatingControls.vue total lines 357 
//#######################################################################

<template>
  <div class="floating-footer-container">
    <div class="cockpit-panel">

      <div class="row-top">
        <div class="d-flex align-center gap-3">
          <div class="status-indicator online">
            <div class="dot"></div> Primary Engine
          </div>
          <div class="status-text">CPU 0% • RAM 14%</div>
        </div>

        <v-spacer></v-spacer>

        <div class="utility-group">
          <button class="util-btn" @click="handlePresetSave" title="Save Workflow">
            <v-icon icon="mdi-content-save-outline" size="14"></v-icon> SAVE
          </button>
          <div class="divider"></div>
          <button class="util-btn" title="Layout Settings">
            <v-icon icon="mdi-view-dashboard-outline" size="14"></v-icon> LAYOUT
          </button>
          <div class="divider"></div>
          <button class="util-btn text-hover-red" title="Clear Canvas">
            <v-icon icon="mdi-trash-can-outline" size="14"></v-icon> CLEAR
          </button>
        </div>
      </div>

      <div class="row-bottom">

        <div class="preset-container">
          <v-icon icon="mdi-flash" size="16" color="yellow-darken-1" class="mr-2"></v-icon>
          <div class="select-wrapper">
            <select v-model="currentPresetName" class="stealth-select" @change="handlePresetLoad($event.target.value)">
              <option value="" disabled selected>Select Workflow...</option>
              <option v-for="p in presetList" :key="p" :value="p">{{ p }}</option>
            </select>
            <v-icon icon="mdi-chevron-down" size="12" class="select-arrow"></v-icon>
          </div>
        </div>

        <div class="config-cluster">
          <div class="config-item" :class="{ active: loopEnabled }">
            <div class="config-label" @click="loopEnabled = !loopEnabled">
              RPT
              <div class="indicator"></div>
            </div>
            <input v-if="loopEnabled" v-model="loopTimes" type="number" class="nano-input" placeholder="#">
          </div>

          <div class="config-item" :class="{ active: delayEnabled }">
            <div class="config-label" @click="delayEnabled = !delayEnabled">
              DLY
              <div class="indicator"></div>
            </div>
            <div v-if="delayEnabled" class="d-flex align-center">
              <input type="number" class="nano-input" placeholder="Sec">
            </div>
          </div>
        </div>

        <div class="action-group">
          <button class="btn-sim" @click="handleExecution('SIMULATE')" title="Simulate">
            <v-icon icon="mdi-flask-outline" size="18"></v-icon>
          </button>
          <button class="btn-run" @click="handleExecution('EXECUTE')">
            <v-icon icon="mdi-play" size="18" class="mr-1"></v-icon> RUN FLOW
          </button>
        </div>

        <div class="view-tabs">
          <button :class="{ active: activeTab === 'logic' }" @click="setDesignerMode('logic')">LOGIC</button>
          <button :class="{ active: activeTab === 'data' }" @click="setDesignerMode('data')">DATA</button>
          <button :class="{ active: activeTab === 'logs' }" @click="setRightPanel('log')">LOGS</button>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useWorkflowStore } from '@/store/workflow';
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';
import { getPresets } from '@/api';

const workflowStore = useWorkflowStore();
const uiStore = useUiStore();
const { currentPresetName } = storeToRefs(workflowStore);
const { loadWorkflow, saveCurrentWorkflow } = workflowStore;

const presetList = ref([]);
const presetsLoading = ref(false);
const loopEnabled = ref(false);
const loopTimes = ref(1);
const delayEnabled = ref(false);
const activeTab = ref('logic');

watch(() => uiStore.designerMode, (newMode) => {
  if (['logic', 'data'].includes(newMode) && !uiStore.activeRightPanel) {
    activeTab.value = newMode;
  }
});
watch(() => uiStore.activeRightPanel, (newPanel) => {
  if (newPanel === 'log') activeTab.value = 'logs';
  else activeTab.value = uiStore.designerMode;
});

function setDesignerMode(mode) {
  uiStore.setDesignerMode(mode);
  uiStore.closeRightPanel();
}
function setRightPanel(panel) {
  uiStore.setActiveRightPanel(panel);
}
function handleExecution(mode) {
    const execConfig = { loop: loopEnabled.value ? loopTimes.value : 1 };
    if (mode === 'SIMULATE') workflowStore.simulateCurrentWorkflow(execConfig);
    else workflowStore.executeCurrentWorkflow(execConfig);
}
function handlePresetLoad(val) { if(val) loadWorkflow(val); }
async function handlePresetSave() {
  const newName = prompt("Save preset as:", currentPresetName.value || '');
  if (newName?.trim()) await saveCurrentWorkflow(newName.trim());
}

onMounted(async () => {
  presetsLoading.value = true;
  try {
    const presets = await getPresets();
    presetList.value = presets.map(p => p.name);
  } catch (error) { console.error(error); }
  finally { presetsLoading.value = false; }
});
</script>

<style scoped>
/* === CORE CONTAINER === */
.floating-footer-container {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 95%;
  max-width: 880px;
  z-index: 9999;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

.cockpit-panel {
  background: #0F0F11; /* Super Dark */
  border: 1px solid #2A2A2E;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.7);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* === ROW 1: UTILITY (28px) === */
.row-top {
  height: 28px;
  background: #18181B;
  border-bottom: 1px solid #252528;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 0.65rem;
  letter-spacing: 0.5px;
}

.status-indicator {
  color: #4CAF50;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
}
.status-indicator .dot {
  width: 6px;
  height: 6px;
  background: #4CAF50;
  border-radius: 50%;
  box-shadow: 0 0 5px #4CAF50;
}
.status-text { color: #666; font-weight: 500; }

.utility-group { display: flex; align-items: center; height: 100%; }
.util-btn {
  background: transparent;
  border: none;
  color: #777;
  height: 100%;
  padding: 0 8px;
  cursor: pointer;
  font-size: 0.65rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}
.util-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }
.util-btn.text-hover-red:hover { color: #FF5252; }
.utility-group .divider { width: 1px; height: 12px; background: #333; }

/* === ROW 2: ACTIONS (48px) === */
.row-bottom {
  height: 48px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  gap: 8px;
  background: #111;
}

/* 1. Preset (Stealth) */
.preset-container {
  flex: 1;
  display: flex;
  align-items: center;
  background: #1A1A1D;
  border: 1px solid #333;
  border-radius: 6px;
  height: 32px;
  padding: 0 8px;
  max-width: 200px;
}
.select-wrapper { position: relative; width: 100%; display: flex; align-items: center; }
.stealth-select {
  width: 100%;
  background: transparent;
  border: none;
  color: #eee;
  font-size: 0.75rem;
  font-weight: 500;
  appearance: none; /* Hilangkan panah bawaan browser */
  outline: none;
  cursor: pointer;
}
.select-arrow { position: absolute; right: 0; pointer-events: none; color: #666; }
.stealth-select option { background: #222; }

/* 2. Config Cluster (Loop/Delay) */
.config-cluster {
  display: flex;
  gap: 4px;
  background: #000;
  border: 1px solid #222;
  border-radius: 6px;
  padding: 3px;
  height: 32px;
  align-items: center;
}
.config-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px;
  border-radius: 4px;
  transition: background 0.2s;
}
.config-item.active { background: rgba(0, 229, 255, 0.1); border: 1px solid rgba(0, 229, 255, 0.2); }
.config-label {
  color: #555;
  font-size: 0.65rem;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 3px;
}
.config-item.active .config-label { color: #00E5FF; }
.config-label .indicator { width: 4px; height: 4px; background: #333; border-radius: 50%; }
.config-item.active .indicator { background: #00E5FF; box-shadow: 0 0 4px #00E5FF; }

.nano-input {
  width: 30px;
  background: #111;
  border: 1px solid #444;
  color: #00E5FF;
  font-size: 0.7rem;
  text-align: center;
  border-radius: 3px;
  outline: none;
  height: 18px;
}

/* 3. Execution Buttons */
.action-group { display: flex; gap: 4px; }
.btn-sim {
  height: 32px; width: 32px;
  background: #1A1A1D;
  border: 1px solid #333;
  color: #888;
  border-radius: 6px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.btn-sim:hover { color: #00E5FF; border-color: #00E5FF; }

.btn-run {
  height: 32px;
  padding: 0 16px;
  background: #00C853; /* Hijau Neon */
  border: none;
  border-radius: 6px;
  color: #000;
  font-weight: 800;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: flex; align-items: center;
  box-shadow: 0 0 10px rgba(0, 200, 83, 0.2);
  transition: transform 0.1s, box-shadow 0.2s;
}
.btn-run:hover { background: #00E676; box-shadow: 0 0 15px rgba(0, 200, 83, 0.4); transform: translateY(-1px); }
.btn-run:active { transform: translateY(1px); }

/* 4. View Tabs */
.view-tabs {
  display: flex;
  background: #1A1A1D;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 2px;
  height: 32px;
}
.view-tabs button {
  background: transparent;
  border: none;
  color: #555;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.view-tabs button:hover { color: #999; }
.view-tabs button.active {
  background: #333;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
</style>
