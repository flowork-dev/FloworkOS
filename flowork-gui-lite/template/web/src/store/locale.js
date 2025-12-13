//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\src\store\locale.js total lines 65 
//#######################################################################

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import en from '@/locales/en.json';
import id from '@/locales/id.json';

export const useLocaleStore = defineStore('locale', () => {
    const currentLang = ref(localStorage.getItem('flowork_language') || 'en');
    const dictionaries = { en, id };
    const isDictionaryLoaded = ref(false); // Biar kompatibel sama UI loader kalo ada

    const loc = computed(() => {
        return (key) => {
            const dict = dictionaries[currentLang.value] || dictionaries['en'];

            const cleanKey = key.startsWith('loc.') ? key.substring(4) : key;

            return dict[cleanKey] || key;
        };
    });

    function setLanguage(lang) {
        if (!dictionaries[lang]) {
            console.warn(`[Locale] Language ${lang} not supported, falling back to en`);
            lang = 'en';
        }

        currentLang.value = lang;

        localStorage.setItem('flowork_language', lang);

        document.documentElement.lang = lang;

        console.log(`[Locale] Switched to: ${lang}`);
    }

    async function fetchDictionary() {
        console.log('[Locale] Initializing dictionary...');

        const saved = localStorage.getItem('flowork_language');

        if (saved) {
            setLanguage(saved);
        } else {
            const browserLang = navigator.language.split('-')[0];
            setLanguage(dictionaries[browserLang] ? browserLang : 'en');
        }

        isDictionaryLoaded.value = true;
        return true;
    }

    return {
        currentLang,
        loc,
        setLanguage,
        fetchDictionary, // Ini dia penyelamatnya
        isDictionaryLoaded
    };
});
