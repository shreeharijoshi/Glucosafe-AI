# OhioT1DM External Validation Metrics

Exploratory external-domain evaluation only; not clinical validation.

## Scope and safeguards

- Input: only `2018/test/*.xml` and `2020/test/*.xml` Ohio files.
- Ohio training XML files were not read or used.
- Final model: unchanged Manchester-trained `model_a_xgboost_final.json`.
- Ohio values are interpreted as mg/dL under the documented conditional decision; original XML metadata does not declare units, and subsequent peer-reviewed publications support the mg/dL convention.
- No Ohio training, fine-tuning, tuning, threshold selection, calibration, or preprocessing fit was performed.
- Threshold: 0.5.
- Features are historical glucose only; no meal or insulin fields are used.

## Dataset counts

- Test files: 12
- Test participants: 12
- Raw glucose observations: 31743
- Candidate rows: 31743
- Known target rows: 31107
- Feature-complete rows: 31425
- Eligible observations: 30789
- Positive observations: 1236
- Negative observations: 29553
- Invalid timestamp/value rows: 0
- Duplicate timestamp rows: 0

Preparation estimates were 30,789 eligible, 1,236 positive, and 29,553 negative observations. The implementation matched those counts exactly; no discrepancy required investigation.

## Pooled metrics

| Metric | Ohio external |
|---|---:|
| Average Precision | 0.875424 |
| ROC-AUC | 0.991105 |
| Precision | 0.863992 |
| Recall | 0.714401 |
| Specificity | 0.995297 |
| F1-score | 0.782108 |
| TP | 883 |
| TN | 29414 |
| FP | 139 |
| FN | 353 |

## Manchester internal LOPO comparison

| Metric | Manchester LOPO | Ohio external |
|---|---:|---:|
| Average Precision | 0.766317 | 0.875424 |
| ROC-AUC | 0.959966 | 0.991105 |
| Precision | 0.850679 | 0.863992 |
| Recall | 0.576556 | 0.714401 |
| Specificity | 0.996189 | 0.995297 |
| F1-score | 0.687293 | 0.782108 |
| TP | 5076 | 883 |
| TN | 232889 | 29414 |
| FP | 891 | 139 |
| FN | 3728 | 353 |

## Participant-wise metrics

participant_id  observations  positive_support  negative_support  average_precision  roc_auc  precision   recall  specificity       f1  tp   tn  fp  fn
           540          2815               194              2621           0.892907 0.987400   0.892617 0.685567     0.993895 0.775510 133 2605  16  61
           544          2653                46              2607           0.697765 0.991861   0.666667 0.652174     0.994246 0.659341  30 2592  15  16
           552          2265               104              2161           0.840176 0.985381   0.818182 0.692308     0.992596 0.750000  72 2145  16  32
           559          2406                86              2320           0.926032 0.994760   0.820225 0.848837     0.993103 0.834286  73 2304  16  13
           563          2543                23              2520           0.677689 0.991632   0.600000 0.652174     0.996032 0.625000  15 2510  10   8
           567          2281               211              2070           0.967721 0.995856   0.933673 0.867299     0.993720 0.899263 183 2057  13  28
           570          2655                19              2636           0.777912 0.995488   0.916667 0.578947     0.999621 0.709677  11 2635   1   8
           575          2491               174              2317           0.920905 0.990081   0.943262 0.764368     0.996547 0.844444 133 2309   8  41
           584          2521                62              2459           0.648055 0.982172   0.729730 0.435484     0.995933 0.545455  27 2449  10  35
           588          2764                 8              2756           0.613232 0.994058   0.571429 0.500000     0.998911 0.533333   4 2753   3   4
           591          2715               199              2516           0.868659 0.985573   0.881579 0.673367     0.992846 0.763533 134 2498  18  65
           596          2680               110              2570           0.835073 0.988495   0.839506 0.618182     0.994942 0.712042  68 2557  13  42

Participant-level AP/ROC-AUC may be unavailable when a participant has only one target class.

## Limitations

- Ohio original XML files do not explicitly declare glucose units; mg/dL is supported by subsequent peer-reviewed publications, not direct original-file metadata.
- Only 12 Ohio participants were evaluated.
- Ohio's official train/test partitions reuse participant IDs, although this model was trained exclusively on Manchester data.
- Dataset shift may affect performance.
- The target is hypoglycemia within 30 minutes after the prediction timestamp, not specifically after a meal.
- Results do not establish clinical validity or probability calibration.
