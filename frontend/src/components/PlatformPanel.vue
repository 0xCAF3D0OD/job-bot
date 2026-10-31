<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type AccountOut, type PlatformOut } from "../api/client";
import { dateInList, dateInSentence, dateWithTime } from "../dates";
import { onDay, plural, untilDay } from "../format";
import AppIcon from "./AppIcon.vue";
import CopyButton from "./CopyButton.vue";
import IconButton from "./IconButton.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import InlineConfirm from "./InlineConfirm.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import StatusPill from "./StatusPill.vue";

// Plateforme (docs/65 §2, §4, §5) : les comptes, réservé à l'exploitant. De chaque compte,
// l'usage seulement (connexion, dépense de l'IA, offres reçues), jamais ses données.
type Platform = PlatformOut;
type Account = AccountOut;

const platform = ref<Platform | null>(null);

// Les étapes datées du test utilisateurs (30.10.2026) : pour chaque compte, le temps entre son
// inscription et la première fois de chaque étape. Une étape et une date, aucun contenu.
const MILESTONES = [
  { key: "first_alert", label: "Alerte" },
  { key: "first_offer", label: "Offre" },
  { key: "first_prepared", label: "Candidature" },
  { key: "first_export", label: "Preuves" },
] as const;
// Gardées jusqu'à la fin du test (décision de Kevin) : « Terminer le test » efface les dates de
// tous les comptes et arrête l'enregistrement ; un nouveau test le rouvre.
const endingTest = ref(false);
async function setUserTest(open: boolean): Promise<void> {
  endingTest.value = false;
  const { data } = await api.PUT("/api/platform/user-test", { body: { open } });
  if (data) show(data);
}
function elapsed(from: string, to: string | null | undefined): string {
  if (!to) return "—";
  const minutes = Math.max(0, Math.round((Date.parse(to) - Date.parse(from)) / 60_000));
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} h`;
  return `${Math.round(hours / 24)} j`;
}
// Où s'arrêtent les comptes qui n'ont pas fini (docs/128 §4) : l'étape à faire, et combien.
const STEP_TITLES = ["Critères et CV", "Alertes sur les sites d'emploi", "Première offre gardée", "Lettre et CV pour l'offre", "Candidature envoyée"];
const stoppedAt = computed(() =>
  (platform.value?.first_steps?.stopped_at ?? [])
    .map((count, index) => ({ label: `Étape ${index + 1} · ${STEP_TITLES[index]}`, count }))
    .filter((row) => row.count > 0),
);
const failed = ref(false);
// Le dernier lien créé, montré une seule fois, à transmettre soi-même.
const link = ref<{ kind: "invite" | "reset"; username: string | null; url: string; expires: string } | null>(null);
// Les champs chiffrés : ce qui est saisi (un nombre, ou un texte tant que le champ est vide).
const total = ref<string | number>("");
const caps = ref<Record<number, string | number>>({});
// Les demandes de compte (docs/102) : l'interrupteur.
const signupOpen = ref(true);

function money(value: string): string {
  return Number(value).toLocaleString("fr-CH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function show(data: Platform | undefined): void {
  if (!data) return;
  platform.value = data;
  total.value = String(Number(data.ai_total_budget_chf));
  signupOpen.value = data.signup_open;
  caps.value = Object.fromEntries(data.accounts.map((a) => [a.id, String(Number(a.ai_budget_chf))]));
}

async function load(): Promise<void> {
  const { data } = await api.GET("/api/platform");
  failed.value = !data;
  show(data);
}

function address(token: string): string {
  return `${window.location.origin}/acces/${token}`;
}

async function invite(): Promise<void> {
  const { data } = await api.POST("/api/platform/invitations");
  if (!data) return;
  link.value = { kind: "invite", username: null, url: address(data.token), expires: data.expires_at };
  await load();
}

// Le plafond reste visible ; les actions sur le compte dans son « ⋯ » (docs/74).
function accountItems(account: Account): MoreMenuItem[] {
  const u = account.username;
  return [
    { label: "Lien de nouveau mot de passe", test: `reset-${u}`, icon: "lock", run: () => void reset(account) },
    { label: account.suspended ? "Réactiver" : "Suspendre", test: `suspend-${u}`, icon: account.suspended ? "refresh" : "lock", run: () => void suspend(account) },
    { label: "Supprimer", test: `delete-${u}`, icon: "trash", danger: true, run: () => void remove(account) },
  ];
}

async function reset(account: Account): Promise<void> {
  const { data } = await api.POST("/api/platform/accounts/{account_id}/reset", {
    params: { path: { account_id: account.id } },
  });
  if (!data) return;
  link.value = { kind: "reset", username: account.username, url: address(data.token), expires: data.expires_at };
}

async function withdraw(id: number): Promise<void> {
  await api.DELETE("/api/platform/invitations/{link_id}", { params: { path: { link_id: id } } });
  await load();
}

// Suspendre, supprimer ou refuser se confirme dans la page, sous le compte (docs/108 §1).
type Pending = { kind: "suspend" | "delete" | "refuse"; id: number; name: string };
const confirming = ref<Pending | null>(null);
const typedName = ref("");
function ask(kind: Pending["kind"], id: number, name: string): void {
  confirming.value = { kind, id, name };
  typedName.value = "";
}
async function confirmPending(): Promise<void> {
  const pending = confirming.value;
  if (!pending) return;
  if (pending.kind === "delete" && typedName.value.trim() !== pending.name) return;
  confirming.value = null;
  const account = platform.value?.accounts.find((a) => a.id === pending.id);
  if (pending.kind === "suspend" && account) await suspend(account, true);
  else if (pending.kind === "delete" && account) await remove(account, true);
  else if (pending.kind === "refuse") await refuse(pending.id, pending.name, true);
}
const confirmMessage = computed(() => {
  const pending = confirming.value;
  if (!pending) return "";
  if (pending.kind === "suspend") return `Suspendre ${pending.name} ? Il ne pourra plus se connecter ; ses données restent.`;
  if (pending.kind === "refuse") return `Refuser la demande de ${pending.name} ? Elle sera effacée, avec le compte.`;
  return `Supprimer ${pending.name} et toutes ses données (offres, candidatures, documents) ? Rien ne sera gardé. Écris son identifiant pour confirmer.`;
});

async function suspend(account: Account, confirmed = false): Promise<void> {
  if (!account.suspended && !confirmed) return ask("suspend", account.id, account.username);
  const { data } = await api.PATCH("/api/platform/accounts/{account_id}", {
    params: { path: { account_id: account.id } },
    body: { suspended: !account.suspended },
  });
  show(data);
}

async function remove(account: Account, confirmed = false): Promise<void> {
  if (!confirmed) return ask("delete", account.id, account.username);
  const { data } = await api.DELETE("/api/platform/accounts/{account_id}", {
    params: { path: { account_id: account.id } },
  });
  show(data);
}

// L'enregistrement ligne par ligne (1.6.67, planche « 5. Réglages ») : un interrupteur ou un choix
// s'applique tout de suite, un champ chiffré quand on le quitte. « Enregistré » sur la ligne
// quelques secondes (message d'état, WCAG 4.1.3) ; une erreur sous le champ (WCAG 3.3.1).
const savedRow = ref<string | null>(null);
const rowErrors = ref<Record<string, string>>({});
let savedTimer: ReturnType<typeof setTimeout> | null = null;

function clearError(row: string): void {
  rowErrors.value = Object.fromEntries(Object.entries(rowErrors.value).filter(([key]) => key !== row));
}

function refusal(error: unknown): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  if (typeof detail === "string") return `${detail.charAt(0).toUpperCase()}${detail.slice(1)}.`;
  return "Refusé : vérifie la valeur.";
}

async function persist<T>(row: string, call: () => Promise<{ data?: T; error?: unknown }>, apply: (data: T) => void): Promise<boolean> {
  if (savedTimer) clearTimeout(savedTimer);
  savedRow.value = null;
  try {
    const { data, error } = await call();
    if (!data) {
      rowErrors.value = { ...rowErrors.value, [row]: refusal(error) };
      return false;
    }
    apply(data);
    clearError(row);
    savedRow.value = row;
    savedTimer = setTimeout(() => (savedRow.value = null), 3000);
    return true;
  } catch {
    rowErrors.value = { ...rowErrors.value, [row]: "API injoignable." };
    return false;
  }
}

// Un montant saisi (Vue rend un nombre pour un champ type="number") : null s'il est vide ou illisible.
function amount(raw: unknown): number | null {
  if (raw === null || raw === undefined || String(raw).trim() === "") return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

// Une valeur impossible n'est pas envoyée : l'ancienne reste enregistrée, la saisie reste dans le champ.
// Les bornes sont celles du serveur (routes/platform.py : AccountChange, PlatformSettingsIn).
function outOfRange(row: string, value: number | null, max: number, old: string): boolean {
  if (value !== null && value >= 0 && value <= max) return false;
  savedRow.value = null;
  rowErrors.value = { ...rowErrors.value, [row]: `Entre 0 et ${max} CHF. Le ${Number(old)} reste enregistré.` };
  return true;
}

async function saveCap(account: Account): Promise<void> {
  const row = `account-${account.id}`;
  const value = amount(caps.value[account.id]);
  if (outOfRange(row, value, 1000, account.ai_budget_chf)) return;
  if (value === Number(account.ai_budget_chf)) return clearError(row);
  await persist(
    row,
    () => api.PATCH("/api/platform/accounts/{account_id}", {
      params: { path: { account_id: account.id } },
      body: { ai_budget_chf: value },
    }),
    show,
  );
}

// La formule du compte (docs/125 §5) : Plus sans paiement, tant que le paiement n'existe pas.
async function savePlan(account: Account, plan: "essentiel" | "plus"): Promise<void> {
  await persist(
    `account-${account.id}`,
    () => api.PATCH("/api/platform/accounts/{account_id}", {
      params: { path: { account_id: account.id } },
      body: { plan },
    }),
    show,
  );
}

async function saveTotal(): Promise<void> {
  const stored = platform.value?.ai_total_budget_chf ?? "0";
  const value = amount(total.value);
  if (outOfRange("total", value, 10000, stored)) return;
  if (value === Number(stored)) return clearError("total");
  await persist("total", () => api.PUT("/api/platform/settings", { body: { ai_total_budget_chf: value } }), show);
}

// Une demande de compte (docs/102) : accepter l'active, refuser l'efface avec le compte.
async function approve(id: number): Promise<void> {
  const { data } = await api.POST("/api/platform/accounts/{account_id}/approve", {
    params: { path: { account_id: id } },
  });
  show(data);
}

async function refuse(id: number, name: string, confirmed = false): Promise<void> {
  if (!confirmed) return ask("refuse", id, name);
  const { data } = await api.DELETE("/api/platform/accounts/{account_id}", {
    params: { path: { account_id: id } },
  });
  show(data);
}

// L'interrupteur s'applique tout de suite ; refusé, il revient où il était.
async function saveSignup(): Promise<void> {
  const wanted = !signupOpen.value;
  signupOpen.value = wanted;
  const ok = await persist("signup", () => api.PUT("/api/platform/settings", { body: { signup_open: wanted } }), show);
  if (!ok) signupOpen.value = !wanted;
}

// Les mentions de la page « Tes données » (docs/65 §6) : responsable, contact, hébergeur.
// Enregistrées quand on quitte le champ, comme les autres réglages.
const mentions = ref("");
const storedMentions = ref("");

async function loadMentions(): Promise<void> {
  const { data } = await api.GET("/api/privacy");
  mentions.value = data?.contact ?? "";
  storedMentions.value = mentions.value;
}

async function saveMentions(): Promise<void> {
  if (mentions.value.trim() === storedMentions.value.trim()) return clearError("mentions");
  await persist("mentions", () => api.PUT("/api/privacy", { body: { contact: mentions.value } }), (data) => {
    storedMentions.value = data.contact ?? "";
  });
}

onMounted(async () => {
  await load();
  await loadMentions();
});

// La phrase d'un compte : son état, sa connexion, son usage du mois ; jamais ses données.
function accountLine(account: Account): string {
  const state = [account.suspended ? "Suspendu" : "", account.has_password ? "" : "Sans mot de passe"].filter(Boolean);
  const login = account.last_login_at ? `connecté ${onDay(account.last_login_at)}` : "jamais connecté";
  const usage = `ce mois : IA ${money(account.month_spend_chf)} CHF sur ${money(account.ai_budget_chf)}`;
  const offers = plural(account.month_offers, "offre reçue", "offres reçues", "aucune offre reçue");
  return [...state, `Créé ${onDay(account.created_at)}`, login, usage, offers].join(" · ");
}

function requestLine(request: Platform["signup_requests"][number]): string {
  const asked = `Demandé ${onDay(request.created_at)}`;
  return request.note ? `${asked} · « ${request.note.trim()} »` : asked;
}

function linkLine(value: NonNullable<typeof link.value>): string {
  return `${value.url} · valable une fois, ${untilDay(value.expires)}. Montré une seule fois : transmets-le toi-même.`;
}

// Les sauvegardes (docs/82) : la dernière et l'essai de restauration, dits en mots.
const backupLate = computed(() => {
  const backup = platform.value?.backup;
  if (!backup?.configured || !backup.late) return null;
  return backup.last_error
    ? { title: "Sauvegarde en échec", text: `La dernière sauvegarde a échoué : ${backup.last_error}.`, tone: "error" as const }
    : { title: "Sauvegarde en retard", text: "Aucune sauvegarde depuis plus de 36 heures.", tone: "todo" as const };
});
const backupLast = computed(() => {
  const backup = platform.value?.backup;
  if (!backup) return "";
  const kept = `${plural(backup.count, "sauvegarde gardée", "sauvegardes gardées")} dans ${backup.folder}.`;
  return backup.last_at
    ? `Faite ${dateWithTime(backup.last_at)}, ${size(backup.last_size)} · ${kept}`
    : `Pas encore de sauvegarde : la première se fait dans l'heure. ${kept}`;
});
const backupTest = computed(() => {
  const backup = platform.value?.backup;
  if (!backup?.test_at) return { text: "Pas encore d'essai : il se fait chaque dimanche.", state: "À venir", tone: "neutral" } as const;
  return backup.test_ok
    ? ({ text: `Dernier essai ${dateInList(backup.test_at)}.`, state: "Réussi", tone: "ok" } as const)
    : ({ text: `Dernier essai ${dateInList(backup.test_at)} : ${backup.test_error}.`, state: "Échec", tone: "error" } as const);
});

// Taille d'une sauvegarde (docs/82) : en Mo, ou en Ko sous le Mo.
function size(bytes: number | null | undefined): string {
  if (!bytes) return "taille inconnue";
  if (bytes < 1_000_000) return `${Math.max(1, Math.round(bytes / 1000))} Ko`;
  return `${(bytes / 1_000_000).toLocaleString("fr-CH", { maximumFractionDigits: 1 })} Mo`;
}
</script>

<template>
  <p
    v-if="failed"
    class="notice error"
  >
    Impossible de lire les comptes pour l'instant.
  </p>
  <!-- L'administration (1.6.67, planche « 5. Réglages ») : des cartes de lignes ; chaque ligne, son
       titre, une phrase et son contrôle ou son action à droite. -->
  <template v-else-if="platform">
    <p
      v-if="platform.database_admin"
      class="notice error"
      role="alert"
      data-test="platform-database-admin"
    >
      Le serveur se connecte à la base en administrateur : la séparation des comptes ne tient qu'à lui.
      Dans le fichier <code>.env</code>, utilise le rôle <code>jobbot_app</code> pour l'API et
      <code>jobbot_worker</code> pour le worker (voir <code>docs/exploitation.md</code>, « Accès à la base »).
    </p>
    <p
      v-if="!platform.auth_enabled"
      class="notice"
      data-test="platform-auth-disabled"
    >
      Connexion désactivée : les comptes invités ne peuvent pas se connecter.
    </p>

    <!-- Les demandes en tête (docs/102) : accepter l'active, refuser l'efface avec le compte. -->
    <SettingCard
      v-if="platform.signup_requests.length"
      class="platform-card"
      data-test="platform-requests"
    >
      <SettingRow
        title="Demandes en attente"
        :description="`${plural(platform.signup_requests.length, 'personne attend', 'personnes attendent')} ta réponse.`"
      />
      <template
        v-for="request in platform.signup_requests"
        :key="request.id"
      >
        <SettingRow
          :title="request.username"
          :description="requestLine(request)"
          :data-test="`request-${request.username}`"
        >
          <button
            type="button"
            class="secondary small"
            :aria-label="`Accepter ${request.username}`"
            :data-test="`approve-${request.username}`"
            @click="approve(request.id)"
          >
            <span class="with-icon"><AppIcon name="done" />Accepter</span>
          </button>
          <button
            type="button"
            class="secondary small danger"
            :aria-label="`Refuser ${request.username}`"
            :data-test="`refuse-${request.username}`"
            @click="refuse(request.id, request.username)"
          >
            Refuser
          </button>
        </SettingRow>
        <InlineConfirm
          v-if="confirming?.kind === 'refuse' && confirming.id === request.id"
          :message="confirmMessage"
          confirm-label="Refuser"
          @confirm="confirmPending"
          @cancel="confirming = null"
        />
      </template>
    </SettingCard>

    <!-- Les comptes (docs/65 §5) : de chacun, l'usage seulement ; la formule et le plafond sur place,
         le reste dans son « ⋯ » (docs/74). -->
    <SettingCard
      class="platform-card"
      data-test="platform-accounts"
    >
      <SettingRow
        title="Comptes"
        description="Leur usage seulement : connexion, dépense de l'IA, offres reçues."
      />
      <template
        v-for="account in platform.accounts"
        :key="account.id"
      >
        <SettingRow
          v-slot="c"
          :title="account.is_owner ? `${account.username} (toi)` : account.username"
          :description="accountLine(account)"
          :saved="savedRow === `account-${account.id}`"
          :error="rowErrors[`account-${account.id}`]"
          :stack="!account.is_owner"
          :data-test="`account-${account.username}`"
        >
          <template v-if="!account.is_owner">
            <select
              :value="account.plan"
              :aria-labelledby="`${c.labelledby} plan-label-${account.id}`"
              :aria-describedby="c.describedby"
              :data-test="`plan-${account.username}`"
              @change="savePlan(account, ($event.target as HTMLSelectElement).value as 'essentiel' | 'plus')"
            >
              <option value="essentiel">
                Essentiel
              </option>
              <option value="plus">
                Plus
              </option>
            </select>
            <span
              :id="`plan-label-${account.id}`"
              class="visually-hidden"
            >formule</span>
            <input
              v-model="caps[account.id]"
              class="setting-number"
              type="number"
              inputmode="decimal"
              min="0"
              max="1000"
              step="0.5"
              :aria-labelledby="`${c.labelledby} cap-label-${account.id}`"
              :aria-describedby="c.describedby"
              :aria-invalid="c.invalid"
              :data-test="`cap-${account.username}`"
              @change="saveCap(account)"
            >
            <span :id="`cap-label-${account.id}`">CHF d'IA / mois</span>
            <MoreMenu
              :items="accountItems(account)"
              :label="`Plus d'actions sur le compte ${account.username}`"
              :test-id="`account-more-${account.username}`"
            />
          </template>
        </SettingRow>
        <InlineConfirm
          v-if="confirming && confirming.kind !== 'refuse' && confirming.id === account.id"
          :message="confirmMessage"
          :confirm-label="confirming.kind === 'suspend' ? 'Suspendre' : 'Supprimer'"
          :busy="confirming.kind === 'delete' && typedName.trim() !== account.username"
          @confirm="confirmPending"
          @cancel="confirming = null"
        >
          <input
            v-if="confirming.kind === 'delete'"
            v-model="typedName"
            type="text"
            autocomplete="off"
            :aria-label="`Identifiant de ${account.username}`"
            :placeholder="account.username"
            data-test="delete-account-name"
          >
        </InlineConfirm>
      </template>
    </SettingCard>

    <!-- Les nouveaux comptes : les demandes ouvertes ou fermées, les invitations. Un lien créé est
         montré une seule fois, à transmettre soi-même. -->
    <SettingCard
      class="platform-card"
      data-test="platform-invite"
    >
      <SettingRow
        v-slot="c"
        title="Demandes de compte"
        :description="signupOpen
          ? 'Ouvertes : on peut demander un compte depuis la page de connexion.'
          : 'Fermées : seules tes invitations ouvrent un compte.'"
        :saved="savedRow === 'signup'"
        :error="rowErrors.signup"
      >
        <input
          type="checkbox"
          role="switch"
          :checked="signupOpen"
          :aria-labelledby="c.labelledby"
          :aria-describedby="c.describedby"
          data-test="signup-open"
          @change="saveSignup"
        >
      </SettingRow>
      <SettingRow
        title="Inviter quelqu'un"
        description="Un lien de création de compte, valable une fois."
      >
        <button
          type="button"
          class="secondary small"
          data-test="invite"
          @click="invite"
        >
          <span class="with-icon"><AppIcon name="users" />Créer un lien</span>
        </button>
      </SettingRow>
      <SettingRow
        v-if="link"
        class="platform-link"
        :title="link.kind === 'invite' ? 'Lien d\'invitation' : `Lien de nouveau mot de passe pour ${link.username}`"
        :description="linkLine(link)"
        data-test="platform-link"
      >
        <CopyButton
          :value="link.url"
          label="Copier le lien"
          test-id="platform-link-copy"
        />
      </SettingRow>
      <SettingRow
        v-for="invitation in platform.invitations"
        :key="invitation.id"
        :title="`Invitation ${dateInSentence(invitation.created_at).replace(/^le /, 'du ')}`"
        :description="`Pas encore utilisée, valable ${untilDay(invitation.expires_at)}.`"
        data-test="platform-invitation"
      >
        <IconButton
          icon="trash"
          label="Retirer l'invitation"
          danger
          data-test="invitation-withdraw"
          @click="withdraw(invitation.id)"
        />
      </SettingRow>
    </SettingCard>

    <!-- Les premiers pas (docs/128 §4) : des nombres seulement, jamais un nom ni un contenu. -->
    <SettingCard
      v-if="platform.first_steps"
      class="platform-card"
      data-test="platform-first-steps"
    >
      <SettingRow
        title="Premiers pas"
        :description="platform.first_steps.accounts
          ? 'Les comptes créés depuis 30 jours, en nombres seulement.'
          : 'Aucun compte créé depuis 30 jours.'"
      />
      <template v-if="platform.first_steps.accounts">
        <SettingRow
          title="Première candidature dans les 7 jours"
          description="Les comptes qui ont envoyé une candidature dans leur première semaine."
          data-test="first-steps-rate"
        >
          <strong>{{ platform.first_steps.sent_within_week }} sur {{ platform.first_steps.accounts }}</strong>
        </SettingRow>
        <SettingRow
          v-for="row in stoppedAt"
          :key="row.label"
          :title="row.label"
          description="Les comptes arrêtés à cette étape, pas encore faite."
          data-test="first-steps-stopped"
        >
          <strong>{{ plural(row.count, "compte", "comptes") }}</strong>
        </SettingRow>
      </template>
    </SettingCard>

    <!-- Le test utilisateurs (30.10.2026) : le temps entre l'inscription et chaque première étape.
         Des numéros de compte et des durées, jamais un nom ni un contenu. -->
    <SettingCard
      class="platform-card"
      data-test="platform-milestones"
    >
      <SettingRow
        title="Test utilisateurs"
        :description="!platform.user_test_open
          ? 'Aucun test en cours : rien n\'est enregistré.'
          : platform.milestones?.length
            ? 'Le temps entre l\'inscription et la première fois de chaque étape. Gardé jusqu\'à la fin du test.'
            : 'Aucun compte invité pour l\'instant.'"
      >
        <button
          v-if="platform.user_test_open"
          type="button"
          class="secondary small"
          data-test="user-test-end"
          @click="endingTest = true"
        >
          Terminer le test
        </button>
        <button
          v-else
          type="button"
          class="secondary small"
          data-test="user-test-start"
          @click="setUserTest(true)"
        >
          Commencer un test
        </button>
      </SettingRow>
      <InlineConfirm
        v-if="endingTest"
        message="Les dates de tous les comptes sont effacées, et plus rien n'est enregistré."
        confirm-label="Terminer et effacer"
        @confirm="setUserTest(false)"
        @cancel="endingTest = false"
      />
      <table
        v-if="platform.user_test_open && platform.milestones?.length"
        class="runs milestones-table"
        data-test="milestones-table"
      >
        <thead>
          <tr>
            <th scope="col">
              Compte
            </th>
            <th
              v-for="column in MILESTONES"
              :key="column.key"
              scope="col"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in platform.milestones"
            :key="row.account"
            data-test="milestones-row"
          >
            <th scope="row">
              n° {{ row.account }}<span class="milestones-since">{{ dateInList(row.created_at) }}</span>
            </th>
            <td
              v-for="column in MILESTONES"
              :key="column.key"
            >
              {{ elapsed(row.created_at, row[column.key]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </SettingCard>

    <!-- Les sauvegardes (docs/82) : l'état en mots à droite, pas seulement en couleur (WCAG 1.4.1). -->
    <SettingCard
      v-if="platform.backup"
      class="platform-card"
      data-test="platform-backup"
    >
      <SettingRow
        v-if="!platform.backup.configured"
        title="Sauvegardes"
        description="Ajoute JOBBOT_BACKUP_PASSPHRASE dans .env, puis redémarre (docs/82)."
        data-test="backup-not-configured"
      >
        <StatusPill
          tone="todo"
          data-test="backup-state"
        >
          Non réglées
        </StatusPill>
      </SettingRow>
      <template v-else>
        <SettingRow
          v-if="backupLate"
          :title="backupLate.title"
          :description="backupLate.text"
          role="alert"
          data-test="backup-late"
        >
          <StatusPill
            :tone="backupLate.tone"
            data-test="backup-state"
          >
            À vérifier
          </StatusPill>
        </SettingRow>
        <SettingRow
          title="Dernière sauvegarde"
          :description="backupLast"
          data-test="backup-last"
        >
          <StatusPill
            :tone="platform.backup.late ? (platform.backup.last_error ? 'error' : 'todo') : 'ok'"
            data-test="backup-state"
          >
            {{ platform.backup.late ? "En retard" : "À jour" }}
          </StatusPill>
        </SettingRow>
        <SettingRow
          title="Essai de restauration"
          :description="backupTest.text"
          data-test="backup-test"
        >
          <StatusPill
            :tone="backupTest.tone"
            data-test="backup-state"
          >
            {{ backupTest.state }}
          </StatusPill>
        </SettingRow>
      </template>
    </SettingCard>

    <!-- Les mentions publiques (docs/65 §6) : enregistrées quand on quitte le champ ; la page en action
         à droite de sa ligne, jamais en lien dans la phrase. -->
    <SettingCard
      class="platform-card platform-mentions"
      data-test="platform-mentions"
    >
      <SettingRow
        v-slot="c"
        title="Mentions de la page « Données personnelles »"
        description="Responsable, contact, hébergement. Publiques, même sans compte."
        :saved="savedRow === 'mentions'"
        :error="rowErrors.mentions"
        wide
      >
        <textarea
          id="platform-mentions"
          v-model="mentions"
          rows="4"
          maxlength="4000"
          :aria-labelledby="c.labelledby"
          :aria-describedby="c.describedby"
          :aria-invalid="c.invalid"
          data-test="mentions"
          @change="saveMentions"
        />
      </SettingRow>
      <SettingRow
        title="Page « Données personnelles »"
        description="Ce que voient les visiteurs, avec tes mentions."
      >
        <RouterLink
          to="/tes-donnees"
          class="button-link"
          data-test="see-privacy"
        >
          Voir la page
        </RouterLink>
      </SettingRow>
    </SettingCard>

    <!-- L'IA de la plateforme : le plafond total s'enregistre au changement (docs/106 §5). -->
    <SettingCard
      class="platform-card"
      data-test="platform-ai"
    >
      <SettingRow
        v-slot="c"
        title="Plafond total de l'IA, tous comptes"
        description="Au-delà, l'IA s'arrête pour tous jusqu'au mois suivant."
        :saved="savedRow === 'total'"
        :error="rowErrors.total"
        stack
      >
        <input
          id="platform-total"
          v-model="total"
          class="setting-number"
          type="number"
          inputmode="decimal"
          min="0"
          max="10000"
          step="1"
          :aria-labelledby="c.labelledby"
          :aria-describedby="c.describedby"
          :aria-invalid="c.invalid"
          data-test="platform-total"
          @change="saveTotal"
        >
        <span>CHF / mois</span>
      </SettingRow>
      <SettingRow
        title="Dépense du mois"
        description="Tous comptes confondus."
        data-test="platform-spend"
      >
        <strong>{{ money(platform.ai_month_spend_chf) }} CHF</strong>
      </SettingRow>
    </SettingCard>
  </template>
  <!-- Le temps du chargement : des blocs gris à la forme des cartes (règles §4). -->
  <LoadingBlocks
    v-else
    :heights="['12rem', '10rem', '6rem']"
  />
</template>
