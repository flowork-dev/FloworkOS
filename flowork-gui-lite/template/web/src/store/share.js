//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\share.js total lines 128 
//#######################################################################

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiGetWorkflowShares, apiCreateShareLink, apiUpdateSharePermission, apiDeleteShare } from '@/api';
import { useUiStore } from './ui';

export const useShareStore = defineStore('share', () => {
    const isModalOpen = ref(false);
    const workflowToShare = ref(null);
    const shares = ref([]);
    const isLoading = ref(false);
    const isLoadingShares = ref(false);


    /**
     * Membuka modal sharing untuk workflow tertentu.
     * @param {object} workflow - Objek workflow yang akan di-share, minimal punya 'name'.
     */
    async function openShareModal(workflow) {
        if (!workflow || !workflow.name) {
            console.error('[ShareStore] Failed to open share modal: workflow data incomplete.');
            return;
        }
        workflowToShare.value = workflow;
        isModalOpen.value = true;
        shares.value = []; // Kosongkan dulu
        await fetchShares(); // Langsung fetch daftar link yang sudah ada
    }

    function closeShareModal() {
        isModalOpen.value = false;
        workflowToShare.value = null;
        shares.value = [];
    }

    async function fetchShares() {
        if (!workflowToShare.value) return;
        isLoadingShares.value = true;
        const uiStore = useUiStore();
        try {
            console.log(`[ShareStore] Fetching shares for workflow: ${workflowToShare.value.name}`);
            const result = await apiGetWorkflowShares(workflowToShare.value.name);
            if (result.error) throw new Error(result.error);
            shares.value = result; // Simpan daftar link
        } catch (error) {
            console.error('[ShareStore] Failed to fetch shares:', error);
            uiStore.showNotification({ text: error.message || 'Failed to fetch share links.', color: 'error' });
            shares.value = [];
        } finally {
            isLoadingShares.value = false;
        }
    }

    async function createShareLink(permissionLevel, linkName) {
        if (!workflowToShare.value) return;

        const uiStore = useUiStore();
        isLoading.value = true;
        try {
            console.log(`[ShareStore] Creating share link for ${workflowToShare.value.name} with permission ${permissionLevel}`);
            const newShare = await apiCreateShareLink(workflowToShare.value.name, permissionLevel, linkName);
            if (newShare.error) throw new Error(newShare.error); // Handle error dari API
            shares.value.push(newShare); // Tambahkan link baru ke list
            uiStore.showNotification({ text: 'Share link created successfully!', color: 'success' });
        } catch (error) {
            console.error('[ShareStore] Failed to create share link:', error);
            uiStore.showNotification({ text: error.message || 'Failed to create share link.', color: 'error' });
        } finally {
            isLoading.value = false;
        }
    }

    async function updateShare(shareId, newPermission) {
        const uiStore = useUiStore();
        isLoading.value = true; // Bisa gunakan isLoading atau state terpisah
        try {
            console.log(`[ShareStore] Updating permission for share ${shareId} to ${newPermission}`);
            const updatedShare = await apiUpdateSharePermission(shareId, newPermission);
            if (updatedShare.error) throw new Error(updatedShare.error);
            const shareIndex = shares.value.findIndex(s => s.share_id === shareId); // PERBAIKAN: Gunakan share_id
            if (shareIndex > -1) {
                shares.value[shareIndex].permission_level = newPermission;
            }
            uiStore.showNotification({ text: 'Permission updated.', color: 'info' });
        } catch (error) {
            console.error('[ShareStore] Failed to update permission:', error);
            uiStore.showNotification({ text: error.message || 'Failed to update permission.', color: 'error' });
        } finally {
            isLoading.value = false;
        }
    }

    async function deleteShare(shareId) {
        const uiStore = useUiStore();
        isLoading.value = true;
        try {
            console.log(`[ShareStore] Deleting share link ${shareId}`);
            const result = await apiDeleteShare(shareId);
            if (result.error) throw new Error(result.error);
            shares.value = shares.value.filter(s => s.share_id !== shareId); // PERBAIKAN: Gunakan share_id
            uiStore.showNotification({ text: 'Share link deleted.', color: 'info' });
        } catch (error) {
            console.error('[ShareStore] Failed to delete share link:', error);
            uiStore.showNotification({ text: error.message || 'Failed to delete share link.', color: 'error' });
        } finally {
            isLoading.value = false;
        }
    }

    return {
        isModalOpen,
        workflowToShare,
        shares,
        isLoading,
        isLoadingShares,
        openShareModal,
        closeShareModal,
        fetchShares,
        createShareLink,
        updateShare,
        deleteShare
    };
});
