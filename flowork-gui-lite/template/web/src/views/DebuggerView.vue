//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\DebuggerView.vue total lines 137 
//#######################################################################

<template>
  <div class="debugger-view">
    <div class="debugger-header">
      <h2 class="orbitron-font">
        <v-icon icon="mdi-bug-check-outline" class="mr-2"></v-icon>
        Execution Timeline
      </h2>
      <v-btn
        variant="outlined"
        size="small"
        @click="logStore.clearLogs"
        :disabled="detailedLogs.length === 0"
      >Clear Log</v-btn>
    </div>

    <div class="timeline-container">
      <v-timeline v-if="detailedLogs.length > 0" align="start" side="end" density="compact">
        <v-timeline-item
          v-for="log in detailedLogs"
          :key="log.node_id"
          :dot-color="getStatusColor(log.status)"
          :icon="getStatusIcon(log.status)"
          fill-dot
          size="small"
        >
          <div class="log-item" :style="{ borderColor: getStatusColor(log.status) }">
            <div class="log-header">
              <span class="node-name">{{ log.node_name }}</span>
              <span class="timestamp text-caption text-grey">{{ new Date(log.timestamp * 1000).toLocaleTimeString() }}</span>
            </div>
            <div class="log-details text-caption">
              <span>Status: <strong :style="{ color: getStatusColor(log.status) }">{{ log.status }}</strong></span>
              <v-divider vertical class="mx-2"></v-divider>
              <span>Duration: {{ log.execution_time_ms ? log.execution_time_ms.toFixed(2) + ' ms' : 'N/A' }}</span>
            </div>
          </div>
        </v-timeline-item>
      </v-timeline>
      <div v-else class="empty-state">
          <v-icon icon="mdi-history" size="64" color="grey-darken-2"></v-icon>
          <h2 class="mt-4 text-grey-darken-1 orbitron-font">No execution data</h2>
          <p>Run a workflow to see the live debug timeline here.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useLogStore } from '@/store/logs';
import { storeToRefs } from 'pinia';

const logStore = useLogStore();
const { detailedTimeline: detailedLogs } = storeToRefs(logStore); // TAMBAHAN: [PERBAIKAN DARI GEMINI] Menggunakan getter 'detailedTimeline' dan me-rename jadi 'detailedLogs' agar template tidak perlu diubah.

const getStatusColor = (status) => {
  switch (status) {
    case 'SUCCESS': return '#39ff14'; // neon-green
    case 'RUNNING': return '#00f5ff'; // neon-cyan
    case 'ERROR':
    case 'FAILED':
      return '#ff5252'; // red
    default: return 'grey';
  }
};
const getStatusIcon = (status) => {
  switch (status) {
    case 'SUCCESS': return 'mdi-check-circle-outline';
    case 'RUNNING': return 'mdi-autorenew';
    case 'ERROR':
    case 'FAILED':
      return 'mdi-alert-circle-outline';
    default: return 'mdi-help-circle-outline';
  }
};
</script>

<style scoped>
.debugger-view {
  width: 100%;
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  background-color: #161625;
}
.debugger-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: #f0f0f0;
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
}
.timeline-container {
  flex-grow: 1;
  overflow-y: auto;
  padding-top: 24px;
}
.log-item {
  background-color: rgba(42, 42, 74, 0.5);
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid;
  /* (COMMENT) PERBAIKAN: Dulu warna border di-hardcode, sekarang dinamis */
  border-color: var(--v-theme-on-surface);
}
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.node-name {
  font-weight: bold;
}
.log-details {
  display: flex;
  align-items: center;
  color: #B0BEC5;
}
.empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>
