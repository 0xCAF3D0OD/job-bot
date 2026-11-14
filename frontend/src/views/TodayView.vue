
<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from "vue";
import { RouterLink, type RouteLocationRaw } from "vue-router";

import { api, type Offer, type Today } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import RhythmCard from "../components/RhythmCard.vue";
import FirstSteps from "../components/FirstSteps.vue";
import { useAuth } from "../composables/useAuth";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import OrpBar from "../components/OrpBar.vue";
import OrpMonth from "../components/OrpMonth.vue";
import SuccessCard from "../components/SuccessCard.vue";
import type { HomeTodo } from "../components/HomePhone.vue";
import TriageNone from "../components/TriageNone.vue";
import { usePhone } from "../composables/usePhone";
import { useCollect } from "../composables/useCollect";
import { useCvReading } from "../composables/useCvReading";
import { DOSE, DOSE_CATCH_UP, markTriageDone, triageDoneToday, unmarkTriageDone } from "../composables/useDailyDose";
import { dateInList, dateInSentence, inDays, timeOfDay } from "../dates";
import { dailyPace, daysBefore, formatMonth, localDate, ofMonth, orpLeftLine, orpPace, plural } from "../format";
import type { IconName } from "../icons";
import { useDataChanged } from "../composables/useDataChanged";
import { firstGoal } from "../composables/useGoalMoment";
import { offerUndo } from "../composables/useUndo";
import { usePageReady } from "../composables/usePageTransition";

// Aujourd'hui sur ordinateur (maquettes AujourdhuiOrdinateurV2 et AujourdhuiOrdinateurV2Sombre du 13 novembre, états
// « accueil », « vide » et « atteint »), en deux colonnes. À gauche : l'accroche sur un fond pêche (« Bonjour Kevin »,
// le titre du jour et sa fin à la main ; avec un justificatif en retard, deux lignes manuscrites, le retard d'abord ;
// l'objectif du mois atteint, en vert puis en bleu), « À faire » (une carte par tâche, numérotée, celle en retard en
// numéro 1), « Quand tu as le temps ». À droite : la bande ORP (la barre ORP), puis « {n} offres à trier » : le livre en
// petit, où l'on trie sur place. Un jour de repos garde l'ancienne mise en page (planche AujourdhuiOrdinateurReposD,
// gardée telle quelle par le paquet du 13 novembre) : la bande bleu pâle, la carte du mois et les ronds de la semaine.
// Le téléphone a sa propre page (HomePhone).
// L'Accueil du téléphone et le petit livre de l'ordinateur sont chargés à part : chaque appareil ne reçoit que sa
// moitié (budget de poids du premier affichage). Le chargement part tout de suite, en même temps que les données.
const loadHomePhone = () => import("../components/HomePhone.vue");
const loadTriageMini = () => import("../components/TriageMini.vue");
const HomePhone = defineAsyncComponent(loadHomePhone);
const TriageMini = defineAsyncComponent(loadTriageMini);
const today = ref<Today | null>(null);
// L'Accueil du téléphone (docs/139 étape 4) : sa propre mise en page, sous 820 px.
const { phone } = usePhone();
void (phone.value ? loadHomePhone() : loadTriageMini());
// Le prénom de « Bonjour Kevin. » : le premier mot du nom des Coordonnées.
const firstName = ref<string | null>(null);
usePageReady("today", () => !!today.value);
const best = ref<Offer[]>([]);
const preparing = ref<Offer[]>([]);
// Le tri du jour fini sur cet appareil (l'écran de tri et le petit livre le notent à la fin de la pile).
const triageDone = ref(false);
// Le petit livre reste ouvert jusqu'au prochain chargement de la page, même le tri fini : « Annuler » y remet l'offre.
const miniOpen = ref(false);
// Un jour de repos (docs/86) : aucune liste à traiter.
const restDay = computed(() => today.value?.rhythm?.research_today === false);
// Le mois ORP en retard sur son rythme (format.orpPace).
const monthBehind = computed(() => {
  const t = today.value;
  return !!t && orpPace(t.month_count, t.month_target, t.month)?.state === "behind";
});
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
const dose = computed(() => best.value.slice(0, monthBehind.value ? DOSE_CATCH_UP : DOSE));
// Les premiers pas (docs/128) : tant qu'il en manque, la carte remplace la phrase et le tri ; le mois
// ORP reste, le reste attend.
const starting = computed(() => {
  const t = today.value;
  return !!t && !t.first_steps_dismissed && t.first_steps.some((s) => !s.done);
});
// Le tri à faire : une tâche « Trier » sur ordinateur, les offres de la dose sur téléphone.
const triagePending = computed(() => !restDay.value && !rhythmPaused.value && dose.value.length > 0 && !triageDone.value);
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
type Task = { key: string; test: string; icon: IconName; title: string; detail: string; action: string; to: RouteLocationRaw };
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
      detail: days < 0 ? (restDay.value ? `Échéance passée ${dateInSentence(`${t.orp_due_date}T12:00:00`)}` : `En retard depuis ${dateInSentence(`${t.orp_due_date}T12:00:00`)}.`) : days === 0 ? "À remettre aujourd’hui." : `À remettre avant ${dateInSentence(`${t.orp_due_date}T12:00:00`)}.`,
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

// Le titre de la bande : l'action du jour, calculée sur le rythme qu'il faut pour tenir l'objectif ORP ; sa fin en
// écriture manuscrite (un seul accent par écran). Un seul élément de titre.
type Heading = { lead: string; hand: string; sub: string };
const heading = computed<Heading>(() => {
  const t = today.value;
  if (!t) return { lead: "", hand: "", sub: "" };
  if (starting.value) return { lead: "Commence par les premiers pas.", hand: "", sub: "" };
  const pause = t.rhythm?.pause_until;
  if (pause) return { lead: "En", hand: "pause.", sub: `Jusqu’au ${untilDay(pause)}. Pense à l’annoncer à ton conseiller.` };
  const waiting = deskTodo.value.length + deskLater.value.length;
  const more = waiting ? `Si tu veux avancer, ${waiting === 1 ? "une chose t’attend" : `${waiting} choses t’attendent`}.` : "Profite de ta journée.";
  if (restDay.value) {
    const weekDone = !!t.rhythm && t.rhythm.target !== null && t.rhythm.count >= t.rhythm.target;
    return { lead: "Jour de", hand: "repos.", sub: weekDone ? `Ta semaine est faite. ${more}` : more };
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
type DeskTask = Task & { tone: "late" | "normal" | "interview"; href?: string };
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
    // Un jour de repos, tout est facultatif : une seule liste.
    (restDay.value || rhythmPaused.value ? todo : later).push(follow);
  }
  return { todo, later };
});
// Des offres dès l'inscription (docs/144) : tant qu'aucune offre n'est arrivée, trois façons d'en
// trouver tout de suite, sans attendre le premier e-mail d'alerte des sites.
const starterTasks = computed<DeskTask[]>(() => {
  const t = today.value;
  if (!t || !starting.value || (t.has_offers ?? true)) return [];
  const list: DeskTask[] = [];
  if (t.search_url) {
    list.push({ key: "google", test: "start-google", icon: "search", title: "Chercher sur Google Emplois", detail: "Les offres de jobup, jobs.ch et d’autres sites, réunies", action: "Ouvrir", to: "", href: t.search_url, tone: "normal" });
  }
  // Alertes prêtes : la carte des premiers pas propose déjà « Ajouter une offre ».
  const alertsDone = t.first_steps.some((s) => s.key === "alerts" && s.done);
  if (!alertsDone) {
    list.push({ key: "add", test: "start-add", icon: "link", title: "Ajouter une offre vue ailleurs", detail: "Colle son lien : jobA1 la lit et la note", action: "Ajouter", to: "/ajouter-une-offre", tone: "normal" });
  }
  list.push(
    { key: "forward", test: "start-forward", icon: "reply", title: "Transférer mes alertes existantes", detail: "Déjà des alertes jobup ou Indeed : elles arrivent ici", action: "Transférer", to: "/candidatures/alertes", tone: "normal" },
  );
  return list;
});
// Le mois de l'inscription : pas de « en retard » tant que les premiers pas ne sont pas faits.
const orpLine = computed(() => {
  const t = today.value;
  if (!t || !starting.value || !t.month_target || t.month_count >= t.month_target) return undefined;
  return orpLeftLine(t.month_count, t.month_target, t.month, t.month_due_date);
});
// « Cette semaine · 2 sur 3 » sous la barre ORP : pas pendant une pause ni les premiers pas.
const weekCount = computed(() => {
  const week = today.value?.rhythm;
  return week && week.target !== null && !week.pause_until && !starting.value ? { count: week.count, target: week.target } : null;
});
const deskTodo = computed(() => deskTasks.value.todo);
const deskLater = computed(() => deskTasks.value.later);
// La carte du mois ORP : toute la carte mène au Bilan ; sa phrase lue remplace le détail dessiné.
const monthName = computed(() => (today.value ? formatMonth(today.value.month).split(" ")[0]!.toLowerCase() : ""));
const orpLabel = computed(() => {
  const t = today.value;
  if (!t) return "";
  const month = t.month_target ? `${t.month_count} sur ${t.month_target}` : plural(t.month_count, "candidature", "candidatures");
  const week = t.rhythm && t.rhythm.target !== null ? `, cette semaine ${t.rhythm.count} sur ${t.rhythm.target}` : "";
  return `Mois ORP : ${monthName.value} ${month}${week}. Voir le bilan`;
});

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
    list.push({ key: group, test: `todo-${task.test}`, count, label: "", to: task.to, ...(group === "cv" ? { icon: task.icon, detail: task.detail } : {}) });
  }
  for (const todo of list) {
    const n = todo.count;
    todo.label = {
      meeting: "Rendez-vous ORP à préparer",
      interview: many(n, "Entretien à préparer", "Entretiens à préparer"),
      orp: t.orp_due_month ? `Justificatifs ${ofMonth(t.orp_due_month)} à remettre` : "Justificatifs à remettre",
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
// Le petit livre finit le tri (ou « Annuler » le reprend) : la tâche « Trier » suit.
function onMiniDone(done: boolean): void {
  triageDone.value = done;
  if (done) markTriageDone();
  else unmarkTriageDone();
}

const dateTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" }).format(
  new Date(),
);
// La collecte seulement quand elle tourne ou a plus d'un jour de retard (docs/131 §B.6).
const collectNote = computed(() => {
  const last = today.value?.last_collect_at;
  const late = !!last && Date.now() - new Date(last).getTime() > DAY_MS;
  // dates.ts, jamais « il y a 136 heures » : « collecte hier », sinon « collecte le 22 octobre ».
  return message.value || (late ? `collecte ${dateInList(last!) === "hier" ? "hier" : dateInSentence(last!)}` : "");
});
// L'étiquette au-dessus du titre d'un jour de repos : la date et la dernière collecte.
const eyebrow = computed(() => (collectNote.value ? `${dateTitle} · ${collectNote.value}` : dateTitle));
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
  // Un jour de repos, l'ancienne mise en page et ses styles (today-rest.css, chargés seulement ce jour-là, avant
  // l'affichage : pas d'écran sans style).
  if (day.data?.rhythm?.research_today === false && !phone.value) await import("../today-rest.css");
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
  // Le petit livre s'ouvre s'il y a un tri à faire ; ouvert, il le reste (le tri fini s'y lit, « Annuler » y revient).
  miniOpen.value ||= triagePending.value;
  if (firstName.value === null) {
    const who = await api.GET("/api/identity").catch(() => null);
    firstName.value = who?.data?.name?.trim().split(/\s+/)[0] || "";
  }
}

// Masquer les premiers pas : la carte s'en va tout de suite, « Annuler » pendant 6 secondes
// (docs/108) ; ensuite, elle ne revient plus (docs/128 §1).
function dismissSteps(): void {
  if (!today.value) return;
  today.value = { ...today.value, first_steps_dismissed: true };
  void offerUndo({
    message: "Premiers pas masqués.",
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
    <FirstSteps
      v-if="starting"
      :steps="today.first_steps"
      :has-offers="today.has_offers ?? true"
      :offer-id="today.first_steps_offer_id ?? null"
      :pick-ready="!restDay && !rhythmPaused && best.length > 0"
      @dismiss="dismissSteps"
    />
  </HomePhone>
  <div
    v-if="!phone && today && !restDay"
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
            v-else-if="goalReached"
            id="today-title"
            class="aj-late"
            data-test="today-sentence"
          >
            <span class="aj-hand aj-hand-reached">Objectif du mois atteint,</span><br><span class="aj-hand">la suite est en plus</span>
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
            v-if="lateCatch || goalReached || heading.sub"
            class="aj-sub"
            data-test="today-sub"
          >
            {{ lateCatch ? lateCatch.sub : goalReached ? reachedSub : heading.sub }}
          </p>
        </div>
        <img
          src="/tri/orange-liste.webp"
          alt=""
          width="174"
          height="168"
        >
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

      <!-- Les premiers pas (docs/128) : la seule action tant qu'il en manque. -->
      <FirstSteps
        v-if="starting"
        :steps="today.first_steps"
        :has-offers="today.has_offers ?? true"
        :offer-id="today.first_steps_offer_id ?? null"
        :pick-ready="!restDay && !rhythmPaused && best.length > 0"
        @dismiss="dismissSteps"
      />

      <section
        v-for="group in [
          { key: 'start', title: 'Des offres dès maintenant', items: starterTasks, test: 'today-start', numbered: false },
          { key: 'todo', title: 'À faire', items: deskTodo, test: 'today-tasks', numbered: true },
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
          >
            <!-- Google Emplois s'ouvre dans un nouvel onglet ; le reste reste dans jobA1. -->
            <component
              :is="task.href ? 'a' : RouterLink"
              v-bind="task.href ? { href: task.href, target: '_blank', rel: 'noopener noreferrer' } : { to: task.to }"
              :class="['today-task', `tone-${task.tone}`]"
              :data-test="task.test"
            >
              <b
                v-if="group.numbered"
                class="aj-num"
                aria-hidden="true"
              >{{ i + 1 }}</b>
              <AppIcon
                v-else
                :name="task.icon"
                class="aj-icon"
              />
              <span class="aj-task-main">
                <strong>{{ task.title }}<span
                  v-if="task.href"
                  class="visually-hidden"
                > (nouvel onglet)</span></strong>
                <span>{{ task.detail }}</span>
              </span>
              <span class="aj-action">{{ task.action }}<span
                class="arrow-circle aj-arrow"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span></span>
            </component>
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
        v-else-if="!starting"
        class="aj-none"
        aria-labelledby="aj-none-title"
        data-test="today-no-triage"
      >
        <h2 id="aj-none-title">
          Offres à trier
        </h2>
        <TriageNone
          :title="emptyTitle"
          :widen="widen"
        />
      </section>
    </aside>
  </div>
  <!-- Un jour de repos : l'ancienne mise en page (planche AujourdhuiOrdinateurReposD, gardée telle quelle). -->
  <template v-if="!phone && today && restDay">
    <section
      class="today-band"
      aria-labelledby="today-title"
      data-test="today-band"
    >
      <div class="today-band-inner">
        <p
          class="today-eyebrow"
          data-test="page-eyebrow"
        >
          {{ eyebrow }}
        </p>
        <h1
          id="today-title"
          class="today-title"
          data-test="today-sentence"
        >
          {{ heading.lead }}<template v-if="heading.hand">
            {{ " " }}<span class="today-hand">{{ heading.hand }}</span>
          </template>
        </h1>
        <p
          v-if="heading.sub"
          class="today-band-sub"
          data-test="today-sub"
        >
          {{ heading.sub }}
        </p>
      </div>
    </section>
    <!-- Sous la bande, le fond crème de la page sur toute la largeur (MODIFICATIONS_9 §1). -->
    <div class="today-page-bg">
      <div class="today-page">
        <RouterLink
          to="/bilan/orp"
          class="today-orp-card"
          :aria-label="orpLabel"
          data-test="orp-month"
        >
          <OrpMonth
            :title="`Mois ORP · ${monthName}`"
            :count="today.month_count"
            :target="today.month_target ?? null"
            :month="today.month"
            :line="orpLine"
            :due="today.month_due_date ?? null"
            band
          />
          <template v-if="today.rhythm && !starting">
            <span
              class="today-orp-rule"
              aria-hidden="true"
            />
            <RhythmCard
              :week="today.rhythm"
              :month-behind="monthBehind"
              band
            />
          </template>
          <AppIcon
            name="chevron"
            class="today-orp-chevron"
          />
        </RouterLink>

        <!-- Accueil remis à plus tard (docs/66 §4) : le reprendre d'un clic. -->
        <RouterLink
          v-if="me?.welcome === 'postponed'"
          to="/bienvenue"
          class="notice today-welcome"
          data-test="finish-welcome"
        >
          <strong>Terminer mon accueil</strong> : quelques questions pour régler ta recherche.
        </RouterLink>

        <!-- Les premiers pas (docs/128) : la seule action tant qu'il en manque. -->
        <FirstSteps
          v-if="starting"
          :steps="today.first_steps"
          :has-offers="today.has_offers ?? true"
          :offer-id="today.first_steps_offer_id ?? null"
          :pick-ready="!restDay && !rhythmPaused && best.length > 0"
          @dismiss="dismissSteps"
        />

        <section
          v-for="group in [
            { key: 'start', title: 'Des offres dès maintenant', items: starterTasks, test: 'today-start' },
            { key: 'todo', title: 'À faire', items: deskTodo, test: 'today-tasks' },
            { key: 'later', title: 'Quand tu as le temps', items: deskLater, test: 'today-later' },
          ].filter((g) => g.items.length)"
          :key="group.key"
          class="today-section"
          :aria-labelledby="`today-${group.key}-title`"
          :data-test="group.test"
        >
          <h2 :id="`today-${group.key}-title`">
            {{ group.title }}
          </h2>
          <ul class="today-tasks">
            <li
              v-for="task in group.items"
              :key="task.key"
            >
              <!-- Google Emplois s'ouvre dans un nouvel onglet ; le reste reste dans jobA1. -->
              <a
                v-if="task.href"
                :href="task.href"
                target="_blank"
                rel="noopener noreferrer"
                :class="['today-task', `tone-${task.tone}`]"
                :data-test="task.test"
              >
                <AppIcon
                  :name="task.icon"
                  class="today-task-icon"
                />
                <span class="today-task-main">
                  <strong>{{ task.title }}<span class="visually-hidden"> (nouvel onglet)</span></strong>
                  <span>{{ task.detail }}</span>
                </span>
                <span class="today-task-action">{{ task.action }}<span
                  class="arrow-circle"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span></span>
              </a>
              <RouterLink
                v-else
                :to="task.to"
                :class="['today-task', `tone-${task.tone}`]"
                :data-test="task.test"
              >
                <AppIcon
                  :name="task.icon"
                  class="today-task-icon"
                />
                <span class="today-task-main">
                  <strong>{{ task.title }}</strong>
                  <span>{{ task.detail }}</span>
                </span>
                <span class="today-task-action">{{ task.action }}<span
                  class="arrow-circle"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span></span>
              </RouterLink>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </template>
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
  <SuccessCard
    v-else-if="stepsWon"
    face
    wink
    keep-focus
    title="Première candidature notée"
    test-id="first-steps-done"
    @close="stepsWon = false"
  >
    <p>Elle compte pour ton mois ORP.</p>
  </SuccessCard>
</template>

<style scoped>
/* Les valeurs des maquettes AujourdhuiOrdinateurV2 et AujourdhuiOrdinateurV2Sombre, écrites avec les échelles ; les
   tailles hors échelle sont nommées ici. Sous 1100 px de large, la colonne de droite passe sous celle de gauche. */
.aj {
  --aj-w: 1280px; --aj-side: 440px; --aj-40: 40px; --aj-r: 32px; --aj-28: 28px; --aj-44: 2.75rem; --aj-17: 1.0625rem; --aj-26: 1.625rem; --aj-22: 1.375rem; --aj-18: 1.125rem; --aj-16: 1rem; --aj-15: 0.9375rem;
  --aj-img: 168px; --aj-row: 88px; --aj-num: 36px; --aj-circle: 44px; --aj-lh-title: 1.25; --aj-none-r: 18px;
  display: grid; grid-template-columns: minmax(0, 1fr) var(--aj-side); gap: var(--aj-40); box-sizing: border-box; max-width: calc(var(--aj-w) + 2 * var(--space-6)); margin: 0 auto; padding: var(--space-6) var(--space-6) var(--space-12);
}
.aj-main { display: flex; flex-direction: column; min-width: 0; }
.aj-hero { display: flex; align-items: center; gap: var(--space-6); padding: var(--space-8) var(--aj-40); border-radius: var(--aj-r); background: var(--peach-soft); }
.aj-hero > div { flex: 1; min-width: 0; }
.aj-hero img { flex: none; width: auto; height: var(--aj-img); }
/* En sombre, le personnage de l'accroche a un contour clair, comme ceux du tri. */
:root[data-theme="dark"] .aj-hero img { filter: drop-shadow(0 0 1px #F3EEE6) drop-shadow(0 0 1px #F3EEE6); }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .aj-hero img { filter: drop-shadow(0 0 1px #F3EEE6) drop-shadow(0 0 1px #F3EEE6); }
}
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
.aj-main > .today-welcome, .aj-main > :deep(.first-steps) { margin: var(--space-6) 0 0; }
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
.aj-icon { flex: none; width: var(--space-6); height: var(--space-6); color: var(--tone-text); }
.aj-task-main { flex: 1; min-width: 0; }
.aj-task-main strong { display: block; font-size: var(--aj-18); line-height: var(--space-6); font-weight: var(--weight-bold); overflow-wrap: anywhere; }
.aj-task-main > span { display: block; margin-top: var(--space-1); font-size: var(--aj-15); line-height: var(--aj-22); color: var(--text-secondary); overflow-wrap: anywhere; }
.tone-late .aj-task-main > span { color: var(--peach-text); font-weight: var(--weight-semibold); }
.aj-action { flex: none; display: flex; align-items: center; gap: var(--space-4); font-size: var(--aj-16); font-weight: var(--weight-bold); color: var(--tone-text); white-space: nowrap; }
.aj-arrow { --circle: var(--aj-circle); }

.aj-side { display: flex; flex-direction: column; gap: var(--space-6); min-width: 0; }
.aj-orp { padding: var(--aj-28) var(--space-8); border-radius: var(--space-6); background: var(--primary-soft); }
.aj-orp-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--space-5); }
.aj-orp-head a { display: inline-flex; align-items: center; min-height: var(--target-min); margin: calc(-1 * var(--space-3)) 0; font-size: var(--aj-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.aj-orp-head a:hover { text-decoration: underline; }
.aj-none { padding-top: var(--space-1); }
.aj-none h2 { margin: 0 var(--space-1) var(--space-5); }
.aj-side > :deep(.tri-mini) { padding-top: var(--space-1); }
@media (max-width: 1099px) {
  .aj { grid-template-columns: minmax(0, 1fr); }
}
</style>
