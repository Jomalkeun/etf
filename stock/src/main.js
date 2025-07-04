import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import PrimeVue from 'primevue/config'
import router from './router'
import Aura from "@primeuix/themes/aura";

// import 'primevue/resources/themes/lara-light-blue/theme.css'  // 테마
// import 'primevue/resources/primevue.min.css'                  // 기본 스타일
// import 'primeicons/primeicons.css'                            // 아이콘

const app = createApp(App);

app.use(router)
app.use(PrimeVue, {
	theme: {
		preset: Aura,
		options: {
			darkModeSelector: ".p-dark",
		}
	},
});

app.mount("#app");
