import { computed, ref } from "vue";

import { api, QUIET, type ChunkProposal, type DocumentOut } from "../api/client";
import { dateInSentence } from "../dates";
import { plural } from "../format";

// La lecture du CV par l'IA (maquette du 10 novembre au soir, PR 21) : elle tourne sur le serveur et continue quand on
// quitte la page ; la cloche prévient à la fin. L'état est partagé (Profil, Aujourd'hui, Documents) : un seul suivi
// pour toute l'application, qui interroge le serveur toutes les 3 s tant qu'une lecture est en cours.
export type CvState = "relire" | "cours" | "lu" | "indispo" | "illisible" | "fait";
// Le message après un dépôt (PR 24) : même fichier jamais lu, même fichier déjà lu, nouveau fichier.
export type CvNotice = "jamais" | "deja" | "nouveau";

const POLL_MS = 3000;

const documents = ref<DocumentOut[] | null>(null);
const notice = ref<{ kind: CvNotice; id: number } | null>(null);
let timer: ReturnType<typeof setInterval> | undefined;

// Mon CV : le dernier document déposé qui n'est pas un certificat de travail (il n'existe pas de type « CV »).
const cv = computed(() => documents.value?.find((d) => d.kind !== "certificate") ?? null);

export function stateOf(doc: DocumentOut): CvState {
  if (doc.read_state === "reading") return "cours";
  if (doc.text_status !== "ok" || doc.read_state === "unreadable") return "illisible";
  if (doc.read_state === "unavailable") return "indispo";
  if (doc.found && Object.values(doc.found).some((n) => n > 0)) return "lu";
  if (doc.chunk_count > 0 || doc.read_state === "done") return "fait";
  return "relire";
}

// Le nombre d'éléments trouvés à choisir, et leur détail : « 4 expériences, 7 compétences et 1 formation ».
export function foundCount(doc: DocumentOut): number {
  return Object.values(doc.found ?? {}).reduce((sum, n) => sum + n, 0);
}

const FOUND_WORDS: [string, string, string][] = [
  ["experience", "expérience", "expériences"],
  ["competence", "compétence", "compétences"],
  ["formation", "formation", "formations"],
  ["preference", "préférence", "préférences"],
  ["redhibitoire", "rédhibitoire", "rédhibitoires"],
  ["ton", "élément de ton", "éléments de ton"],
];
export function foundDetail(doc: DocumentOut): string {
  const parts = FOUND_WORDS.filter(([kind]) => doc.found?.[kind]).map(([kind, one, many]) => plural(doc.found?.[kind] ?? 0, one, many));
  return parts.length > 1 ? `${parts.slice(0, -1).join(", ")} et ${parts[parts.length - 1]}` : (parts[0] ?? "");
}

// La ligne sous le nom du fichier (maquette ProfilOrdinateurCV) et son ton : orange quand il y a quelque chose à
// faire, vert quand la lecture a trouvé, gris sinon.
export function cvSubtitle(doc: DocumentOut, notice: CvNotice | null, now: Date = new Date()): { text: string; tone: "todo" | "ok" | "plain" } {
  const read = doc.read_at ? dateInSentence(doc.read_at, now) : "";
  if (notice === "jamais") return { text: "Déposé à l’instant · pas encore lu", tone: "todo" };
  if (notice === "deja") return { text: `Déposé à l’instant${read ? ` · lu ${read}` : ""}`, tone: "plain" };
  if (notice === "nouveau") return { text: "Déposé à l’instant · pas encore lu", tone: "plain" };
  switch (stateOf(doc)) {
    case "cours":
      return { text: "Lecture en cours", tone: "plain" };
    case "lu":
      return { text: `Lu ${read} · ${plural(foundCount(doc), "élément trouvé", "éléments trouvés")}`, tone: "ok" };
    case "indispo":
      return { text: "Lecture impossible pour le moment", tone: "todo" };
    case "illisible":
      return { text: "Lecture impossible", tone: "todo" };
    case "fait":
      return { text: `${read ? `Lu ${read}` : `Déposé ${dateInSentence(doc.uploaded_at, now)}`} · ${plural(doc.chunk_count, "élément repris", "éléments repris")}`, tone: "plain" };
    default:
      return { text: `Déposé ${dateInSentence(doc.uploaded_at, now)} · pas encore lu`, tone: "todo" };
  }
}

function replace(doc: DocumentOut): void {
  const list = documents.value ?? [];
  documents.value = list.some((d) => d.id === doc.id) ? list.map((d) => (d.id === doc.id ? doc : d)) : [doc, ...list];
}

function follow(): void {
  const reading = documents.value?.some((d) => d.read_state === "reading");
  if (reading && timer === undefined) timer = setInterval(() => void load(), POLL_MS);
  if (!reading && timer !== undefined) {
    clearInterval(timer);
    timer = undefined;
  }
}

async function load(): Promise<DocumentOut[]> {
  try {
    const { data } = await api.GET("/api/documents", QUIET);
    if (Array.isArray(data)) documents.value = data;
  } catch {
    // Hors ligne : on garde ce qu'on a, le prochain passage réessaie.
  }
  follow();
  return documents.value ?? [];
}

// « Relire mon CV » : la lecture part sur le serveur ; « Réessayer » passe par ici aussi.
async function read(id: number): Promise<boolean> {
  if (notice.value?.id === id) notice.value = null;
  try {
    const { data } = await api.POST("/api/documents/{document_id}/read", { params: { path: { document_id: id } } });
    if (!data) return false;
    const before = documents.value?.find((d) => d.id === id);
    replace({ ...data, chunk_count: before?.chunk_count ?? data.chunk_count });
    follow();
    return true;
  } catch {
    return false;
  }
}

// « Choisir les éléments » : la liste trouvée par la dernière lecture.
async function proposals(id: number): Promise<ChunkProposal[]> {
  const { data } = await api.GET("/api/documents/{document_id}/read", { params: { path: { document_id: id } } });
  return data ?? [];
}

// Les éléments choisis : la liste proposée n'est plus gardée sur le serveur.
async function chosen(id: number): Promise<void> {
  await api.DELETE("/api/documents/{document_id}/read", { params: { path: { document_id: id } } });
  await load();
}

// Après un dépôt (« Remplacer ») : 200 = le même fichier, 201 = un nouveau (PR 24).
function deposited(doc: DocumentOut, same: boolean): void {
  replace(doc);
  documents.value = [doc, ...(documents.value ?? []).filter((d) => d.id !== doc.id)];
  if (doc.text_status !== "ok") notice.value = null;
  else if (!same) notice.value = { kind: "nouveau", id: doc.id };
  else notice.value = { kind: doc.chunk_count > 0 || doc.read_at ? "deja" : "jamais", id: doc.id };
}

function closeNotice(): void {
  notice.value = null;
}

// Pour les tests.
export function resetCvReading(): void {
  documents.value = null;
  notice.value = null;
  clearInterval(timer);
  timer = undefined;
}

export function useCvReading() {
  return { documents, cv, notice, load, read, proposals, chosen, deposited, closeNotice, stateOf };
}
