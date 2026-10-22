// Conditions d'utilisation (docs/125 §7) : publiques, avec l'exploitant.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { PUBLIC_ROUTES } from "../router";
import TermsView from "./TermsView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

describe("TermsView", () => {
  it("le service, les formules, le paiement, la résiliation, l'exploitant", async () => {
    GET.mockResolvedValue({ data: { contact: "Kevin Exemple, Lausanne, contact@joba1.ch", guest_mailbox: true, billing: true } });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    const wrapper = mount(TermsView, { global: { plugins: [router] } });
    await flushPromises();
    const text = wrapper.find("[data-test=terms]").text();
    expect(text).toContain("7 CHF par mois");
    expect(text).toContain("Tu résilies quand tu veux");
    expect(text).toContain("jobA1 ne voit jamais ta carte");
    expect(text).not.toContain("—");
    expect(wrapper.find("[data-test=terms-contact]").text()).toContain("contact@joba1.ch");
    expect(PUBLIC_ROUTES.has("terms")).toBe(true);
  });
});
