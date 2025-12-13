//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\main.js total lines 124 
//#######################################################################

import { createApp } from 'vue'
import App from './App.vue'
import './styles/main.css'
import './styles/theme.css'
import { createPinia } from 'pinia'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import {
  VApp, VAppBar, VAppBarNavIcon, VBtn, VIcon, VSpacer, VMenu, VList, VListItem, VListItemTitle, VDivider,
  VLayout, VMain, VProgressCircular, VSnackbar, VRow, VCol, VCard, VCardText, VCardActions, VCardTitle,
  VContainer, VForm, VTextField, VCheckbox, VAlert, VImg, VAvatar, VChip, VDialog, VTabs, VTab, VWindow,
  VWindowItem, VNavigationDrawer, VExpansionPanels, VExpansionPanel, VExpansionPanelText, VSelect,
  VTextarea, VFileInput, VRadioGroup, VRadio, VSwitch, VDataTable, VToolbar, VToolbarTitle,
  VSkeletonLoader, VBtnToggle, VTooltip, VListSubheader, VCheckboxBtn
} from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'
import '@vue-flow/core/dist/style.css'
import router from './router/index.js'
import { useAuthStore } from './store/auth'
import { useLocaleStore } from './store/locale'
import { useSocketStore } from './store/socket'
import { useUiStore } from './store/ui';

import VMdEditor from '@kangc/v-md-editor';
import '@kangc/v-md-editor/lib/style/base-editor.css';
import vuepressTheme from '@kangc/v-md-editor/lib/theme/vuepress.js';
import '@kangc/v-md-editor/lib/theme/style/vuepress.css';
import Prism from 'prismjs';


const floworkThemes = {
  themes: {
    flowork_default: {
      dark: true,
      colors: {
        background: '#1a1a2e',
        surface: '#2a2a4a',
        primary: '#64ffda',
        secondary: '#a59dff',
        error: '#ff5252',
        info: '#2196F3',
        success: '#4CAF50',
        warning: '#FB8C00',
      }
    },
    cyberpunk: { /* ... */ },
    light: { /* ... */ }
  }
}

const vuetify = createVuetify({
  components: {
    VApp, VAppBar, VAppBarNavIcon, VBtn, VIcon, VSpacer, VMenu, VList, VListItem, VListItemTitle, VDivider,
    VLayout, VMain, VProgressCircular, VSnackbar, VRow, VCol, VCard, VCardText, VCardActions, VCardTitle,
    VContainer, VForm, VTextField, VCheckbox, VAlert, VImg, VAvatar, VChip, VDialog, VTabs, VTab, VWindow,
    VWindowItem, VNavigationDrawer, VExpansionPanels, VExpansionPanel, VExpansionPanelText, VSelect,
    VTextarea, VFileInput, VRadioGroup, VRadio, VSwitch, VDataTable, VToolbar, VToolbarTitle,
    VSkeletonLoader, VBtnToggle, VTooltip, VListSubheader, VCheckboxBtn
  },
  directives,
  theme: floworkThemes
})

async function initializeApp() {
  const appElement = document.getElementById('app');
  if (appElement) {
    console.log('[Flowork] Main app element found, mounting GUI...');
    const app = createApp(App);
    const pinia = createPinia();
    app.use(pinia);

    const authStore = useAuthStore();
    const socketStore = useSocketStore();
    const localeStore = useLocaleStore();

    VMdEditor.use(vuepressTheme, {
      Prism,
    });
    app.use(VMdEditor);

    await localeStore.fetchDictionary();

    app.config.globalProperties.$t = localeStore.loc;
    console.log('[Flowork Main] Global translation function ($t) injected.');

    app.use(router);
    app.use(vuetify);

    await authStore.tryAutoLogin();

    if (authStore.isAuthenticated) {
        console.log('[Flowork Main] User is authenticated, connecting socket immediately...');
        socketStore.connect();
    }

    authStore.$subscribe((mutation, state) => {
        const isAuth = !!state.token && !!state.user;

        if (isAuth) {
            if (!socketStore.isConnected && !socketStore.isConnecting) {
                console.log('[Flowork Main Watcher] User logged IN, connecting socket...');
                socketStore.connect();
            }
        } else {
            if (socketStore.isConnected) {
                console.log('[Flowork Main Watcher] User logged OUT, disconnecting socket...');
                socketStore.disconnect();
            }
        }
    });

    app.mount('#app');
  }
}


initializeApp();
