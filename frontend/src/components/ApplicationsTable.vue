<script setup lang="ts">
import type { Application, ApplicationStatus } from "../api/client";
import { dateInList } from "../dates";
import { applicationStatusLabel, formatMonth, methodLabel } from "../format";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import StatusPill from "./StatusPill.vue";

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
    items.push({ label: "Lettre (Word)", test: "letter-docx", icon: "download", href: `/api/letters/${application.letter_draft_id}/docx`, download: true });
  }
  if (application.cv_draft_id) {
    items.push({ label: "CV (Word)", test: "cv-docx", icon: "download", href: `/api/cvs/${application.cv_draft_id}/docx`, download: true });
  }
  if (application.application_url?.startsWith("http")) {
    items.push({ label: "Ouvrir l'annonce", test: "application-link", icon: "external", href: application.application_url });
  }
  items.push({ label: "Modifier", test: "edit-application", icon: "pencil", run: () => emit("edit", application) });
  items.push({ label: "Supprimer", test: "remove-application", icon: "trash", run: () => emit("remove", application) });
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
        <th><span class="visually-hidden">Actions</span></th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="application in items"
        :key="application.id"
        data-test="application"
      >
        <td class="app-date">
          {{ dateInList(`${application.sent_at}T12:00:00`) }}
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
          <!-- Une étiquette sans état : sans point, neutre (règle §4). -->
          <StatusPill
            v-if="application.assigned_by_orp"
            :dot="false"
            data-test="orp-tag"
          >
            ORP
          </StatusPill>
        </td>
        <td>
          {{ application.job_title }}
        </td>
        <td>{{ methodLabel[application.method ?? "electronique"] }}</td>
        <td>
          <select
            :value="application.status"
            :class="['status-select', 'field-compact', application.status]"
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
            :label="`Plus d'actions sur la candidature chez ${application.company}`"
            test-id="row-more"
          />
        </td>
      </tr>
    </tbody>
  </table>
</template>
