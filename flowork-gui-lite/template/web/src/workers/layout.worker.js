//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\workers\layout.worker.js total lines 38 
//#######################################################################

self.onmessage = (event) => {
  console.log('[Worker] Menerima data dari thread utama:', event.data);
  const { nodes } = event.data;

  if (!nodes || nodes.length === 0) {
      self.postMessage({ type: 'LAYOUT_ERROR', error: 'No nodes to process.' });
      return;
  }

  const spacingX = 250;
  const spacingY = 150;
  const nodesPerRow = Math.ceil(Math.sqrt(nodes.length));

  const updatedNodes = nodes.map((node, index) => {
    return {
      ...node,
      position: {
        x: (index % nodesPerRow) * spacingX,
        y: Math.floor(index / nodesPerRow) * spacingY,
      },
    };
  });

  let i = 0;
  while (i < 500000000) { // Ini sengaja untuk "membuang" waktu CPU agar terasa prosesnya
    i++;
  }

  console.log('[Worker] Kalkulasi selesai, mengirim data kembali.');

  self.postMessage({ type: 'LAYOUT_COMPLETE', nodes: updatedNodes });
};
