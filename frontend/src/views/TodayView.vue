
<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from "vue";
import { RouterLink, type RouteLocationRaw } from "vue-router";

import { api, type Offer, type Today } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import FirstStepsList from "../components/FirstStepsList.vue";
import { useAuth } from "../composables/useAuth";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import OrpBar from "../components/OrpBar.vue";
import SuccessCard from "../components/SuccessCard.vue";
import TaskCheck from "../components/TaskCheck.vue";
import type { HomeTodo } from "../components/HomePhone.vue";
import TriageNone from "../components/TriageNone.vue";
import TroupeScene from "../components/TroupeScene.vue";
import { HOME_SCENE } from "../troupe";
import { usePhone } from "../composables/usePhone";
import { useCollect } from "../composables/useCollect";
import { useCvReading } from "../composables/useCvReading";
import { DOSE_CATCH_UP, isTriagePending, markTriageDone, pickDose, triageDoneToday, unmarkTriageDone } from "../composables/useDailyDose";
import { dateInList, dateInSentence, inDays, timeOfDay } from "../dates";
import { dailyPace, daysBefore, localDate, ofMonth, plural } from "../format";
import type { IconName } from "../icons";
import { useDataChanged } from "../composables/useDataChanged";
import { firstGoal } from "../composables/useGoalMoment";
import { GOOGLE_JOBS_BUTTON, GOOGLE_JOBS_HIDE_LABEL, GOOGLE_JOBS_TITLE, googleJobsPill, hideGoogleJobs } from "../composables/useGoogleJobs";
import IconButton from "../components/IconButton.vue";
import { offerUndo } from "../composables/useUndo";
import { usePageReady } from "../composables/usePageTransition";

// La scène des 4 personnages (§59 du 17.11) à droite du texte de l'accroche, 340 px de large ; la même sur téléphone,
// au-dessus du titre (HomePhone). Une seule constante, HOME_SCENE (troupe.ts).
// Aujourd'hui sur ordinateur (maquettes AujourdhuiOrdinateurV2 et AujourdhuiOrdinateurV2Sombre du 13 novembre, états
// « accueil », « vide » et « atteint »), en deux colonnes. À gauche : l'accroche sur un fond pêche (« Bonjour Kevin »,
// le titre du jour et sa fin à la main ; avec un justificatif en retard, deux lignes manuscrites, le retard d'abord ;
// l'objectif du mois atteint, en vert puis en bleu), « À faire » (une carte par tâche, numérotée, celle en retard en
// numéro 1), « Quand tu as le temps ». À droite : la bande ORP (la barre ORP), puis « {n} offres à trier » : l'éventail
// de Trier en petit (§20 du 15 novembre), où l'on trie sur place. Un jour de repos suit le même gabarit (état « repos » de la planche, 14 novembre ; la
// planche AujourdhuiOrdinateurReposD est retirée) : « Jour de repos. » à la main, « Si tu veux avancer » à la place de
// « À faire », « Cette semaine : 3 sur 3, faite » sous la barre ORP, et les offres à trier s'il y en a.
// Le téléphone a sa propre page (HomePhone).
// L'Accueil du téléphone et l'éventail en petit de l'ordinateur sont chargés à part : chaque appareil ne reçoit que sa
// moitié (budget de poids du premier affichage). Le chargement part tout de suite, en même temps que les données.
const loadHomePhone = () => import("../components/HomePhone.vue");
const loadTriageMini = () => import("../components/TriageMini.vue");
const HomePhone = defineAsyncComponent(loadHomePhone);
const TriageMini = defineAsyncComponent(loadTriageMini);
// « Première candidature notée » ne s'affiche qu'une fois : chargée à part, elle ne pèse pas sur l'Accueil.
const FirstApplicationCard = defineAsyncComponent(() => import("../components/FirstApplicationCard.vue"));
const today = ref<Today | null>(null);
// L'Accueil du téléphone (docs/139 étape 4) : sa propre mise en page, sous 820 px.
const { phone } = usePhone();
void (phone.value ? loadHomePhone() : loadTriageMini());
// Le prénom de « Bonjour Kevin. » : le premier mot du nom des Coordonnées.
const firstName = ref<string | null>(null);
usePageReady("today", () => !!today.value);
const best = ref<Offer[]>([]);
const preparing = ref<Offer[]>([]);
// Le tri du jour fini sur cet appareil (l'écran de tri et l'éventail en petit le notent à la fin de la pile).
const triageDone = ref(false);
// L'éventail en petit reste ouvert jusqu'au prochain chargement de la page, même le tri fini : « Annuler » y remet l'offre.
const miniOpen = ref(false);
// Un jour de repos (docs/86) : tout est facultatif, la liste devient « Si tu veux avancer ».
const restDay = computed(() => today.value?.rhythm?.research_today === false);
const rhythmPaused = computed(() => !!today.value?.rhythm?.pause_until);
const { message } = useCollect();

const DAY_MS = 86_400_000;
// Une remise ORP dans moins de 5 jours passe en tête de « À faire » (docs/43 n° 30).
const URGENT_DAYS = 5;

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}
// « Aujourd'hui à 9 h 30 », « Demain à 14 h » (dates.ts : l'heure compte, c'est un rendez-vous).
function dayAndTime(iso: string): string {
  const day = inDays(iso);
  return `${day.charAt(0).toUpperCase()}${day.slice(1)} à ${timeOfDay(iso)}`;
}
// « jusqu'au 1er novembre » : la date de phrase sans son « le », contracté dans « au ».
function untilDay(day: string): string {
  return dateInSentence(`${day}T12:00:00`).replace(/^le /, "");
}

// La dose du jour (docs/86) : 3 offres ; 5 quand le mois ORP est à rattraper (docs/124 §D).
const dose = computed(() => pickDose(today.value, best.value));
// Les premiers pas (docs/128) : tant qu'il en manque, la carte remplace la phrase et le tri ; le mois
// ORP reste, le reste attend.
const starting = computed(() => {
  const t = today.value;
  return !!t && !t.first_steps_dismissed && t.first_steps.some((s) => !s.done);
});
// Le tri à faire : une tâche « Trier » sur ordinateur, les offres de la dose sur téléphone. Un jour de repos aussi
// (planches AujourdhuiOrdinateurV2 et AccueilV2, état « repos », 14 novembre) : « Offres à trier » comme en semaine.
// Même règle que la page « Trier les offres » (useDailyDose) : le compteur d'ici et la pile de Trier ne divergent pas.
const triagePending = computed(() => isTriagePending(today.value, dose.value, triageDone.value));
// « Relire ton CV » (maquette du 10 novembre, PR 22) : en tête de « À faire » tant qu'un CV lisible n'a jamais été lu ;
// la ligne part dès que la lecture a trouvé quelque chose (état « lu »).
const reading = useCvReading();
const cvUnread = computed(() => {
  const cv = reading.cv.value;
  return !!cv && cv.text_status === "ok" && ["relire", "cours", "indispo"].includes(reading.stateOf(cv));
});
const CV_TASK = { key: "cv", test: "cv-unread", icon: "file-alert", title: "Relire ton CV", action: "Relire", to: "/profil" } as const;

// Les tâches du téléphone (« À faire », A4) : icône, titre avec un verbe, une
// ligne de détail, un bouton à contour) ; seulement ce qui a quelque chose à faire, le daté d'abord.
type Task = { key: string; test: string; icon: IconName; title: string; detail: string; action: string; to: RouteLocationRaw; check?: boolean };
const tasks = computed<Task[]>(() => {
  const t = today.value;
  if (!t || starting.value) return [];
  const list: Task[] = [];
  if (cvUnread.value) list.push({ ...CV_TASK, detail: "Sans lui, tes offres ne sont pas notées" });
  if (t.orp_meeting_at) {
    list.push({ key: "meeting", test: "orp-meeting-soon", icon: "calendar", title: "Préparer le rendez-vous ORP", detail: `${dayAndTime(t.orp_meeting_at)} : ta feuille est prête.`, action: "Voir", to: "/candidatures/rendez-vous-orp" });
  }
  for (const item of t.upcoming_interviews ?? []) {
    list.push({ key: `interview-${item.application_id}`, test: "upcoming-interview", icon: "users", title: "Préparer l’entretien", detail: `${dayAndTime(item.at)} chez ${item.company}.`, action: "Préparer", to: "/candidatures/suivi" });
  }
  const orp = orpTask.value;
  if (orp?.urgent) list.push(orp.task);
  if (t.to_follow_up) {
    const oldest = Math.max(0, ...(t.follow_ups ?? []).map((f) => daysBefore(f.sent_at)));
    list.push({
      key: "follow-ups",
      test: "follow-ups",
      icon: "message",
      title: `Relancer ${plural(t.to_follow_up, "candidature", "candidatures")}`,
      detail: oldest ? (t.to_follow_up === 1 ? `Elle attend depuis ${oldest} jours.` : `La plus ancienne attend depuis ${oldest} jours.`) : "Sans réponse depuis 10 jours.",
      action: "Relancer",
      to: "/candidatures/suivi",
    });
  }
  if (preparing.value.length) {
    const n = preparing.value.length;
    list.push({
      key: "preparing",
      test: "preparing",
      icon: "send",
      title: `Préparer ${plural(n, "candidature", "candidatures")}`,
      detail: n === 1 ? "Une offre gardée attend sa lettre." : `${n} offres gardées attendent leur lettre.`,
      action: "Préparer",
      to: n === 1 ? `/candidatures/offres/${preparing.value[0]!.id}/preparer` : { path: "/candidatures/offres", query: { statut: "in_progress" } },
    });
  }
  if (orp && !orp.urgent) list.push(orp.task);
  for (const item of t.interviews_to_review ?? []) {
    list.push({ key: `review-${item.application_id}-${item.interview_on}`, test: "interview-to-review", icon: "clipboard-check", title: "Faire le point sur l’entretien", detail: `Chez ${item.company} : comment s’est-il passé ?`, action: "Faire le point", to: item.link });
  }
  if (t.alerts_waiting) {
    list.push({
      key: "alerts",
      test: "alerts-waiting",
      icon: "bell",
      title: `Vérifier ${plural(t.alerts_waiting, "alerte", "alertes")}`,
      detail: t.alerts_waiting === 1 ? "Créée hier, elle n’a encore rien envoyé." : "Créées depuis hier, elles n’ont encore rien envoyé.",
      action: "Vérifier",
      to: "/candidatures/alertes",
    });
  }
  return list;
});

// « Remettre les justificatifs » se coche (§61 du 17.11, planches AccueilV2 et AujourdhuiOrdinateurV2) : le cercle orange
// marque le mois comme remis (le même appel que « Déjà remis » du Bilan) ; coché, la tâche reste à sa place avec la
// coche verte et « Remis le … » jusqu'au prochain chargement, et le cercle annule. Jamais de texte barré.
const orpDone = ref<string | null>(null);
const orpBusy = ref(false);
async function markOrp(on: boolean): Promise<void> {
  const month = today.value?.orp_due_month;
  if (!month || orpBusy.value) return;
  orpBusy.value = true;
  try {
    const params = { params: { path: { month } } };
    const { error } = on ? await api.PUT("/api/orp/{month}/submission", params) : await api.DELETE("/api/orp/{month}/submission", params);
    if (error === undefined) orpDone.value = on ? new Date().toISOString() : null;
  } catch {
    // Rien n'a changé : le cercle reste comme il était.
  } finally {
    orpBusy.value = false;
  }
}
// Les preuves ORP à remettre (docs/95 §2) : en tête quand l'échéance approche.
const orpTask = computed<{ urgent: boolean; task: Task } | null>(() => {
  const t = today.value;
  if (!t?.orp_due_month || !t.orp_due_date) return null;
  const due = localDate(t.orp_due_date);
  const days = Math.round((due.getTime() - startOfDay(new Date())) / DAY_MS);
  const urgent = days <= URGENT_DAYS;
  return {
    urgent,
    task: {
      key: "orp",
      test: urgent ? "orp-urgent" : "orp-due",
      icon: "check-circle",
      title: `Remettre les justificatifs ${ofMonth(t.orp_due_month)}`,
      check: true,
      detail: orpDone.value ? `Remis ${dateInSentence(orpDone.value)}.` : days < 0 ? `En retard depuis ${dateInSentence(`${t.orp_due_date}T12:00:00`)}.` : days === 0 ? "À remettre aujourd’hui." : `À remettre avant ${dateInSentence(`${t.orp_due_date}T12:00:00`)}.`,
      action: "Remettre",
      // La carte « Justificatifs … à remettre » est en tête du Bilan › ORP sur ordinateur, du Suivi ORP sur
      // téléphone (récapitulatif du 11 novembre, PR 29).
      to: phone.value ? { path: "/bilan/orp", query: { mois: t.orp_due_month } } : { path: "/bilan" },
    },
  };
});

// Un justificatif en retard (échéance passée) : il passe en premier dans l'accroche et dans « À faire ».
const orpLate = computed(() => {
  const due = today.value?.orp_due_date;
  return !!orpTask.value && !!due && localDate(due).getTime() < startOfDay(new Date());
});
// Le rappel du haut de l'Accueil du téléphone (§57 du 17.11 ; Kevin 17.11, 13 h 43) : avant l'échéance, seulement les
// 5 derniers jours (comme la tâche en tête de « À faire ») ; après, chaque jour. Il mène à la même page ORP que la tâche
// « Remettre les justificatifs ».
const reminder = computed(() => {
  const t = today.value;
  const orp = orpTask.value;
  if (!t?.orp_due_month || !t.orp_due_date || !orp?.urgent) return null;
  return { month: t.orp_due_month, due: t.orp_due_date, late: orpLate.value, to: orp.task.to };
});
// L'accroche d'un jour de retard (AujourdhuiOrdinateurV2, état « accueil ») : « 1 justificatif en retard, » en brun,
// puis « puis 2 candidatures » en bleu (le rythme du jour, s'il y en a un). Cinq mots au plus par ligne.
type LateCatch = { hand: string; then: string | null; sub: string };
const lateCatch = computed<LateCatch | null>(() => {
  const t = today.value;
  // En pause ou un jour de repos, le titre reste le leur : le justificatif en retard garde sa place en tête de « À faire ».
  if (!t || starting.value || rhythmPaused.value || restDay.value || !orpLate.value) return null;
  const perDay = dailyPace(t.month_count, t.month_target, t.month);
  return perDay
    ? { hand: "1 justificatif en retard,", then: `puis ${plural(perDay, "candidature", "candidatures")}`, sub: "Commence par l’ORP\u202f: 2 minutes. Ensuite, ton rythme du jour." }
    : { hand: "1 justificatif en retard", then: null, sub: "Commence par l’ORP\u202f: 2 minutes." };
});
// L'objectif du mois atteint (lot de corrections du 13 novembre au soir, §6 ; état « atteint ») : deux lignes à la main,
// « Objectif du mois atteint, » en vert puis « la suite est en plus » en bleu, et la phrase du mois.
const goalReached = computed(() => {
  const t = today.value;
  return !!t && !starting.value && !rhythmPaused.value && !restDay.value && !!t.month_target && t.month_count >= t.month_target;
});
const reachedSub = computed(() => {
  const t = today.value;
  if (!t?.month_target) return "";
  return `Tes ${plural(t.month_target, "recherche", "recherches")} ${ofMonth(t.month)} ${t.month_target === 1 ? "est faite" : "sont faites"}. Ce que tu envoies maintenant compte en plus.`;
});

// Un compte sans offre encore (§22 du 15.11, AujourdhuiOrdinateurNouveau) : « Bienvenue, / tes offres arrivent
// bientôt » à la main, premiers pas ouverts ou fermés.
const newcomer = computed(() => today.value?.has_offers === false);
const newcomerSub = computed(() =>
  today.value?.first_steps.some((s) => s.key === "alerts" && s.done)
    ? "Ton alerte est créée. La prochaine collecte t’apporte tes premières offres."
    : "Crée ta première alerte\u202f: jobA1 s’occupe du reste.",
);
// Le titre de la bande : l'action du jour, calculée sur le rythme qu'il faut pour tenir l'objectif ORP ; sa fin en
// écriture manuscrite (un seul accent par écran). Un seul élément de titre.
type Heading = { lead: string; hand: string; sub: string };
const heading = computed<Heading>(() => {
  const t = today.value;
  if (!t) return { lead: "", hand: "", sub: "" };
  if (starting.value) return { lead: "Commence par les premiers pas.", hand: "", sub: "" };
  const pause = t.rhythm?.pause_until;
  if (pause) return { lead: "En", hand: "pause.", sub: `Jusqu’au ${untilDay(pause)}. Pense à l’annoncer à ton conseiller.` };
  // « N choses t’attendent » : la liste « Si tu veux avancer » (état « repos » : 3 tâches, la relance reste à part).
  const waiting = phone.value ? todos.value.length : deskTodo.value.length;
  const more = waiting ? `Si tu veux avancer, ${waiting === 1 ? "une chose t’attend" : `${waiting} choses t’attendent`}.` : "Profite de ta journée.";
  if (restDay.value) {
    const weekDone = !!t.rhythm && t.rhythm.target !== null && t.rhythm.count >= t.rhythm.target;
    return { lead: "", hand: "Jour de repos.", sub: weekDone ? `Ta semaine est faite. ${more}` : more };
  }
  const perDay = dailyPace(t.month_count, t.month_target, t.month);
  const offers = triagePending.value ? ` ${plural(dose.value.length, "offre est", "offres sont")} à trier.` : "";
  if (perDay) {
    return { lead: plural(perDay, "candidature", "candidatures"), hand: "à envoyer.", sub: `C’est ton rythme pour rester dans l’objectif ORP.${offers}` };
  }
  if (perDay === 0) return { lead: "Tout est", hand: "à jour.", sub: `Objectif ORP du mois atteint : le reste du mois est à toi.${offers}` };
  return { lead: "Tout est", hand: "à jour.", sub: offers.trim() };
});

// Les tâches de l'ordinateur : une carte cliquable chacune, l'icône seule dans la couleur du ton, le libellé d'action
// coloré suivi de « › » (pas de bouton). Retard en pêche, entretien en vert, le reste en bleu.
type DeskTask = Task & { tone: "late" | "normal" | "interview" };
const deskTasks = computed<{ todo: DeskTask[]; later: DeskTask[] }>(() => {
  const t = today.value;
  if (!t || starting.value) return { todo: [], later: [] };
  const todo: DeskTask[] = [];
  const later: DeskTask[] = [];
  const orp = orpTask.value;
  const late = orpLate.value;
  if (cvUnread.value) todo.push({ ...CV_TASK, detail: "Sans lui, tes offres ne sont pas notées · 30 secondes", tone: "late" });
  if (orp?.urgent) todo.push({ ...orp.task, tone: late ? "late" : "normal" });
  if (preparing.value.length) {
    const n = preparing.value.length;
    todo.push({
      key: "preparing",
      test: "preparing",
      icon: "send",
      title: `Préparer ${plural(n, "candidature", "candidatures")}`,
      detail: n === 1 ? "Une offre gardée attend sa lettre" : `${n} offres gardées attendent leur lettre`,
      action: "Préparer",
      to: n === 1 ? `/candidatures/offres/${preparing.value[0]!.id}/preparer` : { path: "/candidatures/offres", query: { statut: "in_progress" } },
      tone: "normal",
    });
  }
  if (triagePending.value) {
    const near = dose.value.filter((o) => (o.score ?? 0) >= 85).length;
    todo.push({
      key: "triage",
      test: "triage",
      icon: "filter",
      title: `Trier ${plural(dose.value.length, "offre", "offres")}`,
      detail: near ? `Dont ${near} très ${near === 1 ? "proche" : "proches"} de ton profil` : "La meilleure d’abord",
      action: "Trier",
      to: { name: "triage" },
      tone: "normal",
    });
  }
  if (t.orp_meeting_at) {
    todo.push({ key: "meeting", test: "orp-meeting-soon", icon: "calendar", title: "Préparer le rendez-vous ORP", detail: `${dayAndTime(t.orp_meeting_at)} · ta feuille est prête`, action: "Voir", to: "/candidatures/rendez-vous-orp", tone: "normal" });
  }
  for (const item of t.upcoming_interviews ?? []) {
    todo.push({ key: `interview-${item.application_id}`, test: "upcoming-interview", icon: "calendar", title: "Préparer l’entretien", detail: `${item.company} · ${dayAndTime(item.at).toLowerCase()}`, action: "Préparer", to: "/candidatures/suivi", tone: "interview" });
  }
  if (orp && !orp.urgent) todo.push({ ...orp.task, tone: "normal" });
  for (const item of t.interviews_to_review ?? []) {
    todo.push({ key: `review-${item.application_id}-${item.interview_on}`, test: "interview-to-review", icon: "clipboard-check", title: "Faire le point sur l’entretien", detail: `Chez ${item.company} : comment s’est-il passé ?`, action: "Faire le point", to: item.link, tone: "interview" });
  }
  if (t.alerts_waiting) {
    todo.push({ key: "alerts", test: "alerts-waiting", icon: "bell", title: `Vérifier ${plural(t.alerts_waiting, "alerte", "alertes")}`, detail: t.alerts_waiting === 1 ? "Créée hier, elle n’a encore rien envoyé" : "Créées depuis hier, elles n’ont encore rien envoyé", action: "Vérifier", to: "/candidatures/alertes", tone: "normal" });
  }
  if (t.to_follow_up) {
    const oldest = Math.max(0, ...(t.follow_ups ?? []).map((f) => daysBefore(f.sent_at)));
    const follow: DeskTask = {
      key: "follow-ups",
      test: "follow-ups",
      icon: "message",
      title: `Relancer ${plural(t.to_follow_up, "candidature", "candidatures")}`,
      detail: oldest ? (t.to_follow_up === 1 ? `Elle attend depuis ${oldest} jours` : `La plus ancienne attend depuis ${oldest} jours`) : "Sans réponse depuis 10 jours",
      action: "Relancer",
      to: "/candidatures/suivi",
      tone: "normal",
    };
    // En pause, tout est facultatif : une seule liste. Un jour de repos garde « Quand tu as le temps » (état « repos »).
    (rhythmPaused.value ? todo : later).push(follow);
  }
  return { todo, later };
});
// Des offres pour toi, en attendant (docs/144, planches AujourdhuiOrdinateurNouveau et AccueilNouveau, §22 du 15.11) :
// le serveur n'envoie la recherche que sans offre, sans « Masquer » et avec un métier. « Ajouter une offre vue
// ailleurs » part quand les alertes sont prêtes : la carte des premiers pas la propose déjà.
const googleJobs = computed(() => today.value?.google_jobs ?? null);
// Les deux liens dessous restent sans carte pendant les premiers pas, comme avant (docs/144).
const googleShown = computed(() => !!googleJobs.value || (starting.value && today.value?.has_offers === false));
// « Cette semaine · 2 sur 3 » sous la barre ORP : pas pendant une pause (premiers pas compris, §22 du 15.11).
const weekCount = computed(() => {
  const week = today.value?.rhythm;
  return week && week.target !== null && !week.pause_until ? { count: week.count, target: week.target } : null;
});
const deskTodo = computed(() => deskTasks.value.todo);
const deskLater = computed(() => deskTasks.value.later);

// « À faire » du téléphone (A4) : les mêmes tâches, un nombre et un libellé ; toute la ligne est le lien.
const todos = computed<HomeTodo[]>(() => {
  const t = today.value;
  if (!t) return [];
  const many = (n: number, one: string, more: string): string => (n === 1 ? one : more);
  const list: HomeTodo[] = [];
  for (const task of tasks.value) {
    const group = task.key.split("-")[0]!;
    const same = list.find((todo) => todo.key === group);
    if (same) {
      same.count += 1;
      continue;
    }
    const count =
      group === "follow" ? t.to_follow_up : group === "preparing" ? preparing.value.length : group === "alerts" ? t.alerts_waiting : 1;
    list.push({
      key: group,
      test: `todo-${task.test}`,
      count,
      label: "",
      to: task.to,
      ...(group === "cv" ? { icon: task.icon, detail: task.detail } : {}),
      // §61 : « Remettre les justificatifs » se coche, avec sa ligne (« En retard depuis le 5 novembre »).
      ...(task.check ? { check: { done: !!orpDone.value, busy: orpBusy.value }, detail: task.detail } : {}),
    });
  }
  for (const todo of list) {
    const n = todo.count;
    todo.label = {
      meeting: "Rendez-vous ORP à préparer",
      interview: many(n, "Entretien à préparer", "Entretiens à préparer"),
      orp: t.orp_due_month ? `Remettre les justificatifs ${ofMonth(t.orp_due_month)}` : "Remettre les justificatifs",
      follow: many(n, "Relance à envoyer", "Relances à envoyer"),
      preparing: many(n, "Candidature à préparer", "Candidatures à préparer"),
      review: many(n, "Entretien à faire le point", "Entretiens à faire le point"),
      alerts: many(n, "Alerte à vérifier", "Alertes à vérifier"),
      cv: "Relire ton CV",
    }[todo.key] ?? "";
    if (todo.key === "interview" || todo.key === "review") todo.to = "/candidatures/suivi";
  }
  return list;
});
const homeEmpty = computed(() => {
  if (rhythmPaused.value) return "En pause : rien à trier.";
  if (restDay.value) return "Jour de repos : rien à trier.";
  return triageDone.value ? "Tri terminé · À demain" : "Rien à trier · À demain";
});

// Sans offre à trier, le bloc « Rien à trier pour l’instant » dit pourquoi quand il y a une raison.
const emptyTitle = computed(() => {
  if (rhythmPaused.value) return "En pause\u202f: rien à trier";
  return triageDone.value ? "Tri terminé · À demain" : undefined;
});
// « Élargir ma recherche » : seulement quand la recherche n'a rien trouvé.
const widen = computed(() => !emptyTitle.value && !best.value.length);
// L'éventail en petit finit le tri (ou « Annuler » le reprend) : la tâche « Trier » suit.
function onMiniDone(done: boolean): void {
  triageDone.value = done;
  if (done) markTriageDone();
  else unmarkTriageDone();
}

// La collecte seulement quand elle tourne ou a plus d'un jour de retard (docs/131 §B.6).
const collectNote = computed(() => {
  const last = today.value?.last_collect_at;
  const late = !!last && Date.now() - new Date(last).getTime() > DAY_MS;
  // dates.ts, jamais « il y a 136 heures » : « collecte hier », sinon « collecte le 22 octobre ».
  return message.value || (late ? `collecte ${dateInList(last!) === "hier" ? "hier" : dateInSentence(last!)}` : "");
});
// Au-dessus du titre : « Bonjour Kevin », et la collecte quand elle tourne ou a plus d'un jour de retard (docs/131 §B.6).
const hello = computed(() => {
  const collect = collectNote.value;
  const who = firstName.value ? `Bonjour ${firstName.value}` : "Bonjour";
  return collect ? `${who} · ${collect}` : who;
});

// R, l'objectif du mois atteint (docs/123 §2) : une victoire, une fois par mois et par appareil (useGoalMoment).
const goalWon = ref(false);
// Les cinq premiers pas faits (docs/128 §1) : le serveur le dit une seule fois.
const stepsWon = ref(false);

// Une panne de réseau au chargement : l'écran « Pas de connexion » (planche « Illustrations »).
const offline = ref(false);
async function load(): Promise<void> {
  try {
    await fetchAll();
    offline.value = false;
  } catch (cause) {
    if (!isNetworkError(cause)) throw cause;
    offline.value = true;
  }
}
async function fetchAll(): Promise<void> {
  const [day, offers, current] = await Promise.all([
    api.GET("/api/today"),
    // La dose du jour (docs/86) : les meilleures, pas toute la pile.
    api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: DOSE_CATCH_UP } } }),
    api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 100 } } }),
  ]);
  today.value = day.data ?? null;
  triageDone.value = triageDoneToday();
  goalWon.value = !!today.value && firstGoal(today.value.month, today.value.month_count, today.value.month_target);
  // Montrée une fois : on le dit au serveur, elle ne revient plus (docs/128 §1).
  if (today.value?.first_steps_finished && !stepsWon.value) {
    stepsWon.value = true;
    void api.PUT("/api/first-steps", { body: { celebrated: true } });
  }
  best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
  preparing.value = (current.data?.items ?? []).filter((o) => o.status === "preparing");
  // L'éventail en petit s'ouvre s'il y a un tri à faire ; ouvert, il le reste (le tri fini s'y lit, « Annuler » y revient).
  miniOpen.value ||= triagePending.value;
  if (firstName.value === null) {
    const who = await api.GET("/api/identity").catch(() => null);
    firstName.value = who?.data?.name?.trim().split(/\s+/)[0] || "";
  }
}

// Masquer la carte Google Emplois : comme les premiers pas, « Annuler » pendant 6 secondes, puis retenu pour le
// compte (Kevin, 15.11). Le lien de Candidatures vide reste.
function hideGoogle(): void {
  const kept = today.value?.google_jobs;
  if (!today.value || !kept) return;
  today.value = { ...today.value, google_jobs: null };
  void offerUndo({
    message: "Carte masquée",
    commit: hideGoogleJobs,
    restore: () => {
      if (today.value) today.value = { ...today.value, google_jobs: kept };
    },
  });
}

// Masquer les premiers pas : la carte s'en va tout de suite, « Annuler » pendant 6 secondes
// (docs/108) ; ensuite, elle ne revient plus (docs/128 §1).
function dismissSteps(): void {
  if (!today.value) return;
  today.value = { ...today.value, first_steps_dismissed: true };
  void offerUndo({
    message: "Premiers pas masqués",
    commit: async (keepalive) => {
      const { response } = await api.PUT("/api/first-steps", { body: { dismissed: true }, keepalive });
      return response.ok;
    },
    restore: () => {
      if (today.value) today.value = { ...today.value, first_steps_dismissed: false };
    },
  });
}

onMounted(() => {
  void load();
  void reading.load();
});
useDataChanged(load);
const { me } = useAuth();
</script>

<template>
  <HomePhone
    v-if="phone && today"
    :name="firstName || null"
    :first-day="starting"
    :month="today.month"
    :count="today.month_count"
    :target="today.month_target ?? null"
    :due="today.month_due_date ?? null"
    :offers="dose"
    :empty-text="starting ? 'Commence par les premiers pas.' : homeEmpty"
    :todos="todos"
    :rest-sub="restDay && !rhythmPaused && !starting ? heading.sub : null"
    :reminder="reminder"
    @check="markOrp"
  >
    <!-- Les premiers pas et l'accueil reporté restent en tête tant qu'ils existent (A9). -->
    <RouterLink
      v-if="me?.welcome === 'postponed'"
      to="/bienvenue"
      class="notice today-welcome"
      data-test="finish-welcome"
    >
      <strong>Terminer mon accueil</strong> : quelques questions pour régler ta recherche.
    </RouterLink>
    <FirstStepsList
      v-if="starting"
      :steps="today.first_steps"
      :summary="today.first_steps_summary ?? null"
      :has-offers="today.has_offers ?? true"
      :offer-id="today.first_steps_offer_id ?? null"
      :pick-ready="!rhythmPaused && best.length > 0"
      phone
      @dismiss="dismissSteps"
    />
    <section
      v-if="googleJobs"
      class="today-task aj-google aj-google-phone"
      aria-labelledby="google-title"
      data-test="google-jobs"
    >
      <span class="aj-task-main">
        <strong id="google-title">{{ GOOGLE_JOBS_TITLE }}</strong>
        <span data-test="google-jobs-search">{{ googleJobsPill(googleJobs) }}</span>
      </span>
      <a
        class="aj-google-go"
        :href="googleJobs.url"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Voir les offres sur Google Emplois (nouvel onglet)"
        data-test="google-jobs-open"
      >{{ GOOGLE_JOBS_BUTTON }}<AppIcon name="trend" /></a>
      <IconButton
        icon="close"
        class="aj-google-x"
        :label="GOOGLE_JOBS_HIDE_LABEL"
        data-test="google-jobs-hide"
        @click="hideGoogle"
      />
    </section>
    <div
      v-if="googleShown"
      :class="['aj-google-links', { 'aj-google-phone': true }]"
      data-test="google-jobs-links"
    >
      <RouterLink
        to="/ajouter-une-offre"
        data-test="start-add"
      >
        Ajouter une offre vue ailleurs<AppIcon name="chevron" />
      </RouterLink>
      <RouterLink
        to="/candidatures/alertes"
        data-test="start-forward"
      >
        Transférer mes alertes<AppIcon name="chevron" />
      </RouterLink>
    </div>
  </HomePhone>
  <div
    v-if="!phone && today"
    class="aj"
  >
    <div class="aj-main">
      <section
        class="aj-hero"
        aria-labelledby="today-title"
        data-test="today-band"
      >
        <div>
          <p
            class="aj-hello"
            data-test="page-eyebrow"
          >
            {{ hello }}
          </p>
          <h1
            v-if="lateCatch"
            id="today-title"
            class="aj-late"
            data-test="today-sentence"
          >
            <span class="aj-hand aj-hand-late">{{ lateCatch.hand }}</span><template v-if="lateCatch.then">
              <br><span class="aj-hand">{{ lateCatch.then }}</span>
            </template>
          </h1>
          <h1
            v-else-if="newcomer"
            id="today-title"
            class="aj-late"
            data-test="today-sentence"
          >
            <span class="aj-hand aj-hand-late">Bienvenue,</span><br><span class="aj-hand">tes offres arrivent bientôt</span>
          </h1>
          <h1
            v-else-if="goalReached"
            id="today-title"
            class="aj-late"
            data-test="today-sentence"
          >
            <span class="aj-hand aj-hand-reached">Objectif du mois atteint,</span><br><span class="aj-hand">la suite est en plus</span>
          </h1>
          <h1
            v-else-if="!heading.lead && heading.hand"
            id="today-title"
            class="aj-late"
            data-test="today-sentence"
          >
            <span class="aj-hand">{{ heading.hand }}</span>
          </h1>
          <h1
            v-else
            id="today-title"
            class="aj-title"
            data-test="today-sentence"
          >
            {{ heading.lead }}<template v-if="heading.hand">
              {{ " " }}<span class="aj-title-hand">{{ heading.hand }}</span>
            </template>
          </h1>
          <p
            v-if="lateCatch || newcomer || goalReached || heading.sub"
            class="aj-sub"
            data-test="today-sub"
          >
            {{ lateCatch ? lateCatch.sub : newcomer ? newcomerSub : goalReached ? reachedSub : heading.sub }}
          </p>
        </div>
        <TroupeScene
          :scene="HOME_SCENE"
          :width="340"
          :desktop-width="340"
          full
        />
      </section>

      <!-- Accueil remis à plus tard (docs/66 §4) : le reprendre d'un clic. -->
      <RouterLink
        v-if="me?.welcome === 'postponed'"
        to="/bienvenue"
        class="notice today-welcome"
        data-test="finish-welcome"
      >
        <strong>Terminer mon accueil</strong> : quelques questions pour régler ta recherche.
      </RouterLink>

      <!-- Les premiers pas en cinq lignes (§23 du 15.11) : la seule action tant qu'il en manque. -->
      <FirstStepsList
        v-if="starting"
        :steps="today.first_steps"
        :summary="today.first_steps_summary ?? null"
        :has-offers="today.has_offers ?? true"
        :offer-id="today.first_steps_offer_id ?? null"
        :pick-ready="!rhythmPaused && best.length > 0"
        @dismiss="dismissSteps"
      />
      <section
        v-if="googleJobs"
        class="today-task aj-google"
        aria-labelledby="google-title"
        data-test="google-jobs"
      >
        <b
          class="aj-num"
          aria-hidden="true"
        ><AppIcon name="search" /></b>
        <span class="aj-task-main">
          <strong id="google-title">{{ GOOGLE_JOBS_TITLE }}</strong>
          <span data-test="google-jobs-search">{{ googleJobsPill(googleJobs) }}</span>
        </span>
        <a
          class="aj-google-go"
          :href="googleJobs.url"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Voir les offres sur Google Emplois (nouvel onglet)"
          data-test="google-jobs-open"
        >{{ GOOGLE_JOBS_BUTTON }}<AppIcon name="trend" /></a>
        <IconButton
          icon="close"
          class="aj-google-x"
          :label="GOOGLE_JOBS_HIDE_LABEL"
          data-test="google-jobs-hide"
          @click="hideGoogle"
        />
      </section>
      <div
        v-if="googleShown"
        :class="['aj-google-links', { 'aj-google-phone': false }]"
        data-test="google-jobs-links"
      >
        <RouterLink
          to="/ajouter-une-offre"
          data-test="start-add"
        >
          Ajouter une offre vue ailleurs<AppIcon name="chevron" />
        </RouterLink>
        <RouterLink
          to="/candidatures/alertes"
          data-test="start-forward"
        >
          Transférer mes alertes<AppIcon name="chevron" />
        </RouterLink>
      </div>

      <section
        v-for="group in [
          { key: 'todo', title: restDay ? 'Si tu veux avancer' : 'À faire', items: deskTodo, test: 'today-tasks', numbered: true },
          { key: 'later', title: 'Quand tu as le temps', items: deskLater, test: 'today-later', numbered: false },
        ].filter((g) => g.items.length)"
        :key="group.key"
        class="aj-section"
        :aria-labelledby="`today-${group.key}-title`"
        :data-test="group.test"
      >
        <h2 :id="`today-${group.key}-title`">
          {{ group.title }}
        </h2>
        <component
          :is="group.numbered ? 'ol' : 'ul'"
          class="today-tasks"
        >
          <li
            v-for="(task, i) in group.items"
            :key="task.key"
            :class="{ 'aj-checkable': task.check }"
          >
            <!-- La tâche faite hors de l'app se coche (§61) : le cercle est à côté du lien, posé sur la place du numéro. -->
            <TaskCheck
              v-if="task.check"
              :checked="!!orpDone"
              :label="orpDone ? `Annuler : ${task.title.replace('Remettre les', 'justificatifs')} pas encore remis` : `Marquer comme remis : ${task.title.replace('Remettre les', 'justificatifs')}`"
              tone="late"
              :busy="orpBusy"
              data-test="orp-task-check"
              @toggle="markOrp"
            />
            <RouterLink
              :to="task.to"
              :class="['today-task', `tone-${task.tone}`]"
              :data-test="task.test"
            >
              <span
                v-if="task.check"
                class="aj-num aj-num-check"
                aria-hidden="true"
              />
              <b
                v-else-if="group.numbered"
                class="aj-num"
                aria-hidden="true"
              >{{ i + 1 }}</b>
              <AppIcon
                v-else
                :name="task.icon"
                class="aj-icon"
              />
              <span class="aj-task-main">
                <strong>{{ task.title }}</strong>
                <span>{{ task.detail }}</span>
              </span>
              <span class="aj-action">{{ task.action }}<span
                class="arrow-circle aj-arrow"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span></span>
            </RouterLink>
          </li>
        </component>
      </section>
    </div>

    <aside class="aj-side">
      <section
        class="aj-orp"
        aria-labelledby="aj-orp-title"
        data-test="orp-month"
      >
        <div class="aj-orp-head">
          <h2 id="aj-orp-title">
            ORP
          </h2>
          <RouterLink
            to="/bilan/orp"
            data-test="orp-month-link"
          >
            Voir le suivi
          </RouterLink>
        </div>
        <!-- La barre ORP (PR 48) : le mois, le rythme et « Cette semaine ». -->
        <OrpBar
          :month="today.month"
          :count="today.month_count"
          :target="today.month_target ?? null"
          :due="today.month_due_date ?? null"
          :pace="!starting"
          :week="weekCount"
        />
      </section>
      <TriageMini
        v-if="miniOpen && !starting"
        :offers="dose"
        @done="onMiniDone(true)"
        @resumed="onMiniDone(false)"
      />
      <section
        v-else-if="!starting || newcomer"
        class="aj-none"
        aria-labelledby="aj-none-title"
        data-test="today-no-triage"
      >
        <h2 id="aj-none-title">
          Offres à trier
        </h2>
        <TriageNone
          :title="newcomer ? undefined : emptyTitle"
          :widen="widen && !newcomer"
          :first="newcomer"
        />
      </section>
    </aside>
  </div>
  <section
    v-if="!today"
    class="band"
  >
    <div class="container today">
      <NetworkError
        v-if="offline"
        @retry="load()"
      />
      <LoadingBlocks
        v-else
        :heights="['7rem', '7rem', '12rem']"
      />
    </div>
  </section>
  <SuccessCard
    v-if="goalWon && today"
    name="reussite"
    keep-focus
    title="Objectif du mois atteint"
    test-id="goal-moment"
    @close="goalWon = false"
  >
    <p>{{ today.month_count }} candidatures sur {{ today.month_target }}.</p>
  </SuccessCard>
  <FirstApplicationCard
    v-else-if="stepsWon && today?.first_application"
    :company="today.first_application.company"
    :sent-at="today.first_application.sent_at"
    :application-id="today.first_application.id"
    :count="today.month_count"
    :target="today.month_target ?? null"
    @close="stepsWon = false"
  />
</template>

<style scoped>
/* Les valeurs des maquettes AujourdhuiOrdinateurV2 et AujourdhuiOrdinateurV2Sombre, écrites avec les échelles ; les
   tailles hors échelle sont nommées ici. Sous 1100 px de large, la colonne de droite passe sous celle de gauche. */
.aj {
  --aj-w: 1280px; --aj-side: 440px; --aj-40: 40px; --aj-r: 32px; --aj-28: 28px; --aj-44: 2.75rem; --aj-17: 1.0625rem; --aj-26: 1.625rem; --aj-22: 1.375rem; --aj-18: 1.125rem; --aj-16: 1rem; --aj-15: 0.9375rem;
  --aj-row: 88px; --aj-num: 36px; --aj-circle: 44px; --aj-lh-title: 1.25;
  display: grid; grid-template-columns: minmax(0, 1fr) var(--aj-side); gap: var(--aj-40); box-sizing: border-box; max-width: calc(var(--aj-w) + 2 * var(--space-6)); margin: 0 auto; padding: var(--space-6) var(--space-6) var(--space-12);
}
.aj-main { display: flex; flex-direction: column; min-width: 0; }
.aj-hero { display: flex; align-items: center; gap: var(--space-6); padding: var(--space-8) var(--aj-40); border-radius: var(--aj-r); background: var(--peach-soft); }
.aj-hero > div { flex: 1; min-width: 0; }
.aj-hello { margin: 0; font-size: var(--aj-16); color: var(--text-lead); }
.aj-late, .aj-title { margin: var(--space-3) 0 0; }
.aj-late { font-size: var(--aj-44); line-height: var(--leading-none); font-weight: var(--weight-regular); }
.aj-hand { display: inline-block; font-family: var(--font-hand); font-size: var(--aj-44); line-height: var(--leading-none); color: var(--primary-text); transform: rotate(-2deg); }
.aj-hand-late { color: var(--peach-text); }
/* L'objectif du mois atteint (§6 du lot du 13 novembre au soir) : la première ligne en vert (#17734A, #62D497 en sombre). */
.aj-hand-reached { color: var(--success); }
.aj-title { font-size: var(--font-page); font-weight: var(--weight-heavy); line-height: var(--aj-lh-title); letter-spacing: -0.4px; color: var(--text); }
.aj-title-hand { font-family: var(--font-hand); font-weight: var(--weight-regular); font-size: 1.45em; line-height: 0; letter-spacing: 0; color: var(--primary-text); }
.aj-sub { margin: var(--space-4) 0 0; font-size: var(--aj-17); line-height: var(--aj-26); color: var(--text-lead); }
.aj-main > .today-welcome { margin: var(--space-6) 0 0; }
.aj-section > h2, .aj-orp h2, .aj-none h2 { margin: 0; font-size: var(--aj-22); font-weight: var(--weight-heavy); }
.aj-section > h2 { margin: var(--space-8) 0 var(--space-3); }
.today-tasks { display: flex; flex-direction: column; gap: var(--space-3); margin: 0; padding: 0; list-style: none; }
.today-task {
  --tone-text: var(--primary-text);
  display: flex; align-items: center; gap: var(--space-4); min-height: var(--aj-row); box-sizing: border-box; padding: var(--space-3) var(--space-4) var(--space-3) var(--space-5);
  border-radius: var(--space-5); background: var(--surface); color: var(--text); text-decoration: none;
}
.today-task.tone-late { --tone-text: var(--peach-text); }
.today-task.tone-interview { --tone-text: var(--success); }
.aj-num { flex: none; display: grid; place-items: center; width: var(--aj-num); height: var(--aj-num); border-radius: 50%; background: var(--surface-muted); color: var(--text); font-size: var(--aj-16); font-weight: var(--weight-bold); }
.tone-late .aj-num { background: var(--peach-text); color: var(--surface); }
/* « Remettre les justificatifs » (§61, AujourdhuiOrdinateurV2) : le cercle à cocher de 26 px (zone de 44) à la place du
   numéro de 36 ; la place du numéro reste vide sous lui, le lien garde toute la ligne. */
.aj-checkable { position: relative; }
.aj-checkable > .task-check { position: absolute; z-index: 1; top: 50%; left: var(--space-4); transform: translateY(-50%); }
.today-task .aj-num-check { background: none; }
.aj-icon { flex: none; width: var(--space-6); height: var(--space-6); color: var(--tone-text); }
.aj-task-main { flex: 1; min-width: 0; }
.aj-task-main strong { display: block; font-size: var(--aj-18); line-height: var(--space-6); font-weight: var(--weight-bold); overflow-wrap: anywhere; }
.aj-task-main > span { display: block; margin-top: var(--space-1); font-size: var(--aj-15); line-height: var(--aj-22); color: var(--text-secondary); overflow-wrap: anywhere; }
.tone-late .aj-task-main > span { color: var(--peach-text); font-weight: var(--weight-semibold); }
.aj-action { flex: none; display: flex; align-items: center; gap: var(--space-4); font-size: var(--aj-16); font-weight: var(--weight-bold); color: var(--tone-text); white-space: nowrap; }
.aj-arrow { --circle: var(--aj-circle); }

/* Carte Google Emplois (§22 du 15.11) : une ligne des premiers pas sur le fond de la carte ORP. */
.aj-google { margin-top: var(--space-8); padding-right: var(--space-3); background: var(--primary-soft); }
.aj-google .aj-num, .aj-google-go { background: var(--surface); color: var(--primary-text); }
.aj-google-go { display: inline-flex; align-items: center; gap: var(--space-2); height: var(--btn-tertiary); --aj-22px: 22px; padding: 0 var(--aj-22px); border-radius: var(--radius-pill); color: var(--text); font-weight: var(--weight-bold); text-decoration: none; white-space: nowrap; }
.aj-google-x { width: var(--target-min); height: var(--target-min); }
.aj-google .aj-task-main > span, .aj-google-x { color: var(--text-lead); }
.aj-google-links { display: flex; gap: var(--space-6); margin-top: var(--space-2); }
.aj-google-phone.aj-google { flex-wrap: wrap; gap: var(--space-3); margin-top: var(--space-6); padding: var(--space-4); }
.aj-google-phone .aj-google-go { order: 1; flex: 1 0 100%; justify-content: center; }
.aj-google-phone .aj-google-x { margin: calc(-1 * var(--space-2)) calc(-1 * var(--space-2)) 0 0; }
.aj-google-phone.aj-google-links { flex-direction: column; align-items: flex-start; gap: 0; }

.aj-side { display: flex; flex-direction: column; gap: var(--space-6); min-width: 0; }
.aj-orp { padding: var(--aj-28) var(--space-8); border-radius: var(--space-6); background: var(--primary-soft); }
.aj-orp-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--space-5); }
.aj-orp-head a, .aj-google-links a { display: inline-flex; align-items: center; min-height: var(--target-min); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.aj-orp-head a { margin: calc(-1 * var(--space-3)) 0; }
.aj-orp-head a:hover { text-decoration: underline; }
.aj-none { padding-top: var(--space-1); }
.aj-none h2 { margin: 0 var(--space-1) var(--space-5); }
.aj-side > :deep(.tri-mini) { padding-top: var(--space-1); }
@media (max-width: 1099px) {
  .aj { grid-template-columns: minmax(0, 1fr); }
}
</style>
