<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";

// À propos (docs/126 §4) : pourquoi jobA1, ce qu'il promet, qui est derrière. Publique, comme
// Données personnelles. Le texte « Pourquoi » est un premier jet, à relire par l'exploitant.
const contact = ref<string | null>(null);

onMounted(async () => {
  const { data } = await api.GET("/api/privacy");
  contact.value = data?.contact ?? null;
});
</script>

<template>
  <PageHero title="À propos" />
  <section class="band">
    <div
      class="container narrow privacy-page"
      data-test="about"
    >
      <h2>Pourquoi jobA1</h2>
      <p>
        Chercher un emploi, c'est trouver les bonnes offres et prouver chaque mois ses recherches. jobA1 s'occupe des preuves et t'aide pour les offres.
      </p>

      <h2>Ce que jobA1 promet</h2>
      <ul>
        <li>Le suivi de tes candidatures et tes preuves ORP restent gratuits, sans limite.</li>
        <li>Tes coordonnées ne partent jamais à l'IA.</li>
        <li>jobA1 ne postule jamais à ta place et ne se connecte pas à tes comptes sur les sites d'emploi.</li>
        <li>
          <RouterLink to="/tes-donnees">
            Données personnelles
          </RouterLink> : ce qui est gardé, et pour combien de temps.
        </li>
      </ul>

      <h2>Qui est derrière</h2>
      <p>jobA1 est conçu et développé par Kevin Di Nocera.</p>
      <p
        v-if="contact"
        class="privacy-contact"
        data-test="about-contact"
      >
        {{ contact }}
      </p>

      <h2>Le code</h2>
      <p>
        Le code de jobA1 est public : chacun peut le lire et vérifier ce qu'il fait.
        <a
          href="https://github.com/0xCAF3D0OD/job-bot"
          target="_blank"
          rel="noopener noreferrer"
        ><span class="with-icon">Voir le code<AppIcon name="external" /></span><span class="visually-hidden"> (nouvel onglet)</span></a>
      </p>
    </div>
  </section>
</template>
