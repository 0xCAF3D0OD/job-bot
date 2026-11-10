import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DocumentOut } from "../api/client";
import { cvSubtitle, foundDetail, resetCvReading, stateOf, useCvReading } from "../composables/useCvReading";
import CvStateBlock from "./CvStateBlock.vue";

const GET = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
  QUIET: { headers: { "X-Jobbot-Quiet": "1" } },
}));

afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
  resetCvReading();
});

const base: DocumentOut = {
  id: 4,
  filename: "CV_Kevin.pdf",
  doc_type: "pdf",
  size: 120_000,
  text_status: "ok",
  uploaded_at: "2026-11-02T08:00:00Z",
  chunk_count: 0,
  kind: null,
  read_state: null,
  read_at: null,
  found: null,
};
const doc = (extra: Partial<DocumentOut> = {}): DocumentOut => ({ ...base, ...extra });
const NOW = new Date("2026-11-10T12:00:00Z");

describe("état de la carte « Mon CV »", () => {
  it.each([
    [doc(), "relire", "Déposé le 2 novembre · pas encore lu", "todo"],
    [doc({ read_state: "reading" }), "cours", "Lecture en cours", "plain"],
    [doc({ read_state: "done", read_at: "2026-11-10T09:00:00Z", found: { experience: 4, competence: 7, formation: 1 } }), "lu", "Lu le 10 novembre · 12 éléments trouvés", "ok"],
    [doc({ read_state: "unavailable" }), "indispo", "Lecture impossible pour le moment", "todo"],
    [doc({ text_status: "unreadable" }), "illisible", "Lecture impossible", "todo"],
    [doc({ chunk_count: 3, read_at: "2026-11-02T09:00:00Z" }), "fait", "Lu le 2 novembre · 3 éléments repris", "plain"],
  ] as const)("%#", (d, state, text, tone) => {
    expect(stateOf(d)).toBe(state);
    expect(cvSubtitle(d, null, NOW)).toEqual({ text, tone });
  });

  it("dit le détail de ce qui a été trouvé", () => {
    expect(foundDetail(doc({ found: { experience: 4, competence: 7, formation: 1 } }))).toBe("4 expériences, 7 compétences et 1 formation");
    expect(foundDetail(doc({ found: { competence: 1 } }))).toBe("1 compétence");
  });

  it("le message après un dépôt passe avant l'état", () => {
    expect(cvSubtitle(doc(), "jamais", NOW)).toEqual({ text: "Déposé à l’instant · pas encore lu", tone: "todo" });
    expect(cvSubtitle(doc({ chunk_count: 2, read_at: "2026-11-02T09:00:00Z" }), "deja", NOW).text).toBe("Déposé à l’instant · lu le 2 novembre");
    expect(cvSubtitle(doc(), "nouveau", NOW)).toEqual({ text: "Déposé à l’instant · pas encore lu", tone: "plain" });
  });
});

describe("CvStateBlock", () => {
  it("« Relire mon CV » lance la lecture sur le serveur, l'état suivant est annoncé", async () => {
    vi.useFakeTimers();
    POST.mockResolvedValue({ data: doc({ read_state: "reading" }) });
    GET.mockResolvedValue({ data: [doc({ read_state: "done", read_at: "2026-11-10T09:00:00Z", found: { competence: 2 } })] });
    const reading = useCvReading();
    reading.documents.value = [doc()];
    const wrapper = mount({
      components: { CvStateBlock },
      setup: () => ({ cv: reading.cv }),
      template: `<CvStateBlock v-if="cv" :doc="cv" />`,
    });
    const live = wrapper.find("[data-test=cv-state-live]");
    expect(live.attributes("role")).toBe("status");
    expect(live.attributes("aria-live")).toBe("polite");
    expect(live.text()).toContain("Ton CV n’a pas encore été lu");
    // Un seul bouton plein.
    expect(wrapper.findAll(".cv-state-primary")).toHaveLength(1);
    await wrapper.find("[data-test=cv-read]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/documents/{document_id}/read", { params: { path: { document_id: 4 } } });
    expect(wrapper.find("[data-test=cv-state-cours]").exists()).toBe(true);
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Lecture du CV");
    // Le suivi interroge le serveur jusqu'à la fin de la lecture.
    await vi.advanceTimersByTimeAsync(3000);
    await flushPromises();
    expect(live.text()).toContain("2 éléments trouvés");
    expect(wrapper.find("[data-test=cv-choose]").exists()).toBe(true);
  });

  it("« Choisir les éléments » ouvre la liste trouvée ; une fois choisis, elle n'est plus gardée", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/documents/{document_id}/read"
            ? [{ kind: "competence", title: "Helm", content: "Charts", tags: [], duplicate_of: null }]
            : path === "/api/profile-chunks"
              ? []
              : [doc({ read_state: "done", chunk_count: 1 })],
      }),
    );
    POST.mockResolvedValue({ data: { id: 1 } });
    DELETE.mockResolvedValue({});
    const wrapper = mount(CvStateBlock, { props: { doc: doc({ read_state: "done", found: { competence: 1 } }) }, attachTo: document.body });
    await wrapper.find("[data-test=cv-choose]").trigger("click");
    await flushPromises();
    expect(document.body.textContent).toContain("Repris de « CV_Kevin.pdf »");
    const add = [...document.body.querySelectorAll("button")].find((b) => b.textContent?.includes("Ajouter 1 élément"));
    add?.click();
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/documents/{document_id}/read", { params: { path: { document_id: 4 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
    wrapper.unmount();
  });

  it("indisponible : « Réessayer » relance ; illisible : autre fichier ou à la main", async () => {
    POST.mockResolvedValue({ data: doc({ read_state: "reading" }) });
    const off = mount(CvStateBlock, { props: { doc: doc({ read_state: "unavailable" }) } });
    expect(off.text()).toContain("Ce n’est pas ton fichier. Réessaie dans quelques minutes.");
    await off.find("[data-test=cv-retry]").trigger("click");
    expect(POST).toHaveBeenCalled();

    const scan = mount(CvStateBlock, { props: { doc: doc({ text_status: "unreadable" }) } });
    await scan.find("[data-test=cv-other-file]").trigger("click");
    expect(scan.emitted("replace")).toHaveLength(1);
    expect(scan.find("[data-test=cv-manual]").text()).toBe("Remplir à la main");
  });

  it("après un dépôt : jamais lu, déjà lu, nouveau ; « Fermer » le retire", async () => {
    const reading = useCvReading();
    const never = mount(CvStateBlock, { props: { doc: doc(), notice: "jamais" } });
    expect(never.text()).toContain("Ce CV était déjà déposé, mais il n’a jamais été lu");
    expect(never.find("[data-test=cv-close]").attributes("aria-label")).toBe("Fermer le message");

    const same = mount(CvStateBlock, { props: { doc: doc({ chunk_count: 3, read_at: "2026-11-02T09:00:00Z" }), notice: "deja" } });
    expect(same.text()).toContain("C’est le même fichier, déjà lu le 2 novembre. Rien n’a changé.");
    expect(same.find("button.cv-state-primary").exists()).toBe(false);

    reading.deposited(doc({ id: 7 }), false);
    expect(reading.notice.value).toEqual({ kind: "nouveau", id: 7 });
    const fresh = mount(CvStateBlock, { props: { doc: doc({ id: 7 }), notice: "nouveau" } });
    expect(fresh.find("[data-test=cv-later]").text()).toBe("Plus tard");
    await fresh.find("[data-test=cv-close]").trigger("click");
    expect(reading.notice.value).toBeNull();
  });

  it("un CV déjà lu et choisi n'a pas de bloc", () => {
    const wrapper = mount(CvStateBlock, { props: { doc: doc({ chunk_count: 3 }) } });
    expect(wrapper.find(".cv-state").exists()).toBe(false);
    expect(wrapper.find("[data-test=cv-state-live]").exists()).toBe(true);
  });
});
