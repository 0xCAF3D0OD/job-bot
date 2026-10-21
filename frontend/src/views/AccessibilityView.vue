<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import PageHero from "../components/PageHero.vue";

// Accessibilité (docs/117 §1) : ce qui est vérifié, ce qui ne l'est pas encore, la dictée, et
// à qui signaler un problème. Publique, comme Données personnelles.
const contact = ref<string | null>(null);

onMounted(async () => {
  const { data } = await api.GET("/api/privacy");
  contact.value = data?.contact ?? null;
});
</script>

<template>
  <PageHero title="Accessibilité" />
  <section class="band">
    <div class="container narrow privacy-page">
      <h2>Ce qui est vérifié</h2>
      <ul>
        <li>Chaque page principale, sur ordinateur et sur téléphone, par axe-core (règles WCAG 2.1 AA), avant chaque version.</li>
        <li>Les contrastes des couleurs, en clair et en sombre.</li>
        <li>Un parcours au clavier : ouvrir une offre et la corriger, sans souris.</li>
        <li>« Réduire les animations » : rien ne bouge.</li>
      </ul>

      <h2>Pas encore vérifié</h2>
      <ul>
        <li>Un essai complet avec un lecteur d'écran (VoiceOver, NVDA).</li>
        <li>L'extension du navigateur.</li>
      </ul>

      <h2>Dicter</h2>
      <p>Sur téléphone, le micro de ton clavier dicte dans tous les champs.</p>

      <h2>Signaler un problème</h2>
      <p
        v-if="contact"
        class="privacy-contact"
        data-test="accessibility-contact"
      >
        {{ contact }}
      </p>
      <p
        v-else
        class="hint"
      >
        L'exploitant de la plateforme n'a pas encore indiqué ses coordonnées.
      </p>
    </div>
  </section>
</template>
