//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\marketplace.js total lines 427 
//#######################################################################

import { defineStore } from 'pinia';
import { ref } from 'vue';
import {
    apiGetMarketplaceItems,
    apiPublishMarketplaceItem,
    apiDeleteMarketplaceItem,
    apiVoteMarketplaceItem,
    apiListCapsules,
    apiGetCapsule,
    apiInstallCapsule,
    apiRemixCapsule
} from '@/api';
import { useUiStore } from './ui';
import { useWorkflowStore } from './workflow';
import { useAuthStore } from './auth';

const GITHUB_USER = 'flowork-dev';
const GITHUB_REPO = 'flowork-presets';
const GITHUB_BRANCH = 'main';
const BASE_RAW_URL = `https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}`;

const LOCAL_ENGINE_API_BASE = 'http://localhost:8989/api/v1';

export const useMarketplaceStore = defineStore('marketplace', () => {
    const items = ref([]);
    const selectedItem = ref(null);
    const isLoadingList = ref(false);
    const isLoadingDetail = ref(false);
    const isPublishing = ref(false);
    const error = ref(null);
    const userVotes = ref({});

    const capsules = ref([]);
    const selectedCapsule = ref(null);
    const isLoadingCapsuleList = ref(false);
    const isLoadingCapsuleDetail = ref(false);
    const capsuleError = ref(null);

    /**
     * HYBRID LIST: Fetch from Database (D1) via API Gateway
     */
    async function fetchItems(filters = { type: 'preset' }) {
        isLoadingList.value = true;
        error.value = null;
        try {
            const itemList = await apiGetMarketplaceItems(filters);
            if (itemList.error) throw new Error(itemList.error);

            items.value = itemList.map(i => ({
                ...i,
                desc: i.desc || i.description || 'No description available.',
                likes: i.likes || 0,
                dislikes: i.dislikes || 0
            }));

            console.log(`[MarketStore] Fetched ${itemList.length} items.`);
        } catch (e) {
            error.value = e.message || 'Failed to fetch marketplace items.';
            console.error(`[MarketStore] ${error.value}`);
        } finally {
            isLoadingList.value = false;
        }
    }

    /**
     * (English Hardcode) ROBUST DETAIL FETCHING
     * Fixes "Description Empty" and "Data Missing" by aggressively searching the JSON structure.
     */
    async function fetchItemDetail(id) {
        isLoadingDetail.value = true;
        error.value = null;
        selectedItem.value = null;

        try {
            let itemMeta = items.value.find(i => i.id === id) || {};

            let downloadUrl = itemMeta.download_url;
            if (!downloadUrl) {
                 downloadUrl = `${BASE_RAW_URL}/presets/${id}.json`;
            }

            console.log(`[MarketStore] Fetching detail from: ${downloadUrl}`);

            const response = await fetch(downloadUrl);
            if (!response.ok) throw new Error(`Failed to download: ${response.statusText}`);

            const rawText = await response.text();
            let fullData = {};
            try {
                fullData = JSON.parse(rawText);
            } catch (e) {
                console.warn("[MarketStore] Not valid JSON, assuming raw content.");
                fullData = { data: rawText }; // Fallback wrapper
            }


            const contentObj = fullData.content || fullData.data || fullData;

            const hasZip = contentObj.zip_data || contentObj.zip_file || fullData.zip_data;
            let finalType = itemMeta.type || fullData.type || (hasZip ? 'module' : 'preset');

            let finalZipData = contentObj.zip_data || contentObj.zip_file || fullData.zip_data;

            let finalDesc =
                   contentObj.description || contentObj.desc
                || fullData.description || fullData.desc
                || fullData.meta?.description || fullData.meta?.desc
                || itemMeta.desc || itemMeta.description
                || 'No description provided.';

            let finalAuthor =
                   fullData.author || fullData.owner
                || fullData.meta?.author
                || itemMeta.author || 'Community';

            selectedItem.value = {
                id: fullData.id || itemMeta.id || id,
                name: fullData.name || itemMeta.name || id,
                type: finalType,
                desc: finalDesc,
                author: finalAuthor,
                price: fullData.price || itemMeta.price || 0,
                likes: itemMeta.likes || 0,
                dislikes: itemMeta.dislikes || 0,
                created_at: fullData.created_at || itemMeta.created_at,
                version: fullData.version || '1.0.0',

                data: hasZip ? finalZipData : contentObj
            };

            console.log("[MarketStore] Detail Loaded:", {
                type: finalType,
                hasData: !!selectedItem.value.data,
                descLen: finalDesc.length
            });

            return selectedItem.value;

        } catch (e) {
            error.value = e.message || 'Failed to fetch item detail.';
            console.error("[MarketStore] Error:", e);
            return null;
        } finally {
            isLoadingDetail.value = false;
        }
    }

    /**
     * PUBLISH PRESET (From Workflow Canvas)
     */
    async function publishCurrentWorkflow(formData) {
        const uiStore = useUiStore();
        const workflowStore = useWorkflowStore();

        if (!formData.name) {
            uiStore.showNotification({ text: 'Item name is required.', color: 'error' });
            return false;
        }

        const workflowData = workflowStore.getWorkflowForPublishing;
        if (!workflowData || workflowData.nodes.length === 0) {
             uiStore.showNotification({ text: 'Cannot publish an empty workflow.', color: 'error' });
            return false;
        }

        isPublishing.value = true;
        error.value = null;

        const payload = {
            type: 'preset',
            name: formData.name,
            desc: formData.desc,
            price: formData.price || 0,
            data: workflowData
        };

        try {
            const result = await apiPublishMarketplaceItem(payload);
            if (result.error) throw new Error(result.error);

            uiStore.showNotification({ text: 'Preset published successfully!', color: 'success' });
            await fetchItems();
            return true;
        } catch (e) {
            const msg = e.message || 'Unknown Error';
            error.value = msg;
            uiStore.showNotification({ text: `Publish Error: ${msg}`, color: 'error' });
            return false;
        } finally {
            isPublishing.value = false;
        }
    }

    /**
     * (English Hardcode) PUBLISH SMART PACKAGE (Pre-zipped by Frontend)
     * Used by ModuleToolbox -> MarketplacePublishDialog flow
     */
    async function publishSmartPackage(payload) {
        const uiStore = useUiStore();
        isPublishing.value = true;
        error.value = null;

        try {
            console.log(`[MarketStore] Publishing smart package: ${payload.name}`);

            const apiPayload = {
                type: payload.type,
                name: payload.name,
                desc: payload.description || payload.desc,
                price: payload.price || 0,
                data: {
                    id: payload.name,
                    type: payload.type,
                    name: payload.name,
                    description: payload.description,
                    zip_data: payload.zip_file // This is the Base64 content
                }
            };

            const result = await apiPublishMarketplaceItem(apiPayload);
            if (result.error) throw new Error(result.error);

            uiStore.showNotification({ text: `${payload.name} published successfully!`, color: 'success' });
            await fetchItems({ type: payload.type });
            return true;

        } catch (e) {
            const msg = e.message || 'Publish Failed';
            error.value = msg;
            uiStore.showNotification({ text: `Publish Error: ${msg}`, color: 'error' });
            return false;
        } finally {
            isPublishing.value = false;
        }
    }

    /**
     * (English Hardcode) LEGACY/BACKUP: Server-side Zipping
     */
    async function publishComponent(componentPayload) {
        const uiStore = useUiStore();
        isPublishing.value = true;
        error.value = null;

        try {
            const targetId = componentPayload.id || componentPayload.name;
            console.log(`[MarketStore] Preparing to package ${componentPayload.type}: ${targetId}`);

            const packageResp = await fetch(`${LOCAL_ENGINE_API_BASE}/components/package`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: componentPayload.type,
                    id: targetId
                })
            });

            if (!packageResp.ok) {
                const errText = await packageResp.text();
                throw new Error(`Local Engine Packaging Failed: ${errText}`);
            }

            const packageData = await packageResp.json();

            const fileContent = {
                id: targetId,
                type: componentPayload.type,
                name: componentPayload.name,
                description: componentPayload.desc || packageData.description,
                zip_data: packageData.zip_data
            };

            componentPayload.data = fileContent;

            if (!componentPayload.desc) {
                componentPayload.desc = packageData.description;
            }

            const result = await apiPublishMarketplaceItem(componentPayload);
            if (result.error) throw new Error(result.error);

            uiStore.showNotification({ text: `${componentPayload.type} published successfully!`, color: 'success' });
            await fetchItems({ type: componentPayload.type });
            return true;
        } catch (e) {
             const msg = e.message || 'Unknown Error';
             error.value = msg;
             uiStore.showNotification({ text: `Publish Error: ${msg}`, color: 'error' });
             return false;
        } finally {
            isPublishing.value = false;
        }
    }

    async function deleteItem(id) {
        const uiStore = useUiStore();
        try {
            const response = await apiDeleteMarketplaceItem(id);
            if (response.error) throw new Error(response.error);

            uiStore.showNotification({ text: 'Item deleted successfully!', color: 'success' });
            await fetchItems();
            selectedItem.value = null;
            return true;
        } catch(e) {
             const msg = e.message || 'Delete Failed';
             uiStore.showNotification({ text: `Delete Failed: ${msg}`, color: 'error' });
             return false;
        }
    }

    async function handleVote(itemId, voteType) {
        const authStore = useAuthStore();
        const uiStore = useUiStore();

        if (!authStore.isAuthenticated) {
            uiStore.showNotification({ text: 'Please connect your wallet to vote.', color: 'warning' });
            return;
        }

        try {
            const result = await apiVoteMarketplaceItem(itemId, voteType);
            if (result.error) throw new Error(result.error);

            const newStatus = result.newVoteStatus;
            const itemIndex = items.value.findIndex(i => i.id === itemId);
            if (itemIndex > -1) {
                const oldStatus = userVotes.value[itemId] || 0;
                let deltaLike = 0;
                let deltaDislike = 0;

                if (oldStatus === 1) deltaLike--;
                if (oldStatus === -1) deltaDislike--;
                if (newStatus === 1) deltaLike++;
                if (newStatus === -1) deltaDislike++;

                items.value[itemIndex].likes = Math.max(0, items.value[itemIndex].likes + deltaLike);
                items.value[itemIndex].dislikes = Math.max(0, items.value[itemIndex].dislikes + deltaDislike);

                if (selectedItem.value && selectedItem.value.id === itemId) {
                    selectedItem.value.likes = items.value[itemIndex].likes;
                    selectedItem.value.dislikes = items.value[itemIndex].dislikes;
                }
            }

            userVotes.value[itemId] = newStatus;
            let msg = newStatus === 1 ? 'Liked!' : (newStatus === -1 ? 'Disliked!' : 'Vote removed.');
            uiStore.showNotification({ text: msg, color: 'info' });

        } catch (e) {
            const msg = e.message || 'Voting Failed';
            uiStore.showNotification({ text: `Vote Error: ${msg}`, color: 'error' });
        }
    }

    async function fetchCapsules() {
        isLoadingCapsuleList.value = true;
        capsuleError.value = null;
        try {
            const data = await apiListCapsules();
            if (data.error) throw new Error(data.error);
            capsules.value = data.items || [];
        } catch (e) {
            capsuleError.value = e.message;
        } finally {
            isLoadingCapsuleList.value = false;
        }
    }

    async function fetchCapsuleDetails(capsuleId) {
        isLoadingCapsuleDetail.value = true;
        selectedCapsule.value = null;
        try {
            const data = await apiGetCapsule(capsuleId);
            if (data.error) throw new Error(data.error);
            selectedCapsule.value = data;
            return data;
        } catch (e) {
            capsuleError.value = e.message;
            return null;
        } finally {
            isLoadingCapsuleDetail.value = false;
        }
    }

    async function installCapsule(capsulePayload) {
        const ui = useUiStore();
        try {
            const installed = await apiInstallCapsule(capsulePayload);
            if (installed.error) throw new Error(installed.error);
            ui.showNotification({ text: `Capsule '${installed.capsule_id}' installed!`, color: 'success' });
            await fetchCapsules();
            return true;
        } catch (e) {
            ui.showNotification({ text: `Install failed: ${e.message}`, color: 'error' });
            return false;
        }
    }

    async function remixCapsule(baseId, newId, patch) {
        const ui = useUiStore();
        try {
            const remixed = await apiRemixCapsule(baseId, newId, patch);
            if (remixed.error) throw new Error(remixed.error);
            ui.showNotification({ text: `Remix '${remixed.capsule_id}' created!`, color: 'success' });
            await fetchCapsules();
            return remixed;
        } catch (e) {
            ui.showNotification({ text: `Remix failed: ${e.message}`, color: 'error' });
            return null;
        }
    }

    return {
        items, selectedItem, isLoadingList, isLoadingDetail, isPublishing, error, userVotes,
        fetchItems, fetchItemDetail, publishCurrentWorkflow, deleteItem, handleVote,
        publishComponent, publishSmartPackage,
        capsules, selectedCapsule, isLoadingCapsuleList, isLoadingCapsuleDetail, capsuleError,
        fetchCapsules, fetchCapsuleDetails, installCapsule, remixCapsule
    };
});
