<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import OfferFan from "../components/OfferFan.vue";
import ScoreRing from "../components/ScoreRing.vue";
import SignetMark from "../components/SignetMark.vue";
import TriageDone from "../components/TriageDone.vue";
import UndoToast from "../components/UndoToast.vue";
import { useArrowKeys } from "../composables/useArrowKeys";
import { markTriageDone, useDailyDose } from "../composables/useDailyDose";
import { useFocusMode } from "../composables/useFocusMode";
import { usePhone } from "../composables/usePhone";
import { useTriage } from "../composables/useTriage";
import { useUndo } from "../composables/useUndo";
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
const { queue, index, total, current, remaining, finished, kept, dismissed, decide } = useTriage(dose, () => void focusNext());
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
            v-if="remaining > 1"
            class="tri-pile tri-pile-far"
            aria-hidden="true"
          />
          <span
            v-if="remaining > 0"
            class="tri-pile tri-pile-near"
            aria-hidden="true"
          />
          <Transition name="tri-fly">
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
            </section>
          </Transition>
          <SignetMark
            class="tri-signet"
            :width="38"
          />
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
          class="tri-counter"
          data-test="triage-counter"
        >
          <i
            v-for="n in total"
            :key="n"
            :class="{ on: n === index + 1 }"
            aria-hidden="true"
          />
          <span>{{ index + 1 }} sur {{ total }}<template v-if="!phone"> · {{ plural(kept.length, "gardée", "gardées") }}</template></span>
        </p>
        <div class="tri-actions">
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
  --t-actions: 440px; --t-mark-r: 4px; --t-10: 10px; --t-14p: 14px; --t-2: 2px; --t-3: 3px;
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
.tri-read { display: inline-flex; align-items: center; min-height: var(--target-min); font-size: var(--t-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: underline; }
.tri-points { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.tri-points li { display: flex; align-items: flex-start; gap: var(--space-3); font-size: var(--t-15); line-height: var(--t-22); }
.tri-dot { flex: none; display: grid; place-items: center; width: var(--t-pip); height: var(--t-pip); border-radius: 50%; font-size: var(--t-13); font-weight: var(--weight-heavy); }
.tri-dot.ok { background: var(--tri-ok); color: var(--tri-ok-ink); }
.tri-dot.ok :deep(svg) { width: var(--t-13); height: var(--t-13); stroke-width: 3; }
.tri-dot.ask { background: var(--tri-ask); color: var(--tri-ask-ink); }
.tri-signet { position: absolute; z-index: 3; }

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
.tri-toast :deep(.tri-toast-bar) { position: absolute; left: 0; bottom: 0; width: 100%; height: 3px; background: var(--tri-count); transform-origin: left center; animation: tri-count 6s linear forwards; }
.tri-toast:is(:hover, :focus-within) :deep(.tri-toast-bar) { animation: none; }
@keyframes tri-count { to { transform: scaleX(0); } }
@media (prefers-reduced-motion: reduce) { .tri-toast :deep(.tri-toast-bar) { display: none; } }
.tri-toast :deep(button) { min-height: var(--target-min); padding: 0 var(--space-3); border: 0; background: none; color: var(--snackbar-action); font-size: var(--t-15); font-weight: var(--weight-bold); }

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
.tri-phone .tri-signet { right: var(--t-18); top: calc(-1 * var(--t-14p)); }
.tri-phone .tri-foot { position: sticky; bottom: 0; z-index: 4; display: flex; flex-direction: column; gap: var(--space-4); padding: var(--space-4) var(--space-5) max(var(--t-28), env(safe-area-inset-bottom)); border-top: 1px solid var(--tri-rule); background: var(--bg); }
.tri-phone .tri-toast { position: absolute; left: var(--space-5); right: var(--space-5); bottom: calc(100% + var(--space-4)); }

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
