<script setup lang="ts">
import type { Application, ApplicationStatus } from "../api/client";
import { applicationStatusLabel, formatMonth, methodLabel } from "../format";

// Suivi des candidatures (docs/08), onglet de la page Candidatures (docs/18 §2).
defineProps<{ items: Application[]; showMonth: boolean }>();
const emit = defineEmits<{
  edit: [application: Application];
  status: [application: Application, status: ApplicationStatus];
  remove: [application: Application];
}>();
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
          {{ application.company }}
          <span
            v-if="application.assigned_by_orp"
            class="badge"
          >ORP</span>
        </td>
        <td>
          {{ application.job_title }}
          <a
            v-if="application.application_url?.startsWith('http')"
            :href="application.application_url"
            target="_blank"
            rel="noopener noreferrer"
            class="link small-link"
            data-test="application-link"
          >Lien</a>
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
        <td class="row-actions">
          <a
            v-if="application.letter_draft_id"
            class="link"
            :href="`/api/letters/${application.letter_draft_id}/docx`"
            download
            data-test="letter-docx"
          >Lettre</a>
          <a
            v-if="application.cv_draft_id"
            class="link"
            :href="`/api/cvs/${application.cv_draft_id}/docx`"
            download
            data-test="cv-docx"
          >CV</a>
          <button
            type="button"
            class="link"
            data-test="edit-application"
            @click="emit('edit', application)"
          >
            Modifier
          </button>
          <button
            type="button"
            class="link danger"
            @click="emit('remove', application)"
          >
            Supprimer
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>
