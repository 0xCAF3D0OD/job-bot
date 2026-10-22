import pluginVue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";

// Les éléments en ligne que eslint-plugin-vue laisse déjà sur une ligne, plus le lien du routeur :
// un lien suivi d'un point s'écrit « <RouterLink …>texte</RouterLink>. », sans espace avant le
// point (docs/128).
const INLINE = ["a", "abbr", "audio", "b", "bdi", "bdo", "canvas", "cite", "code", "data", "del", "dfn", "em", "i", "iframe", "ins", "kbd", "label", "map", "mark", "noscript", "object", "output", "picture", "q", "ruby", "s", "samp", "small", "span", "strong", "sub", "sup", "svg", "time", "u", "var", "video"];
const IGNORED = ["pre", "textarea", ...INLINE, "RouterLink"];

export default tseslint.config(
  { ignores: ["dist/", "node_modules/", "src/api/schema.d.ts"] },
  ...tseslint.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  {
    files: ["**/*.vue"],
    languageOptions: { parserOptions: { parser: tseslint.parser } },
  },
  {
    rules: {
      "vue/multi-word-component-names": "off",
      "vue/singleline-html-element-content-newline": ["warn", { ignores: IGNORED }],
      "vue/multiline-html-element-content-newline": ["warn", { ignores: IGNORED }],
    },
  },
);
