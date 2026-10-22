import type { Application, OrpRow } from "./api/client";
import { isoDay } from "./contactLabels";

// Où en est une candidature (docs/38, docs/23) : partagé par la carte et le panneau du Suivi (docs/46).
const REMIND_AFTER_DAYS = 10;
const NO_ANSWER_DAYS = 14;

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return isoDay(d);
}

// Le jour choisi dans l'étape « Suivre » (docs/124 §G), sinon 10 jours après l'envoi.
export function followUpDue(a: Application): boolean {
  if (a.status !== "en_attente") return false;
  return a.follow_up_on ? a.follow_up_on <= daysAgo(0) : a.sent_at <= daysAgo(REMIND_AFTER_DAYS);
}

export function noAnswerDue(a: Application): boolean {
  return a.status === "relancee" && !!a.followed_up_at && a.followed_up_at <= daysAgo(NO_ANSWER_DAYS);
}

export function interviewUpcoming(a: Application): boolean {
  return !!a.interview_at && new Date(a.interview_at).getTime() > Date.now();
}

// Entretien passé sans retour pour ce jour-là (docs/23 §1).
export function needsFeedback(a: Application): boolean {
  if (a.status !== "entretien" || !a.interview_at) return false;
  const day = new Date(a.interview_at).toISOString().slice(0, 10);
  return day <= new Date().toISOString().slice(0, 10) && !a.interviews?.some((i) => i.held_at === day);
}

export type NextStep = {
  key: "prepare" | "feedback" | "follow-up" | "no-answer" | "complete" | "manage";
  text: string;
  action: string;
};

const interviewDate = new Intl.DateTimeFormat("fr-CH", {
  weekday: "long",
  day: "numeric",
  month: "short",
  hour: "numeric",
  minute: "2-digit",
});

// Une seule prochaine étape sur la carte, la plus urgente (docs/46 §2).
export function nextStep(a: Application, row?: OrpRow | null): NextStep {
  if (interviewUpcoming(a)) {
    return { key: "prepare", text: `Entretien ${interviewDate.format(new Date(a.interview_at!))}`, action: "Préparer" };
  }
  if (needsFeedback(a)) return { key: "feedback", text: "Entretien passé", action: "Faire le point" };
  if (followUpDue(a)) return { key: "follow-up", text: "Sans réponse depuis 10 jours", action: "Relancer" };
  if (noAnswerDue(a)) return { key: "no-answer", text: "Pas de réponse depuis la relance", action: "Sans réponse" };
  if (row?.missing.length) {
    return { key: "complete", text: `Pour l'ORP, il manque : ${row.missing.join(", ")}`, action: "Compléter" };
  }
  return { key: "manage", text: "", action: "Gérer" };
}
