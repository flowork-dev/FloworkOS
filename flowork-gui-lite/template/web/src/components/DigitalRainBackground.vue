//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\DigitalRainBackground.vue total lines 87 
//#######################################################################

<template>
  <canvas ref="canvasEl" class="digital-rain-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const canvasEl = ref(null);
let animationFrameId = null;

const setupDigitalRain = () => {
  const canvas = canvasEl.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width, height;
  let columns;
  const drops = [];
  const fontSize = 16;
  const characters = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';

  const resizeCanvas = () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    columns = Math.floor(width / fontSize);
    for (let i = 0; i < columns; i++) {
      drops[i] = 1;
    }
  };

  const draw = () => {
    ctx.fillStyle = 'rgba(10, 15, 30, 0.1)';
    ctx.fillRect(0, 0, width, height);

    ctx.fillStyle = '#0f0'; // Warna hijau Matrix
    ctx.font = `${fontSize}px Fira Code`;

    for (let i = 0; i < drops.length; i++) {
      const text = characters[Math.floor(Math.random() * characters.length)];
      ctx.fillText(text, i * fontSize, drops[i] * fontSize);

      if (drops[i] * fontSize > height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      drops[i]++;
    }
  };

  const animate = () => {
    draw();
    animationFrameId = requestAnimationFrame(animate);
  };

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  animate();
};

onMounted(() => {
  setupDigitalRain();
});

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
  window.removeEventListener('resize', setupDigitalRain);
});
</script>

<style scoped>
.digital-rain-canvas {
  position: absolute; /* Ganti dari fixed ke absolute */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0; /* Di belakang konten */
  opacity: 0.3; /* Sedikit lebih redup */
}
</style>
