<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { CAPSULE, type CapsuleZone } from "../composables/useCapsule";
import { usePhone } from "../composables/usePhone";

// La capsule qui se déroule (docs/91, d'après le menu de Sphere) : la cloche, le livre et
// l'initiale sont des zones séparées par des filets ; leur contenu est rendu dans #capsule-body.
// Comme Sphere (docs/109) : sur ordinateur, la capsule a la même largeur fermée et ouverte
// (20 rem) et ne fait que descendre ; sur téléphone, elle ne bouge pas, et ce qu'on ouvre prend
// tout l'écran sous l'en-tête, la page derrière immobile et la barre d'onglets cachée.
const DESKTOP_REM = 20;
const SHEET_CLASS = "capsule-sheet";

const route = useRoute();
const { phone } = usePhone();
const active = ref<CapsuleZone | null>(null);
provide(CAPSULE, { active });

const root = ref<HTMLElement | null>(null);
const row = ref<HTMLElement | null>(null);
const body = ref<HTMLElement | null>(null);
const closed = ref({ width: 0, height: 0 });
const size = ref<{ width: number; height: number } | null>(null);
const unrolled = computed(() => active.value !== null);
// Téléphone : le haut de l'écran plein, juste sous la capsule.
const sheetTop = ref(0);

function rem(): number {
  return parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
}

function measureClosed(): void {
  if (!row.value) return;
  const natural = row.value.scrollWidth + 2;
  const width = phone.value ? natural : Math.max(natural, DESKTOP_REM * rem());
  closed.value = { width, height: row.value.offsetHeight + 2 };
}

function measureOpen(): void {
  if (!unrolled.value || !row.value || !body.value || !active.value) {
    size.value = null;
    return;
  }
  if (phone.value) {
    size.value = null;
    sheetTop.value = Math.round((root.value?.getBoundingClientRect().bottom ?? 0) + 0.75 * rem());
    return;
  }
  size.value = { width: closed.value.width, height: row.value.offsetHeight + body.value.scrollHeight + 2 };
}

// La page derrière l'écran plein ne défile pas, la barre d'onglets se cache (docs/109).
watch([unrolled, phone], ([isOpen, isPhone]) => {
  document.documentElement.classList.toggle(SHEET_CLASS, isOpen && isPhone);
});

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
  document.documentElement.classList.remove(SHEET_CLASS);
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
      :class="['capsule', { open: unrolled, sheet: unrolled && phone }]"
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
        :style="unrolled && phone ? { top: `${sheetTop}px` } : undefined"
        data-test="capsule-body"
      />
    </div>
  </div>
</template>
