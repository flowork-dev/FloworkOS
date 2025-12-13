//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\Dashboard.vue total lines 794 
//#######################################################################

<template>
  <div class="dashboard-page">
    <NeuralCanvasBackground />
    <div class="scanner-overlay"></div>
    <div class="vignette-overlay"></div>

    <div class="bg-grid-moving"></div>

    <v-container fluid class="dashboard-container pa-6">

      <div class="hud-header d-flex align-center justify-space-between mb-8">
        <div class="d-flex align-center">
          <div class="hud-logo-mark mr-4">
             <div class="logo-inner-spin"></div>
             <v-icon icon="mdi-console" color="amber-darken-1" size="32" class="relative z-10"></v-icon>
          </div>
          <div>
            <div class="text-h4 font-weight-bold text-white orbitron-font tracking-wide glitch-text" data-text="FLOWORK CORE">
              FLOWORK <span class="text-amber-darken-1">CORE</span>
            </div>
            <div class="d-flex align-center gap-3 mt-1">
               <div class="status-indicator">
                  <div class="pulse-ring"></div>
                  <div class="pulse-dot"></div>
               </div>
               <div class="text-caption font-mono text-grey-lighten-1 typing-effect">
                 SYSTEM::Integrity <span class="text-green-accent-3">[100%]</span>_
               </div>
            </div>
          </div>
        </div>

        <div class="d-flex align-center gap-4">
           <div class="radar-widget hidden-sm-and-down">
              <div class="radar-sweep"></div>
              <div class="radar-grid"></div>
           </div>

           <div class="hud-stat-box text-right hidden-sm-and-down">
              <div class="text-caption font-mono text-grey-darken-1">SERVER_TIME</div>
              <div class="text-body-2 font-mono text-amber-lighten-4">{{ timeString }}</div>
           </div>

           <v-divider vertical color="grey-darken-3" class="mx-2 hidden-sm-and-down" style="height: 30px"></v-divider>

           <div class="d-flex align-center gap-2">
              <v-chip color="amber-darken-4" variant="outlined" class="font-mono bg-black-transparent glass-panel" size="default">
                 <v-icon start icon="mdi-shield-check" size="small" class="blink-slow"></v-icon>
                 SECURE
              </v-chip>
           </div>
        </div>
      </div>

      <div v-if="isInitialLoading" class="d-flex justify-center align-center fill-height" style="min-height: 50vh;">
        <div class="text-center">
           <div class="loader-ring mb-4 mx-auto"></div>
           <div class="text-caption font-mono text-amber-darken-1 blink">INITIALIZING PROTOCOLS...</div>
        </div>
      </div>

      <div v-else-if="error" class="d-flex justify-center align-center" style="min-height: 400px;">
         <div class="text-center text-error border-error pa-8 rounded-lg bg-black-glass glow-red">
            <v-icon icon="mdi-alert-decagram" size="64" color="red-darken-2" class="mb-4"></v-icon>
            <h3 class="orbitron-font text-red-lighten-1 mb-2">SYSTEM FAILURE</h3>
            <p class="font-mono text-grey-lighten-1">{{ error }}</p>
         </div>
      </div>

      <v-row v-else dense class="dashboard-grid">

        <v-col cols="12" lg="3" class="d-flex flex-column gap-4">

          <v-card class="cyber-card identity-card" variant="flat">
             <div class="card-decoration-tl"></div>
             <div class="card-decoration-br"></div>
             <div class="scan-line"></div> <div class="pa-5 relative z-10">
                <div class="d-flex align-start justify-space-between mb-4">
                   <div class="avatar-container">
                       <v-avatar size="64" rounded="0" class="border-amber avatar-glow bg-grey-darken-4">
                          <span class="text-h4 font-weight-black text-amber-darken-1 orbitron-font">
                             {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
                          </span>
                       </v-avatar>
                       <div class="avatar-ring"></div>
                   </div>
                   <v-chip size="x-small" color="amber-darken-1" variant="outlined" class="font-mono">LOCAL_ADMIN</v-chip>
                </div>

                <div class="mb-4">
                   <div class="text-overline text-grey-darken-1 lh-1">OPERATOR</div>
                   <div class="text-h6 font-weight-bold text-white text-truncate font-mono">
                      {{ authStore.user?.username || 'GHOST_UNIT' }}
                   </div>
                   <div class="text-caption text-amber-darken-3 font-mono mt-1">ID: {{ formatUserId(authStore.user?.id) }}</div>
                </div>

                <v-divider class="mb-3 border-dashed"></v-divider>

                <div class="d-flex justify-space-between mb-2">
                   <span class="text-caption text-grey-darken-1 font-mono">MODE</span>
                   <span class="text-caption text-white font-mono">DESKTOP LITE</span>
                </div>
                <div class="d-flex justify-space-between">
                   <span class="text-caption text-grey-darken-1 font-mono">STATUS</span>
                   <span class="text-caption text-amber-lighten-4 font-mono">ONLINE</span>
                </div>
             </div>
          </v-card>

          <v-card class="cyber-card" variant="flat">
            <div class="card-header">
               <span class="header-icon"><v-icon icon="mdi-memory" size="x-small"></v-icon></span>
               <span class="header-title">SYSTEM_INVENTORY</span>
            </div>
            <div class="pa-4 pt-2">
               <div class="spec-grid">
                  <div class="spec-item">
                     <div class="spec-val text-amber-darken-1">{{ summary.system_overview?.modules || 0 }}</div>
                     <div class="spec-label">MODULES</div>
                  </div>
                  <div class="spec-item">
                     <div class="spec-val text-blue-lighten-2">{{ summary.system_overview?.plugins || 0 }}</div>
                     <div class="spec-label">PLUGINS</div>
                  </div>
                  <div class="spec-item">
                     <div class="spec-val text-green-lighten-2">{{ summary.system_overview?.triggers || 0 }}</div>
                     <div class="spec-label">TRIGGERS</div>
                  </div>
                  <div class="spec-item">
                     <div class="spec-val text-purple-lighten-2">{{ summary.system_overview?.presets || 0 }}</div>
                     <div class="spec-label">PRESETS</div>
                  </div>
               </div>
               <v-divider class="my-3 border-dashed"></v-divider>
               <div class="d-flex justify-space-between align-center">
                  <span class="text-caption text-grey-darken-1 font-mono">KERNEL_VER</span>
                  <span class="text-caption text-mono text-white">{{ summary.system_overview?.kernel_version || 'LITE' }}</span>
               </div>
            </div>
          </v-card>

          <v-card class="cyber-card flex-grow-1" variant="flat">
             <div class="card-header">
                <span class="header-icon"><v-icon icon="mdi-flash" size="x-small"></v-icon></span>
                <span class="header-title">QUICK_DEPLOY</span>
             </div>
             <div class="scroll-container" style="height: 200px;">
                <div class="pa-3">
                    <div v-if="favoritePresets.length === 0" class="text-center pa-4 dashed-box opacity-50">
                       <div class="text-caption font-mono text-grey">NO SHORTCUTS DEFINED</div>
                    </div>
                    <div v-else class="d-flex flex-column gap-2">
                       <v-btn
                         v-for="presetName in favoritePresets"
                         :key="presetName"
                         @click="workflowStore.executePresetByName(presetName)"
                         block
                         height="36"
                         class="preset-btn"
                         :disabled="isExecuting || !isEngineOnline"
                       >
                         <div class="d-flex justify-space-between align-center w-100 px-1">
                            <span class="font-mono text-caption text-truncate">{{ presetName }}</span>
                            <v-icon icon="mdi-play" size="small" color="amber-darken-1"></v-icon>
                         </div>
                       </v-btn>
                    </div>
                </div>
             </div>
          </v-card>

        </v-col>

        <v-col cols="12" lg="6" class="d-flex flex-column gap-4">

          <v-card class="cyber-card" variant="flat">
             <div class="card-header justify-space-between">
                <div>
                   <span class="header-icon"><v-icon icon="mdi-server-network" size="x-small"></v-icon></span>
                   <span class="header-title">LIVE_TELEMETRY</span>
                </div>
                <div v-if="selectedEngine" class="d-flex align-center gap-2">
                   <span class="text-caption font-mono text-amber-darken-1">{{ selectedEngine.name }}</span>
                   <div class="status-dot-active blink"></div>
                </div>
             </div>

             <v-card-text class="pa-4 bg-grid-pattern relative">

                <div v-if="!selectedEngine" class="d-flex flex-column align-center justify-center py-10">
                   <v-icon icon="mdi-server-off" size="48" color="grey-darken-3" class="mb-3"></v-icon>
                   <div class="text-caption font-mono text-grey">ENGINE OFFLINE</div>
                   <v-btn variant="outlined" color="amber-darken-3" size="small" class="mt-3 font-mono" @click="reconnect">
                      RETRY CONNECTION
                   </v-btn>
                </div>

                <div v-else>
                   <v-row align="center">
                      <v-col cols="12" md="4" class="d-flex justify-center">
                          <div class="globe-container">
                              <div class="wireframe-globe"></div>
                              <div class="globe-grid"></div>
                              <div class="globe-marker"></div>
                          </div>
                      </v-col>

                      <v-col cols="12" md="8">
                          <v-row dense>
                              <v-col cols="6" sm="3" class="text-center">
                                 <div class="chart-container">
                                    <Doughnut :data="getCpuChartData(selectedEngine)" :options="donutOptions" />
                                    <div class="chart-value">
                                       <div class="text-h6 font-weight-bold text-white orbitron-font">{{ (selectedEngine.vitals?.cpu_percent || 0).toFixed(0) }}%</div>
                                       <div class="text-caption2 text-grey-darken-1 font-mono">CPU</div>
                                    </div>
                                 </div>
                              </v-col>

                              <v-col cols="6" sm="3" class="text-center">
                                 <div class="chart-container">
                                    <Doughnut :data="getRamChartData(selectedEngine)" :options="donutOptions" />
                                    <div class="chart-value">
                                       <div class="text-h6 font-weight-bold text-white orbitron-font">{{ (selectedEngine.vitals?.ram_percent || 0).toFixed(0) }}%</div>
                                       <div class="text-caption2 text-grey-darken-1 font-mono">RAM</div>
                                    </div>
                                 </div>
                              </v-col>

                              <v-col cols="6" sm="3" class="text-center">
                                 <div class="chart-container">
                                    <Doughnut :data="getThermalChartData(selectedEngine)" :options="donutOptions" />
                                    <div class="chart-value">
                                       <div class="text-h6 font-weight-bold text-white orbitron-font">{{ getSimulatedTemp(selectedEngine) }}°</div>
                                       <div class="text-caption2 text-grey-darken-1 font-mono">TEMP</div>
                                    </div>
                                 </div>
                              </v-col>

                              <v-col cols="6" sm="3" class="text-center">
                                 <div class="chart-container">
                                    <Doughnut :data="getLoadChartData(selectedEngine)" :options="donutOptions" />
                                    <div class="chart-value">
                                       <div class="text-h6 font-weight-bold text-white orbitron-font">{{ selectedEngine.status === 'online' ? 'ON' : 'OFF' }}</div>
                                       <div class="text-caption2 text-grey-darken-1 font-mono">PWR</div>
                                    </div>
                                 </div>
                              </v-col>
                          </v-row>
                      </v-col>
                   </v-row>

                   <v-divider class="my-4 border-dashed"></v-divider>

                   <div style="height: 150px; position: relative;" class="mt-2">
                      <div class="d-flex justify-space-between align-center mb-1">
                          <div class="text-caption font-mono text-grey-darken-2">>> JOB_HISTORY_24H</div>
                          <div class="text-caption2 font-mono text-amber-darken-1 blink">MONITORING_ACTIVE...</div>
                      </div>
                      <Bar v-if="chartData.datasets[0].data.some(v => v > 0)" :data="chartData" :options="barChartOptions" />
                      <div v-else class="empty-chart-overlay">
                         <div class="text-caption font-mono text-grey-darken-3 blink">NO DATA</div>
                      </div>
                   </div>
                </div>
             </v-card-text>
          </v-card>

          <v-card class="cyber-card flex-grow-1" variant="flat">
             <div class="card-header">
                <span class="header-icon"><v-icon icon="mdi-console-line" size="x-small"></v-icon></span>
                <span class="header-title">PROCESS_TERMINAL (LIVE)</span>
             </div>
             <v-card-text class="pa-0 terminal-bg relative">
                <div class="matrix-rain-overlay"></div> <div class="terminal-scroll-area custom-scrollbar">
                    <div v-if="!summary.active_jobs || summary.active_jobs.length === 0" class="d-flex align-center justify-center fill-height" style="min-height: 150px;">
                       <div class="text-caption font-mono text-grey-darken-2 opacity-50">>> SYSTEM_IDLE // WAITING_FOR_COMMAND</div>
                    </div>

                    <v-table v-else density="compact" class="bg-transparent terminal-table font-mono">
                        <tbody>
                            <tr v-for="job in summary.active_jobs" :key="job.id" class="terminal-row">
                                <td style="width: 20px;" class="text-amber-darken-3">></td>
                                <td class="text-white">
                                    <span class="text-green-accent-3">EXEC</span> {{ job.preset }}
                                    <div class="text-caption2 text-grey-darken-2">{{ job.id.substring(0,8) }}</div>
                                </td>
                                <td class="text-grey-lighten-1 text-right">{{ job.duration_seconds.toFixed(1) }}s</td>
                                <td class="text-right" style="width: 40px;">
                                   <v-btn
                                     icon="mdi-close"
                                     color="red-darken-3"
                                     variant="text"
                                     size="x-small"
                                     @click="workflowStore.stopJobById(job.id)"
                                     title="KILL"
                                   ></v-btn>
                                </td>
                            </tr>
                        </tbody>
                    </v-table>
                </div>
             </v-card-text>
          </v-card>

        </v-col>

        <v-col cols="12" lg="3" class="d-flex flex-column gap-4">

           <v-card class="cyber-card" variant="flat">
              <div class="card-header">
                 <span class="header-icon"><v-icon icon="mdi-lan" size="x-small"></v-icon></span>
                 <span class="header-title">NETWORK_NODES</span>
              </div>
              <v-card-text class="pa-0">
                 <div class="scroll-container" style="height: 250px;">
                     <div class="pa-2">
                         <div
                           class="engine-item mb-2 selected online"
                         >
                             <div class="d-flex align-center justify-space-between w-100">
                                <div class="d-flex align-center">
                                   <v-icon icon="mdi-desktop-classic" size="small" class="text-amber-darken-1 mr-3"></v-icon>
                                   <div>
                                      <div class="text-caption font-weight-bold text-white font-mono">LOCAL_DESKTOP</div>
                                      <div class="text-caption2 text-grey-darken-1 font-mono">PRIMARY</div>
                                   </div>
                                </div>
                                <v-icon icon="mdi-check-circle-outline" color="amber-darken-3" size="small"></v-icon>
                             </div>
                             <div class="engine-line mt-2" :style="{width: (selectedEngine?.vitals?.cpu_percent || 0) + '%', backgroundColor: '#FFC107'}"></div>
                         </div>
                     </div>
                 </div>
              </v-card-text>
           </v-card>

           <v-card class="cyber-card flex-grow-1" variant="flat">
              <div class="card-header">
                 <span class="header-icon"><v-icon icon="mdi-bug-outline" size="x-small"></v-icon></span>
                 <span class="header-title">SYSTEM_DIAGNOSTICS</span>
              </div>
              <v-card-text class="pa-0">
                 <div class="scroll-container" style="height: 200px;">
                     <div class="pa-3">
                         <div v-if="(!summary.top_failing_presets?.length) && (!summary.top_slowest_presets?.length)" class="d-flex flex-column align-center justify-center py-6 opacity-50">
                             <v-icon icon="mdi-check-all" color="green-darken-2" size="32" class="mb-2"></v-icon>
                             <span class="text-caption font-mono text-green-darken-1">SYSTEM OPTIMAL</span>
                         </div>
                         <div v-else class="font-mono">
                             <div v-if="summary.top_failing_presets?.length" class="mb-3">
                                <div class="text-caption2 text-red-darken-1 mb-1 border-bottom-subtle">>> ERROR_LOGS</div>
                                <div v-for="item in summary.top_failing_presets" :key="'fail-'+item.name" class="d-flex justify-space-between align-center my-1 text-caption">
                                   <span class="text-grey-lighten-1 text-truncate" style="max-width: 60%;">{{ item.name }}</span>
                                   <span class="text-red-accent-2">{{ item.count }}X</span>
                                </div>
                             </div>
                             <div v-if="summary.top_slowest_presets?.length">
                                <div class="text-caption2 text-amber-darken-3 mb-1 border-bottom-subtle">>> LATENCY_SPIKES</div>
                                <div v-for="item in summary.top_slowest_presets" :key="'slow-'+item.name" class="d-flex justify-space-between align-center my-1 text-caption">
                                   <span class="text-grey-lighten-1 text-truncate" style="max-width: 60%;">{{ item.name }}</span>
                                   <span class="text-amber-lighten-1">{{ item.avg_duration_ms.toFixed(0) }}ms</span>
                                </div>
                             </div>
                         </div>
                     </div>
                 </div>
              </v-card-text>
           </v-card>

        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed, ref } from 'vue';
import { useDashboardStore } from '@/store/dashboard';
import { useSocketStore } from '@/store/socket'; // [ADDED] Pengganti EngineStore
import { useWorkflowStore } from '@/store/workflow';
import { useAuthStore } from '@/store/auth';
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';
import { Bar, Doughnut } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement
} from 'chart.js';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

const dashboardStore = useDashboardStore();
const socketStore = useSocketStore();
const workflowStore = useWorkflowStore();
const authStore = useAuthStore();
const uiStore = useUiStore();

const { summary, isInitialLoading, error } = storeToRefs(dashboardStore);
const { favoritePresets, isExecuting } = storeToRefs(workflowStore);

const isEngineOnline = computed(() => socketStore.isConnected);

const selectedEngine = computed(() => {
    if (!socketStore.isConnected) return null;
    return {
        id: 'local',
        name: 'Local Desktop',
        status: 'online',
        vitals: socketStore.currentEngineStatus
    };
});

const timeString = ref(new Date().toLocaleTimeString());

let refreshInterval = null;
let clockInterval = null;

function formatUserId(id) {
    if (!id) return 'UNKNOWN';
    return id.substring(0, 8) + '...' + id.substring(id.length - 4);
}

function reconnect() {
    socketStore.connect();
}

const donutOptions = {
    responsive: true,
    cutout: '75%',
    plugins: {
       legend: { display: false },
       tooltip: { enabled: false }
    },
    maintainAspectRatio: false,
    borderColor: '#000000',
    borderWidth: 2
};

const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
        x: {
            display: true,
            ticks: { color: '#616161', font: { family: 'Fira Code', size: 9 } },
            grid: { display: false }
        },
        y: {
            display: true,
            ticks: { color: '#616161', stepSize: 5, font: { family: 'Fira Code', size: 9 } },
            grid: { color: 'rgba(255, 255, 255, 0.03)' }
        }
    },
    elements: {
       bar: { borderRadius: 2 }
    }
};

function getCpuChartData(engine) {
    const usage = engine?.vitals?.cpu_percent || 0;
    return {
        labels: ['Used', 'Free'],
        datasets: [{
            data: [usage, 100 - usage],
            backgroundColor: ['#FFC107', 'rgba(255, 255, 255, 0.05)'],
            hoverBackgroundColor: ['#FFD54F', 'rgba(255, 255, 255, 0.05)'],
            borderWidth: 0
        }]
    };
}
function getRamChartData(engine) {
    const usage = engine?.vitals?.ram_percent || 0;
    return {
        labels: ['Used', 'Free'],
        datasets: [{
            data: [usage, 100 - usage],
            backgroundColor: ['#00E676', 'rgba(255, 255, 255, 0.05)'],
            hoverBackgroundColor: ['#69F0AE', 'rgba(255, 255, 255, 0.05)'],
            borderWidth: 0
        }]
    };
}
function getThermalChartData(engine) {
    const cpu = engine?.vitals?.cpu_percent || 0;
    const simTemp = 40 + (cpu * 0.4);
    const maxTemp = 90;
    let color = '#29B6F6';
    if(simTemp > 60) color = '#FFC107';
    if(simTemp > 80) color = '#FF5252';
    return {
        labels: ['Temp', 'Limit'],
        datasets: [{
            data: [simTemp, maxTemp - simTemp],
            backgroundColor: [color, 'rgba(255, 255, 255, 0.05)'],
            borderWidth: 0
        }]
    };
}
function getSimulatedTemp(engine) {
    const cpu = engine?.vitals?.cpu_percent || 0;
    return Math.round(40 + (cpu * 0.4));
}
function getLoadChartData(engine) {
    const online = engine?.status === 'online';
    return {
        datasets: [{
            data: [online ? 100 : 0, online ? 0 : 100],
            backgroundColor: ['#E0E0E0', 'rgba(255, 255, 255, 0.05)'],
            borderWidth: 0
        }]
    };
}

const chartData = computed(() => {
    const ts = summary.value?.execution_stats_24h || { success: 0, failed: 0 };
    return {
        labels: ['SUCCESS', 'FAIL'],
        datasets: [{
            label: 'Jobs',
            backgroundColor: ['rgba(255, 193, 7, 0.6)', 'rgba(211, 47, 47, 0.6)'],
            borderColor: ['#FFC107', '#D32F2F'],
            borderWidth: 1,
            data: [ts.success || 0, ts.failed || 0],
            barThickness: 30,
        }]
    }
});

onMounted(async () => {
  clockInterval = setInterval(() => {
     timeString.value = new Date().toLocaleTimeString();
  }, 1000);


  dashboardStore.fetchDashboardSummary(false);

  refreshInterval = setInterval(() => {
    if (authStore.isAuthenticated) {
        dashboardStore.fetchDashboardSummary(true);
    }
  }, 5000);
});

onUnmounted(() => {
  clearInterval(refreshInterval);
  clearInterval(clockInterval);
});
</script>

<style scoped>
/* IMPORTS */
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&display=swap');

/* GLOBAL LAYOUT */
.dashboard-page {
  height: 100%;
  padding: 0;
  position: relative;
  z-index: 1;
  background-color: #050505;
  color: #e0e0e0;
  overflow: hidden; /* Prevent body scroll */
}

/* BACKGROUND FX */
.bg-grid-moving {
    position: absolute; top: 0; left: 0; width: 200%; height: 200%;
    background-image:
        linear-gradient(rgba(255, 193, 7, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 193, 7, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    transform: perspective(500px) rotateX(60deg);
    animation: gridMove 20s linear infinite;
    pointer-events: none; z-index: 0;
}
@keyframes gridMove { 0% { transform: perspective(500px) rotateX(60deg) translateY(0); } 100% { transform: perspective(500px) rotateX(60deg) translateY(40px); } }

.scanner-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(rgba(18, 18, 18, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
    background-size: 100% 2px, 3px 100%;
    pointer-events: none; z-index: 0;
}
.vignette-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle, transparent 50%, rgba(0,0,0,0.9) 100%);
    pointer-events: none; z-index: 1;
}

.dashboard-container {
    position: relative; z-index: 2; height: 100%; overflow-y: auto;
}

/* TYPOGRAPHY & HEADER */
.orbitron-font { font-family: 'Orbitron', sans-serif; letter-spacing: 1px; }
.font-mono { font-family: 'Fira Code', monospace; }
.tracking-wide { letter-spacing: 2px; }
.lh-1 { line-height: 1.2; }
.text-caption2 { font-size: 0.65rem; }

.hud-logo-mark {
    position: relative;
    border: 1px solid rgba(255, 193, 7, 0.3);
    padding: 8px;
    background: rgba(255, 193, 7, 0.05);
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
}
.logo-inner-spin {
    position: absolute; top: 2px; left: 2px; right: 2px; bottom: 2px;
    border: 1px dashed rgba(255, 193, 7, 0.5);
    border-radius: 4px;
    animation: spin 10s linear infinite;
}

/* RADAR WIDGET ANIMATION */
.radar-widget {
    width: 60px; height: 60px;
    border: 2px solid rgba(255, 193, 7, 0.3);
    border-radius: 50%;
    position: relative;
    background: rgba(0, 20, 0, 0.5);
    box-shadow: 0 0 10px rgba(255, 193, 7, 0.1);
    overflow: hidden;
}
.radar-grid {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background-image: radial-gradient(transparent 60%, rgba(255, 193, 7, 0.2) 60%),
                      linear-gradient(0deg, transparent 49%, rgba(255, 193, 7, 0.2) 50%, transparent 51%),
                      linear-gradient(90deg, transparent 49%, rgba(255, 193, 7, 0.2) 50%, transparent 51%);
    background-size: 100% 100%, 100% 100%, 100% 100%;
    border-radius: 50%;
}
.radar-sweep {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: conic-gradient(from 0deg, transparent 0deg, rgba(255, 193, 7, 0.4) 30deg, transparent 30deg);
    border-radius: 50%;
    animation: spin 2s linear infinite;
}

/* HOLOGRAPHIC GLOBE ANIMATION (CSS ONLY) */
.globe-container {
    width: 100px; height: 100px;
    position: relative;
    perspective: 800px;
    margin: 10px;
}
.wireframe-globe {
    width: 100%; height: 100%;
    border-radius: 50%;
    border: 1px solid rgba(255, 193, 7, 0.3);
    position: absolute;
    box-shadow: 0 0 20px rgba(255, 193, 7, 0.1) inset;
    background:
        repeating-linear-gradient(0deg, transparent 0, transparent 10px, rgba(255, 193, 7, 0.1) 10px, rgba(255, 193, 7, 0.1) 11px),
        repeating-linear-gradient(90deg, transparent 0, transparent 10px, rgba(255, 193, 7, 0.1) 10px, rgba(255, 193, 7, 0.1) 11px);
    background-size: 200% 200%;
    animation: globeRotate 10s linear infinite;
}
.globe-grid {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    border-radius: 50%;
    border: 1px dashed rgba(255, 193, 7, 0.5);
    transform: rotateX(60deg);
    animation: spin 5s linear infinite;
}
@keyframes globeRotate {
    0% { background-position: 0 0; }
    100% { background-position: 100px 0; }
}

/* CARDS & PANELS */
.cyber-card {
  background: rgba(10, 10, 10, 0.9) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  color: white;
  transition: all 0.3s ease;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  display: flex; flex-direction: column;
}
.cyber-card:hover { border-color: rgba(255, 193, 7, 0.4); box-shadow: 0 0 15px rgba(255, 193, 7, 0.15); }

/* SCROLL CONTAINERS (INDEPENDENT SCROLL) */
.scroll-container {
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 193, 7, 0.3) transparent;
}
.scroll-container::-webkit-scrollbar { width: 4px; }
.scroll-container::-webkit-scrollbar-thumb { background-color: rgba(255, 193, 7, 0.3); border-radius: 2px; }
.scroll-container::-webkit-scrollbar-track { background: transparent; }

.terminal-scroll-area {
    height: 200px; /* Fixed height for terminal */
    overflow-y: auto;
    overflow-x: hidden;
}

/* IDENTITY CARD FX */
.identity-card { border-top: 2px solid #FFC107; }
.card-decoration-tl { position: absolute; top: 0; left: 0; width: 20px; height: 20px; border-top: 2px solid #FFC107; border-left: 2px solid #FFC107; opacity: 0.5; }
.card-decoration-br { position: absolute; bottom: 0; right: 0; width: 20px; height: 20px; border-bottom: 2px solid #FFC107; border-right: 2px solid #FFC107; opacity: 0.5; }
.scan-line {
    position: absolute; width: 100%; height: 2px; background: rgba(255, 193, 7, 0.5);
    box-shadow: 0 0 10px rgba(255, 193, 7, 0.8);
    top: 0; left: 0;
    animation: scanDown 4s linear infinite;
    pointer-events: none; opacity: 0.3;
}
@keyframes scanDown { 0% { top: -10%; opacity: 0; } 50% { opacity: 0.5; } 100% { top: 110%; opacity: 0; } }

/* AVATAR RING */
.avatar-container { position: relative; width: 64px; height: 64px; }
.avatar-ring {
    position: absolute; top: -5px; left: -5px; right: -5px; bottom: -5px;
    border: 1px dashed rgba(255, 193, 7, 0.3);
    border-radius: 50%;
    animation: spin 20s linear infinite;
}

/* TERMINAL FX */
.terminal-bg { background: #080808; border-top: 1px solid rgba(255,255,255,0.05); }
.terminal-table { background: transparent !important; }
.terminal-table td { border: none !important; font-size: 0.75rem; color: #ccc; padding: 0 8px !important; height: 24px !important; }
.terminal-row:hover td { background: rgba(255, 193, 7, 0.05); color: #FFC107; }

.matrix-rain-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: repeating-linear-gradient(0deg, rgba(0,0,0,0) 0, rgba(0,0,0,0) 2px, rgba(0, 255, 0, 0.03) 2px, rgba(0, 255, 0, 0.03) 4px);
    pointer-events: none;
    animation: rain 1s linear infinite;
    opacity: 0.3;
}
@keyframes rain { from { background-position: 0 0; } to { background-position: 0 20px; } }

/* UTILS */
.glass-panel { backdrop-filter: blur(4px); }
.status-indicator { position: relative; width: 12px; height: 12px; display: flex; align-items: center; justify-content: center; }
.pulse-dot { width: 6px; height: 6px; background: #00E676; border-radius: 50%; }
.pulse-ring { position: absolute; width: 100%; height: 100%; border: 1px solid #00E676; border-radius: 50%; animation: pulse 2s infinite; }
.gap-2 { gap: 8px; } .gap-3 { gap: 12px; } .gap-4 { gap: 16px; }
.w-100 { width: 100%; }
.chart-container { position: relative; height: 80px; width: 80px; margin: 0 auto; }
.chart-value { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none; }
.empty-chart-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); }
.status-dot-active { width: 8px; height: 8px; background: #FFC107; border-radius: 50%; box-shadow: 0 0 5px #FFC107; }
.border-dashed { border-style: dashed !important; border-color: rgba(255, 255, 255, 0.1) !important; }
.dashed-box { border: 1px dashed rgba(255,255,255,0.2); border-radius: 4px; }

/* ENGINE LIST */
.engine-item { padding: 8px 12px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: all 0.2s; border-radius: 4px; }
.engine-item:hover { background: rgba(255, 255, 255, 0.05); }
.engine-item.selected { border-color: rgba(255, 193, 7, 0.5); background: linear-gradient(90deg, rgba(255, 193, 7, 0.05), transparent); }
.engine-line { height: 2px; border-radius: 1px; transition: width 0.5s ease; }

/* PRESET BTN */
.preset-btn { border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.02) !important; text-transform: none !important; transition: all 0.2s; }
.preset-btn:hover { border-color: #FFC107; color: #FFC107; background: rgba(255, 193, 7, 0.05) !important; }

/* ANIMATIONS */
@keyframes pulse { 0% { transform: scale(0.8); opacity: 1; } 100% { transform: scale(2); opacity: 0; } }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.blink { animation: blinker 1.5s linear infinite; }
.blink-slow { animation: blinker 3s linear infinite; }
@keyframes blinker { 50% { opacity: 0.3; } }
.loader-ring { width: 40px; height: 40px; border: 3px solid rgba(255, 193, 7, 0.3); border-radius: 50%; border-top-color: #FFC107; animation: spin 1s ease-in-out infinite; }

/* CUSTOM SCROLLBAR GLOBAL */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: rgba(255, 255, 255, 0.1); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
</style>
