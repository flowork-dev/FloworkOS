//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\panels\LogPanel.vue total lines 174 
//#######################################################################

<template>
  <v-card class="sidebar-content-card">
    <v-card-title class="panel-title">
      <v-icon icon="mdi-console" class="mr-2"></v-icon>
      Execution Log
      <v-spacer /> <v-tooltip text="Copy visible logs" location="bottom">
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            :icon="copyIcon"
            variant="text"
            size="small"
            @click="copyLog"
            :disabled="filteredLogs.length === 0"
          ></v-btn>
        </template>
      </v-tooltip>
      <v-btn
        icon="mdi-delete-sweep-outline"
        variant="text"
        size="small"
        @click="logStore.clearLogs"
        :disabled="executionLogs.length === 0"
        title="Clear Log"
      ></v-btn>
      <v-btn icon="mdi-close" variant="text" size="small" @click="uiStore.closeRightPanel"></v-btn>
    </v-card-title> <v-toolbar density="compact" color="transparent" class="px-2">
        <v-btn-toggle
            v-model="activeFilters"
            multiple
            variant="outlined"
            density="compact"
            class="filter-toggle"
        >
            <v-btn value="INFO" size="x-small" color="info">INFO</v-btn>
            <v-btn value="SUCCESS" size="x-small" color="success">SUCCESS</v-btn>
            <v-btn value="WARN" size="x-small" color="warning">WARN</v-btn>
            <v-btn value="ERROR" size="x-small" color="error">ERROR</v-btn>
            <v-btn value="DEBUG" size="x-small" color="grey">DEBUG</v-btn>
        </v-btn-toggle>
    </v-toolbar>

    <v-divider></v-divider>
    <v-card-text class="panel-content" ref="logContainer">
      <div v-if="executionLogs.length === 0" class="log-entry text-grey">
        [INFO] Waiting for workflow execution...
      </div>
      <div v-else-if="filteredLogs.length === 0" class="log-entry text-grey">
        [INFO] No logs match the current filter.
      </div>
      <div
        v-for="(log, index) in filteredLogs"
        :key="index"
        :class="['log-entry', getLogLevelClass(log.level)]"
      >
        <v-icon :icon="getLogLevelIcon(log.level)" size="x-small" class="mr-2 log-icon"></v-icon>
        <span class="log-source">[{{ log.source }}]</span> {{ log.message }}
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { useUiStore } from '@/store/ui';
import { useLogStore } from '@/store/logs';
import { storeToRefs } from 'pinia';

const uiStore = useUiStore();
const logStore = useLogStore();
const { executionLogs } = storeToRefs(logStore);

const logContainer = ref(null);
const activeFilters = ref(['INFO', 'SUCCESS', 'WARN', 'ERROR', 'DEBUG']);
const copyIcon = ref('mdi-content-copy');

const filteredLogs = computed(() => {
    if (activeFilters.value.length === 5) return executionLogs.value;
    return executionLogs.value.filter(log => activeFilters.value.includes(log.level.toUpperCase()));
});

const getLogLevelClass = (level) => {
  const levelLower = (level || 'info').toLowerCase();
  if (levelLower.includes('success')) return 'log-success';
  if (levelLower.includes('warn')) return 'log-warn';
  if (levelLower.includes('error') || levelLower.includes('critical')) return 'log-error';
  if (levelLower.includes('debug') || levelLower.includes('detail')) return 'log-debug';
  return 'log-info';
};

const getLogLevelIcon = (level) => {
  const levelLower = (level || 'info').toLowerCase();
  if (levelLower.includes('success')) return 'mdi-check-circle-outline';
  if (levelLower.includes('warn')) return 'mdi-alert-outline';
  if (levelLower.includes('error') || levelLower.includes('critical')) return 'mdi-alert-circle-outline';
  if (levelLower.includes('debug') || levelLower.includes('detail')) return 'mdi-bug-outline';
  return 'mdi-information-outline';
};

const copyLog = () => {
    const logText = filteredLogs.value.map(log => `[${log.level.toUpperCase()}] [${log.source}] ${log.message}`).join('\n');
    navigator.clipboard.writeText(logText).then(() => {
        copyIcon.value = 'mdi-check';
        setTimeout(() => {
            copyIcon.value = 'mdi-content-copy';
        }, 1500);
    });
};

watch(executionLogs, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
}, { deep: true });
</script>

<style scoped>
.sidebar-content-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent;
  box-shadow: none;
}
.panel-content {
  flex-grow: 1;
  overflow-y: auto;
  background-color: rgba(20, 20, 30, 0.4);
  border-radius: 4px;
  padding: 16px !important;
}
.panel-title {
  color: #00f5ff !important;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
  padding-bottom: 8px;
  padding-top: 8px;
  text-shadow: 0 0 4px rgba(0, 245, 255, 0.5);
}
.filter-toggle {
    height: 28px !important;
}
.log-entry {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85rem;
  margin-bottom: 4px;
  white-space: pre-wrap;
  text-shadow: 0 0 5px rgba(0, 0, 0, 0.7);
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
}
.log-source {
  font-weight: bold;
  margin-right: 8px;
}
.log-icon {
  margin-top: 3px;
}
.log-info { color: #00f5ff; }
.log-success { color: #39ff14; }
.log-warn { color: #ffeb3b; }
.log-error { color: #ff5252; }
.log-debug { color: #9E9E9E; }
</style>
