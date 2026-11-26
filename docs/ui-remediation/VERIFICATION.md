# Verification record — UI remediation

All commands below were run in the assigned worktree. `web/` means `/Users/temporary/ui-ux-review/worktrees/wave1/Excelsior2026__reasoning-core/web`; repo root means the worktree root. Raw output is in `evidence/`. No command was weakened to make a check pass.

## Environment and preflight

| Command | Result | Classification |
| --- | --- | --- |
| `git rev-parse HEAD` (repo root) | `7151cd47f6c88d6f768a1fc6fd4926a58885020e` | **passed** — matches required baseline |
| `git status --short --branch` (repo root) | `## fix/ui-remediation/reasoning-core-clean-start`, no changes | **passed** — clean baseline |
| `node --version` | `v22.23.4` | passed (environment) |
| `npm --version` | `12.2.0` | passed (environment) |
| `git ls-files web` | no `web/package-lock.json` tracked | passed (diagnostic) |
| `grep -rn "cytoscape" web/src web/package.json web/README.md` | only direct `cytoscape` imports in `KnowledgeGraphViewer.jsx` and `GraphComparison.jsx`; no `cytoscape-react` import | passed (diagnostic) |
| `grep -rn "EventSource\|setInterval\|setTimeout\|/api/results\|poll" web/src` | duplicate loops in `FileUpload.jsx` (lines 56/73/95), `ProgressBar.jsx` (lines 12/26/56/91), and `URLInput.jsx` (lines 33/50/72) | passed (diagnostic) |
| `AI_ATTRIBUTION.md` read before first commit | commit trailers added; PR reserved for separate reviewer | passed |

## Baseline failures (captured before edits)

Evidence: `evidence/npm-ci-baseline.log`, `evidence/npm-install-package-lock-only-baseline.log`, `evidence/npm-view-cytoscape-react-baseline.log`.

| Command | Exact observed result | Classification |
| --- | --- | --- |
| `npm ci` (in `web/`) | exit 1; `npm error code EUSAGE` — "The `npm ci` command can only install with an existing package-lock.json with lockfileVersion >= 1." | **failed** — expected baseline blocker |
| `npm install --package-lock-only` (in `web/`) | exit 1; `npm error code ETARGET` — "No matching version found for cytoscape-react@^2.1.0." | **failed** — expected baseline blocker |
| `npm view cytoscape-react versions --json` (in `web/`) | exit 0; versions `1.0.0`–`1.0.6`, `2.0.0`, `3.0.0`–`3.0.2`, `4.0.0`, `5.0.3`, `5.0.4`. No `2.1.x`. | **passed** — diagnostic; the package exists but the requested range does not |

Correction to the finding wording: the failure is an unavailable `^2.1.0` range, not a wholly nonexistent npm package.

## REA-01 — clean install, server, build

| Command | Result | Classification |
| --- | --- | --- |
| Remove `cytoscape-react` from `web/package.json` | one-line dependency removal | passed |
| `npm install --package-lock-only` (in `web/`) | exit 0; created `package-lock.json`, `lockfileVersion: 3`; no `cytoscape-react` entry | **passed** — evidence `npm-install-package-lock-only-after.log` |
| `npm ci` (in `web/`, no pre-existing `node_modules`) | exit 0; `added 159 packages, and audited 160 packages in 4s`; `2 vulnerabilities (1 moderate, 1 high)`; npm blocked install scripts for `esbuild@0.18.20` and `fsevents@2.3.3` under its allow-scripts policy | **passed with caveats** — evidence `npm-ci-after.log` |
| `npm run dev -- --host 127.0.0.1 --port 3100 --strictPort` (in `web/`) | Vite v4.5.14 ready in 1696 ms, but dependency scan failed on `DetailedView.jsx:116`: `Expected ")" but found "{"` | **failed initially** — evidence `dev-server.log`; app could not compile even though root HTML served |
| `curl -sS -o /dev/null -w 'http_code=%{http_code}\n' --max-time 10 http://127.0.0.1:3100/` | `http_code=200` | **passed** — evidence `curl-http200-after.log`. Note: HTTP 200 on `index.html` alone did not imply a working app; the build error above was found from the server log. |
| `npm run build` (in `web/`, before JSX fix) | exit 1; same `DetailedView.jsx:116` esbuild parse error | **failed** — evidence `npm-run-build-before-jsx-fix.log` |
| Minimal JSX repair in `DetailedView.jsx` | close/invoke the concepts IIFE with `}))` + `})()}`; align following sibling JSX | passed |
| `npm run build` (after JSX fix) | exit 0; `118 modules transformed`, built in 2.30 s; warning: bundle >500 kB | **passed** — evidence `npm-run-build-after-jsx-fix.log` |
| Fresh `npm run dev -- --host 127.0.0.1 --port 3100 --strictPort` | Vite ready in 786 ms; no parse errors in log | **passed** — evidence `dev-server-final.log` |
| Fresh `curl ... http://127.0.0.1:3100/` | `http_code=200` | **passed** — evidence `curl-http200-final.log` |
| `npm install --package-lock-only` (final, in `web/`) | exit 0; `git diff --stat -- package-lock.json` empty | **passed** — evidence `npm-install-package-lock-only-final.log` |

## REA-02 — single stream

| Command | Result | Classification |
| --- | --- | --- |
| Add `web/src/taskProgress.js` with injected `EventSourceImpl`, `getResults`, `schedule`, `cancel` | controller enforces one stream, one polling chain, one pending timer, and one terminal callback | passed (implementation) |
| Rewrite `ProgressBar.jsx` stream effect to `[taskId]` with callback refs | dependency list is exactly `[taskId]`; cleanup calls `stream.dispose()` | passed (implementation) |
| Delete `FileUpload.jsx` `pollResults` and its `setTimeout` loop | no `pollResults`, `setTimeout`, or `setInterval` remains in that file | passed (implementation) |
| Add `web/tests/taskProgress.test.js` and `npm test` script | four tests using fake EventSource/timers plus a static source scan | passed (implementation) |
| `npm test` with initial `node --test tests` | exit 1; `Cannot find module .../web/tests` (Node 22 treated the directory as a module path) | **failed** — fixed by using an explicit glob, not by removing the check |
| `npm test` with `node --test tests/*.test.js` (first glob run) | 3 passed, 1 failed; static regex wrongly matched the intentional `[onComplete]` / `[onError]` ref-sync effects | **failed** — narrowed regex to the stream effect only |
| `npm test` final (`node --test tests/*.test.js`) | `pass 4`, `fail 0`; tests: one EventSource + no duplicate completion; one poll chain after repeated SSE errors; dispose closes/cancels; source invariant | **passed** — evidence `npm-test-after.log` |
| `npm run build` final (in `web/`) | exit 0; `119 modules transformed`, built in 17.77 s; same >500 kB chunk warning | **passed** — evidence `npm-run-build-final.log` |
| Static invariant checked by the fourth test | exactly one `new EventSource` site (`web/src/taskProgress.js`); `FileUpload.jsx` has no polling timers; `ProgressBar.jsx` stream effect ends with `}, [taskId])` | **passed** — part of `npm-test-after.log` |

The path `web/src/lib/taskProgress.js` was initially attempted but the repo's broad `lib/` ignore rule hid it; it was moved to `web/src/taskProgress.js` and all imports/tests were updated before commit.

## Screenshots — blocked, not captured

Required artifacts `evidence/desktop-1440x900.png` and `evidence/mobile-375x812.png` **do not exist**. They were **not captured and therefore not visually inspected**. `evidence/chrome-probe.png` is only an `about:blank` control image and is not an app screenshot.

| Command | Result | Classification |
| --- | --- | --- |
| `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-first-run --hide-scrollbars --window-size=1440,900 --virtual-time-budget=6000 --screenshot=.../desktop-1440x900.png http://127.0.0.1:3100/` | timed out after 120 s, exit 143; `CVDisplayLinkCreateWithCGDisplay failed`, `Network service crashed`, `Abnormal renderer termination`; no file written | **blocked** — evidence `chrome-desktop.log` |
| Same command + `--no-sandbox --disable-dev-shm-usage --user-data-dir=<temp profile>` | timed out after 90 s; same renderer/GPU errors; no file | **blocked** — evidence `chrome-desktop-retry.log` |
| Legacy `--headless` variant with temp profile | timed out after 70 s; no file | **blocked** — evidence `chrome-desktop-legacy.log` |
| Control: same headless flags with `about:blank`, `--window-size=800,600`, `--virtual-time-budget=1000`, `--screenshot=.../chrome-probe.png` | exit 0; `chrome-probe.png` written | **passed** — diagnostic proving Chrome starts; evidence `chrome-probe.log` |
| `npm run preview -- --host 127.0.0.1 --port 3101 --strictPort` then `curl ... http://127.0.0.1:3101/` | `http_code=200` | **passed** — evidence `preview-server.log`, `curl-http200-preview.log` |
| Exact required Chrome command against preview URL `http://127.0.0.1:3101/` | timed out after 70 s; no file | **blocked** — evidence `chrome-desktop-preview-exact.log` |
| Preview URL + temp profile flags | timed out after 90 s; no file | **blocked** — evidence `chrome-desktop-preview-profile.log` |
| Chrome `--dump-dom` against preview URL | exit 2 with `Teardown watchdog expired`; DOM did contain the rendered app header, tabs, upload panel, and "No analysis yet" state | **failed** (Chrome teardown) but useful partial evidence — evidence `chrome-dump-dom.log` |
| Preview URL + `--disable-gpu-compositing --disable-software-rasterizer` | timed out after 75 s; `Abnormal renderer termination`; no file | **blocked** — evidence `chrome-desktop-final-attempt.log` |
| Mobile: `--window-size=375,812 --screenshot=.../mobile-375x812.png` against preview URL with temp profile | timed out after 60 s; no file | **blocked** — evidence `chrome-mobile-375x812.log` |

Conclusion: Chrome can screenshot `about:blank`, can render the app DOM, but cannot complete teardown/screenshot for this page in this environment. This is an environment limit, not evidence of a UI regression. No visual claim is made.

## Repo-native Python/lint checks

| Command | Result | Classification |
| --- | --- | --- |
| `python3 -m pytest -q` (repo root) | exit 4; `ModuleNotFoundError: No module named 'reasoning_core'` while loading `tests/conftest.py` | **failed** — environment/PYTHONPATH, evidence `python-pytest.log` |
| `PYTHONPATH=src python3 -m pytest -q` | exit 2; 3 collection errors: `ModuleNotFoundError: No module named 'aiofiles'` in web tests | **blocked** — missing `web` extra dependency, evidence `python-pytest-pythonpath.log` |
| `PYTHONPATH=src python3 -m pytest -q --ignore=tests/test_web_cleanup.py --ignore=tests/test_web_security.py --ignore=tests/test_web_smoke.py` | exit 0; `73 passed in 2.89s`; coverage 65.41%, above 65% gate | **passed** — evidence `python-pytest-core.log` |
| `pre-commit run --all-files` | `command -v pre-commit` returned nothing; executable not installed | **not-run** — environment limit, no evidence log |

## Failures, lessons, residual risks

- Baseline `npm ci` failed for two independent reasons: missing lockfile and an unresolvable version range. Fixing only one would have left the clean-install story broken.
- HTTP 200 on `/` was insufficient evidence of a working app; the dev-server log exposed a build-breaking JSX error. Both signals are now recorded.
- Changing a lint/test invocation to a form the runner accepts was necessary; changing assertions to hide failures was not done.
- A repo-wide `lib/` ignore rule required relocating the new controller rather than force-adding it.
- Residual risks: `URLInput.jsx` duplicate polling remains; SSE stall without error has no watchdog; backend contract untested; no app screenshots; npm audit findings and blocked install scripts remain; large chunk warning remains; no separate-model review has occurred.

AI-Model: Big Pickle (big-pickle)
AI-Provider: opencode
AI-Role: Drafted
