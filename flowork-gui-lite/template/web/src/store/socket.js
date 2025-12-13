//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\socket.js total lines 410 
//#######################################################################

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { io } from 'socket.io-client';
import { useAuthStore } from './auth';
import { useUiStore } from './ui';
import { useLogStore } from './logs';
import { useWorkflowStore } from './workflow';
import { useVariablesStore } from './variables';
import { useSettingsStore } from './settings';
import { ethers } from 'ethers';

const CURRENT_PAYLOAD_VERSION = 2;

const getGatewayUrl = () => {
    let url = (import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000').replace(/\/$/, '');
    console.log(`[SocketStore] Using Gateway URL: ${url}`);
    return url;
};

const _getAuthHeaders = async () => {
    const authStore = useAuthStore();
    if (!authStore.privateKey || !authStore.user?.id) {
         throw new Error("User not authenticated");
    }
    try {
        const wallet = new ethers.Wallet(authStore.privateKey);
        const timestamp = Math.floor(Date.now() / 1000);
        const messageToSign = `flowork_socket_auth|${wallet.address}|${timestamp}`;
        const signature = await wallet.signMessage(messageToSign);
        return {
            'X-User-Address': wallet.address,
            'X-Signed-Message': messageToSign,
            'X-Signature': signature,
            'X-Payload-Version': CURRENT_PAYLOAD_VERSION
        };
    } catch (error) {
        console.error('[SocketStore] Failed to generate auth headers:', error);
        throw error;
    }
};

export const useSocketStore = defineStore('socket', () => {
    const socket = ref(null);
    const isConnecting = ref(false);
    const connectionError = ref(null);
    const resolvedGatewayUrl = ref(null);
    const isGracePeriod = ref(true);

    const currentEngineStatus = ref({
        isBusy: false,
        cpuPercent: null,
        memoryPercent: null
    });
    const isConnected = computed(() => socket.value?.connected || false);

    const isDevEngine = computed(() => true);

    async function connect() {
        if (socket.value?.connected) {
            console.log("[SocketStore] Already connected. Skipping.");
            return;
        }
        if (isConnecting.value) {
             console.log("[SocketStore] Connection already in progress.");
             return;
        }

        const authStore = useAuthStore();

        if (!authStore.isAuthenticated) {
            console.warn("[SocketStore] Connection attempt aborted: User not authenticated.");
            isGracePeriod.value = false;
            return;
        }

        isConnecting.value = true;
        isGracePeriod.value = true;

        setTimeout(() => {
            if (!isConnected.value) {
                isGracePeriod.value = false;
            }
        }, 3000);

        connectionError.value = null;

        const gatewayUrl = getGatewayUrl();
        resolvedGatewayUrl.value = gatewayUrl;

        let authHeaders;
        try {
            authHeaders = await _getAuthHeaders();
        } catch (error) {
            connectionError.value = `Auth Failed: ${error.message}`;
            isConnecting.value = false;
            isGracePeriod.value = false;
            authStore.logout();
            return;
        }

        const socketPath = "/api/socket.io";
        const socketNamespace = "/gui-socket";
        const socketUrl = gatewayUrl + socketNamespace;
        console.log(`[SocketStore] Connecting directly to namespace: ${socketUrl}`);

        let targetEngineId = localStorage.getItem('flowork_selected_engine_id') || 'local-engine-default';

        const queryParams = {
            engine_id: targetEngineId
        };

        try {
            const newSocket = io(socketUrl, {
                path: socketPath,
                transports: ['websocket'],
                autoConnect: false,
                reconnection: true,
                reconnectionAttempts: Infinity,
                reconnectionDelay: 500,
                reconnectionDelayMax: 2000,
                timeout: 60000,
                ackTimeout: 60000,
                auth: { headers: authHeaders },
                query: queryParams
            });

            socket.value = newSocket;
            await registerEventHandlers();
            console.log("[SocketStore] Listeners attached. Initiating connection...");
            socket.value.connect();

        } catch (error) {
            console.error("[SocketStore] Failed to initialize socket.io client:", error);
            connectionError.value = `Connection Init Failed: ${error.message}`;
            isConnecting.value = false;
            isGracePeriod.value = false;
        }
    }

    function disconnect() {
        if (socket.value) {
            console.log("[SocketStore] Disconnecting socket...");
            socket.value.disconnect();
            socket.value = null;
        }
        isConnecting.value = false;
        connectionError.value = null;
        resolvedGatewayUrl.value = null;
        currentEngineStatus.value = { isBusy: false, cpuPercent: null, memoryPercent: null };
        isGracePeriod.value = false;
    }

    async function sendMessage(payload) {
        if (!isConnected.value || !socket.value) {
            console.error("[SocketStore] Cannot send message: Socket not connected.", payload);
            throw new Error("Socket not connected");
        }

        const eventName = payload.type;
        if (!eventName) {
            console.error("[SocketStore] Payload has no 'type' (event name).", payload);
            return;
        }

        if (!payload.target_engine_id) {
            payload.target_engine_id = localStorage.getItem('flowork_selected_engine_id') || 'local-engine-default';
        }

        const versionedPayload = {
            v: CURRENT_PAYLOAD_VERSION,
            payload: { ...payload }
        };

        try {
            console.log(`[SocketStore] Sending Event '${eventName}'`, versionedPayload);
            socket.value.emit(eventName, versionedPayload);
        } catch (error) {
            console.error(`[SocketStore] Error emitting socket event '${eventName}':`, error);
        }
    }

    function switchEngine(newEngineId) {
        console.log(`[SocketStore] Switching engine ID (Local Reconnect): ${newEngineId}`);
        if (isConnected.value || socket.value) {
            socket.value.disconnect();
            socket.value = null;
        }
        localStorage.setItem('flowork_selected_engine_id', newEngineId);
        setTimeout(() => { connect(); }, 100);
    }

    async function registerEventHandlers() {
        if (!socket.value) return;

        const uiStore = useUiStore();
        const logStore = useLogStore();
        const workflowStore = useWorkflowStore();
        const variableStore = useVariablesStore();
        const settingsStore = useSettingsStore();

        let componentStore = null;
        try {
            const { useComponentStore } = await import('./components');
            componentStore = useComponentStore();
        } catch (e) {
            console.error("[SocketStore] Critical: Failed to dynamically load ComponentStore.", e);
        }

        socket.value.on('connect', () => {
            isConnecting.value = false;
            isGracePeriod.value = false;
            connectionError.value = null;
            console.log(`[SocketStore] Connected. SID: ${socket.value.id}`);
            uiStore.showNotification({ text: `Connected to Local Engine`, color: 'success', timeout: 2000 });

            console.log("[SocketStore] Hydrating Core Data...");
            settingsStore.fetchSettings();
            workflowStore.fetchPresets();
            variableStore.fetchVariables();

            if (componentStore) {
                try {
                    componentStore.forceRefetchAllComponents();
                } catch(e) {
                    console.warn("[SocketStore] ComponentStore refetch failed (maybe not ready):", e);
                }
            }

            workflowStore.fetchUserFavorites();
            if (componentStore) componentStore.fetchUserFavorites();
        });

        socket.value.on('connect_error', (error) => {
            console.error('[SocketStore] Connection Error:', error.message);
            if (!isGracePeriod.value) connectionError.value = `Connection Failed: ${error.message}`;
            isConnecting.value = false;
        });

        socket.value.on('disconnect', (reason) => {
            console.warn(`[SocketStore] Disconnected: ${reason}`);
        });

        socket.value.on('error', (data) => {
            const message = data?.payload?.message || data?.message || "Unknown error";
            console.error('[SocketStore] Gateway Error:', message);
            if (!message.includes("Engine local-engine-default is not connected")) {
                uiStore.showNotification({ text: `Error: ${message}`, color: 'error' });
            }
        });

        socket.value.on('engine_status_update', (data) => {
            if (data.vitals) {
                currentEngineStatus.value.isBusy = data.vitals.is_busy || false;
                currentEngineStatus.value.cpuPercent = data.vitals.cpu_percent || null;
                currentEngineStatus.value.memoryPercent = data.vitals.memory_percent || null;
            }
        });

        socket.value.on('engine_vitals_update', (data) => {
            if (data.vitals) {
                currentEngineStatus.value.isBusy = data.vitals?.is_busy || false;
                currentEngineStatus.value.cpuPercent = data.vitals?.cpu_percent || null;
                currentEngineStatus.value.memoryPercent = data.vitals?.memory_percent || null;
            }
            if (data.engine_id) {
                const currentId = localStorage.getItem('flowork_selected_engine_id');
                if (!currentId || currentId === 'local-engine-default') {
                    console.log(`[SocketStore] Auto-detect: Switching from default to active engine: ${data.engine_id}`);
                    switchEngine(data.engine_id);
                }
            }
        });

        socket.value.on('response_presets_list', (data) => {
            const payload = data.payload || data;
            if (!payload.error) workflowStore.updatePresetsList(payload.presets, payload.favorites);
        });

        socket.value.on('response_load_preset', (data) => {
            const payload = data.payload || data;
            if (payload.error) {
                uiStore.showNotification({ text: `Error loading '${payload.name}': ${payload.error}`, color: 'error' });
                workflowStore.handleFetchError(payload.error);
            } else {
                workflowStore.updateSinglePresetData(payload.name, payload.workflow_data);
            }
        });

        socket.value.on('response_variables', (data) => {
            const payload = data.payload || data;
            if (!payload.error) {
                variableStore.variables = payload.variables;
                variableStore.isLoading = false;
            }
        });

        socket.value.on('response_component_list', (data) => {
            const payload = data.payload || data;
            if (!payload.error && componentStore) componentStore.updateComponentsList(payload.component_type, payload.components);
        });

        socket.value.on('settings_response', (data) => {
            const payload = data.payload || data;
            if (!payload.error) {
                settingsStore.settings = payload.settings;
                uiStore.loadUiPreferences(payload.settings);
            }
            settingsStore.isLoading = false;
        });


        socket.value.on('component_install_status', (data) => {
            const payload = data.payload || data;
            if (componentStore) componentStore.handleInstallStatusUpdate(payload);
        });

        socket.value.on('WORKFLOW_EXECUTION_UPDATE', (data) => {
            const payload = data.payload || data;
            workflowStore.updateExecutionStatus(payload);
        });

        socket.value.on('NODE_METRIC_UPDATE', (data) => {
            const payload = data.payload || data;
            workflowStore.updateNodeExecutionStatus(payload.metric);
            logStore.updateTimelineEntry(payload.metric);
        });

        socket.value.on('CONNECTION_UPDATE', (data) => {
            const payload = data.payload || data;
            workflowStore.updateConnectionStatus(payload);
        });

        socket.value.on('WORKFLOW_LOG_ENTRY', (data) => {
            const payload = data.payload || data;
            logStore.addExecutionLog(payload);

            if (payload.node_id) {
                let status = 'RUNNING';
                const lvl = (payload.level || '').toUpperCase();
                const msg = (payload.message || '').toUpperCase();

                if (lvl.includes('SUCCESS') || msg.includes('COMPLETE')) status = 'SUCCESS';
                else if (lvl.includes('ERROR') || lvl.includes('FAIL')) status = 'FAILED';
                else if (lvl.includes('INFO') || lvl.includes('DEBUG')) status = 'RUNNING';

                workflowStore.updateNodeExecutionStatus({
                    node_id: payload.node_id,
                    status: status,
                    timestamp: payload.ts ? new Date(payload.ts).getTime() / 1000 : Date.now() / 1000,
                    workflow_context_id: payload.job_id
                });

                if (status === 'RUNNING') {
                    workflowStore.animateIncomingEdges(payload.node_id);
                }

                logStore.updateTimelineEntry({
                    node_id: payload.node_id,
                    module_id: payload.source,
                    status: status,
                    timestamp: payload.ts ? new Date(payload.ts).getTime() / 1000 : Date.now() / 1000,
                    execution_time_ms: null
                });
            }
        });

        socket.value.on('SHOW_DEBUG_POPUP', (data) => {
            const payload = data.payload || data;
            uiStore.showDataViewer(payload);
        });

        socket.value.on('CONNECTION_DATA_RESPONSE', (data) => {
            const payload = data.payload || data;
            if (payload.error) {
                uiStore.showDataViewer({ title: `Data Error`, error: `No data found.`, content: payload.error });
            } else {
                uiStore.showDataViewer({
                    title: `Data History (Job: ${payload.job_id?.substring(0,8)})`,
                    payload: payload.history
                });
            }
        });

        socket.value.on('FILESYSTEM_LIST_RESPONSE', (data) => {
            const payload = data.payload || data;
            window.dispatchEvent(new CustomEvent('FILESYSTEM_DATA_READY', { detail: payload }));
        });
    }

    return {
        socket,
        isConnected,
        isConnecting,
        connectionError,
        resolvedGatewayUrl,
        currentEngineStatus,
        isDevEngine,
        isGracePeriod,
        connect,
        disconnect,
        sendMessage,
        switchEngine
    };
});
