<script setup lang="ts">
import { defineAsyncComponent, nextTick, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { isActive, lang } from "../lang";
import { LANGUAGES, type Lang } from "../languages";
import AppIcon from "./AppIcon.vue";
import SidePanel from "./SidePanel.vue";

// La feuille n'est chargée que sur téléphone : Réglages sur ordinateur ne la télécharge pas.
const BottomSheet = defineAsyncComponent(() => import("./BottomSheet.vue"));

// « Langue de jobA1 » (LISEZMOI §62 du 17.11, planches ReglagesLangue et ReglagesLangueSombre ; docs/147) : les sept
// langues dans un ordre fixe, chaque nom écrit dans sa langue (attribut lang, WCAG 3.1.2) et le nom en français dessous
// (« Langue actuelle » pour la langue choisie). Une langue pas encore relue reste visible, grisée, « Bientôt »,
// aria-disabled et sans effet. Ligne de 56 px, bouton radio à l'encre comme « M'avertir dès » (§56). En bas, la langue
// des lettres, qui est un autre réglage (Préparer). Sur téléphone, la feuille en îlot (§45) se ferme dès le choix ; sur
// ordinateur, le panneau de droite reste ouvert (comme ChoicePanel).
const props = defineProps<{ open: boolean; sheet?: boolean }>();
const emit = defineEmits<{ close: [] }>();
const route = useRoute();
const group = ref<HTMLElement | null>(null);
const TITLE = "Langue de jobA1";

async function pick(code: Lang): Promise<void> {
  if (!isActive(code)) return;
  if (code !== lang.value) {
    // Les traductions ne se téléchargent qu'au changement de langue.
    const { setLang } = await import("../i18n");
    await setLang(code, route?.name ? [String(route.name)] : []);
  }
  if (props.sheet) emit("close");
}

function radios(): HTMLElement[] {
  return [...(group.value?.querySelectorAll<HTMLElement>("[role=radio]") ?? [])];
}

// Les flèches parcourent les sept lignes (une langue grisée reste lisible au clavier), Entrée ou Espace choisissent.
function onKeydown(event: KeyboardEvent): void {
  if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const list = radios();
  const at = list.indexOf(document.activeElement as HTMLElement);
  const forward = event.key === "ArrowDown" || event.key === "ArrowRight";
  const next = event.key === "Home" ? 0 : event.key === "End" ? list.length - 1 : forward ? at + 1 : at - 1;
  list[(next + list.length) % list.length]?.focus();
}

// À l'ouverture, le focus va sur la langue choisie.
watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    await nextTick();
    radios().find((radio) => radio.getAttribute("aria-checked") === "true")?.focus();
  },
);
</script>

<template>
  <component
    :is="sheet ? BottomSheet : SidePanel"
    :open="open"
    :title="TITLE"
    @close="emit('close')"
  >
    <div
      class="language-panel"
      data-test="language-panel"
    >
      <div
        ref="group"
        role="radiogroup"
        :aria-label="TITLE"
        @keydown="onKeydown"
      >
        <button
          v-for="language in LANGUAGES"
          :key="language.code"
          type="button"
          role="radio"
          :class="['language-row', { off: !isActive(language.code) }]"
          :aria-checked="lang === language.code"
          :aria-disabled="isActive(language.code) ? undefined : 'true'"
          :tabindex="lang === language.code ? 0 : -1"
          :data-test="`language-${language.code}`"
          @click="pick(language.code)"
        >
          <span
            class="language-dot"
            aria-hidden="true"
          />
          <span class="language-text">
            <span
              class="language-name"
              :lang="language.code"
            >{{ language.name }}</span>
            <span class="language-hint">{{ lang === language.code ? "Langue actuelle" : language.french }}</span>
          </span>
          <span
            v-if="!isActive(language.code)"
            class="language-soon"
          >Bientôt</span>
        </button>
      </div>
      <p class="language-note">
        <AppIcon name="info" />
        <span><b>Les lettres ont leur propre langue</b>Tu la choisis dans Préparer, pour chaque candidature.</span>
      </p>
    </div>
  </component>
</template>

<style>
/* Planche ReglagesLangue (§62) : lignes de 56 px séparées d'un trait --surface-muted (#ECE9E1, sombre #2C2722) ; rond de
   22 px, trait 2 px --button-outline, à l'encre (--text) avec un point de 10 px quand il est choisi ; nom 16/600, 700
   s'il est choisi ; nom en français 13 px gris. Langue pas encore relue : nom et rond grisés (#8C8478 et #DDD8CC,
   sombre #8C8478 et #38322B), pastille « Bientôt » 12/700 sur --surface-muted. Encadré : fond --bg, rayon 14, 14/20. */
.language-panel { --lp-dot: 22px; --lp-in: 10px; --lp-2: 2px; --lp-10: 10px; --lp-12: 12px; --lp-13: 13px; --lp-14: 14px; --lp-18: 18px; --lp-20: 20px; --lp-off: #8C8478; --lp-off-dot: #DDD8CC; display: grid; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .language-panel { --lp-off-dot: #38322B; } }
:root[data-theme="dark"] .language-panel { --lp-off-dot: #38322B; }
.language-row { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: 56px; padding: 0; border: 0; border-top: 1px solid var(--surface-muted); background: transparent; font: inherit; text-align: left; color: var(--text); cursor: pointer; }
.language-row.off { cursor: default; }
.language-dot { flex: none; display: grid; place-items: center; box-sizing: border-box; width: var(--lp-dot); height: var(--lp-dot); border: 2px solid var(--button-outline); border-radius: 50%; }
.language-row.off .language-dot { border-color: var(--lp-off-dot); }
.language-row[aria-checked="true"] .language-dot { border-color: var(--text); }
.language-row[aria-checked="true"] .language-dot::after { content: ""; width: var(--lp-in); height: var(--lp-in); border-radius: 50%; background: var(--text); }
.language-text { display: grid; flex: 1; min-width: 0; }
.language-name { font-size: var(--font-body); font-weight: var(--weight-semibold); }
.language-row[aria-checked="true"] .language-name { font-weight: var(--weight-bold); }
.language-row.off .language-name { color: var(--lp-off); }
.language-hint { font-size: var(--lp-13); color: var(--text-secondary); }
.language-soon { flex: none; padding: var(--lp-2) var(--space-2); border-radius: var(--radius-pill); background: var(--surface-muted); color: var(--text-secondary); font-size: var(--lp-12); line-height: var(--lp-18); font-weight: var(--weight-bold); }
.language-note { display: flex; gap: var(--lp-10); margin: var(--space-3) 0 0; padding: var(--space-3) var(--lp-14); border-radius: var(--lp-14); background: var(--bg); font-size: var(--lp-14); line-height: var(--lp-20); color: var(--text-lead); }
.language-note .icon { flex: none; width: 18px; height: 18px; margin-top: 1px; color: var(--text-secondary); }
.language-note b { display: block; color: var(--text); }
</style>
