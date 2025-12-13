//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\Marketplace.vue total lines 499 
//#######################################################################

<template>
  <div class="marketplace-page">
    <div class="background-layer">
      <NeuralCanvasBackground />
      <div class="gold-overlay"></div>
    </div>

    <v-container class="page-container" fluid>
      <v-row justify="center">
        <v-col cols="12" xl="10">

          <div class="hud-header mb-8 fade-in-down">
            <div class="hud-title-section">
              <div class="icon-box-gold mr-4">
                <v-icon icon="mdi-store-cog" color="#D4AF37" size="32"></v-icon>
              </div>
              <div>
                <h1 class="page-title orbitron-font">MARKETPLACE</h1>
                <div class="hud-subtitle text-mono">PREMIUM ASSETS & MODULES REPOSITORY</div>
              </div>
            </div>

            <div class="hud-controls">
              <v-tabs
                v-model="activeTab"
                class="gold-tabs"
                bg-color="transparent"
                slider-color="#D4AF37"
                density="compact"
                show-arrows
              >
                <v-tab value="presets" class="tech-tab">
                  <v-icon start icon="mdi-cloud-sync" size="small"></v-icon> PRESETS
                </v-tab>
                <v-tab value="widgets" class="tech-tab"> <v-icon start icon="mdi-view-grid-plus-outline" size="small"></v-icon> WIDGETS
                </v-tab>
                <v-tab value="modules" class="tech-tab">
                  <v-icon start icon="mdi-expansion-card" size="small"></v-icon> MODULES
                </v-tab>
                <v-tab value="plugins" class="tech-tab">
                  <v-icon start icon="mdi-power-plug" size="small"></v-icon> PLUGINS
                </v-tab>
                <v-tab value="tools" class="tech-tab">
                  <v-icon start icon="mdi-tools" size="small"></v-icon> TOOLS
                </v-tab>
                <v-tab value="triggers" class="tech-tab">
                  <v-icon start icon="mdi-flash" size="small"></v-icon> TRIGGERS
                </v-tab>
                <v-tab value="capsules" class="tech-tab special-tab">
                  <v-icon start icon="mdi-vector-link" size="small"></v-icon> LOCAL CAPSULES
                </v-tab>
              </v-tabs>
            </div>
          </div>

          <v-window v-model="activeTab" class="content-window">
            <v-window-item
                v-for="tab in ['presets', 'widgets', 'modules', 'plugins', 'tools', 'triggers']"
                :key="tab"
                :value="tab"
            >
              <div v-if="isLoadingList" class="scanner-loader py-16">
                <v-progress-circular indeterminate color="#D4AF37" size="64" width="2"></v-progress-circular>
                <p class="mt-6 text-mono text-gold blink-text">FETCHING DATA...</p>
              </div>

              <v-alert v-else-if="error" type="error" variant="outlined" color="red" class="gold-alert mt-4">
                <div class="text-mono">CONNECTION ERROR: {{ error }}</div>
              </v-alert>

              <div v-else-if="items.length === 0" class="empty-state-grid text-center py-16">
                <v-icon icon="mdi-safe-square-outline" size="64" color="#444" class="mb-4"></v-icon>
                <p class="text-h6 orbitron-font text-grey-darken-1">NO INVENTORY</p>
                <p class="text-mono text-grey-darken-2">SECTOR {{ tab.toUpperCase() }} IS EMPTY.</p>
              </div>

              <div v-else class="gold-grid-layout">
                <div
                  v-for="item in items"
                  :key="item.id"
                  class="gold-grid-item fade-in-up"
                >
                  <router-link :to="`/marketplace/item/${item.id}?type=${item.type || 'preset'}`" class="no-decoration">
                    <div class="gold-card">
                      <div class="card-header">
                        <div class="d-flex justify-space-between align-center">
                           <v-chip size="x-small" variant="outlined" :color="getTypeColor(item.type)" class="type-chip text-mono">
                              {{ item.type ? item.type.toUpperCase() : 'PRESET' }}
                           </v-chip>
                           <v-icon icon="mdi-dots-horizontal" color="#555" size="small"></v-icon>
                        </div>
                        <h3 class="card-title orbitron-font mt-2">{{ truncateText(item.name, 40) }}</h3>
                      </div>

                      <div class="card-body">
                        <div class="author-row text-mono mb-3">
                          <span class="text-grey-darken-1">BY //</span>
                          <router-link
                            :to="{ name: 'ProfileView', params: { identifier: item.author } }"
                            class="author-link ml-1"
                            @click.stop
                          >
                            {{ formatAuthor(item.author) }}
                          </router-link>
                        </div>

                        <div class="card-desc">
                          {{ truncateText(item.desc || 'No description provided.', 85) }}
                        </div>
                      </div>

                      <div class="gold-divider"></div>

                      <div class="card-footer d-flex align-center">
                          <div class="stat-group">
                            <v-icon icon="mdi-download" size="x-small" color="#D4AF37"></v-icon>
                            <span class="text-mono ml-1">{{ item.dl || 0 }}</span>
                          </div>

                          <v-spacer></v-spacer>

                          <div class="vote-controls">
                            <span class="mr-3 hover-gold">
                               <v-icon
                                :icon="userVotes[item.id] === 1 ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                                size="x-small"
                                :color="userVotes[item.id] === 1 ? '#D4AF37' : 'grey'"
                                @click.prevent.stop="handleVote(item.id, 1)"
                               ></v-icon>
                               <span class="vote-text ml-1">{{ item.likes || 0 }}</span>
                            </span>
                            <span class="hover-red">
                               <v-icon
                                :icon="userVotes[item.id] === -1 ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                                size="x-small"
                                :color="userVotes[item.id] === -1 ? 'red' : 'grey'"
                                @click.prevent.stop="handleVote(item.id, -1)"
                               ></v-icon>
                            </span>
                          </div>
                      </div>
                    </div>
                  </router-link>
                </div>
              </div>
            </v-window-item>

            <v-window-item value="capsules">
              <div v-if="isLoadingCapsuleList" class="scanner-loader py-16">
                 <v-progress-circular indeterminate color="#D4AF37" size="64" width="2"></v-progress-circular>
                 <p class="mt-6 text-mono text-gold blink-text">SYNCING GATEWAY...</p>
              </div>

              <v-alert v-else-if="capsuleError" type="error" variant="outlined" class="gold-alert mt-4">
                 <div class="text-mono">ERROR: {{ capsuleError }}</div>
              </v-alert>

              <div v-else-if="capsules.length === 0" class="empty-state-grid text-center py-16">
                 <v-icon icon="mdi-vector-link-off" size="64" color="#444"></v-icon>
                 <p class="text-h6 orbitron-font mt-4 text-grey">NO LOCAL CAPSULES</p>
              </div>

              <div v-else class="gold-grid-layout">
                <div
                  v-for="capsule in capsules"
                  :key="capsule.capsule_id"
                  class="gold-grid-item fade-in-up"
                >
                  <router-link :to="`/marketplace/item/${capsule.capsule_id}?type=capsule`" class="no-decoration">
                    <div class="gold-card capsule-variant">
                      <div class="card-header">
                         <div class="d-flex align-center mb-2">
                            <v-icon icon="mdi-vector-link" color="#D4AF37" size="small" class="mr-2"></v-icon>
                            <h3 class="card-title orbitron-font text-white" :title="capsule.capsule_id">
                                {{ truncateText(capsule.capsule_id, 35) }}
                            </h3>
                         </div>
                      </div>

                      <div class="card-body">
                         <div class="text-mono text-xs text-gold-light mb-3">
                            <span class="text-grey-darken-1">ROLE //</span> {{ capsule.role || 'UNKNOWN' }}
                         </div>
                      </div>

                      <div class="gold-divider"></div>

                      <div class="card-footer d-flex align-center">
                            <div class="stat-group">
                                <v-icon icon="mdi-gas-cylinder" size="x-small" color="#D4AF37"></v-icon>
                                <span class="text-mono ml-1">{{ capsule.budget_gas || 0 }} G</span>
                            </div>
                            <v-spacer></v-spacer>
                            <span class="text-caption text-grey text-mono">[LOCAL]</span>
                      </div>
                    </div>
                  </router-link>
                </div>
              </div>
            </v-window-item>

          </v-window>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { useMarketplaceStore } from '@/store/marketplace';
import { storeToRefs } from 'pinia';
import NeuralCanvasBackground from '@/components/NeuralCanvasBackground.vue';

const marketplaceStore = useMarketplaceStore();
const { items, isLoadingList, error, capsules, isLoadingCapsuleList, capsuleError, userVotes } = storeToRefs(marketplaceStore);

const activeTab = ref('presets');

function formatAuthor(address) {
  if (!address) return 'ANON';
  if (address.startsWith('0x') && address.length === 42) {
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  }
  return address;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function handleVote(itemId, type) {
    marketplaceStore.handleVote(itemId, type);
}

function getTypeColor(type) {
    const map = {
        preset: 'cyan',
        module: 'purple',
        plugin: 'orange',
        tool: 'blue',
        trigger: 'green',
        widget: 'yellow' // [ADDED]
    };
    return map[type] || 'grey';
}

watch(activeTab, (newTab) => {
  if (newTab === 'capsules') {
    if (capsules.value.length === 0) marketplaceStore.fetchCapsules();
  } else {
    const typeMap = {
        presets: 'preset',
        widgets: 'widget',
        modules: 'module',
        plugins: 'plugin',
        tools: 'tool',
        triggers: 'trigger'
    };
    const targetType = typeMap[newTab] || 'preset';
    marketplaceStore.fetchItems({ type: targetType });
  }
});

onMounted(() => {
  if (activeTab.value === 'presets') {
    marketplaceStore.fetchItems({ type: 'preset' });
  } else if (activeTab.value === 'capsules') {
    marketplaceStore.fetchCapsules();
  }
});
</script>

<style scoped>
.marketplace-page {
  min-height: 100vh;
  position: relative;
  z-index: 1; /* Cukup 1, jangan terlalu tinggi biar ga nutup navbar */
  padding-bottom: 48px;
}

/* Background Layer */
.background-layer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  background-color: #050505;
}

/* GOLD OVERLAY */
.gold-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 50% 0%, rgba(212, 175, 55, 0.05), transparent 70%);
  pointer-events: none;
}

.page-container {
  max-width: 1600px;
  margin-top: 24px;
}

/* FONTS */
.orbitron-font {
  font-family: 'Orbitron', monospace;
  letter-spacing: 2px;
  color: #f0f0f0;
}
.text-mono {
  font-family: 'Fira Code', monospace;
}

/* HUD HEADER - SETTINGS STYLE */
.hud-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
  padding: 0 0 20px 0;
  margin-bottom: 32px;
  opacity: 0; /* Mulai dari invisible sebelum animasi */
}

.hud-title-section {
  display: flex;
  align-items: center;
}

.icon-box-gold {
  border: 1px solid rgba(212, 175, 55, 0.3);
  padding: 8px;
  border-radius: 4px;
  background: rgba(212, 175, 55, 0.05);
  box-shadow: 0 0 15px rgba(212, 175, 55, 0.1);
}

.page-title {
  font-size: 1.8rem;
  font-weight: 500;
  margin: 0;
  line-height: 1;
  text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
}

.hud-subtitle {
  color: #888;
  font-size: 0.75rem;
  margin-top: 6px;
  letter-spacing: 1px;
}

/* GOLD TABS */
.gold-tabs .v-tab {
  color: #888 !important;
  font-family: 'Exo 2', sans-serif;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  text-transform: uppercase;
  font-size: 0.8rem;
}

.gold-tabs .v-tab--selected {
  color: #D4AF37 !important;
  text-shadow: 0 0 8px rgba(212, 175, 55, 0.4);
}

/* GRID LAYOUT */
.gold-grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

/* GOLD CARD DESIGN (ELEGANT DARK) */
.gold-card {
  background: rgba(15, 15, 20, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  overflow: hidden;
}

.gold-card:hover {
  transform: translateY(-4px);
  border-color: rgba(212, 175, 55, 0.4);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.gold-card:hover::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #D4AF37, transparent);
  box-shadow: 0 0 10px #D4AF37;
}

.card-header {
  padding: 20px 20px 10px 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e0e0e0;
  letter-spacing: 1px;
}

.card-body {
  padding: 0 20px 20px 20px;
  flex: 1;
}

.author-link {
  color: #D4AF37;
  text-decoration: none;
  font-size: 0.8rem;
  transition: color 0.2s;
}
.author-link:hover {
  color: #fff;
}

.card-desc {
  font-size: 0.85rem;
  color: #999;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.gold-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
  width: 100%;
}

.card-footer {
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.2);
  font-size: 0.8rem;
  color: #777;
}

/* UTILS */
.text-gold { color: #D4AF37; }
.text-gold-light { color: #F0E68C; }
.blink-text { animation: blink 2s infinite; }
.no-decoration { text-decoration: none; color: inherit; }

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* FIXED ANIMATIONS */
/* Animasi dari bawah ke atas (untuk items) */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-in-up { animation: fadeInUp 0.4s ease-out forwards; }

/* Animasi dari atas ke bawah (untuk Header) */
/* Gw benerin nih biar nggak ilang lagi */
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-in-down { animation: fadeInDown 0.5s ease-out forwards; }

/* RESPONSIVE */
@media (max-width: 600px) {
  .hud-header { flex-direction: column; align-items: flex-start; }
  .hud-controls { width: 100%; margin-top: 16px; overflow-x: auto; }
}
</style>
