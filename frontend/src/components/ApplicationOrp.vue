<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application, OrpRow } from "../api/client";
import { usePhone } from "../composables/usePhone";
import CopyButton from "./CopyButton.vue";
import JobRoomDeclared from "./JobRoomDeclared.vue";
import OrpFiche from "./OrpFiche.vue";
import SidePanel from "./SidePanel.vue";

// « Pour l'ORP » d'une candidature (lot 18, §10.3) : ce qui manque, la fiche à recopier (sous-page sur téléphone,
// panneau de 480 px sur ordinateur) et la déclaration Job-Room. Partagé par le panneau et le détail d'Envoyées (§8).
const props = defineProps<{ application: Application; orpRow: OrpRow | null }>();
const emit = defineEmits<{ edit: []; changed: [] }>();
const { phone } = usePhone();
// Télétravail complet hors de Suisse (docs/26 §6) : rappel pour l'ORP, pas un avis officiel.
const remoteAbroad = computed(
  () => props.application.remote_full && !/suisse|switzerland|schweiz/i.test(props.application.remote_region ?? ""),
);
// La fiche « Pour l'ORP » du mois de la candidature (« 02.11.2026 » donne 2026-11).
const ficheTo = computed(() => {
  const [, m, y] = (props.orpRow?.date ?? "").split(".");
  return { path: `/bilan/orp/candidature/${props.application.id}`, query: m && y ? { mois: `${y}-${m}` } : {} };
});
const ficheOpen = ref(false);
function onDeclared(): void {
  ficheOpen.value = false;
  emit("changed");
}
</script>

<template>
  <section
    class="panel-section"
    data-test="section-orp"
  >
    <h3>Pour l'ORP</h3>
    <p
      v-if="orpRow?.missing.length"
      class="notice card-missing"
      data-test="card-missing"
    >
      Il manque : {{ orpRow.missing.join(", ") }}.
      <button
        type="button"
        class="link"
        data-test="card-complete"
        @click="emit('edit')"
      >
        Compléter
      </button>
    </p>
    <p
      v-if="remoteAbroad"
      class="remote-orp"
      data-test="remote-orp"
    >
      Employeur à l'étranger ? Vérifie le contrat et les assurances avec ton conseiller.
    </p>
    <!-- Téléphone (lot 18, §10.3) : les champs à recopier sont dans la fiche « Pour l'ORP ». -->
    <RouterLink
      v-if="orpRow && phone"
      :to="ficheTo"
      class="orp-fiche-link"
      data-test="orp-fiche-link"
    >
      Pour l’ORP ›
    </RouterLink>
    <!-- Ordinateur (lot 18, §10.3) : la même fiche dans un panneau latéral de 480 px. -->
    <button
      v-if="orpRow && !phone"
      type="button"
      class="orp-fiche-link"
      data-test="orp-fiche-open"
      @click="ficheOpen = true"
    >
      Pour l’ORP ›
    </button>
    <JobRoomDeclared
      v-if="orpRow && (!phone || orpRow.declared_at)"
      :application-id="application.id"
      :declared-at="orpRow.declared_at"
      @changed="emit('changed')"
    />
    <dl
      v-if="orpRow && !phone"
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
          <CopyButton
            v-if="item.value && !item.choice"
            :value="item.value"
            :label="`Copier : ${item.label}`"
            test-id="card-copy"
          />
        </dd>
      </template>
    </dl>

    <SidePanel
      v-if="orpRow && !phone"
      :open="ficheOpen"
      title="Pour l’ORP"
      :width="480"
      @close="ficheOpen = false"
    >
      <OrpFiche
        v-if="ficheOpen"
        :application-id="application.id"
        :month="ficheTo.query.mois"
        @declared="onDeclared"
      />
    </SidePanel>
  </section>
</template>
