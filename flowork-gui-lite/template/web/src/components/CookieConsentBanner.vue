//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\components\CookieConsentBanner.vue total lines 68 
//#######################################################################

<template>
  <v-snackbar
    v-model="showBanner"
    :timeout="-1"
    location="bottom right"
    color="blue-grey-darken-3"
    class="cookie-banner"
    multi-line
  >
    <div class="banner-content">
        <p class="text-body-2 mb-2">
            This website uses cookies to ensure you get the best experience. By continuing to use this site, you agree to our use of cookies.
        </p>
        <router-link to="/privacy-policy" class="privacy-link">Learn More</router-link>
    </div>

    <template v-slot:actions>
      <v-btn color="cyan" variant="flat" @click="acceptCookies" class="accept-btn">
        Accept
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const showBanner = ref(false);

onMounted(() => {
  if (!localStorage.getItem('flowork_cookies_accepted')) {
    showBanner.value = true;
  }
});

function acceptCookies() {
  localStorage.setItem('flowork_cookies_accepted', 'true');
  showBanner.value = false;
}
</script>

<style scoped>
.cookie-banner {
  z-index: 2000 !important; /* Pastikan di atas konten lain */
}
.banner-content {
    display: flex;
    flex-direction: column;
}
.privacy-link {
  color: #00f5ff;
  text-decoration: none;
  font-size: 0.8rem;
}
.privacy-link:hover {
    text-decoration: underline;
}
.accept-btn {
    font-weight: bold;
    color: #000 !important;
}
</style>
