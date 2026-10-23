import { flushPromises } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

// Chaque requête reste en route jusqu'à ce que le test lui donne sa réponse.
const pending = vi.hoisted(() => [] as ((value: unknown) => void)[]);
vi.mock("../api/client", () => ({
  api: { GET: () => new Promise((resolve) => pending.push(resolve)) },
}));

import { useNewsCount } from "./useNewsCount";

function answer(articles: number, videos: number): void {
  pending.shift()!({ data: { new_articles: articles, new_videos: videos } });
}

afterEach(() => {
  vi.useRealTimers();
});

describe("Le compteur des Actualités (docs/15 §2, 1.6.1)", () => {
  it("une réponse partie avant la visite ne ramène pas le compteur à zéro remis", async () => {
    vi.useFakeTimers();
    const { count, start, refresh, reset } = useNewsCount();
    // Au démarrage de l'application, la requête part…
    start();
    // … et l'on ouvre les Actualités avant qu'elle revienne.
    reset();
    answer(4, 2);
    await flushPromises();
    expect(count.value).toBe(0);
    // Une requête partie après la visite compte normalement.
    void refresh();
    answer(1, 0);
    await flushPromises();
    expect(count.value).toBe(1);
  });
});
