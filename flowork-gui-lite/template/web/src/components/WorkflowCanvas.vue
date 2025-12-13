//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\WorkflowCanvas.vue total lines 218 
//#######################################################################

<template>
  <div class="canvas-wrapper">
    <VueFlow
      v-model="elements"
      class="vue-flow-canvas"
      :apply-changes="false"
      :fit-view-on-init="true"
      @dragover="onDragOver"
      @drop="onDrop"
      @connect="onConnect"
      @node-click="onNodeClick"
      @pane-click="onPaneClick"
      @node-drag-start="onNodeDragStart"
      @node-drag-stop="onNodeDragStop"
    >
      <template #node-default="props">
        <div
          class="vue-flow__node-custom flowork-node"
          :class="getNodeClasses(props)"
        >
          <Handle type="target" :position="Position.Left" />
          <div class="node-body">
            <div class="node-icon">
              <img :src="getIconUrl(props.data.componentType, props.data.moduleId)" alt="">
            </div>
            <div class="node-label">
              {{ props.label }}
            </div>
             <div v-if="getNodeStatus(props.id)" class="status-indicator" :class="getNodeStatus(props.id)"></div>
          </div>
          <Handle type="source" :position="Position.Right" />
        </div>
      </template>

      <Background :pattern-color="BG_COLOR" gap="16" />
      <Controls />
    </VueFlow>

    <CanvasWatermark />
  </div>
</template>

<script setup>
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { storeToRefs } from 'pinia';
import { useWorkflowStore } from '@/store/workflow';
import CanvasWatermark from './CanvasWatermark.vue';
import { getComponentIconUrl } from '@/api';
import { watch } from 'vue';

const workflowStore = useWorkflowStore();
const { elements, executionStatus, connectionStatus } = storeToRefs(workflowStore);
const { addNode, addEdge, setSelectedNode, clearSelectedNode } = workflowStore;
const { onPaneReady, screenToFlowCoordinate } = useVueFlow();
const BG_COLOR = '#444';

onPaneReady(({ fitView }) => { fitView(); });

function onNodeDragStart(event) {
  if (event.node) {
    event.node.data.isDragging = true;
  }
}
function onNodeDragStop(event) {
  if (event.node) {
    setTimeout(() => {
      event.node.data.isDragging = false;
    }, 100);
  }
}

function getIconUrl(type, id) {
    return getComponentIconUrl(type, id);
}

function onDrop(event) {
  event.preventDefault();
  const componentData = JSON.parse(event.dataTransfer?.getData('application/json') || '{}');
  if (!componentData.id) return;
  const position = screenToFlowCoordinate({ x: event.clientX, y: event.clientY });
  addNode({
    moduleId: componentData.id,
    label: componentData.name,
    componentType: componentData.type,
    x: position.x,
    y: position.y,
  });
}

function onDragOver(event) { event.preventDefault(); if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'; }
function onConnect(connection) { addEdge(connection); }
function onNodeClick(event) { setSelectedNode(event.node); }
function onPaneClick() { clearSelectedNode(); }

function getNodeClasses(props) {
    const status = getNodeStatus(props.id);
    return {
        'is-dragging': props.data.isDragging,
        'node-running': status === 'running',
        'node-success': status === 'success',
        'node-error': status === 'error'
    };
}

function getNodeStatus(nodeId) {
    const statusObj = executionStatus.value[nodeId];
    if (!statusObj) return null;

    const s = statusObj.status?.toUpperCase();
    if (s === 'RUNNING' || s === 'PENDING') return 'running';
    if (s === 'DONE' || s === 'SUCCEEDED' || s === 'SUCCESS') return 'success';
    if (s === 'FAILED' || s === 'ERROR') return 'error';
    return null;
}

watch(connectionStatus, (newStatus) => {
    const updatedElements = elements.value.map(el => {
        if (el.source && el.target) { // It's an edge
             const statusData = newStatus[el.id];
             if (statusData && statusData.status === 'ACTIVE') {
                 return {
                    ...el,
                    animated: true,
                    style: { stroke: '#00ffcc', strokeWidth: 3, opacity: 1, filter: 'drop-shadow(0 0 5px #00ffcc)' }
                 };
             } else {
                 return {
                    ...el,
                    animated: false,
                    style: { stroke: '#b1b1b7', strokeWidth: 1, filter: 'none' }
                 };
             }
        }
        return el;
    });
    elements.value = updatedElements;
}, { deep: true });

</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';

.canvas-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

/* (VISUAL FIX) Neon Styles */
.flowork-node {
    transition: all 0.3s ease;
    border: 1px solid transparent;
}

/* RUNNING: Yellow/Gold Pulse */
.node-running {
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.8);
    border-color: #ffd700 !important;
    animation: pulse-yellow 1.5s infinite;
}

/* SUCCESS: Green Neon */
.node-success {
    box-shadow: 0 0 20px rgba(0, 255, 128, 0.6);
    border-color: #00ff80 !important;
}

/* ERROR: Red Shake */
.node-error {
    box-shadow: 0 0 20px rgba(255, 50, 50, 0.8);
    border-color: #ff3232 !important;
    animation: shake 0.5s;
}

.status-indicator {
    position: absolute;
    top: -6px;
    right: -6px;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2px solid #1a1a1a;
    z-index: 10;
}
.status-indicator.running { background-color: #ffd700; box-shadow: 0 0 5px #ffd700; }
.status-indicator.success { background-color: #00ff80; box-shadow: 0 0 5px #00ff80; }
.status-indicator.error { background-color: #ff3232; box-shadow: 0 0 5px #ff3232; }

@keyframes pulse-yellow {
    0% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
}

@keyframes shake {
  0% { transform: translate(1px, 1px) rotate(0deg); }
  10% { transform: translate(-1px, -2px) rotate(-1deg); }
  20% { transform: translate(-3px, 0px) rotate(1deg); }
  30% { transform: translate(3px, 2px) rotate(0deg); }
  40% { transform: translate(1px, -1px) rotate(1deg); }
  50% { transform: translate(-1px, 2px) rotate(-1deg); }
  60% { transform: translate(-3px, 1px) rotate(0deg); }
  70% { transform: translate(3px, 1px) rotate(-1deg); }
  80% { transform: translate(-1px, -1px) rotate(1deg); }
  90% { transform: translate(1px, 2px) rotate(0deg); }
  100% { transform: translate(1px, -2px) rotate(-1deg); }
}
</style>
