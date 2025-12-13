//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\settings\CloudSyncSettings.vue total lines 100 
//#######################################################################

<template>
  <div>
    <h2 class="section-title">{{ loc('settings_section_cloud_sync') }}</h2>
    <SettingsField :label="loc('settings_sync_title')" :hint="loc('settings_sync_description')">
      <div class="d-flex" style="gap: 16px;">
        <v-btn
          variant="tonal"
          color="primary"
          prepend-icon="mdi-cloud-upload"
          @click="triggerAction('backup')"
          :loading="loadingAction === 'backup'"
        >
          {{ loc('settings_sync_backup_btn') }}
        </v-btn>
        <v-btn
          variant="tonal"
          color="warning"
          prepend-icon="mdi-cloud-download"
          @click="triggerAction('restore')"
          :loading="loadingAction === 'restore'"
        >
          {{ loc('settings_sync_restore_btn') }}
        </v-btn>
      </div>
    </SettingsField>

    <v-card v-if="lastMessage" class="mt-4 pa-3 bg-grey-darken-4" variant="outlined">
        <div class="d-flex align-center">
            <v-icon :color="lastStatus === 'error' ? 'red' : 'green'" class="mr-2">
                {{ lastStatus === 'error' ? 'mdi-alert-circle' : 'mdi-check-circle' }}
            </v-icon>
            <span class="text-caption">{{ lastMessage }}</span>
        </div>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useSocketStore } from '@/store/socket';
import { useLocaleStore } from '@/store/locale';
import { useUiStore } from '@/store/ui';
import SettingsField from '@/components/settings/SettingsField.vue';
import { storeToRefs } from 'pinia';

const socketStore = useSocketStore();
const localeStore = useLocaleStore();
const uiStore = useUiStore();
const { loc } = storeToRefs(localeStore);

const loadingAction = ref(null);
const lastMessage = ref('');
const lastStatus = ref('');

function onBackupRestoreResult(data) {
    loadingAction.value = null;
    const payload = data.payload || data;

    if (payload.error) {
        lastStatus.value = 'error';
        lastMessage.value = payload.error;
        uiStore.showNotification({ text: 'Operation Failed: ' + payload.error, color: 'error' });
    } else {
        lastStatus.value = 'success';
        lastMessage.value = payload.message || 'Operation successful!';
        uiStore.showNotification({ text: payload.message || 'Success!', color: 'success' });
    }
}

function triggerAction(action) {
    loadingAction.value = action;
    lastMessage.value = '';

    socketStore.sendMessage({
        type: action === 'backup' ? 'trigger_backup' : 'trigger_restore'
    });

    setTimeout(() => {
        if (loadingAction.value === action) {
            loadingAction.value = null;
            lastStatus.value = 'error';
            lastMessage.value = 'Request timed out. Is the Engine online?';
        }
    }, 10000);
}

onMounted(() => {
    socketStore.addListener('backup_restore_result', onBackupRestoreResult);
});

onUnmounted(() => {
    socketStore.removeListener('backup_restore_result', onBackupRestoreResult);
});
</script>
