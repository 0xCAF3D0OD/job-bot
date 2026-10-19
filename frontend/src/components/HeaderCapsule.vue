<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { CAPSULE, type CapsuleZone } from "../composables/useCapsule";
import { usePhone } from "../composables/usePhone";

// La capsule qui se déroule (docs/91, d'après le menu de Sphere) : la cloche, l'initiale et ☰
// sont des zones séparées par des filets ; ouvrir l'une agrandit le cadre vers le bas, et son
// contenu apparaît dedans (rendu dans #capsule-body). La rangée du haut ne bouge pas. Sur
// téléphone, la cloche garde sa carte qui pousse la page (retour du 2026-10-15).
const WIDTHS: Record<CapsuleZone, number> = { account: 240, bell: 384, progress: 416, menu: 240 };
const GUTTER = 32;

const route = useRoute();
const { phone } = usePhone();
const active = ref<CapsuleZone | null>(null);
provide(CAPSULE, { active });

const root = ref<HTMLElement | null>(null);
const row = ref<HTMLElement | null>(null);
const body = ref<HTMLElement | null>(null);
const closed = ref({ width: 0, height: 0 });
const size = ref<{ width: number; height: number } | null>(null);
// La cloche sur téléphone s'ouvre sous la barre : la capsule reste fermée.
const unrolled = computed(() => active.value !== null && !(phone.value && active.value === "bell"));

function measureClosed(): void {
  if (!row.value) return;
  closed.value = { width: row.value.scrollWidth + 2, height: row.value.offsetHeight + 2 };
}

function measureOpen(): void {
  if (!unrolled.value || !row.value || !body.value || !active.value) {
    size.value = null;
    return;
  }
  const room = window.innerWidth - GUTTER;
  const width = phone.value ? room : Math.min(WIDTHS[active.value], room);
  size.value = { width: Math.max(width, closed.value.width), height: row.value.offsetHeight + body.value.scrollHeight + 2 };
}

const style = computed(() => {
  const current = size.value ?? closed.value;
  return current.width ? { width: `${current.width}px`, height: `${current.height}px` } : {};
});

function zoneButton(zone: CapsuleZone): HTMLElement | null {
  return root.value?.querySelector<HTMLElement>(`[data-capsule-zone="${zone}"]`) ?? null;
}

function close(focus: boolean): void {
  const was = active.value;
  active.value = null;
  if (focus && was) zoneButton(was)?.focus();
}

function onDocumentClick(event: MouseEvent): void {
  const target = event.target as Node;
  if (!active.value || root.value?.contains(target)) return;
  if (document.getElementById("bell-drop")?.contains(target)) return;
  close(false);
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && active.value) close(true);
}

watch(active, async () => {
  await nextTick();
  requestAnimationFrame(measureOpen);
});
// Une page choisie referme la capsule.
watch(
  () => route.fullPath,
  () => close(false),
);

let observer: ResizeObserver | undefined;
function onResize(): void {
  measureClosed();
  measureOpen();
}

onMounted(() => {
  measureClosed();
  document.addEventListener("click", onDocumentClick);
  document.addEventListener("keydown", onKeydown);
  window.addEventListener("resize", onResize);
  // Le contenu arrive parfois après l'ouverture (les alertes relues) : la hauteur suit.
  if (typeof ResizeObserver !== "undefined") {
    observer = new ResizeObserver(onResize);
    if (row.value) observer.observe(row.value);
    if (body.value) observer.observe(body.value);
  }
});
onUnmounted(() => {
  document.removeEventListener("click", onDocumentClick);
  document.removeEventListener("keydown", onKeydown);
  window.removeEventListener("resize", onResize);
  observer?.disconnect();
});
</script>

<template>
  <div
    class="capsule-slot"
    :style="closed.width ? { width: `${closed.width}px`, height: `${closed.height}px` } : undefined"
  >
    <div
      ref="root"
      :class="['capsule', { open: unrolled }]"
      :style="style"
      data-test="capsule"
    >
      <div
        ref="row"
        class="capsule-row"
      >
        <slot />
      </div>
      <div
        id="capsule-body"
        ref="body"
        class="capsule-body"
        data-test="capsule-body"
      />
    </div>
  </div>
</template>
