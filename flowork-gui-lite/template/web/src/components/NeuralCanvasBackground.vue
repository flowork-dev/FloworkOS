//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\NeuralCanvasBackground.vue total lines 143 
//#######################################################################

<template>
  <canvas ref="canvasEl" class="neural-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const canvasEl = ref(null);
let animationFrameId = null;
let mouse = { x: null, y: null, radius: 150 };

function handleMouseMove(event) {
    mouse.x = event.clientX;
    mouse.y = event.clientY;
}

const setupCanvasAnimation = () => {
    const canvas = canvasEl.value; if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];

    const resizeCanvas = () => {
        if(canvas) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('mousemove', handleMouseMove);

    class Particle {
        constructor(x, y, size, color, speedX, speedY) {
            this.x = x; this.y = y;
            this.originX = x;
            this.originY = y;
            this.size = size; this.color = color;
            this.speedX = speedX; this.speedY = speedY;
            this.density = (Math.random() * 30) + 1;
        }
        update() {
            let dx = mouse.x - this.x;
            let dy = mouse.y - this.y;
            let distance = Math.sqrt(dx*dx + dy*dy);
            if (distance < mouse.radius) {
                let forceDirectionX = dx / distance;
                let forceDirectionY = dy / distance;
                let force = (mouse.radius - distance) / mouse.radius;
                let directionX = forceDirectionX * force * this.density * 0.5;
                let directionY = forceDirectionY * force * this.density * 0.5;
                this.x -= directionX;
                this.y -= directionY;
            } else {
                if (this.x !== this.originX) {
                    let dx = this.x - this.originX;
                    this.x -= dx/10;
                }
                if (this.y !== this.originY) {
                    let dy = this.y - this.originY;
                    this.y -= dy/10;
                }
            }
            if (this.x > canvas.width || this.x < 0) this.speedX = -this.speedX;
            if (this.y > canvas.height || this.y < 0) this.speedY = -this.speedY;
            if (distance >= mouse.radius) {
                this.x += this.speedX;
                this.y += this.speedY;
            }
        }
        draw() { ctx.fillStyle = this.color; ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); ctx.fill(); }
    }

    function init() {
        particles = [];
        let numberOfParticles = (canvas.height * canvas.width) / 9000;
        for (let i = 0; i < numberOfParticles; i++) {
            let size = (Math.random() * 2) + 1;
            let x = Math.random() * (innerWidth - size * 4) + size * 2;
            let y = Math.random() * (innerHeight - size * 4) + size * 2;
            let speedX = (Math.random() * 0.4) - 0.2;
            let speedY = (Math.random() * 0.4) - 0.2;
            particles.push(new Particle(x, y, size, 'rgba(0, 245, 255, 0.5)', speedX, speedY));
        }
    }

    function connect() {
        let opacityValue = 1;
        for (let a = 0; a < particles.length; a++) {
            for (let b = a; b < particles.length; b++) {
                let distance = ((particles[a].x - particles[b].x) * (particles[a].x - particles[b].x)) + ((particles[a].y - particles[b].y) * (particles[a].y - particles[b].y));
                if (distance < (canvas.width / 7) * (canvas.height / 7)) {
                    opacityValue = 1 - (distance / 20000);
                    ctx.strokeStyle = `rgba(191, 0, 255, ${opacityValue})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(particles[a].x, particles[a].y);
                    ctx.lineTo(particles[b].x, particles[b].y);
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        animationFrameId = requestAnimationFrame(animate);
        ctx.clearRect(0, 0, innerWidth, innerHeight);
        particles.forEach(p => { p.update(); p.draw(); });
        connect();
    }

    init();
    animate();
};

onMounted(() => {
  setupCanvasAnimation();
});

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
  window.removeEventListener('mousemove', handleMouseMove);
});
</script>

<style scoped>
.neural-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  opacity: 0.5;
}
</style>
