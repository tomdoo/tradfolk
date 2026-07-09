import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import VoteView from './views/VoteView.vue'
import ResultsView from './views/ResultsView.vue'
import DisclaimerView from './views/DisclaimerView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: VoteView },
    { path: '/results', component: ResultsView },
    { path: '/disclaimer', component: DisclaimerView },
  ],
})

createApp(App).use(router).mount('#app')
