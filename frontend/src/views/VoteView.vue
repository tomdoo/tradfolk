<template>
  <section class="screen screen--vote active">
    <div
      v-if="showSwipeTutorial"
      class="swipe-tutorial-overlay"
      aria-hidden="true"
    ></div>

    <div class="progress-row">
      <div class="session-count">{{ progressLabel }}</div>
    </div>

    <div class="card-zone">
      <div
        v-if="errorMessage"
        class="error-banner"
        role="status"
        aria-live="polite"
      >
        {{ errorMessage }}
      </div>

      <div
        v-if="showSwipeTutorial"
        class="swipe-tutorial"
        role="dialog"
        aria-live="polite"
        aria-label="Tutoriel de swipe"
      >
        <div class="swipe-tutorial__title">Comment voter ?</div>
        <p>
          Glisse la carte vers la gauche pour <strong>Trad</strong> et vers la
          droite pour <strong>Folk</strong>.
        </p>
        <div class="swipe-tutorial__legend">
          <span>← Trad</span>
          <span>Folk →</span>
        </div>
        <button
          type="button"
          class="swipe-tutorial__button"
          @click="dismissSwipeTutorial"
        >
          J’ai compris
        </button>
      </div>

      <div v-if="loading" class="done-panel show done-panel--loading">
        <div class="done-media">
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
        <p class="loading-phrase">
          {{ loadingPhrase }}<br />Veuillez patienter...
        </p>
      </div>

      <div v-else-if="done" class="done-panel show">
        <div class="done-media">
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
        <h3>Plus de proposition pour l’instant</h3>
        <p>
          Tu as voté sur toutes les propositions disponibles pour le moment.
          Reviens plus tard pour de nouvelles propositions !
        </p>
        <RouterLink class="next-btn next-btn--ghost" to="/propose"
          >Envoyer une proposition</RouterLink
        >
        <RouterLink class="next-btn" to="/results"
          >Voir les résultats</RouterLink
        >
      </div>

      <div v-else-if="result" class="stats-panel show stats-panel--flip-in">
        <div class="stamp-badge" :class="lastVoteChoice">
          {{ lastVoteLabel }}
        </div>
        <div class="stats-title">{{ proposal?.label }}</div>

        <div class="bar-row">
          <div class="bar-label">
            <span style="color: var(--trad)">Trad</span
            ><span>{{ result.percentages.trad }}%</span>
          </div>
          <div class="bar-track">
            <div
              class="bar-fill trad"
              :style="{ width: `${result.percentages.trad}%` }"
            ></div>
          </div>
        </div>

        <div class="bar-row">
          <div class="bar-label">
            <span style="color: var(--folk-deep)">Folk</span
            ><span>{{ result.percentages.folk }}%</span>
          </div>
          <div class="bar-track">
            <div
              class="bar-fill folk"
              :style="{ width: `${result.percentages.folk}%` }"
            ></div>
          </div>
        </div>

        <div class="votes-total">
          {{ result.counts.trad }} votes trad · {{ result.counts.folk }} votes
          folk
        </div>

        <button class="next-btn" @click="loadRandom">
          Proposition suivante
        </button>
      </div>

      <div
        v-else-if="proposal"
        ref="cardRef"
        class="card"
        :style="cardStyle"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointercancel="resetSwipe"
      >
        <div class="overlay-tag folk" :style="folkOverlayStyle">Folk</div>
        <div class="overlay-tag trad" :style="tradOverlayStyle">Trad</div>

        <div class="card-media card-media--image">
          <img
            v-if="hasDisplayableImage"
            :src="proposal.image"
            :alt="proposal.label"
            @error="handleImageError"
          />
          <div v-else class="card-media__fallback" aria-hidden="true">
            <svg
              viewBox="0 0 64 64"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="10" y="14" width="44" height="36" rx="6" />
              <path d="M18 42l10-11 8 8 6-6 4 4" />
              <circle cx="24" cy="24" r="3" fill="currentColor" stroke="none" />
            </svg>
            <span>Pas d’image</span>
          </div>
        </div>

        <h2 :class="cardTitleClass">{{ proposal.label }}</h2>
      </div>
    </div>

    <div v-if="!result && !done" class="hint-row">
      <div class="hint trad"><span class="swipe-arrow">←</span>Trad</div>
      <div class="hint folk">Folk<span class="swipe-arrow">→</span></div>
    </div>

    <div v-if="!result && !done" class="skip-row">
      <button class="skip-btn" @click="skipProposition">
        passer sans voter →
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api, API_BASE, getApiErrorMessage } from '../api'
import { pickLoadingPhrase, waitForMinimumDelay } from '../loadingState'

const loading = ref(false)
const done = ref(false)
const proposal = ref(null)
const result = ref(null)
const progress = ref({ voted: 0, total: 0, remaining: 0 })
const cardRef = ref(null)
const imageErrored = ref(false)
const swipeStartX = ref(null)
const swipePointerId = ref(null)
const swipeOffsetX = ref(0)
const swipeAnimatingOut = ref(false)
const swipeAnimationDirection = ref(0)
const lastVoteChoice = ref(null)
const loadingPhrase = ref('')
const errorMessage = ref('')
const showSwipeTutorial = ref(false)

const SWIPE_THRESHOLD = 110
const SWIPE_EXIT_DURATION_MS = 260
const SWIPE_TUTORIAL_KEY = 'swipe_tutorial_seen'

const progressLabel = computed(
  () => `${progress.value.voted} / ${progress.value.total} propositions votees`
)

const swipeRatio = computed(() =>
  Math.min(Math.abs(swipeOffsetX.value) / SWIPE_THRESHOLD, 1)
)

const cardStyle = computed(() => ({
  transform: `translateX(${swipeOffsetX.value}px) rotate(${swipeAnimatingOut.value ? swipeAnimationDirection.value * 16 : swipeOffsetX.value / 24}deg)`,
  transition: swipeAnimatingOut.value
    ? `transform ${SWIPE_EXIT_DURATION_MS}ms cubic-bezier(0.22, 0.64, 0.17, 0.98), opacity ${SWIPE_EXIT_DURATION_MS}ms ease`
    : swipeStartX.value === null
      ? 'transform 220ms cubic-bezier(0.22, 0.61, 0.36, 1)'
      : 'none',
  opacity: swipeAnimatingOut.value ? 0.08 : 1,
}))

const folkOverlayStyle = computed(() => {
  if (swipeOffsetX.value <= 0) {
    return { opacity: 0, transform: 'rotate(-14deg) scale(0.85)' }
  }
  return {
    opacity: swipeRatio.value,
    transform: `rotate(-14deg) scale(${0.85 + swipeRatio.value * 0.15})`,
  }
})

const tradOverlayStyle = computed(() => {
  if (swipeOffsetX.value >= 0) {
    return { opacity: 0, transform: 'rotate(14deg) scale(0.85)' }
  }
  return {
    opacity: swipeRatio.value,
    transform: `rotate(14deg) scale(${0.85 + swipeRatio.value * 0.15})`,
  }
})

const lastVoteLabel = computed(() =>
  lastVoteChoice.value === 'trad' ? 'Trad' : 'Folk'
)
const hasDisplayableImage = computed(
  () => Boolean(proposal.value?.image) && !imageErrored.value
)
const cardTitleClass = computed(() => {
  const labelLength = proposal.value?.label?.length ?? 0
  if (labelLength >= 70) {
    return 'card-title--xlong'
  }
  if (labelLength >= 52) {
    return 'card-title--long'
  }
  return ''
})

function getSwipeExitDistance() {
  return Math.max(window.innerWidth + 180, 520)
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function resolveImageUrl(url) {
  if (!url) return url
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return `${API_BASE.replace(/\/$/, '')}${url}`
}

function normalizeProposal(raw) {
  return {
    id: raw.proposal_id || raw.id,
    label: raw.label,
    image: resolveImageUrl(raw.image),
  }
}

function preloadProposalImage(imageUrl) {
  if (!imageUrl) {
    return Promise.resolve(false)
  }

  return new Promise((resolve) => {
    const image = new Image()
    image.onload = () => resolve(true)
    image.onerror = () => resolve(false)
    image.src = imageUrl
  })
}

async function loadProgress() {
  const { data } = await api.get('/progress')
  progress.value = data
}

async function loadRandom() {
  const loadingStartedAt = Date.now()
  loading.value = true
  errorMessage.value = ''
  loadingPhrase.value = pickLoadingPhrase()
  result.value = null
  imageErrored.value = false
  resetSwipe()
  try {
    const [progressResponse, proposalResponse] = await Promise.all([
      api.get('/progress'),
      api.get('/proposals/random'),
    ])
    progress.value = progressResponse.data
    const nextProposal = normalizeProposal(proposalResponse.data)
    const imageReady = await preloadProposalImage(nextProposal.image)
    imageErrored.value = !imageReady && Boolean(nextProposal.image)
    proposal.value = nextProposal
    done.value = false
  } catch (e) {
    if (e?.response?.status === 404) {
      await loadProgress()
      done.value = true
      proposal.value = null
    } else {
      errorMessage.value = getApiErrorMessage(
        e,
        'Impossible de charger une nouvelle proposition'
      )
    }
  } finally {
    await waitForMinimumDelay(loadingStartedAt)
    loading.value = false
  }
}

function handleImageError() {
  imageErrored.value = true
}

async function vote(value) {
  if (!proposal.value) return false
  try {
    errorMessage.value = ''
    lastVoteChoice.value = value
    const { data } = await api.post('/votes', {
      proposal_id: proposal.value.id,
      value,
    })
    result.value = data
    progress.value = {
      ...progress.value,
      voted: Math.min(progress.value.voted + 1, progress.value.total),
      remaining: Math.max(progress.value.remaining - 1, 0),
    }
    return true
  } catch (e) {
    errorMessage.value = getApiErrorMessage(e, 'Erreur lors de l’envoi du vote')
    return false
  }
}

async function swipeOutAndVote(value) {
  if (swipeAnimatingOut.value || loading.value || !proposal.value) {
    return
  }

  const direction = value === 'trad' ? -1 : 1
  swipeAnimatingOut.value = true
  swipeAnimationDirection.value = direction
  swipeOffsetX.value = direction * getSwipeExitDistance()

  await wait(SWIPE_EXIT_DURATION_MS - 30)
  const sent = await vote(value)

  swipeAnimatingOut.value = false
  swipeAnimationDirection.value = 0
  if (!sent) {
    swipeOffsetX.value = 0
  }
}

async function skipProposition() {
  if (loading.value || result.value || swipeAnimatingOut.value) return
  await loadRandom()
}

function resetSwipe() {
  swipeStartX.value = null
  swipePointerId.value = null
  swipeAnimatingOut.value = false
  swipeAnimationDirection.value = 0
  swipeOffsetX.value = 0
}

function dismissSwipeTutorial() {
  showSwipeTutorial.value = false
  localStorage.setItem(SWIPE_TUTORIAL_KEY, '1')
}

function handlePointerDown(event) {
  if (result.value || loading.value || swipeAnimatingOut.value) return
  if (showSwipeTutorial.value) {
    dismissSwipeTutorial()
  }
  swipeStartX.value = event.clientX
  swipePointerId.value = event.pointerId
  event.currentTarget.setPointerCapture(event.pointerId)
}

function handlePointerMove(event) {
  if (
    swipePointerId.value !== event.pointerId ||
    swipeStartX.value === null ||
    result.value ||
    swipeAnimatingOut.value
  ) {
    return
  }
  swipeOffsetX.value = event.clientX - swipeStartX.value
}

function handlePointerUp(event) {
  if (
    swipePointerId.value !== event.pointerId ||
    swipeStartX.value === null ||
    result.value
  ) {
    resetSwipe()
    return
  }

  if (event.currentTarget.hasPointerCapture(event.pointerId)) {
    event.currentTarget.releasePointerCapture(event.pointerId)
  }

  const deltaX = event.clientX - swipeStartX.value
  swipeStartX.value = null
  swipePointerId.value = null

  if (deltaX <= -SWIPE_THRESHOLD) {
    swipeOutAndVote('trad')
  } else if (deltaX >= SWIPE_THRESHOLD) {
    swipeOutAndVote('folk')
  } else {
    swipeOffsetX.value = 0
  }
}

onMounted(async () => {
  showSwipeTutorial.value = localStorage.getItem(SWIPE_TUTORIAL_KEY) !== '1'
  await loadRandom()
})
</script>
