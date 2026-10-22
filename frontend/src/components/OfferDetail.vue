
<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Offer, type RegistryCandidate } from "../api/client";
import { expiredText, formatDate, gapSkill, rateText, remoteText, sourceLabel } from "../format";
import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
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

function sources(ids: number[]): string {
  return ids
    .map((id) => props.chunkTitles?.[id])
    .filter(Boolean)
    .join(", ");
}
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
// « À savoir » (docs/45, docs/101) : taux, télétravail et contrat en pastilles, puis une ligne par
// fait : cercle coché sûr, alerte à vérifier, croix raison d'un écart, œil pour les passages.
type Fact = { mark: "ok" | "check" | "no" | "seen"; text: string; hidden?: string; excerpt?: string; scam?: boolean };
const MARKS: Record<Fact["mark"], IconName> = { ok: "check-circle", check: "alert", no: "x-circle", seen: "eye" };
const terms = computed(() => {
  const o = props.offer;
  const rate = rateText(o.rate_min, o.rate_max);
  const remote = remoteText(o);
  return [
    { test: "rate", icon: "rate" as IconName, hidden: rate ? "Taux : " : "", text: rate || "Taux non indiqué" },
    ...(remote ? [{ test: "remote", icon: "home" as IconName, hidden: "", text: remote }] : []),
    ...(o.employment_type ? [{ test: "contract", icon: "briefcase" as IconName, hidden: "Contrat : ", text: o.employment_type }] : []),
  ];
});
const facts = computed<Fact[]>(() => {
  const o = props.offer;
  const list: Fact[] = [
    { mark: "seen", hidden: "Vue ", text: `${o.seen_count} fois, depuis le ${formatDate(o.first_seen_at)}` },
  ];
  if (o.remote_from_switzerland === false) list.push({ mark: "check", text: "Télétravail pas ouvert depuis la Suisse" });
  for (const doubt of o.doubts ?? []) {
    list.push({ mark: "check", text: doubt.text, excerpt: doubt.excerpt ?? undefined, scam: doubt.kind === "scam" });
  }
  for (const reason of o.filter_reasons ?? []) list.push({ mark: "no", text: reason });
  if (o.enrich_status === "expired") list.push({ mark: "no", text: "L'annonce n'est plus en ligne sur jobup." });
  return list;
});
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

const scoreNote = computed(() => {
  const o = props.offer;
  return [
    o.summary_partial && "Sur l'extrait de l'alerte seulement.",
    o.score_stale && "Ton profil a changé depuis : note à refaire.",
    o.score === null && "Pas de note : aucun bloc de profil actif.",
  ]
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
    <div class="detail-top">
      <CompanyLogo
        :offer="offer"
        large
      />
      <div class="detail-top-actions">
        <!-- Tout sauf les deux actions principales, dans « ⋯ » (docs/45, docs/50 §1). -->
        <MoreMenu
          v-if="menuItems.length"
          :items="menuItems"
          label="Actions sur l'offre"
        />
        <!-- Fermer (croix) sur écran moyen ; sur téléphone, le retour aux offres (docs/101). -->
        <IconButton
          icon="close"
          label="Fermer le détail"
          class="detail-close"
          data-test="close-detail"
          @click="$emit('close')"
        />
        <button
          type="button"
          class="link detail-back"
          data-test="back-detail"
          @click="$emit('close')"
        >
          <span class="with-icon"><AppIcon name="arrow-left" /><span><span class="visually-hidden">Retour aux </span>Offres</span></span>
        </button>
      </div>
    </div>
    <div>
      <h2
        tabindex="-1"
        data-test="offer-detail-title"
      >
        {{ offer.title }}
      </h2>
      <span
        class="detail meta-line"
        data-test="detail-meta"
      >
        <span><AppIcon name="building" /><span class="visually-hidden">Entreprise : </span>{{ offer.company ?? "Entreprise non indiquée" }}</span>
        <span v-if="offer.location"><AppIcon name="pin" /><span class="visually-hidden">Lieu : </span>{{ offer.location }}</span>
      </span>
      <div class="status-line">
        <span
          v-if="statusLabel"
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
    <p
      v-if="offer.expired_at && offer.status !== 'applied'"
      class="notice expired-notice"
      data-test="expired"
    >
      {{ expiredText(offer) }}
    </p>

    <!-- Deux boutons seulement (docs/45) : préparer, postuler. -->
    <div
      v-if="offer.status !== 'applied'"
      class="triage mobile-dock"
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

    <section
      v-if="offer.summary_role || offer.score_error"
      class="panel-section"
      data-test="section-for-you"
    >
      <h3>
        <HoverNote text="Résumé et note par l'IA : elle compare l'annonce à tes blocs de profil actifs. Les points forts citent le bloc d'où ils viennent.">
          Pour toi
        </HoverNote>
      </h3>
      <template v-if="offer.summary_role">
        <div
          class="ai-head"
          data-test="ai"
        >
          <!-- La note en mot, le chiffre au survol (docs/131 §A.4). -->
          <ScoreWord
            v-if="offer.score !== null && offer.score !== undefined"
            :score="offer.score"
          />
          <dl class="summary">
            <div><dt>Poste</dt><dd>{{ offer.summary_role }}</dd></div>
            <div><dt>Demande</dt><dd>{{ offer.summary_asks }}</dd></div>
            <!-- « À savoir » le dit déjà en pastilles (docs/131 §A.3). -->
            <div v-if="!terms.length">
              <dt>Offre</dt><dd>{{ offer.summary_offers }}</dd>
            </div>
          </dl>
        </div>
        <!-- Pourquoi cette note, en une phrase, et le niveau visé (docs/121 §C.1-2). -->
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
        <div
          v-if="offer.strengths?.length || offer.gaps?.length"
          class="points"
        >
          <div v-if="offer.strengths?.length">
            <h4>Points forts</h4>
            <ul data-test="strengths">
              <li
                v-for="point in offer.strengths"
                :key="point.text"
              >
                <!-- Le bloc d'où vient le point, au survol (docs/131 §B.7). -->
                <HoverNote
                  v-if="sources(point.chunk_ids)"
                  :text="`Bloc : ${sources(point.chunk_ids)}`"
                >
                  {{ point.text }}
                </HoverNote>
                <template v-else>
                  {{ point.text }}
                </template>
              </li>
            </ul>
          </div>
          <div v-if="offer.gaps?.length">
            <h4>Manques</h4>
            <ul
              class="gaps"
              data-test="gaps"
            >
              <li
                v-for="point in offer.gaps"
                :key="point.text"
              >
                {{ point.text }}
                <!-- Une exigence absente du profil (aucun bloc cité) : « Je l'ai » (docs/121 §C.3). -->
                <GapFill
                  v-if="!point.chunk_ids.length && gapSkill(point.text)"
                  :offer-id="offer.id"
                  :gap="point.text"
                  @added="emit('changed')"
                />
              </li>
            </ul>
          </div>
        </div>
      </template>
      <p
        v-else
        class="hint"
      >
        Note impossible : {{ offer.score_error }}
      </p>
    </section>

    <section
      class="panel-section"
      data-test="section-facts"
    >
      <h3>À savoir</h3>
      <ul
        class="meta-chips offer-terms"
        data-test="terms"
      >
        <li
          v-for="term in terms"
          :key="term.test"
          class="meta-chip"
          :data-test="`term-${term.test}`"
        >
          <AppIcon :name="term.icon" /><span><span
            v-if="term.hidden"
            class="visually-hidden"
          >{{ term.hidden }}</span>{{ term.text }}</span>
        </li>
      </ul>
      <ul
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
            <span
              v-if="fact.hidden"
              class="visually-hidden"
            >{{ fact.hidden }}</span>{{ fact.text }}
            <q v-if="fact.excerpt">{{ fact.excerpt }}</q>
          </span>
        </li>
      </ul>
    </section>

    <section
      class="panel-section"
      data-test="company-section"
    >
      <div class="panel-section-head">
        <h3>Entreprise</h3>
        <MoreMenu
          v-if="companyItems.length"
          class="section-more"
          :items="companyItems"
          label="Actions sur l'entreprise"
          test-id="company-more"
        />
      </div>
      <div
        class="address-line"
        data-test="address"
      >
        <template v-if="!editingAddress">
          <span
            class="address-icon"
            data-test="address-icon"
          ><AppIcon name="pin" /><span class="visually-hidden">Adresse : </span></span>
          <span v-if="offer.company_address">
            {{ offer.company_address.split("\n").join(", ") }}
            <span class="hint">· {{ ADDRESS_SOURCE[offer.company_address_source ?? "manual"] }}</span>
          </span>
          <template v-else>
            <span class="hint">inconnue</span>
            <button
              type="button"
              class="link"
              data-test="add-address"
              @click="startAddress"
            >
              <span class="with-icon"><AppIcon name="plus" />Ajouter l'adresse</span>
            </button>
          </template>
        </template>
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
        <form
          v-if="editingAddress"
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
      </div>
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
    </section>
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

    <section
      class="panel-section"
      data-test="section-ad"
    >
      <div class="panel-section-head">
        <h3>Annonce</h3>
        <MoreMenu
          v-if="announceItems.length"
          class="section-more"
          :items="announceItems"
          label="Actions sur l'annonce"
          test-id="ad-more"
        />
      </div>
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
    </section>
  </article>
</template>
