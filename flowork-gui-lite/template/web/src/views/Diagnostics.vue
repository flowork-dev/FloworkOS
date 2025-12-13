//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\Diagnostics.vue total lines 371 
//#######################################################################

<template>
  <div class="diagnostics-view fill-height d-flex flex-column pa-6">

    <div class="d-flex align-center justify-space-between mb-6 flex-shrink-0">
      <div>
        <h1 class="text-h4 font-weight-black text-white orbitron-font">
          <v-icon icon="mdi-flash-alert" color="#FFD700" class="mr-3 pulsing-icon"></v-icon>
          SYSTEM DIAGNOSTICS
        </h1>
        <p class="text-grey-lighten-1 mt-1 font-mono text-caption">
          TARGET: <span class="text-gold-dim">C:\FLOWORK\scanners</span>
        </p>
      </div>
      <div class="d-flex align-center gap-4">
        <div class="text-right d-none d-md-block" v-if="activeScans > 0">
            <span class="text-caption text-gold font-weight-bold blink">SCANNING IN PROGRESS...</span>
        </div>
        <v-btn
          size="large"
          color="#FFD700"
          variant="flat"
          class="text-black font-weight-bold"
          :loading="isScanning"
          @click="runAllScanners"
        >
          <v-icon start>mdi-radar</v-icon>
          RUN FULL SCAN
        </v-btn>
      </div>
    </div>

    <v-row class="fill-height overflow-hidden ma-0">

      <v-col cols="12" md="4" class="fill-height py-0 pl-0 pr-2 d-flex flex-column overflow-hidden gap-4">

        <v-card class="glass-panel border-gold-thin pa-6 text-center position-relative overflow-hidden flex-shrink-0">
          <div class="scan-line"></div>
          <div class="text-overline text-grey mb-2">SYSTEM INTEGRITY SCORE</div>

          <v-progress-circular
            :model-value="healthScore"
            :color="healthColor"
            :size="160"
            :width="12"
            bg-color="rgba(255,255,255,0.05)"
          >
            <div class="d-flex flex-column align-center">
              <span class="text-h3 font-weight-black font-mono text-white">{{ healthScore }}%</span>
              <span class="text-caption text-uppercase mt-1 font-weight-bold" :class="`text-${healthColor}`">{{ healthStatus }}</span>
            </div>
          </v-progress-circular>

          <div class="mt-4 d-flex justify-space-around">
            <div class="text-center">
              <div class="text-h6 font-weight-bold text-white">{{ componentStore.allComponents.length }}</div>
              <div class="text-caption text-grey">Modules</div>
            </div>
            <div class="text-center">
              <div class="text-h6 font-weight-bold text-white">{{ socketStore.ping || '12' }}ms</div>
              <div class="text-caption text-grey">Ping</div>
            </div>
            <div class="text-center">
              <div class="text-h6 font-weight-bold text-white">{{ scanners.length }}</div>
              <div class="text-caption text-grey">Scanners</div>
            </div>
          </div>
        </v-card>

        <v-card class="glass-panel border-gold-thin flex-grow-1 d-flex flex-column overflow-hidden">
          <v-card-title class="text-subtitle-2 font-weight-bold bg-grey-darken-4 py-3 border-bottom-gold flex-shrink-0">
            <v-icon start icon="mdi-file-code-outline" size="small" color="#FFD700"></v-icon>
            AVAILABLE SCANNERS
          </v-card-title>

          <div class="scanner-list-container flex-grow-1 overflow-y-auto custom-scrollbar pa-2">
            <v-list bg-color="transparent" density="compact">
              <v-list-item
                v-for="scanner in scanners"
                :key="scanner.filename"
                class="scanner-item mb-1 rounded border-thin-transparent"
                :class="{ 'running': scanner.status === 'running' }"
              >
                <template v-slot:prepend>
                  <v-icon
                    :icon="getIcon(scanner.status)"
                    :color="getColor(scanner.status)"
                    size="small"
                    class="mr-2"
                    :class="{ 'mdi-spin': scanner.status === 'running' }"
                  ></v-icon>
                </template>

                <v-list-item-title class="font-mono text-caption text-white font-weight-medium">
                  {{ scanner.filename }}
                </v-list-item-title>

                <template v-slot:append>
                   <v-btn
                    v-if="scanner.status !== 'running'"
                    icon="mdi-play"
                    variant="text"
                    density="compact"
                    size="small"
                    color="#FFD700"
                    @click="runScanner(scanner)"
                   ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </div>
        </v-card>

      </v-col>

      <v-col cols="12" md="8" class="fill-height py-0 pr-0 pl-2 d-flex flex-column overflow-hidden">
        <v-card class="terminal-card flex-grow-1 border-gold-thin d-flex flex-column overflow-hidden">
          <div class="terminal-header d-flex align-center px-4 py-2 bg-grey-darken-4 border-bottom-gold flex-shrink-0">
            <v-icon icon="mdi-console" color="grey" size="small" class="mr-2"></v-icon>
            <span class="text-caption font-mono text-grey">root@flowork-doctor:~# tail -f /var/log/diagnostics.log</span>
            <v-spacer></v-spacer>
            <div class="d-flex gap-2 align-center">
                <v-btn icon="mdi-delete-sweep" size="x-small" variant="text" color="grey" @click="logs = []"></v-btn>
                <div class="window-dot red"></div>
                <div class="window-dot yellow"></div>
                <div class="window-dot green"></div>
            </div>
          </div>

          <div class="terminal-body pa-4 font-mono flex-grow-1 overflow-y-auto custom-scrollbar" ref="logContainer">
            <div v-if="logs.length === 0" class="h-100 d-flex flex-column align-center justify-center text-grey-darken-2">
              <v-icon icon="mdi-medical-bag" size="64" class="mb-4 opacity-30"></v-icon>
              <div>System Ready. Initiate Scan.</div>
            </div>

            <div v-for="(log, i) in logs" :key="i" class="log-entry mb-1">
              <span class="text-grey-darken-1 mr-2">[{{ log.timestamp }}]</span>
              <span class="text-gold-dim font-weight-bold mr-2" style="min-width: 120px; display: inline-block;">[{{ log.source }}]</span>
              <span :class="log.color">{{ log.message }}</span>
            </div>

            <div v-if="activeScans > 0" class="typing-cursor mt-2">_</div>
          </div>
        </v-card>
      </v-col>

    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { useSocketStore } from '@/store/socket';
import { useAuthStore } from '@/store/auth';
import { useComponentStore } from '@/store/components';
import { useUiStore } from '@/store/ui';

const socketStore = useSocketStore();
const authStore = useAuthStore();
const componentStore = useComponentStore();
const uiStore = useUiStore();

const logs = ref([]);
const logContainer = ref(null);
const healthScore = ref(100);
const isScanning = ref(false);

const scanners = ref([
  { filename: 'cache_integrity_scan.py', status: 'idle' },
  { filename: 'core_compiler_health_scan.py', status: 'idle' },
  { filename: 'core_integrity_scan.py', status: 'idle' },
  { filename: 'data_preview_readiness_scan.py', status: 'idle' },
  { filename: 'license_and_integrity_scan.py', status: 'idle' },
  { filename: 'manifest_completeness_scan.py', status: 'idle' },
  { filename: 'manifest_mismatch_scan.py', status: 'idle' },
  { filename: 'tier_attribute_scan.py', status: 'idle' }
]);

const activeScans = computed(() => scanners.value.filter(s => s.status === 'running').length);

const healthColor = computed(() => {
  if (healthScore.value >= 90) return 'green-accent-3';
  if (healthScore.value >= 60) return 'amber';
  return 'red-accent-2';
});

const healthStatus = computed(() => {
  if (healthScore.value >= 90) return 'OPTIMAL';
  if (healthScore.value >= 60) return 'STABLE';
  if (healthScore.value > 0) return 'CRITICAL';
  return 'OFFLINE';
});

function getIcon(status) {
  if (status === 'running') return 'mdi-loading';
  if (status === 'success') return 'mdi-check-circle';
  if (status === 'error') return 'mdi-alert-circle';
  return 'mdi-file-document-outline';
}

function getColor(status) {
  if (status === 'running') return 'amber';
  if (status === 'success') return 'green-accent-3';
  if (status === 'error') return 'red-accent-2';
  return 'grey';
}

function addLog(source, message, type = 'info') {
  const timestamp = new Date().toLocaleTimeString('en-GB', { hour12: false, minute: '2-digit', second: '2-digit' });
  let color = 'text-grey-lighten-2';

  if (type === 'success') color = 'text-green-accent-3';
  else if (type === 'error') color = 'text-red-accent-2';
  else if (type === 'warning') color = 'text-amber-accent-3';
  else if (type === 'process') color = 'text-gold';

  logs.value.push({ timestamp, source, message, color });

  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
}

async function runScanner(scanner) {
    if (scanner.status === 'running') return;

    scanner.status = 'running';
    addLog(scanner.filename, 'Initializing scanner protocol...', 'process');

    setTimeout(() => {
        addLog(scanner.filename, 'Reading system vectors...', 'info');
    }, 800);

    setTimeout(() => {
        const success = Math.random() > 0.1;
        if(success) {
            scanner.status = 'success';
            addLog(scanner.filename, 'Integrity Check PASSED.', 'success');
        } else {
            scanner.status = 'error';
            healthScore.value -= 10;
            addLog(scanner.filename, 'Integrity Check FAILED. Mismatch found.', 'error');
        }

        if(activeScans.value === 0) isScanning.value = false;

    }, 2000 + Math.random() * 2000);
}

function runAllScanners() {
    isScanning.value = true;
    healthScore.value = 100;
    logs.value = [];
    addLog('SYSTEM', 'Initiating Global Diagnostics Sequence...', 'process');

    scanners.value.forEach((s, index) => {
        setTimeout(() => {
            runScanner(s);
        }, index * 300);
    });
}

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&display=swap');

.diagnostics-view {
  background-color: #050505;
  background-image:
    linear-gradient(rgba(255, 215, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 215, 0, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
}

.glass-panel {
  background: rgba(15, 15, 15, 0.9) !important;
  backdrop-filter: blur(12px);
  border-radius: 12px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
}

.terminal-card {
  background-color: #000;
  border-radius: 12px;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
}

.border-gold-thin { border: 1px solid rgba(255, 215, 0, 0.15); }
.border-bottom-gold { border-bottom: 1px solid rgba(255, 215, 0, 0.15); }
.border-thin-transparent { border: 1px solid rgba(255, 255, 255, 0.05); }

.text-gold { color: #FFD700 !important; }
.text-gold-dim { color: rgba(255, 215, 0, 0.7) !important; }

.orbitron-font { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; }
.font-mono { font-family: 'Fira Code', monospace !important; }

/* SCANNER ITEM STYLE */
.scanner-item {
    transition: background-color 0.2s;
    cursor: default;
}
.scanner-item:hover {
    background-color: rgba(255, 255, 255, 0.05);
}
.scanner-item.running {
    background-color: rgba(255, 215, 0, 0.1);
    border-color: rgba(255, 215, 0, 0.3);
}

/* TERMINAL DOTS */
.window-dot { width: 10px; height: 10px; border-radius: 50%; }
.window-dot.red { background-color: #ff5f56; }
.window-dot.yellow { background-color: #ffbd2e; }
.window-dot.green { background-color: #27c93f; }

/* ANIMATIONS */
.scan-line {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 2px;
  background: rgba(255, 215, 0, 0.5);
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
  animation: scan 3s linear infinite;
  z-index: 1; pointer-events: none;
}
@keyframes scan {
  0% { top: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

.pulsing-icon { animation: pulse 2s infinite; }
@keyframes pulse {
  0% { text-shadow: 0 0 0 rgba(255, 215, 0, 0.7); }
  50% { text-shadow: 0 0 20px rgba(255, 215, 0, 0.7); opacity: 0.8; }
  100% { text-shadow: 0 0 0 rgba(255, 215, 0, 0.7); }
}

.blink { animation: blinker 1s linear infinite; }
@keyframes blinker { 50% { opacity: 0; } }

.typing-cursor {
  display: inline-block; width: 8px; height: 16px;
  background-color: #FFD700; animation: blinker 1s step-end infinite;
}

/* UTILS */
.log-entry { font-size: 0.8rem; line-height: 1.4; }
.gap-4 { gap: 16px; }

/* CUSTOM SCROLLBAR */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 215, 0, 0.2);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 215, 0, 0.4);
}
</style>
