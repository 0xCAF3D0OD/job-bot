<script setup lang="ts">
import { computed, ref, useId } from "vue";

import type { AlertsPage } from "../api/client";
import type { SearchGroup, SiteState } from "../alertsState";
import AppIcon from "./AppIcon.vue";
import BlockRow from "./BlockRow.vue";
import BottomSheet from "./BottomSheet.vue";
import SidePanel from "./SidePanel.vue";
import "../blocks.css";

// Les alertes e-mail sur téléphone (MODIFICATIONS du 8 novembre au soir, §10.8 ; maquettes AlertesTel,
// AlertesTelConfirmer, AlertesTelAlerte) : une carte cliquable (D29) par recherche et par site, rangées par famille
// (« À confirmer », « Actives », « À créer » ; une famille vide n'est pas affichée), puis « + Ajouter une recherche ».
// La carte ouvre la feuille « Alerte » : le rappel, « La recherche » (lieux, site), puis selon l'état confirmer,
// créer, ou les actions ; « Ne plus suivre cette recherche » partout.
// `desk` (maquette AlertesOrdinateur du 9 novembre, §2.8) : la même liste sur ordinateur ; « lieux · site » sous le
// titre, le mot d'état à droite en couleur, « + Ajouter une recherche » dans l'en-tête de la page ; la feuille devient
// le panneau de droite (`al`, `cf`), et la note sur le filtre Gmail ferme la liste
// (seulement avec l'adresse par compte, où les e-mails arrivent par ce filtre).
// `highlighted` : la recherche venue de la recherche globale (?recherche=…), ses cartes sont mises en avant.
const props = defineProps<{ page: AlertsPage; groups: SearchGroup[]; desk?: boolean; highlighted?: string | null }>();
const emit = defineEmits<{
  add: [];
  create: [site: string, terms: string];
  remove: [group: SearchGroup];
  confirmed: [searchId: number];
}>();

type Kind = "confirm" | "active" | "todo";
interface Card {
  key: string;
  group: SearchGroup;
  site: SearchGroup["sites"][number];
  kind: Kind;
  places: string;
  confirm: { url: string; search_id: number } | null;
}

const STATE_WORD: Record<SiteState["kind"], (label: string) => string> = {
  received: (label) => label.charAt(0).toLowerCase() + label.slice(1),
  quiet: (label) => label,
  waiting: () => "en attente du premier envoi",
  silent: () => "rien reçu depuis la création",
  todo: () => "pas encore créée",
};

const cards = computed<Card[]>(() =>
  props.groups
    .filter((group) => group.active)
    .flatMap((group) =>
      group.sites.map((site) => {
        const confirm = props.page.to_confirm?.find((c) => c.site === site.slug && group.ids.includes(c.search_id)) ?? null;
        const kind: Kind = confirm ? "confirm" : site.state.kind === "todo" ? "todo" : "active";
        return { key: `${group.terms}-${site.slug}`, group, site, kind, places: group.locations.join(", ") || "Toute la Suisse", confirm };
      }),
    ),
);
const DESK_WORD: Record<SiteState["kind"], (label: string) => string> = {
  received: (label) => label,
  quiet: (label) => label,
  waiting: () => "En attente du premier envoi",
  silent: () => "Rien reçu depuis la création",
  todo: () => "Pas encore créée",
};
function aside(card: Card): { text: string; tone: "todo" | "plain" | "muted" } {
  if (card.kind === "confirm") return { text: "Confirmation demandée", tone: "todo" };
  if (card.kind === "todo") return { text: DESK_WORD.todo(""), tone: "muted" };
  return { text: DESK_WORD[card.site.state.kind](card.site.state.label), tone: card.site.state.kind === "silent" ? "todo" : "plain" };
}
const status = (card: Card) =>
  `${card.site.name} · ${card.kind === "confirm" ? "confirmation demandée" : STATE_WORD[card.site.state.kind](card.site.state.label)}`;

const confirmNames = computed(() => [...new Set(cards.value.filter((c) => c.kind === "confirm").map((c) => c.site.name))]);
const families = computed(() =>
  [
    {
      kind: "confirm" as const,
      title: "À confirmer",
      help: `${confirmNames.value.join(" et ")} ${confirmNames.value.length > 1 ? "attendent" : "attend"} ta confirmation avant d’envoyer les offres. Ouvre l’alerte pour confirmer.`,
    },
    { kind: "active" as const, title: "Actives", help: "Les offres reçues par e-mail arrivent dans « À traiter »." },
    { kind: "todo" as const, title: "À créer", help: "La recherche existe dans jobA1, pas encore sur le site." },
  ]
    .map((family) => ({ ...family, id: `alerts-fam-${family.kind}`, cards: cards.value.filter((c) => c.kind === family.kind) }))
    .filter((family) => family.cards.length),
);

// La feuille « Alerte ».
const shown = ref<Card | null>(null);
const open = ref(false);
const searchId = useId();
const actionsId = useId();
function show(card: Card): void {
  shown.value = card;
  open.value = true;
}
const stateLine = computed(() => {
  const card = shown.value;
  if (!card) return "";
  if (card.kind === "confirm") return `À confirmer sur ${card.site.name}`;
  if (card.kind === "todo") return `À créer sur ${card.site.name}`;
  return `Active · ${STATE_WORD[card.site.state.kind](card.site.state.label)}`;
});
function confirm(): void {
  if (shown.value?.confirm) emit("confirmed", shown.value.confirm.search_id);
  open.value = false;
}
function create(): void {
  if (shown.value) emit("create", shown.value.site.slug, shown.value.group.terms);
  open.value = false;
}
function remove(): void {
  if (shown.value) emit("remove", shown.value.group);
  open.value = false;
}
</script>

<template>
  <div
    :class="['blocks-page', 'alerts-families', { desk }]"
    data-test="alert-searches"
  >
    <section
      v-for="family in families"
      :key="family.kind"
      :class="['alerts-family', family.kind]"
      :aria-labelledby="family.id"
      :data-test="`alerts-family-${family.kind}`"
    >
      <h2
        :id="family.id"
        class="alerts-family-title"
      >
        {{ family.title }} · {{ family.cards.length }}
      </h2>
      <p class="alerts-family-help">
        {{ family.help }}
      </p>
      <BlockRow
        v-for="card in family.cards"
        :key="card.key"
        :title="card.group.terms"
        :lines="desk ? [`${card.places} · ${card.site.name}`] : [card.places, status(card)]"
        :aside="desk ? aside(card) : null"
        :class="{ highlighted: !!highlighted && card.group.terms === highlighted }"
        aria-haspopup="dialog"
        :data-test="`alert-card-${card.group.ids[0]}-${card.site.slug}`"
        @click="show(card)"
      />
    </section>
    <button
      v-if="!desk"
      type="button"
      class="secondary action-2 alerts-add-phone"
      data-test="add-search"
      @click="emit('add')"
    >
      + Ajouter une recherche
    </button>
  </div>
  <component
    :is="desk ? SidePanel : BottomSheet"
    :open="open"
    title="Alerte"
    @close="open = false"
  >
    <div
      v-if="shown"
      class="alert-sheet"
      data-test="alert-sheet"
    >
      <div class="sheet-sum">
        <div class="sheet-sum-text">
          <b>{{ shown.group.terms }}</b>
          <span
            :class="['alert-sheet-state', shown.kind]"
            data-test="alert-sheet-state"
          >{{ stateLine }}</span>
        </div>
      </div>
      <section
        class="sheet-group"
        :aria-labelledby="searchId"
      >
        <h3
          :id="searchId"
          class="sheet-group-title"
        >
          La recherche
        </h3>
        <ul class="sheet-items">
          <li class="sheet-item">
            <div>
              <div class="sheet-key">
                Lieux
              </div>
              <div class="sheet-text">
                {{ shown.places }}
              </div>
            </div>
          </li>
          <li class="sheet-item">
            <div>
              <div class="sheet-key">
                Site
              </div>
              <div class="sheet-text">
                {{ shown.site.name }}, par e-mail
              </div>
            </div>
          </li>
        </ul>
      </section>
      <template v-if="shown.kind === 'confirm' && shown.confirm">
        <p class="sheet-note">
          {{ shown.site.name }} a envoyé un e-mail de confirmation. Tant que tu ne confirmes pas, aucune offre n’arrive.
        </p>
        <a
          class="sheet-cta"
          :href="shown.confirm.url"
          target="_blank"
          rel="noopener noreferrer"
          data-test="alert-confirm"
          @click="confirm"
        >Confirmer sur {{ shown.site.name }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
      </template>
      <template v-else-if="shown.kind === 'todo'">
        <p class="sheet-note">
          La recherche existe dans jobA1, pas encore sur {{ shown.site.name }}.
        </p>
        <button
          type="button"
          class="sheet-cta alert-sheet-cta"
          data-test="alert-create"
          @click="create"
        >
          Créer l’alerte sur {{ shown.site.name }}
        </button>
      </template>
      <section
        v-else
        class="sheet-group"
        :aria-labelledby="actionsId"
      >
        <h3
          :id="actionsId"
          class="sheet-group-title"
        >
          Actions
        </h3>
        <div class="sheet-items">
          <RouterLink
            class="sheet-link"
            :to="{ path: '/candidatures/offres', query: { site: shown.site.slug } }"
            data-test="alert-offers"
            @click="open = false"
          >
            Voir les offres de cette alerte<AppIcon name="chevron" />
          </RouterLink>
          <a
            v-if="shown.site.url"
            class="sheet-link"
            :href="shown.site.url"
            target="_blank"
            rel="noopener noreferrer"
            data-test="alert-edit"
          ><span class="with-icon">Modifier sur {{ shown.site.name }}<AppIcon name="external" /></span><span class="visually-hidden"> (nouvel onglet)</span></a>
          <button
            type="button"
            class="sheet-link danger"
            data-test="alert-remove"
            @click="remove"
          >
            Ne plus suivre cette recherche
          </button>
        </div>
      </section>
      <button
        v-if="shown.kind !== 'active'"
        type="button"
        class="sheet-link danger center"
        data-test="alert-remove"
        @click="remove"
      >
        Ne plus suivre cette recherche
      </button>
    </div>
  </component>
  <p
    v-if="desk && page.personal_address"
    class="alerts-desk-note"
    data-test="alerts-note"
  >
    jobA1 lit seulement les e-mails d’alerte transférés par ton filtre Gmail. Les autres sont supprimés à la réception.
  </p>
</template>

<style>
/* Valeurs du HTML d'AlertesTel : familles à 16 px l'une de l'autre (plus l'écart de la page), sur-titre 13/16 en
   capitales dans la couleur de l'état, aide 14/20 avec 4 px dessous, 8 px entre les cartes ; « + Ajouter une
   recherche » sur toute la largeur, 48 px. */
.alerts-families { display: flex; flex-direction: column; gap: var(--space-4); }
.alerts-family { display: flex; flex-direction: column; gap: var(--space-2); }
.alerts-family + .alerts-family { margin-top: var(--space-4); }
.alerts-family-title { margin: 0; font-size: var(--label-caps); line-height: var(--space-4); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
.alerts-family.confirm .alerts-family-title { color: var(--peach-text); }
.alerts-family.active .alerts-family-title { color: var(--success); }
.alerts-family-help { margin: 0 0 var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.alerts-families .block-row { margin: 0; background: var(--surface); border: 1.5px solid var(--card-line); }
/* Les lieux sont coupés avec « … » (§10.8) ; la ligne « site · état » passe à la ligne sur les écrans étroits (§2.8). */
.alerts-families .block-row-line:last-child { white-space: normal; }
.alerts-families.blocks-page { background: transparent; }
.alerts-families .alerts-add-phone { width: 100%; height: var(--btn-tertiary); min-height: var(--btn-tertiary); justify-content: center; }
/* §2.9 : sous la liste, « J'attends un code » et « Afficher plus » ont aussi 44 px de haut. */
.alerts-phone :is(.show-more, button.small) { min-height: var(--target-min); }
.alert-sheet { display: contents; }
.alerts-desk-note { margin: 0 var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.alert-sheet-state { font-weight: var(--weight-bold); }
.alert-sheet-state.active { color: var(--success); }
.alert-sheet-state.confirm { color: var(--peach-text); }
/* Ordinateur (AlertesOrdinateur, §2.8) : 32 px entre les familles, 8 px entre les cartes ; carte de 72 px, 20 px de
   marge trait compris, rayon 18, 16 px entre le texte, le mot et le cercle de 36 px. */
.alerts-families.desk { --alerts-pad-y: 14.5px; --alerts-pad-x: 18.5px; gap: var(--space-8); }
.alerts-families.desk .alerts-family + .alerts-family { margin-top: 0; }
.alerts-families.desk :is(.alerts-family-title, .alerts-family-help) { margin-left: var(--space-1); margin-right: var(--space-1); }
.alerts-families.desk .block-row { gap: var(--space-4); min-height: var(--row-72); padding: var(--alerts-pad-y) var(--alerts-pad-x); border-radius: var(--radius-card); }
.alerts-families.desk .block-row:hover { border-color: var(--primary-graphic); }
.alerts-families .block-row.highlighted { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.alerts-families.desk .block-row .arrow-circle { --circle: 36px; }
button.sheet-link, button.sheet-cta { width: 100%; padding: 0; border: 0; border-radius: 0; background: none; font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; cursor: pointer; }
button.sheet-cta { border-radius: var(--radius-pill); background: var(--action); color: var(--on-action); font-size: var(--font-body); justify-content: center; }
</style>
