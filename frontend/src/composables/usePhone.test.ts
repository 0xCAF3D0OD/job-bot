import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { defineComponent, h } from "vue";

import { PHONE_QUERY, usePhone } from "./usePhone";

const original = globalThis.matchMedia;
afterEach(() => {
  globalThis.matchMedia = original;
});

describe("usePhone (docs/33)", () => {
  it("sait dès le premier rendu qu'on est sur téléphone", () => {
    globalThis.matchMedia = ((query: string) =>
      ({ matches: query === PHONE_QUERY, addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList);
    const seen: boolean[] = [];
    const Probe = defineComponent(() => {
      const { phone } = usePhone();
      seen.push(phone.value);
      return () => h("span", String(phone.value));
    });
    const wrapper = mount(Probe);
    expect(seen[0]).toBe(true);
    wrapper.unmount();
  });
});
