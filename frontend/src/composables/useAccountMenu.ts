import { ref } from "vue";

// Une demande d'ouverture du panneau « Mon compte » (prompt du 10 novembre, PR 20) : sur ordinateur, un lien vers
// /compte ouvre ce panneau au lieu d'une page. Le compteur change à chaque demande ; AccountMenu le suit.
export const accountMenuRequest = ref(0);
