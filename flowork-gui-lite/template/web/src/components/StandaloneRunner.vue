//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\StandaloneRunner.vue total lines 377 
//#######################################################################

<template>
  <v-dialog v-model="dialog" persistent max-width="900px" scrollable>
    <v-card class="runner-card" v-if="componentData">
      <v-card-title class="panel-title d-flex align-center">
        <v-img
          v-if="componentData.manifest.icon_file"
          :src="getComponentIconUrl(componentData.componentType, componentData.id)"
          class="tool-icon mr-3"
          width="24"
          height="24"
          cover
        ></v-img>
        <v-icon v-else class="tool-icon mr-3" :icon="getToolIcon(componentData)"></v-icon>
        <span class="orbitron-font">{{ loc(componentData.name) }}</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" size="small" @click="close"></v-btn>
      </v-card-title>

      <v-tabs v-model="activeTab" bg-color="#161625" color="cyan" grow>
        <v-tab value="config">
          <v-icon start>mdi-tune</v-icon>
          Configuration
        </v-tab>
        <v-tab value="log">
          <v-icon start>mdi-console</v-icon>
          Execution Log
        </v-tab>
      </v-tabs>

      <v-divider></v-divider>

      <v-card-text class="pa-0">
        <v-window v-model="activeTab" class="runner-window">
          <v-window-item value="config">
            <div class="pa-5">
              <p class="text-caption text-grey-lighten-1 mb-6">{{ loc(componentData.manifest.description) }}</p>

              <div v-if="nodeProperties.length === 0" class="text-center text-caption text-grey mt-4">
                This node has no configurable properties.
              </div>

              <div v-for="prop in nodeProperties" :key="prop.id" class="prop-item">
                <CronEditor
                  v-if="prop.type === 'cron_editor'"
                  :label="loc(prop.label)"
                  :hint="loc(prop.description)"
                  v-model="configValues[prop.id]"
                />
                <DynamicKeyValueEditor
                  v-else-if="prop.type === 'dynamic_key_value_editor'"
                  :label="loc(prop.label)"
                  :hint="loc(prop.description)"
                  v-model="configValues[prop.id]"
                />
                <v-text-field
                  v-else-if="['string', 'integer', 'float', 'folderpath'].includes(prop.type)"
                  :label="loc(prop.label)"
                  :type="['integer', 'float'].includes(prop.type) ? 'number' : 'text'"
                  v-model="configValues[prop.id]"
                  variant="outlined"
                  density="compact"
                  :hint="loc(prop.description)"
                  persistent-hint
                ></v-text-field>
                <v-switch
                  v-else-if="prop.type === 'boolean'"
                  :label="loc(prop.label)"
                  v-model="configValues[prop.id]"
                  color="cyan"
                  inset
                  :messages="loc(prop.description)"
                ></v-switch>
                <v-textarea
                  v-else-if="prop.type === 'textarea'"
                  :label="loc(prop.label)"
                  v-model="configValues[prop.id]"
                  variant="outlined"
                  density="compact"
                  rows="3"
                  :hint="loc(prop.description)"
                  persistent-hint
                ></v-textarea>
                <div v-else-if="prop.type === 'code'" class="code-editor-wrapper">
                  <label class="v-label text-caption">{{ loc(prop.label) }}</label>
                  <v-textarea
                    class="code-editor"
                    v-model="configValues[prop.id]"
                    variant="outlined"
                    density="compact"
                    rows="10"
                    :hint="loc(prop.description)"
                    persistent-hint
                  ></v-textarea>
                </div>
                <v-select
                  v-else-if="prop.type === 'enum'"
                  :label="loc(prop.label)"
                  :items="prop.options"
                  v-model="configValues[prop.id]"
                  variant="outlined"
                  density="compact"
                  :hint="loc(prop.description)"
                  persistent-hint
                ></v-select>
                <FolderPairList
                  v-else-if="prop.type === 'list'"
                  :label="loc(prop.label)"
                  :hint="loc(prop.description)"
                  v-model="configValues[prop.id]"
                />
              </div>
            </div>
          </v-window-item>

          <v-window-item value="log" class="fill-height">
            <LogPanelContent />
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-divider></v-divider>
      <v-card-actions class="pa-4">
        <v-chip
          v-if="jobStatus"
          :color="jobStatus.color"
          label
          size="small"
          class="mr-4"
        >
          <v-icon start :icon="jobStatus.icon"></v-icon>
          {{ jobStatus.text }}
        </v-chip>
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          @click="handleExecute('SIMULATE')"
          :disabled="isExecuting"
          :loading="isSimulating"
        >Simulate</v-btn>
        <v-btn
          v-if="!isExecuting"
          color="cyan"
          variant="flat"
          class="action-button"
          @click="handleExecute('EXECUTE')"
          :loading="isRunning"
          :disabled="!selectedComponent"
        >
          <v-icon start>mdi-play</v-icon>
          Run
        </v-btn>
        <v-btn
          v-else
          color="error"
          variant="flat"
          class="action-button"
          @click="handleStop"
          :loading="isStopping"
        >
          <v-icon start>mdi-stop</v-icon>
          Stop
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useSocketStore } from '@/store/socket';
import { useLogStore } from '@/store/logs';
import { useLocaleStore } from '@/store/locale';
import { useUiStore } from '@/store/ui';
import { getComponentIconUrl } from '@/api';
import { v4 as uuidv4 } from 'uuid';
import LogPanelContent from '@/components/panels/LogPanelContent.vue'; // Kita akan buat ini selanjutnya
import CronEditor from './custom-properties/CronEditor.vue';
import DynamicKeyValueEditor from './custom-properties/DynamicKeyValueEditor.vue';
import FolderPairList from './custom-properties/FolderPairList.vue';

const props = defineProps({
  modelValue: Boolean, // for v-model
  componentData: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:modelValue']);

const socketStore = useSocketStore();
const logStore = useLogStore();
const localeStore = useLocaleStore();
const uiStore = useUiStore();
const { loc } = localeStore;

const activeTab = ref('config');
const configValues = ref({});
const currentJobId = ref(null);
const jobStatus = ref(null); // { text, color, icon }

const isRunning = ref(false);
const isSimulating = ref(false);
const isStopping = ref(false);

const isExecuting = computed(() => isRunning.value || isSimulating.value);

const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const nodeProperties = computed(() => {
  return props.componentData?.manifest?.properties || [];
});

watch(() => props.componentData, (newComponent) => {
  if (newComponent) {
    logStore.clearLogs();
    activeTab.value = 'config';
    jobStatus.value = null;
    currentJobId.value = null;

    const defaults = {};
    (newComponent.manifest?.properties || []).forEach(prop => {
      if (prop.default !== undefined) {
        let defaultValue = prop.default;
        if (prop.type === 'integer' || prop.type === 'float') {
            defaultValue = Number(defaultValue);
        } else if (prop.type === 'boolean') {
            defaultValue = String(defaultValue).toLowerCase() === 'true';
        } else if (prop.type === 'list' && !Array.isArray(defaultValue)) {
            defaultValue = [];
        }
        defaults[prop.id] = defaultValue;
      } else {
        defaults[prop.id] = null;
      }
    });
    configValues.value = defaults;
  }
}, { immediate: true });

async function handleExecute(mode) {
  if (mode === 'EXECUTE') isRunning.value = true;
  if (mode === 'SIMULATE') isSimulating.value = true;

  logStore.clearLogs();
  activeTab.value = 'log'; // Otomatis pindah ke tab log
  const newJobId = `quickjob-${uuidv4()}`;
  currentJobId.value = newJobId;
  jobStatus.value = { text: 'Running...', color: 'info', icon: 'mdi-autorenew' };

  try {
    await socketStore.sendMessage({
      type: 'execute_standalone_node',
      job_id: newJobId,
      node_data: {
        module_id: props.componentData.id,
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
        isStopping.value = false; // <-- PERBAIKAN DARI TEMUAN 4
    }
}

watch(() => logStore.executionLogs, (logs) => {
    if (!currentJobId.value) return;

    const statusLogs = logs.filter(l => l.workflow_context_id === currentJobId.value && l.source === 'Executor' && l.message.startsWith('Workflow finished'));
    if (statusLogs.length > 0) {
        const lastStatusMsg = statusLogs[statusLogs.length - 1].message;
        if (lastStatusMsg.includes('SUCCEEDED')) {
            jobStatus.value = { text: 'Succeeded', color: 'success', icon: 'mdi-check-circle-outline' };
        } else if (lastStatusMsg.includes('FAILED')) {
            jobStatus.value = { text: 'Failed', color: 'error', icon: 'mdi-alert-circle-outline' };
        } else if (lastStatusMsg.includes('STOPPED')) {
            jobStatus.value = { text: 'Stopped', color: 'warning', icon: 'mdi-stop-circle-outline' };
        }
        isRunning.value = false;
        isSimulating.value = false;
        isStopping.value = false;
        currentJobId.value = null; // Selesaikan job
    }
}, { deep: true });

function close() {
    if (isExecuting.value) {
        if (confirm("A job is still running. Are you sure you want to close? The job will continue in the background.")) {
            dialog.value = false;
        }
    } else {
        dialog.value = false;
    }
}

function getToolIcon(item) {
  if (item.componentType === 'modules') return 'mdi-cog-outline';
  if (item.componentType === 'plugins') return 'mdi-power-plug-outline';
  if (item.componentType === 'tools') return 'mdi-hammer-wrench';
  return 'mdi-cube-outline';
}
</script>

<style scoped>
.runner-card {
  background-color: #2a2a4a;
  border: 1px solid rgba(0, 245, 255, 0.3);
  display: flex;
  flex-direction: column;
  height: 80vh; /* Make dialog taller */
}
.panel-title {
  color: #00f5ff !important;
  font-family: 'Orbitron', monospace;
  font-weight: 700;
  font-size: 1.1rem;
  text-shadow: 0 0 4px rgba(0, 245, 255, 0.5);
}
.tool-icon {
    margin-right: 12px;
    color: #00f5ff;
    width: 24px;
    height: 24px;
    object-fit: contain;
}
.runner-window {
    height: 100%;
}
.v-card-text {
    flex-grow: 1;
    overflow-y: auto;
}
.prop-item {
  margin-bottom: 24px;
}
.code-editor-wrapper .v-label {
    margin-bottom: 4px;
    display: block;
}
.code-editor :deep(textarea) {
  font-family: 'Courier New', Courier, monospace !important;
  font-size: 0.9rem;
  line-height: 1.6;
}
.action-button {
  font-weight: bold;
  color: #010c03 !important;
}
</style>
