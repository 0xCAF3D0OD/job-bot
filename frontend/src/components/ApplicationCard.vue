<script setup lang="ts">
import { ref } from "vue";

import type { Application, ApplicationStatus, OrpRow } from "../api/client";
import { applicationStatusLabel } from "../format";

// Carte d'une candidature (docs/22 §4) : statut, ce qui manque pour l'ORP, documents,
// copie pour Job-Room de cette seule candidature.
const props = defineProps<{ application: Application; orpRow?: OrpRow | null }>();
const emit = defineEmits<{
  status: [application: Application, status: ApplicationStatus];
  edit: [application: Application];
  remove: [application: Application];
}>();

const jobRoom = ref(false);
const menuOpen = ref(false);
const copied = ref("");
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

async function copy(value: string, key: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
    copied.value = key;
    setTimeout(() => {
      if (copied.value === key) copied.value = "";
    }, 1500);
  } catch {
    copied.value = "";
  }
}

function act(action: () => void): void {
  menuOpen.value = false;
  action();
}

const onStatus = (event: Event): void =>
  emit("status", props.application, (event.target as HTMLSelectElement).value as ApplicationStatus);
</script>

<template>
  <article
    class="application-card"
    data-test="application-card"
  >
    <header>
      <div>
        <strong>{{ application.company }}</strong>
        <span
          v-if="application.assigned_by_orp"
          class="badge"
        >ORP</span>
        <p class="muted">
          {{ application.job_title }} · {{ shortDate.format(new Date(application.sent_at)) }}
        </p>
      </div>
      <div class="more-menu">
        <button
          type="button"
          class="close"
          aria-label="Plus d'actions"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          ⋯
        </button>
        <ul
          v-if="menuOpen"
          class="menu"
          role="menu"
        >
          <li>
            <button
              type="button"
              role="menuitem"
              data-test="card-edit"
              @click="act(() => emit('edit', application))"
            >
              Modifier
            </button>
          </li>
          <li>
            <button
              type="button"
              role="menuitem"
              class="danger"
              @click="act(() => emit('remove', application))"
            >
              Supprimer
            </button>
          </li>
        </ul>
      </div>
    </header>

    <p
      v-if="application.interview_at"
      class="card-facts"
    >
      Entretien le {{ longDate.format(new Date(application.interview_at)) }}
    </p>

    <label class="card-status">
      Statut
      <select
        :value="application.status"
        :class="['status-select', application.status]"
        data-test="card-status"
        @change="onStatus"
      >
        <option
          v-for="(text, value) in applicationStatusLabel"
          :key="value"
          :value="value"
        >
          {{ text }}
        </option>
      </select>
    </label>

    <p
      v-if="orpRow?.missing.length"
      class="notice card-missing"
      data-test="card-missing"
    >
      Pour l'ORP, il manque : {{ orpRow.missing.join(", ") }}.
      <button
        type="button"
        class="link"
        data-test="card-complete"
        @click="emit('edit', application)"
      >
        Compléter
      </button>
    </p>

    <p class="card-links">
      <a
        v-if="application.letter_draft_id"
        class="link"
        :href="`/api/letters/${application.letter_draft_id}/docx`"
        download
      >Lettre</a>
      <a
        v-if="application.cv_draft_id"
        class="link"
        :href="`/api/cvs/${application.cv_draft_id}/docx`"
        download
      >CV</a>
      <a
        v-if="application.application_url?.startsWith('http')"
        class="link"
        :href="application.application_url"
        target="_blank"
        rel="noopener noreferrer"
      >Lien de candidature</a>
      <button
        v-if="orpRow"
        type="button"
        class="link"
        :aria-expanded="jobRoom"
        data-test="card-job-room"
        @click="jobRoom = !jobRoom"
      >
        {{ jobRoom ? "Fermer Job-Room" : "Copier pour Job-Room" }}
      </button>
    </p>

    <dl
      v-if="jobRoom && orpRow"
      class="card-job-room"
      data-test="card-job-room-fields"
    >
      <template
        v-for="item in orpRow.job_room"
        :key="item.label"
      >
        <dt>{{ item.label }}</dt>
        <dd>
          <span
            v-if="item.choice"
            class="job-room-choice"
          >{{ item.value ? `à cocher : ${item.value}` : "—" }}</span>
          <span v-else>{{ item.value || "—" }}</span>
          <button
            v-if="item.value && !item.choice"
            type="button"
            class="link"
            data-test="card-copy"
            @click="copy(item.value, item.label)"
          >
            {{ copied === item.label ? "Copié" : "Copier" }}
          </button>
        </dd>
      </template>
    </dl>
  </article>
</template>
