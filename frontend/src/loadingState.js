export const MIN_LOADING_MS = 2000

const LOADING_PHRASES = [
  "Changement du f\xfbt en cours...",
  "Les musiciens se mettent d'accord pour la tonalit\xe9...",
  "On accorde les violons et les esprits...",
  "Le bal va commencer !",
  "Une derni\xe8re mise au point avant la prochaine ronde...",
  "Cirage des chaussures en cours...",
  "Pose du parquet en cours...",
  "Vous avez pens\xe9 au talc ?",
  "On v\xe9rifie les cordes de l'accord\xe9on...",
  "Patientez, c'est le rush \xe0 la buvette...",
  "L'interplateau est un peu mou...",
  "Bient\xf4t le d\xe9but du b\u0153uf...",
  "Annulation du Son Continu, veuillez patienter...",
]

export function pickLoadingPhrase() {
  return LOADING_PHRASES[Math.floor(Math.random() * LOADING_PHRASES.length)]
}

export async function waitForMinimumDelay(startedAt, minDelayMs = MIN_LOADING_MS) {
  const elapsed = Date.now() - startedAt
  const remainingDelay = Math.max(minDelayMs - elapsed, 0)
  if (remainingDelay <= 0) {
    return
  }

  await new Promise((resolve) => {
    window.setTimeout(resolve, remainingDelay)
  })
}
