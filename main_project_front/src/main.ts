import { createApp } from 'vue';

import App from './App.vue';
import { initializeLocale } from './composables/useLocale';
import router from './router';
import './style.css';

initializeLocale();

createApp(App).use(router).mount('#app');
