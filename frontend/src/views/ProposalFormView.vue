<template>
  <section class="screen screen--proposal active">
    <div class="proposal-scroll">
      <div class="proposal-hero">
        <h2>Envoyer une proposition</h2>
        <p>
          Remplis ce formulaire pour soumettre une nouvelle proposition. Une
          fois envoyée il te sera demandé de la valider par email.
        </p>
      </div>

      <div v-if="submissionDone" class="proposal-success">
        <h3>Proposition envoyee</h3>
        <p>{{ successMessage }}</p>
        <button type="button" class="next-btn" @click="resetFormFlow">
          Envoyer une nouvelle proposition
        </button>
      </div>

      <div v-if="!submissionDone">
        <div v-show="verifying" class="proposal-verify">
          <div class="proposal-preview-card">
            <div class="card-media card-media--image">
              <img
                v-if="imagePreviewUrl"
                :src="imagePreviewUrl"
                :alt="form.proposal"
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
                  <circle
                    cx="24"
                    cy="24"
                    r="3"
                    fill="currentColor"
                    stroke="none"
                  />
                </svg>
                <span>Pas d'image</span>
              </div>
            </div>
            <h2 :class="cardTitleClass">{{ form.proposal }}</h2>
          </div>

          <p
            v-if="feedbackMessage"
            class="proposal-feedback"
            role="status"
            aria-live="polite"
          >
            {{ feedbackMessage }}
          </p>

          <button
            type="button"
            class="next-btn proposal-submit-btn"
            :disabled="!canSubmit"
            @click="doActualSubmit"
          >
            Envoyer la proposition
          </button>

          <button
            type="button"
            class="next-btn next-btn--ghost proposal-modify-btn"
            @click="backToForm"
          >
            Modifier
          </button>
        </div>

        <form
          v-show="!verifying"
          class="proposal-form"
          @submit.prevent="handleSubmit"
        >
          <label class="proposal-field">
            <span>Email</span>
            <input
              v-model.trim="form.email"
              type="email"
              name="email"
              autocomplete="email"
              placeholder="toi@exemple.fr"
              required
            />
          </label>

          <label class="proposal-field">
            <span>Nom</span>
            <input
              v-model.trim="form.name"
              type="text"
              name="name"
              autocomplete="name"
              placeholder="Ton nom"
              required
            />
          </label>

          <label class="proposal-field">
            <span>Proposition</span>
            <textarea
              v-model.trim="form.proposal"
              name="proposal"
              rows="4"
              placeholder="Exemple: Avoir chaud en été"
              required
            ></textarea>
          </label>

          <label class="proposal-field">
            <span>Image</span>
            <input
              ref="imageInput"
              type="file"
              name="image"
              accept="image/*"
              required
              @change="handleImageFile"
            />
          </label>

          <p
            v-if="feedbackMessage"
            class="proposal-feedback"
            role="status"
            aria-live="polite"
          >
            {{ feedbackMessage }}
          </p>

          <button
            type="submit"
            class="next-btn proposal-submit-btn"
            :disabled="submitting"
          >
            Vérifier
          </button>
        </form>
      </div>

      <div
        v-if="hasSiteKey && !submissionDone"
        ref="turnstileContainer"
        class="proposal-captcha proposal-captcha--invisible"
        aria-hidden="true"
      ></div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { api, getApiErrorMessage } from '../api'

const TURNSTILE_SCRIPT_ID = 'cf-turnstile-script'
const siteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY || ''
const hasSiteKey = computed(() => Boolean(siteKey))

const form = reactive({
  email: '',
  name: '',
  proposal: '',
})

const imageFile = ref(null)
const imageInput = ref(null)
const imagePreviewUrl = ref('')

const feedbackMessage = ref('')
const successMessage = ref('')
const submissionDone = ref(false)
const submitting = ref(false)
const verifying = ref(false)
const turnstileContainer = ref(null)
const turnstileWidgetId = ref(null)
const captchaToken = ref('')
const captchaPending = ref(false)
const pendingSubmit = ref(false)

const canSubmit = computed(
  () => hasSiteKey.value && !captchaPending.value && !submitting.value
)

const cardTitleClass = computed(() => {
  const labelLength = form.proposal?.length ?? 0
  if (labelLength >= 70) return 'card-title--xlong'
  if (labelLength >= 52) return 'card-title--long'
  return ''
})

function loadTurnstileScript() {
  if (window.turnstile) {
    return Promise.resolve()
  }

  return new Promise((resolve, reject) => {
    const existingScript = document.getElementById(TURNSTILE_SCRIPT_ID)
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(), { once: true })
      existingScript.addEventListener(
        'error',
        () => reject(new Error('Impossible de charger Turnstile')),
        { once: true }
      )
      return
    }

    const script = document.createElement('script')
    script.id = TURNSTILE_SCRIPT_ID
    script.src =
      'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Impossible de charger Turnstile'))
    document.head.appendChild(script)
  })
}

function renderTurnstile() {
  if (!hasSiteKey.value || !turnstileContainer.value || !window.turnstile) {
    return
  }
  if (turnstileWidgetId.value !== null) {
    return
  }

  turnstileWidgetId.value = window.turnstile.render(turnstileContainer.value, {
    sitekey: siteKey,
    size: 'invisible',
    execution: 'execute',
    callback: (token) => {
      captchaToken.value = token
      captchaPending.value = false
      feedbackMessage.value = ''
      if (pendingSubmit.value) {
        pendingSubmit.value = false
        completeSubmit()
      }
    },
    'expired-callback': () => {
      captchaToken.value = ''
      captchaPending.value = false
      pendingSubmit.value = false
    },
    'error-callback': () => {
      captchaToken.value = ''
      captchaPending.value = false
      pendingSubmit.value = false
      feedbackMessage.value = 'Le captcha a echoue. Merci de reessayer.'
    },
  })
}

onMounted(async () => {
  if (!hasSiteKey.value) {
    return
  }
  try {
    await loadTurnstileScript()
    renderTurnstile()
  } catch {
    feedbackMessage.value = 'Impossible de charger le captcha pour le moment.'
  }
})

onBeforeUnmount(() => {
  if (turnstileWidgetId.value !== null && window.turnstile) {
    window.turnstile.remove(turnstileWidgetId.value)
    turnstileWidgetId.value = null
  }
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }
})

function handleImageFile(e) {
  imageFile.value = e.target.files?.[0] ?? null
}

function handleSubmit() {
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }
  imagePreviewUrl.value = imageFile.value
    ? URL.createObjectURL(imageFile.value)
    : ''
  feedbackMessage.value = ''
  verifying.value = true
}

function backToForm() {
  verifying.value = false
  feedbackMessage.value = ''
}

function doActualSubmit() {
  if (!hasSiteKey.value) {
    feedbackMessage.value =
      'Captcha non configure: definir VITE_TURNSTILE_SITE_KEY pour activer la soumission.'
    return
  }

  if (!window.turnstile || turnstileWidgetId.value === null) {
    feedbackMessage.value =
      'Captcha indisponible pour le moment. Merci de reessayer.'
    return
  }

  if (captchaPending.value) return

  pendingSubmit.value = true
  captchaPending.value = true
  captchaToken.value = ''
  feedbackMessage.value = ''
  window.turnstile.execute(turnstileWidgetId.value)
}

async function completeSubmit() {
  if (!captchaToken.value) {
    feedbackMessage.value = 'Validation captcha invalide. Merci de reessayer.'
    return
  }

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('email', form.email)
    formData.append('name', form.name)
    formData.append('proposal', form.proposal)
    formData.append('turnstileToken', captchaToken.value)
    if (imageFile.value) {
      formData.append('image', imageFile.value)
    }

    const { data } = await api.post('/proposals', formData)

    successMessage.value =
      data?.message ||
      'Ta proposition a bien été reçue. Vérifie tes emails pour la valider.'
    submissionDone.value = true
    verifying.value = false
    feedbackMessage.value = ''

    if (imagePreviewUrl.value) {
      URL.revokeObjectURL(imagePreviewUrl.value)
      imagePreviewUrl.value = ''
    }

    form.email = ''
    form.name = ''
    form.proposal = ''
    imageFile.value = null
    if (imageInput.value) imageInput.value.value = ''
  } catch (error) {
    feedbackMessage.value = getApiErrorMessage(
      error,
      "Impossible d'envoyer la proposition pour le moment."
    )
  } finally {
    submitting.value = false
    pendingSubmit.value = false

    if (turnstileWidgetId.value !== null && window.turnstile) {
      window.turnstile.reset(turnstileWidgetId.value)
    }
    captchaToken.value = ''
    captchaPending.value = false
  }
}

function resetFormFlow() {
  submissionDone.value = false
  successMessage.value = ''
  feedbackMessage.value = ''

  if (turnstileWidgetId.value !== null && window.turnstile) {
    window.turnstile.reset(turnstileWidgetId.value)
  }
}
</script>
