/**
 * 前端应用入口文件 (Main Entry)
 * 初始化 Vue 实例，挂载 Pinia 状态管理库，并引入 Tailwind 等全局 CSS
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles/index.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
