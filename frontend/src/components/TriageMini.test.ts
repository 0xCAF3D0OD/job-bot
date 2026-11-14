// Le livre en petit d'Aujourd'hui sur ordinateur (lot du 11 novembre au soir, PR 49) : on trie sur place.
import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Offer } from "../api/client";
import { useUndo } from "../composables/useUndo";
import TriageMini from "./TriageMini.vue";

const PATCH = vi.fn();
vi.mock("../api/client", () => ({ api: { PATCH: (...a: unknown[]) => PATCH(...a) } }));

const offer = (id: number, title: string, score: number): Offer =>
  ({ id, title, company: "Acme SA", location: "Lausanne", score, description: "Vous exploitez nos clusters Kubernetes au quotidien.", snippet: null, passages: ["clusters Kubernetes"], has_logo: false }) as unknown as Offer;

beforeEach(() => PATCH.mockResolvedValue({ response: { ok: true } }));
afterEach(async () => {
  await useUndo().flush();
  vi.resetAllMocks();
});

const mini = () =>
  mount(TriageMini, { props: { offers: [offer(1, "DevOps", 90), offer(2, "SRE", 80)] }, global: { stubs: { RouterLink: RouterLinkStub } }, attachTo: document.body });

describe("Le petit livre d’Aujourd’hui (PR 49)", () => {
  it("« {n} offres à trier », le compteur, l’offre ouverte : titre, entreprise, note, extrait surligné et sa légende", () => {
    const view = mini();
    expect(view.find("h2").text()).toBe("2 offres à trier");
    expect(view.find("[data-test=triage-mini-count]").text()).toBe("1 sur 2");
    expect(view.find("[data-test=triage-mini-title]").text()).toBe("DevOps");
    expect(view.text()).toContain("Acme SA · Lausanne");
    expect(view.text()).toContain("Très proche");
    expect(view.findAll("[data-test=triage-mini-excerpt] mark").map((m) => m.text())).toEqual(["clusters Kubernetes"]);
    // Le surlignage a toujours sa légende en texte (§1 du lot).
    expect(view.find("[data-test=triage-mini-legend]").text()).toBe("1 point retrouvé");
    view.unmount();
  });

  it("« Écarter » et « Garder » sont de vrais boutons ; on trie sur place, « Annuler » remet l’offre, la fin se dit", async () => {
    const view = mini();
    const keep = view.find("[data-test=triage-mini-keep]");
    const dismiss = view.find("[data-test=triage-mini-dismiss]");
    expect([keep.element.tagName, keep.text(), dismiss.element.tagName, dismiss.text()]).toEqual(["BUTTON", "Garder", "BUTTON", "Écarter"]);
    await keep.trigger("click");
    await flushPromises();
    expect(view.find("[data-test=triage-mini-count]").text()).toBe("2 sur 2");
    expect(document.activeElement).toBe(view.find("[data-test=triage-mini-title]").element);
    expect(useUndo().pending.value?.message).toBe("Offre gardée dans tes candidatures");
    // Rien n'est parti au serveur ; « Annuler » remet l'offre à l'écran.
    expect(PATCH).not.toHaveBeenCalled();
    await useUndo().undo();
    await flushPromises();
    expect(view.find("[data-test=triage-mini-title]").text()).toBe("DevOps");
    await view.find("[data-test=triage-mini-keep]").trigger("click");
    await view.find("[data-test=triage-mini-dismiss]").trigger("click");
    await flushPromises();
    // La dernière offre triée : le bloc de fin, et le parent le sait.
    expect(view.find("[data-test=triage-mini-done]").text()).toContain("Tri terminé · À demain");
    expect(view.emitted("done")).toHaveLength(1);
    await useUndo().flush();
    const sent = PATCH.mock.calls.map((c) => [(c[1] as { params: { path: { offer_id: number } } }).params.path.offer_id, (c[1] as { body: { status: string } }).body.status]);
    expect(sent).toEqual([[1, "later"], [2, "ignored"]]);
    view.unmount();
  });

  it("« Annuler » sur la dernière offre : le tri reprend", async () => {
    const view = mount(TriageMini, { props: { offers: [offer(1, "DevOps", 90)] }, global: { stubs: { RouterLink: RouterLinkStub } } });
    await view.find("[data-test=triage-mini-dismiss]").trigger("click");
    await flushPromises();
    expect(view.emitted("done")).toHaveLength(1);
    await useUndo().undo();
    await flushPromises();
    expect(view.emitted("resumed")).toHaveLength(1);
    expect(view.find("[data-test=triage-mini-title]").text()).toBe("DevOps");
    expect(PATCH).not.toHaveBeenCalled();
  });
});
