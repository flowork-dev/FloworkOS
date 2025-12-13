//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\views\LoginView.vue total lines 89 
//#######################################################################

<template>
  <AuthLayout
    title="UNLOCK IDENTITY"
    switchText="Don't have an identity? Create one"
    switchLink="/register"
  >
    <template #form-fields>
      <v-form @submit.prevent="handleLogin">
        <v-textarea
          label="Import Private Key or Mnemonic"
          name="privateKey"
          prepend-inner-icon="mdi-key-outline"
          type="password"
          variant="outlined"
          v-model="privateKeyOrMnemonic"
          class="neon-input mb-4"
          rows="3"
          :rules="[rules.required]"
          placeholder="Enter your 12-word recovery phrase or your 0x... private key"
        ></v-textarea>


        <v-alert
          v-if="authStore.error || sessionExpired"
          type="error"
          density="compact"
          class="mt-4"
          variant="tonal"
        >
          {{ authStore.error || 'Your session has expired. Please login again.' }}
        </v-alert>
      </v-form>

      </template>
    <template #actions>
      <v-btn
        color="cyan"
        large
        block
        @click="handleLogin"
        :loading="authStore.isLoading"
        class="neon-submit-btn"
      >
        Unlock Identity & Connect
      </v-btn>
    </template>
  </AuthLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import AuthLayout from '@/components/AuthLayout.vue';
import { useRoute, useRouter } from 'vue-router';

const privateKeyOrMnemonic = ref('');
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const rules = {
  required: value => !!value || 'This field is required.',
};

const sessionExpired = computed(() => route.query.session === 'expired');

const handleLogin = async () => {
  if (privateKeyOrMnemonic.value) {
    const success = await authStore.importIdentity(privateKeyOrMnemonic.value);
    if (success) {
      console.log("[LoginView] Identity import successful. Triggering login success handler...");
      await authStore.handleLoginSuccess();

      const redirectTo = route.query.redirect || { name: 'Designer' };
      router.push(redirectTo);
    }
  }
};

onMounted(() => {
    authStore.error = null;
});
</script>
