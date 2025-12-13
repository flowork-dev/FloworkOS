//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\api\index.js total lines 888 
//#######################################################################

import axios from 'axios';
import { useAuthStore } from '@/store/auth';
import { ethers } from 'ethers';

const CURRENT_PAYLOAD_VERSION = 2;
const DEFAULT_API_TIMEOUT = 60000;

const getContentBaseUrl = () => {
    const url = '/api/v1';
    return url;
};

const apiClient = axios.create({
    baseURL: '/',
    timeout: DEFAULT_API_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    }
});

const contentApiClient = axios.create({
    baseURL: getContentBaseUrl(),
    timeout: DEFAULT_API_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    }
});

export const getGatewayUrl = () => {
    try {
        const storedState = localStorage.getItem('flowork_gateway');
        if (storedState) {
            const parsed = JSON.parse(storedState);
            let url = parsed.gatewayUrl || 'https://api.flowork.cloud';
            return url.replace(/\/$/, "");
        }
    } catch (e) {
    }

    const hostname = window.location.hostname;
    if (!hostname.includes('flowork.cloud') && !hostname.includes('www.flowork.cloud')) {
         return window.location.origin;
    }

    return 'https://api.flowork.cloud';
};

/**
 * [ADDED BY FLOWORK HYBRID SYSTEM]
 * Automatically generates a local "Burner Identity" if running on localhost and no auth exists.
 * This solves the 401 Loop on GUI Lite/Hybrid mode without needing a tunnel token.
 */
const ensureLocalHybridIdentity = () => {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');

    if (isLocal) {
        const existingAuth = localStorage.getItem('wallet_auth');
        if (!existingAuth) {
            console.log("[Hybrid Mode] No identity found for Local GUI. Auto-generating Burner Identity...");
            try {
                const randomWallet = ethers.Wallet.createRandom();
                const authData = {
                    address: randomWallet.address,
                    privateKey: randomWallet.privateKey,
                    mnemonic: randomWallet.mnemonic.phrase
                };
                localStorage.setItem('wallet_auth', JSON.stringify(authData));

                console.log(`[Hybrid Mode] Identity generated: ${authData.address}`);
                return authData.privateKey;
            } catch (e) {
                console.error("[Hybrid Mode] Failed to generate local identity:", e);
            }
        }
    }
    return null;
};

/**
 * [MODIFIED BY AWENK]
 * Generate Auth Headers (Bearer + Web3 Signature + Gateway Token).
 * [FIXED] Removed hardcoded Content-Type: application/json to allow multipart uploads
 */
export const getAuthHeaders = async (fullUrl, method = 'GET') => {
    const headers = {};

    ensureLocalHybridIdentity();

    const authStore = useAuthStore();

    let token = authStore.token || localStorage.getItem('flowork_gateway_token') || localStorage.getItem('token');

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        headers['x-gateway-token'] = token;
    }

    let privateKey = authStore.privateKey;
    if (!privateKey) {
        try {
            const localAuth = localStorage.getItem('wallet_auth');
            if (localAuth) {
                const parsed = JSON.parse(localAuth);
                if (parsed.privateKey) privateKey = parsed.privateKey;
            }
        } catch (e) {
            console.warn("[API] Failed to recover auth from storage", e);
        }
    }

    if (privateKey) {
        try {
            const wallet = new ethers.Wallet(privateKey);
            let relativeUrl = fullUrl;

            const gatewayUrl = getGatewayUrl();
            if (relativeUrl.startsWith(gatewayUrl)) {
                 relativeUrl = relativeUrl.substring(gatewayUrl.length);
            }
            if (relativeUrl.startsWith('//')) relativeUrl = relativeUrl.substring(1);

            if (relativeUrl.startsWith('/api/v1')) {
                relativeUrl = relativeUrl.substring(7); // remove /api/v1
            }

            if (!relativeUrl.startsWith('/')) {
                relativeUrl = '/' + relativeUrl;
            }

            const timestamp = Math.floor(Date.now() / 1000);

            const messageToSign = `flowork_api_auth|${wallet.address}|${timestamp}`;
            const signature = await wallet.signMessage(messageToSign);

            headers['X-User-Address'] = wallet.address;
            headers['X-Signature'] = signature;
            headers['X-Signed-Message'] = messageToSign;
            headers['X-Payload-Version'] = CURRENT_PAYLOAD_VERSION;
        } catch (e) {
            console.error("[API] Failed to sign request:", e);
        }
    }

    const activeEngineId = localStorage.getItem('flowork_active_engine_id');
    if (activeEngineId) {
        headers['X-Flowork-Engine-ID'] = activeEngineId;
    }

    return headers;
};

const dynamicUrlInterceptor = (config) => {
    const currentGatewayUrl = getGatewayUrl();
    const newBaseUrl = `${currentGatewayUrl}/api/v1`;

    if (config.url.startsWith('/api/v1')) {
        config.baseURL = currentGatewayUrl;
    } else {
        config.baseURL = newBaseUrl;
    }

    return config;
};

const cryptoInterceptor = async config => {
    const baseURL = config.baseURL || '';
    let fullUrl = config.url;
    if (!fullUrl.startsWith('http')) {
        fullUrl = baseURL + (config.url.startsWith('/') ? config.url : '/' + config.url);
    }

    const authHeaders = await getAuthHeaders(fullUrl, config.method);

    config.headers = {
        ...config.headers,
        ...authHeaders
    };

    return config;
};

apiClient.interceptors.request.use(dynamicUrlInterceptor, error => Promise.reject(error));
apiClient.interceptors.request.use(cryptoInterceptor, error => Promise.reject(error));
contentApiClient.interceptors.request.use(cryptoInterceptor, error => Promise.reject(error));

function handleApiError(error, context) {
    console.error(`[API Error] ${context}:`, error);

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.warn(`[API Error] Request timed out for ${context}. Gateway might be overloaded or offline.`);
        return { error: 'Connection timed out. Is the Engine running?' };
    }

    if (error.response) {
        if (error.response.status === 401) {
            const authStore = useAuthStore();
            console.warn(`[API Error] Received 401 Unauthorized for ${context}. Logging out.`);

            const hostname = window.location.hostname;
            if (!hostname.includes('localhost') && !hostname.includes('127.0.0.1')) {
                 authStore.handleLogoutError();
            } else {
                 console.log("[Hybrid Mode] 401 ignored locally. Retrying with identity logic next time.");
            }
        }
        if (error.response.status === 404) {
            console.warn(`[API Error] 404 Not Found for ${context}. URL may be incorrect.`);
            return error.response.data || { error: `HTTP Error 404: Not Found` };
        }
        return error.response.data || { error: `HTTP Error ${error.response.status}` };
    } else if (error.request) {
        return { error: 'Network Error: Could not connect to API. Check your Gateway URL.' };
    } else {
        return { error: `Request Setup Error: ${error.message}` };
    }
}


export async function apiSetUserUiPreferences(preferences) {
  try {
    const gateway = getGatewayUrl();
    const url = `${gateway}/api/v1/user/preferences`;

    const headers = await getAuthHeaders(url, 'PATCH');
    headers['Content-Type'] = 'application/json';

    const response = await fetch(url, {
      method: 'PATCH',
      headers: headers,
      body: JSON.stringify(preferences)
    });
    return await response.json();
  } catch (error) {
    console.error("[API] Failed to save UI preferences:", error);
    return { error: error.message };
  }
}

export const apiDownloadLicenseFile = async () => {
    try {
        const response = await apiClient.get('/user/license');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiDownloadLicenseFile');
    }
};

export const apiLogin = async (email, password) => Promise.resolve({ error: "Login is handled locally via Private Key." });
export const apiRegister = async (username, email, password) => Promise.resolve({ error: "Identity creation is handled locally." });

export const apiGetProfile = async () => {
    return Promise.resolve({ error: "apiGetProfile is deprecated" });
};

export const apiGetUserFavorites = async () => {
    try {
        const response = await apiClient.get('/user/state/favorite_presets');
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetUserFavorites');
    }
};

export const apiSetUserFavorites = async (favoriteIds) => {
    try {
        const response = await apiClient.put('/user/state/favorite_presets', favoriteIds);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiSetUserFavorites');
    }
};


export const apiGetUserComponentFavorites = async () => {
    try {
        const response = await apiClient.get('/user/state/favorite_components');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetUserComponentFavorites');
    }
};

export const apiSetUserComponentFavorites = async (favoriteComponentIds) => {
    try {
        const response = await apiClient.put('/user/state/favorite_components', favoriteComponentIds);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiSetUserComponentFavorites');
    }
};

export const apiFetchEngines = async () => {
    try {
        const response = await apiClient.get('/user/engines');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiFetchEngines');
    }
};


export const apiRegisterEngine = async (data) => {
    try {
        const response = await apiClient.post('/user/engines', data);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiRegisterEngine');
    }
};


export const apiResetEngineToken = async (engineId) => {
    try {
        const response = await apiClient.post(`/user/engines/${engineId}/reset-token`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiResetEngineToken');
    }
};


export const apiDeleteEngine = async (engineId) => {
    try {
        const response = await apiClient.delete(`/user/engines/${engineId}`);
        if (response.status === 204 || (response.status === 200 && response.data?.message)) {
            return { message: response.data?.message || 'Engine deleted' };
        } else {
            throw new Error(response.data?.error || `Failed with status ${response.status}`);
        }
    } catch (error) {
        return handleApiError(error, 'apiDeleteEngine');
    }
};


export const apiUpdateEngine = async (engineId, data) => {
    try {
        const response = await apiClient.put(`/user/engines/${engineId}/update-name`, data);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiUpdateEngine');
    }
};


export const apiFetchSharedEngines = async () => {
    try {
        const response = await apiClient.get('/user/shared-engines');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiFetchSharedEngines');
    }
};


export const apiFetchEngineShares = async (engineId) => {
    try {
        const response = await apiClient.get(`/user/engines/${engineId}/shares`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiFetchEngineShares');
    }
};

export const apiGrantShare = async (engineId, shareWithIdentifier, role = 'reader') => {
     try {
        const payload = {
            user_id: shareWithIdentifier,
            role: role
        };
        const response = await apiClient.post(`/user/engines/${engineId}/share`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGrantShare');
    }
};


export const apiRevokeShare = async (engineId, sharedUserId) => {
     try {
        const response = await apiClient.delete(`/user/engines/${engineId}/shares/${sharedUserId}`);

        if (response.status >= 200 && response.status < 300) {
            return { message: response.data?.message || 'Share revoked successfully.' };
        } else {
             throw new Error(response.data?.error || `Failed with status ${response.status}`);
        }
    } catch (error) {
        try {
             const response = await apiClient.post(`/user/engines/${engineId}/shares/delete`, { share_id: sharedUserId });
             return response.data;
        } catch(e) {
             return handleApiError(error, 'apiRevokeShare');
        }
    }
};

export const apiGetWorkflowShares = async (workflowName) => {
    try {
        const response = await apiClient.get(`/workflows/${workflowName}/shares`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetWorkflowShares');
    }
};

export const apiCreateShareLink = async (workflowName, permissionLevel, linkName) => {
    try {
        const payload = { permission_level: permissionLevel, link_name: linkName };
        const response = await apiClient.post(`/workflows/${workflowName}/shares`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiCreateShareLink');
    }
};

export const apiUpdateSharePermission = async (shareId, newPermission) => {
    try {
        const payload = { permission_level: newPermission };
        const response = await apiClient.put(`/workflow-shares/${shareId}`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiUpdateSharePermission');
    }
};

export const apiDeleteShare = async (shareId) => {
    try {
        const response = await apiClient.delete(`/workflow-shares/${shareId}`);
        if (response.status === 204 || (response.status === 200 && response.data.status === 'success')) {
             return { message: 'Share link deleted successfully.' };
        } else {
             throw new Error(response.data?.error || `Failed with status ${response.status}`);
        }
    } catch (error) {
        return handleApiError(error, 'apiDeleteShare');
    }
};

export const apiResolveShareToken = async (shareToken) => {
    try {
        const response = await apiClient.get(`/workflow-shares/resolve/${shareToken}`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiResolveShareToken');
    }
};
export const apiGetMyArticles = async () => {
    try {
        const response = await contentApiClient.get('/content/my-articles');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetMyArticles');
    }
};

export const apiCreateArticle = async (articleData) => {
    try {
        const response = await contentApiClient.post('/content/articles', articleData);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiCreateArticle');
    }
};

export const apiGetArticleForEdit = async (articleId) => {
    try {
        const response = await contentApiClient.get(`/content/articles/${articleId}/edit`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetArticleForEdit');
    }
};

export const apiUpdateArticle = async (articleId, articleData) => {
    try {
        const response = await contentApiClient.put(`/content/articles/${articleId}`, articleData);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiUpdateArticle');
    }
};

export const apiDeleteArticle = async (articleId) => {
    try {
        const response = await contentApiClient.delete(`/content/articles/${articleId}`);
        if (response.status === 204 || (response.data && (response.data.status === 'deleted' || response.data.message))) {
            return { message: 'Article deleted successfully.' };
        } else if (response.data.error) {
            throw new Error(response.data.error);
        } else {
             throw new Error(`Failed with status ${response.status}`);
        }
    } catch (error) {
        return handleApiError(error, 'apiDeleteArticle');
    }
};

export const apiGetPublicArticle = async (slug, lang) => {
    try {
        const publicContentClient = axios.create({ baseURL: getContentBaseUrl() });
        const response = await publicContentClient.get(`/content/articles/public/${slug}/${lang}`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetPublicArticle');
    }
};

export const apiGetComments = async (slug) => {
    try {
        const publicContentClient = axios.create({ baseURL: getContentBaseUrl() });
        const response = await publicContentClient.get(`/content/articles/${slug}/comments`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetArticleComments');
    }
};

export const apiPostComment = async (slug, content, parentId = null, captchaAnswer = null) => {
    try {
        const payload = { content, parent_id: parentId, captchaAnswer };
        const response = await contentApiClient.post(`/content/articles/${slug}/comments`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiPostComment');
    }
};

export const apiVoteComment = async (commentId, voteType) => {
    try {
        const payload = { vote_type: voteType };
        const response = await contentApiClient.post(`/content/comments/${commentId}/vote`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiVoteComment');
    }
};

export const apiFlagComment = async (commentId) => {
    try {
        const response = await contentApiClient.post(`/content/comments/${commentId}/flag`, {});
        if (response.data.error) {
            if (error.response?.status === 409) {
                return { status: 409, message: response.data.message, error: response.data.error };
            }
            throw new Error(response.data.error);
        }
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiFlagComment');
    }
};

export const apiUpdateComment = async (commentId, content) => {
    try {
        const payload = { content: content };
        const response = await contentApiClient.put(`/content/comments/${commentId}`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiUpdateComment');
    }
};

export const apiDeleteComment = async (commentId) => {
    try {
        const response = await contentApiClient.delete(`/content/comments/${commentId}`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiDeleteComment');
    }
};

export const apiGetCloudProfile = async () => {
    try {
        const response = await contentApiClient.get('/users/me');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
         return handleApiError(error, 'apiGetCloudProfile');
    }
};

export const apiUpdateCloudProfile = async (profileData) => {
    try {
        const response = await contentApiClient.put('/users/me', profileData);
       if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiUpdateCloudProfile');
    }
};

export const apiGetMarketplaceItems = async (filters = {}) => {
    try {
        const response = await contentApiClient.get('/marketplace/list', { params: filters });
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetMarketplaceItems');
    }
};

export const apiGetMarketplaceItemDetail = async (id) => {
    try {
        const response = await contentApiClient.get(`/marketplace/${id}`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetMarketplaceItemDetail');
    }
};

export const apiPublishMarketplaceItem = async (itemData) => {
    try {
        const response = await contentApiClient.post('/marketplace/publish', itemData);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiPublishMarketplaceItem');
    }
};

export const apiDeleteMarketplaceItem = async (id) => {
    try {
        const response = await contentApiClient.post('/marketplace/delete', { id });
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiDeleteMarketplaceItem');
    }
};

export const apiVoteMarketplaceItem = async (itemId, voteType) => {
    try {
        const payload = { itemId, voteType };
        const response = await contentApiClient.post('/marketplace/vote', payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiVoteMarketplaceItem');
    }
};

export const apiGetPublicProfile = async (identifier) => {
    try {
       const response = await apiClient.get(`/user/public/${identifier}`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetPublicProfile');
    }
};


export const apiFetchNews = async () => {
    try {
        return Promise.resolve([]);
    } catch (error) {
        return handleApiError(error, 'apiFetchNews');
    }
};

export const apiGetDashboardSummary = async () => {
    try {
        const response = await apiClient.get('/dashboard/summary');
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetDashboardSummary');
    }
};

export const apiSelectEngineForAuth = async (requestId, engineId) => {
    try {
        const response = await apiClient.post('/user/engines/select-for-auth', {
            request_id: requestId,
            engine_id: engineId
        }
        );
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiSelectEngineForAuth');
    }
};

export const getLocalizationDictionary = async (lang = 'en') => { // Default to 'en'
     try {
        return Promise.resolve({});
    } catch (error) {
        return handleApiError(error, 'getLocalizationDictionary');
    }
};

export const getComponentIconUrl = (componentType, componentId) => {
    const currentGatewayUrl = getGatewayUrl() || window.location.origin;
    const baseUrl = `${currentGatewayUrl}/api/v1`;
    return `${baseUrl}/components/${componentType}/${componentId}/icon`;
};


const wsOnlyError = (context = '') => {
    const message = `Functionality moved to local engine WebSocket connection. (${context})`;
    console.warn(`[API Stub] ${message}`);
    return Promise.resolve({ error: message });
};
export { wsOnlyError };

export const apiStartSession = async (engine_id, intent, episode_id = null) => {
    try {
        const payload = { engine_id, intent };
        if (episode_id) {
            payload.episode_id = episode_id;
        }
        const response = await apiClient.post('/sessions', payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiStartSession');
    }
};

export const apiCancelSession = async (session_id) => {
    try {
        const response = await apiClient.post(`/sessions/${session_id}/cancel`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiCancelSession');
    }
};

export const apiGetEpisodes = async (engine_id) => {
    try {
        const response = await apiClient.get('/episodes', { params: { engine_id } });
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetEpisodes');
    }
};

export const apiCreateEpisode = async (engine_id, title = "New Chat") => {
    try {
        const response = await apiClient.post('/episodes', { engine_id, title });
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiCreateEpisode');
    }
};

export const apiShareEngine = async (engine_id, user_id, role = 'reader') => {
    try {
        const payload = { user_id, role };
        const response = await apiClient.post(`/user/engines/${engine_id}/share`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiShareEngine');
    }
};

export const apiListCapsules = async () => {
    try {
        const response = await contentApiClient.get('/marketplace/list', { params: { type: 'capsule' } });

        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiListCapsules');
    }
};

export const apiGetCapsule = async (capsuleId) => {
    try {
        const response = await apiClient.get(`/capsules/${capsuleId}`);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiGetCapsule');
    }
};

export const apiInstallCapsule = async (capsulePayload) => {
    try {
        const response = await apiClient.post('/capsules', capsulePayload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiInstallCapsule');
    }
};

export const apiRemixCapsule = async (baseCapsuleId, newCapsuleId, patch) => {
    try {
        const payload = { new_capsule_id: newCapsuleId, patch: patch };
        const response = await apiClient.post(`/capsules/${baseCapsuleId}/remix`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiRemixCapsule');
    }
};

export const apiPreviewCapsuleFac = async (capsuleId, user, engine) => {
    try {
        const payload = { user, engine };
        const response = await apiClient.post(`/capsules/${capsuleId}/fac-preview`, payload);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiPreviewCapsuleFac');
    }
};

/**
 * [ADDED BY FLOWORK DEV]
 * Mengirim input langsung ke Component/Node spesifik di Engine.
 * [FIXED] Updated to match backend route /api/v1/components/run
 */
export const apiSendComponentInput = async (engineId, nodeId, inputData) => {
    try {
        const payload = {
            node_id: nodeId,
            input: inputData,
            engine_id: engineId, // Opsional, buat logging
            timestamp: Date.now()
        };

        const response = await apiClient.post(`/components/run`, payload);

        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiSendComponentInput');
    }
};

/**
 * [ADDED BY FLOWORK DEV]
 * Save custom created component from Component Forge to Gateway/Core.
 * This triggers the backend to write the files (.py, .json, .txt) to the disk.
 */
export const apiSaveCustomComponent = async (componentData) => {
    try {
        const response = await apiClient.post('/components/custom/create', componentData);
        if (response.data.error) throw new Error(response.data.error);
        return response.data;
    } catch (error) {
        return handleApiError(error, 'apiSaveCustomComponent');
    }
};

export { apiClient };
export default apiClient;
