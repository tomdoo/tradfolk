<template>
  <section class="screen screen--proposal active">
    <div class="proposal-scroll">
      <div class="proposal-hero">
        <h2>Envoyer une proposition</h2>
        <p>
          Remplis ce formulaire pour soumettre une nouvelle proposition. Une
          fois envoyée, il te sera demandé de la valider par email. Ton nom et
          ton email ne seront pas partagés publiquement ni utilisés à d'autres
          fins, mais ils sont nécessaires pour que nous puissions te contacter
          si besoin.
        </p>
      </div>

      <div v-if="submissionDone" class="proposal-success">
        <h3>Proposition envoyée</h3>
        <p>{{ successMessage }}</p>
        <button type="button" class="next-btn" @click="resetFormFlow">
          Envoyer une nouvelle proposition
        </button>
      </div>

      <form v-else class="proposal-form" @submit.prevent="handleSubmit">
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
          :disabled="!canSubmit"
        >
          Envoyer la proposition
        </button>

        <div
          v-if="hasSiteKey"
          ref="turnstileContainer"
          class="proposal-captcha proposal-captcha--invisible"
          aria-hidden="true"
        ></div>
      </form>
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

const feedbackMessage = ref('')
const successMessage = ref('')
const submissionDone = ref(false)
const submitting = ref(false)
const turnstileContainer = ref(null)
const turnstileWidgetId = ref(null)
const captchaToken = ref('')
const captchaPending = ref(false)
const pendingSubmit = ref(false)

const canSubmit = computed(
  () => hasSiteKey.value && !captchaPending.value && !submitting.value
)

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
      feedbackMessage.value = 'Le captcha a échoué. Merci de réessayer.'
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
})

function handleImageFile(e) {
  imageFile.value = e.target.files?.[0] ?? null
}

function handleSubmit() {
  if (!hasSiteKey.value) {
    feedbackMessage.value =
      'Captcha non configure: definir VITE_TURNSTILE_SITE_KEY pour activer la soumission.'
    return
  }

  if (!window.turnstile || turnstileWidgetId.value === null) {
    feedbackMessage.value =
      'Captcha indisponible pour le moment. Merci de réessayer.'
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
    feedbackMessage.value = 'Validation captcha invalide. Merci de réessayer.'
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
    feedbackMessage.value = ''

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
