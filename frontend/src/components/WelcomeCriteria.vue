<script lang="ts">
export type CriteriaSources = Record<"roles" | "places" | "rate", "cv" | "user" | "default">;
</script>

<script setup lang="ts">
import { computed, ref } from "vue";

import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import SidePanel from "./SidePanel.vue";
import TagInput from "./TagInput.vue";

// Premiers pas, étape « Quel travail cherches-tu ? » (section 41 du paquet du 16.11, planches OnboardingOrdinateurEtape2
// et OnboardingC, étape 2) : un seul bloc de 3 lignes (Postes recherchés en puces, Lieu, Taux d'activité), icône à
// gauche, « Modifier » à droite (un crayon de 44 px sur téléphone), la pastille « Depuis ton CV » collée à l'intitulé ;
// puis le bloc ORP. Téléphone et ordinateur partagent ce bloc ; chaque ligne ouvre le même panneau qu'avant.
// La provenance de chaque ligne (Kevin, 16.11, #806) : la pastille « Depuis ton CV » seulement pour « cv ». Jamais
// sur Lieu : l'adresse est retirée du CV avant toute lecture (option B du 16.11).
const props = defineProps<{ desk: boolean; reading: boolean; sources: CriteriaSources; maxRoles: number }>();
// Une ligne modifiée dans son panneau, puis validée : elle devient « user » et perd la pastille.
const emit = defineEmits<{ edited: [key: keyof CriteriaSources] }>();
const roles = defineModel<string[]>("roles", { required: true });
const picked = defineModel<string[]>("picked", { required: true });
const places = defineModel<string[]>("places", { required: true });
const rate = defineModel<number | null>("rate", { required: true });
const orp = defineModel<boolean>("orp", { required: true });
const target = defineModel<number>("target", { required: true });

const RATES = [null, 50, 60, 70, 80, 90, 100] as const;
const rateLabel = (value: number | null): string => (value ? `${value} à 100 %` : "Peu importe");
const editing = ref<"" | "roles" | "places" | "rate">("");
const current = (key: keyof CriteriaSources): string => JSON.stringify(key === "roles" ? picked.value : key === "places" ? places.value : rate.value);
let before = "";
function edit(key: keyof CriteriaSources): void {
  before = current(key);
  editing.value = key;
}
function close(): void {
  const key = editing.value;
  editing.value = "";
  if (key && current(key) !== before) emit("edited", key);
}
const EDIT_TITLES = { roles: "Postes recherchés", places: "Lieu", rate: "Taux d’activité" } as const;
const newRole = ref("");

const rows = computed(() => [
  { key: "roles", icon: "briefcase", label: "Postes recherchés", aria: "Modifier les postes", cv: props.sources.roles === "cv" },
  { key: "places", icon: "pin", label: "Lieu", aria: "Modifier le lieu", cv: false },
  { key: "rate", icon: "clock", label: "Taux d’activité", aria: "Modifier le taux", cv: props.sources.rate === "cv" },
] as const);

function toggleRole(role: string): void {
  if (picked.value.includes(role)) picked.value = picked.value.filter((r) => r !== role);
  else if (picked.value.length < props.maxRoles) picked.value = [...picked.value, role];
}

function addRole(): void {
  const role = newRole.value.trim().slice(0, 80);
  newRole.value = "";
  if (!role) return;
  // Les modèles ne suivent qu'au rendu suivant : la liste à jour est calculée ici.
  const same = roles.value.find((r) => r.toLowerCase() === role.toLowerCase());
  if (!same) roles.value = [...roles.value, role];
  const name = same ?? role;
  if (!picked.value.includes(name) && picked.value.length < props.maxRoles) picked.value = [...picked.value, name];
}

// « Continuer » : un poste tapé sans le « + » compte aussi (2026-11-05, Kevin).
defineExpose({ flush: () => newRole.value.trim() && addRole() });
</script>

<template>
  <div :class="['wc', { 'wc-desk': desk }]">
    <ul class="wc-card">
      <li
        v-for="row in rows"
        :key="row.key"
        :class="['wc-row', { 'wc-top': row.key === 'roles' }]"
        :data-test="`criteria-${row.key}`"
      >
        <AppIcon
          :name="row.icon"
          class="wc-icon"
        />
        <span class="wc-text">
          <span class="wc-key">{{ row.label }}<span
            v-if="row.cv"
            class="wc-cv"
          ><AppIcon name="tick" />Depuis ton CV</span></span>
          <template v-if="row.key === 'roles'">
            <span
              v-if="reading && !picked.length"
              class="wc-value"
            >Lecture du CV…</span>
            <ul
              v-else-if="picked.length"
              class="wc-list"
            >
              <li
                v-for="role in picked"
                :key="role"
              >{{ role }}</li>
            </ul>
            <span
              v-else
              class="wc-value"
            >À choisir</span>
          </template>
          <span
            v-else-if="row.key === 'places'"
            class="wc-value"
          >{{ places.join(", ") || "Toute la Suisse" }}</span>
          <span
            v-else
            class="wc-value"
          >{{ reading && rate === null ? "Lecture du CV…" : rateLabel(rate) }}</span>
        </span>
        <button
          type="button"
          class="secondary wc-edit"
          :aria-label="desk ? undefined : row.aria"
          aria-haspopup="dialog"
          :data-test="`criteria-${row.key}-edit`"
          @click="edit(row.key)"
        >
          <AppIcon name="pencil" /><template v-if="desk">
            Modifier
          </template>
        </button>
      </li>
    </ul>

    <div class="wc-card wc-orp">
      <label class="wc-row">
        <AppIcon
          name="users"
          class="wc-icon"
        />
        <span class="wc-text"><b class="wc-title">Je suis inscrit à l’ORP</b><span class="wc-sub">{{ desk ? "jobA1 tient alors le suivi de tes recherches pour l’ORP." : "jobA1 tient le suivi de tes recherches." }}</span></span>
        <input
          v-model="orp"
          type="checkbox"
          role="switch"
          data-test="orp-switch"
        >
      </label>
      <div
        v-if="orp"
        class="wc-row"
      >
        <AppIcon
          name="search"
          class="wc-icon"
        />
        <span
          id="welcome-target"
          class="wc-text"
        ><b class="wc-title">{{ desk ? "Recherches à faire par mois" : "Recherches par mois" }}</b><span class="wc-sub">{{ desk ? "L’objectif fixé avec ta conseillère ou ton conseiller." : "L’objectif fixé avec l’ORP." }}</span></span>
        <span class="wc-steps">
          <button
            type="button"
            class="wc-stepper"
            aria-label="Une de moins"
            :disabled="target <= 1"
            data-test="target-minus"
            @click="target = Math.max(1, target - 1)"
          >
            −
          </button>
          <output
            class="wc-target"
            aria-live="polite"
            aria-labelledby="welcome-target"
            data-test="target"
          >{{ target }}</output>
          <button
            type="button"
            class="wc-stepper"
            aria-label="Une de plus"
            :disabled="target >= 99"
            data-test="target-plus"
            @click="target = Math.min(99, target + 1)"
          >
            +
          </button>
        </span>
      </div>
    </div>

    <SidePanel
      :open="editing !== ''"
      :title="editing ? EDIT_TITLES[editing] : ''"
      @close="close"
    >
      <div
        v-if="editing === 'roles'"
        class="wc-panel"
      >
        <p class="wc-panel-note">
          Trois postes au plus.
        </p>
        <div
          class="wc-roles"
          data-test="roles"
        >
          <button
            v-for="role in roles"
            :key="role"
            type="button"
            :class="['chip', 'wc-role', { on: picked.includes(role) }]"
            :aria-pressed="picked.includes(role)"
            :aria-disabled="!picked.includes(role) && picked.length >= maxRoles ? 'true' : undefined"
            @click="toggleRole(role)"
          >
            <AppIcon
              v-if="picked.includes(role)"
              name="check"
            />{{ role }}
          </button>
        </div>
        <div class="tag-add">
          <input
            id="welcome-role"
            v-model="newRole"
            type="text"
            maxlength="80"
            placeholder="Ajouter un poste"
            aria-label="Ajouter un poste"
            data-test="role-input"
            @keydown.enter.prevent="addRole"
          >
          <IconButton
            icon="plus"
            label="Ajouter"
            data-test="role-add"
            @click="addRole"
          />
        </div>
      </div>
      <div
        v-else-if="editing === 'places'"
        class="wc-panel"
      >
        <label
          for="welcome-place"
          class="wc-panel-note"
        >Une ville ou un canton, autant que tu veux.</label>
        <TagInput
          id="welcome-place"
          v-model="places"
          placeholder="Une ville ou un canton"
        />
      </div>
      <fieldset
        v-else-if="editing === 'rate'"
        class="wc-panel wc-rates"
      >
        <legend class="visually-hidden">
          Taux d’activité minimum
        </legend>
        <label
          v-for="value in RATES"
          :key="String(value)"
          class="wc-rate"
        >
          <input
            v-model="rate"
            type="radio"
            name="welcome-rate"
            :value="value"
          >
          {{ rateLabel(value) }}
        </label>
      </fieldset>
      <template #footer>
        <button
          type="button"
          class="primary wc-done"
          data-test="criteria-done"
          @click="close"
        >
          OK
        </button>
      </template>
    </SidePanel>
  </div>
</template>

<style>
/* Valeurs des planches OnboardingOrdinateurEtape2 (ordinateur) et OnboardingC étape 2 (téléphone), section 41. */
.wc { --wc-gap: 12px; --wc-pad: 12px 14px; --wc-h: 72px; --wc-key: 14px; --wc-value: 17px; --wc-value-lh: 23px; --wc-li-lh: 25px;
  --wc-title: 16px; --wc-cv-h: 24px; --wc-cv-pad: 8px; --wc-cv: 12px; --wc-step: 44px; --wc-2: 2px; --wc-6: 6px; --wc-15: 15px; --wc-20: 20px; --wc-22: 22px;
  display: flex; flex-direction: column; gap: var(--space-4); }
.wc-desk { --wc-gap: 16px; --wc-pad: 12px 16px; --wc-h: 76px; --wc-key: 15px; --wc-value: 18px; --wc-value-lh: 24px; --wc-li-lh: 26px;
  --wc-title: 17px; --wc-cv-h: 28px; --wc-cv-pad: 10px; --wc-cv: 13px; --wc-step: 40px;
  /* Ordinateur : la grille de 4 (audit-grille à 1440 px) ; 18, 2 et 6 px de la planche arrondis à 16, 4 et 8. */
  --wc-2: 4px; --wc-6: 8px; margin-top: var(--space-6); }
.wc-card { margin: 0; padding: 0; list-style: none; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); overflow: hidden; }
.wc-row { box-sizing: border-box; display: flex; align-items: center; gap: var(--wc-gap); min-height: var(--wc-h); padding: var(--wc-pad); }
.wc-row + .wc-row { border-top: 1px solid var(--line); }
.wc-row.wc-top { align-items: flex-start; padding-block: var(--space-4); }
.wc-top .wc-icon { margin-top: var(--wc-2); }
.wc-icon { flex: none; width: 22px; height: 22px; color: var(--primary-graphic); stroke-width: 2; }
.wc-text { flex: 1; min-width: 0; }
.wc-key { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); font-size: var(--wc-key); line-height: var(--wc-20); color: var(--text-secondary); }
.wc-cv { display: inline-flex; align-items: center; gap: var(--space-1); height: var(--wc-cv-h); padding: 0 var(--wc-cv-pad); border-radius: var(--radius-pill); background: var(--success-soft); color: var(--success); font-size: var(--wc-cv); font-weight: var(--weight-bold); }
.wc-cv .icon { width: 13px; height: 13px; stroke-width: 3; }
.wc-value { display: block; margin-top: var(--wc-2); font-size: var(--wc-value); line-height: var(--wc-value-lh); font-weight: var(--weight-bold); }
.wc-list { margin: var(--wc-6) 0 0; padding-left: var(--wc-20); list-style: disc; font-size: var(--wc-value); line-height: var(--wc-li-lh); font-weight: var(--weight-bold); }
.wc-title { display: block; font-size: var(--wc-title); line-height: var(--wc-22); }
.wc-sub { display: block; margin-top: var(--wc-2); font-size: var(--wc-key); line-height: var(--wc-20); color: var(--text-secondary); }
button.wc-edit { flex: none; justify-content: center; gap: var(--wc-6); min-height: var(--target-min); width: var(--target-min); padding: 0; border-radius: var(--radius-pill); font-size: var(--wc-15); }
.wc-desk button.wc-edit { width: auto; padding: 0 var(--space-4); }
.wc-edit .icon { width: 18px; height: 18px; stroke-width: 2; }
.wc-desk .wc-edit .icon { width: 16px; height: 16px; }
.wc-steps { flex: none; display: flex; align-items: center; gap: var(--space-1); }
.wc-desk .wc-steps { gap: var(--wc-gap); }
.wc-stepper { display: grid; place-items: center; width: var(--wc-step); height: var(--wc-step); min-height: var(--wc-step); padding: 0; border: 1.5px solid var(--field-border); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font: inherit; font-size: var(--wc-20); }
.wc-target { min-width: 28px; text-align: center; font-size: var(--wc-20); font-weight: var(--weight-heavy); }
.wc-panel { display: flex; flex-direction: column; gap: var(--space-4); margin: 0; padding: 0; border: 0; }
.wc-panel-note { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.wc-roles { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.wc-role.chip { min-height: var(--btn-compact); padding: 0 var(--space-3); font-size: var(--font-small); font-weight: var(--weight-semibold); }
.wc-role .icon { width: 16px; height: 16px; }
.wc-rate { display: flex; align-items: center; gap: var(--space-3); min-height: var(--target-min); font-size: var(--font-body); cursor: pointer; }
.wc-rate input { width: 20px; height: 20px; margin: 0; accent-color: var(--primary-graphic); }
.wc-done { width: 100%; }
</style>
