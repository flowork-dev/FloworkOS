//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\components.js total lines 336 
//#######################################################################

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useLocaleStore } from './locale';
import exampleComponents from '../../public/example/components.json';
import { apiGetUserComponentFavorites, apiSetUserComponentFavorites, apiSaveCustomComponent, apiClient } from '@/api';
import { debounce } from '@/utils/debounce.js';
import { useAuthStore } from './auth';
import { useUiStore } from './ui';

const CACHE_KEY_PREFIX = 'flowork_component_cache_';

const createComponentTypeState = () => ({
  items: [],
  isLoading: false,
  hasFetched: false,
});

export const useComponentStore = defineStore('components', () => {
  const modules = ref(createComponentTypeState());
  const plugins = ref(createComponentTypeState());
  const tools = ref(createComponentTypeState());
  const triggers = ref(createComponentTypeState());
  const favoriteComponents = ref([]);
  const installingComponentId = ref(null);
  const uninstallingComponentId = ref(null);

  const fetchTimers = ref({});
  const error = ref(null);

  const isLoading = computed(() =>
    modules.value.isLoading ||
    plugins.value.isLoading ||
    tools.value.isLoading ||
    triggers.value.isLoading
  );

  const allComponents = computed(() => {
        const all = [];
        modules.value.items.forEach(m => all.push({ ...m, componentType: 'modules' }));
        plugins.value.items.forEach(p => all.push({ ...p, componentType: 'plugins' }));
        tools.value.items.forEach(t => all.push({ ...t, componentType: 'tools' }));
        triggers.value.items.forEach(t => all.push({ ...t, componentType: 'triggers' }));
        return all;
    });

    const findComponentById = (id) => {
        return allComponents.value.find(c => c.id === id);
    };

  function clearTimersForType(type) {
    if (fetchTimers.value[type]) {
      clearTimeout(fetchTimers.value[type]?.realDataTimeoutId);
      delete fetchTimers.value[type];
    }
  }

  const saveFavoritesDebounced = debounce(async () => {
    const authStore = useAuthStore();
    if (!authStore.isAuthenticated) return;
    try {
        await apiSetUserComponentFavorites(favoriteComponents.value);
    } catch (error) {
        console.error("[ComponentStore] Failed to save favorites:", error);
    }
  }, 1500);

  async function fetchUserFavorites() {
    const authStore = useAuthStore();
    if (!authStore.isAuthenticated) return;
    try {
        const favorites = await apiGetUserComponentFavorites();
        if (favorites.error) throw new Error(favorites.error);
        favoriteComponents.value = favorites;
    } catch (error) {
        favoriteComponents.value = [];
    }
  }

  function toggleFavorite(componentId) {
    const index = favoriteComponents.value.indexOf(componentId);
    if (index > -1) {
        favoriteComponents.value.splice(index, 1);
    } else {
        favoriteComponents.value.push(componentId);
    }
    saveFavoritesDebounced();
  }

  async function getSocketStore() {
      const { useSocketStore } = await import('./socket');
      return useSocketStore();
  }

  async function installComponent(componentType, componentId) {
    if (installingComponentId.value || uninstallingComponentId.value) return;

    installingComponentId.value = componentId;
    try {
        const socketStore = await getSocketStore();
        await socketStore.sendMessage({
            type: 'install_component',
            component_type: componentType,
            component_id: componentId,
        });
        useUiStore().showNotification({ text: `Installing ${componentId}...`, color: 'info' });
    } catch (e) {
        useUiStore().showNotification({ text: `Install failed: ${e.message}`, color: 'error' });
        installingComponentId.value = null;
    }
  }

  async function uninstallComponent(componentType, componentId) {
    if (installingComponentId.value || uninstallingComponentId.value) return;

    uninstallingComponentId.value = componentId;
    try {
        const socketStore = await getSocketStore();
        await socketStore.sendMessage({
            type: 'uninstall_component',
            component_type: componentType,
            component_id: componentId,
        });
        useUiStore().showNotification({ text: `Uninstalling ${componentId}...`, color: 'info' });
    } catch (e) {
        useUiStore().showNotification({ text: `Uninstall failed: ${e.message}`, color: 'error' });
        uninstallingComponentId.value = null;
    }
  }

  function handleInstallStatusUpdate(data) {
    const { component_id, component_type, success, message, is_installed } = data;

    if (installingComponentId.value === component_id) installingComponentId.value = null;
    if (uninstallingComponentId.value === component_id) uninstallingComponentId.value = null;

    const uiStore = useUiStore();
    if (success) {
        uiStore.showNotification({ text: `${component_id}: ${message}`, color: 'success' });
    } else {
        uiStore.showNotification({ text: `${component_id}: ${message}`, color: 'error', timeout: 7000 });
    }

    const stateMap = { modules, plugins, tools, triggers };
    const stateRef = stateMap[component_type];
    if (stateRef && stateRef.value) {
        const item = stateRef.value.items.find(i => i.id === component_id);
        if (item) {
            item.is_installed = is_installed;
            saveToCache(component_type, stateRef.value.items);
        }
    }
  }

  function updateComponentsList(type, components, errorMessage = null) {
    const stateMap = { modules, plugins, tools, triggers };
    const stateRef = stateMap[type];

    if (stateRef && stateRef.value) {
      stateRef.value.isLoading = false;
      stateRef.value.hasFetched = true;

      if (errorMessage) {
          console.warn(`[ComponentStore] Received ERROR for ${type}: ${errorMessage}`);
          return;
      }

      const processedComponents = components.map(c => ({
          ...c,
          is_example: false,
          is_installed: (c.is_installed !== undefined) ? c.is_installed : true
      }));

      stateRef.value.items = processedComponents;
      error.value = null;
      saveToCache(type, processedComponents);
    }
  }

  function saveToCache(type, items) {
      try {
          localStorage.setItem(CACHE_KEY_PREFIX + type, JSON.stringify(items));
      } catch (e) {}
  }

  async function fetchComponentsForType(type, options = { reset: false }) {
    const stateMap = { modules, plugins, tools, triggers };
    const stateRef = stateMap[type];
    if (!stateRef || !stateRef.value) return;

    const currentState = stateRef.value;
    clearTimersForType(type);

    if (options.reset) currentState.hasFetched = false;

    if (currentState.items.length === 0) {
        try {
            const cachedData = localStorage.getItem(CACHE_KEY_PREFIX + type);
            if (cachedData) {
                const parsedItems = JSON.parse(cachedData);
                if (Array.isArray(parsedItems) && parsedItems.length > 0) {
                    currentState.items = parsedItems;
                }
            }
        } catch (e) { }
    }

    currentState.isLoading = true;
    error.value = null;

    try {
        console.log(`[ComponentStore] Fetching ${type} via HTTP API (Hybrid Mode)...`);

        const response = await apiClient.get(`/${type}`);

        if (response.data && !response.data.error) {
             console.log(`[ComponentStore] HTTP Success for ${type}`);
             updateComponentsList(type, response.data.components || response.data);
             return;
        }
    } catch (httpError) {
        console.warn(`[ComponentStore] HTTP fetch for ${type} failed, trying Socket/Fallback...`, httpError);
    }

    try {
        const socketStore = await getSocketStore();
        if (socketStore.isConnected) {
            const targetEngineId = localStorage.getItem('flowork_selected_engine_id') || 'local-engine-default';
            const payload = {
                type: 'request_components_list',
                component_type: type,
                target_engine_id: targetEngineId
            };
            socketStore.sendMessage(payload);

            fetchTimers.value[type] = {
                realDataTimeoutId: setTimeout(() => {
                    if (currentState.isLoading && currentState.items.length === 0) {
                        loadExampleData(type);
                    }
                    currentState.isLoading = false;
                }, 4000)
            };
            return;
        }
    } catch (e) {
        console.warn("[ComponentStore] Socket unavailable.");
    }

    if (currentState.items.length === 0) {
        loadExampleData(type);
    } else {
        currentState.isLoading = false;
    }
  }

  function loadExampleData(type) {
      const stateMap = { modules, plugins, tools, triggers };
      const stateRef = stateMap[type];
      const localeStore = useLocaleStore();
      const exampleData = exampleComponents[type] || [];

      console.warn(`[ComponentStore] Using EXAMPLE DATA for ${type}`);

      stateRef.value.items = exampleData.map(c => ({
          ...c,
          name: localeStore.loc(c.name) || c.name,
          manifest: {
              ...c.manifest,
              name: localeStore.loc(c.manifest?.name) || c.manifest?.name || c.name,
              description: localeStore.loc(c.manifest?.description) || c.manifest?.description || ''
          },
          is_example: true,
          is_installed: true
      }));
      stateRef.value.isLoading = false;
  }

  async function fetchAllComponents() {
      await Promise.all([
          fetchComponentsForType('modules'),
          fetchComponentsForType('plugins'),
          fetchComponentsForType('tools'),
          fetchComponentsForType('triggers')
      ]);
  }

  async function forceRefetchAllComponents() {
      await Promise.all([
          fetchComponentsForType('modules',  { reset: true }),
          fetchComponentsForType('plugins',  { reset: true }),
          fetchComponentsForType('tools',    { reset: true }),
          fetchComponentsForType('triggers', { reset: true })
      ]);
  }

  async function saveCustomComponent(componentData) {
      const uiStore = useUiStore();
      try {
          const result = await apiSaveCustomComponent(componentData);
          if (result.error) throw new Error(result.error);
          uiStore.showNotification({ text: `Component saved!`, color: 'success' });
          await fetchComponentsForType(componentData.type + 's', { reset: true });
          return { success: true };
      } catch (e) {
          uiStore.showNotification({ text: `Save failed: ${e.message}`, color: 'error' });
          return { success: false, error: e.message };
      }
  }

  return {
    modules, plugins, tools, triggers,
    favoriteComponents,
    installingComponentId,
    uninstallingComponentId,
    isLoading,
    allComponents,
    fetchComponentsForType,
    fetchAllComponents,
    forceRefetchAllComponents,
    updateComponentsList,
    findComponentById,
    fetchUserFavorites,
    toggleFavorite,
    installComponent,
    uninstallComponent,
    handleInstallStatusUpdate,
    saveCustomComponent,
    error
  };
});
