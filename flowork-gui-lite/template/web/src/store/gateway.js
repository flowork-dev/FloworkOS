//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\gateway.js total lines 215 
//#######################################################################

import { defineStore } from 'pinia';
import { io } from 'socket.io-client';
import { apiClient } from '@/api';
import { useAuthStore } from './auth';
import { useEngineStore } from './engines';
import { useComponentStore } from './components';
import { useLogStore } from './logs';

async function fetchServersConfig() {
	try {
		const response = await fetch('/servers.json');
		if (!response.ok) {
			throw new Error('Failed to load servers.json');
		}
		return await response.json();
	} catch (error) {
		console.warn('servers.json not found, using default gateway URL');
		return { VITE_GATEWAY_URL: import.meta.env.VITE_GATEWAY_URL || 'http://127.0.0.1:5001' };
	}
}

export const useGatewayStore = defineStore('gateway', {
	state: () => ({
		gatewayUrl: '',
		gatewayConnected: false,
		gatewayApiStatus: 'checking',
		socket: null,
		api: null,
		activeEngineId: localStorage.getItem('activeEngineId') || null,
		isInitialized: false,
	}),
	getters: {
		isGatewayConnected: (state) => state.gatewayConnected,
		isApiHealthy: (state) => state.gatewayApiStatus === 'healthy',
		apiClient: (state) => state.api,
		activeEngine: (state) => {
			const enginesStore = useEngineStore();
			return enginesStore.engines.find((e) => e.engine_id === state.activeEngineId);
		},
	},
	actions: {
		async initialize({ commit, dispatch, state }) {
			if (state.isInitialized) return;

			console.log('Initializing Gateway store...');

			const config = await fetchServersConfig();
			const gatewayUrl = config.VITE_GATEWAY_URL;
			commit('SET_GATEWAY_URL', gatewayUrl);

			const authStore = useAuthStore();
			const api = apiClient;
			commit('SET_API_CLIENT', api);

			dispatch('initializeWebSocket');
			dispatch('checkGatewayStatus');
			setInterval(() => dispatch('checkGatewayStatus'), 30000);

			commit('SET_INITIALIZED', true);
			console.log('Gateway store initialized.');
		},

		initializeWebSocket({ commit, dispatch, state, rootState }) {
			const authStore = useAuthStore();
			const enginesStore = useEngineStore();
			const componentsStore = useComponentStore();
			const logsStore = useLogStore();

			if (state.socket) {
				state.socket.disconnect();
			}

			console.log(`Connecting Socket.IO to ${state.gatewayUrl}`);
			const socket = io(state.gatewayUrl, {
				transports: ['websocket'],
				reconnectionAttempts: 5,
				reconnectionDelay: 1000,
			});

			socket.on('connect', () => {
				console.log('Socket.IO connected to Gateway.');
				commit('SET_GATEWAY_CONNECTED', true);

				const token = authStore.token;
				if (token) {
					socket.emit('authenticate', { token });
					console.log('Socket: Emitted authentication request.');
				}

				if (state.activeEngineId) {
					console.log(`Socket: Requesting status for active engine ${state.activeEngineId}`);
					socket.emit('request_engine_status', { engine_id: state.activeEngineId });
				}
			});

			socket.on('disconnect', (reason) => {
				console.log(`Socket.IO disconnected: ${reason}`);
				commit('SET_GATEWAY_CONNECTED', false);
				const enginesStore = useEngineStore();
				enginesStore.SET_ENGINE_STATUS('offline');
			});

			socket.on('connect_error', (error) => {
				console.error('Socket.IO connection error:', error.message);
				commit('SET_GATEWAY_CONNECTED', false);
			});

			socket.on('engine_status_updated', (data) => {
				dispatch('handleEngineStatusUpdate', data);
			});

			socket.on('log_message', (data) => {
				logsStore.addLog(data);
			});

			socket.on('execution_update', (data) => {
				console.log('Execution update:', data);
			});

			socket.on('node_status_update', (data) => {
				console.log('Node status update:', data);
			});

			commit('SET_SOCKET', socket);
		},

		handleEngineStatusUpdate({ commit, dispatch, rootGetters, rootState }, data) {
			console.log('Socket: Received engine_status_updated', data);
			let activeEngineId = rootState.gateway.activeEngineId;
			const enginesStore = useEngineStore();
			const componentsStore = useComponentStore();

			enginesStore.updateEngineInList(data);

			if (!activeEngineId && data.status === 'online') {
				console.log(`Socket: No active engine. Auto-activating ${data.engine_id}`);
				dispatch('setActiveEngine', data.engine_id);
				activeEngineId = data.engine_id;
			}

			if (data.engine_id === activeEngineId) {
				enginesStore.SET_ENGINE_STATUS(data.status);

				if (data.status === 'online') {
					console.log(`Socket: Active engine ${activeEngineId} is online. Fetching components.`);
					componentsStore.fetchComponents();
				} else {
					console.log(`Socket: Active engine ${activeEngineId} went offline. Loading examples.`);
					componentsStore.loadExampleComponents();
				}
			}
		},

		async checkGatewayStatus({ commit, state }) {
			if (!state.api) return;
			try {
				const response = await state.api.get('/health');
				if (response.status === 200 && response.data.status === 'healthy') {
					commit('SET_API_STATUS', 'healthy');
				} else {
					commit('SET_API_STATUS', 'unhealthy');
				}
			} catch (error) {
				console.error('Gateway API health check failed:', error);
				commit('SET_API_STATUS', 'unhealthy');
				commit('SET_GATEWAY_CONNECTED', false);
			}
		},

		async setActiveEngine({ commit, dispatch, state, rootState }, engineId) {
			const enginesStore = useEngineStore();

			commit('SET_ACTIVE_ENGINE', engineId);
			localStorage.setItem('activeEngineId', engineId);

			if (state.socket && state.socket.connected) {
				state.socket.emit('request_engine_status', { engine_id: engineId });
			}

			await enginesStore.checkEngineStatus(engineId);

			console.log('setActiveEngine: Re-initializing components for new engine.');
			const componentsStore = useComponentStore();
			await componentsStore.initializeComponents();
		},

		SET_GATEWAY_URL(state, url) {
			state.gatewayUrl = url;
		},
		SET_API_CLIENT(state, api) {
			state.api = api;
		},
		SET_SOCKET(state, socket) {
			state.socket = socket;
		},
		SET_GATEWAY_CONNECTED(state, status) {
			state.gatewayConnected = status;
		},
		SET_API_STATUS(state, status) {
			state.gatewayApiStatus = status;
		},
		SET_ACTIVE_ENGINE(state, engineId) {
			state.activeEngineId = engineId;
		},
		SET_INITIALIZED(state, status) {
			state.isInitialized = status;
		},
	},
});
