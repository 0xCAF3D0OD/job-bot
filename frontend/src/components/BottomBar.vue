<!-- La barre du bas du téléphone, la même partout (Kevin, 19.11.2026, d'après la barre de la planche Offre) : une
     seule ligne, 12 px 16 px plus la zone de sécurité du bas, fond de la page, trait de 1 px en haut. Une action
     principale pleine, qui prend le reste de la largeur ; au plus une secondaire à contour, à sa gauche (quel que soit
     l'ordre du code), large comme son texte ; 48 px de haut. Kevin a demandé 10 px entre elles : 8 px, la grille de 4
     (audit-grille), en attendant sa réponse. Les enfants portent `bottom-bar-primary` et `bottom-bar-secondary` ;
     `bottom-bar-note` est une ligne au-dessus (une erreur), sur toute la largeur. La page garde sous son contenu la
     hauteur de la barre. Sans script, pour le poids. Rendue seulement sur téléphone par l'appelant. -->

<template>
  <div
    class="bottom-bar"
    data-test="bottom-bar"
  >
    <slot />
  </div>
</template>

<style>
.bottom-bar {
  --bb-gap: var(--space-2); --bb-h: 48px; --bb-line: 1.5px;
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 21; box-sizing: border-box;
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--bb-gap);
  padding: var(--space-3) var(--space-4) calc(var(--space-3) + env(safe-area-inset-bottom));
  background: var(--bg); border-top: 1px solid var(--line);
}
html:root:has(.bottom-bar) main { padding-bottom: calc(var(--space-12) + var(--space-12) + env(safe-area-inset-bottom)); }
.bottom-bar > .bottom-bar-note { flex: 1 0 100%; margin: 0; }
.bottom-bar > :is(.bottom-bar-primary, .bottom-bar-secondary) {
  box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  min-height: var(--bb-h); margin: 0; border-radius: var(--radius-pill); font-weight: var(--weight-bold);
  line-height: var(--leading-tight); text-align: center; text-decoration: none;
}
.bottom-bar > .bottom-bar-secondary {
  flex: none; white-space: nowrap; order: -1; padding: 0 var(--space-5); border: var(--bb-line) solid var(--action);
  background: var(--surface); color: var(--primary-text); font-size: var(--font-label);
}
.bottom-bar > .bottom-bar-primary {
  flex: 1; min-width: 0; padding: 0 var(--space-4); border: 0; white-space: normal;
  background: var(--action); color: var(--on-action); font-size: var(--font-body);
}
.bottom-bar > .busy-button { display: inline-grid; justify-items: center; }
.bottom-bar > .bottom-bar-primary .icon { width: 1.125rem; height: 1.125rem; }
</style>
