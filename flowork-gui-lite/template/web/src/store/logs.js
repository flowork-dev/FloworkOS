//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\logs.js total lines 68 
//#######################################################################

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useComponentStore } from './components';
import { useWorkflowStore } from './workflow'; // (English Hardcode) Import Workflow Store

export const useLogStore = defineStore('logs', () => {
    const timelineEntries = ref([]);
    const executionLogs = ref([]);
    const componentStore = useComponentStore();

    const detailedTimeline = computed(() => {
        const workflowStore = useWorkflowStore();

        return timelineEntries.value.map(entry => {
            const node = workflowStore.nodes.find(n => n.id === entry.node_id);

            let displayName = entry.node_id;

            if (node) {
                displayName = node.label;
            } else if (entry.module_id) {
                 const component = componentStore.findComponentById(entry.module_id);
                 if (component) displayName = component.name;
            }

            return {
                ...entry,
                node_name: displayName,
                status: entry.status ? entry.status.toUpperCase() : 'UNKNOWN'
            };
        }).sort((a, b) => a.timestamp - b.timestamp);
    });


    function updateTimelineEntry(log) {
        const existingEntryIndex = timelineEntries.value.findIndex(e => e.node_id === log.node_id);

        if (existingEntryIndex > -1) {
            timelineEntries.value[existingEntryIndex] = { ...timelineEntries.value[existingEntryIndex], ...log };
        } else {
            timelineEntries.value.push(log);
        }
    }

    function addExecutionLog(log) {
        executionLogs.value.push(log);
    }

    function clearLogs() {
        timelineEntries.value = [];
        executionLogs.value = [];
    }

    return {
        timelineEntries,
        detailedTimeline,
        executionLogs,
        updateTimelineEntry,
        addExecutionLog,
        clearLogs,
    };
});
