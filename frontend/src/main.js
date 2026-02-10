import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import VNetworkGraph from "v-network-graph"
import "v-network-graph/lib/style.css"
import './style.css'

const app = createApp(App);
app.use(createPinia());
app.use(Antd);
app.use(ElementPlus);
app.use(VNetworkGraph);

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app');
