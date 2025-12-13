//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\variables.js total lines 114 
//#######################################################################

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient } from '@/api';

export const useVariablesStore = defineStore('variables', () => {
    const variables = ref([]);
    const isLoading = ref(false);
    const error = ref(null);

    const SYSTEM_VARIABLES = [
        { name: 'OPENAI_API_KEY', defaultValue: 'CHANGE THIS API' },
        { name: 'GEMINI_API_KEY', defaultValue: 'CHANGE THIS API' }
    ];

    async function fetchVariables() {
        isLoading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get('/variables');
            const rawData = response.data || [];

            let varList = Array.isArray(rawData) ? rawData : Object.entries(rawData).map(([k, v]) => ({
                name: k,
                value: v,
                is_enabled: true,
                is_secret: false
            }));

            SYSTEM_VARIABLES.forEach(sysVar => {
                const exists = varList.find(v => v.name === sysVar.name);

                if (!exists) {
                    varList.unshift({
                        name: sysVar.name,
                        value: { type: 'static', value: sysVar.defaultValue },
                        is_enabled: true,
                        is_secret: false,
                        is_protected: true // Flag: Gak bisa dihapus & Nama gak bisa diedit
                    });
                } else {
                    exists.is_protected = true;
                }
            });

            variables.value = varList;
            console.log('[Variables] Loaded:', variables.value.length, 'items');
        } catch (e) {
            console.error('[Variables] Fetch failed:', e);
            error.value = e.response?.data?.error || e.message;
        } finally {
            isLoading.value = false;
        }
    }

    async function saveVariable(name, variableData) {
        try {

            const payload = {
                value: variableData.value, // Object {type: 'static', value: '...'}
                is_enabled: variableData.is_enabled,
                is_secret: variableData.is_secret,
                mode: 'single'
            };

            await apiClient.put(`/variables/${encodeURIComponent(name)}`, payload);

            const idx = variables.value.findIndex(v => v.name === name);
            if (idx !== -1) {
                variables.value[idx] = { ...variables.value[idx], ...payload };
            } else {
                variables.value.push({ name, ...payload });
            }

            return true;
        } catch (e) {
            console.error(`[Variables] Failed to save ${name}:`, e);
            throw new Error(e.response?.data?.error || e.message);
        }
    }

    async function removeVariable(name) {
        if (SYSTEM_VARIABLES.some(sv => sv.name === name)) {
            console.warn("Cannot delete system variable:", name);
            return false;
        }

        isLoading.value = true;
        try {
            await apiClient.delete(`/variables/${encodeURIComponent(name)}`);
            variables.value = variables.value.filter(v => v.name !== name);
            return true;
        } catch (e) {
            console.error(`[Variables] Failed to delete ${name}:`, e);
            return false;
        } finally {
            isLoading.value = false;
        }
    }

    return {
        variables,
        isLoading,
        error,
        fetchVariables,
        saveVariable,
        removeVariable
    };
});
