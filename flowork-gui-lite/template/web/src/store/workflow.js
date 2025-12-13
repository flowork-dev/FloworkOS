//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\workflow.js total lines 638 
//#######################################################################

import { defineStore } from 'pinia';
import { ref, computed, watch, nextTick } from 'vue';
import { v4 as uuidv4 } from 'uuid';
import { useUiStore } from '@/store/ui';
import { useComponentStore } from '@/store/components';
import { useLogStore } from '@/store/logs';
import { useSocketStore } from '@/store/socket';
import { ethers } from 'ethers';
import { useAuthStore } from '@/store/auth';
import { apiCreateShareLink, apiGetWorkflowShares, apiUpdateSharePermission, apiDeleteShare, apiResolveShareToken, apiGetUserFavorites, apiSetUserFavorites } from '@/api';
import { debounce } from '@/utils/debounce.js';


const delay = (ms) => new Promise(res => setTimeout(res, ms));

function stableStringify(obj) {
    const replacer = (key, value) => {
        if (value === null) return null;
        if (typeof value === 'object' && !Array.isArray(value)) {
            return Object.keys(value).sort().reduce((sorted, key) => {
                sorted[key] = value[key];
                return sorted;
            }, {});
        }
        return value;
    };
    try {
        const initiallySortedString = JSON.stringify(obj, replacer);
        return JSON.stringify(JSON.parse(initiallySortedString), replacer, undefined);
    } catch (e) {
        return JSON.stringify(obj);
    }
}

export const useWorkflowStore = defineStore('workflow', () => {
    const elements = ref([]);
    const selectedNode = ref(null);
    const currentPresetName = ref(null);
    const isExecuting = ref(false);
    const isPaused = ref(false);
    const jobId = ref(null);
    const executionStatus = ref({});
    const connectionStatus = ref({});
    const presets = ref([]);
    const favoritePresets = ref([]);
    const clipboard = ref(null);
    const globalLoopConfig = ref({
        isEnabled: false, iterations: 1, isDelayEnabled: false,
        delayType: 'static', delayStatic: 1, delayRandomMin: 1, delayRandomMax: 5
    });
    const isStopRequested = ref(false);
    const permissionLevel = ref('edit');
    const error = ref(null);
    const isModified = ref(false);
    const isLoadingPresets = ref(false);

    const nodes = computed(() => elements.value.filter(el => 'position' in el));
    const edges = computed(() => elements.value.filter(el => 'source' in el));
    const isCanvasEmpty = computed(() => nodes.value.length === 0);
    const isReadOnly = computed(() => permissionLevel.value === 'view');

    const canExecute = computed(() => {
        const hasPermission = permissionLevel.value === 'view-run' || permissionLevel.value === 'edit' || permissionLevel.value === 'view-edit-run';
        return hasPermission && !isCanvasEmpty.value;
    });

    const selectedNodeHasBehavior = computed(() => (behaviorName) => {
        if (!selectedNode.value?.data?.manifest?.behaviors) return false;
        return selectedNode.value.data.manifest.behaviors.includes(behaviorName);
    });

    const getWorkflowForPublishing = computed(() => {
        return {
            nodes: nodes.value.map(node => ({
                id: node.id,
                name: node.label,
                x: node.position.x,
                y: node.position.y,
                module_id: node.data.moduleId,
                config_values: node.data.config_values || {},
                ...(node.data.color && { data: { color: node.data.color } })
            })),
            connections: edges.value.map(edge => ({
                id: edge.id,
                source: edge.source,
                target: edge.target,
                source_port_name: edge.sourceHandle,
                target_port_name: edge.targetHandle,
                type: edge.type,
                animated: edge.animated,
            })),
            global_loop_config: globalLoopConfig.value
        };
    });

    async function fetchUserFavorites() {
        const authStore = useAuthStore();
        if (!authStore.isAuthenticated) return;
        try {
            console.log("[WorkflowStore] Fetching user favorites...");
            const favorites = await apiGetUserFavorites();
            if (favorites.error) throw new Error(favorites.error);
            favoritePresets.value = favorites;
        } catch (error) {
            console.error("[WorkflowStore] Failed to fetch favorites:", error);
            favoritePresets.value = [];
        }
    }

    const saveFavoritesDebounced = debounce(async () => {
        const authStore = useAuthStore();
        if (!authStore.isAuthenticated) return;
        try {
            await apiSetUserFavorites(favoritePresets.value);
        } catch (error) {
            console.error("[WorkflowStore] Save favorites failed:", error);
        }
    }, 1500);

    function toggleFavorite(presetName) {
        const index = favoritePresets.value.indexOf(presetName);
        if (index > -1) favoritePresets.value.splice(index, 1);
        else favoritePresets.value.push(presetName);
        saveFavoritesDebounced();
    }

    function applyChanges(changes) {
        if (isReadOnly.value) return;
        let tempElements = [...elements.value];
        let selectionChanged = false;

        changes.forEach(change => {
            const index = tempElements.findIndex(el => el.id === change.id);
            if (change.type === 'remove' && index !== -1) {
                if (selectedNode.value && selectedNode.value.id === change.id) selectionChanged = true;
                tempElements.splice(index, 1);
                isModified.value = true;
            } else if (change.type === 'position' && change.position && index !== -1) {
                tempElements[index].position = change.position;
                isModified.value = true;
            }
        });
        elements.value = tempElements;
        if (selectionChanged) clearSelectedNode();
    }

    async function fetchConnectionData(connectionId) {
        const uiStore = useUiStore();
        const currentJobId = jobId.value;
        if (!currentJobId) {
            uiStore.showDataViewer({ title: `Data`, error: "Run workflow first." });
            return;
        }
        try {
            const socketStore = useSocketStore();
            await socketStore.sendMessage({
                type: 'request_connection_history',
                job_id: currentJobId,
                connection_id: connectionId
            });
        } catch (error) {
            uiStore.showDataViewer({ title: `Data`, error: "No history found.", details: error.message });
        }
    }

    function updateConnectionStatus(data) {
        if (!data?.connection_id) return;
        connectionStatus.value = {
            ...connectionStatus.value,
            [data.connection_id]: { status: data.status, timestamp: Date.now() }
        };
        if (data.status === 'ACTIVE') {
            setTimeout(() => {
                 if (connectionStatus.value[data.connection_id]) {
                     connectionStatus.value = {
                         ...connectionStatus.value,
                         [data.connection_id]: { ...connectionStatus.value[data.connection_id], status: 'IDLE' }
                     };
                 }
            }, 2000);
        }
    }

    function animateIncomingEdges(targetNodeId) {
        const incomingEdges = edges.value.filter(e => e.target === targetNodeId);
        incomingEdges.forEach(edge => {
            updateConnectionStatus({ connection_id: edge.id, status: 'ACTIVE' });
        });
    }

    function setNodeColor({ nodeId, color }) {
      if (isReadOnly.value) return;
      const node = elements.value.find(el => el.id === nodeId);
      if (node) {
        if (!node.data) node.data = {};
        node.data.color = color;
        isModified.value = true;
      }
    }

    function removeElements(elementsToRemove) {
      if (isReadOnly.value) return;
      const idsToRemove = new Set(elementsToRemove.map(el => el.id));
      elements.value = elements.value.filter(el => !idsToRemove.has(el.id));
      if (selectedNode.value && idsToRemove.has(selectedNode.value.id)) clearSelectedNode();
      isModified.value = true;
    }

    function copyNode(node) {
        clipboard.value = JSON.parse(JSON.stringify(node));
    }

    function pasteNode({ x, y }) {
        if (isReadOnly.value || !clipboard.value) return;
        const nodeDataToPaste = JSON.parse(JSON.stringify(clipboard.value.data));
        const componentStore = useComponentStore();
        const component = componentStore.findComponentById(nodeDataToPaste.moduleId);

        if (!component) return;

        const defaultConfig = (component.manifest?.properties || []).reduce((acc, prop) => {
            if (prop.default !== undefined) acc[prop.id] = prop.default;
            return acc;
        }, {});

        const newNode = {
            id: uuidv4(),
            type: 'default',
            label: clipboard.value.label,
            position: { x, y },
            data: {
              moduleId: nodeDataToPaste.moduleId,
              componentType: nodeDataToPaste.componentType,
              config_values: { ...defaultConfig, ...(nodeDataToPaste.config_values || {}) },
              color: nodeDataToPaste.color,
            },
        };
        elements.value = [...elements.value, newNode];
        isModified.value = true;
    }

    function duplicateNode(node) {
        if (isReadOnly.value) return;
        const { x, y } = node.position;
        copyNode(node);
        pasteNode({ x: x + 40, y: y + 40 });
    }

    async function fetchPresets() {
        isLoadingPresets.value = true;
        try {
            const socketStore = useSocketStore();
            if (socketStore.isConnected) {
                await socketStore.sendMessage({ type: 'request_presets_list' });
            } else {
                isLoadingPresets.value = false;
            }
        } catch (error) {
            isLoadingPresets.value = false;
        }
    }

    function updatePresetsList(presetList) {
        presets.value = presetList.map(p => ({ id: p.name, name: p.name }));
        isLoadingPresets.value = false;
    }

    function handleFetchError(errorMessage) {
        isLoadingPresets.value = false;
        error.value = errorMessage;
    }

    function addNode(component) {
        if (isReadOnly.value || !component?.moduleId) return;
        const componentStore = useComponentStore();
        const fullComponentData = componentStore.findComponentById(component.moduleId);
        if (!fullComponentData) return;

        const defaultConfig = (fullComponentData.manifest?.properties || []).reduce((acc, prop) => {
            if (prop.default !== undefined) acc[prop.id] = prop.default;
            return acc;
        }, {});

        const newNode = {
            id: uuidv4(),
            type: 'default',
            label: fullComponentData.name,
            position: { x: component.x, y: component.y },
            data: {
                moduleId: fullComponentData.id,
                componentType: fullComponentData.componentType,
                config_values: defaultConfig,
            }
        };
        elements.value = [...elements.value, newNode];
        isModified.value = true;
    }

    function addEdge(connectionData) {
        if (isReadOnly.value) return;
        const newEdge = {
            id: `edge-${uuidv4()}`,
            type: 'default',
            animated: true,
            source: connectionData.source,
            target: connectionData.target,
            sourceHandle: connectionData.sourceHandle,
            targetHandle: connectionData.targetHandle,
        };
        elements.value = [...elements.value, newEdge];
        isModified.value = true;
    }

    function setSelectedNode(node) {
        if (selectedNode.value?.id !== node.id) selectedNode.value = node;
    }

    function clearSelectedNode() {
        if (selectedNode.value) selectedNode.value = null;
    }

    function updateNodeConfig({ nodeId, key, value }) {
        if (isReadOnly.value) return;
        const nodeIndex = elements.value.findIndex(el => el.id === nodeId && 'position' in el);
        if (nodeIndex !== -1) {
            if (!elements.value[nodeIndex].data.config_values) elements.value[nodeIndex].data.config_values = {};
            elements.value[nodeIndex].data.config_values[key] = value;
            isModified.value = true;
        }
    }

    async function loadWorkflow(presetName, ownerId = null) {
        if (!presetName) return false;
        const uiStore = useUiStore();
        const socketStore = useSocketStore();
        const componentStore = useComponentStore();

        if (componentStore.modules.items.length === 0) {
             await componentStore.fetchAllComponents();
             await delay(200);
        }

        if (socketStore.isConnected) {
            await socketStore.sendMessage({
                type: 'load_preset',
                name: presetName,
                owner_id: ownerId
            });
            return true;
        } else {
             uiStore.showConnectEngineDialog();
             return false;
        }
    }

     function updateSinglePresetData(presetName, presetData) {
        if (!presetData) {
             clearCanvas();
             currentPresetName.value = presetName;
             return;
        }
        const componentStore = useComponentStore();
        const newNodes = (presetData.nodes || []).map(node => {
            const component = componentStore.findComponentById(node.module_id);
            const nodeConfig = node.config_values || {};
            return {
                id: node.id || uuidv4(),
                type: 'default',
                label: node.name || component?.name || node.module_id,
                position: { x: node.x || 0, y: node.y || 0 },
                data: {
                    moduleId: node.module_id,
                    componentType: component ? component.componentType : 'modules',
                    config_values: nodeConfig,
                    color: node.data?.color,
                }
            }
        });

        const newConnections = (presetData.connections || []).map(conn => ({
            id: conn.id || `edge-${uuidv4()}`,
            type: conn.type || 'default',
            animated: conn.animated !== undefined ? conn.animated : true,
            source: conn.source || conn.from,
            target: conn.target || conn.to,
            sourceHandle: conn.source_port_name || conn.sourceHandle || null,
            targetHandle: conn.target_port_name || conn.targetHandle || null,
        }));

        executionStatus.value = {};
        connectionStatus.value = {};
        jobId.value = null;
        isExecuting.value = false;
        isPaused.value = false;
        isStopRequested.value = false;
        isModified.value = false;
        elements.value = [...newNodes, ...newConnections];
        if (!permissionLevel.value.startsWith('view')) currentPresetName.value = presetName;

        if (presetData.global_loop_config) globalLoopConfig.value = { ...globalLoopConfig.value, ...presetData.global_loop_config };

        clearSelectedNode();
    }

    async function loadSharedWorkflow(token) {
        error.value = null;
        const uiStore = useUiStore();
        uiStore.showNotification({ text: 'Loading shared workflow...', color: 'info' });
        try {
            const shareDetails = await apiResolveShareToken(token);
            if (shareDetails.error) throw new Error(shareDetails.error);

            const { preset_name: presetName, owner_id: ownerPublicAddress, permission_level: sharedPermission } = shareDetails;

            const loadSuccess = await loadWorkflow(presetName, ownerPublicAddress);

            if (loadSuccess) {
                permissionLevel.value = sharedPermission || 'view';
                currentPresetName.value = `Shared: ${presetName}`;
                uiStore.showNotification({ text: `Shared workflow loaded.`, color: 'success' });
            }
            return loadSuccess;

        } catch (e) {
            error.value = 'Failed to load shared workflow.';
            uiStore.showNotification({ text: error.value, color: 'error'});
            return false;
        }
    }

    function sanitizeForFilename(name) {
        if (!name || typeof name !== 'string') return 'untitled_workflow';
        return name.trim().replace(/[<>:"/\\|?*]/g, '').replace(/\s+/g, '-').substring(0, 50);
    }

    async function saveCurrentWorkflow(newPresetName) {
        const uiStore = useUiStore();
        const socketStore = useSocketStore();
        const authStore = useAuthStore();

        if (!socketStore.isConnected || !authStore.privateKey) return false;

        try {
            const sanitizedName = sanitizeForFilename(newPresetName);
            const workflowData = {
                nodes: nodes.value.map(node => ({
                    id: node.id,
                    name: node.label,
                    x: node.position.x,
                    y: node.position.y,
                    module_id: node.data.moduleId,
                    config_values: node.data.config_values || {},
                    ...(node.data.color && { data: { color: node.data.color } })
                })),
                connections: edges.value.map(edge => ({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    source_port_name: edge.sourceHandle,
                    target_port_name: edge.targetHandle,
                    type: edge.type,
                    animated: edge.animated,
                })),
                 global_loop_config: globalLoopConfig.value
            };

            const wallet = new ethers.Wallet(authStore.privateKey);
            const messageToSign = stableStringify({ "workflow_data": workflowData });
            const signature = await wallet.signMessage(messageToSign);

            await socketStore.sendMessage({
                type: 'save_preset',
                name: sanitizedName,
                workflow_data: workflowData,
                signature
            });

            currentPresetName.value = newPresetName;
            isModified.value = false;
            uiStore.showNotification({ text: `Workflow saved.`, color: 'success' });
            await fetchPresets();
            return true;

        } catch (error) {
            uiStore.showNotification({ text: `Save failed: ${error.message}`, color: 'error' });
            return false;
        }
    }

    async function deletePresetAction(presetName) {
        const uiStore = useUiStore();
        const socketStore = useSocketStore();
        if (!socketStore.isConnected) return false;

        try {
            await socketStore.sendMessage({ type: 'delete_preset', name: presetName });
            if (currentPresetName.value === presetName) clearCanvas();
            uiStore.showNotification({ text: `Preset deleted.`, color: 'info' });
            await fetchPresets();
            return true;
        } catch (error) {
            return false;
        }
    }

    function clearCanvas() {
        elements.value = [];
        selectedNode.value = null;
        currentPresetName.value = null;
        executionStatus.value = {};
        connectionStatus.value = {};
        permissionLevel.value = 'edit';
        jobId.value = null;
        isExecuting.value = false;
        isPaused.value = false;
        isModified.value = false;
    }

    function applyAutoLayout(updatedNodes) {
        if (isReadOnly.value || !Array.isArray(updatedNodes)) return;
        const nodeMap = new Map(updatedNodes.map(n => [n.id, n.position]));
        elements.value = elements.value.map(el => {
            if ('position' in el && nodeMap.has(el.id)) return { ...el, position: nodeMap.get(el.id) };
            return el;
        });
        isModified.value = true;
    }

    async function _startExecutionLoop(startNodeId = null, mode = 'EXECUTE') {
        const uiStore = useUiStore();
        const socketStore = useSocketStore();
        const logStore = useLogStore();

        if (!socketStore.isConnected) return;
        if (isExecuting.value) return;

        isExecuting.value = true;
        isPaused.value = false;
        logStore.clearLogs();
        const newJobId = uuidv4();
        jobId.value = newJobId;

        const payload = {
            type: 'execute_workflow',
            job_id: newJobId,
            preset_name: currentPresetName.value || 'unsaved-workflow',
            workflow_data: getWorkflowForPublishing.value,
            start_node_id: startNodeId,
            mode: mode,
        };

        try {
            await socketStore.sendMessage(payload);
        } catch (error) {
             isExecuting.value = false;
        }
    }

    async function executePresetByName(presetName) {
        const socketStore = useSocketStore();
        if (!socketStore.isConnected || isExecuting.value) return;
        await loadWorkflow(presetName);
        setTimeout(() => { _startExecutionLoop(null, 'EXECUTE'); }, 500);
    }

    function executeCurrentWorkflow(startNodeId = null) { _startExecutionLoop(startNodeId, 'EXECUTE'); }
    function simulateCurrentWorkflow(startNodeId = null) { _startExecutionLoop(startNodeId, 'SIMULATE'); }

    function updateExecutionStatus(data) {
        const statusData = data.status_data || {};
        if (statusData.status === 'RUNNING') {
            isExecuting.value = true;
        } else if (['SUCCEEDED', 'FAILED', 'STOPPED'].includes(statusData.status)) {
            isExecuting.value = false;
            jobId.value = null;
        }
    }

    function updateNodeExecutionStatus(metric) {
        if (!metric?.node_id) return;
        executionStatus.value = {
            ...executionStatus.value,
            [metric.node_id]: { status: metric.status, timestamp: metric.timestamp }
        };
    }

    async function stopCurrentWorkflow() {
        if (!jobId.value) return;
        const socketStore = useSocketStore();
        await socketStore.sendMessage({ type: 'stop_workflow', job_id: jobId.value });
    }

    async function stopJobById(jobIdToStop) {
        const socketStore = useSocketStore();
        await socketStore.sendMessage({ type: 'stop_workflow', job_id: jobIdToStop });
    }

    async function pauseCurrentWorkflow() {
        if (!jobId.value) return;
        const socketStore = useSocketStore();
        await socketStore.sendMessage({ type: 'pause_workflow', job_id: jobId.value });
    }

    async function resumeCurrentWorkflow() {
        if (!jobId.value) return;
        const socketStore = useSocketStore();
        await socketStore.sendMessage({ type: 'resume_workflow', job_id: jobId.value });
    }

    return {
        elements, selectedNode, currentPresetName, isExecuting, jobId, executionStatus, presets, clipboard,
        isPaused, connectionStatus, globalLoopConfig, permissionLevel, error, favoritePresets,
        isModified,
        nodes, edges, isCanvasEmpty, isReadOnly, canExecute, selectedNodeHasBehavior,
        getWorkflowForPublishing,
        fetchPresets, updatePresetsList,
        loadWorkflow, updateSinglePresetData, loadSharedWorkflow,
        saveCurrentWorkflow, deletePresetAction,
        clearCanvas, applyAutoLayout,
        addNode, addEdge, setSelectedNode, clearSelectedNode, updateNodeConfig,
        removeElements, copyNode, pasteNode, duplicateNode, setNodeColor,
        toggleFavorite, fetchUserFavorites,
        fetchConnectionData, updateConnectionStatus,
        executeCurrentWorkflow, simulateCurrentWorkflow, executePresetByName,
        updateExecutionStatus, updateNodeExecutionStatus,
        stopCurrentWorkflow, pauseCurrentWorkflow, resumeCurrentWorkflow, stopJobById,
        applyChanges,
        isLoadingPresets,
        handleFetchError,
        animateIncomingEdges
    };
});
