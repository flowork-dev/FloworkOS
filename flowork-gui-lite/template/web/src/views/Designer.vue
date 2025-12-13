//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\Designer.vue total lines 614 
//#######################################################################

<template>
  <v-layout class="designer-view-layout fill-height god-mode-theme">

    <v-navigation-drawer
        v-model="uiStore.isToolboxOpen"
        width="300"
        class="left-drawer holo-glass"
        >
        <div class="panel-scanner-line"></div>
        <Toolbox />
    </v-navigation-drawer>

    <v-main class="main-canvas flex-grow-1">

      <template v-if="uiStore.designerMode === 'logic'">

          <NeuralCanvasBackground />
          <div class="gold-vignette"></div>

          <div class="hacker-log-stream">
              <div class="log-header text-mono text-gold-dim mb-2 text-right text-caption">
                  <v-icon icon="mdi-console" size="x-small" class="mr-1"></v-icon>SYSTEM_LOGS // LIVE
              </div>
              <transition-group name="log-slide">
                  <div v-for="log in visibleLogs" :key="log.id" class="stream-line">
                      <span class="stream-message" :class="'lvl-' + (log.level || 'info').toLowerCase()">
                          {{ log.message }}
                      </span>
                      <span class="stream-source text-gold"> &lt;{{ log.source }}&gt;</span>
                  </div>
              </transition-group>
          </div>

          <div v-if="!socketStore.isConnected && authStore.isAuthenticated && !socketStore.isGracePeriod" class="offline-banner glass-warning">
              <v-icon icon="mdi-lan-disconnect" class="mr-2 blink-fast"></v-icon>
              <span class="text-mono">CONNECTION LOST // OFFLINE MODE</span>
              <v-btn to="/settings" size="small" variant="outlined" color="#D4AF37" class="ml-4 glow-border">RECONNECT</v-btn>
          </div>

          <div v-if="isReadOnly" class="read-only-indicator glass-info">
              <v-icon icon="mdi-eye-outline" class="mr-2"></v-icon>
              {{ loc('sharing_readonly_mode') }}
          </div>

          <VueFlow
            v-model="elements"
            class="vue-flow-canvas"
            @dragover="handleDragOver"
            @drop="handleDrop"
            @pane-click="handlePaneClick"
            @node-click="handleNodeClick"
            @node-context-menu="onNodeContextMenu"
            @edge-context-menu="onEdgeContextMenu"
            @edge-click="handleEdgeClick"
            @pane-context-menu="onPaneContextMenu"
            :fit-view-on-init="true"
            :edge-class="getEdgeClass"
            @node-drag-start="onNodeDragStart"
            @node-drag-stop="onNodeDragStop"
            @connect="onConnect"
            :nodes-draggable="!isReadOnly"
            :nodes-connectable="!isReadOnly"
            :elements-selectable="true"
            :apply-changes="false"
            @pane-ready="onPaneReady"
          >

          <Background :variant="BackgroundVariant.Dots" :gap="25" :size="1" color="rgba(212, 175, 55, 0.2)" />

            <template #node-default="props">
              <CustomNode
                :id="props.id"
                :label="props.label"
                :selected="props.selected"
                :data="props.data"
                :is-zoomed-out="isZoomedOut"
              />
            </template>
          </VueFlow>

          <div class="flow-watermark" v-if="isCanvasEmpty">
              <h1 class="text-gold-gradient">FLOWORK</h1>
              <p class="text-mono text-gold-dim">SYSTEM READY</p>
          </div>

          </template>

      <DataflowView v-if="uiStore.designerMode === 'data'" />

      <DebuggerView v-if="uiStore.designerMode === 'debugger'" />

      <div v-if="uiStore.designerMode === 'logs'" class="log-full-page-wrapper">
         <LogPanelContent :is-full-page="true" />
      </div>

      <ControlsFooter />
    </v-main>

    <v-navigation-drawer
        location="right"
        :model-value="isRightPanelOpen"
        @update:modelValue="handleRightPanelClose"
        width="500"
        :temporary="!uiStore.isPropertiesPanelPinned"
        class="right-drawer holo-glass"
      >
      <div class="panel-scanner-line-right"></div>
      <RightSidebar />
    </v-navigation-drawer>

    <v-menu
      v-model="contextMenu.visible"
      :style="{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }"
      location="top start"
      absolute
      content-class="gold-context-menu"
      >
      <v-list density="compact" class="gold-list">
        <template v-for="(item, index) in contextMenu.items">
          <v-divider v-if="item.isDivider" :key="`divider-${index}`" class="gold-divider"></v-divider>
           <v-list-item v-else-if="item.items" :key="`submenu-${index}`" class="gold-list-item">
              <template v-slot:prepend>
                  <v-icon :icon="item.icon" :color="item.color || '#D4AF37'"></v-icon>
              </template>
              <v-list-item-title class="text-mono">{{ item.title }}</v-list-item-title>
              <v-menu activator="parent" location="end" content-class="gold-context-menu">
                  <v-list density="compact" class="gold-list">
                      <v-list-item v-for="(subItem, subIndex) in item.items" :key="subIndex" @click="subItem.action" class="gold-list-item">
                          <template v-slot:prepend>
                              <v-icon :icon="subItem.icon" :color="subItem.color || '#D4AF37'"></v-icon>
                          </template>
                          <v-list-item-title class="text-mono">{{ subItem.title }}</v-list-item-title>
                      </v-list-item>
                  </v-list>
              </v-menu>
          </v-list-item>
          <v-list-item v-else :key="index" @click="item.action" :disabled="item.disabled" class="gold-list-item">
            <template v-slot:prepend>
              <v-icon :icon="item.icon" :color="item.color || '#D4AF37'"></v-icon>
            </template>
            <v-list-item-title class="text-mono">{{ item.title }}</v-list-item-title>
          </v-list-item>
        </template>
      </v-list>
    </v-menu>

    <DataViewer />
    <ShareWorkflowModal />

  </v-layout>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { storeToRefs } from 'pinia';
import { Background, BackgroundVariant } from '@vue-flow/background';
import Toolbox from '@/components/Toolbox.vue';
import CustomNode from '@/components/CustomNode.vue';
import RightSidebar from '@/components/RightSidebar.vue';
import ControlsFooter from '@/components/ControlsFooter.vue';
import DataViewer from '@/components/DataViewer.vue';
import ShareWorkflowModal from '@/components/ShareWorkflowModal.vue';
import LogPanelContent from '@/components/panels/LogPanelContent.vue';


import { useComponentStore } from '@/store/components';
import { useWorkflowStore } from '@/store/workflow';
import { useUiStore } from '@/store/ui';
import { useLocaleStore } from '@/store/locale';
import { useAuthStore } from '@/store/auth';
import { useSocketStore } from '@/store/socket';
import { useLogStore } from '@/store/logs';
import { useRouter, useRoute } from 'vue-router';
import { v4 as uuidv4 } from 'uuid';
import DataflowView from '@/views/DataflowView.vue';
import DebuggerView from '@/views/DebuggerView.vue';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';

const componentStore = useComponentStore();
const workflowStore = useWorkflowStore();
const uiStore = useUiStore();
const localeStore = useLocaleStore();
const authStore = useAuthStore();
const socketStore = useSocketStore();
const logStore = useLogStore();
const router = useRouter();
const route = useRoute();

const { elements, selectedNode, connectionStatus, isReadOnly, isCanvasEmpty } = storeToRefs(workflowStore);
const { loc } = storeToRefs(localeStore);
const isRightPanelOpen = computed(() => !!uiStore.activeRightPanel);

const visibleLogs = ref([]);

watch(() => logStore.executionLogs.length, (newLen, oldLen) => {
    if (newLen > oldLen) {
        const newLogs = logStore.executionLogs.slice(oldLen - newLen);

        newLogs.forEach(log => {
            const id = uuidv4();
            const logItem = { ...log, id };

            visibleLogs.value.push(logItem);

            setTimeout(() => {
                const idx = visibleLogs.value.findIndex(l => l.id === id);
                if (idx !== -1) visibleLogs.value.splice(idx, 1);
            }, 15000);
        });
    } else if (newLen === 0) {
        visibleLogs.value = [];
    }
});

const { project, screenToFlowCoordinate, fitView, zoom } = useVueFlow();
const isZoomedOut = computed(() => zoom?.value < 0.4);

const contextMenu = ref({ visible: false, x: 0, y: 0, items: [], target: null });
const lastPaneClickPosition = ref({ x: 0, y: 0 });

const colorPalette = [
  { name: 'Default', value: null, icon: 'mdi-circle-off-outline', color: 'grey' },
  { name: 'Blue', value: '#2196F3', icon: 'mdi-circle', color: '#2196F3' },
  { name: 'Green', value: '#4CAF50', icon: 'mdi-circle', color: '#4CAF50' },
  { name: 'Orange', value: '#FF9800', icon: 'mdi-circle', color: '#FF9800' },
  { name: 'Red', value: '#F44336', icon: 'mdi-circle', color: '#F44336' },
];

function onPaneReady() {
    setTimeout(() => { fitView(); }, 100);
}

function getEdgeClass(edge) {
    const status = connectionStatus.value[edge.id]?.status;
    if (status === 'ACTIVE') {
        return 'connection-active';
    }
    return '';
}

function handleEdgeClick({ event, edge }) {
    workflowStore.fetchConnectionData(edge.id);
}

function handleRightPanelClose(isOpen) {
    if (!isOpen) {
        if (!uiStore.isPropertiesPanelPinned || uiStore.activeRightPanel !== 'properties') {
             uiStore.closeRightPanel();
        }
    }
}

function onPaneContextMenu(event) {
  event.preventDefault();
  lastPaneClickPosition.value = { x: event.clientX, y: event.clientY };
  contextMenu.value.target = null;
  contextMenu.value.items = [
    { title: 'Paste Node', icon: 'mdi-content-paste', action: () => {
        const { x, y } = project(lastPaneClickPosition.value);
        workflowStore.pasteNode({ x, y });
    }, disabled: !workflowStore.clipboard || isReadOnly.value },
  ];
  contextMenu.value.x = event.clientX;
  contextMenu.value.y = event.clientY;
  nextTick(() => { contextMenu.value.visible = true; });
}

function onNodeContextMenu({ event, node }) {
  event.preventDefault();
  contextMenu.value.target = node;
  contextMenu.value.items = [
    { title: 'Run From This Node', icon: 'mdi-play-box-outline', color: '#4CAF50', action: () => workflowStore.executeCurrentWorkflow(node.id), disabled: !workflowStore.canExecute },
    {
      title: 'Change Color',
      icon: 'mdi-palette',
      items: colorPalette.map(color => ({
        title: color.name,
        icon: color.icon,
        color: color.color,
        action: () => workflowStore.setNodeColor({ nodeId: node.id, color: color.value })
      })),
      disabled: isReadOnly.value
    },
    { isDivider: true },
    { title: 'Copy Node', icon: 'mdi-content-copy', action: () => workflowStore.copyNode(node) },
    { title: 'Duplicate Node', icon: 'mdi-content-duplicate', action: () => workflowStore.duplicateNode(node), disabled: isReadOnly.value },
    { title: 'View Execution Log', icon: 'mdi-console-line', action: () => console.log('View logs for', node.id) },
    { isDivider: true },
    { title: 'Delete Node', icon: 'mdi-delete-outline', color: 'red', action: () => workflowStore.removeElements([node]), disabled: isReadOnly.value }
  ];
  contextMenu.value.x = event.clientX;
  contextMenu.value.y = event.clientY;
  nextTick(() => { contextMenu.value.visible = true; });
}

function onEdgeContextMenu({ event, edge }) {
  event.preventDefault();
  contextMenu.value.target = edge;
  contextMenu.value.items = [
    { title: 'View Data History', icon: 'mdi-history', action: () => workflowStore.fetchConnectionData(edge.id) },
    { isDivider: true },
    { title: 'Delete Connection', icon: 'mdi-delete-outline', color: 'red', action: () => workflowStore.removeElements([edge]), disabled: isReadOnly.value }
  ];
  contextMenu.value.x = event.clientX;
  contextMenu.value.y = event.clientY;
  nextTick(() => { contextMenu.value.visible = true; });
}

onMounted(() => {
  const token = route.params.token;
  if (token) {
    console.log(`[Designer] Found share token: ${token}, loading workflow...`);
    workflowStore.loadSharedWorkflow(token);
  } else {
    console.log('[Designer] Normal session. Waiting for WebSocket connection to fetch data.');
  }
  uiStore.isToolboxOpen = true;
});

function handleDragOver(event) {
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
}

function handleDrop(event) {
  if (isReadOnly.value) return;

  try {
      const jsonData = event.dataTransfer?.getData('application/json');
      if (!jsonData) return;

      const droppedData = JSON.parse(jsonData);
      if (!droppedData.id) return;

      const position = screenToFlowCoordinate({ x: event.clientX, y: event.clientY - 64 });
      workflowStore.addNode({
          moduleId: droppedData.id,
          x: position.x,
          y: position.y,
      });
  } catch (e) {
      console.error("[Designer] Failed to parse dropped item:", e);
  }
}

function onConnect(connectionData) {
    if (isReadOnly.value) return;
    workflowStore.addEdge(connectionData);
}

function handlePaneClick() {
    workflowStore.clearSelectedNode();
    if (uiStore.activeRightPanel !== 'properties' || !uiStore.isPropertiesPanelPinned) {
        uiStore.closeRightPanel();
    }
    contextMenu.value.visible = false;
}

function handleNodeClick({ event, node }) {
    workflowStore.setSelectedNode(node);
    uiStore.setActiveRightPanel('properties');
}

function onNodeDragStart(event) {
  const node = event.node;
  if (node) {
    if (!node.data) node.data = {};
    node.data.isDragging = true;
  }
}
function onNodeDragStop({ event, node }) {
  if (node) {
    if (!node.data) node.data = {};
    node.data.isDragging = false;
  }
}
</script>

<style scoped>
/* ==========================================================================
   ROYAL DARK GOLD THEME - "GOD MODE" (Scoped)
   ========================================================================== */

/* --- CORE LAYOUT --- */
.god-mode-theme {
    background-color: #050505; /* Deepest Black */
    color: #e0e0e0;
    font-family: 'Exo 2', sans-serif;
    position: relative;
    overflow: hidden;
}

.main-canvas {
  position: relative;
  flex-grow: 1;
  height: 100%;
  padding-top: 65px !important;
  z-index: 1;
}

/* --- BACKGROUND FX --- */
.gold-vignette {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at center, transparent 30%, #050505 100%);
    pointer-events: none;
    z-index: 0;
}

/* --- HOLOGRAPHIC DRAWERS (Glassmorphism) --- */
.holo-glass {
    background: rgba(12, 14, 20, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    border: none !important;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.8);
    transition: all 0.3s ease;
}

.left-drawer {
    border-right: 1px solid rgba(212, 175, 55, 0.2) !important; /* Gold Border */
}
.right-drawer {
    border-left: 1px solid rgba(212, 175, 55, 0.2) !important;
}

/* Scanner Line Animation on Drawers */
.panel-scanner-line, .panel-scanner-line-right {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, #D4AF37, transparent);
    animation: scan-line 4s infinite ease-in-out;
    opacity: 0.7;
    z-index: 10;
    pointer-events: none;
}
.panel-scanner-line-right {
    animation-delay: 2s;
}

@keyframes scan-line {
    0% { top: 0%; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { top: 100%; opacity: 0; }
}

/* --- HACKER LOG STREAM (Terminal Style) --- */
.hacker-log-stream {
    position: absolute;
    bottom: 20px;
    right: 20px;
    width: 480px;
    max-height: 400px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: flex-end;
    pointer-events: none; /* Click through */
    z-index: 5;
    /* Fade out top */
    mask-image: linear-gradient(to bottom, transparent, black 30%);
    -webkit-mask-image: linear-gradient(to bottom, transparent, black 30%);
}

.stream-line {
    text-align: right;
    margin-bottom: 4px;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    line-height: 1.5;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
    white-space: nowrap;
}

.stream-source {
    font-size: 0.85em;
    font-weight: bold;
    opacity: 0.8;
}

/* --- BANNERS & INDICATORS --- */
.offline-banner {
  position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
  z-index: 20; padding: 10px 24px;
  color: #D4AF37;
  font-family: 'Orbitron', monospace;
  font-size: 0.85rem;
  letter-spacing: 1px;
  pointer-events: all;
  display: flex; align-items: center;
  border-radius: 4px;
}
.glass-warning {
    background: rgba(40, 20, 0, 0.85);
    border: 1px solid rgba(255, 152, 0, 0.5);
    box-shadow: 0 0 20px rgba(255, 152, 0, 0.2);
    backdrop-filter: blur(10px);
}

.read-only-indicator {
  position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
  z-index: 20; padding: 8px 20px;
  color: #00f5ff;
  font-family: 'Orbitron', monospace;
  pointer-events: none;
  border-radius: 4px;
}
.glass-info {
    background: rgba(0, 20, 40, 0.85);
    border: 1px solid rgba(0, 245, 255, 0.4);
    backdrop-filter: blur(10px);
}

/* --- WATERMARK --- */
.flow-watermark {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  pointer-events: none; z-index: 0; opacity: 0.05; text-align: center;
}
.text-gold-gradient {
    font-size: 10rem;
    font-family: 'Orbitron', monospace;
    font-weight: 900;
    margin: 0; line-height: 1;
    letter-spacing: -5px;
    background: linear-gradient(to bottom, #D4AF37, #5a4a1b);
    -webkit-background-clip: text;
    background-clip: text; /* Compatibility Fix */
    -webkit-text-fill-color: transparent;
}

/* --- UTILS --- */
.text-mono { font-family: 'Fira Code', monospace; }
.text-gold { color: #D4AF37; }
.text-gold-dim { color: rgba(212, 175, 55, 0.7); }
.glow-border { border-color: #D4AF37 !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }
.blink-fast { animation: blink 1s infinite; }

/* --- LOG LEVELS --- */
.lvl-info { color: #00f5ff; text-shadow: 0 0 5px rgba(0, 245, 255, 0.5); }
.lvl-success { color: #39ff14; text-shadow: 0 0 5px rgba(57, 255, 20, 0.5); }
.lvl-warn { color: #ffeb3b; }
.lvl-error { color: #ff0055; text-shadow: 0 0 8px rgba(255, 0, 85, 0.6); }
.lvl-debug { color: #888; }

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* --- ANIMATIONS: Log Slide --- */
.log-slide-enter-active { transition: all 0.3s ease-out; }
.log-slide-leave-active { transition: all 0.3s ease-in; position: absolute; }
.log-slide-enter-from { opacity: 0; transform: translateX(20px); }
.log-slide-leave-to { opacity: 0; transform: translateY(-10px); }
.log-slide-move { transition: transform 0.3s ease; }

.log-full-page-wrapper {
    width: 100%;
    height: 100%;
    background-color: #0F111A;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    overflow: hidden;
}
.neural-canvas {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; opacity: 0.5;
}
</style>

<style>
/* --- GLOBAL STYLES (Overrides for VueFlow & Vuetify) --- */

/* CONTEXT MENU */
.gold-context-menu .v-list {
    background: rgba(10, 12, 18, 0.95) !important;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.8);
    border-radius: 4px !important;
}
.gold-list-item {
    min-height: 32px !important;
    padding: 6px 16px !important;
    color: #e0e0e0 !important;
    transition: all 0.2s;
}
.gold-list-item:hover {
    background: rgba(212, 175, 55, 0.15) !important;
    padding-left: 20px !important; /* Slide effect */
}
.gold-divider {
    border-color: rgba(212, 175, 55, 0.2) !important;
}

/* EDGE ANIMATION: GOLD FLOW */
.vue-flow__edge.connection-active .vue-flow__edge-path {
    stroke: #D4AF37; /* Gold */
    stroke-width: 2;
    stroke-dasharray: 8;
    animation: gold-flow 1s linear infinite;
    filter: drop-shadow(0 0 3px rgba(212, 175, 55, 0.6));
}
@keyframes gold-flow { to { stroke-dashoffset: -16; } }

/* NODE SELECTION - GOLD GLOW */
.vue-flow__node.selected {
    border: 1px solid #D4AF37 !important;
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.5) !important;
}
</style>
