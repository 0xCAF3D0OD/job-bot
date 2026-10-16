<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

import DiscoverMock, { type MockKind } from "../components/DiscoverMock.vue";
import Illustration, { type IllustrationName } from "../components/Illustration.vue";
import { useAuth } from "../composables/useAuth";

// La plateforme, pour qui n'est pas connecté (docs/67, compléments) : un parcours façon Duolingo.
// Un chemin relie les étapes ; chaque scène montre un bout de la plateforme en arrière-plan, un
// personnage devant, et sa bulle qui explique. Le chemin se colore à mesure qu'on descend.
// L'accès se fait sur invitation (docs/65).
const { loggedIn } = useAuth();

const SCENES: { art: IllustrationName; mock: MockKind; title: string; text: string }[] = [
  {
    art: "alertes-carte",
    mock: "alerts",
    title: "Tes alertes, une fois pour toutes",
    text: "Crée tes alertes sur jobup.ch ou Indeed : les offres arrivent ici, au même endroit, sans doublons.",
  },
  {
    art: "offres-profils",
    mock: "offers",
    title: "Les bonnes offres d'abord",
    text: "Chaque offre reçoit une note selon ce que tu cherches et ton profil : les meilleures en tête.",
  },
  {
    art: "suivi-envoi",
    mock: "apply",
    title: "Ta candidature préparée",
    text: "Une lettre et un CV adaptés à l'offre. Tu relis, tu corriges, tu envoies toi-même.",
  },
  {
    art: "tableau-de-bord",
    mock: "follow",
    title: "Le suivi, sans rien oublier",
    text: "Réponses, entretiens, relances : tout est daté, et la plateforme te rappelle ce qui attend.",
  },
  {
    art: "preuves-orp",
    mock: "orp",
    title: "Tes preuves ORP prêtes",
    text: "Chaque mois, la liste de tes recherches est prête à remettre à l'ORP, avant la date limite.",
  },
  {
    art: "formations",
    mock: "news",
    title: "Ton métier, et ce qui bouge",
    text: "Les actualités et les formations de ton domaine, triées pour toi.",
  },
];

// Le chemin passe par les pastilles numérotées ; il est recalculé quand la page change de largeur.
const journey = ref<HTMLElement | null>(null);
const path = ref("");
const length = ref(0);
const progress = ref(0);
const reached = ref(0);
const shown = ref<boolean[]>(SCENES.map(() => false));
const line = ref<SVGPathElement | null>(null);

function trace(): void {
  const box = journey.value?.getBoundingClientRect();
  if (!box) return;
  const points = [...journey.value!.querySelectorAll<HTMLElement>(".discover-node")].map((node) => {
    const r = node.getBoundingClientRect();
    return { x: r.left + r.width / 2 - box.left, y: r.top + r.height / 2 - box.top };
  });
  path.value = points
    .map((p, i) => {
      if (i === 0) return `M ${p.x} ${p.y}`;
      const prev = points[i - 1]!;
      const bend = (p.y - prev.y) * 0.55;
      return `C ${prev.x} ${prev.y + bend}, ${p.x} ${p.y - bend}, ${p.x} ${p.y}`;
    })
    .join(" ");
  void nextTick(() => {
    // jsdom ne mesure pas les tracés : sans mesure, le chemin reste en pointillés.
    length.value = typeof line.value?.getTotalLength === "function" ? line.value.getTotalLength() : 0;
    follow();
  });
}

// La part du chemin parcourue suit le milieu de l'écran ; les pastilles dépassées se remplissent.
function follow(): void {
  const box = journey.value?.getBoundingClientRect();
  if (!box) return;
  const middle = window.innerHeight * 0.6 - box.top;
  progress.value = Math.max(0, Math.min(1, middle / box.height));
  const nodes = [...journey.value!.querySelectorAll<HTMLElement>(".discover-node")];
  reached.value = nodes.filter((n) => n.getBoundingClientRect().top + n.offsetHeight / 2 < window.innerHeight * 0.6).length;
}

let resize: ResizeObserver | null = null;
let reveal: IntersectionObserver | null = null;
onMounted(() => {
  trace();
  resize = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(trace);
  if (journey.value) resize?.observe(journey.value);
  window.addEventListener("scroll", follow, { passive: true });
  // Chaque scène entre une fois, quand elle arrive à l'écran.
  if (typeof IntersectionObserver === "undefined") {
    shown.value = SCENES.map(() => true);
    return;
  }
  reveal = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        shown.value[Number((entry.target as HTMLElement).dataset.index)] = true;
        reveal?.unobserve(entry.target);
      }
    },
    { threshold: 0.2 },
  );
  journey.value?.querySelectorAll(".discover-scene").forEach((scene) => reveal?.observe(scene));
});
onBeforeUnmount(() => {
  resize?.disconnect();
  reveal?.disconnect();
  window.removeEventListener("scroll", follow);
});
</script>

<template>
  <article
    class="discover"
    data-test="discover"
  >
    <header class="discover-hero">
      <Illustration
        name="porte-ouverte"
        class="discover-hero-art"
      />
      <h1>Less searching. More living.</h1>
      <p class="discover-lead">
        jobA1 t'aide à chercher un emploi en Suisse et à prouver tes recherches à l'ORP, sans y passer tes journées.
      </p>
      <RouterLink
        v-if="!loggedIn"
        to="/connexion"
        class="button-link primary-link"
        data-test="discover-login"
      >
        Se connecter
      </RouterLink>
      <p
        v-if="!loggedIn"
        class="hint"
      >
        L'accès se fait sur invitation.
      </p>
    </header>

    <h2 class="discover-title">
      Comment ça marche
    </h2>

    <div
      ref="journey"
      class="discover-journey"
    >
      <svg
        class="discover-path"
        aria-hidden="true"
      >
        <path
          class="discover-path-base"
          :d="path"
        />
        <path
          ref="line"
          class="discover-path-done"
          :d="path"
          :style="{ strokeDasharray: length, strokeDashoffset: length * (1 - progress) }"
        />
      </svg>

      <ol class="discover-scenes">
        <li
          v-for="(scene, i) in SCENES"
          :key="scene.art"
          :class="['discover-scene', { shown: shown[i], flip: i % 2 === 1 }]"
          :data-index="i"
        >
          <div class="discover-stage">
            <DiscoverMock :kind="scene.mock" />
            <Illustration
              :name="scene.art"
              class="discover-character"
            />
          </div>
          <div class="discover-say">
            <span :class="['discover-node', { reached: i < reached }]">{{ i + 1 }}</span>
            <div class="discover-bubble">
              <h3>{{ scene.title }}</h3>
              <p>{{ scene.text }}</p>
            </div>
          </div>
        </li>
        <li
          class="discover-scene discover-end shown"
          data-index="6"
        >
          <div class="discover-say">
            <span :class="['discover-node', 'goal', { reached: reached > SCENES.length }]">★</span>
            <div class="discover-data">
              <h2>Tes données restent à toi</h2>
              <p>
                Ton compte est séparé de ceux des autres. Tu peux tout exporter, ou supprimer ton compte. Tes coordonnées et
                les noms de tes contacts ne partent jamais à l'IA.
              </p>
              <RouterLink to="/tes-donnees">
                Ce qui est gardé, et ce qui part à l'IA
              </RouterLink>
              <RouterLink
                v-if="!loggedIn"
                to="/connexion"
                class="button-link primary-link discover-end-login"
              >
                Se connecter
              </RouterLink>
            </div>
          </div>
        </li>
      </ol>
    </div>
  </article>
</template>
