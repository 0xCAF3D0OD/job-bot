<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type AccountOut, type PlatformOut } from "../api/client";
import { formatDate, plural, since } from "../format";
import AppIcon from "./AppIcon.vue";
import CopyLabel from "./CopyLabel.vue";
import IconButton from "./IconButton.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import InlineConfirm from "./InlineConfirm.vue";

// Plateforme (docs/65 §2, §4, §5) : les comptes, réservé à l'exploitant. De chaque compte,
// l'usage seulement (connexion, dépense de l'IA, offres reçues), jamais ses données.
type Platform = PlatformOut;
type Account = AccountOut;

const platform = ref<Platform | null>(null);
// Où s'arrêtent les comptes qui n'ont pas fini (docs/128 §4) : l'étape à faire, et combien.
const STEP_TITLES = ["Dis ce que tu cherches", "Crée tes alertes", "Garde ta première offre", "Prépare ta candidature", "Marque-la comme envoyée"];
const stoppedAt = computed(() =>
  (platform.value?.first_steps?.stopped_at ?? [])
    .map((count, index) => ({ label: `Étape ${index + 1} · ${STEP_TITLES[index]}`, count }))
    .filter((row) => row.count > 0),
);
const failed = ref(false);
// Le dernier lien créé, montré une seule fois, à transmettre soi-même.
const link = ref<{ kind: "invite" | "reset"; username: string | null; url: string; expires: string } | null>(null);
const copied = ref(false);
const total = ref("");
const message = ref("");
const caps = ref<Record<number, string>>({});
// Les demandes de compte (docs/102) : l'interrupteur et ce qu'il dit après l'enregistrement.
const signupOpen = ref(true);
const signupMessage = ref("");

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
  copied.value = false;
  await load();
}

// Le plafond reste visible ; les actions sur le compte dans son « ⋯ » (docs/74).
function accountItems(account: Account): MoreMenuItem[] {
  const u = account.username;
  return [
    { label: "Lien de nouveau mot de passe", test: `reset-${u}`, icon: "lock", run: () => void reset(account) },
    { label: account.suspended ? "Réactiver" : "Suspendre", test: `suspend-${u}`, icon: account.suspended ? "refresh" : "lock", run: () => void suspend(account) },
    { label: "Supprimer", test: `delete-${u}`, danger: true, run: () => void remove(account) },
  ];
}

async function reset(account: Account): Promise<void> {
  const { data } = await api.POST("/api/platform/accounts/{account_id}/reset", {
    params: { path: { account_id: account.id } },
  });
  if (!data) return;
  link.value = { kind: "reset", username: account.username, url: address(data.token), expires: data.expires_at };
  copied.value = false;
}

async function copy(): Promise<void> {
  if (!link.value) return;
  await navigator.clipboard.writeText(link.value.url);
  copied.value = true;
  setTimeout(() => (copied.value = false), 2000);
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

async function saveCap(account: Account): Promise<void> {
  const value = Number(caps.value[account.id]);
  if (!Number.isFinite(value) || value < 0) return;
  const { data } = await api.PATCH("/api/platform/accounts/{account_id}", {
    params: { path: { account_id: account.id } },
    body: { ai_budget_chf: value },
  });
  show(data);
}

// La formule du compte (docs/125 §5) : Plus sans paiement, tant que le paiement n'existe pas.
async function savePlan(account: Account, plan: "essentiel" | "plus"): Promise<void> {
  const { data } = await api.PATCH("/api/platform/accounts/{account_id}", {
    params: { path: { account_id: account.id } },
    body: { plan },
  });
  show(data);
}

async function saveTotal(): Promise<void> {
  const { data } = await api.PUT("/api/platform/settings", {
    body: { ai_total_budget_chf: Number(total.value) },
  });
  show(data);
  message.value = data ? "Enregistré" : "Valeur refusée.";
  if (data) setTimeout(() => message.value === "Enregistré" && (message.value = ""), 1500);
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

async function saveSignup(): Promise<void> {
  const wanted = !signupOpen.value;
  const { data } = await api.PUT("/api/platform/settings", { body: { signup_open: wanted } });
  show(data);
  signupMessage.value = data
    ? wanted ? "Demandes de compte ouvertes." : "Demandes de compte fermées."
    : "Enregistrement impossible.";
}

// Les mentions de la page « Tes données » (docs/65 §6) : responsable, contact, hébergeur.
const mentions = ref("");
const mentionsMessage = ref("");

async function loadMentions(): Promise<void> {
  const { data } = await api.GET("/api/privacy");
  mentions.value = data?.contact ?? "";
}

async function saveMentions(): Promise<void> {
  const { data } = await api.PUT("/api/privacy", { body: { contact: mentions.value } });
  mentionsMessage.value = data ? "Mentions enregistrées." : "Enregistrement impossible.";
}

onMounted(async () => {
  await load();
  await loadMentions();
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
      La connexion est désactivée sur cette installation : les comptes invités ne pourront pas se connecter.
    </p>
    <div
      v-if="platform.signup_requests.length"
      class="form-card"
      data-test="platform-requests"
    >
      <fieldset>
        <legend>Demandes de compte</legend>
        <ul class="platform-accounts">
          <li
            v-for="request in platform.signup_requests"
            :key="request.id"
            :data-test="`request-${request.username}`"
          >
            <div class="platform-account-head">
              <strong>{{ request.username }}</strong>
            </div>
            <p class="meta-line muted">
              <span><AppIcon name="clock" /><span class="visually-hidden">Demandé le </span>{{ formatDate(request.created_at) }}</span>
            </p>
            <p
              v-if="request.note"
              class="muted platform-request-note"
            >
              {{ request.note }}
            </p>
            <div class="platform-actions">
              <button
                type="button"
                class="secondary"
                :data-test="`approve-${request.username}`"
                @click="approve(request.id)"
              >
                <span class="with-icon"><AppIcon name="done" />Accepter</span>
              </button>
              <button
                type="button"
                class="secondary danger"
                :data-test="`refuse-${request.username}`"
                @click="refuse(request.id, request.username)"
              >
                Refuser
              </button>
            </div>
            <InlineConfirm
              v-if="confirming?.kind === 'refuse' && confirming.id === request.id"
              :message="confirmMessage"
              confirm-label="Refuser"
              @confirm="confirmPending"
              @cancel="confirming = null"
            />
          </li>
        </ul>
      </fieldset>
    </div>
    <div
      class="form-card"
      :class="{ 'settings-next-card': platform.signup_requests.length }"
      data-test="platform-accounts"
    >
      <fieldset>
        <legend>Comptes</legend>
        <ul class="platform-accounts">
          <li
            v-for="account in platform.accounts"
            :key="account.id"
            :data-test="`account-${account.username}`"
          >
            <div class="platform-account-head">
              <strong>{{ account.username }}</strong>
              <span
                v-if="account.is_owner"
                class="badge"
              >toi</span>
              <span
                v-if="account.suspended"
                class="badge warn"
              >suspendu</span>
              <span
                v-if="!account.has_password"
                class="badge"
              >sans mot de passe</span>
            </div>
            <p class="hint">
              Créé le {{ formatDate(account.created_at) }} ·
              {{ account.last_login_at ? `connecté le ${formatDate(account.last_login_at)}` : "jamais connecté" }}
            </p>
            <p class="platform-usage">
              Ce mois : IA {{ money(account.month_spend_chf) }} CHF sur {{ money(account.ai_budget_chf) }} ·
              {{ plural(account.month_offers, "offre reçue", "offres reçues", "aucune offre reçue") }}
            </p>
            <div
              v-if="!account.is_owner"
              class="platform-actions"
            >
              <label class="inline-field">
                <span>Formule</span>
                <select
                  :value="account.plan"
                  :data-test="`plan-${account.username}`"
                  @change="savePlan(account, ($event.target as HTMLSelectElement).value as 'essentiel' | 'plus')"
                >
                  <option value="essentiel">Essentiel</option>
                  <option value="plus">Plus</option>
                </select>
              </label>
              <label class="inline-field">
                <span>Plafond IA</span>
                <input
                  v-model="caps[account.id]"
                  type="number"
                  min="0"
                  max="1000"
                  step="0.5"
                  :data-test="`cap-${account.username}`"
                  @change="saveCap(account)"
                >
                <span>CHF / mois</span>
              </label>
              <MoreMenu
                class="section-more"
                :items="accountItems(account)"
                :label="`Actions sur le compte ${account.username}`"
                :test-id="`account-more-${account.username}`"
              />
            </div>
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
          </li>
        </ul>
        <div class="platform-signup">
          <label class="filter-switch">
            <input
              type="checkbox"
              role="switch"
              :checked="signupOpen"
              data-test="signup-open"
              @change="saveSignup"
            >
            <span>Accepter des demandes de compte</span>
          </label>
          <span
            v-if="signupMessage"
            role="status"
            class="muted"
          >{{ signupMessage }}</span>
        </div>
        <div class="form-actions">
          <button
            type="button"
            class="secondary"
            data-test="invite"
            @click="invite"
          >
            <span class="with-icon"><AppIcon name="users" />Inviter quelqu'un</span>
          </button>
        </div>
        <div
          v-if="link"
          class="extension-token platform-link"
          data-test="platform-link"
        >
          <p>
            {{ link.kind === "invite" ? "Lien d'invitation" : `Lien de nouveau mot de passe pour ${link.username}` }},
            valable jusqu'au {{ formatDate(link.expires) }} :
          </p>
          <code>{{ link.url }}</code>
          <button
            type="button"
            class="link"
            @click="copy"
          >
            <CopyLabel
              :done="copied"
              label="Copier le lien"
            />
          </button>
          <p class="hint">
            Montré une seule fois, valable une fois : transmets-le toi-même.
          </p>
        </div>
        <ul
          v-if="platform.invitations.length"
          class="extension-tokens"
          data-test="platform-invitations"
        >
          <li
            v-for="invitation in platform.invitations"
            :key="invitation.id"
          >
            <span>Invitation du {{ formatDate(invitation.created_at) }}
              <span class="muted">· valable jusqu'au {{ formatDate(invitation.expires_at) }}</span></span>
            <IconButton
              icon="trash"
              label="Retirer l'invitation"
              danger
              data-test="invitation-withdraw"
              @click="withdraw(invitation.id)"
            />
          </li>
        </ul>
      </fieldset>
    </div>
    <!-- Les premiers pas (docs/128 §4) : des nombres seulement, jamais un nom ni un contenu. -->
    <div
      v-if="platform.first_steps"
      class="form-card settings-next-card"
      data-test="platform-first-steps"
    >
      <fieldset>
        <legend>Premiers pas</legend>
        <p class="setting-desc">
          Les comptes créés depuis 30 jours, en nombres seulement.
        </p>
        <p
          v-if="!platform.first_steps.accounts"
          class="setting-info"
        >
          Aucun compte créé depuis 30 jours.
        </p>
        <template v-else>
          <p
            class="setting-info"
            data-test="first-steps-rate"
          >
            <strong>{{ platform.first_steps.sent_within_week }} sur {{ platform.first_steps.accounts }}</strong>
            ont envoyé une première candidature dans les 7 jours.
          </p>
          <ul
            v-if="stoppedAt.length"
            class="plan-usage"
            data-test="first-steps-stopped"
          >
            <li
              v-for="row in stoppedAt"
              :key="row.label"
            >
              <span class="plan-usage-name">{{ row.label }}</span>
              <span class="plan-usage-count">{{ plural(row.count, "compte", "comptes") }}</span>
            </li>
          </ul>
        </template>
      </fieldset>
    </div>
    <div
      v-if="platform.backup"
      class="form-card settings-next-card"
      data-test="platform-backup"
    >
      <fieldset>
        <legend>Sauvegardes</legend>
        <p
          v-if="!platform.backup.configured"
          class="notice error"
          data-test="backup-not-configured"
        >
          Les sauvegardes ne sont pas réglées : écris une phrase secrète dans le fichier <code>.env</code>
          (<code>JOBBOT_BACKUP_PASSPHRASE</code>), puis redémarre la plateforme. Voir <code>docs/82-sauvegardes.md</code>.
        </p>
        <template v-else>
          <p
            v-if="platform.backup.late"
            class="notice error"
            role="alert"
            data-test="backup-late"
          >
            {{ platform.backup.last_error
              ? `La dernière sauvegarde a échoué : ${platform.backup.last_error}.`
              : "Aucune sauvegarde depuis plus de 36 heures." }}
          </p>
          <p data-test="backup-last">
            {{ platform.backup.last_at
              ? `Dernière sauvegarde ${since(platform.backup.last_at)}, ${size(platform.backup.last_size)}.`
              : "Pas encore de sauvegarde : la première se fait dans l'heure." }}
            {{ plural(platform.backup.count, "sauvegarde gardée", "sauvegardes gardées") }} dans
            <code>{{ platform.backup.folder }}</code>.
          </p>
          <p
            class="hint"
            data-test="backup-test"
          >
            {{ platform.backup.test_at
              ? platform.backup.test_ok
                ? `Dernier essai de restauration ${since(platform.backup.test_at)} : réussi.`
                : `Dernier essai de restauration ${since(platform.backup.test_at)} : échec (${platform.backup.test_error}).`
              : "Pas encore d'essai de restauration : il se fait chaque dimanche." }}
          </p>
        </template>
      </fieldset>
    </div>
    <form
      class="form-card settings-next-card"
      data-test="platform-mentions"
      @submit.prevent="saveMentions"
    >
      <fieldset>
        <legend>
          <label for="platform-mentions">Mentions de la page « Données personnelles »</label>
        </legend>
        <p class="setting-desc">
          Responsable, contact, hébergement. Public, sur <RouterLink to="/tes-donnees">la page Données personnelles</RouterLink>.
        </p>
        <textarea
          id="platform-mentions"
          v-model="mentions"
          rows="4"
          maxlength="4000"
        />
      </fieldset>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
        >
          Enregistrer
        </button>
        <span
          v-if="mentionsMessage"
          role="status"
          class="muted"
        >{{ mentionsMessage }}</span>
      </div>
    </form>
    <form
      class="form-card settings-next-card"
      data-test="platform-ai"
      @submit.prevent="saveTotal"
    >
      <fieldset>
        <legend>
          <label for="platform-total">Plafond total de l'IA, tous comptes</label>
        </legend>
        <p class="setting-desc">
          Au-delà, l'IA s'arrête pour tous jusqu'au mois suivant.
        </p>
        <!-- Un seul champ : il s'enregistre au changement (docs/106 §5), « Enregistré » à côté. -->
        <div class="inline-field">
          <input
            id="platform-total"
            v-model="total"
            type="number"
            inputmode="numeric"
            min="0"
            max="10000"
            step="1"
            required
            @change="saveTotal"
          >
          <span>CHF / mois</span>
          <span
            v-if="message"
            role="status"
            :class="message === 'Enregistré' ? 'saved-flash' : 'field-error'"
          >{{ message }}</span>
        </div>
        <!-- Ce qu'on consulte, sur fond gris (docs/110). -->
        <p class="setting-info">
          Ce mois, tous comptes : <strong>{{ money(platform.ai_month_spend_chf) }} CHF</strong>.
        </p>
      </fieldset>
    </form>
  </template>
</template>
