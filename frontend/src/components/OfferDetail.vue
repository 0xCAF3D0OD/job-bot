
<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Offer, type RegistryCandidate } from "../api/client";
import { dateInList } from "../dates";
import { expiredText, gapSkill, plural, rateText, remoteText, sourceLabel } from "../format";
import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import DisclosureRow from "./DisclosureRow.vue";
import ContactsPanel from "./ContactsPanel.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import ScoreWord from "./ScoreWord.vue";
import GapFill from "./GapFill.vue";
import ScoreCorrection from "./ScoreCorrection.vue";
import SidePanel from "./SidePanel.vue";
import { useAssistant } from "../composables/useAssistant";

import HoverNote from "./HoverNote.vue";
import IconButton from "./IconButton.vue";
const props = defineProps<{ offer: Offer; chunkTitles?: Record<number, string> }>();

// Les contacts dans le panneau latéral (docs/32 §2.2) ; l'entreprise a sa section (docs/45).
const contactsOpen = ref(false);
const contactsCount = ref(0);
// L'annonce repliée à 6 lignes (docs/45) : « Lire toute l'annonce » la déplie.
const LONG_TEXT = 420;
const textOpen = ref(false);
const textEl = ref<HTMLElement | null>(null);
const textHeight = ref<string | undefined>(undefined);
function openText(): void {
  textHeight.value = textEl.value ? `${textEl.value.scrollHeight}px` : undefined;
  textOpen.value = true;
}
watch(
  () => props.offer.id,
  () => {
    contactsOpen.value = false;
    contactsCount.value = 0;
    textOpen.value = false;
    textHeight.value = undefined;
  },
);
const emit = defineEmits<{
  close: [];
  status: [status: "to_review" | "later" | "ignored" | "preparing"];
  applied: [];
  expiry: [expired: boolean];
  address: [address: string];
  changed: [];
}>();

// Annonce chez l'employeur (docs/20 §2) : lien vérifié, ou recherche à la demande.
const PROXY_HOSTS = ["jobup.ch", "jobs.ch", "indeed.", "linkedin.com", "glassdoor.", "jobscout24.", "job-room.ch"];
const EMPLOYER_SOURCES: Record<string, string> = {
  site: "sur son site",
  ats: "via son outil de recrutement",
  web: "sur Internet",
};
const employerBusy = ref(false);
const employerMessage = ref("");
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });
// Lien vers l'employeur déjà donné par l'annonce jobup : rien à chercher.
const employerKnown = computed(() => {
  const url = props.offer.apply_url;
  return props.offer.apply_kind === "external" && !!url && !PROXY_HOSTS.some((h) => url.includes(h));
});

async function findEmployer(): Promise<void> {
  employerBusy.value = true;
  employerMessage.value = "";
  try {
    const { data, error } = await api.POST("/api/offers/{offer_id}/employer", {
      params: { path: { offer_id: props.offer.id } },
    });
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      employerMessage.value = typeof detail === "string" ? `Recherche impossible : ${detail}.` : "Recherche impossible.";
      return;
    }
    // L'état (« Pas trouvée… », lien trouvé) s'affiche avec l'offre rechargée : pas de second message.
    emit("changed");
  } finally {
    employerBusy.value = false;
  }
}

// Bouton « Postuler » (docs/21 §5) : chez l'employeur si l'annonce y est, sinon sur le site.
const postLink = computed(() => {
  const o = props.offer;
  if (o.employer_url) return { url: o.employer_url, label: "Postuler chez l'employeur" };
  if (o.apply_url) {
    return { url: o.apply_url, label: o.apply_kind === "external" ? "Postuler chez l'employeur" : "Postuler sur jobup" };
  }
  const link = o.links[0];
  if (link?.source === "manual") return { url: link.url, label: "Ouvrir l'annonce" };
  return link ? { url: link.url, label: `Postuler sur ${sourceLabel[link.source]}` } : null;
});

// Registre IDE (docs/12 §2.2) : propositions quand le nom ne suffit pas à trancher.
const searching = ref(false);
const proposals = ref<RegistryCandidate[]>([]);
const registryMessage = ref("");

async function searchRegistry(): Promise<void> {
  searching.value = true;
  registryMessage.value = "";
  proposals.value = [];
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/address-candidates", {
      params: { path: { offer_id: props.offer.id } },
    });
    if (!data) {
      registryMessage.value = "Registre IDE injoignable, réessaie plus tard.";
    } else if (data.chosen_uid && props.offer.company_address_source !== "registry") {
      registryMessage.value = "Adresse trouvée dans le registre IDE.";
      emit("changed");
    } else if (data.web_address) {
      registryMessage.value = "Adresse trouvée sur Internet : vérifie la source.";
      proposals.value = data.candidates;
      emit("changed");
    } else {
      proposals.value = data.candidates;
      const web = data.web_unavailable
        ? ` Recherche sur Internet impossible : ${data.web_unavailable}.`
        : " Rien de fiable sur Internet non plus.";
      registryMessage.value = data.candidates.length
        ? `Pas de correspondance sûre : choisis parmi le registre, ou saisis l'adresse.${web}`
        : `Aucune entreprise à ce nom dans le registre.${web} Saisis l'adresse à la main.`;
    }
  } catch {
    registryMessage.value = "API injoignable.";
  } finally {
    searching.value = false;
  }
}

async function chooseRegistry(uid: string): Promise<void> {
  const { data } = await api.POST("/api/offers/{offer_id}/address-candidates/choose", {
    params: { path: { offer_id: props.offer.id } },
    body: { uid },
  });
  proposals.value = [];
  registryMessage.value = data ? "" : "Choix refusé.";
  if (data) emit("changed");
}

const STATUS_LABEL: Partial<Record<Offer["status"], string>> = {
  preparing: "En préparation",
  later: "Plus tard",
  ignored: "Ignorée",
  filtered_out: "Écartée par le filtre",
  applied: "Candidature envoyée",
};
const statusLabel = computed(() =>
  props.offer.expired_at && props.offer.status !== "applied" ? "Expirée" : (STATUS_LABEL[props.offer.status] ?? ""),
);
const pillClass = computed(() =>
  props.offer.expired_at && props.offer.status !== "applied" ? "expired" : props.offer.status,
);
// « À savoir » (planche « Fiche d'une offre ») : une ligne « libellé : valeur » pour ce qui est
// connu seulement ; l'adresse a toujours sa ligne (« Adresse inconnue · Ajouter »). Puis les faits à
// vérifier : alerte à vérifier, croix pour la raison d'un écart.
type Fact = { mark: "check" | "no"; text: string; excerpt?: string; scam?: boolean };
const MARKS: Record<Fact["mark"], IconName> = { check: "alert", no: "x-circle" };
const rows = computed(() => {
  const o = props.offer;
  const rate = rateText(o.rate_min, o.rate_max).replace("–", " à ");
  // La ligne s'appelle déjà « Télétravail » : la valeur ne le répète pas (« 2 jours par semaine »).
  const remote =
    o.remote === "hybrid" && o.remote_days
      ? `${plural(o.remote_days, "jour", "jours")} par semaine`
      : o.remote === "hybrid"
        ? "Partiel"
        : remoteText(o)?.replace(" télétravail", "");
  return [
    ...(rate ? [{ test: "rate", label: "Taux", value: rate }] : []),
    ...(remote ? [{ test: "remote", label: "Télétravail", value: remote }] : []),
    ...(o.employment_type ? [{ test: "contract", label: "Contrat", value: o.employment_type }] : []),
    ...(o.first_seen_at ? [{ test: "received", label: "Reçue", value: dateInList(o.first_seen_at) }] : []),
  ];
});
const facts = computed<Fact[]>(() => {
  const o = props.offer;
  const list: Fact[] = [];
  if (o.remote_from_switzerland === false) list.push({ mark: "check", text: "Télétravail pas ouvert depuis la Suisse" });
  for (const doubt of o.doubts ?? []) {
    list.push({ mark: "check", text: doubt.text, excerpt: doubt.excerpt ?? undefined, scam: doubt.kind === "scam" });
  }
  for (const reason of o.filter_reasons ?? []) list.push({ mark: "no", text: reason });
  if (o.enrich_status === "expired") list.push({ mark: "no", text: "L'annonce n'est plus en ligne sur jobup." });
  return list;
});
// Points forts et manques (planche) : trois au plus, le mot clé en gras en tête (« Kubernetes : … »).
const POINTS_MAX = 3;
function pointParts(text: string): { key: string; rest: string } {
  const match = /^([^:]{1,40}?)\s?:\s+(.+)$/.exec(text.trim());
  return match ? { key: match[1]!, rest: match[2]! } : { key: "", rest: text };
}
const strengths = computed(() => (props.offer.strengths ?? []).slice(0, POINTS_MAX));
const gaps = computed(() => (props.offer.gaps ?? []).slice(0, POINTS_MAX));
// Les annonces d'origine qui ne sont pas déjà le bouton « Postuler » (docs/45 : pas de doublon).
const otherLinks = computed(() =>
  props.offer.links.filter((link) => props.offer.status === "applied" || link.url !== postLink.value?.url),
);
const ADDRESS_SOURCE: Record<string, string> = {
  page: "annonce",
  registry: "registre IDE",
  web: "trouvée sur Internet",
  letter: "relevée dans l'annonce",
  manual: "saisie par toi",
};

// Menu « ⋯ » : les actions rares, hors de la vue principale (docs/12 §1, docs/45, docs/50 §1).
const assistant = useAssistant();
function askAssistant(): void {
  const o = props.offer;
  assistant.askAbout({ offerId: o.id, label: `offre ${o.title}${o.company ? ` chez ${o.company}` : ""}` });
}

// Sous la note, en petit : elle ne porte que sur l'extrait de l'alerte. Les autres réserves suivent
// la phrase « pourquoi ».
const scoreNote = computed(() => {
  const o = props.offer;
  return [o.score_stale && "Ton profil a changé depuis : note à refaire.", o.score === null && "Pas de note : aucun bloc de profil actif."]
    .filter(Boolean)
    .join(" ");
});
const menuItems = computed<MoreMenuItem[]>(() => {
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  if (o.status !== "applied") {
    items.push({ label: "J'ai postulé", test: "mark-applied", icon: "check-circle", run: () => emit("applied") });
    if (o.status === "later" || o.status === "ignored" || o.status === "preparing") {
      items.push({ label: "Remettre à examiner", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
    } else {
      items.push({ label: "Plus tard", test: "later", icon: "clock", run: () => emit("status", "later") });
      items.push({ label: "Ignorer", test: "ignore", icon: "x-circle", run: () => emit("status", "ignored") });
    }
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "alert", run: () => emit("expiry", true) },
    );
  }
  if (assistant.available.value) {
    items.push({ label: "Demander à l'assistant", test: "ask-assistant", icon: "ai", run: askAssistant });
  }
  return items;
});

// Partie « Entreprise » (docs/74) : l'adresse visible, les actions dans son « ⋯ ».
const canSearchEmployer = computed(
  () =>
    !employerKnown.value &&
    props.offer.employer_status !== "agency" &&
    !(props.offer.employer_url && props.offer.employer_checked_at),
);
const companyItems = computed<MoreMenuItem[]>(() => {
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  if (o.company_address) items.push({ label: "Modifier l'adresse", test: "edit-address", icon: "pencil", run: startAddress });
  if (o.company && o.company_address_source !== "manual" && o.company_address_source !== "page") {
    items.push({
      label: "Chercher l'adresse",
      test: "search-registry",
      icon: "ai",
      disabled: searching.value,
      run: () => void searchRegistry(),
    });
  }
  if (canSearchEmployer.value) {
    items.push({
      label: o.employer_checked_at ? "Chercher à nouveau chez l'employeur" : "Chercher l'offre chez l'employeur",
      test: "find-employer",
      icon: "ai",
      disabled: employerBusy.value,
      run: () => void findEmployer(),
    });
  }
  if (o.company) {
    items.push({ label: "Contacts", test: "open-contacts", icon: "users", count: contactsCount.value, run: () => (contactsOpen.value = true) });
  }
  if (o.company_address_source === "web" && o.company_address_url) {
    items.push({ label: "Vérifier la source de l'adresse", test: "address-source", href: o.company_address_url });
  }
  return items;
});
// Le site de l'annonce, résumé de la ligne « Annonce » repliée.
const adSource = computed(() => {
  const link = props.offer.links[0];
  return link && link.source !== "manual" ? sourceLabel[link.source] : "";
});
// Les annonces d'origine, dans le « ⋯ » de la partie « Annonce ».
const announceItems = computed<MoreMenuItem[]>(() =>
  otherLinks.value.map((link) => ({ label: `Voir sur ${sourceLabel[link.source]}`, test: `source-${link.source}`, href: link.url })),
);

const editingAddress = ref(false);
const addressDraft = ref("");
function startAddress(): void {
  addressDraft.value = props.offer.company_address ?? "";
  editingAddress.value = true;
}
function saveAddress(): void {
  editingAddress.value = false;
  emit("address", addressDraft.value);
}
watch(
  () => props.offer.id,
  () => {
    editingAddress.value = false;
    proposals.value = [];
    registryMessage.value = "";
  },
);
</script>


<template>
  <article
    class="detail-panel"
    data-test="offer-detail"
  >
    <!-- Sur téléphone, le retour en haut à gauche, au-dessus de la fiche (règles §2). -->
    <button
      type="button"
      class="link detail-back"
      data-test="back-detail"
      @click="$emit('close')"
    >
      <span class="with-icon"><AppIcon name="arrow-left" /><span><span class="visually-hidden">Retour aux </span>Offres</span></span>
    </button>

    <!-- L'offre (planche « Fiche d'une offre ») : logo, poste, « Entreprise · Lieu », les deux actions ;
         tout le reste dans « ⋯ », toujours le dernier à droite. -->
    <section
      class="detail-card detail-offer"
      data-test="section-offer"
    >
      <div class="detail-head">
        <CompanyLogo
          :offer="offer"
          large
        />
        <div class="detail-title">
          <h2
            tabindex="-1"
            data-test="offer-detail-title"
          >
            {{ offer.title }}
          </h2>
          <p
            class="detail-sub"
            data-test="detail-meta"
          >
            <span class="visually-hidden">Entreprise : </span>{{ offer.company ?? "Entreprise non indiquée"
            }}<template v-if="offer.location">
              · <span class="visually-hidden">Lieu : </span>{{ offer.location }}
            </template>
          </p>
          <div
            v-if="statusLabel"
            class="status-line"
          >
            <span
              :class="['status-pill', pillClass]"
              data-test="status-pill"
            >{{ statusLabel }}</span>
            <RouterLink
              v-if="offer.status === 'applied'"
              to="/candidatures/suivi"
              class="link"
            >
              Voir le suivi
            </RouterLink>
          </div>
        </div>
        <div class="detail-top-actions">
          <!-- Fermer (croix) sur écran moyen ; sur téléphone, le retour aux offres. -->
          <IconButton
            icon="close"
            label="Fermer le détail"
            class="detail-close"
            data-test="close-detail"
            @click="$emit('close')"
          />
          <MoreMenu
            v-if="menuItems.length"
            :items="menuItems"
            label="Plus d'actions sur l'offre"
          />
        </div>
      </div>
      <p
        v-if="offer.expired_at && offer.status !== 'applied'"
        class="notice expired-notice"
        data-test="expired"
      >
        {{ expiredText(offer) }}
      </p>
      <div
        v-if="offer.status !== 'applied'"
        class="detail-actions"
        data-test="triage"
      >
        <RouterLink
          :to="`/candidatures/offres/${offer.id}/preparer`"
          class="button-link primary-link"
          data-test="prepare"
        >
          {{ offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
        </RouterLink>
        <a
          v-if="postLink"
          :href="postLink.url"
          target="_blank"
          rel="noopener noreferrer"
          class="button-link"
          :data-test="offer.employer_url ? 'employer' : 'apply'"
        ><span class="with-icon"><AppIcon name="send" />{{ postLink.label }}<span class="visually-hidden"> (nouvel onglet)</span></span></a>
      </div>
    </section>

    <!-- Pourquoi : la note, la phrase, « Cette note ne me correspond pas ». -->
    <section
      v-if="offer.summary_role || offer.score_error || offer.why"
      class="detail-card"
      data-test="section-for-you"
    >
      <h3>Pourquoi</h3>
      <template v-if="offer.summary_role || offer.why">
        <div
          v-if="offer.score !== null && offer.score !== undefined"
          class="detail-note"
          data-test="ai"
        >
          <ScoreWord :score="offer.score" />
          <p
            v-if="offer.summary_partial"
            class="hint"
            data-test="score-partial"
          >
            Sur l'extrait de l'alerte seulement
          </p>
        </div>
        <div
          v-if="offer.why || offer.level"
          class="score-why"
          data-test="score-why"
        >
          <p v-if="offer.why">
            {{ offer.why }}
          </p>
          <p
            v-if="offer.level"
            class="level-line"
            data-test="score-level"
          >
            <HoverNote :text="offer.level_detail ?? ''">
              {{ offer.level === "above" ? "Niveau au-dessus" : "Niveau en dessous" }}
            </HoverNote>
          </p>
        </div>
        <p
          v-if="scoreNote"
          class="hint score-note"
          data-test="score-note"
        >
          {{ scoreNote }}
        </p>
        <!-- « Cette note ne me correspond pas » (docs/114). -->
        <ScoreCorrection
          v-if="offer.score !== null && offer.score !== undefined"
          :offer-id="offer.id"
          @changed="emit('changed')"
        />
      </template>
      <p
        v-else
        class="hint"
      >
        Note impossible : {{ offer.score_error }}
      </p>
    </section>

    <!-- Points forts, puis Manques : trois puces au plus, le mot clé en gras en tête. -->
    <section
      v-if="strengths.length || gaps.length"
      class="detail-card detail-points"
      data-test="section-points"
    >
      <template v-if="strengths.length">
        <h3>Points forts</h3>
        <ul data-test="strengths">
          <li
            v-for="point in strengths"
            :key="point.text"
          >
            <strong v-if="pointParts(point.text).key">{{ pointParts(point.text).key }} :</strong>
            {{ pointParts(point.text).rest }}
          </li>
        </ul>
      </template>
      <template v-if="gaps.length">
        <h3>Manques</h3>
        <ul
          class="gaps"
          data-test="gaps"
        >
          <li
            v-for="point in gaps"
            :key="point.text"
          >
            <strong v-if="pointParts(point.text).key">{{ pointParts(point.text).key }} :</strong>
            {{ pointParts(point.text).rest }}
            <!-- Une exigence absente du profil (aucun bloc cité) : « Je l'ai » (docs/121 §C.3). -->
            <GapFill
              v-if="!point.chunk_ids.length && gapSkill(point.text)"
              :offer-id="offer.id"
              :gap="point.text"
              @added="emit('changed')"
            />
          </li>
        </ul>
      </template>
    </section>

    <!-- À savoir : « libellé : valeur », seulement ce qui est connu ; l'adresse toujours. -->
    <section
      class="detail-card"
      data-test="section-facts"
    >
      <h3>À savoir</h3>
      <dl
        class="detail-rows"
        data-test="terms"
      >
        <div
          v-for="row in rows"
          :key="row.test"
          :data-test="`term-${row.test}`"
        >
          <dt>{{ row.label }}</dt>
          <dd>{{ row.value }}</dd>
        </div>
        <div data-test="address">
          <dt>Adresse</dt>
          <dd v-if="editingAddress">
            <form
              class="address-form"
              @submit.prevent="saveAddress"
            >
              <textarea
                v-model="addressDraft"
                rows="2"
                placeholder="Rue et numéro&#10;NPA localité"
                aria-label="Adresse de l'entreprise"
                data-test="address-input"
              />
              <div>
                <button
                  type="submit"
                  class="secondary small"
                  data-test="save-address"
                >
                  Enregistrer
                </button>
                <button
                  type="button"
                  class="link"
                  @click="editingAddress = false"
                >
                  Annuler
                </button>
              </div>
            </form>
          </dd>
          <dd v-else-if="offer.company_address">
            {{ offer.company_address.split("\n").join(", ") }}
            <span class="hint">· {{ ADDRESS_SOURCE[offer.company_address_source ?? "manual"] }}</span>
          </dd>
          <dd v-else>
            Adresse inconnue · <button
              type="button"
              class="link"
              data-test="add-address"
              @click="startAddress"
            >
              Ajouter
            </button>
          </dd>
        </div>
      </dl>
      <p
        v-if="searching"
        class="hint"
        role="status"
      >
        Recherche dans le registre IDE…
      </p>
      <div
        v-if="registryMessage || proposals.length"
        class="registry-proposals"
        data-test="registry"
      >
        <p
          v-if="registryMessage"
          class="hint"
        >
          {{ registryMessage }}
        </p>
        <ul v-if="proposals.length">
          <li
            v-for="proposal in proposals"
            :key="proposal.uid"
          >
            <span>
              <strong>{{ proposal.name }}</strong><br>
              <span class="muted">{{ proposal.address.split("\n").join(", ") }}</span>
            </span>
            <button
              type="button"
              class="secondary small"
              data-test="choose-registry"
              @click="chooseRegistry(proposal.uid)"
            >
              Choisir
            </button>
          </li>
        </ul>
      </div>
      <ul
        v-if="facts.length"
        class="offer-facts"
        data-test="facts"
      >
        <li
          v-for="fact in facts"
          :key="fact.mark + fact.text"
          :class="[fact.mark, { scam: fact.scam }]"
        >
          <span
            class="fact-mark"
            :data-mark="fact.mark"
          ><AppIcon :name="MARKS[fact.mark]" /></span>
          <span>
            {{ fact.text }}
            <q v-if="fact.excerpt">{{ fact.excerpt }}</q>
          </span>
        </li>
      </ul>
    </section>

    <!-- L'entreprise et l'annonce, moins utiles pour décider, repliées (règles §3.4). -->
    <DisclosureRow
      title="Entreprise"
      :value="offer.company ?? ''"
      class="detail-disclosure"
      data-test="company-section"
    >
      <template
        v-if="companyItems.length"
        #actions
      >
        <MoreMenu
          class="section-more"
          :items="companyItems"
          label="Plus d'actions sur l'entreprise"
          test-id="company-more"
        />
      </template>
      <p
        v-if="!employerKnown && (offer.employer_checked_at || offer.employer_status === 'agency' || employerBusy || employerMessage)"
        class="hint employer-line"
        data-test="employer-line"
      >
        <span
          v-if="employerBusy"
          role="status"
        >Recherche chez l'employeur en cours (jusqu'à 30 s)…</span>
        <span
          v-else-if="offer.employer_url && offer.employer_checked_at"
        >Trouvée chez l'employeur {{ EMPLOYER_SOURCES[offer.employer_url_source ?? "web"] }}, vérifiée le
          {{ shortDate.format(new Date(offer.employer_checked_at)) }}.</span>
        <span v-else-if="offer.employer_status === 'agency'">Annonce d'agence : employeur non indiqué.</span>
        <span v-else-if="offer.employer_status === 'not_found'">Pas trouvée chez l'employeur.</span>
        <span v-else-if="offer.employer_status === 'gone'">L'annonce a disparu du site de l'employeur.</span>
        <span
          v-if="employerMessage"
          role="status"
        >{{ employerMessage }}</span>
      </p>
      <p
        v-else
        class="hint"
      >
        {{ offer.company ? "Contacts, adresse et recherche chez l'employeur : dans ⋯." : "Entreprise non indiquée dans l'annonce." }}
      </p>
    </DisclosureRow>
    <SidePanel
      v-if="offer.company"
      :open="contactsOpen"
      :title="`Contacts chez ${offer.company}`"
      @close="contactsOpen = false"
    >
      <ContactsPanel
        :key="offer.id"
        :offer-id="offer.id"
        @count="contactsCount = $event"
      />
    </SidePanel>

    <DisclosureRow
      title="Annonce"
      :value="adSource"
      class="detail-disclosure"
      data-test="section-ad"
    >
      <template
        v-if="announceItems.length"
        #actions
      >
        <MoreMenu
          class="section-more"
          :items="announceItems"
          label="Plus d'actions sur l'annonce"
          test-id="ad-more"
        />
      </template>
      <template v-if="offer.description">
        <div
          ref="textEl"
          :class="['full-text', { folded: !textOpen && offer.description.length > LONG_TEXT }]"
          :style="textOpen && textHeight ? { maxHeight: textHeight } : undefined"
          data-test="description"
        >
          {{ offer.description }}
        </div>
        <button
          v-if="!textOpen && offer.description.length > LONG_TEXT"
          type="button"
          class="link read-more"
          data-test="read-more"
          @click="openText"
        >
          <span class="with-icon">Lire toute l'annonce<AppIcon name="chevron-down" /></span>
        </button>
      </template>
      <p
        v-else-if="offer.snippet"
        class="detail-snippet"
      >
        {{ offer.snippet }}
      </p>
      <p
        v-else
        class="detail-snippet"
      >
        Pas d'extrait dans l'alerte : le texte complet de l'annonce est sur le site.
      </p>
    </DisclosureRow>
  </article>
</template>
