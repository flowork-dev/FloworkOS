//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\auth.js total lines 271 
//#######################################################################

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useSocketStore } from './socket';
import { ethers } from 'ethers';
import { useUiStore } from './ui';
import { apiDownloadLicenseFile } from '@/api';
import { useWorkflowStore } from './workflow';
import { useComponentStore } from './components';

export const useAuthStore = defineStore('auth', () => {
  const privateKey = ref(localStorage.getItem('flowork_private_key'));
  const user = ref(null);

  try {
      const storedUser = localStorage.getItem('flowork_user_identity');
      if (storedUser) user.value = JSON.parse(storedUser);
  } catch (e) {
      console.error("[AuthStore] Failed to parse stored user:", e);
  }

  const isMnemonicDialogVisible = ref(false);
  const newMnemonic = ref('');
  const isLoading = ref(false);
  const error = ref(null);

  const isAuthenticated = computed(() => !!privateKey.value && !!user.value);
  const hasPermission = computed(() => (permissionName) => isAuthenticated.value);

  function ensureHybridIdentity() {
      const hostname = window.location.hostname;
      const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');

      if (privateKey.value && user.value) return;

      const burnerAuth = localStorage.getItem('wallet_auth');
      if (burnerAuth) {
          try {
              const parsed = JSON.parse(burnerAuth);
              console.log("[AuthStore] Found Hybrid Burner Identity. Adopting it...");

              const identity = {
                  id: parsed.address,
                  publicKey: parsed.address, // Simplification for burner
                  username: parsed.address
              };

              privateKey.value = parsed.privateKey;
              user.value = identity;

              localStorage.setItem('flowork_private_key', parsed.privateKey);
              localStorage.setItem('flowork_user_identity', JSON.stringify(identity));
              return;
          } catch (e) {
              console.error("[AuthStore] Failed to parse wallet_auth:", e);
          }
      }

      if (isLocal) {
          console.log("[AuthStore] Localhost detected & No Identity. Generating Burner Wallet...");
          try {
              const wallet = ethers.Wallet.createRandom();
              const authData = {
                  address: wallet.address,
                  privateKey: wallet.privateKey,
                  mnemonic: wallet.mnemonic.phrase
              };

              localStorage.setItem('wallet_auth', JSON.stringify(authData));

              privateKey.value = wallet.privateKey;
              user.value = {
                  id: wallet.address,
                  publicKey: wallet.address,
                  username: wallet.address
              };

              localStorage.setItem('flowork_private_key', wallet.privateKey);
              localStorage.setItem('flowork_user_identity', JSON.stringify(user.value));

              console.log(`[AuthStore] Identity generated: ${wallet.address}`);
          } catch (e) {
              console.error("[AuthStore] Failed to generate local identity:", e);
          }
      }
  }

  ensureHybridIdentity();

  async function handleLoginSuccess() {
    console.log("[AuthStore] Lite Mode: handleLoginSuccess called.");

    const socketStore = useSocketStore();
    const workflowStore = useWorkflowStore();
    const componentStore = useComponentStore();

    await new Promise(resolve => setTimeout(resolve, 50));

    try {
        if (isAuthenticated.value) {
            await workflowStore.fetchUserFavorites();
            await componentStore.fetchUserFavorites();
        }
    } catch (e) {
        console.warn("[AuthStore] Failed to fetch favorites (Offline/Local?):", e);
    }

    console.log("[AuthStore] Connecting WebSocket directly (Lite Mode)...");
    socketStore.connect();
  }

  async function createNewIdentity() {
    isLoading.value = true;
    error.value = null;
    try {
      const wallet = ethers.Wallet.createRandom();
      newMnemonic.value = wallet.mnemonic.phrase;
      isMnemonicDialogVisible.value = true;
      localStorage.setItem('flowork_private_key_temp', wallet.privateKey);
      const identity = {
          id: wallet.address,
          publicKey: wallet.publicKey,
          username: wallet.address
      };
      localStorage.setItem('flowork_user_identity_temp', JSON.stringify(identity));
      return true;
    } catch (e) {
      error.value = e.message || "Failed to create identity.";
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function handleBackupConfirmation() {
       const tempKey = localStorage.getItem('flowork_private_key_temp');
       const tempIdentity = localStorage.getItem('flowork_user_identity_temp');
       if (!tempKey || !tempIdentity) {
           error.value = "Failed to finalize identity. Temporary data not found.";
           isMnemonicDialogVisible.value = false;
           return false;
       }
       localStorage.setItem('flowork_private_key', tempKey);
       localStorage.setItem('flowork_user_identity', tempIdentity);
       privateKey.value = tempKey;
       user.value = JSON.parse(tempIdentity);

       localStorage.removeItem('flowork_private_key_temp');
       localStorage.removeItem('flowork_user_identity_temp');

       isMnemonicDialogVisible.value = false;
       newMnemonic.value = '';

       const walletAuth = {
           address: user.value.id,
           privateKey: tempKey,
           mnemonic: 'backup-confirmed'
       };
       localStorage.setItem('wallet_auth', JSON.stringify(walletAuth));

       return true;
  }

  async function importIdentity(keyOrMnemonic) {
    isLoading.value = true;
    error.value = null;
    let wallet;
    try {
        wallet = keyOrMnemonic.startsWith('0x') ? new ethers.Wallet(keyOrMnemonic) : ethers.Wallet.fromPhrase(keyOrMnemonic);
        localStorage.setItem('flowork_private_key', wallet.privateKey);
        const identity = {
            id: wallet.address,
            publicKey: wallet.publicKey,
            username: wallet.address
        };
        localStorage.setItem('flowork_user_identity', JSON.stringify(identity));
        privateKey.value = wallet.privateKey;
        user.value = identity;

        const walletAuth = {
            address: wallet.address,
            privateKey: wallet.privateKey,
            mnemonic: 'imported'
        };
        localStorage.setItem('wallet_auth', JSON.stringify(walletAuth));

        return true;
    } catch (e) {
        console.error("Error importing identity:", e);
        error.value = "Invalid Private Key or Mnemonic Phrase.";
        return false;
    } finally {
        isLoading.value = false;
    }
  }

  async function downloadLicenseFile() {
       const uiStore = useUiStore();
       if (!isAuthenticated.value) {
           uiStore.showNotification({ text: 'You must be logged in to download a license.', color: 'error' });
           return;
       }
       uiStore.showNotification({ text: 'Requesting license file from server...', color: 'info' });
       try {
           const licenseContent = await apiDownloadLicenseFile();
           if (licenseContent.error) throw new Error(licenseContent.error);

           const licenseString = JSON.stringify(licenseContent, null, 2);
           const blob = new Blob([licenseString], { type: 'application/json' });
           const url = URL.createObjectURL(blob);
           const a = document.createElement('a');
           a.href = url;
           a.download = 'license.lic';
           document.body.appendChild(a);
           a.click();
             document.body.removeChild(a);
           URL.revokeObjectURL(url);
           uiStore.showNotification({ text: 'License file download started!', color: 'success' });
       } catch (error) {
           uiStore.showNotification({ text: error.message || 'Could not download license file.', color: 'error' });
       }
  }

  async function logout() {
    const socketStore = useSocketStore();
    socketStore.disconnect();
    privateKey.value = null;
    user.value = null;

    localStorage.removeItem('flowork_private_key');
    localStorage.removeItem('flowork_user_identity');
    localStorage.removeItem('wallet_auth'); // Clean up burner auth

    const router = (await import('@/router')).default;
    router.push({ name: 'Lander' });

    window.location.reload();
  }

  function handleLogoutError() {
       console.warn("[AuthStore] handleLogoutError called. Logging out fully.");
       logout();
  }

  async function tryAutoLogin() {
    isLoading.value = true;
    ensureHybridIdentity();

   if (privateKey.value && user.value) {
     console.log("[AuthStore] Found existing local identity. Connecting...");
     await handleLoginSuccess();
   } else {
        console.log("[AuthStore] No local identity found.");
   }
    isLoading.value = false;
  }

  return {
    user, privateKey, isAuthenticated, isLoading, error,
    isMnemonicDialogVisible, newMnemonic,
    hasPermission,
    logout, tryAutoLogin, createNewIdentity, importIdentity, handleBackupConfirmation,
    handleLogoutError,
    handleLoginSuccess
  };
});
