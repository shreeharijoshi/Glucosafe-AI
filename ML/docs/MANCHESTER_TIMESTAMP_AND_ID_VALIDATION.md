# Manchester Timestamp and Participant-ID Validation

## 1. Confirmed participant mapping and unresolved mismatches

### Evidence used

- Dataset README filename convention: `UoM + "Data category" + ParticipantID.csv`.
- Actual folders:
  - `Glucose Data/UoMGlucose<ID>.csv`
  - `Nutrition Data/UoMNutrition<ID>.csv`
- Existing participant and data-quality findings in `Prac/dataset_audit_report.md` and `ML/docs/MEAL_DATA_AUDIT.md`.

Participant IDs were extracted from the explicit suffix between `UoMGlucose`/`UoMNutrition` and `.csv`. Matching was performed on that identifier, not on file order, row counts, or date similarity.

| Participant ID | Glucose files | Nutrition files | Both modalities |
|---|---:|---:|---|
| 2301 | 1 | 1 | Yes |
| 2302 | 1 | 1 | Yes |
| 2303 | 1 | 0 | No |
| 2304 | 1 | 1 | Yes |
| 2305 | 1 | 1 | Yes |
| 2306 | 1 | 1 | Yes |
| 2307 | 1 | 1 | Yes |
| 2308 | 1 | 1 | Yes |
| 2309 | 1 | 1 | Yes |
| 2310 | 1 | 0 | No |
| 2313 | 1 | 1 | Yes |
| 2314 | 1 | 1 | Yes |
| 2320 | 1 | 1 | Yes |
| 2401 | 1 | 1 | Yes |
| 2403 | 1 | 1 | Yes |
| 2404 | 1 | 1 | Yes |
| 2405 | 1 | 1 | Yes |

### Mapping result

- 17 glucose files contain 17 unique participant IDs.
- 15 nutrition files contain 15 unique participant IDs.
- 15 IDs have both glucose and nutrition files.
- Glucose-only IDs are `2303` and `2310`.
- No nutrition-only ID was found.
- No participant has multiple glucose files or multiple nutrition files in these two folders.

This confirms a deterministic filename-level pairing for the extracted tree. It does **not** prove that each participant's files cover the same dates or represent one continuous recording. The README documents the filename convention but does not document recording-segment boundaries, file overlap rules, or whether a participant can have separate periods represented elsewhere. A future loader must still compare within-file date ranges and preserve file/recording identifiers before joining modalities.

The README's stated population and the extracted file counts remain inconsistent with other local metadata: the README describes 16 individuals, citation metadata describes 17, and the extracted tree has 17 glucose IDs but only 15 nutrition IDs. The file-level mapping above is confirmed; the dataset-wide population count is not resolved by this check.

## 1.1 Publication and release documentation check

The locally available citation metadata identifies the release as:

> **T1D-UOM – A Longitudinal Multimodal Dataset of Type 1 Diabetes**

It lists Alsuhaymi et al. as authors, describes longitudinal data from 17
people with Type 1 diabetes, and gives a 2025 release date plus a Zenodo DOI
entry. The project audit documentation cites the dataset README and this
release metadata, but no separate locally available publication text or data
dictionary was found that defines timestamp ordering beyond the README tables.

The release metadata describes the study as longitudinal and the README gives
the collection period as October 2023 through August 2024. Neither source
explains the day/month contradiction, the different apparent population
counts, or the out-of-period nutrition years. The citation metadata therefore
identifies the dataset but does not independently validate the timestamp
convention.

## 2. Timestamp format evidence and parsing conclusion

### Documented formats

The dataset README documents:

- `bg_ts` as `MM/DD/YYYY HH:MM:SS`;
- `meal_ts` as `MM/DD/YYYY HH:MM`.

The existing inspection script instead uses day-first parsing:

- glucose and nutrition values are parsed as `%d/%m/%Y %H:%M`;
- the local audit reports that source values such as `22/10/2023` require day-first interpretation.

The README is the only directly relevant format documentation located in the
dataset release. It explicitly supports month-first notation for both
modalities, but it does not explain the contradiction with source values whose
first component is greater than 12. No separate data dictionary, release note,
or timezone metadata was found that resolves this conflict.

The sampled raw files use minute precision, not seconds:

```text
UoMGlucose2301.csv: 01/10/2023 00:04
UoMGlucose2301.csv: 01/10/2023 00:09
UoMNutrition2301.csv: 22/10/2023 10:00
UoMNutrition2301.csv: 22/10/2023 12:00
```

### Targeted format check

The following representative files were checked:

- `Glucose Data/UoMGlucose2301.csv`
- `Glucose Data/UoMGlucose2405.csv`
- `Nutrition Data/UoMNutrition2301.csv`
- `Nutrition Data/UoMNutrition2405.csv`

For each file, the raw timestamp strings were tested against exact day-first and month-first minute formats:

| File | Rows checked | Day-first parses | Month-first parses | Both interpretations parse | Raw duplicate timestamps | Backward transitions under day-first |
|---|---:|---:|---:|---:|---:|---:|
| `UoMGlucose2301.csv` | 45,768 | 45,768 | 20,452 | 20,452 | 7,250 | 0 |
| `UoMGlucose2405.csv` | 12,547 | 12,547 | 4,869 | 4,869 | 0 | 0 |
| `UoMNutrition2301.csv` | 302 | 302 | 126 | 126 | 6 | 5 |
| `UoMNutrition2405.csv` | 256 | 256 | 103 | 103 | 0 | 9 |

The counts show why “whichever format parses more rows” is not a valid rule. Day-first parses every sampled value, but month-first also parses dates where both day and month are at most 12. For example, `01/10/2023` can mean 1 October under day-first or January 10 under month-first. Values such as `22/10/2023` cannot be month-first and are direct evidence against applying the README's month-first interpretation to the entire extracted tree.

The evidence points in the same direction for `bg_ts` and `meal_ts`: both
contain unambiguous day-first records and both are compatible with a day-first
parser. This is a data-pattern conclusion, not authoritative documentation.
The README documents the same month-first convention for both fields, so the
available evidence does not establish a reliable final convention for either
field or prove that the two modalities were generated with the same convention.

The study period in the README is October 2023 through August 2024. A targeted
year scan found all glucose timestamps in 2023 or 2024, but nutrition data also
contains three out-of-period year values:

```text
UoMNutrition2404.csv: 29/04/2025 12:30
UoMNutrition2320.csv: 02/12/2033 20:00
UoMNutrition2404.csv: 22/04/2204 11:45
```

The 2025, 2033, and 2204 values are confirmed source strings, not corrected
dates. They cannot be used to decide day/month ordering and must be quarantined
as implausible until the source owner confirms whether they are data-entry
errors or represent an undocumented recording period.

The targeted year check found 2,461 glucose rows outside the reported
October 2023-August 2024 period, in `UoMGlucose2302.csv` and
`UoMGlucose2405.csv`. These include `04/09/2023 00:03` in
`UoMGlucose2302.csv`, which is an early-September 2023 record under the
day-first interpretation. It also found 10 nutrition rows outside that
period, in `UoMNutrition2314.csv`, `UoMNutrition2320.csv`, and
`UoMNutrition2404.csv`. The nutrition examples include December 2024 rows,
`02/12/2033 20:00`, `29/04/2025 12:30`, and `22/04/2204 11:45`.

The `2204` value is plausibly a typo for `2024`, but this is only an inference.
Nearby rows in the same file support that possibility:

```text
22/04/2024 07:45  Breakfast
22/04/2204 11:45  Lunch
22/04/2024 18:00  Dinner
```

The source value must remain unchanged and must not be corrected automatically.

Day-first parsing gives monotonic order for the two sampled glucose files. The
sampled nutrition files contain backward transitions even under day-first
parsing, so chronological consistency does not validate the nutrition
interpretation. This may reflect unsorted nutrition rows or invalid records;
it is not evidence for month-first parsing.

The targeted samples contained no timezone suffix or offset. The timestamp fields are timezone-naive strings; no timezone can be inferred from this check.

### Invalid and implausible values

The prior audit found five invalid or unparseable nutrition timestamps under its approved-at-that-time parsing attempt. A targeted search also found:

```text
UoMNutrition2404.csv: 22/04/2204 11:45
```

This value is syntactically parseable under a day-first pattern but is an obvious chronology/data-entry anomaly relative to the 2023–2024 study period. It must be classified as implausible or malformed and excluded from temporal joins unless the source owner confirms it.

The additional `29/04/2025` and `02/12/2033` values show that the 2204
timestamp is not the only out-of-period nutrition value, although it remains
the most extreme anomaly. No out-of-period glucose year was found in the
targeted year scan.

The prior full audit found 15,915 duplicate glucose timestamps and 18 duplicate nutrition timestamps. The sample reproduces the existence of duplicates but is not intended to replace those full-audit counts. Duplicate timestamps are not timezone evidence and must not be silently deduplicated.

The available local documentation does not explain any of the three
out-of-period nutrition years (`2025`, `2033`, or `2204`). They remain
unexplained source anomalies, not dates that may be corrected from local
evidence.

## 2.1 Investigation of the 10 out-of-period nutrition records

Using the empirically supported day-first interpretation and the reported
study period of October 2023 through August 2024, the exact 10 records are:

| File | Participant | Original `meal_ts` | Meal type | Meal tag | `carbs_g` | Classification |
|---|---:|---|---|---|---:|---|
| `UoMNutrition2314.csv` | 2314 | `06/12/2024 12:00` | Lunch | Beef sandwich and crisps | 38 | Plausible outside-period record |
| `UoMNutrition2314.csv` | 2314 | `08/12/2024 10:00` | Breakfast | Sausage and bacon bap | 69 | Plausible outside-period record |
| `UoMNutrition2314.csv` | 2314 | `08/12/2024 14:00` | Lunch | Turkey burger | 65 | Plausible outside-period record |
| `UoMNutrition2314.csv` | 2314 | `08/12/2024 21:00` | Dinner | Pizza and rum cake | 117 | Plausible outside-period record |
| `UoMNutrition2314.csv` | 2314 | `08/12/2024 16:00` | Snack | Wispa (x2) | 31 | Plausible outside-period record |
| `UoMNutrition2314.csv` | 2314 | `15/12/2024 10:30` | Snack | Tea cake | 32 | Plausible outside-period record |
| `UoMNutrition2314.csv` | 2314 | `15/12/2024 12:30` | Lunch | Standard lunch with fruit loaf | 83 | Plausible outside-period record |
| `UoMNutrition2320.csv` | 2320 | `02/12/2033 20:00` | Snack | Red Wine (2) | 70 | Likely malformed/corrupted |
| `UoMNutrition2404.csv` | 2404 | `22/04/2204 11:45` | Lunch | Aubergine Sandwich | 37 | Likely malformed/corrupted; possible `2024` typo |
| `UoMNutrition2404.csv` | 2404 | `29/04/2025 12:30` | Lunch | Ham Sandwich | 45 | Ambiguous; valid-looking isolated out-of-period record |

The seven December 2024 records for participant 2314 form a coherent
multi-day cluster with ordinary meal types, tags, and carbohydrate values.
They are outside the reported collection period, but there is no local
evidence that they are malformed. They should therefore be treated as
plausible out-of-period records rather than automatically discarded.

The 2033 record is isolated in the inspected evidence and is far outside the
reported 2023–2024 collection period, so corruption is more likely than a
valid study extension. This remains a classification, not a confirmed
correction. The 2025 record is also outside the period but has a normal-looking
date, meal description, and carbohydrate value; without provenance it cannot
be distinguished between a valid later record and a date-entry error.

For `UoMNutrition2404.csv`, nearby records are:

```text
22/04/2024 07:45,Breakfast,Porridge,34,13,7,
22/04/2204 11:45,Lunch,Aubergine Sandwich,37,10,14,0
22/04/2024 18:00,Dinner,Chicken Caedar,8,16,16,1
```

The same participant and calendar day have breakfast and dinner in 2024,
with the suspicious lunch between them. This strongly supports the possibility
that `2204` is a typo for `2024`, but it does not confirm the intended source
value and must not be corrected automatically.

The classification is based only on raw strings, local study-period metadata,
meal-field plausibility, clustering, and nearby rows. It does not establish
that any record is valid, that the study period is a hard boundary, or that
the timestamps represent actual consumption time.

## 2.2 Empirical date-order check across timestamp columns

A targeted pass over only the `bg_ts` and `meal_ts` columns counted the numeric
day/month components without parsing or changing the source strings. Dates
with both components at most 12 were counted as ambiguous.

| Modality | Rows checked | First component >12 (supports DD/MM) | Second component >12 (supports MM/DD) | Both components <=12 (ambiguous) | Other/malformed |
|---|---:|---:|---:|---:|---:|
| Glucose `bg_ts` | 356,146 | 211,951 | 0 | 144,195 | 0 |
| Nutrition `meal_ts` | 4,351 | 2,547 | 0 | 1,803 | 1 |

Representative unambiguous day-first values include:

```text
Glucose:   UoMGlucose2301.csv  13/10/2023 00:00
Nutrition: UoMNutrition2301.csv 22/10/2023 10:00
```

No unambiguous value supporting MM/DD/YYYY (a second component greater than
12) was found in either modality. The remaining values are ambiguous rather
than evidence for month-first parsing. This pass found no evidence of a
mixture in which some records unambiguously use MM/DD/YYYY; it cannot rule out
mixed conventions within the ambiguous subset.

The empirical evidence therefore supports a **day-first operational parsing
rule separately for both modalities**, with the important qualification that
the README explicitly documents month-first notation. This is a defensible
rule for the current files because it parses all observed day-first evidence
and no contrary unambiguous evidence was found, but it is still a documented
source conflict rather than independent authoritative confirmation. A loader
must preserve the raw value, record this decision, and quarantine malformed or
implausible rows.

## 3. Recommended future-loader rules

### Participant matching

1. Enumerate files only from the documented modality folders.
2. Extract the identifier using the exact modality prefixes `UoMGlucose` and `UoMNutrition`.
3. Match normalized identifier strings exactly.
4. Produce a manifest with participant ID, file path, modality, row count, original timestamp range, parsed timestamp range, and invalid/duplicate counts.
5. Keep unmatched glucose IDs out of the primary common Model A/Model B set; keep them available for separate Model A accounting.
6. Do not concatenate or join files across a participant until their recording boundaries and overlap have been checked.
7. Treat multiple files for one participant as separate recording segments unless provenance proves otherwise. The current two folders contain one file per ID per modality.

### Timestamp parsing

1. Preserve each original timestamp string.
2. Use the empirically supported day-first minute format (`%d/%m/%Y %H:%M`) separately for `bg_ts` and `meal_ts`, while recording the README's conflicting month-first specification in audit metadata.
3. Do not assume that a future dataset release or another modality uses the same convention; validate each timestamp column independently.
4. Retain parseable records that are plausible despite falling outside the reported study period; quarantine invalid, corrupted-looking, or unresolved records rather than silently correcting them.
5. Record parser format, parse status, and rejection reason per row.
6. Resolve the README/source-format conflict with the dataset owner or authoritative release documentation before treating the data-pattern day-first interpretation as final.
7. Keep timestamps timezone-naive unless authoritative metadata supplies a timezone. Do not invent or infer one.
8. After parsing, check monotonicity within each recording segment and retain duplicate/conflicting timestamp metadata.

## 4. Confirmed facts, provisional assumptions, and blockers

### Confirmed

- Participant IDs can be extracted and paired deterministically from the actual glucose and nutrition filenames.
- The extracted tree contains 17 glucose IDs, 15 nutrition IDs, 15 shared IDs, and two glucose-only IDs (`2303`, `2310`).
- There is one glucose file and one nutrition file per ID in these folders.
- Day-first minute parsing handles the representative raw values, including dates with day values above 12.
- Many sampled values are ambiguous because both day-first and month-first parsing succeed.
- Both modalities contain unambiguous day-first-looking values; this is evidence from the data, not authoritative format documentation.
- The targeted timestamp-column pass found 211,951 unambiguous day-first glucose values and 2,547 unambiguous day-first nutrition values, with zero unambiguous month-first values in either modality.
- The README states the same month-first format for both modalities.
- The targeted year check found 2,461 glucose rows and 10 nutrition rows outside the October 2023-August 2024 period under day-first interpretation.
- The sampled files contain duplicate timestamps; existing full-audit counts are 15,915 glucose duplicates and 18 nutrition duplicates.
- Timestamp strings contain no timezone information in the checked samples.

### Provisional assumptions

- Day-first is the empirically supported operational rule for both modalities because unambiguous day-first values occur and no unambiguous month-first values occur; the README conflict remains documented.
- A future loader can use exact filename-ID matching as its initial pairing rule.
- Within-file chronology and date-range comparisons can identify, but not by themselves resolve, recording overlap.

### Unresolved blockers

- The README's month-first documentation conflicts with the empirically supported day-first values in both modalities; source-owner confirmation remains desirable, especially for future releases.
- The five previously reported invalid nutrition timestamps, one malformed nutrition row, and the 2033/2204 records require an approved quarantine policy; the seven December 2024 records and isolated 2025 record require an explicit retain-or-quarantine decision.
- Duplicate and conflicting timestamp handling is not yet approved.
- File boundaries, possible recording segments, and timezone/clock alignment are not documented.
- The README/citation/extracted-tree participant-count disagreement remains unresolved.
- A parsed `meal_ts` is still only a recorded nutrition timestamp; this validation does not establish actual meal-consumption time.

### Safest next step

Do not build temporal joins or labels yet. Obtain the dataset owner's
authoritative clarification for `bg_ts` and `meal_ts` independently, including
the intended date order, study-period exceptions, and timezone. Until then,
preserve raw strings, quarantine the three implausible nutrition values, and
report day-first and month-first interpretations as unresolved alternatives
rather than silently selecting one.

## 5. Temporal-join readiness decision

The Manchester dataset is **not currently safe for temporal meal-to-glucose
joins**. The filename-level participant mapping is usable, but the local
README, citation metadata, and project documentation do not independently
confirm the date convention for either `bg_ts` or `meal_ts`, do not prove that
both modalities use the same convention, and do not explain the three
out-of-period nutrition values. No timezone is documented.

The remaining decision required before implementation is an authoritative
source-owner clarification covering, separately for glucose and nutrition:

1. date order and accepted precision;
2. timezone or confirmation that timestamps are intentionally local/naive;
3. whether the 2025, 2033, and 2204 nutrition records are corrections,
   exclusions, or valid exceptions.

Until that clarification is obtained, the project should preserve raw
timestamps, retain plausible out-of-period records for traceability, quarantine
the 2033 and 2204 records pending evidence, and avoid temporal meal-to-glucose
joins, labels, and model examples based on any unresolved records.

## 6. Official publication and repository check

The requested official publication is **“A Longitudinal Multimodal Dataset of
Type 1 Diabetes,”** Nature Scientific Data, DOI
`10.1038/s41597-025-05695-1`. The Nature article and PDF were not retrievable
in this environment (HTTP 406), so no claim about publication text beyond the
identified citation is made here.

The official repository
(`sharpic/ManchesterCSCoordinatedDiabetesStudy`) was checked. Its README
contains the same relevant claims as the local README: the collection period
is October 2023 through August 2024, and the data dictionary lists
`bg_ts`/`meal_ts` in month-first notation. The repository README does not:

- specify a separate, independently verified convention for glucose versus
  nutrition timestamps;
- establish a timezone or explain whether timestamps are local, UTC, or
  timezone-naive;
- explain whether `meal_ts` is meal logging time, reported meal time, or actual
  consumption time; or
- explain the nutrition values from 2025, 2033, and 2204.

Therefore, the official repository does not resolve the existing blockers.
The publication remains an unverified source in this environment because the
official Nature page could not be fetched. The project must not treat search
snippets or the study period as evidence that the out-of-period records are
errors or that a timezone can be assumed.

**Status after empirical date-order check:** The raw files support using
day-first parsing for both `bg_ts` and `meal_ts` as an explicit operational
rule: there are unambiguous day-first values in both modalities and no
unambiguous month-first values. This resolves the practical date-order choice
for the current files, but does not remove the README documentation conflict.

Manchester is still **not ready for unqualified temporal meal-to-glucose
joins**. Before implementation, the project must quarantine or otherwise
account for the out-of-period and malformed nutrition records, retain raw
timestamps, and document the absence of timezone metadata. The recorded
`meal_ts` semantics (logging/reporting versus actual consumption time) also
remain unresolved. Authoritative maintainer clarification is still preferred,
but a loader may proceed only under the explicitly recorded day-first rule and
these exclusions/limitations.
