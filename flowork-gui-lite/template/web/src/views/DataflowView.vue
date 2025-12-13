//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\DataflowView.vue total lines 75 
//#######################################################################

<template>
  <div class="dataflow-view">
    <div class="mode-indicator orbitron-font">
      <v-icon icon="mdi-table-large" class="mr-2"></v-icon>
      DATAFLOW MODE (READ-ONLY)
    </div>
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :nodes-draggable="false"
      :nodes-connectable="false"
      :elements-selectable="true"
      :zoom-on-scroll="true"
      :pan-on-drag="true"
      fit-view-on-init
      @edge-click="handleEdgeClick"
    >
      <Background :variant="BackgroundVariant.Lines" :gap="40" :size="1.5" color="#2a2a4a" />
      <Controls />
       <template #node-default="props">
        <CustomNode
          :id="props.id"
          :label="props.label"
          :selected="props.selected"
          :data="props.data"
        />
      </template>
    </VueFlow>
  </div>
</template>

<script setup>
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { Background, BackgroundVariant } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { storeToRefs } from 'pinia';
import { useWorkflowStore } from '@/store/workflow';
import CustomNode from '@/components/CustomNode.vue';

const workflowStore = useWorkflowStore();
const { nodes, edges } = storeToRefs(workflowStore);

function handleEdgeClick({ event, edge }) {
    console.log(`[DataflowView] Edge clicked: ${edge.id}`);
    workflowStore.fetchConnectionData(edge.id);
}
</script>

<style scoped>
.dataflow-view {
  width: 100%;
  height: 100%;
  position: relative;
}
.mode-indicator {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 8px 16px;
  border-radius: 20px;
  color: #ffeb3b;
  font-size: 0.8rem;
  letter-spacing: 1px;
  pointer-events: none;
}
</style>
