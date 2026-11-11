# Manchester/T1D-UOM Timestamp Semantics Review

## Scope

This review covers the dataset README and citation metadata, the existing
Manchester loader, and the project's open-questions record. No source data,
datasets, or evaluation artifacts were changed.

## Documented facts

- The dataset README describes `meal_ts` as a nutrition datetime field and
  labels it “Datetime of observation.”
- The README lists the nutrition timestamp display format as
  `MM/DD/YYYY HH:MM`.
- The nutrition schema documents `carbs_g` as carbohydrates eaten, in grams.
- The README similarly describes `bg_ts` as a glucose datetime of observation
  and lists `MM/DD/YYYY HH:MM:SS`.
- The README reports collection from October 2023 to August 2024. The citation
  metadata describes longitudinal data collected in real-world settings and
  identifies the dataset as T1D-UOM.
- Neither the README nor the citation metadata specifies a timezone, UTC
  conversion, daylight-saving policy, device clock policy, or clock
  synchronization rule.
- The available documentation does not state whether `meal_ts` is the time
  food was consumed, the time nutrition was entered or recorded, a
  retrospective report time, or another event time.
- The project open questions retain meal timing, logging delay, timestamp
  precision, timezone, and alignment uncertainties.

## Empirical and operational observations already established

- Earlier targeted inspection found that raw timestamp values such as
  `22/10/2023` are operationally consistent with day-first parsing. The same
  operational rule is supported for glucose and nutrition timestamps.
- The existing audit also found a contradiction: the README documents
  month-first formatting, while the observed raw values and date-range checks
  support day-first interpretation for the project data.
- The loader quarantines malformed timestamps and suspicious years
  (`2033` and `2204`) rather than silently correcting them.
- The loader preserves the original timestamp text in `timestamp_raw` and
  stores parsed timestamps as timezone-naive pandas datetimes.

## Current implementation assumptions

The loader in `ML/src/data/manchester.py` applies:

- `pd.to_datetime(..., format="%d/%m/%Y %H:%M", errors="coerce")` for both
  glucose and nutrition files;
- no timezone localization or daylight-saving conversion;
- participant association based on the filename-derived participant ID;
- retention of valid duplicate timestamps for explicit downstream handling;
- quarantine of invalid and suspicious timestamp rows.

The Model B integration and paired experiment additionally assume that:

- nutrition records can be compared temporally with glucose prediction
  timestamps after this shared, timezone-naive parsing;
- only same-participant nutrition records are eligible;
- the recorded nutrition timestamp is usable as an ordering proxy;
- the carbohydrate window is the inclusive interval `[t - 30 minutes, t]`;
- nutrition records after prediction time are excluded;
- timestamps from different source partitions are not safely interchangeable
  without an explicit association.

These are operational research rules, not claims established by the dataset
documentation. In particular, the 30-minute window and `meal_ts <= t` rule
prevent future-record leakage under the operational clock, but they do not
prove that a recorded nutrition time equals actual consumption time.

## What is resolved

- The dataset contains participant identifiers in filenames and separate
  glucose and nutrition modalities.
- The project has a reproducible operational parser: day-first,
  minute-resolution, timezone-naive timestamps.
- Invalid and suspicious timestamp records have an explicit quarantine policy.
- The project has an explicit same-participant and no-future-record rule for
  exploratory carbohydrate alignment.

## What remains unresolved

- The semantic event represented by `meal_ts`: consumption, entry, logging,
  retrospective reporting, or another observation time.
- Whether logging delay is systematic or participant-dependent.
- The source timezone for either modality.
- Daylight-saving transitions and whether device clocks changed or were
  synchronized.
- Whether glucose and nutrition clocks share the same clock basis.
- Whether minute precision represents exact event time or rounded display time.
- Whether a meal record can safely be interpreted as available to an
  application at prediction time.

## Conclusion

The documentation does not establish `meal_ts` as actual consumption time,
recording time, or any more specific event time beyond a nutrition datetime
described as an observation. The existing pipeline therefore performs a
documented operational alignment, not a validated physiological meal-to-glucose
alignment. Model B results should remain exploratory and should not be
interpreted as evidence that carbohydrate information was available at the
actual time of eating or as clinical validation.
