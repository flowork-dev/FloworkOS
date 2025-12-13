//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\DigitalFingerprintBackground.vue total lines 198 
//#######################################################################

<template>
  <canvas ref="canvasEl" class="digital-fingerprint-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const canvasEl = ref(null);
let animationFrameId = null;
let ctx = null;
let particles = [];
let noise;
let noiseSeed = Math.random() * 1000;
let frame = 0;
const mouse = {
  x: window.innerWidth / 2,
  y: window.innerHeight / 2,
  radius: 150
};

const PerlinNoise = function() {
  this.p = new Uint8Array(512);
  const permutation = Array.from({length: 256}, (_, i) => i);
  permutation.sort(() => Math.random() - 0.5);
  for (let i=0; i < 256; i++) {
    this.p[i] = this.p[i + 256] = permutation[i];
  }

  const fade = t => t * t * t * (t * (t * 6 - 15) + 10);
  const lerp = (t, a, b) => a + t * (b - a);
  const grad = (hash, x, y, z) => {
    const h = hash & 15;
    const u = h < 8 ? x : y;
    const v = h < 4 ? y : h === 12 || h === 14 ? x : z;
    return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
  };

  this.noise = (x, y, z) => {
    const p = this.p;
    const X = Math.floor(x) & 255;
    const Y = Math.floor(y) & 255;
    const Z = Math.floor(z) & 255;
    x -= Math.floor(x);
    y -= Math.floor(y);
    z -= Math.floor(z);
    const u = fade(x);
    const v = fade(y);
    const w = fade(z);
    const A = p[X] + Y, AA = p[A] + Z, AB = p[A + 1] + Z;
    const B = p[X + 1] + Y, BA = p[B] + Z, BB = p[B + 1] + Z;

    return lerp(w, lerp(v, lerp(u, grad(p[AA], x, y, z),
                                     grad(p[BA], x - 1, y, z)),
                             lerp(u, grad(p[AB], x, y - 1, z),
                                     grad(p[BB], x - 1, y - 1, z))),
                     lerp(v, lerp(u, grad(p[AA + 1], x, y, z - 1),
                                     grad(p[BA + 1], x - 1, y, z - 1)),
                             lerp(u, grad(p[AB + 1], x, y - 1, z - 1),
                                     grad(p[BB + 1], x - 1, y - 1, z - 1))));
  };
};

class Particle {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.color = color;
    this.history = [];
    this.life = Math.random() * 200 + 100;
  }

  update(width, height, noise) {
    const n = noise.noise(this.x * 0.001, this.y * 0.001, frame * 0.001);
    const angle = n * Math.PI * 4;

    const speed = 1.5;
    this.x += Math.cos(angle) * speed;
    this.y += Math.sin(angle) * speed;

    this.history.push({ x: this.x, y: this.y });
    if (this.history.length > 20) {
      this.history.shift();
    }

    this.life--;

    if (this.x > width || this.x < 0 || this.y > height || this.y < 0 || this.life <= 0) {
      this.reset(width, height);
    }
  }

  reset(width, height) {
    this.x = Math.random() * width;
    this.y = Math.random() * height;
    this.history = [];
    this.life = Math.random() * 200 + 100;
  }

  draw(ctx) {
    ctx.beginPath();
    ctx.moveTo(this.history[0]?.x || this.x, this.history[0]?.y || this.y);
    for (let i = 1; i < this.history.length; i++) {
      ctx.lineTo(this.history[i].x, this.history[i].y);
    }

    const dx = this.x - mouse.x;
    const dy = this.y - mouse.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    let opacity = 0.2;

    if (distance < mouse.radius) {
      opacity = (1 - (distance / mouse.radius)) * 0.8 + 0.2;
    }

    ctx.strokeStyle = `rgba(${this.color}, ${opacity})`;
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

const setupCanvas = () => {
  const canvas = canvasEl.value;
  if (!canvas) return;
  ctx = canvas.getContext('2d');
  noise = new PerlinNoise();

  const resizeCanvas = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    particles = [];
    const particleCount = Math.floor((canvas.width * canvas.height) / 8000);
    const colors = [ "0, 245, 255", "191, 0, 255" ]; // Cyan, Purple

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle(
        Math.random() * canvas.width,
        Math.random() * canvas.height,
        colors[i % colors.length]
      ));
    }
  };

  const animate = () => {
    ctx.fillStyle = 'rgba(10, 15, 30, 0.1)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      p.update(canvas.width, canvas.height, noise);
      p.draw(ctx);
    });

    frame++;
    animationFrameId = requestAnimationFrame(animate);
  };

  const handleMouseMove = (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  };

  window.addEventListener('resize', resizeCanvas);
  window.addEventListener('mousemove', handleMouseMove);

  resizeCanvas();
  animate();

  onUnmounted(() => {
    window.removeEventListener('resize', resizeCanvas);
    window.removeEventListener('mousemove', handleMouseMove);
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
  });
};

onMounted(() => {
  setupCanvas();
});
</script>

<style scoped>
.digital-fingerprint-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  opacity: 0.5;
}
</style>
