//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\Canvas.vue total lines 57 
//#######################################################################

<template>
  <div class="canvas-wrapper">
    <VueFlow v-model="elements" @node-click="onNodeClick" @pane-click="onPaneClick" fit-view-on-init>
      <Background />
      <Controls />

      <template #node-default="{ data, id }">
        <CustomNode
          :module-id="data.moduleId"
          :manifest="data.manifest"
          :node-id="id"
        />
      </template>

    </VueFlow>
  </div>
</template>

<script setup>
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { storeToRefs } from 'pinia';
import { useWorkflowStore } from '@/store/workflow';
import { useUiStore } from '@/store/ui';
import CustomNode from './CustomNode.vue';

const workflowStore = useWorkflowStore();
const uiStore = useUiStore();

const { elements } = storeToRefs(workflowStore);
const { setSelectedNode, clearSelectedNode } = workflowStore;

const onNodeClick = (event, { node }) => {
  setSelectedNode(node);
  uiStore.setActiveRightPanel('properties');
};

const onPaneClick = () => {
  clearSelectedNode();
  uiStore.closeRightPanel();
};

</script>

<style>
.canvas-wrapper {
  height: 100%;
  width: 100%;
}
</style>
