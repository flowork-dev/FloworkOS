//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\ShareWorkflowModal.vue total lines 166 
//#######################################################################

<template>
  <v-dialog v-model="shareStore.isModalOpen" max-width="700px" persistent scrollable>
    <v-card class="share-dialog-card">
      <v-card-title class="pa-4 d-flex align-center">
        <v-icon icon="mdi-share-variant-outline" class="mr-3" color="cyan"></v-icon>
        <span class="orbitron-font">{{ loc('sharing_modal_title', { workflowName: workflowToShare?.name }) }}</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="shareStore.closeShareModal"></v-btn>
      </v-card-title>
      <v-divider></v-divider>

      <v-card-text>
        <div class="mb-4">
            <p class="text-caption text-grey-lighten-1 mb-2">{{ loc('sharing_create_new_link') }}</p>
            <div class="d-flex align-center" style="gap: 16px;">
                <v-text-field
                    v-model="newLinkName"
                    :label="loc('sharing_link_name_label')"
                    variant="outlined"
                    density="compact"
                    hide-details
                    class="flex-grow-1"
                ></v-text-field>
                <v-select
                    v-model="permissionLevel"
                    :items="permissionOptions"
                    item-title="text"
                    item-value="value"
                    variant="outlined"
                    density="compact"
                    hide-details
                    style="max-width: 180px;"
                ></v-select>
                <v-btn
                    color="cyan"
                    variant="flat"
                    @click="handleCreateLink"
                    :loading="shareStore.isLoading"
                    class="action-button"
                >
                    {{ loc('sharing_create_button') }}
                </v-btn>
            </div>
        </div>

        <v-divider class="my-4"></v-divider>
        <h3 class="text-subtitle-1 mb-2">{{ loc('sharing_access_list_title') }}</h3>
         <div v-if="isLoadingShares" class="text-center pa-4">
            <v-progress-circular indeterminate color="cyan"></v-progress-circular>
         </div>
         <div v-else-if="shares.length === 0" class="text-center text-caption text-grey pa-4">
            {{ loc('sharing_empty_list_links') }}
        </div>
        <v-list v-else lines="two" bg-color="transparent" class="pa-0">
            <v-list-item v-for="share in shares" :key="share.share_id" class="share-item">
                <v-list-item-title class="font-weight-bold">{{ share.link_name }}</v-list-item-title>
                <v-list-item-subtitle class="text-caption text-grey">Created: {{ new Date(share.created_at).toLocaleString() }}</v-list-item-subtitle>
                 <div class="d-flex align-center mt-2" style="gap: 8px;">
                    <v-text-field
                        :model-value="share.share_url"
                        readonly
                        density="compact"
                        variant="solo-filled"
                        hide-details
                        append-inner-icon="mdi-content-copy"
                        @click:append-inner="copyToClipboard(share.share_url)"
                    ></v-text-field>
                     <v-select
                        :model-value="share.permission_level"
                        @update:modelValue="updatePermission(share.share_id, $event)"
                        :items="permissionOptions"
                        item-title="text"
                        item-value="value"
                        variant="outlined"
                        density="compact"
                        hide-details
                        style="max-width: 180px;"
                    ></v-select>
                 </div>

                <template v-slot:append>
                    <v-btn icon="mdi-delete-outline" variant="text" color="grey" @click="handleDelete(share.share_id)"></v-btn>
                </template>
            </v-list-item>
        </v-list>
      </v-card-text>

    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useShareStore } from '@/store/share';
import { useUiStore } from '@/store/ui';
import { useLocaleStore } from '@/store/locale';
import { storeToRefs } from 'pinia';

const shareStore = useShareStore();
const uiStore = useUiStore();
const localeStore = useLocaleStore();
const { loc } = storeToRefs(localeStore);
const { workflowToShare, shares, isLoadingShares } = storeToRefs(shareStore);

const newLinkName = ref('');
const permissionLevel = ref('view'); // English Hardcode
const permissionOptions = computed(() => [
    { text: loc.value('sharing_permission_view'), value: 'view' }, // English Hardcode
    { text: loc.value('sharing_permission_run'), value: 'view-run' }, // English Hardcode
    { text: loc.value('sharing_permission_edit'), value: 'view-edit-run' } // English Hardcode
]);

async function handleCreateLink() {
    await shareStore.createShareLink(permissionLevel.value, newLinkName.value || `New Link`); // English Hardcode
    newLinkName.value = '';
}

async function updatePermission(shareId, newPermission) {
    await shareStore.updateShare(shareId, newPermission);
}

async function handleDelete(shareId) {
    const confirmed = await uiStore.showConfirmation({
        title: 'Delete Share Link', // English Hardcode
        text: 'Are you sure you want to delete this share link? Anyone with this link will lose access immediately.', // English Hardcode
        color: 'error', // English Hardcode
        confirmText: 'Delete' // English Hardcode
    });
    if (confirmed) {
        await shareStore.deleteShare(shareId);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    uiStore.showNotification({ text: 'Link copied to clipboard!', color: 'success' }); // English Hardcode
}
</script>

<style scoped>
.share-dialog-card {
  background-color: #2a2a4a;
  border: 1px solid rgba(0, 245, 255, 0.3);
}
.orbitron-font {
  font-family: 'Orbitron', monospace;
  color: var(--neon-cyan);
}
.action-button {
    font-weight: bold;
    color: #010c03 !important;
}
.share-item {
    padding: 16px !important;
    margin-bottom: 12px;
    border-radius: 8px;
    background-color: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.1);
}
</style>
