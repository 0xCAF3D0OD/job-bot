<script setup lang="ts">
// Icônes au trait, dessinées pour job-bot (style de la maquette, aucun fichier repris).
defineProps<{ name: "pin" | "rate" | "globe" | "check" | "chevron" | "calendar" | "eye" }>();
</script>

<template>
  <svg
    class="icon"
    viewBox="0 0 24 24"
    width="16"
    height="16"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'pin'">
      <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" />
      <circle
        cx="12"
        cy="9.5"
        r="2.5"
      />
    </template>
    <template v-else-if="name === 'rate'">
      <circle
        cx="12"
        cy="12"
        r="9"
      />
      <path d="M9 15l6-6M9.5 9.5h.01M14.5 14.5h.01" />
    </template>
    <template v-else-if="name === 'globe'">
      <circle
        cx="12"
        cy="12"
        r="9"
      />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </template>
    <template v-else-if="name === 'check'">
      <circle
        cx="12"
        cy="12"
        r="9"
        fill="currentColor"
        stroke="none"
      />
      <path
        d="M8 12.5l2.5 2.5L16 9.5"
        stroke="#fff"
      />
    </template>
    <template v-else-if="name === 'chevron'">
      <path d="M9 6l6 6-6 6" />
    </template>
    <template v-else-if="name === 'calendar'">
      <rect
        x="4"
        y="5"
        width="16"
        height="15"
        rx="2"
      />
      <path d="M8 3v4M16 3v4M4 10h16" />
    </template>
    <template v-else>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
      <circle
        cx="12"
        cy="12"
        r="3"
      />
    </template>
  </svg>
</template>
