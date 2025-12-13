//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\DebugPopup.vue total lines 292 
//#######################################################################

<template>
  <v-dialog
    v-model="isOpen"
    :max-width="800"
    :persistent="autoCloseTimer > 0"
    class="debug-popup-dialog"
    transition="dialog-bottom-transition"
  >
    <div :class="['debug-container', currentThemeClass]">

      <div v-if="isRetro" class="crt-scanline"></div>
      <div v-if="isRetro" class="crt-flicker"></div>

      <div class="debug-header d-flex align-center justify-space-between pa-4">
        <div class="d-flex align-center">
          <v-icon :icon="headerIcon" :color="themeColor" class="mr-3 icon-pulse"></v-icon>
          <span class="text-h6 font-weight-bold font-mono glitch-text" :data-text="title">
            {{ title }}
          </span>
        </div>
        <div class="d-flex align-center">
          <span v-if="timeLeft > 0" class="text-caption mr-3 text-red font-weight-bold blink-text">
            CLOSING IN {{ timeLeft }}s
          </span>
          <v-btn icon variant="text" @click="closePopup" :color="themeColor">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
      </div>

      <v-divider :color="themeColor"></v-divider>

      <div class="debug-content pa-4">
        <div class="code-wrapper">
            <div class="line-numbers text-grey-darken-2 text-caption mr-2 text-end">
               <div v-for="n in 10" :key="n">{{ n * 10 }}</div>
            </div>
            <pre class="code-block" :style="{ color: themeTextColor }">{{ content }}</pre>
        </div>
      </div>

      <div class="debug-footer pa-2 px-4 d-flex justify-space-between align-center">
        <div class="text-caption text-grey">
          <v-icon size="x-small" class="mr-1">mdi-server-network</v-icon>
          ENGINE::RUNTIME_EVENT
        </div>
        <v-btn
          size="small"
          variant="outlined"
          :color="themeColor"
          class="hacker-btn"
          @click="copyToClipboard"
        >
          <v-icon start>mdi-content-copy</v-icon>
          COPY DATA
        </v-btn>
      </div>
    </div>
  </v-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useSocketStore } from '@/store/socket';

const socketStore = useSocketStore();

const isOpen = ref(false);
const title = ref('System Message');
const content = ref('');
const theme = ref('Default');
const autoCloseTimer = ref(0);
const timeLeft = ref(0);
let intervalId = null;

const currentThemeClass = computed(() => {
  const t = theme.value.toLowerCase();
  if (t.includes('matrix')) return 'theme-matrix';
  if (t.includes('cyberpunk')) return 'theme-cyberpunk';
  if (t.includes('minimalist')) return 'theme-minimalist';
  return 'theme-default';
});

const isRetro = computed(() => {
  return currentThemeClass.value === 'theme-matrix' || currentThemeClass.value === 'theme-cyberpunk';
});

const themeColor = computed(() => {
  if (currentThemeClass.value === 'theme-matrix') return '#00ff00';
  if (currentThemeClass.value === 'theme-cyberpunk') return '#00f3ff';
  return 'white';
});

const themeTextColor = computed(() => {
  if (currentThemeClass.value === 'theme-matrix') return '#00ff00';
  if (currentThemeClass.value === 'theme-cyberpunk') return '#e0fbfc';
  return '#e0e0e0';
});

const headerIcon = computed(() => {
  if (currentThemeClass.value === 'theme-matrix') return 'mdi-console';
  if (currentThemeClass.value === 'theme-cyberpunk') return 'mdi-robot-industrial';
  return 'mdi-information-outline';
});

let offListener = null;

function setupListener() {
  if (!socketStore.socket) return;

  const handler = (payload) => {
    if (payload.event === 'SHOW_DEBUG_POPUP' || (payload.type && payload.type.includes('DEBUG'))) {
        const data = payload.payload || payload; // Handle wrapped or raw

        title.value = data.title || 'Debug Info';

        if (typeof data.content === 'object') {
            content.value = JSON.stringify(data.content, null, 2);
        } else {
            content.value = data.content;
        }

        const config = data.config || {};
        theme.value = config.theme || 'Default';
        autoCloseTimer.value = config.auto_close || 0;

        openPopup();
    }
  };

  socketStore.socket.on('SHOW_DEBUG_POPUP', handler);
  socketStore.socket.on('message', (msg) => {
      if(msg.type === 'SHOW_DEBUG_POPUP') handler(msg);
  });

  return () => {
    socketStore.socket.off('SHOW_DEBUG_POPUP', handler);
  };
}

function openPopup() {
  isOpen.value = true;

  if (autoCloseTimer.value > 0) {
    timeLeft.value = autoCloseTimer.value;
    if (intervalId) clearInterval(intervalId);

    intervalId = setInterval(() => {
      timeLeft.value--;
      if (timeLeft.value <= 0) {
        closePopup();
      }
    }, 1000);
  }
}

function closePopup() {
  isOpen.value = false;
  if (intervalId) clearInterval(intervalId);
}

function copyToClipboard() {
  navigator.clipboard.writeText(content.value);
}

watch(() => socketStore.isConnected, (connected) => {
  if (connected) {
    if (offListener) offListener();
    offListener = setupListener();
  }
});

onMounted(() => {
  if (socketStore.isConnected) {
    offListener = setupListener();
  }
});

onUnmounted(() => {
  if (offListener) offListener();
  if (intervalId) clearInterval(intervalId);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Orbitron:wght@500;900&display=swap');

.debug-popup-dialog {
  overflow: hidden;
}

.debug-container {
  position: relative;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
  overflow: hidden;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.font-mono { font-family: 'Orbitron', sans-serif; letter-spacing: 1px; }
.code-wrapper { display: flex; height: 400px; overflow: hidden; font-family: 'Fira Code', monospace; }
.code-block { overflow: auto; width: 100%; font-size: 0.85rem; line-height: 1.5; }
.line-numbers { opacity: 0.3; font-size: 0.8rem; padding-top: 2px; user-select: none; }

/* --- THEME: DEFAULT --- */
.theme-default {
  background-color: #1e1e2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
}

/* --- THEME: MATRIX GREEN --- */
.theme-matrix {
  background-color: #000000;
  border: 2px solid #00ff00;
  box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
  color: #00ff00;
}
.theme-matrix .debug-header { background-color: rgba(0, 255, 0, 0.1); }
.theme-matrix .hacker-btn { border-color: #00ff00; color: #00ff00; }

/* --- THEME: CYBERPUNK NEON --- */
.theme-cyberpunk {
  background-color: #0b001a;
  border: 2px solid #00f3ff;
  box-shadow: 0 0 15px #00f3ff, inset 0 0 20px rgba(255, 0, 255, 0.1);
  color: #00f3ff;
}
.theme-cyberpunk .debug-header {
  background: linear-gradient(90deg, rgba(0, 243, 255, 0.2), transparent);
  border-bottom: 1px solid #ff00ff;
}

/* --- ANIMATIONS (CRT / GLITCH) --- */
.crt-scanline {
  width: 100%; height: 100px; z-index: 10;
  background: linear-gradient(0deg, rgba(0,0,0,0) 0%, rgba(255, 255, 255, 0.04) 50%, rgba(0,0,0,0) 100%);
  opacity: 0.1; position: absolute; bottom: 100%;
  animation: scanline 10s linear infinite; pointer-events: none;
}
.crt-flicker {
  width: 100%; height: 100%; position: absolute; z-index: 9;
  background: rgba(18, 16, 16, 0.02); opacity: 0; pointer-events: none;
  animation: flicker 0.15s infinite;
}

@keyframes scanline {
  0% { bottom: 100%; }
  100% { bottom: -100%; }
}
@keyframes flicker {
  0% { opacity: 0.02; }
  50% { opacity: 0.05; }
  100% { opacity: 0.02; }
}

.icon-pulse { animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

.blink-text { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0; } }

.glitch-text {
  position: relative;
}
.glitch-text::before, .glitch-text::after {
  content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.8;
}
.theme-cyberpunk .glitch-text::before {
  color: #ff00ff; z-index: -1; animation: glitch-anim-1 2s infinite linear alternate-reverse;
}
.theme-cyberpunk .glitch-text::after {
  color: #00f3ff; z-index: -2; animation: glitch-anim-2 3s infinite linear alternate-reverse;
}

@keyframes glitch-anim-1 {
  0% { clip-path: inset(20% 0 80% 0); transform: translate(-2px, 1px); }
  100% { clip-path: inset(60% 0 10% 0); transform: translate(2px, -1px); }
}
@keyframes glitch-anim-2 {
  0% { clip-path: inset(10% 0 60% 0); transform: translate(1px, 1px); }
  100% { clip-path: inset(80% 0 5% 0); transform: translate(-1px, -2px); }
}
</style>
