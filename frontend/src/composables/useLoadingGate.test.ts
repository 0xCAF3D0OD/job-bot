import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, nextTick, ref } from "vue";

import { useLoadingGate } from "./useLoadingGate";

function host(data: ReturnType<typeof ref<string | null>>) {
  let gate!: ReturnType<typeof useLoadingGate>;
  mount(
    defineComponent({
      setup() {
        gate = useLoadingGate(() => !!data.value);
        return () => null;
      },
    }),
  );
  return gate;
}

describe("useLoadingGate (docs/58 §3.2)", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("rapide : aucune illustration ni attente", async () => {
    const data = ref<string | null>(null);
    const gate = host(data);
    vi.advanceTimersByTime(200);
    data.value = "ok";
    await nextTick();
    expect(gate.ready.value).toBe(true);
    expect(gate.illustrated.value).toBe(false);
  });

  it("lent : l'illustration après 0,4 s, gardée au moins 0,6 s", async () => {
    const data = ref<string | null>(null);
    const gate = host(data);
    vi.advanceTimersByTime(400);
    expect(gate.illustrated.value).toBe(true);
    vi.advanceTimersByTime(100);
    data.value = "ok";
    await nextTick();
    expect(gate.ready.value).toBe(false);
    vi.advanceTimersByTime(500);
    expect(gate.ready.value).toBe(true);
    expect(gate.illustrated.value).toBe(false);
  });
});
