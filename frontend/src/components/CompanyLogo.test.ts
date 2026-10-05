import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { Offer } from "../api/client";
import CompanyLogo from "./CompanyLogo.vue";

const offer = (extra: Partial<Offer> = {}) => ({ id: 3, title: "DevOps", company: "acme SA", ...extra }) as Offer;

describe("CompanyLogo", () => {
  it("affiche le logo servi par la plateforme, sinon la lettre", async () => {
    const withLogo = mount(CompanyLogo, { props: { offer: offer({ has_logo: true }) } });
    expect(withLogo.find("img").attributes("src")).toBe("/api/offers/3/logo");

    await withLogo.find("img").trigger("error");
    expect(withLogo.find("img").exists()).toBe(false);
    expect(withLogo.text()).toBe("A");

    const letter = mount(CompanyLogo, { props: { offer: offer({ has_logo: false }) } });
    expect(letter.text()).toBe("A");
  });
});
