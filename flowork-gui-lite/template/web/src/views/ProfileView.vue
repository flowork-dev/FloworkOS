//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\ProfileView.vue total lines 229 
//#######################################################################

<template>
  <v-main>
    <div class="profile-view-page">
      <DigitalFingerprintBackground />

      <v-container class="page-content-container">
        <v-row justify="center">
          <v-col cols="12" md="10" lg="8">

            <div v-if="isLoadingProfile" class="text-center py-16">
              <v-progress-circular indeterminate color="cyan" size="64"></v-progress-circular>
              <p class="mt-4 text-grey-lighten-1">Loading Profile...</p>
            </div>

            <v-alert v-else-if="error" type="error" variant="tonal" class="mt-4">
                {{ error }}
            </v-alert>

            <div v-else-if="profile" class="profile-content">
              <v-card class="profile-header-card" flat>
                <v-card-text class="d-flex align-center">
                  <v-avatar color="blue-grey-darken-3" size="96" class="mr-6">
                    <v-icon icon="mdi-account-circle" size="80"></v-icon>
                  </v-avatar>
                  <div>
                    <h1 class="profile-name orbitron-font">{{ profile.name || 'Anonymous User' }}</h1>
                    <p class="profile-address">{{ profile.addr }}</p>
                    <p v-if="profile.bio" class="profile-bio">{{ profile.bio }}</p>
                  </div>
                </v-card-text>
              </v-card>

              <h2 class="section-title orbitron-font">
                Published Marketplace Items
              </h2>

              <v-alert v-if="isLoadingItems" type="info" variant="tonal" class="mt-4">
                Loading items...
              </v-alert>
              <v-alert v-else-if="itemsError" type="error" variant="tonal" class="mt-4">
                Could not load items: {{ itemsError }}
              </v-alert>
              <div v-else-if="marketplaceItems.length === 0" class="text-grey mt-4 text-center py-8">
                <p>This user has not published any marketplace items yet.</p>
              </div>

              <div v-else class="masonry-grid">
                <div v-for="item in marketplaceItems" :key="item.id" class="masonry-item">
                  <v-card
                    class="article-grid-item"
                    variant="flat"
                    :to="`/marketplace/item/${item.id}`"
                  >
                    <v-card-title class="item-title orbitron-font">{{ item.name }}</v-card-title>
                    <v-card-text class="item-snippet">
                      {{ item.desc || 'No description provided.' }}
                    </v-card-text>
                    <v-divider></v-divider>
                    <v-card-actions class="pa-3">
                      <v-chip size="small" variant="tonal" :color="item.price > 0 ? 'yellow-darken-2' : 'green-lighten-2'">
                        {{ item.price > 0 ? `$${item.price}` : 'Free' }}
                      </v-chip>
                      <v-spacer></v-spacer>
                      <span class="text-caption text-grey-lighten-1 mr-2">
                        <v-icon icon="mdi-download-outline" size="x-small" class="mr-1"></v-icon>
                        {{ item.dl || 0 }}
                      </span>
                    </v-card-actions>
                  </v-card>
                </div>
              </div>

            </div>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </v-main>
  <LanderFooter />
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { apiGetPublicProfile, apiGetMarketplaceItems } from '@/api';
import LanderFooter from '@/components/LanderFooter.vue';
import DigitalFingerprintBackground from '@/components/DigitalFingerprintBackground.vue';

const route = useRoute();
const profile = ref(null);
const marketplaceItems = ref([]);
const isLoadingProfile = ref(true);
const isLoadingItems = ref(false);
const error = ref(null);
const itemsError = ref(null);

async function fetchProfileData() {
  isLoadingProfile.value = true;
  isLoadingItems.value = true;
  error.value = null;
  itemsError.value = null;
  profile.value = null;
  marketplaceItems.value = [];

  const identifier = route.params.identifier;
  if (!identifier) {
    error.value = "No user identifier provided.";
    isLoadingProfile.value = false;
    isLoadingItems.value = false;
    return;
  }

  try {
    const profileData = await apiGetPublicProfile(identifier);
    if (profileData.error) throw new Error(profileData.error);
    profile.value = profileData;
    console.log("[ProfileView] Loaded profile:", profileData);

    try {
        const itemsData = await apiGetMarketplaceItems({ author: profile.value.addr });
        if (itemsData.error) throw new Error(itemsData.error);
        marketplaceItems.value = itemsData;
        console.log(`[ProfileView] Found ${itemsData.length} items for this user.`);
    } catch (e_items) {
        console.error("[ProfileView] Failed to fetch marketplace items:", e_items);
        itemsError.value = e_items.message;
    }

  } catch (e) {
    console.error("[ProfileView] Failed to fetch profile:", e);
    error.value = e.message;
  } finally {
    isLoadingProfile.value = false;
    isLoadingItems.value = false;
  }
}

watch(() => route.params.identifier, fetchProfileData, { immediate: true });
</script>

<style scoped>
/* (English Hardcode) Rule #5: High contrast text */
.profile-view-page {
  position: relative;
  z-index: 1;
  background-color: #0A0F1E;
  padding: 120px 0;
  min-height: 100vh;
}
.page-content-container {
  position: relative;
  z-index: 2;
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
  color: #f0f0f0;
}
.profile-header-card {
  background: rgba(30, 30, 47, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 245, 255, 0.2);
  padding: 24px;
  margin-bottom: 48px;
}
.profile-name {
  font-size: 2.5rem;
  color: var(--text-primary);
  text-shadow: 0 0 10px var(--neon-cyan);
}
.profile-address {
  font-family: monospace;
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.profile-bio {
  color: var(--text-primary);
  margin-top: 16px;
  font-size: 1rem;
  font-style: italic;
}
.section-title {
  color: var(--neon-cyan);
  margin-bottom: 24px;
}

/* (English Hardcode) Masonry Grid Styles */
.masonry-grid {
  column-gap: 16px;
  column-count: 1;
}
@media (min-width: 700px) { .masonry-grid { column-count: 2; } }
@media (min-width: 1280px) { .masonry-grid { column-count: 3; } }

.masonry-item {
  break-inside: avoid;
  margin-bottom: 16px;
}
.article-grid-item {
  background: rgba(23, 33, 65, 0.7);
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease-in-out;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.article-grid-item:hover {
  transform: translateY(-5px);
  border-color: rgba(0, 245, 255, 0.3);
}
.item-title {
  color: var(--text-primary);
  font-size: 1.1rem;
}
.item-snippet {
  color: var(--text-secondary);
  font-size: 0.9rem;
  flex-grow: 1;
}
.article-grid-item .v-card-actions {
  background-color: rgba(0,0,0,0.2);
}
</style>
