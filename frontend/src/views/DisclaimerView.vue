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
        aider de manière simple et concrète :
      </p>

      <ul class="contrib-list">
        <li>
          <span class="contrib-label">✍️ En proposant</span>
          <span class="contrib-text">
            Une idée de proposition à ajouter ? Il faut juste un titre et une
            image. Envoie le tout via
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

      <p>
        🍪 Cette application utilise un cookie. Un seul. Il est bon, plein de
        beurre et retient juste tes votes. Pas de pub, pas de tracking, pas de
        dark pattern, pas de mystère.
      </p>

      <p>
        🕋 Les données sont hébergées en France, dans un datacenter du côté de
        Strasbourg. Il n'est pas prévu d'utiliser les données personnelles à
        d'autres fins que de la modération de contenu.
      </p>

      <div class="credit-line">ALORS, TRAD OU FOLK ?</div>
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
