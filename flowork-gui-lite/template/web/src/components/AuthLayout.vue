//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\AuthLayout.vue total lines 148 
//#######################################################################

<template>
  <div class="auth-wrapper">
    <DigitalFingerprintBackground />
    <v-container class="fill-height" fluid>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="4">
          <v-card class="elevation-12 auth-card" ref="cardEl" :style="cardStyle">
            <v-toolbar class="auth-toolbar" color="transparent" dark flat>
              <v-toolbar-title class="text-center orbitron-font">{{ displayedTitle }}</v-toolbar-title>
            </v-toolbar>
            <v-card-text class="pa-4">
              <slot name="form-fields"></slot>
            </v-card-text>
            <v-card-actions class="pa-4 pt-0">
              <slot name="actions"></slot>
            </v-card-actions>
             <div class="text-center pa-2">
                <router-link :to="switchLink" class="switch-mode-link">
                    {{ switchText }}
                </router-link>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import DigitalFingerprintBackground from '@/components/DigitalFingerprintBackground.vue';

const props = defineProps({
  title: String,
  switchText: String,
  switchLink: String,
});

const cardEl = ref(null);
const cardStyle = ref({});
const displayedTitle = ref('');

onMounted(() => {
  let i = 0;
  const typing = setInterval(() => {
    if (i < props.title.length) {
      displayedTitle.value += props.title.charAt(i);
      i++;
    } else {
      clearInterval(typing);
    }
  }, 100);
});

const handleMouseMove = (e) => {
  if (!cardEl.value) return;
  const { clientX, clientY } = e;
  const { top, left, width, height } = cardEl.value.$el.getBoundingClientRect();
  const x = (clientX - left - width / 2) / (width / 2);
  const y = (clientY - top - height / 2) / (height / 2);
  const rotateY = 15 * x;
  const rotateX = -15 * y;
  cardStyle.value = {
    transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`,
  };
};
const handleMouseLeave = () => {
  cardStyle.value = {
    transform: 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)',
  };
};

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseleave', handleMouseLeave);
});

onUnmounted(() => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseleave', handleMouseLeave);
});
</script>

<style scoped>
.auth-wrapper {
    background-color: var(--bg-dark);
    min-height: 100vh;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}
.auth-card {
    background-color: var(--bg-panel-glass-light);
    backdrop-filter: blur(15px) saturate(150%);
    border: 1px solid var(--border-glow-medium);
    box-shadow: 0 0 40px var(--border-glow-soft), inset 0 0 10px var(--border-glow-purple-soft);
    z-index: 10;
    transition: transform 0.2s ease-out;
    animation: card-enter 0.8s ease-out forwards;
    opacity: 0;
    transform: translateY(20px);
}
@keyframes card-enter {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.orbitron-font {
    font-family: 'Orbitron', monospace;
    font-weight: 900;
    letter-spacing: 2px;
    color: var(--neon-cyan);
    text-shadow: 0 0 10px var(--neon-cyan), 0 0 20px var(--border-glow-medium);
    min-height: 2rem;
}
.switch-mode-link {
    font-size: 0.9rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.2s ease;
}
.switch-mode-link:hover {
    color: var(--neon-cyan);
    text-decoration: underline;
    text-shadow: 0 0 5px var(--neon-cyan);
}

:deep(.neon-submit-btn) {
    font-weight: bold;
    color: #010c03 !important;
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple)) !important;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px var(--border-glow-medium);
}
:deep(.neon-submit-btn:hover) {
    box-shadow: 0 0 30px var(--neon-cyan), 0 0 50px var(--neon-purple) !important;
    transform: translateY(-3px) scale(1.02);
}
</style>
