//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\PropertiesPanel.vue total lines 264 
//#######################################################################

<template>
  <div class="properties-container">
    <div v-if="!selectedNode" class="properties-empty-state">
      <v-icon icon="mdi-cursor-default-click-outline" size="48" class="mb-4 text-grey"></v-icon>
      <div class="text-h6 text-grey">Select a Node</div>
      <div class="text-body-2 text-grey-lighten-1">Click on a node in the canvas to view and edit its properties here.</div>
    </div>
    <div v-else class="properties-form">
      <div class="node-title">
        <v-icon icon="mdi-cog" class="node-icon-title mr-3"></v-icon>
        {{ loc(nodeManifest.name) }}
        <v-spacer></v-spacer>
        <v-btn
          :icon="uiStore.isPropertiesPanelPinned ? 'mdi-pin' : 'mdi-pin-outline'"
          :color="uiStore.isPropertiesPanelPinned ? 'cyan' : 'grey'"
          variant="text"
          size="small"
          @click="uiStore.togglePropertiesPanelPin"
        ></v-btn>
        <v-btn icon="mdi-close" variant="text" size="small" @click="workflowStore.clearSelectedNode"></v-btn>
      </div>
      <div class="node-description">
        {{ loc(nodeManifest.description) }}
      </div>

      <v-divider class="my-4"></v-divider>

      <div class="config-section">
        <div class="config-title">CONFIGURATION</div>

        <div v-if="nodeUiSchema.length > 0">
           <DynamicFormRenderer
              :schema="nodeUiSchema"
              :model-value="nodeConfigValues"
              @update:modelValue="handleDynamicFormUpdate"
           />
        </div>

        <div v-else>
            <div v-if="nodeProperties.length === 0" class="text-center text-caption text-grey mt-4">
              This node has no configurable properties.
            </div>

            <div v-for="prop in nodeProperties" :key="prop.id" class="prop-item">

              <CronEditor
                v-if="prop.type === 'cron_editor'"
                :label="loc(prop.label)"
                :hint="loc(prop.description)"
                :model-value="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
              />

              <DynamicKeyValueEditor
                v-else-if="prop.type === 'dynamic_key_value_editor'"
                :label="loc(prop.label)"
                :hint="loc(prop.description)"
                :model-value="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
              />

              <v-text-field
                v-else-if="['string', 'integer', 'float', 'folderpath'].includes(prop.type)"
                :label="loc(prop.label)"
                :type="['integer', 'float'].includes(prop.type) ? 'number' : 'text'"
                :step="prop.type === 'float' ? '0.1' : '1'"
                v-model="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
                variant="outlined"
                density="compact"
                :hint="loc(prop.description)"
                persistent-hint
                class="hacker-input"
              ></v-text-field>

              <v-switch
                v-else-if="prop.type === 'boolean'"
                :label="loc(prop.label)"
                v-model="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
                color="cyan"
                inset
                :messages="loc(prop.description)"
              ></v-switch>

              <v-textarea
                v-else-if="prop.type === 'textarea'"
                :label="loc(prop.label)"
                v-model="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
                variant="outlined"
                density="compact"
                rows="3"
                :hint="loc(prop.description)"
                persistent-hint
                class="hacker-input"
              ></v-textarea>

              <div v-else-if="prop.type === 'code'" class="code-editor-wrapper">
                <label class="v-label text-caption">{{ loc(prop.label) }}</label>
                <v-textarea
                  class="code-editor hacker-input"
                  v-model="nodeConfigValues[prop.id]"
                  @update:modelValue="updateConfig(prop.id, $event)"
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
                v-model="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
                variant="outlined"
                density="compact"
                :hint="loc(prop.description)"
                persistent-hint
                class="hacker-input"
              ></v-select>

              <FolderPairList
                v-else-if="prop.type === 'list'"
                :label="loc(prop.label)"
                :hint="loc(prop.description)"
                :model-value="nodeConfigValues[prop.id]"
                @update:modelValue="updateConfig(prop.id, $event)"
              />

            </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useWorkflowStore } from '@/store/workflow';
import { useLocaleStore } from '@/store/locale';
import { useUiStore } from '@/store/ui';
import { useComponentStore } from '@/store/components';
import FolderPairList from './custom-properties/FolderPairList.vue';
import CronEditor from './custom-properties/CronEditor.vue';
import DynamicKeyValueEditor from '@/components/custom-properties/DynamicKeyValueEditor.vue';
import DynamicFormRenderer from '@/components/DynamicFormRenderer.vue'; // NEW INJECTOR

const workflowStore = useWorkflowStore();
const localeStore = useLocaleStore();
const uiStore = useUiStore();
const componentStore = useComponentStore();

const { selectedNode } = storeToRefs(workflowStore);
const { loc } = storeToRefs(localeStore);

const nodeManifest = computed(() => {
    if (!selectedNode.value?.data?.moduleId) return {};
    const component = componentStore.findComponentById(selectedNode.value.data.moduleId);
    return component?.manifest || {};
});

const nodeUiSchema = computed(() => {
  return nodeManifest.value?.ui_schema || [];
});

const nodeProperties = computed(() => {
  return nodeManifest.value?.properties || [];
});

const nodeConfigValues = computed(() => {
  if (selectedNode.value && !selectedNode.value.data.config_values) {
    selectedNode.value.data.config_values = {};
  }
  return selectedNode.value?.data?.config_values || {};
});

function updateConfig(key, value) {
  if (selectedNode.value) {
    workflowStore.updateNodeConfig({
      nodeId: selectedNode.value.id,
      key,
      value
    });
  }
}

function handleDynamicFormUpdate(newConfig) {
  if (!selectedNode.value) return;

  Object.keys(newConfig).forEach(key => {
    if (nodeConfigValues.value[key] !== newConfig[key]) {
      updateConfig(key, newConfig[key]);
    }
  });
}
</script>

<style scoped>
.properties-container {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}
.properties-empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}
.node-title {
  font-family: 'Orbitron', monospace;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--neon-cyan);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}
.node-description {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  padding-bottom: 8px;
}
.prop-item {
  margin-bottom: 16px;
}
.code-editor-wrapper .v-label {
    margin-bottom: 4px;
    display: block;
}
.config-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-secondary);
    margin-bottom: 16px;
}
.node-icon-title {
    width: 24px;
    height: 24px;
    color: var(--neon-cyan);
}

/* Additional styling for Hacker Input consistency in legacy mode */
.hacker-input :deep(.v-field) { background-color: rgba(30, 30, 45, 0.6) !important; color: #FFFFFF !important; }
.hacker-input :deep(.v-field__outline) { border-color: rgba(0, 245, 255, 0.5) !important; }
</style>
