<script setup lang="ts">
// Icônes au trait, dessinées pour jobA1 (style de la maquette, aucun fichier repris).
// Pictogrammes des bulles d'Aujourd'hui (docs/54) : inbox, send, refresh, file, trend, book, news ;
// du Bilan (docs/55) : reply, clock, star.
defineProps<{
  name:
    | "pin"
    | "rate"
    | "globe"
    | "check"
    | "chevron"
    | "calendar"
    | "eye"
    | "bell"
    | "user"
    | "search"
    | "inbox"
    | "send"
    | "refresh"
    | "file"
    | "trend"
    | "book"
    | "news"
    | "reply"
    | "clock"
    | "star";
}>();
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
    <template v-if="name === 'search'">
      <circle
        cx="11"
        cy="11"
        r="6.5"
      />
      <path d="M16 16l4.5 4.5" />
    </template>
    <template v-else-if="name === 'pin'">
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
    <template v-else-if="name === 'user'">
      <circle
        cx="12"
        cy="8"
        r="4"
      />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </template>
    <template v-else-if="name === 'bell'">
      <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15L6 16z" />
      <path d="M10 20a2 2 0 0 0 4 0" />
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
    <template v-else-if="name === 'inbox'">
      <path d="M4 13l2.5-7h11L20 13v6H4z" />
      <path d="M4 13h4.5l1 2h5l1-2H20" />
    </template>
    <template v-else-if="name === 'send'">
      <path d="M20 4L3.5 11l6.5 2.5L12.5 20z" />
      <path d="M20 4l-10 9.5" />
    </template>
    <template v-else-if="name === 'refresh'">
      <path d="M19 12a7 7 0 1 1-2.1-5" />
      <path d="M19 4.5V9h-4.5" />
    </template>
    <template v-else-if="name === 'file'">
      <path d="M7 3h7l4 4v14H7z" />
      <path d="M14 3v4h4M10 12h5M10 16h5" />
    </template>
    <template v-else-if="name === 'trend'">
      <path d="M7 17L17 7M9 7h8v8" />
    </template>
    <template v-else-if="name === 'book'">
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z" />
      <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3H6.5" />
    </template>
    <template v-else-if="name === 'reply'">
      <path d="M4 5h16v11H9l-5 4z" />
      <path d="M8 9.5h8M8 12.5h5" />
    </template>
    <template v-else-if="name === 'clock'">
      <circle
        cx="12"
        cy="12"
        r="8.5"
      />
      <path d="M12 7.5V12l3 2" />
    </template>
    <template v-else-if="name === 'star'">
      <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z" />
    </template>
    <template v-else-if="name === 'news'">
      <rect
        x="3.5"
        y="5"
        width="17"
        height="14"
        rx="2"
      />
      <path d="M7 9h6M7 12.5h10M7 16h10" />
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
