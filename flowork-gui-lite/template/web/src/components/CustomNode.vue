//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\CustomNode.vue total lines 405 
//#######################################################################

<template>
  <div
    v-if="manifest"
    :class="['custom-node', nodeClass, { 'is-selected': selected }, nodeExecutionState]"
    :style="nodeStyle"
  >
    <div v-if="isZoomedOut" class="node-lod" :style="lodStyle"></div>

    <div v-else>
      <div class="node-header">
        <div class="icon-container">
          <img
            v-if="manifest.icon_file && !iconLoadError"
            :src="iconUrl"
            class="node-img-icon"
            alt="icon"
            @error="iconLoadError = true"
          />
          <v-icon v-else :icon="getDefaultIcon" size="small" class="node-icon"></v-icon>
        </div>
        <span v-if="componentType !== 'triggers'" class="node-name">{{ loc(manifest.name) }}</span>
      </div>

      <div v-if="componentType === 'triggers'" class="node-label-trigger">
        {{ loc(manifest.name) }}
      </div>

      <div v-if="manifest.id === 'agent_host'" class="agent-monitor">
        <v-textarea
          :model-value="agentLog"
          variant="solo-filled"
          flat
          readonly
          no-resize
          rows="4"
          placeholder="Agent thoughts and actions..."
        ></v-textarea>
      </div>

      <div v-if="manifest.id === 'prompt_receiver_module'" class="receiver-monitor">
         <div class="terminal-line">> READY_TO_RECEIVE_</div>
         <div class="terminal-line blink">_</div>
      </div>
    </div>

    <div v-if="inputPorts.length > 0" class="handle-wrapper handle-wrapper-left">
      <div v-for="port in inputPorts" :key="port.name" class="handle-item port-input">
        <Handle :id="port.name" type="target" :position="Position.Left" />
      </div>
    </div>

    <div v-if="outputPortsRight.length > 0" class="handle-wrapper handle-wrapper-right">
       <div v-for="port in outputPortsRight" :key="port.name" class="handle-item port-output">
        <Handle :id="port.name" type="source" :position="Position.Right">
            <v-tooltip :text="loc(port.tooltip || port.display_name)" location="end">
                <template v-slot:activator="{ props }">
                    <v-icon v-bind="props" size="small" :color="getOutputPortStyle(port.name).color">{{ getOutputPortStyle(port.name).icon }}</v-icon>
                </template>
            </v-tooltip>
        </Handle>
      </div>
    </div>

    <div v-if="outputPortsTop.length > 0" class="handle-wrapper handle-wrapper-top">
       <div v-for="port in outputPortsTop" :key="port.name" class="handle-item port-output">
        <Handle :id="port.name" type="source" :position="Position.Top">
            <v-tooltip :text="loc(port.tooltip || port.display_name)" location="top">
                 <template v-slot:activator="{ props }">
                    <v-icon v-bind="props" size="small" :color="getOutputPortStyle(port.name).color">{{ getOutputPortStyle(port.name).icon }}</v-icon>
                 </template>
            </v-tooltip>
        </Handle>
      </div>
    </div>

    <div v-if="manifest.tool_ports && manifest.tool_ports.length > 0" class="handle-wrapper handle-wrapper-bottom">
      <div v-for="port in manifest.tool_ports" :key="port.name" class="handle-item port-tool">
         <Handle :id="port.name" type="target" :position="Position.Bottom">
             <v-tooltip :text="loc(port.tooltip || port.display_name)" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-icon v-bind="props" size="small" class="handle-icon-bottom">{{ getToolPortIcon(port.name) }}</v-icon>
                </template>
             </v-tooltip>
        </Handle>
        <span class="handle-label-bottom">{{ port.display_name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { useWorkflowStore } from '@/store/workflow';
import { useComponentStore } from '@/store/components';
import { storeToRefs } from 'pinia';
import { getComponentIconUrl } from '@/api';
import { useLocaleStore } from '@/store/locale';

const props = defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  selected: { type: Boolean, required: true },
  data: { type: Object, required: true },
  isZoomedOut: { type: Boolean, default: false },
});

const workflowStore = useWorkflowStore();
const localeStore = useLocaleStore();
const componentStore = useComponentStore();


const { executionStatus } = storeToRefs(workflowStore);
const { loc } = storeToRefs(localeStore);

const manifest = computed(() => {
    if (!props.data?.moduleId) return {};
    const component = componentStore.findComponentById(props.data.moduleId);
    return component?.manifest || {};
});

const componentType = computed(() => props.data?.componentType);
const moduleId = computed(() => props.data?.moduleId);
const agentLog = ref('Agent is standing by...');
const iconLoadError = ref(false);


watch(() => props.data.moduleId, () => {
  iconLoadError.value = false;
});

const nodeStyle = computed(() => {
  const color = props.data?.color || manifest.value.display_properties?.color;
  if (color) {
    return {
      borderColor: color,
      boxShadow: `0 0 12px ${color}`
    };
  }
  return {};
});

const lodStyle = computed(() => {
    return {
        backgroundColor: props.data?.color || manifest.value.display_properties?.color || '#6c757d'
    };
});

const iconUrl = computed(() => {
  if (manifest.value.icon_file && moduleId.value && componentType.value) {
    return getComponentIconUrl(componentType.value, moduleId.value);
  }
  return '';
});

const getDefaultIcon = computed(() => {
    if (componentType.value === 'triggers') return 'mdi-flash';
    if (manifest.value.id === 'agent_host') return 'mdi-robot-outline';
    if (componentType.value === 'tools') return 'mdi-hammer-wrench';
    return 'mdi-cube-outline';
});

const inputPorts = computed(() => {
    if (componentType.value === 'tools' || componentType.value === 'triggers') {
        return [];
    }
    if (manifest.value.input_ports && manifest.value.input_ports.length > 0) {
        return manifest.value.input_ports;
    }
    if (manifest.value.requires_input === false) {
        return [];
    }
    return [{ name: 'input', display_name: '' }];
});

const outputPorts = computed(() => manifest.value.output_ports || []);

const outputPortsRight = computed(() => {
    if (componentType.value === 'triggers') {
        return [
            { name: 'output', display_name: 'Start' },
            { name: 'error', display_name: 'Error' }
        ];
    }
    return outputPorts.value.filter(p => !p.port_position || p.port_position === 'right');
});

const outputPortsTop = computed(() => {
    return outputPorts.value.filter(p => p.port_position === 'top');
});


const getToolPortIcon = (portName) => {
  if (portName.includes('brain')) return 'mdi-brain';
  if (portName.includes('prompt')) return 'mdi-text-box-outline';
  if (portName.includes('tool')) return 'mdi-wrench';
  return 'mdi-power-plug';
};

const getOutputPortStyle = (portName) => {
  const name = portName.toLowerCase();
  if (name.includes('success') || name.includes('true') || name.includes('output')) {
    return { icon: 'mdi-check-circle-outline', color: '#39ff14' };
  }
  if (name.includes('error') || name.includes('false')) {
    return { icon: 'mdi-alert-circle-outline', color: '#ff5252' };
  }
  return { icon: 'mdi-chevron-right', color: '#a59dff' };
};

const nodeExecutionState = computed(() => {
    const statusData = executionStatus.value[props.id];
    if (!statusData) return '';

    const status = statusData.status;
    const timestamp = statusData.timestamp;

    if (status === 'SUCCESS' || status === 'ERROR' || status === 'FAILED') {
        setTimeout(() => {
            if (executionStatus.value[props.id] && executionStatus.value[props.id].timestamp === timestamp) {
                delete executionStatus.value[props.id];
            }
        }, 2000);
    }

    if (status === 'RUNNING') return 'is-executing';
    if (status === 'SUCCESS') return 'is-success';
    if (status === 'ERROR' || status === 'FAILED') return 'is-error';
    return '';
});

const nodeClass = computed(() => {
  const classes = [];
  if (componentType.value === 'triggers') {
    classes.push('node-trigger');
  } else if (manifest.value.id === 'agent_host') {
    classes.push('node-agent-host');
  } else if (manifest.value.id === 'prompt_receiver_module') {
    classes.push('node-prompt-receiver');
  } else if (componentType.value === 'tools') {
    classes.push('node-tool');
  } else {
    switch (manifest.value.type?.toUpperCase()) {
        case 'ACTION': classes.push('node-action'); break;
        case 'CONTROL_FLOW': classes.push('node-control-flow'); break;
        case 'LOGIC': classes.push('node-logic'); break;
        case 'PLUGIN': classes.push('node-plugin'); break;
        default: classes.push('node-default-style'); break;
    }
  }
  return classes;
});
</script>

<style scoped>
/* (COMMENT) ... style lama tetap ada ... */
.node-lod {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  opacity: 0.8;
}

.custom-node {
  background: var(--bg-dark-panel);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  font-family: 'Exo 2', sans-serif;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  position: relative;
  padding: 0;
}
.custom-node.is-selected { border-color: var(--neon-blue); box-shadow: 0 0 20px var(--neon-blue); }
.node-header { display: flex; align-items: center; font-weight: 600; font-size: 0.9rem; padding: 8px 12px; }
.node-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.icon-container { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; margin-right: 8px; }
.node-img-icon { max-width: 20px; max-height: 20px; object-fit: contain; }
.node-icon { color: var(--neon-blue); }
.handle-wrapper { position: absolute; display: flex; }
.handle-wrapper-left { left: 0; top: 0; bottom: 0; flex-direction: column; justify-content: center; transform: translateX(-50%); }
.handle-wrapper-right { right: 0; top: 0; bottom: 0; flex-direction: column; justify-content: center; transform: translateX(50%); gap: 8px; }
.handle-wrapper-bottom { bottom: 0; left: 0; right: 0; padding-bottom: 8px; justify-content: space-evenly; }
.handle-wrapper-top { top: 0; left: 0; right: 0; justify-content: center; transform: translateY(-50%); }
.handle-item { display: flex; align-items: center; }
.handle-label-bottom { font-size: 0.65rem; color: var(--text-secondary); margin-top: 2px; }
.handle-wrapper-bottom .handle-item { flex-direction: column; }
:deep(.vue-flow__handle) {
  width: 18px;
  height: 18px;
  background: #777;
  border: none;
  transition: all 0.2s ease;
  z-index: 10;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
:deep(.vue-flow__handle:hover) { transform: scale(1.2); background: var(--neon-blue); }
.port-input :deep(.vue-flow__handle) { border-radius: 50%; }
.port-output :deep(.vue-flow__handle) { border-radius: 50%; background: var(--bg-dark-panel); border: 1px solid #777; }
.port-output :deep(.vue-flow__handle:hover) { border-color: var(--neon-blue); }
.port-tool :deep(.vue-flow__handle) { border-radius: 3px; background: var(--bg-dark-panel); border: 1px solid #ffc400; width: 16px; height: 16px; }
.handle-icon-bottom { color: #ffc400; font-size: 0.8rem !important; }
.node-default-style { width: 220px; border-radius: 6px; }
.node-action { width: 220px; border-radius: 50px; }
.node-action .node-header { padding: 10px 18px; }
.node-control-flow { width: 150px; height: 130px; clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%); display: flex; align-items: center; justify-content: center; text-align: center; }
.node-control-flow .node-header { flex-direction: column; }
.node-logic { width: 220px; border-radius: 6px; background: radial-gradient(circle at 50% 50%, #4a2f6c, var(--bg-dark-panel) 70%); border-color: var(--neon-purple); }
.node-plugin { width: 220px; border-radius: 6px; border-style: dashed; border-color: rgba(255, 255, 255, 0.4); }
.node-tool { width: 240px; border-radius: 4px; border-left: 4px solid #ffc400; }
.node-agent-host { width: 320px; min-height: 180px; border-radius: 8px; border-left: 4px solid var(--neon-purple); }
.agent-monitor { padding: 0 8px 8px 8px; }
.agent-monitor :deep(.v-textarea .v-field__input) { font-family: 'Courier New', monospace; font-size: 0.75rem; line-height: 1.4; color: var(--text-secondary) !important; }
.agent-monitor :deep(.v-field) { background-color: rgba(0,0,0,0.2) !important; }

/* [NEW] Style Khusus Prompt Receiver */
.node-prompt-receiver {
    width: 260px;
    border-radius: 4px;
    border: 1px solid var(--neon-cyan);
    background: linear-gradient(135deg, rgba(0,255,255,0.05) 0%, rgba(0,0,0,0.9) 100%);
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
}
.node-prompt-receiver .node-header {
    background: rgba(0, 255, 255, 0.1);
    border-bottom: 1px solid rgba(0, 255, 255, 0.2);
    color: var(--neon-cyan);
}
.node-prompt-receiver .node-icon {
    color: var(--neon-cyan) !important;
}
.receiver-monitor {
    padding: 10px;
    font-family: 'Courier New', monospace;
    font-size: 0.7rem;
    color: #a7f3d0;
}
.terminal-line { margin-bottom: 2px; }
.blink { animation: blinker 1s linear infinite; }
@keyframes blinker { 50% { opacity: 0; } }

.node-trigger {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border-color: var(--neon-cyan);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  animation: pulse-shadow-cyan 2.5s infinite;
}
.node-trigger .handle-wrapper-right {
    justify-content: space-evenly;
}
.node-trigger .node-header {
  padding: 0;
  margin-bottom: 4px;
}
.node-trigger .icon-container {
  margin-right: 0;
}
.node-trigger .node-icon {
  font-size: 2rem !important;
  color: var(--neon-cyan);
}
.node-trigger .node-label-trigger {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  line-height: 1.2;
  word-break: break-word;
  max-width: 90%;
}
.is-executing { border-color: #39ff14; animation: pulse-shadow-green 1.5s infinite; }
.is-success { border-color: #39ff14; animation: flash-green 0.5s ease-out; }
.is-error { border-color: #ff5252; animation: pulse-shadow-red 1.5s infinite; }
@keyframes pulse-shadow-green { 0% { box-shadow: 0 0 10px #39ff14; } 50% { box-shadow: 0 0 25px #39ff14; } 100% { box-shadow: 0 0 10px #39ff14; } }
@keyframes pulse-shadow-red { 0% { box-shadow: 0 0 10px #ff5252; } 50% { box-shadow: 0 0 25px #ff5252; } 100% { box-shadow: 0 0 10px #ff5252; } }
@keyframes flash-green {
  0% { box-shadow: 0 0 30px #39ff14; }
  100% { box-shadow: 0 0 0px transparent; }
}
</style>

<style>
.vue-flow__node-default {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  width: auto !important;
  height: auto !important;
}
</style>
