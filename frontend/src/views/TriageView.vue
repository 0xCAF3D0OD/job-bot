<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { onBeforeRouteLeave } from "vue-router";

import { api, type Offer } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import BookmarkMark from "../components/BookmarkMark.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import FaceState from "../components/FaceState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import ScoreRing from "../components/ScoreRing.vue";
import TriageDone from "../components/TriageDone.vue";
import { useArrowKeys } from "../composables/useArrowKeys";
import { markTriageDone, useDailyDose } from "../composables/useDailyDose";
import { useFocusMode } from "../composables/useFocusMode";
import { usePhone } from "../composables/usePhone";
import { offerUndo, useUndo } from "../composables/useUndo";
import { companyPlace, plural, rateText, remoteText, scoreWord } from "../format";
import { buildExcerpt, matchedPassages, offerText } from "../offerPassages";

// Trier les offres (lot du 11 novembre au soir, PR 45 ; maquettes TrierOffresV2 et TrierOffresOrdinateurV2). Les
// offres du jour, une par une, la meilleure d'abord : une carte sur téléphone, un livre ouvert sur ordinateur, le
// même contenu dans le même ordre (titre, entreprise, lieu, note, étiquettes, extrait, points). « Écarter » et
// « Garder » sont de vrais boutons (← et → sur ordinateur) ; aucun geste n'est nécessaire. « Annuler » pendant
// 6 secondes : rien ne part au serveur avant. À la fin, « C’est trié ! » (TriageDone).
// Le nom des deux touches, écrit sur leur capuchon (planche TrierOffresOrdinateurV2) : un
// libellé de touche, pas une icône d'action (docs/101).
const KEY_LEFT = "\u2190";
const KEY_RIGHT = "\u2192";
const { phone } = usePhone();
const { focus } = useFocusMode();
const { dose, restDay, loaded, load } = useDailyDose();
const { pending, undo, hold, release, flush } = useUndo();
// Le trait du bandeau suit le compte de useUndo : arrêté tant que la souris ou le focus est sur le bandeau, il
// repart de plein quand ils le quittent (le compte de 6 secondes repart lui aussi).
const held = ref(false);
const countdown = ref(0);
function holdToast(): void {
  held.value = true;
  hold();
}
function releaseToast(): void {
  held.value = false;
  countdown.value += 1;
  release();
}

type Choice = "keep" | "dismiss";
// La pile du jour ne change pas pendant le tri.
const queue = ref<Offer[]>([]);
const index = ref(0);
const choices = ref<Choice[]>([]);
watch(
  () => dose.value.map((o) => o.id).join(","),
  () => {
    if (index.value === 0) queue.value = [...dose.value];
  },
  { immediate: true },
);
const total = computed(() => queue.value.length);
const current = computed(() => queue.value[index.value] ?? null);
const remaining = computed(() => Math.max(0, total.value - index.value - 1));
const done = computed(() => loaded.value && total.value > 0 && index.value >= total.value);
const kept = computed(() => queue.value.filter((_, i) => choices.value[i] === "keep"));
const dismissed = computed(() => choices.value.filter((c) => c === "dismiss").length);

// Sur téléphone, la page de tri remplace l'en-tête et la barre du bas (maquette) ; la fin du tri aussi.
watch(phone, (now) => (focus.value = now), { immediate: true });
onBeforeUnmount(() => (focus.value = false));
watch(done, (now) => now && markTriageDone());

const word = computed(() => (current.value?.score == null ? null : scoreWord(current.value.score)));
// Contrat, taux, puis télétravail : toujours en étiquettes, pour rester lisibles quand le titre est coupé.
const tags = computed(() => {
  const o = current.value;
  if (!o) return [];
  return [o.employment_type ?? "", rateText(o.rate_min, o.rate_max), remoteText(o) ?? ""].filter(Boolean).slice(0, 3);
});
const excerpt = computed(() => {
  const o = current.value;
  const text = o ? offerText(o) : "";
  return text ? buildExcerpt(text, matchedPassages(o!)) : null;
});
// Trois points au plus : d'abord ce qui est retrouvé dans le profil, puis au plus un point à vérifier.
const points = computed(() => {
  const o = current.value;
  if (!o) return [];
  const check = o.gaps?.[0]?.text;
  const found = (o.strengths ?? []).slice(0, check ? 2 : 3).map((s) => ({ text: s.text, ok: true }));
  return check ? [...found, { text: check, ok: false }] : found;
});

const title = ref<HTMLElement | null>(null);
const doneScreen = ref<InstanceType<typeof TriageDone> | null>(null);
async function focusNext(): Promise<void> {
  await nextTick();
  if (current.value) title.value?.focus();
  else doneScreen.value?.focus();
}

function decide(choice: Choice): void {
  const offer = current.value;
  if (!offer) return;
  const at = index.value;
  choices.value[at] = choice;
  index.value = at + 1;
  void focusNext();
  void offerUndo({
    message: choice === "keep" ? "Offre gardée dans tes candidatures" : "Offre écartée",
    commit: async (keepalive) => {
      const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
        params: { path: { offer_id: offer.id } },
        // « Garder » : l'état « Gardée » (`later`, décision de Kevin du 11 novembre), pas un second état.
        body: { status: choice === "keep" ? "later" : "ignored" },
        keepalive,
      });
      return response.ok;
    },
    restore: () => {
      choices.value.length = at;
      index.value = at;
      void focusNext();
    },
  });
}
useArrowKeys({ left: () => decide("dismiss"), right: () => decide("keep") });

// Quitter la page (« Préparer », « Retour à l’accueil ») envoie d'abord le dernier choix.
onBeforeRouteLeave(async () => {
  await flush();
});

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
    <div
      v-else-if="restDay || !total"
      class="tri-wait"
    >
      <FaceState
        :title="restDay ? 'Jour de repos' : 'Rien à trier'"
        data-test="triage-empty"
      >
        <p>{{ restDay ? "Pas de tri aujourd’hui." : "Les nouvelles offres arrivent chaque matin." }}</p>
        <div class="face-state-actions">
          <RouterLink
            :to="{ name: 'today' }"
            class="button-link"
          >
            Retour à l’accueil
          </RouterLink>
        </div>
      </FaceState>
    </div>
    <template v-else-if="current">
      <p class="tri-catch">
        <span
          class="tri-hand"
          data-test="triage-count"
        >{{ plural(total, "offre pour toi", "offres pour toi") }}</span>
        <span
          v-if="!phone"
          class="tri-lead"
        >Tourne les pages : garde celles qui te parlent.</span>
      </p>
      <div class="tri-stage">
        <div class="tri-deck">
          <span
            v-if="remaining > 1"
            class="tri-pile tri-pile-far"
            aria-hidden="true"
          />
          <span
            v-if="remaining > 0"
            class="tri-pile tri-pile-near"
            aria-hidden="true"
          />
          <Transition :name="phone ? 'tri-fly' : 'tri-turn'">
            <section
              :key="current.id"
              class="tri-offer"
              :aria-label="`Offre ${index + 1} sur ${total}`"
              data-test="triage-offer"
            >
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
                      {{ companyPlace(current.company || "Entreprise non indiquée", current.location) }}
                    </p>
                  </div>
                </div>
                <div class="tri-score">
                  <ScoreRing
                    :score="current.score ?? null"
                    :stale="current.score_stale"
                    bare
                  />
                  <b
                    v-if="word"
                    :class="['tri-word', word.tone]"
                    aria-hidden="true"
                  >{{ word.word }}</b>
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
                  <RouterLink
                    v-if="excerpt.built"
                    :to="{ path: '/candidatures/offres', query: { offre: current.id } }"
                    class="tri-read"
                    data-test="triage-read"
                  >
                    Lire toute l’annonce
                  </RouterLink>
                  <p
                    v-if="excerpt.count"
                    :class="['tri-legend', { 'visually-hidden': phone }]"
                    data-test="triage-legend"
                  >
                    <span
                      class="tri-legend-mark"
                      aria-hidden="true"
                    />{{ plural(excerpt.count, "point retrouvé", "points retrouvés") }}
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
            </section>
          </Transition>
          <svg
            v-if="!phone"
            class="tri-sparks"
            width="50"
            height="21"
            viewBox="0 0 60 26"
            aria-hidden="true"
          ><path d="M14 8l6 12M33 3v15M52 8l-6 12" /></svg>
          <BookmarkMark
            class="tri-bookmark"
            :width="phone ? 38 : 50"
          />
        </div>
        <template v-if="!phone">
          <img
            class="tri-friend tri-friend-left"
            src="/tri/orange-tient-le-livre.webp"
            alt=""
            width="140"
            height="265"
          >
          <img
            class="tri-friend tri-friend-right"
            src="/tri/sourire-tient-le-livre.webp"
            alt=""
            width="152"
            height="185"
          >
        </template>
      </div>
      <footer class="tri-foot">
        <div
          v-if="pending"
          :key="pending.id"
          class="tri-toast"
          role="status"
          data-test="triage-toast"
          @mouseenter="holdToast"
          @mouseleave="releaseToast"
          @focusin="holdToast"
          @focusout="releaseToast"
        >
          <span>{{ pending.message }}</span>
          <button
            type="button"
            data-test="undo"
            @click="undo"
          >
            Annuler
          </button>
          <i
            :key="countdown"
            :class="['tri-toast-bar', { held }]"
            aria-hidden="true"
          />
        </div>
        <p
          class="tri-counter"
          data-test="triage-counter"
        >
          <i
            v-for="n in total"
            :key="n"
            :class="{ on: n === index + 1 }"
            aria-hidden="true"
          />
          <span>{{ index + 1 }} sur {{ total }}</span>
        </p>
        <p
          v-if="!phone"
          class="tri-keys"
          aria-hidden="true"
          data-test="triage-keys"
        >
          <kbd>{{ KEY_LEFT }}</kbd>Écarter<kbd>{{ KEY_RIGHT }}</kbd>Garder
        </p>
        <div class="tri-actions">
          <button
            type="button"
            class="tri-dismiss"
            aria-keyshortcuts="ArrowLeft"
            data-test="triage-dismiss"
            @click="decide('dismiss')"
          >
            <AppIcon name="close" />Écarter
          </button>
          <button
            type="button"
            class="primary tri-keep"
            aria-keyshortcuts="ArrowRight"
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
/* Les couleurs propres au tri (maquettes TrierOffresV2 et TrierOffresOrdinateurV2, clair et sombre) : la pile, le
   liseré du livre, l'extrait, le surlignage (§1 du lot), les étiquettes et les pastilles des points. */
.tri, .tri-done {
  --tri-edge: #2445C2; --tri-pile-near: #9FB0F2; --tri-pile-far: #C9D3FA; --tri-rim: #DCE2F8;
  --tri-shadow: 0 12px 24px rgba(36, 69, 194, 0.18); --tri-book-shadow: 0 14px 28px rgba(36, 69, 194, 0.22); --tri-fold: rgba(27, 31, 42, 0.18);
  --tri-quote: #FFF8E1; --tri-mark: #FFE9A8; --tri-tag: #F1EEE7; --tri-tag-text: #3D4250;
  --tri-ok: #1F7A4D; --tri-ok-ink: #FFFFFF; --tri-ask: #FBEBDD; --tri-ask-ink: #8A4A12;
  --tri-rule: #ECE9E1; --tri-dot: #DAD6CC; --tri-outline: #C9C5BA; --tri-dash: #DAD6CC; --tri-spark: #2445C2; --tri-count: #7D95FF;
}
:root[data-theme="dark"] :is(.tri, .tri-done) {
  --tri-edge: #4560D8; --tri-pile-near: #3A4A86; --tri-pile-far: #2C3558; --tri-rim: #2C3558;
  --tri-shadow: none; --tri-book-shadow: none; --tri-fold: rgba(0, 0, 0, 0.5);
  --tri-quote: #2B2618; --tri-mark: #5C4A14; --tri-tag: #2C2722; --tri-tag-text: #D9D2C7;
  --tri-ok: #7FD3A6; --tri-ok-ink: #171411; --tri-ask: #3A2A1C; --tri-ask-ink: #F2B98E;
  --tri-rule: #2C2722; --tri-dot: #4E473E; --tri-outline: #4E473E; --tri-dash: #4E473E; --tri-spark: #7D95FF; --tri-count: #7D95FF;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) :is(.tri, .tri-done) {
    --tri-edge: #4560D8; --tri-pile-near: #3A4A86; --tri-pile-far: #2C3558; --tri-rim: #2C3558;
    --tri-shadow: none; --tri-book-shadow: none; --tri-fold: rgba(0, 0, 0, 0.5);
    --tri-quote: #2B2618; --tri-mark: #5C4A14; --tri-tag: #2C2722; --tri-tag-text: #D9D2C7;
    --tri-ok: #7FD3A6; --tri-ok-ink: #171411; --tri-ask: #3A2A1C; --tri-ask-ink: #F2B98E;
    --tri-rule: #2C2722; --tri-dot: #4E473E; --tri-outline: #4E473E; --tri-dash: #4E473E; --tri-spark: #7D95FF; --tri-count: #7D95FF;
  }
  /* En sombre, les personnages et l'illustration ont un contour clair (lot, « Fin du tri »). */
  :root:not([data-theme="light"]) :is(.tri-friend, .tri-done .sent-screen-image) { filter: drop-shadow(0 0 1px #F3EEE6) drop-shadow(0 0 1px #F3EEE6); }
}
:root[data-theme="dark"] :is(.tri-friend, .tri-done .sent-screen-image) { filter: drop-shadow(0 0 1px #F3EEE6) drop-shadow(0 0 1px #F3EEE6); }
/* Le bandeau « Annuler » du tri remplace celui de l'application le temps qu'il est là. */
:root:has(.tri-toast) .undo-toast { display: none; }
</style>

<style scoped>
/* Les valeurs des maquettes, écrites avec les échelles ; les tailles hors échelle sont nommées ici. Les marges,
   retraits et écarts hors de la grille de 4 (6, 10, 14, 22, 26, 50) sont ramenés à la grille. */
.tri {
  --t-head: 56px; --t-84: 84px; --t-29: 29px; --t-40: 40px; --t-48: 48px; --t-20: 1.25rem; --t-28: 1.75rem; --t-44h: 2.75rem; --t-18: 1.125rem; --t-23: 1.4375rem; --t-14: 0.875rem; --t-15: 0.9375rem; --t-13: 0.8125rem;
  --t-25: 1.5625rem; --t-22: 1.375rem; --t-26: 1.625rem; --t-17: 1.0625rem; --t-16: 1rem; --t-card-r: 22px; --t-pad: 16px; --t-quote-r: 14px; --t-tag-h: 28px; --t-tag-r: 14px;
  --t-btn: 52px; --t-btn-wide: 56px; --t-toast: 48px; --t-toast-wide: 52px; --t-dot: 8px; --t-dash: 24px; --t-pip: 22px; --t-ring: 48px; --t-logo: 44px; --t-logo-wide: 48px;
  --t-page-w: 300px; --t-page-h: 430px; --t-book: 616px; --t-actions: 440px; --t-mark-r: 4px; --t-key-r: 6px; --t-10: 10px; --t-14p: 14px; --t-2: 2px; --t-3: 3px;
  display: flex; flex-direction: column; color: var(--text);
}
.tri-head { display: flex; align-items: center; gap: var(--space-3); }
.tri-head h1 { margin: 0; font-size: var(--t-20); font-weight: var(--weight-heavy); }
.tri-back { display: grid; place-items: center; width: var(--target-min); height: var(--target-min); margin-left: calc(-1 * var(--space-3)); color: var(--text); }
.tri-back :deep(svg) { width: var(--t-22); height: var(--t-22); }
.tri-wait { padding: var(--space-6) var(--space-5); }
.tri-catch { margin: 0; }
.tri-hand { display: inline-block; font-family: var(--font-hand); font-weight: var(--weight-regular); line-height: var(--leading-none); color: var(--primary-text); transform: rotate(-2deg); }
.tri-lead { display: block; margin-top: var(--space-3); font-size: var(--t-17); color: var(--tri-tag-text); }

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
.tri-read { display: inline-flex; align-items: center; min-height: var(--target-min); font-size: var(--t-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: underline; }
.tri-legend { display: flex; align-items: center; gap: var(--space-2); font-size: var(--t-13); }
.tri-legend-mark { flex: none; width: var(--t-22); height: 11px; border-radius: var(--t-mark-r); background: var(--tri-mark); }
.tri-points { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.tri-points li { display: flex; align-items: flex-start; gap: var(--space-3); font-size: var(--t-15); line-height: var(--t-22); }
.tri-dot { flex: none; display: grid; place-items: center; width: var(--t-pip); height: var(--t-pip); border-radius: 50%; font-size: var(--t-13); font-weight: var(--weight-heavy); }
.tri-dot.ok { background: var(--tri-ok); color: var(--tri-ok-ink); }
.tri-dot.ok :deep(svg) { width: var(--t-13); height: var(--t-13); stroke-width: 3; }
.tri-dot.ask { background: var(--tri-ask); color: var(--tri-ask-ink); }
.tri-bookmark { position: absolute; z-index: 3; }

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
/* Le trait du bandeau (paquet du 13 novembre) : 3 px en bas, il se vide pendant les 6 secondes où « Annuler » reste
   possible. Il s'arrête, plein, tant que la souris ou le focus est sur le bandeau. Masqué sans mouvement. */
.tri-toast { position: relative; overflow: hidden; }
.tri-toast-bar { position: absolute; left: 0; bottom: 0; width: 100%; height: 3px; background: var(--tri-count); transform-origin: left center; animation: tri-count 6s linear forwards; }
.tri-toast-bar.held { animation: none; }
@keyframes tri-count { to { transform: scaleX(0); } }
@media (prefers-reduced-motion: reduce) { .tri-toast-bar { display: none; } }
/* Les raccourcis, sous le compteur sur ordinateur : deux touches dessinées de 24 px et leur libellé. */
.tri-keys { display: flex; align-items: center; justify-content: center; gap: var(--space-2); margin: 0; font-size: var(--t-13); line-height: var(--space-6); color: var(--text-secondary); }
.tri-keys kbd { display: inline-flex; align-items: center; justify-content: center; min-width: var(--space-6); height: var(--space-6); box-sizing: border-box; padding: 0 var(--space-1); border: 1px solid var(--tri-outline); border-radius: var(--t-key-r); background: var(--surface); font: inherit; font-weight: var(--weight-bold); color: var(--text); }
.tri-keys kbd:nth-of-type(2) { margin-left: var(--space-4); }
.tri-toast button { min-height: var(--target-min); padding: 0 var(--space-3); border: 0; background: none; color: var(--snackbar-action); font-size: var(--t-15); font-weight: var(--weight-bold); }

/* Téléphone : une carte par offre, la pile derrière, le pied collé en bas. La carte grandit avec son contenu ; si
   l'écran est trop court, c'est la page qui défile. */
.tri-phone { min-height: 100dvh; background: var(--bg); }
.tri-phone .tri-head { min-height: var(--t-head); padding: 0 var(--space-4); }
.tri-phone .tri-catch { padding: var(--space-1) var(--space-6) 0; }
.tri-phone .tri-hand { font-size: var(--t-28); }
.tri-phone .tri-stage { flex: 1; margin-top: var(--t-40); padding-bottom: var(--space-8); overflow-x: clip; }
.tri-phone .tri-deck { margin: 0 var(--space-6); }
.tri-pile { position: absolute; height: var(--t-40); border-radius: var(--space-5); }
.tri-pile-far { left: var(--t-22); right: var(--t-22); top: calc(-1 * var(--t-14p)); background: var(--tri-pile-far); }
.tri-pile-near { left: var(--t-10); right: var(--t-10); top: -7px; background: var(--tri-pile-near); }
.tri-phone .tri-offer { padding: var(--t-pad); border: var(--t-3) solid var(--tri-edge); border-radius: var(--t-card-r); background: var(--surface); box-shadow: var(--tri-shadow); }
.tri-phone .tri-top { display: flex; align-items: flex-start; gap: var(--space-3); padding-right: var(--space-12); }
.tri-phone .tri-logo { width: var(--t-logo); height: var(--t-logo); }
.tri-phone .tri-names { flex: 1; min-width: 0; }
.tri-phone .tri-title { font-size: var(--t-18); line-height: var(--t-23); }
.tri-phone .tri-sub { margin-top: var(--space-1); font-size: var(--t-14); line-height: var(--t-20); }
.tri-phone .tri-score { margin-top: var(--space-3); }
.tri-phone .tri-tags { margin-top: var(--space-3); }
.tri-phone .tri-quote { margin-top: var(--space-3); padding: var(--space-3) var(--space-4); border-radius: var(--t-quote-r); background: var(--tri-quote); }
.tri-phone .tri-quote p { font-size: var(--t-15); line-height: var(--t-25); display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.tri-phone .tri-points { gap: var(--space-2); margin-top: var(--space-3); }
.tri-phone .tri-bookmark { right: var(--t-18); top: calc(-1 * var(--t-14p)); }
.tri-phone .tri-foot { position: sticky; bottom: 0; z-index: 4; display: flex; flex-direction: column; gap: var(--space-4); padding: var(--space-4) var(--space-5) max(var(--t-28), env(safe-area-inset-bottom)); border-top: 1px solid var(--tri-rule); background: var(--bg); }
.tri-phone .tri-toast { position: absolute; left: var(--space-5); right: var(--space-5); bottom: calc(100% + var(--space-4)); }

/* La carte qui part : 250 ms au plus (§1). */
.tri-fly-leave-active { position: absolute; inset: 0 0 auto; z-index: 2; transition: transform 0.25s ease-in, opacity 0.25s ease-in; transform-origin: 50% 100%; }
.tri-fly-leave-to { transform: translateX(300px) rotate(9deg); opacity: 0; }
.tri-turn-leave-active { position: absolute; inset: 0; z-index: 2; }
.tri-turn-leave-active .tri-left { visibility: hidden; }
.tri-turn-leave-active .tri-right { transition: transform 0.25s ease-in; transform-origin: left center; }
.tri-turn-leave-to .tri-right { transform: perspective(1200px) rotateY(-88deg); }
@media (prefers-reduced-motion: reduce) {
  .tri-fly-leave-active, .tri-turn-leave-active { transition: opacity 0.12s linear; }
  .tri-turn-leave-active .tri-right { transition: none; }
  .tri-fly-leave-to, .tri-turn-leave-to { transform: none; opacity: 0; }
  .tri-turn-leave-to .tri-right { transform: none; }
}

/* Ordinateur : un livre ouvert de taille fixe, les deux personnages par-dessus, les boutons puis le compteur. */
.tri:not(.tri-phone) { align-items: center; padding: var(--space-3) 0 var(--space-12); text-align: center; }
.tri:not(.tri-phone) .tri-hand { font-size: var(--t-44h); }
.tri:not(.tri-phone) .tri-stage { width: var(--t-book); margin-top: var(--t-48); text-align: left; }
.tri:not(.tri-phone) .tri-deck { z-index: 1; padding: var(--space-2) var(--space-2) var(--space-4); border-radius: var(--t-18); background: var(--tri-edge); box-shadow: var(--tri-book-shadow); }
.tri:not(.tri-phone) .tri-pile { display: none; }
.tri:not(.tri-phone) .tri-offer { display: flex; border-radius: var(--space-3); box-shadow: 0 0 0 var(--t-3) var(--tri-rim); }
.tri:not(.tri-phone) .tri-turn-leave-active { inset: var(--space-2) var(--space-2) var(--space-4); }
.tri:not(.tri-phone) :is(.tri-left, .tri-right) { box-sizing: border-box; width: var(--t-page-w); height: var(--t-page-h); overflow: hidden; background: var(--surface); }
.tri:not(.tri-phone) .tri-left { padding: var(--space-6); border-radius: var(--space-3) 0 0 var(--space-3); box-shadow: inset -18px 0 16px -12px var(--tri-fold); }
.tri:not(.tri-phone) .tri-right { padding: var(--t-84) var(--space-6) var(--space-4) var(--t-28); border-radius: 0 var(--space-3) var(--space-3) 0; box-shadow: inset 18px 0 16px -12px var(--tri-fold); }
.tri:not(.tri-phone) .tri-logo { width: var(--t-logo-wide); height: var(--t-logo-wide); }
.tri:not(.tri-phone) .tri-title { margin-top: var(--space-3); font-size: var(--t-20); line-height: var(--t-26); }
.tri:not(.tri-phone) .tri-sub { margin-top: var(--space-1); font-size: var(--t-16); line-height: var(--t-22); }
.tri:not(.tri-phone) .tri-score { margin-top: var(--space-4); }
.tri:not(.tri-phone) .tri-tags { margin-top: var(--space-3); }
.tri:not(.tri-phone) .tri-quote p:first-child { font-size: var(--t-16); line-height: var(--t-26); display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
.tri:not(.tri-phone) .tri-legend { margin-top: var(--space-3); }
.tri:not(.tri-phone) .tri-points { gap: var(--space-2); margin-top: var(--space-4); padding-top: var(--space-4); border-top: 1px dashed var(--tri-dash); }
.tri:not(.tri-phone) .tri-bookmark { left: calc(50% - var(--t-29)); top: calc(-1 * var(--t-14p)); }
.tri-sparks { position: absolute; left: calc(50% - var(--t-26)); top: -41px; fill: none; stroke: var(--tri-spark); stroke-width: 5; stroke-linecap: round; }
.tri-friend { position: absolute; z-index: 2; width: auto; pointer-events: none; }
.tri-friend-left { left: -104px; top: -6px; height: 265px; }
.tri-friend-right { left: 591px; top: 118px; height: 185px; }
.tri:not(.tri-phone) .tri-foot { display: flex; flex-direction: column; gap: var(--space-5); width: var(--t-actions); margin-top: var(--space-8); }
.tri:not(.tri-phone) .tri-actions { order: 1; }
.tri:not(.tri-phone) .tri-actions button { min-height: var(--t-btn-wide); }
.tri:not(.tri-phone) .tri-counter { order: 2; }
.tri:not(.tri-phone) .tri-keys { order: 3; margin-top: calc(var(--space-2) * -1); }
.tri:not(.tri-phone) .tri-toast { order: 4; min-height: var(--t-toast-wide); padding-left: var(--space-5); }
</style>
