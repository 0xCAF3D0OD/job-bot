<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { dayMonthShort } from "../dates";
import BrandMark from "./BrandMark.vue";
import IconButton from "./IconButton.vue";

// « Première candidature notée » (section 44 du 17.11, planches AccueilPremiereCandidature et
// AujourdhuiOrdinateurPremiereCandidature, avec leurs versions sombres). Une carte posée en bas, sans voile : l'app
// reste utilisable. Le logo dans un rond avec quatre points de couleur, le titre, « {Entreprise} · {date courte} »
// (Kevin, 17.11), la barre du mois ORP (les candidatures d'avant en bleu, la nouvelle en pêche), puis « Voir », qui
// ouvre la candidature. role="status", sans prendre le focus ; affichée une seule fois (le serveur le retient).
// Elle ne disparaît jamais seule (Kevin, 17.11 : elle contient une action, WCAG 2.2.1) : elle reste jusqu'à « Fermer »,
// Échap, ou la sortie de la page. Aucun minuteur.
const props = defineProps<{ company: string; sentAt: string; applicationId: number; count: number; target: number | null }>();
const emit = defineEmits<{ close: [] }>();

// Un segment par candidature de l'objectif ; la dernière comptée est la nouvelle. Sans objectif réglé, ni barre ni
// « sur N » (aucune planche ne dessine ce cas).
const segments = computed(() =>
  Array.from({ length: props.target ? Math.max(props.target, props.count) : 0 }, (_, i) =>
    i < props.count - 1 ? "done" : i === props.count - 1 ? "new" : "todo",
  ),
);
const line = computed(() => `${props.company} · ${dayMonthShort(props.sentAt)}`);
const to = computed(() => ({ path: "/candidatures/suivi", query: { candidature: String(props.applicationId) } }));

const leaving = ref(false);
function close(): void {
  if (leaving.value) return;
  leaving.value = true;
  // Le temps qu'elle redescende en s'effaçant (250 ms).
  setTimeout(() => emit("close"), 250);
}
function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") close();
}
onMounted(() => {
  document.addEventListener("keydown", onKey);
});
onUnmounted(() => {
  document.removeEventListener("keydown", onKey);
});
</script>

<template>
  <Teleport to="body">
    <div
      :class="['fa-card', { leaving }]"
      role="status"
      data-test="first-steps-done"
    >
      <div class="fa-head">
        <span
          class="fa-mark"
          aria-hidden="true"
        >
          <BrandMark :size="28" />
          <span
            v-for="dot in 4"
            :key="dot"
            :class="['fa-dot', `fa-dot-${dot}`]"
          />
        </span>
        <div class="fa-text">
          <b class="fa-title">Première candidature notée</b>
          <span
            class="fa-line"
            data-test="first-application-line"
          >{{ line }}</span>
        </div>
        <IconButton
          class="fa-close"
          icon="close"
          label="Fermer"
          @click="close"
        />
      </div>
      <div
        v-if="segments.length"
        class="fa-bar"
        aria-hidden="true"
      >
        <span
          v-for="(state, i) in segments"
          :key="i"
          :class="['fa-seg', `fa-${state}`]"
          :data-test="`first-application-seg-${state}`"
        />
      </div>
      <div class="fa-foot">
        <span class="fa-count">Compte pour ton mois ORP : <b>{{ target ? `${count} sur ${target}` : count }}</b></span>
        <RouterLink
          class="fa-see"
          :to="to"
          data-test="first-application-see"
          @click="close"
        >
          Voir
        </RouterLink>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Les valeurs des planches de la section 44 ; les tailles hors échelle sont nommées ici. */
.fa-card {
  --fa-shadow: 0 12px 32px rgba(27, 31, 42, 0.18);
  --fa-title: 17px;
  --fa-title-lh: 23px;
  --fa-line-lh: 21px;
  --fa-count-lh: 20px;
  --fa-bottom: 14px;
  --fa-2: 2px;
  --fa-6: 6px;
  position: fixed;
  right: var(--space-8);
  bottom: var(--space-8);
  z-index: 60;
  box-sizing: border-box;
  width: 400px;
  padding: var(--space-4) var(--space-4) var(--fa-bottom);
  border: 1px solid var(--line);
  border-radius: var(--space-6);
  background: var(--surface);
  box-shadow: var(--fa-shadow);
  color: var(--text);
  transition: opacity 250ms ease, transform 250ms ease;
}
.fa-card.leaving { opacity: 0; transform: translateY(var(--space-2)); }
@media (prefers-reduced-motion: reduce) {
  .fa-card { transition: none; }
}
/* Téléphone : 16 px des bords, au-dessus de la barre du bas. */
@media (max-width: 820px) {
  .fa-card { right: var(--space-4); left: var(--space-4); bottom: calc(var(--nav-height) + 28px); width: auto; }
}
.fa-head { display: flex; align-items: flex-start; gap: var(--space-3); }
.fa-mark {
  position: relative;
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary-soft);
}
.fa-dot { position: absolute; border-radius: 50%; background: var(--logo-line); }
.fa-dot-1 { left: -6px; top: 4px; width: 6px; height: 6px; background: var(--spark); }
.fa-dot-2 { left: 36px; top: -6px; width: 5px; height: 5px; }
.fa-dot-3 { left: -4px; top: 38px; width: 4px; height: 4px; }
.fa-dot-4 { left: 18px; top: -8px; width: 4px; height: 4px; background: var(--spark); }
.fa-text { flex: 1; min-width: 0; padding-top: var(--space-1); }
.fa-title { display: block; font-size: var(--fa-title); line-height: var(--fa-title-lh); font-weight: var(--weight-bold); }
.fa-line { display: block; margin-top: var(--fa-2); font-size: var(--font-label); line-height: var(--fa-line-lh); font-weight: var(--weight-bold); color: var(--text-lead); }
.fa-close.icon-button { flex: none; width: 44px; height: 44px; min-height: 44px; margin: calc(-1 * var(--space-2)) calc(-1 * var(--space-2)) 0 calc(-1 * var(--fa-6)); border: 0; background: transparent; color: var(--text-lead); }
.fa-bar { display: flex; gap: var(--space-1); margin-top: var(--fa-bottom); }
.fa-seg { flex: 1; height: var(--space-2); border-radius: var(--space-1); background: var(--line); }
.fa-seg.fa-done { background: var(--primary-graphic); }
.fa-seg.fa-new { background: var(--spark); }
.fa-foot { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-top: var(--space-2); }
.fa-count { font-size: var(--font-small); line-height: var(--fa-count-lh); color: var(--text-lead); }
.fa-count b { color: var(--text); }
.fa-see { display: inline-flex; flex: none; align-items: center; min-height: 44px; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.fa-see:hover { text-decoration: underline; }
</style>
