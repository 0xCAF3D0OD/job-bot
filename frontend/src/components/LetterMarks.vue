<script lang="ts">
import { defineComponent, h, type PropType } from "vue";

import { letterSegments } from "../offerPassages";
// La légende (`.passage-legend`) a ses styles avec le surlignage de l'annonce.
import "./MarkedText.vue";

// Le surlignage d'un paragraphe de la lettre (lot du 11 novembre au soir, PR 51 ; maquettes MaCandidatureV2 et
// PreparerOrdinateur) : un calque posé sur la zone de saisie, même texte, mêmes marges, même police, texte
// transparent. Seuls les passages repris de l'annonce ont un fond. Le paragraphe reste modifiable dessous : le calque
// ne reçoit ni clic ni focus, et il est caché aux lecteurs d'écran (la légende au-dessus de la feuille dit le compte).
// C'est un affichage : il n'existe ni dans le PDF, ni dans l'e-mail, ni à l'impression (`screen-only`).
export default defineComponent({
  name: "LetterMarks",
  props: {
    text: { type: String, required: true },
    terms: { type: Array as PropType<string[]>, required: true },
  },
  setup(props) {
    return () =>
      h(
        "div",
        { class: "letter-marks screen-only", "aria-hidden": "true" },
        letterSegments(props.text, props.terms).map((part) => (part.mark ? h("mark", part.text) : part.text)),
      );
  },
});
</script>

<style>
/* Sur la feuille blanche, le surlignage garde #FFE9A8 même en sombre (§1 du lot). Rayon 4 px ; les 4 px de chaque
   côté sont une ombre, pas une marge, pour que le texte du calque se coupe aux mêmes endroits que la saisie.
   `multiply` : le texte noir de la saisie reste lisible sous le fond jaune. */
.letter-paragraph { position: relative; }
.letter-marks { position: absolute; inset: 0 0 auto; box-sizing: border-box; padding: 0.15rem 0.25rem; border: 1px solid transparent; font: inherit; white-space: pre-wrap; overflow-wrap: break-word; text-align: left; color: transparent; pointer-events: none; user-select: none; mix-blend-mode: multiply; }
.letter-marks mark { --letter-mark: #FFE9A8; padding: 0; border-radius: 4px; background: var(--letter-mark); box-shadow: -4px 0 0 var(--letter-mark), 4px 0 0 var(--letter-mark); color: transparent; }
/* La légende au-dessus de la feuille : pastille 24 × 12, « Repris de l’annonce : {k} points » en 13 px. */
.passage-legend.letter-legend { margin: 0 0 var(--space-2); color: var(--text-lead); }
.prep-desk .doc-card > .passage-legend.letter-legend { margin-top: var(--space-4); margin-bottom: 0; line-height: var(--space-4); }
.prep-desk .doc-card > .letter-legend + .letter-sheet { margin-top: var(--space-4); }
</style>
