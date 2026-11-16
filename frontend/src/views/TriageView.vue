<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import OfferFan from "../components/OfferFan.vue";
import ScoreRing from "../components/ScoreRing.vue";
import TriSlider from "../components/TriSlider.vue";
import TriageDone from "../components/TriageDone.vue";
import UndoToast from "../components/UndoToast.vue";
import { useArrowKeys } from "../composables/useArrowKeys";
import { markTriageDone, useDailyDose } from "../composables/useDailyDose";
import { useFocusMode } from "../composables/useFocusMode";
import { usePhone } from "../composables/usePhone";
import { useTriage } from "../composables/useTriage";
import { useUndo } from "../composables/useUndo";
import { MATCH_TITLE } from "../compat";
import { dateInList } from "../dates";
import { companyPlace, plural, scoreWord, triageTags } from "../format";
import { buildExcerpt, matchedPassages, offerText, triagePoints } from "../offerPassages";
import "../triage.css";

// Trier les offres (lot du 11 novembre au soir, PR 45 ; maquettes TrierOffresV2 et TrierOffresOrdinateurV2). Les
// offres du jour, une par une, la meilleure d'abord : une carte sur téléphone (titre, entreprise, lieu, note,
// étiquettes, extrait, points) ; sur ordinateur, l'éventail de cartes (maquette du 15 novembre, §12, OfferFan).
// « Écarter » et « Garder » sont de vrais boutons (← et →, annoncés par aria-keyshortcuts et écrits dans leur
// infobulle) ; aucun geste n'est nécessaire. « Annuler » pendant 6 secondes : rien ne part au serveur avant. À la fin,
// « C’est trié ! » (TriageDone).
// L'écart du message « Annuler » au bas de la fenêtre, et l'écart gardé au-dessus de lui (12 px, planche).
const TOAST_GAP = 12;
// Les flèches des raccourcis, écrites dans l'infobulle des deux boutons (Kevin, 15.11) : un libellé de touche, pas une
// icône d'action (docs/101).
const KEY_LEFT = "\u2190";
const KEY_RIGHT = "\u2192";
const { phone } = usePhone();
const { focus } = useFocusMode();
const { dose, loaded, load } = useDailyDose();
const { pending, flush } = useUndo();

// La pile et les choix (useTriage, partagé avec l'éventail en petit d'Aujourd'hui).
const { queue, index, total, current, finished, kept, dismissed, decide } = useTriage(dose, () => void focusNext());
const done = computed(() => loaded.value && finished.value);

// Sur téléphone, la page de tri remplace l'en-tête et la barre du bas (maquette) ; la fin du tri aussi.
watch(phone, (now) => (focus.value = now), { immediate: true });
onBeforeUnmount(() => (focus.value = false));
watch(done, (now) => now && markTriageDone());

const word = computed(() => (current.value?.score == null ? null : scoreWord(current.value.score)));
// Contrat, taux, puis télétravail : toujours en étiquettes, pour rester lisibles quand le titre est coupé.
const tags = computed(() => (current.value ? triageTags(current.value) : []));
const excerpt = computed(() => {
  const o = current.value;
  const text = o ? offerText(o) : "";
  return text ? buildExcerpt(text, matchedPassages(o!)) : null;
});
const points = computed(() => (current.value ? triagePoints(current.value) : []));
// Téléphone (§40 du 16.11, planche TrierOffresV2) : la carte est un dossier ; derrière, les dossiers des offres
// suivantes du groupe de 3, avec leur onglet (« 2 », « 3 »), à leur place : le suivant devant, l'autre derrière.
const folders = computed(() => {
  const start = Math.floor(index.value / 3) * 3;
  const list: { n: number; slot: number }[] = [];
  for (let at = index.value + 1; at < Math.min(start + 3, total.value); at++) list.push({ n: at + 1, slot: at - start });
  return list.reverse();
});
const where = computed(() => {
  const o = current.value;
  if (!o) return "";
  const line = companyPlace(o.company || "Entreprise non indiquée", o.location);
  return o.first_seen_at ? `${line} · ${dateInList(o.first_seen_at)}` : line;
});

// Ordinateur : l'éventail montre les offres par groupes de 3, dans l'ordre de la pile. Une offre gardée y reste, avec
// son badge « Gardée » ; une offre écartée en sort. La carte du moment est devant.
const keptIds = computed(() => kept.value.map((o) => o.id));
const fan = computed(() => {
  const start = Math.floor(Math.min(index.value, total.value - 1) / 3) * 3;
  const window = queue.value.slice(start, start + 3).map((offer, k) => ({ offer, at: start + k }));
  const shown = window.filter((w) => w.at >= index.value || keptIds.value.includes(w.offer.id));
  return {
    offers: shown.map((w) => w.offer),
    tones: shown.map((w) => w.at),
    front: Math.max(0, shown.findIndex((w) => w.at === index.value)),
  };
});
// Le titre manuscrit sous l'éventail : « 3 offres pour toi », puis « Encore 2 à trier ».
const handTitle = computed(() =>
  index.value === 0 || phone.value ? plural(total.value, "offre pour toi", "offres pour toi") : `Encore ${total.value - index.value} à trier`,
);

const title = ref<HTMLElement | null>(null);
const group = ref<HTMLElement | null>(null);
const doneScreen = ref<InstanceType<typeof TriageDone> | null>(null);
async function focusNext(): Promise<void> {
  await nextTick();
  if (current.value) (phone.value ? title.value : group.value)?.focus();
  else doneScreen.value?.focus();
}

// Sur ordinateur, le message « Annuler » est fixé en bas de la fenêtre (planche : 12 px du bord) : il reste visible
// pendant ses 6 secondes, quelle que soit la longueur de la page. Dans une fenêtre basse, la page défile juste
// assez pour que les boutons restent au-dessus de lui.
const toast = ref<InstanceType<typeof UndoToast> | null>(null);
const foot = ref<HTMLElement | null>(null);
watch(
  () => pending.value?.id,
  async (id) => {
    if (!id || phone.value) return;
    await nextTick();
    const actions = foot.value?.querySelector(".tri-actions");
    const box = toast.value?.$el as HTMLElement | undefined;
    if (!box || !foot.value || !actions) return;
    // La place du message, calculée et non mesurée : pendant l'entrée de la page, une mesure serait fausse.
    const top = window.innerHeight - box.offsetHeight - 2 * TOAST_GAP;
    // Les boutons toujours ; le compteur aussi, tant que le haut de l'éventail reste sous l'en-tête.
    const buttons = actions.getBoundingClientRect().bottom - top;
    const all = foot.value.getBoundingClientRect().bottom - top;
    const header = document.querySelector("[data-test=app-header]")?.getBoundingClientRect().bottom ?? 0;
    const room = Math.max(0, (foot.value.parentElement?.querySelector(".tri-stage")?.getBoundingClientRect().top ?? 0) - header);
    const by = Math.max(buttons, Math.min(all, room));
    if (by > 0) window.scrollBy({ top: by, behavior: "instant" });
  },
);

useArrowKeys({ left: () => decide("dismiss"), right: () => decide("keep") });

// Quitter la page (« Préparer », « Retour à l’accueil ») envoie d'abord le dernier choix.
// (Une garde du routeur posée ici, pas `onBeforeRouteLeave` : son import détachait un morceau du routeur et ajoutait
// 0,4 Ko au premier écran.)
const leaving = useRouter().beforeEach(async () => {
  await flush();
});
onBeforeUnmount(leaving);

onMounted(load);
</script>

<template>
  <TriageDone
    v-if="done"
    ref="doneScreen"
    :kept="kept"
    :dismissed="dismissed"
  />
  <section
    v-else
    :class="['tri', { 'tri-phone': phone }]"
    data-test="triage"
  >
    <header class="tri-head">
      <RouterLink
        v-if="phone"
        :to="{ name: 'today' }"
        class="tri-back"
        aria-label="Retour"
        data-test="triage-back"
      >
        <AppIcon name="arrow-left" />
      </RouterLink>
      <h1 :class="{ 'visually-hidden': !phone }">
        Trier les offres
      </h1>
    </header>
    <LoadingBlocks
      v-if="!loaded"
      class="tri-wait"
      :heights="['2.5rem', '20rem']"
    />
    <!-- 0 offre à trier (LISEZMOI §12, Kevin 15.11) : l'état vide commun (§13), la mascotte de FinDuTriAucune, le titre
         manuscrit, la pastille, deux boutons. Ni éventail vide, ni « Écarter » / « Garder ». -->
    <EmptyState
      v-else-if="!total"
      title="Rien à trier pour l’instant"
      pill="Offres collectées chaque jour"
      data-test="triage-empty"
    >
      <template #illustration>
        <img
          src="/tri/fin-du-tri.webp"
          alt=""
          :width="phone ? 260 : 400"
          :height="phone ? 150 : 230"
        >
      </template>
      <template #title>
        <span class="tri-hand">Rien à trier pour l’instant</span>
      </template>
      <template #actions>
        <RouterLink
          to="/candidatures"
          class="button-link primary-link"
          data-test="triage-empty-jobs"
        >
          Voir mes candidatures
        </RouterLink>
        <RouterLink
          to="/candidatures/alertes"
          class="button-link secondary"
          data-test="triage-empty-alerts"
        >
          Gérer mes alertes
        </RouterLink>
      </template>
    </EmptyState>
    <template v-else-if="current">
      <p
        v-if="phone"
        class="tri-catch"
      >
        <span
          class="tri-hand"
          data-test="triage-count"
        >{{ handTitle }}</span>
      </p>
      <div
        v-if="phone"
        class="tri-stage"
      >
        <div class="tri-deck">
          <span
            v-for="folder in folders"
            :key="folder.n"
            :class="['tri-folder', `tri-folder-${folder.slot}`]"
            aria-hidden="true"
          ><b>{{ folder.n }}</b></span>
          <Transition name="tri-fly">
            <section
              :key="current.id"
              class="tri-offer"
              :aria-label="`Offre ${index + 1} sur ${total}`"
              data-test="triage-offer"
            >
              <span
                class="tri-tab"
                aria-hidden="true"
              >Offre {{ index + 1 }} sur {{ total }}</span>
              <div class="tri-left">
                <div class="tri-top">
                  <CompanyLogo
                    :offer="current"
                    pair
                    class="tri-logo"
                  />
                  <div class="tri-names">
                    <h2
                      ref="title"
                      class="tri-title"
                      tabindex="-1"
                      data-test="triage-title"
                    >
                      {{ current.title }}
                    </h2>
                    <p class="tri-sub">
                      {{ where }}
                    </p>
                  </div>
                </div>
                <div class="tri-score">
                  <ScoreRing
                    :score="current.score ?? null"
                    :stale="current.score_stale"
                    bare
                  />
                  <span
                    v-if="word"
                    class="tri-match"
                  >
                    <b
                      :class="['tri-word', word.tone]"
                      aria-hidden="true"
                    >{{ MATCH_TITLE[word.tone] }}</b>
                    <span class="tri-why">Selon ton profil et tes préférences</span>
                  </span>
                </div>
                <ul
                  v-if="tags.length"
                  class="tri-tags"
                  data-test="triage-tags"
                >
                  <li
                    v-for="tag in tags"
                    :key="tag"
                  >
                    {{ tag }}
                  </li>
                </ul>
              </div>
              <div class="tri-right">
                <div
                  v-if="excerpt"
                  class="tri-quote"
                  data-test="triage-excerpt"
                >
                  <p>
                    «&nbsp;<template
                      v-for="(part, i) in excerpt.segments"
                      :key="i"
                    >
                      <mark v-if="part.mark">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
                    </template>&nbsp;»
                  </p>
                  <p
                    v-if="excerpt.count"
                    class="visually-hidden"
                    data-test="triage-legend"
                  >
                    {{ plural(excerpt.count, "point retrouvé", "points retrouvés") }}
                  </p>
                </div>
                <ul
                  v-if="points.length"
                  class="tri-points"
                  data-test="triage-points"
                >
                  <li
                    v-for="point in points"
                    :key="point.text"
                  >
                    <span
                      :class="['tri-dot', point.ok ? 'ok' : 'ask']"
                      aria-hidden="true"
                    ><AppIcon
                      v-if="point.ok"
                      name="tick"
                    /><template v-else>?</template></span>
                    <span><span class="visually-hidden">{{ point.ok ? "Retrouvé : " : "À vérifier : " }}</span>{{ point.text }}</span>
                  </li>
                </ul>
              </div>
              <RouterLink
                :to="{ path: '/candidatures/offres', query: { offre: current.id } }"
                class="tri-full"
                data-test="triage-read"
              >
                Voir l’offre complète<AppIcon name="chevron" />
              </RouterLink>
            </section>
          </Transition>
        </div>
      </div>
      <div
        v-else
        ref="group"
        class="tri-stage"
        role="group"
        tabindex="-1"
        :aria-label="`Offre ${index + 1} sur ${total}`"
        data-test="triage-offer"
      >
        <OfferFan
          :offers="fan.offers"
          :front="fan.front"
          :tones="fan.tones"
          :kept="keptIds"
        />
      </div>
      <p
        v-if="!phone"
        class="tri-catch"
      >
        <span
          class="tri-hand"
          data-test="triage-count"
        >{{ handTitle }}</span>
      </p>
      <footer
        ref="foot"
        class="tri-foot"
      >
        <UndoToast
          ref="toast"
          bar
        />
        <p
          v-if="!phone"
          class="tri-counter"
          data-test="triage-counter"
        >
          <i
            v-for="n in total"
            :key="n"
            :class="{ on: n === index + 1 }"
            aria-hidden="true"
          />
          <span>{{ index + 1 }} sur {{ total }} · {{ plural(kept.length, "gardée", "gardées") }}</span>
        </p>
        <TriSlider
          v-if="phone"
          @decide="decide"
        />
        <div
          v-else
          class="tri-actions"
        >
          <button
            type="button"
            class="tri-dismiss"
            aria-keyshortcuts="ArrowLeft"
            :title="`Écarter (${KEY_LEFT})`"
            data-test="triage-dismiss"
            @click="decide('dismiss')"
          >
            <AppIcon name="close" />Écarter
          </button>
          <button
            type="button"
            class="primary tri-keep"
            aria-keyshortcuts="ArrowRight"
            :title="`Garder (${KEY_RIGHT})`"
            data-test="triage-keep"
            @click="decide('keep')"
          >
            <AppIcon name="bookmark" />Garder
          </button>
        </div>
      </footer>
    </template>
  </section>
</template>

<style>
/* Le bandeau « Annuler » du tri remplace celui de l'application le temps qu'il est là. */
:root:has(.tri-toast) .undo-toast { display: none; }
</style>

<style scoped>
/* Les valeurs des maquettes, écrites avec les échelles ; les tailles hors échelle sont nommées ici. Les marges,
   retraits et écarts hors de la grille de 4 (6, 10, 14, 22, 26, 50) sont ramenés à la grille. */
.tri {
  --t-head: 56px; --t-60: 3.75rem; --t-40: 40px; --t-20: 1.25rem; --t-28: 1.75rem; --t-18: 1.125rem; --t-23: 1.4375rem; --t-14: 0.875rem; --t-15: 0.9375rem; --t-13: 0.8125rem;
  --t-25: 1.5625rem; --t-22: 1.375rem; --t-16: 1rem; --t-card-r: 22px; --t-pad: 16px; --t-quote-r: 14px; --t-tag-h: 28px; --t-tag-r: 14px;
  --t-btn: 52px; --t-toast: 48px; --t-toast-wide: 52px; --t-dot: 8px; --t-dash: 24px; --t-pip: 22px; --t-ring: 48px; --t-logo: 44px;
  --t-actions: 440px; --t-56: 56px; --t-21: 1.3125rem; --t-27: 1.6875rem; --t-24: 1.5rem; --t-32: 32px; --t-6: 6px; --t-tab-w: 136px; --t-tab-up: 34px; --t-folder-r: 18px; --t-folder-tab: 30px; --t-folder-w: 52px; --t-folder-at: 136px; --t-folder-step: 52px; --t-mark-r: 4px; --t-10: 10px; --t-14p: 14px; --t-2: 2px; --t-3: 3px;
  display: flex; flex-direction: column; color: var(--text);
}
.tri-head { display: flex; align-items: center; gap: var(--space-3); }
.tri-head h1 { margin: 0; font-size: var(--t-20); font-weight: var(--weight-heavy); }
.tri-back { display: grid; place-items: center; width: var(--target-min); height: var(--target-min); margin-left: calc(-1 * var(--space-3)); color: var(--text); }
.tri-back :deep(svg) { width: var(--t-22); height: var(--t-22); }
.tri-wait { padding: var(--space-6) var(--space-5); }
.tri-catch { margin: 0; }
.tri-hand { display: inline-block; font-family: var(--font-hand); font-weight: var(--weight-regular); line-height: var(--leading-none); color: var(--primary-text); transform: rotate(-2deg); }

.tri-stage { position: relative; }
.tri-deck { position: relative; }
.tri-offer { position: relative; }
.tri-title { margin: 0; font-weight: var(--weight-bold); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; outline-offset: var(--t-2); }
.tri-sub { margin: 0; color: var(--text-secondary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.tri-logo { flex: none; }
.tri-score { display: flex; align-items: center; gap: var(--space-3); }
/* La classe globale « .close » (bouton de fermeture) porte le même nom que la note « Proche ». */
.tri-score :deep(.score-ring-wrap) { padding: 0; }
.tri-score :deep(.score-ring) { width: var(--t-ring); height: var(--t-ring); font-size: var(--t-16); }
.tri-word { padding: 0; line-height: var(--t-20); font-size: var(--t-15); font-weight: var(--weight-bold); color: var(--success); }
.tri-word.dig { color: var(--score-dig); }
.tri-word.far { color: var(--text-secondary); }
.tri-tags { display: flex; flex-wrap: wrap; gap: var(--space-2); margin: 0; padding: 0; list-style: none; }
.tri-tags li { display: inline-flex; align-items: center; min-height: var(--t-tag-h); padding: 0 var(--space-2); border-radius: var(--t-tag-r); background: var(--tri-tag); color: var(--tri-tag-text); font-size: var(--t-13); font-weight: var(--weight-semibold); }
.tri-quote p { margin: 0; color: var(--tri-tag-text); }
.tri-quote mark { padding: 0 var(--space-1); border-radius: var(--t-mark-r); background: var(--tri-mark); color: inherit; }
.tri-points { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.tri-points li { display: flex; align-items: flex-start; gap: var(--space-3); font-size: var(--t-15); line-height: var(--t-22); }
.tri-dot { flex: none; display: grid; place-items: center; width: var(--t-pip); height: var(--t-pip); border-radius: 50%; font-size: var(--t-13); font-weight: var(--weight-heavy); }
.tri-dot.ok { background: var(--tri-ok); color: var(--tri-ok-ink); }
.tri-dot.ok :deep(svg) { width: var(--t-13); height: var(--t-13); stroke-width: 3; }
.tri-dot.ask { background: var(--tri-ask); color: var(--tri-ask-ink); }

.tri-counter { display: flex; justify-content: center; align-items: center; gap: var(--space-2); margin: 0; font-size: var(--t-13); color: var(--text-secondary); }
.tri-counter i { width: var(--t-dot); height: var(--t-dot); border-radius: var(--space-1); background: var(--tri-dot); }
.tri-counter i.on { width: var(--t-dash); background: var(--primary-graphic); }
.tri-counter span { margin-left: var(--space-2); }
.tri-actions { display: flex; gap: var(--space-3); }
.tri-actions button { flex: 1; display: flex; align-items: center; justify-content: center; gap: var(--space-2); min-height: var(--t-btn); border-radius: var(--radius-pill); font-size: var(--t-16); font-weight: var(--weight-bold); }
.tri-actions :deep(svg) { width: var(--t-20); height: var(--t-20); }
.tri-dismiss { border: 1.5px solid var(--tri-outline); background: var(--surface); color: var(--text); }
.tri-keep { border: 0; }
.tri-toast { display: flex; align-items: center; justify-content: space-between; min-height: var(--t-toast); padding: 0 var(--space-2) 0 var(--space-4); border-radius: var(--t-quote-r); background: var(--snackbar-bg); color: var(--snackbar-text); font-size: var(--t-15); }
.tri-toast { position: relative; }
.tri-toast :deep(button) { min-height: var(--target-min); padding: 0 var(--space-3); border: 0; background: none; color: var(--snackbar-action); font-size: var(--t-15); font-weight: var(--weight-bold); }

/* Téléphone (§40 du 16.11, planches TrierOffresV2 et TrierOffresCurseur*) : la carte est un dossier, son onglet
   « Offre 1 sur 3 » soudé en haut à gauche ; derrière, les dossiers suivants en pêche avec leur onglet. La carte prend
   la hauteur libre jusqu'au curseur. Valeurs ramenées à la grille de 4 : 22 px de marge et de retrait (24), 14 px
   d'écart (16), 18 px autour des traits (16), onglets à 146 et 208 px (148 et 208). */
.tri-phone { min-height: 100dvh; background: var(--bg); }
.tri-phone .tri-head { min-height: var(--t-head); padding: 0 var(--space-4); }
.tri-phone .tri-catch { padding: var(--space-1) var(--space-6) 0; }
.tri-phone .tri-hand { font-size: var(--t-28); }
.tri-phone .tri-stage { flex: 1; display: flex; flex-direction: column; margin-top: var(--t-56); padding-bottom: var(--space-4); overflow-x: clip; }
.tri-phone .tri-deck { flex: 1; display: flex; flex-direction: column; margin: 0 var(--space-6); }
.tri-folder { position: absolute; top: calc(-1 * var(--space-2)); left: var(--t-10); right: var(--t-10); bottom: var(--space-12); border: 1.5px solid var(--tri-folder-edge); border-radius: var(--t-folder-r); background: var(--tri-folder); }
.tri-folder-2 { top: calc(-1 * var(--space-4)); left: var(--space-5); right: var(--space-5); border-color: var(--tri-folder-far-edge); background: var(--tri-folder-far); }
.tri-folder b { position: absolute; top: calc(-1 * var(--t-folder-tab)); left: var(--t-folder-at); display: flex; justify-content: center; box-sizing: border-box; width: var(--t-folder-w); height: calc(var(--t-folder-tab) + var(--space-1)); padding-top: var(--t-6); border: inherit; border-bottom: 0; border-radius: var(--t-14p) var(--t-14p) 0 0; background: inherit; font-size: var(--t-14); font-weight: var(--weight-bold); color: var(--tri-folder-ink); }
.tri-folder-2 b { left: calc(var(--t-folder-at) + var(--t-folder-step)); }
.tri-phone .tri-offer { flex: 1; display: flex; flex-direction: column; z-index: 1; padding: var(--space-6) var(--space-6) var(--space-2); border: 1.5px solid var(--tri-card-edge); border-radius: 0 var(--space-5) var(--space-5) var(--space-5); background: var(--surface); box-shadow: var(--tri-card-shadow); }
.tri-tab { position: absolute; z-index: 2; left: -1.5px; top: calc(-1 * var(--t-tab-up)); display: flex; justify-content: center; box-sizing: border-box; width: var(--t-tab-w); height: var(--t-40); padding-top: var(--space-2); border: 1.5px solid var(--tri-card-edge); border-bottom: 0; border-radius: var(--space-4) var(--space-4) 0 0; background: var(--surface); font-size: var(--t-15); font-weight: var(--weight-heavy); }
.tri-phone .tri-top { display: flex; align-items: center; gap: var(--space-4); }
.tri-phone .tri-logo { width: var(--t-56); height: var(--t-56); border-radius: var(--t-14p); }
.tri-phone .tri-names { flex: 1; min-width: 0; }
.tri-phone .tri-title { font-size: var(--t-21); line-height: var(--t-27); font-weight: var(--weight-heavy); }
.tri-phone .tri-sub { margin-top: var(--t-2); font-size: var(--t-15); line-height: var(--t-20); }
.tri-phone :is(.tri-score, .tri-quote, .tri-points) { margin-top: var(--space-4); padding-top: var(--space-4); border-top: 1px solid var(--tri-rule); }
.tri-phone .tri-score { gap: var(--space-4); }
.tri-phone .tri-score :deep(.score-ring) { width: var(--t-56); height: var(--t-56); font-size: var(--t-18); }
.tri-match { display: grid; gap: var(--t-2); }
.tri-phone .tri-word { font-size: var(--t-18); line-height: var(--t-24); }
.tri-why { font-size: var(--t-14); color: var(--text-secondary); }
.tri-phone .tri-tags { margin-top: var(--space-4); }
.tri-phone .tri-tags li { min-height: var(--t-32); padding: 0 var(--space-3); border-radius: var(--space-4); font-size: var(--t-14); }
.tri-phone .tri-quote p { font-size: var(--t-16); line-height: var(--t-27); display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.tri-phone .tri-points { gap: var(--space-4); }
.tri-phone .tri-points li { align-items: center; font-size: var(--t-16); }
.tri-phone .tri-dot { width: var(--space-6); height: var(--space-6); font-size: var(--t-14); }
.tri-full { display: flex; align-items: center; justify-content: center; gap: var(--t-6); min-height: var(--target-min); margin-top: auto; padding-top: var(--space-3); font-size: var(--t-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.tri-full :deep(svg) { width: var(--t-16); height: var(--t-16); }
.tri-phone .tri-foot { position: sticky; bottom: 0; z-index: 4; padding: var(--space-4) var(--space-5) max(var(--t-28), env(safe-area-inset-bottom)); background: var(--bg); }
.tri-phone .tri-toast { position: absolute; left: var(--space-5); right: var(--space-5); bottom: 100%; z-index: 6; }

/* La carte qui part : 250 ms au plus (§1). */
.tri-fly-leave-active { position: absolute; inset: 0 0 auto; z-index: 2; transition: transform 0.25s ease-in, opacity 0.25s ease-in; transform-origin: 50% 100%; }
.tri-fly-leave-to { transform: translateX(300px) rotate(9deg); opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .tri-fly-leave-active { transition: opacity 0.12s linear; }
  .tri-fly-leave-to { transform: none; opacity: 0; }
}

/* Ordinateur (§12) : l'éventail (OfferFan), le titre manuscrit, les boutons, puis le compteur. Écarts de la
   planche ramenés à la grille : 26 px au-dessus de l'éventail (24), 30 px au-dessus du titre (32), 22 px au-dessus
   des boutons (24). Le groupe reçoit le focus après chaque choix sans être une commande : pas de contour. */
.tri:not(.tri-phone) { align-items: center; padding: var(--space-3) 0 var(--space-12); text-align: center; }
.tri:not(.tri-phone) .tri-stage { align-self: stretch; margin-top: var(--space-6); outline: 0; }
.tri:not(.tri-phone) .tri-catch { margin-top: var(--space-8); }
.tri:not(.tri-phone) .tri-hand { font-size: var(--t-60); }
.tri:not(.tri-phone) .tri-foot { display: flex; flex-direction: column; gap: var(--space-4); width: var(--t-actions); margin-top: var(--space-6); }
.tri:not(.tri-phone) .tri-actions { order: 1; }
.tri:not(.tri-phone) .tri-counter { order: 2; }
/* Le message « Annuler » : fixé en bas de la fenêtre, à 12 px du bord (planche), 440 px de large. La page garde sous
   le compteur la place du message et de ses deux écarts, pour qu'il ne recouvre jamais rien en bas de page. */
.tri:not(.tri-phone) .tri-toast {
  position: fixed; left: 50%; bottom: var(--space-3); z-index: 4; box-sizing: border-box; width: min(var(--t-actions), calc(100vw - var(--space-8)));
  min-height: var(--t-toast-wide); padding-left: var(--space-5); transform: translateX(-50%);
}
.tri:not(.tri-phone) { padding-bottom: calc(var(--t-toast-wide) + var(--space-6)); }
</style>
