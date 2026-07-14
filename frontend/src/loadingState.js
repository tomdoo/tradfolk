export const MIN_LOADING_MS = 2000

const LOADING_PHRASES = [
  'Changement du fût en cours.',
  'Les musiciens se mettent d’accord pour la tonalité.',
  'On accorde les violons et les esprits.',
  'Le bal va commencer.',
  'Une dernière mise au point avant la prochaine ronde.',
  'Cirage des chaussures en cours.',
  'Pose du parquet en cours.',
  'Dispersion du talc.',
  'On vérifie les cordes de l’accordéon.',
  'C’est le rush à la buvette.',
  'L’interplateau est un peu mou.',
  'Bientôt le début du bœuf.',
  'Annulation du Son Continu.',
  'Les vielles s’accordent (encore).',
  'Réparation du parquet de sautière en cours.',
  'Le pilé-menu de Fleuves vient de commencer.',
  'Il y a du monde à la douche.',
  'Contrôle sécurité du Son Continu.',
  'Balances en cours.',
  'Repiage de la tente 2 secondes en cours',
  'Remplaillage de Bijou en cours.',
]

export function pickLoadingPhrase() {
  return LOADING_PHRASES[Math.floor(Math.random() * LOADING_PHRASES.length)]
}

export async function waitForMinimumDelay(
  startedAt,
  minDelayMs = MIN_LOADING_MS
) {
  const elapsed = Date.now() - startedAt
  const remainingDelay = Math.max(minDelayMs - elapsed, 0)
  if (remainingDelay <= 0) {
    return
  }

  await new Promise((resolve) => {
    window.setTimeout(resolve, remainingDelay)
  })
}
