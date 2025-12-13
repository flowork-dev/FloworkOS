//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\settings.js total lines 89 
//#######################################################################

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient, apiSetUserUiPreferences } from '@/api';
import { useLocaleStore } from './locale';

export const useSettingsStore = defineStore('settings', () => {
    const defaultSettings = {
        language: 'en',
        theme: 'dark',
        ai_model_for_text: 'openai',
        ai_gpu_layers: 0,
        webhook_enabled: false,
        global_error_handler_enabled: false,
        global_error_workflow_preset: null
    };

    const settings = ref({ ...defaultSettings });
    const isLoading = ref(false);
    const activeSection = ref('general');

    const savedLocal = localStorage.getItem('flowork_settings');
    if (savedLocal) {
        try {
            const parsed = JSON.parse(savedLocal);
            settings.value = { ...settings.value, ...parsed };
        } catch (e) {
            console.error("[Settings] Corrupted local storage, resetting...", e);
        }
    }

    async function fetchSettings() {
        isLoading.value = true;
        try {
            const response = await apiClient.get('/user/preferences');
            if (response.data && !response.data.error) {
                settings.value = { ...settings.value, ...response.data };

                const localeStore = useLocaleStore();
                if (settings.value.language && settings.value.language !== localeStore.currentLang) {
                    localeStore.setLanguage(settings.value.language);
                }
            }
        } catch (e) {
            console.warn("[Settings] Cloud sync failed, utilizing local cache only:", e);
        } finally {
            isLoading.value = false;
        }
    }

    async function saveSettingsAction() {
        isLoading.value = true;
        try {
            localStorage.setItem('flowork_settings', JSON.stringify(settings.value));

            await apiSetUserUiPreferences(settings.value);

            const localeStore = useLocaleStore();
            if (settings.value.language) {
                localeStore.setLanguage(settings.value.language);
            }

            return true;
        } catch (e) {
            console.error("[Settings] Save failed:", e);
            return false;
        } finally {
            isLoading.value = false;
        }
    }

    function setActiveSection(section) {
        activeSection.value = section;
    }

    return {
        settings,
        isLoading,
        activeSection,
        fetchSettings,
        saveSettingsAction,
        setActiveSection
    };
});
