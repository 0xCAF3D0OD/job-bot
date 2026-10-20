import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import SignupView from "./SignupView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

async function mountSignup(open = true) {
  GET.mockResolvedValue({ data: { open } });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/inscription", component: SignupView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/inscription");
  const wrapper = mount(SignupView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

async function fill(wrapper: Awaited<ReturnType<typeof mountSignup>>, values: { username?: string; password?: string; again?: string; consent?: boolean; note?: string } = {}) {
  const all = { username: "camille", password: "un-mot-de-passe-solide", again: "un-mot-de-passe-solide", consent: true, ...values };
  await wrapper.find("[data-test=signup-username]").setValue(all.username);
  await wrapper.find("[data-test=signup-password]").setValue(all.password);
  await wrapper.find("[data-test=signup-again]").setValue(all.again);
  await wrapper.find("[data-test=signup-consent]").setValue(all.consent);
  if (values.note !== undefined) await wrapper.find("[data-test=signup-note]").setValue(values.note);
}

describe("demander un compte (docs/102)", () => {
  it("vérifie avant d'envoyer : chaque envoi compte dans la limite", async () => {
    const wrapper = await mountSignup();
    const form = wrapper.find("[data-test=signup-form]");
    await fill(wrapper, { username: "  " });
    await form.trigger("submit");
    expect(wrapper.find("[data-test=signup-error]").text()).toContain("identifiant");
    await fill(wrapper, { password: "court", again: "court" });
    await form.trigger("submit");
    expect(wrapper.find("[data-test=signup-error]").text()).toContain("12 caractères");
    await fill(wrapper, { again: "un-mot-de-passe-autre" });
    await form.trigger("submit");
    expect(wrapper.find("[data-test=signup-error]").text()).toContain("diffèrent");
    await fill(wrapper, { consent: false });
    await form.trigger("submit");
    expect(wrapper.find("[data-test=signup-error]").text()).toContain("Coche la case");
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=signup-note]").attributes("maxlength")).toBe("300");
    expect(wrapper.find("[data-test=signup-username]").attributes("maxlength")).toBe("40");
  });

  it("la demande envoyée : le message, et le lien vers la connexion", async () => {
    POST.mockResolvedValue({ response: { ok: true, status: 204 } });
    const wrapper = await mountSignup();
    await fill(wrapper, { username: " camille ", note: "Amie de Kevin, à Lausanne." });
    await wrapper.find("[data-test=signup-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/auth/signup", {
      body: {
        username: "camille",
        password: "un-mot-de-passe-solide",
        note: "Amie de Kevin, à Lausanne.",
        consent: true,
        website: null,
      },
    });
    const sent = wrapper.find("[data-test=signup-sent]");
    expect(sent.text()).toContain("Ta demande est envoyée. Tu pourras te connecter dès que l'exploitant l'aura acceptée.");
    expect(sent.find("a").attributes("href")).toBe("/connexion");
    expect(wrapper.find("[data-test=signup-form]").exists()).toBe(false);
  });

  it("l'erreur du serveur, comme sur la page d'invitation", async () => {
    POST.mockResolvedValue({ response: { ok: false, status: 422 }, error: { detail: "cet identifiant est déjà pris" } });
    const wrapper = await mountSignup();
    await fill(wrapper);
    await wrapper.find("[data-test=signup-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=signup-error]").text()).toBe("Cet identifiant est déjà pris.");
    POST.mockResolvedValue({ response: { ok: false, status: 422 }, error: { detail: [{ msg: "too long" }] } });
    await wrapper.find("[data-test=signup-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=signup-error]").text()).toBe("Demande refusée : vérifie les champs.");
  });

  it("demandes fermées : le dit, sans formulaire", async () => {
    const wrapper = await mountSignup(false);
    expect(wrapper.find("[data-test=signup-closed]").text()).toContain("Les demandes de compte sont fermées pour le moment.");
    expect(wrapper.find("[data-test=signup-closed] a").attributes("href")).toBe("/connexion");
    expect(wrapper.find("[data-test=signup-form]").exists()).toBe(false);
  });

  it("fermées entre-temps : la réponse 403 montre la même page", async () => {
    POST.mockResolvedValue({ response: { ok: false, status: 403 }, error: { detail: "les demandes de compte sont fermées pour le moment" } });
    const wrapper = await mountSignup();
    await fill(wrapper);
    await wrapper.find("[data-test=signup-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=signup-closed]").exists()).toBe(true);
  });

  it("le champ piège : présent, hors de portée des lecteurs d'écran et du clavier", async () => {
    const wrapper = await mountSignup();
    const trap = wrapper.find("[data-test=signup-trap]");
    expect(trap.attributes("aria-hidden")).toBe("true");
    expect(trap.classes()).toContain("signup-trap");
    const input = wrapper.find("[data-test=signup-website]");
    expect(input.attributes("name")).toBe("website");
    expect(input.attributes("tabindex")).toBe("-1");
    expect(input.attributes("autocomplete")).toBe("off");
    expect(input.attributes("style") ?? "").not.toContain("display: none");
  });

  it("le lien vers « Tes données » à côté de la case", async () => {
    const wrapper = await mountSignup();
    const consent = wrapper.find(".signup-consent");
    expect(consent.text()).toContain("J'ai lu ce que deviennent mes données");
    expect(consent.find("a").attributes("href")).toBe("/tes-donnees");
  });
});
