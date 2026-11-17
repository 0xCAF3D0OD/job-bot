<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

// Le cercle à cocher d'une tâche faite hors de l'app (LISEZMOI du 17.11, §58 et §61 ; planches Orp, AccueilV2,
// AujourdhuiOrdinateurV2, + Sombre) : un rond de 26 px au bord de 2 px, orange pour une tâche en retard (#B4631F,
// sombre #F2B98E), gris sinon (#8C8478) ; coché, il devient vert avec une coche, avec un petit rebond. La zone de
// toucher fait 44 px (role="checkbox"). Une tâche finie n'est jamais barrée : c'est la ligne qui dit « Remis le … ».
withDefaults(defineProps<{ checked: boolean; label: string; tone?: "late" | "idle"; busy?: boolean }>(), { tone: "idle", busy: false });
const emit = defineEmits<{ toggle: [checked: boolean] }>();
</script>

<template>
  <button
    type="button"
    role="checkbox"
    :class="['task-check', tone]"
    :aria-checked="checked"
    :aria-label="label"
    :aria-disabled="busy || undefined"
    @click="busy || emit('toggle', !checked)"
  >
    <span
      v-if="checked"
      class="task-check-done"
    ><AppIcon name="done" /></span>
    <span
      v-else
      class="task-check-ring"
    />
  </button>
</template>

<style>
.task-check {
  --task-ring: #8C8478; --task-size: 26px;
  flex: none; display: grid; place-items: center; width: var(--target-min); height: var(--target-min); min-height: var(--target-min);
  padding: 0; border: 0; border-radius: var(--radius-pill); background: none; box-shadow: none; cursor: pointer;
}
.task-check.late { --task-ring: #B4631F; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .task-check.late { --task-ring: var(--peach-text); } }
:root[data-theme="dark"] .task-check.late { --task-ring: var(--peach-text); }
.task-check:hover:not(:disabled) { background: none; box-shadow: none; }
.task-check-ring { box-sizing: border-box; width: var(--task-size); height: var(--task-size); border: 2px solid var(--task-ring); border-radius: var(--radius-pill); }
.task-check-done { display: grid; place-items: center; width: var(--task-size); height: var(--task-size); border-radius: var(--radius-pill); background: var(--success); color: var(--on-action); animation: task-pop 0.4s linear(0, 0.36 8%, 0.75 18%, 1.02 28%, 1.1 36%, 1.08 44%, 1.02 56%, 0.99 68%, 1) both; }
/* La coche de la planche : 15 px, trait 3,2. */
.task-check-done > .icon { --task-tick: 15px; width: var(--task-tick); height: var(--task-tick); stroke-width: 3.2; }
@keyframes task-pop { from { transform: scale(0.6); } to { transform: none; } }
@media (prefers-reduced-motion: reduce) { .task-check-done { animation: none; } }
</style>
