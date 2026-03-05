import { createApp } from "vue";
import App from "./App.vue";
import { vuetify } from "./plugins/vuetify";
import "./styles.css";

createApp(App).use(vuetify).mount("#app");
