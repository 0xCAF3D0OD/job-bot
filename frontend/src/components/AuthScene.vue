<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

import video from "../assets/videos/connexion-soir.mp4";

// La scène de la connexion (docs/67, compléments 0.55.2 et 0.55.3) : la ville et le bureau. En
// clair, le jour. En sombre, la vidéo du jour qui tombe joue une fois, puis l'image du soir reste ;
// de même si le thème passe en sombre pendant qu'on est sur la page. « Réduire les animations » :
// l'image du soir directement. Les trois ont le même cadrage ; le ciel, uni, est prolongé par la
// couleur du fond, qui suit la vidéo. Ce qu'on pose dessus (la phrase de jobA1) suit aussi : foncé
// sur le ciel du jour, clair sur celui du soir.
const files = import.meta.glob<string>("../assets/illustrations/connexion*.webp", { query: "?url", import: "default", eager: true });
const srcset = (name: string) =>
  [480, 800, 1264].map((width) => `${files[`../assets/illustrations/${name}-${width}.webp`]} ${width}w`).join(", ");
const DAY = srcset("connexion");
const NIGHT = srcset("connexion-soir");
const SIZES = "(max-width: 820px) 160vw, 90vw";
// Au-delà, la vidéo est tenue pour finie (lecture bloquée, fichier lent).
const VIDEO_MAX_MS = 15_000;

const phase = ref<"day" | "dusk" | "night">("day");
const film = ref<HTMLVideoElement | null>(null);
let dark: MediaQueryList | null = null;
let still: MediaQueryList | null = null;
let fallback: ReturnType<typeof setTimeout> | undefined;

function night(): void {
  clearTimeout(fallback);
  phase.value = "night";
}

async function dusk(): Promise<void> {
  if (still?.matches) return night();
  phase.value = "dusk";
  fallback = setTimeout(night, VIDEO_MAX_MS);
  const el = film.value;
  if (!el) return night();
  try {
    el.currentTime = 0;
    await el.play();
  } catch {
    night();
  }
}

function follow(): void {
  if (dark?.matches) {
    if (phase.value === "day") void dusk();
  } else {
    clearTimeout(fallback);
    film.value?.pause();
    phase.value = "day";
  }
}

onMounted(() => {
  if (typeof window.matchMedia !== "function") return;
  dark = window.matchMedia("(prefers-color-scheme: dark)");
  still = window.matchMedia("(prefers-reduced-motion: reduce)");
  dark.addEventListener("change", follow);
  follow();
});
onBeforeUnmount(() => {
  clearTimeout(fallback);
  dark?.removeEventListener("change", follow);
});
</script>

<template>
  <div
    :class="['auth-scene', phase]"
    :data-phase="phase"
    aria-hidden="true"
  >
    <img
      class="auth-scene-media day-image"
      :srcset="DAY"
      :sizes="SIZES"
      alt=""
      decoding="async"
    >
    <img
      v-if="phase !== 'day'"
      class="auth-scene-media night-image"
      :srcset="NIGHT"
      :sizes="SIZES"
      alt=""
      decoding="async"
    >
    <video
      ref="film"
      class="auth-scene-media film"
      :src="video"
      muted
      playsinline
      preload="none"
      disablepictureinpicture
      @ended="night"
    />
    <slot />
  </div>
</template>
