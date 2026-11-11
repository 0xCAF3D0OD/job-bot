<script lang="ts">
import { defineComponent, h, type PropType } from "vue";

import { markSegments } from "../offerPassages";

// Un texte de l'annonce dont les passages retrouvés dans le profil sont surlignés (lot du 11 novembre au soir,
// PR 45 et 47) : la même source que le tri (`passages`, vérifiés par le serveur). Le texte affiché ne change pas :
// rendu sans gabarit, pour n'ajouter ni espace ni retour à la ligne (l'annonce garde les siens).
export default defineComponent({
  name: "MarkedText",
  props: {
    text: { type: String, required: true },
    passages: { type: Array as PropType<string[]>, required: true },
  },
  setup(props) {
    return () => markSegments(props.text, props.passages).map((part) => (part.mark ? h("mark", { class: "passage-mark" }, part.text) : part.text));
  },
});
</script>

<style>
/* Le surlignage (§1 du lot) : #FFE9A8 en clair, #5C4A14 en sombre, rayon 4 px, 0 4 px, texte hérité. */
.passage-mark { --passage: #FFE9A8; padding: 0 var(--space-1); border-radius: var(--space-1); background: var(--passage); color: inherit; }
.passage-legend { --passage: #FFE9A8; --legend-w: 24px; --legend-h: 12px; --legend-13: 0.8125rem; display: flex; align-items: center; gap: var(--space-2); margin: var(--space-3) 0 var(--space-1); font-size: var(--legend-13); color: var(--text-tertiary); }
.passage-legend-mark { flex: none; width: var(--legend-w); height: var(--legend-h); border-radius: var(--space-1); background: var(--passage); }
:root[data-theme="dark"] :is(.passage-mark, .passage-legend) { --passage: #5C4A14; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) :is(.passage-mark, .passage-legend) { --passage: #5C4A14; } }
</style>
