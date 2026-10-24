// Aucun fichier de test ne passe en silence : sur une suite complète (`npm test`, `make test`),
// le nombre de fichiers lancés doit égaler le nombre de fichiers `*.test.ts` de `src/`, et la
// moindre erreur hors d'un test fait échouer la suite. Sous charge, un processus de vitest peut
// ne pas démarrer : ses fichiers disparaissaient du total sans faire échouer la suite.
import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import type { Reporter, TestModule } from "vitest/node";

function testFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return testFiles(path);
    return /\.test\.ts$/.test(name) ? [path] : [];
  });
}

export default class TotalReporter implements Reporter {
  onTestRunEnd(testModules: ReadonlyArray<TestModule>, unhandledErrors: ReadonlyArray<unknown>): void {
    const problems: string[] = [];
    if (unhandledErrors.length) problems.push(`${unhandledErrors.length} erreur(s) hors des tests`);
    // Seulement sur la suite complète : `vitest run un-fichier.test.ts` en lance moins, exprès.
    if (process.env.TESTS_TOTAL === "1") {
      const expected = testFiles(join(process.cwd(), "src")).length;
      if (testModules.length !== expected) {
        problems.push(`${testModules.length} fichiers de tests lancés sur ${expected} attendus`);
      }
    }
    if (problems.length) {
      console.error(`\nSuite incomplète : ${problems.join(" ; ")}.`);
      process.exitCode = 1;
    }
  }
}
