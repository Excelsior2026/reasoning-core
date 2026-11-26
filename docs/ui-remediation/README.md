# UI remediation record — reasoning-core

## Roles

- **Implementer:** Big Pickle (`big-pickle`), running as the OpenCode coding agent in the assigned worktree.
- **Orchestrator / integration owner:** Big Pickle (the session that spawned this subagent). This subagent did **not** push, merge, open a PR, or deploy.
- **Reviewer:** a separate reviewer/model is expected to follow. Per `AI_ATTRIBUTION.md`, an AI-drafted PR needs final-head review by a different model; that review has **not** happened here.

## Scope anchors

- Repository: `Excelsior2026/reasoning-core`
- Worktree: `/Users/temporary/ui-ux-review/worktrees/wave1/Excelsior2026__reasoning-core`
- Branch: `fix/ui-remediation/reasoning-core-clean-start`
- Baseline SHA (verified before any edit): `7151cd47f6c88d6f768a1fc6fd4926a58885020e`
- Implementation commits:
  - `9987130a42f119b304f3cbb0deaedff7b9ef7087` — clean install/build unblock (REA-01 + enabling JSX fix)
  - `e9a68e1c84d8a9a70df130f5eda4f7c7460d077b` — single-stream fix and regression tests (REA-02)
- Head at handoff: `e9a68e1c84d8a9a70df130f5eda4f7c7460d077b` (this documentation commit follows it; documentation does not self-reference its own SHA).

## Approach

1. Verified the worktree HEAD matched the baseline before editing.
2. Captured the baseline `npm ci` and dependency-resolution failures **before** changing `web/package.json`.
3. Removed the unusable `cytoscape-react` dependency after confirming no source file imports it; generated `web/package-lock.json` deliberately and re-ran `npm ci`, dev-server HTTP check, and the native build.
4. Repaired a pre-existing `DetailedView.jsx` JSX syntax error that surfaced during the build verification and would otherwise leave a 200-OK dev server with an uncompilable app.
5. Only after REA-01 verification, centralized the progress stream into `web/src/taskProgress.js`, made `ProgressBar` the sole caller, deleted `FileUpload`'s second poll loop, and added runtime + static regression tests.
6. Recorded every command result in `VERIFICATION.md`, including blocked screenshot attempts and failures that were subsequently fixed.

## In scope

- `web/package.json`: remove `cytoscape-react@^2.1.0`; add a dependency-free `npm test` script.
- `web/package-lock.json`: newly generated lockfile (`lockfileVersion: 3`).
- `web/src/components/DetailedView.jsx`: minimal JSX delimiter repair needed for the build to run.
- `web/src/taskProgress.js`: single-owner stream controller (SSE + fallback polling + cleanup).
- `web/src/components/ProgressBar.jsx`: stable `taskId`-only effect; callbacks held in refs.
- `web/src/components/FileUpload.jsx`: duplicate result-polling loop removed.
- `web/tests/taskProgress.test.js`: four Node tests covering the single-stream invariant.
- `docs/ui-remediation/`: this README, `DECISIONS.md`, `VERIFICATION.md`, and raw evidence logs/artifacts.

## Out of scope / not done

- `URLInput.jsx` still has its own `pollResults` loop alongside `ProgressBar`. It is the same defect class as REA-02 but was not in the assigned finding and was left unchanged for reviewability.
- Backend `/api/progress` and `/api/results` behavior was not exercised; no backend was started.
- `npm audit` vulnerabilities (2 reported) were not remediated; no dependency upgrades beyond lockfile generation.
- No visual inspection, accessibility audit, or UX review was performed.
- No app screenshots were produced (Chrome teardown failure in this environment); see `VERIFICATION.md`.
- No push, merge, PR, deployment, credential change, or production-data change.
- Python source and tests were not changed; Python tests were only run as a repo-native check.

## Evidence index

- `DECISIONS.md` — ADRs for the dependency choice, single-stream design, and enabling JSX fix.
- `VERIFICATION.md` — command-by-command results with `passed` / `failed` / `blocked` / `not-run` classifications.
- `evidence/` — raw logs. `chrome-probe.png` is an `about:blank` environment probe, **not** an app screenshot.

AI-Model: Big Pickle (big-pickle)
AI-Provider: opencode
AI-Role: Drafted
