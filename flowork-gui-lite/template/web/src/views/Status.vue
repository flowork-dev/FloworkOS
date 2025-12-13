//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\Status.vue total lines 131 
//#######################################################################

<template>
  <v-app theme="dark">
    <v-container class="fill-height" style="background-color: #0b1220; max-width: 100vw;">
      <v-row align="center" justify="center">
        <v-col cols="12" md="8" lg="6">
          <div class="d-flex align-center mb-4">
            <h1 class="text-h4 font-weight-bold text-white mr-4">FLOWORK</h1>
            <v-chip
              color="#ffd400"
              text-color="#0b1220"
              class="font-weight-bold"
              size="large"
              label
            >
              STATUS
            </v-chip>
          </div>

          <p class="text-medium-emphasis mb-4">
            Engines discovered by Gateway (via /api/v1/system/public-engines):
          </p>

          <template v-if="loading">
            <v-skeleton-loader
              v-for="i in 2"
              :key="i"
              type="list-item-two-line"
              theme="dark"
              class="mb-3"
              style="background-color: #111a2e; border: 1px solid #24304d; border-radius: 14px;"
            ></v-skeleton-loader>
          </template>

          <v-alert
            v-else-if="error"
            type="error"
            variant="tonal"
            border="start"
            density="compact"
            icon="mdi-alert-circle-outline"
            class="text-white"
          >
            <strong>Failed to load status.</strong><br/>
            Error: {{ error }}
          </v-alert>

          <v-alert
            v-else-if="!loading && engines.length === 0"
            type="info"
            variant="tonal"
            border="start"
            density="compact"
            icon="mdi-information-outline"
            class="text-white"
            style="background-color: #111a2e; border-color: #24304d;"
          >
            No 'Up' engines found by the Gateway.
          </v-alert>

          <v-card
            v-for="engine in engines"
            :key="engine.engine_id"
            variant="outlined"
            class="mb-3 pa-4"
            style="background-color: #111a2e; border-color: #24304d; border-radius: 14px;"
          >
            <strong class="text-h6 text-white">{{ engine.engine_id }}</strong>
            <div class="text-grey-lighten-1 mt-1">
              weight={{ engine.weight }} · capacity={{ engine.capacity }} · status=<span style="color: #4CAF50;">{{ engine.status }}</span>
            </div>
          </v-card>

        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const engines = ref([]);
const loading = ref(true);
const error = ref(null);

async function loadStatus() {
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch("/api/v1/system/public-engines");

    if (!res.ok) {
      throw new Error(`Gateway returned status: ${res.status}`);
    }

    const data = await res.json();

    if (data.error || !Array.isArray(data.engines)) {
      throw new Error(data.error || "Invalid response format from Gateway.");
    }

    engines.value = data.engines;

  } catch (e) {
    console.error("Failed to load engine status:", e);
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadStatus();
});
</script>

<style scoped>
/* (English Hardcode) Ensure high contrast text */
.text-white {
  color: #ffffff !important;
}
.text-grey-lighten-1 {
  color: #BDBDBD !important;
}
</style>
