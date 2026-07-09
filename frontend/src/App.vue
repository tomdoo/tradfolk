<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentTab = computed(() => {
  if (route.path.startsWith('/results')) {
    return 'results'
  }
  if (route.path.startsWith('/disclaimer')) {
    return 'about'
  }
  return 'vote'
})
</script>

<template>
  <div class="app-page">
    <div class="app-device">
      <header class="topbar">
        <div class="brand">
          <div class="title">Trad <em>ou</em> Folk ?</div>
          <div class="sub">le débat éternel du bal</div>
        </div>

        <RouterLink class="icon-btn" to="/disclaimer" aria-label="A propos">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <circle cx="12" cy="12" r="9.5" />
            <line x1="12" y1="11" x2="12" y2="16.5" />
            <circle cx="12" cy="7.5" r="0.6" fill="currentColor" />
          </svg>
        </RouterLink>
      </header>

      <main class="screen-shell">
        <RouterView />
      </main>

      <nav class="bottom-nav" aria-label="Navigation principale">
        <RouterLink
          to="/"
          class="nav-btn"
          :class="{ active: currentTab === 'vote' }"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M12 3l2.4 4.9 5.4.8-3.9 3.8.9 5.4L12 15.3 7.2 17.9l.9-5.4L4.2 8.7l5.4-.8z"
            />
          </svg>
          <span>Voter</span>
        </RouterLink>

        <RouterLink
          to="/results"
          class="nav-btn"
          :class="{ active: currentTab === 'results' }"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="5" y1="20" x2="5" y2="11" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="19" y1="20" x2="19" y2="14" />
          </svg>
          <span>Resultats</span>
        </RouterLink>

        <RouterLink
          to="/disclaimer"
          class="nav-btn"
          :class="{ active: currentTab === 'about' }"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <circle cx="12" cy="12" r="9.5" />
            <line x1="12" y1="11" x2="12" y2="16.5" />
            <circle cx="12" cy="7.5" r="0.6" fill="currentColor" />
          </svg>
          <span>A propos</span>
        </RouterLink>
      </nav>
    </div>
  </div>
</template>
