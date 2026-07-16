<template>
  <section class="screen screen--results active">
    <div class="results-header-row">
      <div class="sub-pill">
        <div>{{ items.length }} propositions</div>
        <div>{{ totalVotes }} {{ totalVotes > 1 ? 'votes' : 'vote' }}</div>
      </div>
      <select v-model="sortMode" class="sort-select">
        <option value="order">Ordre alphabétique</option>
        <option value="trad">Plutôt trad</option>
        <option value="folk">Plutôt folk</option>
      </select>
    </div>

    <div v-if="loading" class="results-empty-state">
      <h3>Chargement des résultats</h3>
      <div class="results-loading-card" role="status" aria-live="polite">
        <div class="results-loading-media" aria-hidden="true">
          <svg
            viewBox="0 0 64 64"
            fill="none"
            stroke="currentColor"
            stroke-width="2.2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="32" cy="32" r="22" />
            <path d="M32 20v13l9 6" />
          </svg>
        </div>
        <p>{{ loadingPhrase }}<br />Veuillez patienter...</p>
      </div>
    </div>

    <div v-else-if="errorMessage" class="results-empty-state">
      <h3>Résultats indisponibles</h3>
      <p>{{ errorMessage }}</p>
    </div>

    <div v-else-if="sortedItems.length === 0" class="results-empty-state">
      <h3>Pas encore de résultats</h3>
      <p>
        Les propositions apparaitront ici dès que les premiers votes seront
        enregistrés.
      </p>
    </div>

    <div v-else class="results-scroll">
      <article v-for="item in sortedItems" :key="item.id" class="result-card">
        <div class="result-top">
          <div class="result-name">{{ item.label }}</div>
          <div class="result-winner" :class="winnerClass(item)">
            {{ winnerLabel(item) }}
          </div>
        </div>

        <div class="mini-bar">
          <div
            class="mini-fill trad"
            :style="{ width: `${item.percentages.trad}%` }"
          ></div>
          <div
            class="mini-fill folk"
            :style="{ width: `${item.percentages.folk}%` }"
          ></div>
        </div>

        <div class="result-stats-row">
          <span
            >Trad {{ item.percentages.trad }}% · {{ item.counts.trad }}</span
          >
          <span
            >Folk {{ item.percentages.folk }}% · {{ item.counts.folk }}</span
          >
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { api, getApiErrorMessage } from '../api'
import { pickLoadingPhrase, waitForMinimumDelay } from '../loadingState'

const loading = ref(false)
const items = ref([])
const sortMode = ref('order')
const errorMessage = ref('')
const loadingPhrase = ref('')

const sortedItems = computed(() => {
  const list = [...items.value]
  if (sortMode.value === 'trad') {
    return list.sort(
      (left, right) => right.percentages.trad - left.percentages.trad
    )
  }
  if (sortMode.value === 'folk') {
    return list.sort(
      (left, right) => right.percentages.folk - left.percentages.folk
    )
  }
  return list
})

const totalVotes = computed(() => {
  return items.value.reduce((sum, item) => {
    const itemTotal =
      item.counts?.total ?? item.counts?.trad + item.counts?.folk
    return sum + (Number.isFinite(itemTotal) ? itemTotal : 0)
  }, 0)
})

function normalizeResult(raw) {
  return {
    id: raw.proposal_id || raw.id,
    label: raw.label,
    image: raw.image,
    counts: raw.counts,
    percentages: raw.percentages,
  }
}

function winnerClass(item) {
  return item.percentages.trad === item.percentages.folk
    ? 'consensus'
    : item.percentages.trad >= item.percentages.folk
      ? 'trad'
      : 'folk'
}

function winnerLabel(item) {
  return item.percentages.trad === item.percentages.folk
    ? 'Plutôt consensuel'
    : item.percentages.trad >= item.percentages.folk
      ? 'Plutôt trad'
      : 'Plutôt folk'
}

onMounted(async () => {
  const loadingStartedAt = Date.now()
  loading.value = true
  errorMessage.value = ''
  loadingPhrase.value = pickLoadingPhrase()
  try {
    const { data } = await api.get('/results')
    items.value = data.map(normalizeResult)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      'Impossible de recuperer les resultats'
    )
  } finally {
    await waitForMinimumDelay(loadingStartedAt)
    loading.value = false
  }
})
</script>
