# Face-Off

A teacher-hosted maths game for a shared screen. Pick a set, add players or teams, and award points as students solve problems. No accounts or build step.

## Open the app

The GitHub Pages entry is `index.html`. For a local copy, run `python -m http.server 8000` in this directory, then open `http://localhost:8000`. On Windows, double-click `Start Face-Off.bat` with Python installed. Opening the HTML directly with `file://` does not allow the question-bank fetches.

## Modes

Choose the theme name at the top right. Studio, Notebook, Arcade, Sweet Shop, Orbit, Volcano, Stadium and Paper Flight share the same round and scores. Classic opens the original app in its own session. Returning to a modern mode preserves its round, with its timer paused.

Studio is the understated default. The more animated modes have moving scenery, particles, theme-specific transitions, and scoring celebrations. Volcano's lava rises with the countdown. Motion can be reduced or disabled in Settings; the system's reduced-motion preference is respected. Sound effects start off. Music stays on the local device.

## Questions

The library has all 23 original sets plus 16 new sets, each with 12 questions. The 192 new questions have separate hints, answers and worked solutions. Each set also has a short introduction under **Explore the idea**. The questions progress through three difficulty levels; their level is shown as one, two or three filled dots.

There are nine core practice sets and seven enrichment sets. Core sets cover number, fractions, decimals, percents, ratios, patterns, equations, spatial reasoning, measurement, data, probability and money decisions. Enrichment covers clock arithmetic, binary and ciphers, networks, counting, invariants, the pigeonhole principle and winning strategies. See `docs/teaching-notes.md` for prerequisites and the curriculum scope.

Enrichment rounds default to untimed and in order. A teacher can change time, length and order before starting any round. Scoring is manual; the app does not collect or automatically mark student responses. The original sets have been preserved rather than re-edited or re-audited.

## Controls

Space pauses or resumes the timer. A toggles the answer, H toggles the hint, and the left and right arrows change questions. Shortcuts are ignored in forms and dialogs. Revealing an answer, opening a dialog or hiding the browser tab suspends the countdown. A review round stays paused when moving between questions. **Undo point** reverses the latest score adjustment.

Settings control text size, motion, sound and local music. Player names, scores and preferences are stored in the browser, not sent to a server. The current question sequence is session-only. The fullscreen button depends on browser support.

## Mathematical content

The new app renders LaTeX formulas through KaTeX when its CDN is available. A built-in MathML fallback supports the notation used by the new bank without the CDN. Geometry uses 25 SVG diagrams with descriptive alternative text. This is formula and SVG support, not a browser TikZ compiler.

The modern bank is `g57_bank.json`. Its SVGs are embedded to avoid separate image requests. Matching SVG files are in `assets/diagrams/`. Individual JSON sets, using the existing `name` / `problems` / `q` / `answer` / `image` structure, are in `sets/g57/`; optional hints, solutions and lesson metadata extend that structure. The original `question_bank.json` is unchanged and is loaded separately.

Edit `content/sets.txt`, then run `python tools/build_bank.py`. A header starts with `@`; a lesson paragraph starts with `!`; a question uses `question || answer || hint || solution`, with optional `|| diagram-key || alt-text`. Mathematical expressions use dollar delimiters. Use a currency word in prose rather than an unpaired dollar sign. The builder writes the bundle, standalone sets and SVG assets deterministically.

## Checks

```
python tools/build_bank.py
python tests/validate.py
python tests/verify_answers.py
node --check faceoff-next.js
pip install -r tests/requirements.txt
python -m playwright install chromium
python tests/browser.py
```

The browser test starts its own local server. It tests every new question, theme changes, desktop and phone layouts, scoring, timer behaviour, persistence, offline formula fallback, KaTeX and Classic. `--embedded --executable /usr/bin/chromium` runs the restricted-environment renderer without opening a localhost URL. Screenshots and results go into `test-results/`.

`tests/verify_answers.py` independently recomputes all 192 answers, including exhaustive counting, parity reachability, shortest paths and game-strategy checks. `tests/validate.py` checks schema, SVG safety, generated-file consistency and the preservation hashes for the original app.

## Classic preservation

`classic.html` is byte-for-byte the original index page from commit `bf04d60f87bbabc4a71addce7fc474d9a695eb0e`. The original `app.js`, JSON files and class subfolders are untouched. Their hashes are recorded in `tests/classic_manifest.json`. The original repository also remains on `classic-backup-2026-09-06`.

Classic retains its original React, Tailwind and KaTeX CDN dependencies, interface and behaviour. It does not share scores or settings with the modern game.
