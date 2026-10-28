<script setup lang="ts">
// Un bouton dont l'action prend du temps (planche « vide et chargement ») : pendant l'action, le nom
// suivi de « … » (`busyLabel`), aria-disabled et non disabled pour que le focus reste dessus
// (WCAG 2.4.3), l'état annoncé (WCAG 4.1.3). Les deux libellés occupent la même case : le bouton
// garde la largeur du plus long, il ne bouge pas.
defineOptions({ inheritAttrs: false });
const props = withDefaults(defineProps<{ busy: boolean; busyLabel: string; type?: "button" | "submit" }>(), {
  type: "button",
});
const emit = defineEmits<{ click: [event: MouseEvent] }>();

function onClick(event: MouseEvent): void {
  if (props.busy) {
    event.preventDefault();
    return;
  }
  emit("click", event);
}
</script>

<template>
  <button
    v-bind="$attrs"
    :type="type"
    :class="['busy-button', { busy }]"
    :aria-disabled="busy ? 'true' : undefined"
    @click="onClick"
  >
    <span
      class="busy-label"
      :aria-hidden="busy ? 'true' : undefined"
    ><slot /></span>
    <span
      class="busy-label busy-label-on"
      :aria-hidden="busy ? undefined : 'true'"
    >{{ busyLabel }}</span>
  </button>
  <span
    class="visually-hidden"
    role="status"
  >{{ busy ? busyLabel : "" }}</span>
</template>
