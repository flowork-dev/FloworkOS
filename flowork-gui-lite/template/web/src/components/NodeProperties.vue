//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\NodeProperties.vue total lines 144 
//#######################################################################

<template>
  <div class="properties-panel pa-4">
    <div v-if="selectedNode && nodeManifest">
      <div class="d-flex justify-space-between align-center mb-4">
        <h3 class="panel-title text-truncate" :title="loc(nodeManifest.name)">{{ loc(nodeManifest.name) }}</h3>
        <v-btn icon="mdi-close" variant="text" size="small" @click="workflowStore.clearSelectedNode"></v-btn>
      </div>

      <div>
        <div v-for="prop in nodeProperties" :key="prop.id" class="mb-3">

          <v-text-field
            v-if="prop.type === 'string' || prop.type === 'integer' || prop.type === 'float'"
            :label="loc(prop.label)"
            :type="prop.type === 'string' ? 'text' : 'number'"
            v-model="nodeConfigValues[prop.id]"
            @update:modelValue="updateConfig(prop.id, $event)"
            variant="outlined"
            density="compact"
            hide-details="auto"
          ></v-text-field>

          <v-switch
            v-if="prop.type === 'boolean'"
            :label="loc(prop.label)"
            v-model="nodeConfigValues[prop.id]"
            @update:modelValue="updateConfig(prop.id, $event)"
            color="primary"
            hide-details
          ></v-switch>

          <v-select
            v-if="prop.type === 'enum'"
            :label="loc(prop.label)"
            :items="prop.options"
            v-model="nodeConfigValues[prop.id]"
            @update:modelValue="updateConfig(prop.id, $event)"
            variant="outlined"
            density="compact"
            hide-details
          ></v-select>

          <v-textarea
            v-if="prop.type === 'textarea' || prop.type === 'code'"
            :label="loc(prop.label)"
            v-model="nodeConfigValues[prop.id]"
            @update:modelValue="updateConfig(prop.id, $event)"
            variant="outlined"
            density="compact"
            rows="4"
            hide-details
          ></v-textarea>

        </div>
      </div>
    </div>

    <div v-else class="text-center text-grey d-flex flex-column justify-center align-center fill-height">
      <v-icon icon="mdi-cursor-default-click-outline" size="48" class="mb-2"></v-icon>
      <p>Select a node to see its properties.</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useWorkflowStore } from '@/store/workflow';
import { useComponentStore } from '@/store/components';
import { useLocaleStore } from '@/store/locale';


const workflowStore = useWorkflowStore();
const { selectedNode } = storeToRefs(workflowStore);
const { clearSelectedNode } = workflowStore;
const componentStore = useComponentStore();
const localeStore = useLocaleStore();
const { loc } = storeToRefs(localeStore);


const nodeManifest = computed(() => {
    if (!selectedNode.value?.data?.moduleId) return {};
    const component = componentStore.findComponentById(selectedNode.value.data.moduleId);
    return component?.manifest || {};
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

/*
watch(selectedNode, async (newNode) => {
  if (newNode) {
    isManifestLoading.value = true;
    manifestProperties.value = [];
    try {
      const details = await getComponentDetails('modules', newNode.data.moduleId);
      manifestProperties.value = details.manifest.properties || [];
    } catch (error) {
      console.error(`Could not fetch manifest for ${newNode.data.moduleId}`, error); // English log
    } finally {
      isManifestLoading.value = false;
    }
  } else {
    manifestProperties.value = [];
  }
}, { immediate: true });
*/
</script>

<style scoped>
.properties-panel {
  height: 100%;
  background-color: #2a2a2a;
  color: white;
  overflow-y: auto;
}
.panel-title {
  font-family: 'Exo 2', sans-serif;
}
</style>
