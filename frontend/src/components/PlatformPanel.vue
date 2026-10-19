<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type AccountOut, type PlatformOut } from "../api/client";
import { formatDate, plural, since } from "../format";
import CopyLabel from "./CopyLabel.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// Plateforme (docs/65 §2, §4, §5) : les comptes, réservé à l'exploitant. De chaque compte,
// l'usage seulement (connexion, dépense de l'IA, offres reçues), jamais ses données.
type Platform = PlatformOut;
type Account = AccountOut;

const platform = ref<Platform | null>(null);
const failed = ref(false);
// Le dernier lien créé, montré une seule fois, à transmettre soi-même.
const link = ref<{ kind: "invite" | "reset"; username: string | null; url: string; expires: string } | null>(null);
const copied = ref(false);
const total = ref("");
const message = ref("");
const caps = ref<Record<number, string>>({});

function money(value: string): string {
  return Number(value).toLocaleString("fr-CH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function show(data: Platform | undefined): void {
  if (!data) return;
  platform.value = data;
  total.value = String(Number(data.ai_total_budget_chf));
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
    { label: "Lien de nouveau mot de passe", test: `reset-${u}`, run: () => void reset(account) },
    { label: account.suspended ? "Réactiver" : "Suspendre", test: `suspend-${u}`, run: () => void suspend(account) },
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

async function suspend(account: Account): Promise<void> {
  const verb = account.suspended ? "Réactiver" : "Suspendre";
  if (!account.suspended && !window.confirm(`${verb} ${account.username} ? Il ne pourra plus se connecter ; ses données restent.`)) return;
  const { data } = await api.PATCH("/api/platform/accounts/{account_id}", {
    params: { path: { account_id: account.id } },
    body: { suspended: !account.suspended },
  });
  show(data);
}

async function remove(account: Account): Promise<void> {
  const typed = window.prompt(
    `Supprimer ${account.username} et toutes ses données (offres, candidatures, documents) ? ` +
      "Rien ne sera gardé. Écris son identifiant pour confirmer.",
  );
  if (typed?.trim() !== account.username) return;
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

async function saveTotal(): Promise<void> {
  const { data } = await api.PUT("/api/platform/settings", {
    body: { ai_total_budget_chf: Number(total.value) },
  });
  show(data);
  message.value = data ? "Plafond enregistré." : "Valeur refusée.";
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
      class="form-card"
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
          </li>
        </ul>
        <div class="form-actions">
          <button
            type="button"
            class="secondary"
            data-test="invite"
            @click="invite"
          >
            Inviter quelqu'un
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
            <button
              type="button"
              class="link danger"
              @click="withdraw(invitation.id)"
            >
              Retirer
            </button>
          </li>
        </ul>
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
        <p class="hint">
          Responsable, contact, hébergement. Public, sur <RouterLink to="/tes-donnees">
            la page Données personnelles
          </RouterLink>.
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
          class="secondary"
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
        <div class="inline-field">
          <input
            id="platform-total"
            v-model="total"
            type="number"
            min="0"
            max="10000"
            step="1"
            required
          >
          <span>CHF / mois</span>
        </div>
        <p class="hint">
          Ce mois, tous comptes : {{ money(platform.ai_month_spend_chf) }} CHF. Au-delà, l'IA s'arrête pour tous jusqu'au mois suivant.
        </p>
      </fieldset>
      <div class="form-actions">
        <button
          type="submit"
          class="secondary"
        >
          Enregistrer
        </button>
        <span
          v-if="message"
          role="status"
          class="muted"
        >{{ message }}</span>
      </div>
    </form>
  </template>
</template>
