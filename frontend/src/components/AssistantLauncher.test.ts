import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAssistant } from "../composables/useAssistant";
import AssistantLauncher from "./AssistantLauncher.vue";

const panel = vi.hoisted(() => ({ loaded: 0 }));
vi.mock("./AssistantPanel.vue", async () => {
  const { defineComponent, h, onMounted } = await import("vue");
  panel.loaded += 1;
  return {
    __esModule: true,
    default: defineComponent({
      emits: ["ready"],
      setup(_, { emit }) {
        onMounted(() => emit("ready"));
        return () => h("div", { "data-test": "assistant-panel" });
      },
    }),
  };
});
vi.mock("../api/client", async (original) => ({
  ...(await original<object>()),
  api: { GET: vi.fn(async (path: string) => ({ data: path.endsWith("/status") ? { available: true } : [] })) },
}));

function router() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "today", component: { render: () => null } },
      { path: "/assistant", name: "assistant", component: { render: () => null } },
    ],
  });
}

describe("AssistantLauncher : le panneau de l'Assistant chargé à la demande (allègement du 17.11)", () => {
  beforeEach(() => {
    useAssistant().open.value = false;
  });
  afterEach(() => vi.clearAllMocks());

  it("affiche le bouton tout de suite, sans télécharger le panneau", async () => {
    const r = router();
    await r.push("/");
    const wrapper = mount(AssistantLauncher, { global: { plugins: [r] } });
    await flushPromises();
    expect(wrapper.find("[data-test=assistant-open]").exists()).toBe(true);
    expect(wrapper.find("[data-test=assistant-panel]").exists()).toBe(false);
    expect(panel.loaded).toBe(0);
  });

  it("charge le panneau au clic ; le bouton reste jusqu'à son arrivée", async () => {
    const r = router();
    await r.push("/");
    const wrapper = mount(AssistantLauncher, { global: { plugins: [r] } });
    await flushPromises();
    await wrapper.find("[data-test=assistant-open]").trigger("click");
    expect(useAssistant().open.value).toBe(true);
    await flushPromises();
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(wrapper.find("[data-test=assistant-panel]").exists()).toBe(true);
    expect(wrapper.find("[data-test=assistant-open]").exists()).toBe(false);
  });

  it("une question posée d'ailleurs (open) charge aussi le panneau", async () => {
    const r = router();
    await r.push("/");
    const wrapper = mount(AssistantLauncher, { global: { plugins: [r] } });
    await flushPromises();
    useAssistant().ask("Pas de CV à jour ?");
    await flushPromises();
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(wrapper.find("[data-test=assistant-panel]").exists()).toBe(true);
  });
});
