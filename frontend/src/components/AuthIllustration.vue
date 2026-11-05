<script setup lang="ts">
import hello from "../assets/personnage/perso-02-bonjour-400.webp";
import hello2x from "../assets/personnage/perso-02-bonjour-800.webp";

// L'illustration de la connexion (maquettes Connexion et Connexion, ordinateur ; kit du 2026-11-05) : le
// personnage qui dit bonjour (kit HD : 400 px, 800 px pour les écrans 2×), le soleil, le nuage, la colline et le sol, aux couleurs du thème (--peach-soft,
// --primary-soft, --surface-muted). `large` : la moitié gauche de l'ordinateur (560 × 420) ; sinon le bandeau du
// téléphone (150 px). Personnage haut de 200 px au plus sur téléphone, 400 px sur ordinateur. Statique et décorative : aria-hidden, alt vide, un fondu de 200 ms coupé par « réduire les
// animations » (règles du kit).
withDefaults(defineProps<{ large?: boolean }>(), { large: false });
</script>

<template>
  <div
    class="auth-illustration"
    :class="{ 'auth-illustration-large': large }"
    aria-hidden="true"
    data-test="auth-illustration"
  >
    <svg
      class="auth-illustration-sun"
      viewBox="0 0 100 100"
    ><circle
      cx="50"
      cy="50"
      r="50"
    /></svg>
    <svg
      class="auth-illustration-cloud"
      viewBox="0 0 200 100"
    ><path d="M30 100 a30 30 0 0 1 10-58 a46 46 0 0 1 88-6 a34 34 0 0 1 48 34 a24 24 0 0 1 -6 30 Z" /></svg>
    <svg
      class="auth-illustration-hill"
      viewBox="0 0 300 90"
      preserveAspectRatio="none"
    ><path d="M0 90 C 40 20, 120 0, 170 10 C 220 20, 270 50, 300 90 Z" /></svg>
    <span class="auth-illustration-ground" />
    <img
      class="auth-illustration-person"
      :src="hello"
      :srcset="`${hello} 1x, ${hello2x} 2x`"
      alt=""
      width="150"
      height="400"
      decoding="async"
    >
  </div>
</template>

<style>
/* Valeurs de la maquette Connexion (390 px) et Connexion, ordinateur (560 × 420). */
.auth-illustration { position: relative; flex: none; width: 100%; height: 150px; overflow: hidden; }
.auth-illustration svg { position: absolute; display: block; }
.auth-illustration-sun { right: 46px; top: 9px; width: 82px; height: 82px; fill: var(--peach-soft); }
.auth-illustration-cloud { left: 23px; top: 18px; width: 101px; height: 50px; fill: var(--primary-soft); }
.auth-illustration-hill { left: -19px; bottom: 4px; width: 292px; height: 42px; fill: var(--primary-soft); }
.auth-illustration-ground { position: absolute; left: 23px; right: 23px; bottom: 0; height: 10px; border-radius: var(--radius-sm); background: var(--surface-muted); }
.auth-illustration-person { position: absolute; left: 50%; bottom: 4px; width: auto; height: 140px; max-width: none; max-height: 200px; transform: translateX(-50%); animation: auth-illustration-in 200ms ease-out both; }
.auth-illustration-large { width: 560px; max-width: 100%; height: 420px; }
.auth-illustration-large .auth-illustration-sun { right: 67px; top: 25px; width: 231px; height: 231px; }
.auth-illustration-large .auth-illustration-cloud { left: 33px; top: 50px; width: 145px; height: 72px; }
.auth-illustration-large .auth-illustration-hill { left: -28px; bottom: 12px; width: 420px; height: 117px; }
.auth-illustration-large .auth-illustration-ground { left: 33px; right: 33px; height: 16px; }
.auth-illustration-large .auth-illustration-person { bottom: 8px; height: 380px; max-height: 400px; }
@keyframes auth-illustration-in { from { opacity: 0; } to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .auth-illustration-person { animation: none; } }
</style>
