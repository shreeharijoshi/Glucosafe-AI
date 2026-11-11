# Experiment Plan

## Experiment 0 — Data validation

Validate files, timestamp formats, units, duplicates, participant IDs, missingness, gaps, and meal-carbohydrate semantics.

## Experiment 1 — Label feasibility

Implement and test the 30-minute target. Report positive, negative, and unknown labels separately. Test exact-boundary readings, gaps, duplicate rows, and recording boundaries. Do not copy earlier counts without correcting the known late-coverage boundary issue.

## Experiment 2 — Glucose-only baseline

Use current glucose, recent history, and valid historical trends only.

## Experiment 3 — Current-meal carbohydrate model

Add only the carbohydrate quantity of the current meal. Use the same eligible timestamps and participant partitions as Experiment 2.

## Experiment 4 — Comparative evaluation

Compare both models on identical held-out participants and, where possible, identical timestamps. Measure whether current-meal carbohydrates improve results; do not assume improvement.

A 60-minute horizon is a separate future experiment, not part of the initial implementation.
