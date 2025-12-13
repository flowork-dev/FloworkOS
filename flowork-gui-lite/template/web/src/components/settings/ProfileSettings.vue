//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\settings\ProfileSettings.vue total lines 198 
//#######################################################################

<template>
  <div>
    <h2 class="section-title">Public Cloud Profile</h2>
    <p class="section-description">
      This information is stored on the Flowork cloud server and is visible to other users.
    </p>

    <v-skeleton-loader
      v-if="profileStore.isLoading && !profileStore.profile"
      type="list-item-two-line, list-item-two-line"
      color="transparent"
      class="mb-4"
    ></v-skeleton-loader>

    <v-alert
      v-else-if="profileStore.error"
      type="error"
      variant="tonal"
      class="mb-4"
      closable
    >
      {{ profileStore.error }}
      <template v-slot:append>
        <v-btn size="small" variant="text" @click="profileStore.fetchProfile()">Retry</v-btn>
      </template>
    </v-alert>

    <v-form v-else-if="localProfile" @submit.prevent="handleSave">
      <SettingsField
        label="Public Username"
        hint="Must be 3-20 characters (letters, numbers, underscore)."
      >
        <v-text-field
          v-model="localProfile.name"
          variant="outlined"
          density="compact"
          hide-details="auto"
          placeholder="Your unique username"
          :rules="[usernameRule]"
          :error-messages="profileStore.error && profileStore.error.includes('Username') ? profileStore.error : ''"
          class="hacker-input"
        ></v-text-field>
      </SettingsField>

      <v-btn
        color="cyan"
        @click="handleSave"
        :loading="isSaving"
        :disabled="!isFormValid"
        class="mt-4 save-button"
        block
        size="large"
      >
        Save Profile
      </v-btn>
    </v-form>

    <div v-else class="text-center pa-8">
         <v-icon icon="mdi-account-off" size="64" color="grey"></v-icon>
         <p class="mt-4 text-grey">Please connect your wallet to view profile.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useProfileStore } from '@/store/profile';
import { useAuthStore } from '@/store/auth';
import { useUiStore } from '@/store/ui';
import SettingsField from '@/components/settings/SettingsField.vue';

const profileStore = useProfileStore();
const authStore = useAuthStore();
const uiStore = useUiStore();

const localProfile = ref(null);
const isSaving = ref(false);

const usernameRule = (value) => {
  if (!value) return true;
  return /^[a-zA-Z0-9_]{3,20}$/.test(value) || 'Must be 3-20 alphanumeric characters or underscore.';
};

const isFormValid = computed(() => {
    if (!localProfile.value || !localProfile.value.name) return true;
    return usernameRule(localProfile.value.name) === true;
});

watch(() => profileStore.profile, (newProfile) => {
  if (newProfile) {
    localProfile.value = JSON.parse(JSON.stringify(newProfile));
  } else if (authStore.user) {
    localProfile.value = {
        name: authStore.user.username || '',
        bio: '',
        addr: authStore.user.public_address || ''
    };
  }
}, { immediate: true, deep: true });

watch(() => authStore.token, (newToken) => {
    if (newToken && !profileStore.profile) {
         console.log('[ProfileSettings] Auth token ready. Retrying fetch...');
         profileStore.fetchProfile();
    }
});

onMounted(() => {
    if (authStore.token || authStore.privateKey) {
        profileStore.fetchProfile();
    }
});

async function handleSave() {
  if (localProfile.value && isFormValid.value) {
    isSaving.value = true;
    try {
        const success = await profileStore.saveProfile({
          name: localProfile.value.name,
          bio: localProfile.value.bio, // Tetap dikirim (hidden value)
          avatar: localProfile.value.avatar,
        });

        if (success) {
             uiStore.showNotification({ text: 'Profile updated successfully!', color: 'success' });
             await profileStore.fetchProfile();
        } else {
             uiStore.showNotification({ text: 'Failed to update profile.', color: 'error' });
        }
    } catch (e) {
        console.error(e);
        uiStore.showNotification({ text: 'Error saving profile: ' + e.message, color: 'error' });
    } finally {
        isSaving.value = false;
    }
  }
}
</script>

<style scoped>
.section-title {
  font-family: 'Orbitron', monospace;
  font-size: 1.5rem;
  margin-bottom: 8px;
  color: #ffffff;
  text-shadow: 0 0 5px rgba(0,0,0,0.8);
}
.section-description {
  font-size: 0.9rem;
  color: #bdbdbd;
  margin-bottom: 32px;
}
.save-button {
  font-weight: 900;
  color: #000 !important;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
}

.hacker-input :deep(.v-field) {
    background-color: rgba(20, 20, 35, 0.9) !important;
    color: #ffffff !important;
    border: 1px solid rgba(100, 255, 218, 0.3);
}
.hacker-input :deep(.v-field__outline) {
    display: none;
}
.hacker-input :deep(input),
.hacker-input :deep(textarea) {
    color: #ffffff !important;
    font-family: 'Consolas', monospace;
}
.hacker-input :deep(input::placeholder),
.hacker-input :deep(textarea::placeholder) {
    color: rgba(255, 255, 255, 0.3) !important;
}
.hacker-input :deep(.v-label) {
    color: var(--neon-cyan) !important;
    opacity: 0.9 !important;
}
.hacker-input :deep(.v-field--focused) {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.25);
}
.disabled-input :deep(.v-field) {
    background-color: rgba(0, 0, 0, 0.5) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}
.disabled-input :deep(input) {
    color: #888 !important;
    cursor: not-allowed;
}
</style>
