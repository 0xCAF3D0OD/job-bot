import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAssistant } from "../composables/useAssistant";
import { DATA_CHANGED_EVENT } from "../composables/useDataChanged";
import AssistantPanel from "./AssistantPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", async (original) => ({
  ...(await original<typeof import("../api/client")>()),
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), DELETE: (...a: unknown[]) => DELETE(...a) },
}));
afterEach(() => {
  vi.resetAllMocks();
  vi.unstubAllGlobals();
});

const proposal = {
  id: 7,
  kind: "offer_status",
  label: "Passer « Cloud Architect » (Jura Data SA) en Plus tard",
  state: "proposed",
  created_at: "2026-10-15T10:00:00Z",
};

// Réponse SSE minimale : un seul morceau, lu par getReader().
function stream(...events: [string, unknown][]) {
  const body = events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join("");
  let sent = false;
  return {
    ok: true,
    status: 200,
    body: {
      getReader: () => ({
        read: () => {
          if (sent) return Promise.resolve({ done: true, value: undefined });
          sent = true;
          return Promise.resolve({ done: false, value: new TextEncoder().encode(body) });
        },
      }),
    },
  };
}

async function mountPanel() {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/assistant/status" ? { available: true, model: "x" } : [] }),
  );
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/candidatures/offres");
  const assistant = useAssistant();
  assistant.available.value = true;
  assistant.open.value = true;
  const wrapper = mount(AssistantPanel, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("AssistantPanel, propositions (docs/52)", () => {
  it("affiche la proposition, la fait sur « Confirmer », puis propose « Annuler »", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          stream(
            ["conversation", { id: 3, title: "Trie" }],
            ["text", { text: "Je te propose de la mettre de côté." }],
            ["action", proposal],
            ["done", {}],
          ),
        ),
      ),
    );
    const changed = vi.fn();
    globalThis.addEventListener(DATA_CHANGED_EVENT, changed);
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=assistant-input]").setValue("Trie mes offres");
    await wrapper.find("form.assistant-form").trigger("submit");
    // Le flux se lit en plusieurs tours de boucle.
    for (let i = 0; i < 50 && !wrapper.find("[data-test=assistant-action]").exists(); i++) {
      await new Promise((resolve) => setTimeout(resolve, 5));
      await flushPromises();
    }

    // La mascotte (docs/97) : dans l'en-tête et devant la réponse, pas devant la question.
    expect(wrapper.find(".assistant-head [data-test=assistant-mascot]").exists()).toBe(true);
    expect(wrapper.find(".assistant-line.assistant [data-test=assistant-mascot]").exists()).toBe(true);
    expect(wrapper.find(".assistant-line.user [data-test=assistant-mascot]").exists()).toBe(false);
    expect(wrapper.find("[data-test=assistant-mascot]").attributes("aria-hidden")).toBe("true");

    const card = wrapper.find("[data-test=assistant-action]");
    expect(card.text()).toContain("Passer « Cloud Architect » (Jura Data SA) en Plus tard");
    expect(POST).not.toHaveBeenCalled();

    POST.mockResolvedValue({ data: { ...proposal, state: "done", note: null } });
    await card.find("[data-test=assistant-action-confirm]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/assistant/actions/{action_id}/confirm", { params: { path: { action_id: 7 } } });
    expect(wrapper.find("[data-test=assistant-action]").text()).toContain("Fait.");
    expect(wrapper.find("[data-test=assistant-action-undo]").exists()).toBe(true);
    expect(changed).toHaveBeenCalledOnce();
    globalThis.removeEventListener(DATA_CHANGED_EVENT, changed);
  });

  it("une discussion rouverte remet chaque proposition sous sa réponse, avec son état", async () => {
    const wrapper = await mountPanel();
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data: path.endsWith("{conversation_id}")
          ? {
              id: 3,
              title: "Trie",
              updated_at: "2026-10-15T10:01:00Z",
              messages: [
                { id: 1, role: "user", content: "Trie", created_at: "2026-10-15T09:59:00Z" },
                { id: 2, role: "assistant", content: "Voilà.", created_at: "2026-10-15T10:00:30Z" },
              ],
              actions: [{ ...proposal, state: "stale", note: null }],
            }
          : [{ id: 3, title: "Trie", updated_at: "2026-10-15T10:01:00Z" }],
      }),
    );
    // Discussions récentes rechargées, puis « Trie » rouverte.
    useAssistant().open.value = false;
    await flushPromises();
    useAssistant().open.value = true;
    await flushPromises();
    await wrapper.find("[data-test=assistant-recent]").trigger("click");
    await flushPromises();
    const lines = wrapper.findAll(".assistant-line");
    expect(lines[1]!.find("[data-test=assistant-action]").text()).toContain("rien n'a été changé");
    expect(wrapper.find("[data-test=assistant-action-confirm]").exists()).toBe(false);
  });
});

describe("AssistantPanel, effacer la discussion (règles §4, menu « ⋯ »)", () => {
  it("« Effacer la discussion » se confirme sur place ; « Garder » n'efface rien", async () => {
    const wrapper = await mountPanel();
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data: path.endsWith("{conversation_id}")
          ? {
              id: 3,
              title: "Trie",
              updated_at: "2026-10-15T10:01:00Z",
              messages: [{ id: 1, role: "user", content: "Trie", created_at: "2026-10-15T09:59:00Z" }],
              actions: [],
            }
          : [{ id: 3, title: "Trie", updated_at: "2026-10-15T10:01:00Z" }],
      }),
    );
    useAssistant().open.value = false;
    await flushPromises();
    useAssistant().open.value = true;
    await flushPromises();
    await wrapper.find("[data-test=assistant-recent]").trigger("click");
    await flushPromises();
    const more = wrapper.find("[data-test=assistant-more]");
    expect(more.attributes("aria-label")).toBe("Plus d'actions sur la discussion");

    await more.trigger("click");
    await wrapper.find("[data-test=assistant-erase]").trigger("click");
    expect(wrapper.find("[data-test=inline-confirm]").exists()).toBe(true);
    await wrapper.find("[data-test=inline-confirm-no]").trigger("click");
    expect(wrapper.find("[data-test=inline-confirm]").exists()).toBe(false);
    expect(DELETE).not.toHaveBeenCalled();

    await wrapper.find("[data-test=assistant-more]").trigger("click");
    await wrapper.find("[data-test=assistant-erase]").trigger("click");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/assistant/conversations/{conversation_id}", { params: { path: { conversation_id: 3 } } });
    expect(wrapper.find(".assistant-line").exists()).toBe(false);
  });
});

describe("AssistantPanel, les visages de la mascotte (docs/99)", () => {
  // Un flux qu'on fait avancer à la main : chaque appel à `push` livre un morceau, `end` le ferme.
  function manualStream() {
    const pending: ((chunk: { done: boolean; value?: Uint8Array }) => void)[] = [];
    const queue: { done: boolean; value?: Uint8Array }[] = [];
    const deliver = (chunk: { done: boolean; value?: Uint8Array }) => {
      const waiter = pending.shift();
      if (waiter) waiter(chunk);
      else queue.push(chunk);
    };
    return {
      response: {
        ok: true,
        status: 200,
        body: {
          getReader: () => ({
            read: () => {
              const next = queue.shift();
              return next ? Promise.resolve(next) : new Promise((resolve) => pending.push(resolve));
            },
          }),
        },
      },
      push: (event: string, data: unknown) =>
        deliver({ done: false, value: new TextEncoder().encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`) }),
      end: () => deliver({ done: true }),
    };
  }
  const mood = (wrapper: Awaited<ReturnType<typeof mountPanel>>, selector: string) =>
    wrapper.find(`${selector} [data-test=assistant-mascot]`).attributes("data-mood");

  it("réfléchit pendant la réponse, a trouvé à l'arrivée, puis revient à l'écoute", async () => {
    const first = manualStream();
    const second = manualStream();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(first.response).mockResolvedValueOnce(second.response));
    const wrapper = await mountPanel();
    expect(mood(wrapper, ".assistant-head")).toBe("listening");

    await wrapper.find("[data-test=assistant-input]").setValue("Où en est ma semaine ?");
    await wrapper.find("form.assistant-form").trigger("submit");
    await flushPromises();
    expect(mood(wrapper, ".assistant-head")).toBe("thinking");
    expect(mood(wrapper, "[data-test=assistant-status]")).toBe("thinking");
    expect(wrapper.find(".assistant-line.assistant [data-test=assistant-mascot]").exists()).toBe(false);

    first.push("text", { text: "Il te reste 2 candidatures." });
    await flushPromises();
    expect(mood(wrapper, ".assistant-line.assistant")).toBe("thinking");
    expect(wrapper.find("[data-test=assistant-status] [data-test=assistant-mascot]").exists()).toBe(false);

    vi.useFakeTimers();
    first.end();
    await flushPromises();
    expect(mood(wrapper, ".assistant-head")).toBe("found");
    expect(mood(wrapper, ".assistant-line.assistant")).toBe("found");
    vi.advanceTimersByTime(2000);
    await flushPromises();
    vi.useRealTimers();
    expect(mood(wrapper, ".assistant-head")).toBe("listening");
    expect(mood(wrapper, ".assistant-line.assistant")).toBe("found");

    // À la question suivante, la réponse précédente repasse à l'écoute.
    await wrapper.find("[data-test=assistant-input]").setValue("Et la suivante ?");
    await wrapper.find("form.assistant-form").trigger("submit");
    await flushPromises();
    expect(mood(wrapper, ".assistant-line.assistant")).toBe("listening");
    second.end();
    await flushPromises();
  });

  it("une erreur reste à l'écoute", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({ detail: "Indisponible" }) })));
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=assistant-input]").setValue("Bonjour");
    await wrapper.find("form.assistant-form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".assistant-line.assistant").text()).toContain("Indisponible");
    expect(mood(wrapper, ".assistant-line.assistant")).toBe("listening");
    expect(mood(wrapper, ".assistant-head")).toBe("listening");
  });
});
