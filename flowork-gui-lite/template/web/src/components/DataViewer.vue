//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\DataViewer.vue total lines 87 
//#######################################################################

<template>
  <v-dialog
    v-model="uiStore.isDataViewerVisible"
    @update:model-value="handleClose"
    max-width="800px"
    scrollable
  >
    <v-card class="data-viewer-card">
      <v-card-title class="panel-title">
        <v-icon icon="mdi-code-json" class="mr-2"></v-icon>
        {{ viewerTitle }}
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" size="small" @click="handleClose"></v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="data-content">
        <pre><code>{{ formattedContent }}</code></pre>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { useUiStore } from '@/store/ui';

const uiStore = useUiStore();

const viewerTitle = computed(() => {
    return uiStore.dataViewerContent?.title || (uiStore.dataViewerContent?.error ? 'Error' : 'Connection Data Viewer');
});

const formattedContent = computed(() => {
  try {
    const dataToShow = uiStore.dataViewerContent?.payload ??
                       uiStore.dataViewerContent?.content ??
                       uiStore.dataViewerContent?.data ??
                       uiStore.dataViewerContent?.error ??
                       uiStore.dataViewerContent;

    if (typeof dataToShow === 'string') {
        try {
            return JSON.stringify(JSON.parse(dataToShow), null, 2);
        } catch (e) {
            return dataToShow;
        }
    }
    return JSON.stringify(dataToShow, null, 2);
  } catch (e) {
    return "Error parsing data.";
  }
});

function handleClose() {
  uiStore.hideDataViewer();
}
</script>

<style scoped>
.data-viewer-card {
  background-color: #1e1e2f;
  border: 1px solid var(--neon-cyan);
}

.panel-title {
  color: var(--neon-cyan);
  font-family: 'Orbitron', monospace;
}

.data-content {
  background-color: #161625;
  color: #e0e0e0;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85rem;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
