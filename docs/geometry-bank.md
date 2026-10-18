# Area and perimeter bank

## Scope

One 50-question set, with ten questions each for squares, rectangles, parallelograms, triangles and trapezoids. Preserve the approved range: direct calculations, reverse calculations, shared boundaries, shaded regions, comparisons and connected deductions. Solutions use arithmetic, elementary algebra and area/perimeter relationships. They do not require Pythagoras, trigonometry or similarity calculations.

Difficulty is assigned explicitly on a five-point scale. It must remain attached to the question when the bank is filtered or shuffled. Keep the existing twelve-question banks and their three-point scale intact.

## Diagrams

Every question has a deterministic SVG diagram. The question supplies all measurements needed for a solution, either in its wording or its diagram. Right-angle markers identify perpendicular heights; equal-side ticks and parallel markers are used where relevant. Include rotated figures and outside heights.

The image, its title and its alternative text contain only givens. Unknown lengths remain unknown. Do not add computed side lengths, areas, intermediate arithmetic or solution constructions to the initial drawing. Hints, answers and worked solutions are separate revealable fields.

Drawing coordinates must describe mathematically possible figures. Numerical calculations used to construct a diagram do not become prerequisites for the student. Keep label text independent from construction coordinates, so constructing an accurate figure cannot automatically label its unknown lengths.

## Verification

Independently recompute all fifty answers. Check labelled dimensions, equal-side claims, perpendicular markers, SVG safety, alternative text and label bounds. Exercise all questions in the browser, including reveal/hide behaviour, shorter rounds, shape filtering, shuffling, review, narrow screens and the existing themes. Existing source-preservation and browser regression checks remain in place.

## Files and round settings

`content/geometry.json` is the editable source. Each problem has a stable code (S1–S10, R1–R10, P1–P10, T1–T10 or Z1–Z10), a shape group, an explicit `level` from 1 to 5, and separate `q`, `answer`, `hint`, `solution` and `imageAlt` fields. `diagramSpec.panels` holds one or two shape descriptions. Shape dimensions control construction; the `labels`, `heightLabel` and `caption` fields explicitly control displayed information.

`geometry.js` supplies reusable square, rectangle, parallelogram, triangle and trapezoid constructions, plus grids, joined squares, frames, corner cuts, diagonals and subdivisions. SVG markup is assembled from allowed primitives with escaped text. Shapes are scaled uniformly rather than stretched. The renderer also works under Node for validation or exporting SVGs.

The modern loader adds this bank separately from `g57_bank.json`, so the original generated bank and its reproducibility checks remain unchanged. No entries are added to the Classic manifest.

The bank defaults to 50 questions. The Shapes selector can limit a round to one group of ten. For a mixed shuffled round, shuffled shape buckets are sampled in rounds, with a fresh random shape order each time. A twelve-question round therefore contains two or three questions of each shape. Questions retain their authored difficulty and never repeat within a round.

Geometry diagrams can be enlarged in a dialog. The dialog contains the original givens-only SVG, pauses the timer and returns focus to the diagram when closed.
