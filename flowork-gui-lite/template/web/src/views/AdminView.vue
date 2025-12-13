//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\AdminView.vue total lines 168 
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
              ADMIN
            </v-chip>
          </div>

          <v-card
            variant="outlined"
            class="mb-6"
            style="background-color: #111a2e; border-color: #24304d; border-radius: 14px;"
          >
            <v-card-text>
              <v-text-field
                v-model="adminToken"
                label="ADMIN_TOKEN"
                placeholder="Enter token from your .env file"
                variant="outlined"
                density="compact"
                hide-details
                class="text-white"
              ></v-text-field>
            </v-card-text>
          </v-card>

          <v-card
            variant="outlined"
            class="mb-6"
            style="background-color: #111a2e; border-color: #24304d; border-radius: 14px;"
          >
            <v-card-title class="text-white">Drain Control</v-card-title>
            <v-card-text>
              <v-btn @click="setDrain(true)" color="#ffd400" class="mr-4" style="color: #0b1220; font-weight: 800;">
                Enable Drain
              </v-btn>
              <v-btn @click="setDrain(false)" color="grey-darken-3" class="text-white">
                Disable Drain
              </v-btn>
              <v-alert
                v-if="drainStatus"
                :type="drainStatus.includes('Error') ? 'error' : 'info'"
                variant="tonal"
                density="compact"
                class="mt-4"
              >
                {{ drainStatus }}
              </v-alert>
            </v-card-text>
          </v-card>

          <v-card
            variant="outlined"
            style="background-color: #111a2e; border-color: #24304d; border-radius: 14px;"
          >
            <v-card-title class="d-flex align-center justify-space-between text-white">
              Peer Status
              <v-btn @click="loadPeers" icon="mdi-refresh" variant="text" size="small"></v-btn>
            </v-card-title>
            <v-card-text>
              <v-alert
                v-if="peerStatus.error"
                type="error"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                {{ peerStatus.error }}
              </v-alert>
              <pre
                style="background-color: #0f1730; color: #fff; border: 1px solid #24304d; border-radius: 10px; padding: 8px; min-height: 100px; white-space: pre-wrap; word-wrap: break-word;"
              >{{ peerStatus.data }}</pre>
            </v-card-text>
          </v-card>

        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const adminToken = ref('');
const drainStatus = ref('');
const peerStatus = ref({ data: 'Loading...', error: null });

onMounted(() => {
  adminToken.value = localStorage.getItem('ADMIN_TOKEN') || '';
  loadPeers();
});

async function apiFetch(url, options = {}) {
  if (!adminToken.value) {
    return { error: 'ADMIN_TOKEN is missing.' };
  }
  localStorage.setItem('ADMIN_TOKEN', adminToken.value);

  try {
    const res = await fetch(`/api${url}`, {
      ...options,
      headers: {
        ...options.headers,
        'X-Admin-Token': adminToken.value,
        'Content-Type': 'application/json',
      },
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`[${res.status}] ${errText}`);
    }
    return res.json();
  } catch (e) {
    return { error: e.message };
  }
}

async function setDrain(enabled) {
  drainStatus.value = `Setting drain to ${enabled}...`;
  const res = await apiFetch('/ops/drain', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  });

  if (res.error) {
    drainStatus.value = `Error: ${res.error}`;
  } else {
    drainStatus.value = `Success: Drain state is now: ${JSON.stringify(res.drain)}`;
  }
}

async function loadPeers() {
  peerStatus.value = { data: 'Loading...', error: null };
  const res = await apiFetch('/ops/peers');

  if (res.error) {
    peerStatus.value.error = res.error;
    peerStatus.value.data = 'Failed to load.';
  } else {
    peerStatus.value.data = JSON.stringify(res, null, 2);
  }
}
</script>

<style scoped>
/* (English Hardcode) Ensure high contrast text */
.text-white {
  color: #ffffff !important;
}
</style>
