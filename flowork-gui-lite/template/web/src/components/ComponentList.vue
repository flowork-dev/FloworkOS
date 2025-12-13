//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\ComponentList.vue total lines 413 
//#######################################################################

<template>
  <v-list density="compact" class="component-list">
    <div v-if="state && state.isLoading && state.items.length === 0" class="text-center pa-4">
      <v-progress-circular indeterminate color="cyan"></v-progress-circular>
    </div>

    <div v-else-if="(!groupedAndFilteredItems || Object.keys(groupedAndFilteredItems).length === 0) && filteredFavorites.length === 0" class="text-center pa-4 text-caption text-grey">
      No items found.
    </div>

    <div v-else>
      <div v-if="filteredFavorites.length > 0">
        <v-list-subheader class="category-header favorites-header">
          <v-icon size="x-small" class="mr-1">mdi-star</v-icon>
          Favorites
        </v-list-subheader>
        <v-tooltip
          v-for="item in filteredFavorites"
          :key="item.id"
          location="end"
          content-class="ai-tooltip"
        >
          <template v-slot:activator="{ props: tooltipProps }">
             <v-list-item
              v-bind="tooltipProps" draggable="true"
              @dragstart="onDragStart($event, item)"
              @click="onItemClick(item)"
              class="toolbox-item"
            >
              <template v-slot:prepend>
                <v-icon class="component-icon" :icon="categoryIcon" color="cyan-accent-3"></v-icon>
              </template>
              <div>
                <v-list-item-title class="item-title">{{ loc(item.name) || item.name }}</v-list-item-title>
                <v-list-item-subtitle class="item-subtitle">{{ item.id }}</v-list-item-subtitle>
              </div>

              <template v-slot:append>
                <div class="d-flex align-center button-group">
                  <v-btn
                    v-if="installingComponentId === item.id"
                    icon variant="text" size="x-small" disabled class="install-btn"
                  ><v-progress-circular indeterminate size="16" width="2" /></v-btn>
                  <v-btn
                    v-else-if="uninstallingComponentId === item.id"
                    icon variant="text" size="x-small" disabled color="error" class="install-btn"
                  ><v-progress-circular indeterminate size="16" width="2" color="error" /></v-btn>

                  <v-btn
                    v-else-if="item.is_installed"
                    icon="mdi-delete" variant="text" size="x-small" color="white"
                    @click.stop="componentStore.uninstallComponent(props.type, item.id)"
                    title="Uninstall dependencies" class="install-btn"
                  ></v-btn>

                  <v-btn
                    v-else
                    icon="mdi-download" variant="text" size="x-small" color="white"
                    @click.stop="componentStore.installComponent(props.type, item.id)"
                    title="Install dependencies" class="install-btn"
                  ></v-btn>

                  <v-btn
                    v-if="item.is_installed"
                    icon="mdi-cloud-upload"
                    variant="text"
                    size="x-small"
                    color="green-accent-3"
                    @click.stop="onUploadClick(item)"
                    title="Update/Upload to Marketplace"
                    class="action-btn"
                  ></v-btn>

                  <v-btn
                    :icon="favoriteComponents.includes(item.id) ? 'mdi-star' : 'mdi-star-outline'"
                    variant="text"
                    size="x-small"
                    color="white"
                    @click.stop="componentStore.toggleFavorite(item.id)"
                    :title="favoriteComponents.includes(item.id) ? 'Remove from favorites' : 'Add to favorites'"
                    class="favorite-btn"
                  ></v-btn>
                </div>
              </template>
            </v-list-item>
          </template>
          <div class="ai-tooltip-content">
            <div class="font-weight-bold mb-1">{{ loc(item.name) || item.name }}</div>
            {{ loc(item.manifest?.description) || item.description || 'No description available.' }}
            <v-divider class="my-2"></v-divider>
            <span :class="item.is_installed ? 'text-green-lighten-2' : 'text-red-lighten-2'" class="text-caption d-flex align-center">
              <v-icon :icon="item.is_installed ? 'mdi-check-circle' : 'mdi-close-circle'" size="x-small" class="mr-1"></v-icon>
              {{ item.is_installed ? 'Dependencies Installed' : 'Not Installed' }}
            </span>
          </div>
        </v-tooltip>
      </div>

      <div v-for="(components, category) in groupedAndFilteredItems" :key="category">
        <v-list-subheader class="category-header">{{ category }}</v-list-subheader>
        <v-tooltip
          v-for="item in components"
          :key="item.id"
          location="end"
          content-class="ai-tooltip"
        >
          <template v-slot:activator="{ props: tooltipProps }">
             <v-list-item
              v-bind="tooltipProps" draggable="true"
              @dragstart="onDragStart($event, item)"
              @click="onItemClick(item)"
              class="toolbox-item"
            >
              <template v-slot:prepend>
                <v-icon class="component-icon" :icon="categoryIcon" color="cyan-accent-3"></v-icon>
              </template>
              <div>
                <v-list-item-title class="item-title">{{ loc(item.name) || item.name }}</v-list-item-title>
                <v-list-item-subtitle class="item-subtitle">{{ item.id }}</v-list-item-subtitle>
              </div>

              <template v-slot:append>
                <div class="d-flex align-center button-group">
                  <v-btn
                    v-if="installingComponentId === item.id"
                    icon variant="text" size="x-small" disabled class="install-btn"
                  ><v-progress-circular indeterminate size="16" width="2" /></v-btn>
                  <v-btn
                    v-else-if="uninstallingComponentId === item.id"
                    icon variant="text" size="x-small" disabled color="error" class="install-btn"
                  ><v-progress-circular indeterminate size="16" width="2" color="error" /></v-btn>

                  <v-btn
                    v-else-if="item.is_installed"
                    icon="mdi-delete" variant="text" size="x-small" color="white"
                    @click.stop="componentStore.uninstallComponent(props.type, item.id)"
                    title="Uninstall dependencies" class="install-btn"
                  ></v-btn>

                  <v-btn
                    v-else
                    icon="mdi-download" variant="text" size="x-small" color="white"
                    @click.stop="componentStore.installComponent(props.type, item.id)"
                    title="Install dependencies" class="install-btn"
                  ></v-btn>

                  <v-btn
                    v-if="item.is_installed"
                    icon="mdi-cloud-upload"
                    variant="text"
                    size="x-small"
                    color="green-accent-3"
                    @click.stop="onUploadClick(item)"
                    title="Update/Upload to Marketplace"
                    class="action-btn"
                  ></v-btn>

                  <v-btn
                    :icon="favoriteComponents.includes(item.id) ? 'mdi-star' : 'mdi-star-outline'"
                    variant="text"
                    size="x-small"
                    color="white"
                    @click.stop="componentStore.toggleFavorite(item.id)"
                    :title="favoriteComponents.includes(item.id) ? 'Remove from favorites' : 'Add to favorites'"
                    class="favorite-btn"
                  ></v-btn>
                </div>
              </template>
            </v-list-item>
          </template>
          <div class="ai-tooltip-content">
            <div class="font-weight-bold mb-1">{{ loc(item.name) || item.name }}</div>
            {{ loc(item.manifest?.description) || item.description || 'No description available.' }}
            <v-divider class="my-2"></v-divider>
            <span :class="item.is_installed ? 'text-green-lighten-2' : 'text-red-lighten-2'" class="text-caption d-flex align-center">
              <v-icon :icon="item.is_installed ? 'mdi-check-circle' : 'mdi-close-circle'" size="x-small" class="mr-1"></v-icon>
              {{ item.is_installed ? 'Dependencies Installed' : 'Not Installed' }}
            </span>
          </div>
        </v-tooltip>
      </div>
    </div>
    <div ref="observerEl" class="observer"></div>
    <div v-if="state && state.isLoading && state.items.length > 0" class="text-center pa-2 text-caption">{{ loc('toolbox_loading_more') }}</div>
  </v-list>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useComponentStore } from '@/store/components';
import { useLocaleStore } from '@/store/locale';
import { storeToRefs } from 'pinia';

const props = defineProps({
  type: {
    type: String,
    required: true,
  },
  searchTerm: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['item-click', 'upload-request']);

const componentStore = useComponentStore();
const localeStore = useLocaleStore();

const { loc } = storeToRefs(localeStore);
const {
  favoriteComponents,
  installingComponentId,
  uninstallingComponentId
} = storeToRefs(componentStore);

const state = computed(() => {
    if (!componentStore || !componentStore[props.type]) return { items: [], isLoading: false };
    return componentStore[props.type];
});

const observerEl = ref(null);
let observer;

const categoryIcon = computed(() => {
    switch(props.type) {
        case 'modules': return 'mdi-cog-outline';
        case 'plugins': return 'mdi-power-plug-outline';
        case 'triggers': return 'mdi-flash';
        default: return 'mdi-cube-outline';
    }
});

const onDragStart = (event, item) => {
  if (event.dataTransfer) {
    if (!item.is_installed) {
        event.preventDefault();
        console.warn(`[ComponentList] Drag aborted: Component ${item.id} is not installed.`);
        return;
    }
    const dataToTransfer = JSON.stringify({
      ...item,
      componentType: props.type
    });
    event.dataTransfer.setData('application/json', dataToTransfer);
    event.dataTransfer.effectAllowed = 'move';
  }
};

const onItemClick = (item) => {
  console.log(`[ComponentList] Item clicked: ${item.id}`);
  emit('item-click', item);
};

const onUploadClick = (item) => {
    console.log(`[ComponentList] Upload requested for: ${item.id}`);
    emit('upload-request', item);
};

const baseFilteredItems = computed(() => {
    if (!state.value || !state.value.items) return [];
    let items = state.value.items;

    if (props.searchTerm) {
        const q = props.searchTerm.toLowerCase();
        items = items.filter(t =>
            (t.name && t.name.toLowerCase().includes(q)) ||
            (t.id && t.id.toLowerCase().includes(q)) ||
            (t.description && t.description.toLowerCase().includes(q)) ||
            (t.manifest?.name && t.manifest.name.toLowerCase().includes(q)) ||
            (t.manifest?.description && t.manifest.description.toLowerCase().includes(q))
        );
    }
    return items;
});

const filteredFavorites = computed(() => {
    return baseFilteredItems.value
        .filter(item => favoriteComponents.value.includes(item.id))
        .sort((a, b) => (a.name || '').localeCompare(b.name || ''));
});

const groupedAndFilteredItems = computed(() => {
  const nonFavoriteItems = baseFilteredItems.value.filter(item => !favoriteComponents.value.includes(item.id));

  const items = nonFavoriteItems || [];
  if (!items) return {};

  const grouped = items.reduce((groups, item) => {
    const category = item.manifest?.type?.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || 'Uncategorized';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(item);
    return groups;
  }, {});

  const sortedCategories = Object.keys(grouped).sort();
  const sortedGrouped = {};
  sortedCategories.forEach(category => {
    sortedGrouped[category] = grouped[category].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  });
  return sortedGrouped;
});


onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      componentStore.fetchComponentsForType(props.type);
    }
  }, { root: null, rootMargin: '0px', threshold: 1.0 });

  if (observerEl.value) {
    observer.observe(observerEl.value);
  }
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
});

watch(() => props.type, (newType, oldType) => {
    if (newType !== oldType) {
        console.log(`[ComponentList] Type changed to ${newType}. Fetching components with reset...`);
        componentStore.fetchComponentsForType(newType, { reset: true });
    }
});
</script>

<style scoped>
.component-list {
  background-color: transparent;
}
.category-header {
  font-weight: bold;
  text-transform: uppercase;
  font-size: 0.7rem;
  color: #64ffda;
  padding: 16px 16px 8px 16px;
  background-color: #1a1a2e;
  position: sticky;
  top: 0;
  z-index: 1;
}
.favorites-header {
    color: #FFEB3B; /* Kuning */
    display: flex;
    align-items: center;
}
.toolbox-item {
  transition: background-color 0.2s ease-in-out, transform 0.1s ease;
  cursor: pointer;
  padding-left: 16px !important;
  border-radius: 4px;
  margin: 4px 8px;
}
.toolbox-item:hover {
  background-color: rgba(100, 255, 218, 0.1);
  transform: translateX(4px);
}
.component-icon {
  margin-right: 12px;
  opacity: 0.8;
  filter: drop-shadow(0 0 2px rgba(100, 255, 218, 0.5));
}
.item-title {
  font-weight: 500;
  color: #ccd6f6;
}
.item-subtitle {
  font-size: 0.75rem;
  color: #8892b0;
  font-family: 'Fira Code', monospace;
}
.observer {
    height: 10px;
}
.ai-tooltip-content {
  max-width: 300px;
  white-space: normal;
  word-wrap: break-word;
  padding: 12px;
}
:deep(.ai-tooltip) {
    max-width: 320px !important;
    pointer-events: none;
}

/* --- STYLE TOMBOL BARU --- */
.button-group {
    opacity: 0;
    transition: opacity 0.2s ease;
    display: flex;
    align-items: center;
}
.toolbox-item:hover .button-group,
.toolbox-item .button-group .v-btn[disabled],
.toolbox-item .button-group .favorite-btn .v-icon.mdi-star {
    opacity: 1;
}
.install-btn, .action-btn {
    width: 24px;
}
</style>
