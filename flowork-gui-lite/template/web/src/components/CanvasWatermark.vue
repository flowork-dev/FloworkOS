//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\CanvasWatermark.vue total lines 94 
//#######################################################################

<template>
  <div class="watermark-container">
    <svg viewBox="0 0 400 100" class="watermark-svg">
      <defs>
        <filter id="neon-glow">
          <feGaussianBlur stdDeviation="3.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <text
        x="50%"
        y="50%"
        dy=".35em"
        text-anchor="middle"
        class="watermark-text"
      >
        FLOWORK.SYNAPSE
      </text>

      <path
        class="aurora-path"
        d="M 50 50 m -45, 0 a 45,45 0 1,1 90,0 a 45,45 0 1,1 -90,0"
        transform="translate(150, 0)"
      ></path>
    </svg>
  </div>
</template>

<style scoped>
.watermark-container {
  /* This makes the watermark stay in the center and not move with the canvas */
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none; /* Make it unclickable so it doesn't block the canvas */
  z-index: 0;
  opacity: 0.4;
}

.watermark-svg {
  width: 400px;
  height: 100px;
  overflow: visible;
}

.watermark-text {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 32px;
  fill: rgba(0, 245, 255, 0.4);
  filter: url(#neon-glow);
  animation: text-pulse 4s ease-in-out infinite alternate;
}

.aurora-path {
  fill: none;
  stroke: url(#aurora-gradient);
  stroke-width: 2;
  stroke-dasharray: 10 5;
  filter: url(#neon-glow);
  animation: rotate-glow 10s linear infinite;
}

@keyframes text-pulse {
  from {
    fill: rgba(0, 245, 255, 0.3);
    text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
  }
  to {
    fill: rgba(191, 0, 255, 0.4);
    text-shadow: 0 0 20px rgba(191, 0, 255, 0.7);
  }
}

@keyframes rotate-glow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
