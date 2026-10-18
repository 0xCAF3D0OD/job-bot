<script setup lang="ts">
import type { Application, ApplicationStatus } from "../api/client";
import { applicationStatusLabel, formatMonth, methodLabel } from "../format";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// Suivi des candidatures (docs/08), onglet de la page Candidatures (docs/18 §2).
defineProps<{ items: Application[]; showMonth: boolean }>();
const emit = defineEmits<{
  open: [application: Application];
  edit: [application: Application];
  status: [application: Application, status: ApplicationStatus];
  remove: [application: Application];
}>();

// Les actions d'une ligne dans son « ⋯ » (docs/74 §4), la suppression en dernier.
function rowItems(application: Application): MoreMenuItem[] {
  const items: MoreMenuItem[] = [];
  if (application.letter_draft_id) {
    items.push({ label: "Lettre (Word)", test: "letter-docx", href: `/api/letters/${application.letter_draft_id}/docx`, download: true });
  }
  if (application.cv_draft_id) {
    items.push({ label: "CV (Word)", test: "cv-docx", href: `/api/cvs/${application.cv_draft_id}/docx`, download: true });
  }
  if (application.application_url?.startsWith("http")) {
    items.push({ label: "Ouvrir l'annonce", test: "application-link", href: application.application_url });
  }
  items.push({ label: "Modifier", test: "edit-application", run: () => emit("edit", application) });
  items.push({ label: "Supprimer", test: "remove-application", danger: true, run: () => emit("remove", application) });
  return items;
}
</script>

<template>
  <table class="runs">
    <thead>
      <tr>
        <th>Envoyée</th>
        <th>Entreprise</th>
        <th>Poste</th>
        <th>Mode</th>
        <th>Statut</th>
        <th />
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="application in items"
        :key="application.id"
        data-test="application"
      >
        <td>
          {{ new Date(application.sent_at).toLocaleDateString("fr-CH") }}
          <span
            v-if="showMonth"
            class="hint"
          ><br>ORP : {{ formatMonth(application.orp_month) }}</span>
        </td>
        <td>
          <!-- Le nom ouvre le panneau de la candidature (docs/46 §5). -->
          <button
            type="button"
            class="link table-open"
            data-test="table-open"
            @click="emit('open', application)"
          >
            {{ application.company }}
          </button>
          <span
            v-if="application.assigned_by_orp"
            class="badge"
          >ORP</span>
        </td>
        <td>
          {{ application.job_title }}
        </td>
        <td>{{ methodLabel[application.method ?? "electronique"] }}</td>
        <td>
          <select
            :value="application.status"
            :class="['status-select', application.status]"
            :aria-label="`Statut de la candidature chez ${application.company}`"
            data-test="status-select"
            @change="emit('status', application, ($event.target as HTMLSelectElement).value as ApplicationStatus)"
          >
            <option
              v-for="(label, value) in applicationStatusLabel"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </select>
        </td>
        <td class="row-more">
          <MoreMenu
            :items="rowItems(application)"
            :label="`Actions sur la candidature chez ${application.company}`"
            test-id="row-more"
          />
        </td>
      </tr>
    </tbody>
  </table>
</template>
