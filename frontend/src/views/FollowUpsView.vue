<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Application, type Offer } from "../api/client";
import { applicationBody } from "../applicationBody";
import { followUpList, noAnswerText } from "../applicationState";
import ActionBar from "../components/ActionBar.vue";
import AppIcon from "../components/AppIcon.vue";
import BottomSheet from "../components/BottomSheet.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import FaceState from "../components/FaceState.vue";
import FollowUpPanel from "../components/FollowUpPanel.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PageHero from "../components/PageHero.vue";
import StatusPill from "../components/StatusPill.vue";
import StepProgress from "../components/StepProgress.vue";
import UndoToast from "../components/UndoToast.vue";
import { offerUndo } from "../composables/useUndo";
import { dateInSentence } from "../dates";

// Les relances une à une (planche « Tri et panneau de commande », B2) : ouvertes depuis la carte
// « À relancer » du Suivi, sur téléphone. Une candidature à la fois ; dans le panneau du bas,
// « Relancer » (le panneau de relance dans une feuille du bas), puis « Passer » et « Classer sans
// réponse ». « Passer » va à la suivante sans rien enregistrer (pas de report côté serveur) :
// la candidature reste dans « À relancer ». « Classer sans réponse » : « Annuler » pendant 6 s.
const loaded = ref(false);
const queue = ref<Application[]>([]);
const index = ref(0);
const followed = ref(0);
const archived = ref(0);
const sheet = ref(false);

const current = computed(() => queue.value[index.value] ?? null);
const position = computed(() => (current.value ? index.value + 1 : 0));

const BY: Record<Application["method"], string> = {
  electronique: "par courriel",
  ecrit: "par courrier",
  telephone: "par téléphone",
  personnel: "en personne",
};
const sentLine = computed(() => {
  const a = current.value;
  return a ? `Envoyée ${dateInSentence(`${a.sent_at}T12:00:00`)}, ${BY[a.method]}.` : "";
});
const lastLine = computed(() => {
  const a = current.value;
  if (!a) return "";
  return a.status === "relancee" && a.followed_up_at
    ? `Relancée ${dateInSentence(`${a.followed_up_at}T12:00:00`)} : aucune réponse.`
    : "Dernier échange : aucune réponse.";
});
// Le logo de l'entreprise, comme pour une offre : la lettre en couleur, l'image si l'offre en a une.
const logo = computed(() => {
  const a = current.value;
  return a ? ({ id: a.offer_id ?? -a.id, company: a.company, title: a.job_title, has_logo: false } as Offer) : null;
});

function next(): void {
  index.value += 1;
}

function onFollowedUp(): void {
  sheet.value = false;
  followed.value += 1;
  next();
}

function archive(): void {
  const a = current.value;
  if (!a) return;
  archived.value += 1;
  next();
  void offerUndo({
    message: `Classée sans réponse : ${a.company}.`,
    commit: async (keepalive) => {
      const { response } = await api.PUT("/api/applications/{application_id}", {
        params: { path: { application_id: a.id } },
        body: {
          ...applicationBody(a),
          status: "sans_reponse",
          status_reason: a.status_reason ?? null,
          interview_at: a.interview_at ?? null,
        },
        keepalive,
      });
      return response.ok;
    },
    restore: () => {
      archived.value -= 1;
      index.value = Math.max(0, index.value - 1);
    },
  });
}

const summary = computed(() =>
  [
    followed.value ? `${followed.value} ${followed.value === 1 ? "relancée" : "relancées"}` : "",
    archived.value ? `${archived.value} ${archived.value === 1 ? "classée" : "classées"} sans réponse` : "",
  ]
    .filter(Boolean)
    .join(", "),
);

onMounted(async () => {
  const { data } = await api.GET("/api/applications");
  queue.value = followUpList(data ?? []);
  loaded.value = true;
});
</script>

<template>
  <PageHero
    title="À relancer"
    class="triage-head"
  >
    <template #back>
      <RouterLink
        to="/candidatures/suivi"
        class="back-link"
        data-test="follow-ups-back"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />Suivi</span>
      </RouterLink>
    </template>
  </PageHero>
  <section class="band">
    <div class="container triage-page">
      <LoadingBlocks
        v-if="!loaded"
        :heights="['2.5rem', '12rem']"
      />
      <FaceState
        v-else-if="!queue.length"
        title="Rien à relancer"
        data-test="follow-ups-empty"
      >
        <p>Les candidatures sans réponse depuis 10 jours arrivent ici.</p>
      </FaceState>
      <div
        v-else
        class="triage-pile"
      >
        <StepProgress
          v-if="position"
          :current="position"
          :total="queue.length"
        />
        <div
          v-if="current"
          :key="current.id"
          class="pick-step"
        >
          <article
            class="pick-card"
            data-test="follow-up-card"
          >
            <header class="pick-head">
              <CompanyLogo
                v-if="logo"
                :offer="logo"
              />
              <div class="pick-title">
                <strong>{{ current.job_title }}</strong>
                <span class="muted">{{ [current.company, current.location].filter(Boolean).join(" · ") }}</span>
              </div>
            </header>
            <div class="follow-up-lines">
              <p>{{ sentLine }}</p>
              <p class="muted">
                {{ lastLine }}
              </p>
            </div>
            <StatusPill tone="todo">
              {{ noAnswerText(current) }}
            </StatusPill>
          </article>
          <UndoToast inline />
          <ActionBar>
            <button
              type="button"
              class="primary follow-up-main"
              data-test="follow-up-open"
              @click="sheet = true"
            >
              <span class="with-icon"><AppIcon name="reply" />Relancer</span>
            </button>
            <div class="action-bar-row follow-up-row">
              <button
                type="button"
                class="secondary"
                data-test="follow-up-later"
                @click="next"
              >
                Passer
              </button>
              <button
                type="button"
                class="secondary"
                data-test="follow-up-archive"
                @click="archive"
              >
                Classer sans réponse
              </button>
            </div>
            <p class="action-bar-note">
              Après « Classer sans réponse », « Annuler » pendant 6 s.
            </p>
          </ActionBar>
          <BottomSheet
            :open="sheet"
            title="Relancer"
            @close="sheet = false"
          >
            <FollowUpPanel
              :application="current"
              @done="onFollowedUp"
            />
          </BottomSheet>
        </div>
        <div
          v-else
          class="pick-step"
        >
          <FaceState
            title="Relances du jour terminées"
            illustration="reussite"
            class="pick-done"
            data-test="follow-ups-done"
          >
            <p v-if="summary">
              {{ summary }}.
            </p>
            <div class="face-state-actions">
              <RouterLink
                to="/candidatures/suivi"
                class="button-link"
                data-test="follow-ups-back-done"
              >
                Revenir au Suivi
              </RouterLink>
            </div>
          </FaceState>
          <UndoToast inline />
        </div>
      </div>
    </div>
  </section>
</template>
