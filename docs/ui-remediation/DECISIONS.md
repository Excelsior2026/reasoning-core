# Decision records — UI remediation

## ADR-001 — Remove `cytoscape-react` instead of pinning another version

**Status:** Accepted. Implemented in `9987130`.

### Context

Baseline `web/package.json` declared `cytoscape-react@^2.1.0`. Resolution failed with `ETARGET: No matching version found for cytoscape-react@^2.1.0`. `npm view cytoscape-react versions --json` showed published versions `1.0.0`…`1.0.6`, `2.0.0`, `3.0.0`…`3.0.2`, `4.0.0`, `5.0.3`, `5.0.4` — the package exists, but no `2.1.x` version does. `web/package-lock.json` was not tracked, so plain `npm ci` failed earlier with `EUSAGE` for lack of a lockfile.

A repository-wide search found only direct `cytoscape` imports in `KnowledgeGraphViewer.jsx` and `GraphComparison.jsx`. No file imports `cytoscape-react`.

### Decision

Delete the dependency and generate a real lockfile from the remaining manifest. Keep the direct `cytoscape@^3.26.0` dependency, which is actually used.

### Alternatives rejected

- **Pin `cytoscape-react@2.0.0` or `^3.0.0`:** would make install pass but add an unused wrapper package and a new compatibility surface for no benefit.
- **Replace with a different React graph wrapper:** larger refactor, no evidence any wrapper API is used.
- **Leave the declaration and rely on `npm install --legacy-peer-deps` / `--force`:** does not resolve `ETARGET`; would only hide unrelated warnings.

### Risks and mitigations

- Risk: a dynamic or future use of `cytoscape-react` was missed. Mitigated by the grep evidence, a successful production build, and the runtime DOM check; no import exists.
- Risk: newly generated lockfile pins transitive versions that differ from a maintainer's local state. Intentional: a clean, reproducible install is the goal. Final `npm install --package-lock-only` produced no further diff.
- Residual: npm reported 2 vulnerabilities (1 moderate, 1 high) and blocked 2 install scripts under npm 12's allow-scripts policy. Neither was changed here; both are recorded in `VERIFICATION.md`.

## ADR-002 — One injectable stream owner, stable React lifecycle

**Status:** Accepted. Implemented in `e9a68e1`.

### Context

`ProgressBar.jsx` opened an `EventSource` in an effect with dependencies `[taskId, onComplete, onError, stage]`. `stage` changed on nearly every message, and `onComplete`/`onError` were inline functions recreated on every parent render, so the effect could close and reopen the stream repeatedly. Its completion path scheduled an untracked `setTimeout` result fetch; its `onerror` path started an untracked polling chain. `FileUpload.jsx` independently called `pollResults()` after upload and had its own untracked `setTimeout` loop. Completion or error from both owners could call the parent callback more than once, and no timer was guaranteed to be cleared on unmount.

### Decision

- Extract all stream mechanics into `web/src/taskProgress.js` (`createTaskStream`).
- One `createTaskStream` call equals at most one `EventSource`, at most one polling chain, at most one pending timer, and at most one terminal callback. A `settled` guard enforces `onComplete`/`onError` exclusivity; a `finalizing` guard prevents duplicate final result fetches; `polling` prevents duplicate fallback chains.
- `ProgressBar` is the only caller. Its stream effect depends on `[taskId]` alone; callbacks are read through refs so parent re-renders cannot restart the stream.
- `FileUpload` only uploads and sets `taskId`; it does not poll.
- `dispose()` closes the stream and cancels the pending timer.
- Regression coverage is dependency-free: `web/tests/taskProgress.test.js` uses injected fake EventSource/timers for runtime assertions plus a static source scan asserting one `new EventSource` site, no `pollResults`/`setTimeout` in `FileUpload.jsx`, and the exact `[taskId]` dependency list on the stream effect.

### Alternatives rejected

- **Keep two loops but add shared flags:** more fragile; the coupling would live across two components and still depend on callback identities.
- **Move everything into `FileUpload` and make `ProgressBar` purely presentational:** cleaner in isolation, but a larger refactor touching the shared `ProgressBar` API used by `URLInput` and `TextInput`; not needed for the assigned finding.
- **Add a third-party SSE library:** new dependency and install surface, contrary to the REA-01 lesson.
- **Only add a code comment documenting the invariant:** no enforcement.

### Risks and mitigations

- Risk: SSE connects but never emits and never errors, so fallback polling never starts. Mitigation: unchanged from baseline behavior; explicitly recorded as a residual risk rather than silently adding new policy.
- Risk: parent callback identity changes are ignored by the stream effect. Mitigation: refs are synced in small dedicated effects, so callbacks stay current without reopening the stream.
- Risk: the static test is text-based and could be bypassed by unusual formatting. Mitigation: it is paired with runtime tests of the actual controller.
- Residual: `URLInput.jsx` retains its own duplicate poll loop alongside `ProgressBar`; this fix does not cover that component.
- Residual: no backend was available, so end-to-end SSE behavior against the real API was not verified.

## ADR-003 — Minimal JSX repair in `DetailedView.jsx`

**Status:** Accepted. Implemented in `9987130`.

### Context

After the dependency fix, `npm run build` failed at `DetailedView.jsx:116` with `Expected ")" but found "{"`. The concepts-tab IIFE was never invoked: `))}` closed the `map()` call and arrow body but omitted `)()}`, leaving the following `chains`/`questions` JSX inside an unclosed expression. The dev server returned HTTP 200 for `index.html` while Vite's dependency scan failed, which would be misleading evidence if left unreported.

### Decision

Close and invoke the IIFE by changing the `))}` line to `))` followed by `})()}`, then align the following sibling JSX indentation. No conditional logic or data flow was changed.

### Alternatives rejected

- **Leave it and report only HTTP 200:** would claim a working dev server while the app could not compile.
- **Rewrite the DetailedView component:** out of scope and harder to review.

### Risks and mitigations

- Risk: the repair changes which tabs render. Mitigation: the previous code was uncompilable, so there was no working behavior to preserve; build and DOM rendering were re-verified. Remaining tab behavior was not interactively tested and is listed in `VERIFICATION.md` as not-run.

AI-Model: Big Pickle (big-pickle)
AI-Provider: opencode
AI-Role: Drafted
