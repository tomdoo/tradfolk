<template>
  <section class="screen screen--about active">
    <div class="about-scroll">
      <div class="about-hero">
        « C’est pas trad ça, c’est folk ! » <br />
        — Là où tout commence.
      </div>

      <p>
        <strong>Trad ou Folk ?</strong> ne tranche pas le débat, il le met en
        scène. Une proposition apparaît, tu glisses la carte à gauche si tu
        penses <strong>Trad</strong>, à droite si tu penses
        <strong>Folk</strong>.
      </p>

      <p>
        Il n’y a pas de bonne ou de mauvaise réponse : les statistiques
        affichées après chaque vote reflètent simplement l’opinion collective,
        telle qu’elle évolue au fil des passages.
      </p>

      <p>Swipe honnête, débat éternel : à toi de voter !</p>

      <p>
        Ce projet existe grâce à la communauté. Si tu aimes l’idée, tu peux
        aider de trois façons, simples et concrètes :
      </p>

      <ul class="contrib-list">
        <li>
          <span class="contrib-label">💛 Financièrement</span>
          <span class="contrib-text">
            L’hébergement coûte 5,39&nbsp;€/mois et le nom de domaine
            5,99&nbsp;€/an, soit environ <strong>70,67&nbsp;€/an</strong>.
            Chaque soutien, même modeste, aide à garder le site en ligne et
            libre d’accès. Pour le moment, tu peux remonter jusqu'à la personne
            qui héberge le site pour s'arranger directement.
          </span>
        </li>
        <li>
          <span class="contrib-label">✍️ En proposant</span>
          <span class="contrib-text">
            Envoie-nous une proposition à ajouter : un titre et une image si tu
            en as une. Envoie le tout via
            <RouterLink to="/propose">ce formulaire</RouterLink>.
          </span>
        </li>
        <li>
          <span class="contrib-label">🛠️ Sur GitHub</span>
          <span class="contrib-text">
            Idées, bugs, corrections, nouvelles fonctions : tout est bienvenu.
            Passe sur
            <a
              href="https://github.com/tomdoo/tradfolk"
              target="_blank"
              rel="noopener noreferrer"
              >GitHub</a
            >.
          </span>
        </li>
      </ul>

      <p>
        Merci de faire vivre ce débat avec nous. Ici, on ne cherche pas à
        trancher une vérité : on cultive des points de vue.
      </p>

      <div class="credit-line">ALORS, TRAD OU FOLK ?</div>
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
