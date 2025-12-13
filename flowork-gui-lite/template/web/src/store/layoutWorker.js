//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\layoutWorker.js total lines 79 
//#######################################################################

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useWorkflowStore } from './workflow';
import { useUiStore } from './ui';

export const useLayoutWorkerStore = defineStore('layoutWorker', () => {
    const worker = ref(null);
    const isWorking = ref(false);

    function initWorker() {
        if (window.Worker) {
            if (worker.value) {
                worker.value.terminate();
            }
            worker.value = new Worker(new URL('../workers/layout.worker.js', import.meta.url), { type: 'module' });
            worker.value.onmessage = (event) => {
                const uiStore = useUiStore();
                const workflowStore = useWorkflowStore();

                const { type, nodes } = event.data;

                if (type === 'LAYOUT_COMPLETE') {
                    console.log('[Main Thread] Menerima layout baru dari worker.');
                    workflowStore.applyAutoLayout(nodes);
                    uiStore.showNotification({ text: 'Auto-layout applied successfully!', color: 'success' });
                }
                isWorking.value = false;
            };
            worker.value.onerror = (error) => {
                console.error('[Worker Error]', error);
                const uiStore = useUiStore();
                uiStore.showNotification({ text: `Layout worker error: ${error.message}`, color: 'error' });
                isWorking.value = false;
            };
        } else {
            console.error('Web Workers are not supported in this browser.');
            alert('Your browser does not support Web Workers, this feature will be unavailable.');
        }
    }

    function runAutoLayout() {
        if (!worker.value) {
            initWorker();
        }

        if (isWorking.value) {
            console.warn('Layout worker is already busy.');
            return;
        }

        const workflowStore = useWorkflowStore();
        const uiStore = useUiStore();

        if (workflowStore.nodes.length === 0) {
            uiStore.showNotification({ text: 'Canvas is empty, nothing to layout.', color: 'info' });
            return;
        }

        isWorking.value = true;
        uiStore.showNotification({ text: 'Calculating optimal layout in background...', color: 'info' });

        const nodesToProcess = JSON.parse(JSON.stringify(workflowStore.nodes));
        worker.value.postMessage({
            nodes: nodesToProcess
        });
    }

    return {
        isWorking,
        initWorker,
        runAutoLayout
    };
});
