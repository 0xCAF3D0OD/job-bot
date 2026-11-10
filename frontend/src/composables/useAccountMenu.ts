import { ref } from "vue";

// Une demande d'ouverture du panneau « Mon compte » (prompt du 10 novembre, PR 20) : sur ordinateur, un lien vers
// /compte ouvre ce panneau au lieu d'une page. Le routeur la pose ; AccountMenu l'exécute dès qu'il est là (même s'il
// est monté après, à l'arrivée directe sur /compte) et la retire.
export const accountMenuRequest = ref(false);
