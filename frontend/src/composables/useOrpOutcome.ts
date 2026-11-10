import { computed, ref, watch, type Ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";

type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

// Ce qui a été convenu au rendez-vous ORP (docs/83 §1) : les champs, repartis de ce qui est noté à chaque changement
// de rendez-vous, et l'enregistrement. Partagé par la feuille du téléphone (OrpOutcomeSheet) et le formulaire du
// détail sur ordinateur (OrpOutcomeInline, lot 14). En l'enregistrant, le serveur met à jour l'objectif du mois et
// crée le rendez-vous suivant (0.67.2). Les formations accordées et les assignations d'avant sont gardées.
export function useOrpOutcome(meeting: Ref<Meeting | null>, target: Ref<number | null>, onSaved: (page: Page) => void) {
  const count = ref(10);
  const measures = ref("");
  const nextDay = ref("");
  const nextTime = ref("");
  const note = ref("");
  const message = ref("");
  const busy = ref(false);

  watch(
    meeting,
    (m) => {
      if (!m) return;
      count.value = m.agreed_target ?? target.value ?? 10;
      measures.value = m.measures
        .filter((x) => x.training_id == null)
        .map((x) => x.text)
        .join(", ");
      const next = m.next_starts_at ? new Date(m.next_starts_at) : null;
      nextDay.value = next ? `${next.getFullYear()}-${pad(next.getMonth() + 1)}-${pad(next.getDate())}` : "";
      nextTime.value = next ? `${pad(next.getHours())}:${pad(next.getMinutes())}` : "";
      note.value = m.note ?? "";
      message.value = "";
    },
    { immediate: true },
  );

  // À côté du compteur : ce qui était demandé jusqu'ici.
  const before = computed(() => {
    if (!target.value) return "";
    return count.value === target.value ? "Comme le mois dernier" : `${target.value} le mois dernier`;
  });

  function step(delta: number): void {
    count.value = Math.min(100, Math.max(1, count.value + delta));
  }

  async function save(): Promise<void> {
    const m = meeting.value;
    if (!m || busy.value) return;
    const kept = m.measures.filter((x) => x.training_id != null).map((x) => ({ text: x.text, training_id: x.training_id ?? null }));
    const text = measures.value.trim();
    const next = nextDay.value ? new Date(`${nextDay.value}T${nextTime.value || "09:00"}`) : null;
    busy.value = true;
    try {
      const { data, error } = await api.PUT("/api/orp-meeting/{meeting_id}/convenu", {
        params: { path: { meeting_id: m.id } },
        body: {
          target: count.value,
          measures: [...kept, ...(text ? [{ text, training_id: null }] : [])],
          assignments: m.assignments ?? "",
          note: note.value,
          next_starts_at: next ? next.toISOString() : null,
        },
      });
      if (data) onSaved(data);
      else message.value = (error as { detail?: string } | undefined)?.detail ?? "Impossible d’enregistrer pour l’instant.";
    } finally {
      busy.value = false;
    }
  }

  return { count, measures, nextDay, nextTime, note, message, busy, before, step, save };
}
