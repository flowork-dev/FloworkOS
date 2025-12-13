//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\MarketplaceItem.vue total lines 406 
//#######################################################################

<template>
  <div class="item-detail-page">
    <NeuralCanvasBackground />
    <v-container class="page-container">
      <v-row justify="center">
        <v-col cols="12" md="11" lg="10">

          <v-btn
            :to="{ name: 'Marketplace' }"
            prepend-icon="mdi-arrow-left"
            variant="text"
            class="mb-4"
          >
            Back to Marketplace
          </v-btn>

          <div v-if="itemType === 'capsule'">
             <v-alert type="info">Capsule View Active</v-alert>
          </div>

          <div v-else>
            <div v-if="isLoadingDetail" class="text-center py-16">
              <v-progress-circular indeterminate color="cyan" size="64"></v-progress-circular>
              <p class="mt-4 text-grey-lighten-1">Loading item detail...</p>
            </div>

            <v-alert v-else-if="error" type="error" variant="tonal" class="mt-4">
              {{ error }}
            </v-alert>

            <v-card v-else-if="selectedItem" class="item-card detail-card-enhanced" variant="flat">

              <div class="hero-header pa-6 d-flex justify-space-between align-start">
                 <div>
                    <v-chip
                        size="small"
                        :color="getTypeColor(selectedItem.type)"
                        class="mb-2 font-weight-bold"
                        variant="outlined"
                    >
                        {{ selectedItem.type ? selectedItem.type.toUpperCase() : 'ITEM' }}
                    </v-chip>

                    <h1 class="item-title-large orbitron-font">{{ selectedItem.name }}</h1>

                    <div class="text-grey-lighten-1 mt-2">
                        Published by
                        <router-link
                          :to="{ name: 'ProfileView', params: { identifier: selectedItem.author || 'anon' } }"
                          class="author-link font-weight-bold text-cyan"
                        >
                          {{ formatAuthor(selectedItem.author) }}
                        </router-link>
                    </div>
                 </div>

                 <div class="d-flex gap-2">
                    <v-btn
                      v-if="canDelete"
                      color="yellow-darken-2"
                      variant="tonal"
                      size="small"
                      prepend-icon="mdi-pencil"
                      @click="showEditDialog = true"
                      class="mr-2"
                    >
                      Edit
                    </v-btn>
                    <v-btn
                      v-if="canDelete"
                      color="red-darken-1"
                      variant="tonal"
                      size="small"
                      prepend-icon="mdi-delete"
                      @click="handleDelete"
                    >
                      Delete
                    </v-btn>
                 </div>
              </div>

              <v-divider class="border-opacity-50"></v-divider>

              <v-card-text class="pa-6">
                <div class="d-flex align-center mb-6">
                  <v-btn
                    variant="tonal"
                    :color="userVoteStatus === 1 ? 'cyan' : 'grey-darken-2'"
                    @click="handleVote(1)"
                    :prepend-icon="userVoteStatus === 1 ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                    class="mr-2"
                    rounded="pill"
                  >
                    {{ selectedItem.likes || 0 }}
                  </v-btn>
                  <v-btn
                    variant="tonal"
                    :color="userVoteStatus === -1 ? 'red' : 'grey-darken-2'"
                    @click="handleVote(-1)"
                    :prepend-icon="userVoteStatus === -1 ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                    class="mr-4"
                    rounded="pill"
                  >
                    {{ selectedItem.dislikes || 0 }}
                  </v-btn>
                  <v-chip variant="text" color="grey">
                    <v-icon start>mdi-calendar-clock</v-icon>
                    {{ selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleDateString() : 'Recent' }}
                  </v-chip>
                </div>

                <div class="content-layout d-flex flex-column flex-md-row gap-6">

                    <div class="description-box flex-grow-1">
                        <h3 class="section-title text-cyan mb-3">Description</h3>
                        <p class="item-description">
                        {{ selectedItem.desc || selectedItem.description || 'No description provided.' }}
                        </p>

                        <div v-if="selectedItem.type !== 'preset'" class="mt-6 pa-4 bg-grey-darken-4 rounded border">
                            <div class="text-caption text-grey mb-2">COMPONENT INFO</div>
                            <div class="d-flex align-center gap-4">
                                <v-chip size="small" label color="purple">Ver: {{ selectedItem.version || '1.0.0' }}</v-chip>
                                <span class="text-caption text-mono">{{ selectedItem.id }}</span>
                            </div>
                        </div>
                    </div>

                    <div class="action-sidebar">
                        <v-card variant="outlined" class="action-box-card pa-4">
                            <div class="mb-4 text-center">
                                <span class="text-h4 orbitron-font text-green-accent-3">
                                    {{ selectedItem.price > 0 ? `$${selectedItem.price}` : 'FREE' }}
                                </span>
                            </div>

                            <v-btn
                                v-if="selectedItem.type === 'preset'"
                                color="cyan"
                                block
                                size="large"
                                variant="flat"
                                class="action-button-glow"
                                @click="handleImportPreset"
                                prepend-icon="mdi-import"
                            >
                                Import Workflow
                            </v-btn>

                            <v-btn
                                v-else
                                color="yellow-darken-1"
                                block
                                size="large"
                                variant="flat"
                                class="action-button-glow text-black"
                                @click="handleInstallComponent"
                                :loading="isInstalling"
                                prepend-icon="mdi-download-box"
                            >
                                Install {{ selectedItem.type ? selectedItem.type : 'Component' }}
                            </v-btn>

                            <p class="text-caption text-center mt-3 text-grey">
                                {{ selectedItem.type === 'preset'
                                    ? 'Instantly add this workflow to your active Designer canvas.'
                                    : 'Download and install this component to your local engine.'
                                }}
                            </p>
                        </v-card>
                    </div>
                </div>
              </v-card-text>
            </v-card>
          </div>

        </v-col>
      </v-row>

      <MarketplacePublishDialog
        v-model="showEditDialog"
        :existing-item="selectedItem"
        @published="handleItemUpdated"
      />

    </v-container>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMarketplaceStore } from '@/store/marketplace';
import { useWorkflowStore } from '@/store/workflow';
import { useAuthStore } from '@/store/auth';
import { useUiStore } from '@/store/ui';
import { storeToRefs } from 'pinia';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';
import MarketplacePublishDialog from '@/components/MarketplacePublishDialog.vue';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const marketplaceStore = useMarketplaceStore();
const workflowStore = useWorkflowStore();
const authStore = useAuthStore();
const uiStore = useUiStore();

const { selectedItem, isLoadingDetail, error, userVotes } = storeToRefs(marketplaceStore);
const itemType = computed(() => route.query.type);

const showEditDialog = ref(false);
const isInstalling = ref(false);

const userVoteStatus = computed(() => {
    const itemId = selectedItem.value?.id;
    return itemId ? userVotes.value[itemId] : 0;
});

const canDelete = computed(() => {
    if (!selectedItem.value || !authStore.user) return false;
    const currentUser = authStore.user.id.toLowerCase();
    const author = (selectedItem.value.author || '').toLowerCase();
    const admins = [
        "0xF39733B34131c13E35733E9Af1adD78a5e768929".toLowerCase(),
        "0x0F1F31783A93C94f5055E2A11AA28B2368bA982d".toLowerCase()
    ];
    return currentUser === author || admins.includes(currentUser);
});

function formatAuthor(address) {
  if (!address) return 'Anonymous';
  if (address.startsWith('0x') && address.length === 42) {
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  }
  return address;
}

function getTypeColor(type) {
    if (!type) return 'grey';
    if (type === 'preset') return 'cyan';
    if (type === 'module') return 'purple-accent-2';
    if (type === 'plugin') return 'orange-accent-3';
    return 'blue';
}

async function handleVote(type) {
    if (!selectedItem.value) return;
    await marketplaceStore.handleVote(selectedItem.value.id, type);
}

async function handleImportPreset() {
  if (!selectedItem.value || !selectedItem.value.data) {
    uiStore.showNotification({ text: 'Error: No workflow data found.', color: 'error' });
    return;
  }
  try {
    let workflowData = selectedItem.value.data;
    if (typeof workflowData === 'string') {
        try { workflowData = JSON.parse(workflowData); } catch(e) { /* ignore */ }
    }
    const newPresetName = `Imported - ${selectedItem.value.name}`;
    workflowStore.updateSinglePresetData(newPresetName, workflowData);
    workflowStore.permissionLevel = 'edit';
    workflowStore.currentPresetName = newPresetName;
    uiStore.showNotification({ text: `Workflow '${newPresetName}' imported successfully!`, color: 'success' });
    router.push({ name: 'Designer' });
  } catch (e) {
    uiStore.showNotification({ text: `Import failed: ${e.message}`, color: 'error' });
  }
}

async function handleInstallComponent() {
    if (!selectedItem.value) return;

    if (!selectedItem.value.data) {
        uiStore.showNotification({ text: 'Error: Package data missing.', color: 'error' });
        return;
    }

    isInstalling.value = true;
    try {
        const payload = {
            id: selectedItem.value.id,
            type: selectedItem.value.type,
            zip_data: selectedItem.value.data
        };

        const response = await axios.post('/api/v1/marketplace/component/install', payload);

        if (response.data.error) throw new Error(response.data.error);

        uiStore.showNotification({
            text: `Successfully installed ${selectedItem.value.name}!`,
            color: 'success',
            timeout: 4000
        });

    } catch (error) {
        const msg = error.response?.data?.error || error.message || 'Unknown error';
        uiStore.showNotification({ text: `Installation Failed: ${msg}`, color: 'error' });
    } finally {
        isInstalling.value = false;
    }
}

async function handleDelete() {
    const confirmed = await uiStore.showConfirmation({
        title: 'Delete Marketplace Item',
        message: 'Are you sure you want to delete this item?',
        color: 'red'
    });
    if (!confirmed) return;
    const success = await marketplaceStore.deleteItem(selectedItem.value.id);
    if (success) {
        router.push({ name: 'Marketplace' });
    }
}

async function handleItemUpdated() {
    if (selectedItem.value?.id) {
        await marketplaceStore.fetchItemDetail(selectedItem.value.id);
    }
}

onMounted(() => {
  const itemId = route.params.id;
  if (itemType.value === 'capsule') {
    marketplaceStore.fetchCapsuleDetails(itemId);
  } else {
    marketplaceStore.fetchItemDetail(itemId);
  }
});
</script>

<style scoped>
.item-detail-page {
    height: 100%;
    overflow-y: auto;
    padding: 48px 0;
    position: relative;
    z-index: 1;
}
.page-container {
    max-width: 1600px;
    position: relative;
    z-index: 2;
}
.orbitron-font {
    font-family: 'Orbitron', monospace;
    color: #f0f0f0;
}
.detail-card-enhanced {
    background: rgba(30, 30, 47, 0.85);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(0, 245, 255, 0.2);
    box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
    overflow: hidden;
}
.item-title-large {
    font-size: 2.8rem;
    line-height: 1.1;
    color: white;
    text-shadow: 0 0 15px rgba(0, 245, 255, 0.4);
}
.content-layout {
    margin-top: 24px;
}
.item-description {
    font-size: 1.1rem;
    line-height: 1.8;
    color: #ccc;
    white-space: pre-wrap;
}
.action-sidebar {
    min-width: 300px;
}
.action-box-card {
    background: rgba(0, 0, 0, 0.3);
    border-color: rgba(255, 255, 255, 0.1);
}
.action-button-glow {
    font-weight: bold;
    box-shadow: 0 0 15px rgba(0, 245, 255, 0.5);
    transition: all 0.3s ease;
}
.action-button-glow:hover {
    box-shadow: 0 0 25px rgba(0, 245, 255, 0.8);
    transform: translateY(-2px);
}
.author-link {
    text-decoration: none;
    transition: all 0.3s ease;
}
.author-link:hover {
    text-shadow: 0 0 10px rgba(0, 245, 255, 0.6);
    text-decoration: underline;
}
.text-mono { font-family: monospace; }
</style>
