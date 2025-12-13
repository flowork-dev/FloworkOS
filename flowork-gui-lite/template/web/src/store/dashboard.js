//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\dashboard.js total lines 76 
//#######################################################################

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiGetDashboardSummary } from '@/api';

export const useDashboardStore = defineStore('dashboard', () => {
    const summary = ref({
        active_jobs: [],
        recent_activity: [],
        execution_stats_24h: { success: 0, failed: 0 },
        execution_timeseries_24h: { labels: [], datasets: [] },
        system_overview: {
            kernel_version: 'N/A',
            license_tier: 'N/A',
            modules: 0,
            plugins: 0,
            widgets: 0,
            triggers: 0,
            presets: 0,
            status: 'unknown'
        },
        top_failing_presets: [],
        top_slowest_presets: [],
        usage_stats: {
            used: 0
        },
        total_engines: 0,
        total_shared_with_me: 0
    });
    const isInitialLoading = ref(true);
    const isRefreshing = ref(false);
    const error = ref(null);

    async function fetchDashboardSummary(isRefresh = false, engineId = null) {
        if (!isRefresh) {
            isInitialLoading.value = true;
        }
        isRefreshing.value = true;
        error.value = null;
        try {
            const data = await apiGetDashboardSummary(engineId);
            summary.value = {
                ...summary.value,
                ...data,
                execution_stats_24h: data.execution_stats_24h || summary.value.execution_stats_24h,
                system_overview: { ...summary.value.system_overview, ...(data.system_overview || {}) }
            };
        } catch (e) {
            error.value = e.error || 'Failed to fetch dashboard summary.';
            console.error('[STORE] Failed to fetch dashboard summary:', e);
        } finally {
            isInitialLoading.value = false;
            isRefreshing.value = false;
        }
    }

    function updateActiveJobs(activeJobsList) {
        if (summary.value) {
            summary.value.active_jobs = activeJobsList;
        }
    }

    return {
        summary,
        isInitialLoading,
        isRefreshing,
        error,
        fetchDashboardSummary,
        updateActiveJobs,
    };
});
