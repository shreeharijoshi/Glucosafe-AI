# Model A Random Forest LOPO Evaluation

Exploratory research results only; not clinical validation.

- Folds: 16
- Eligible out-of-fold predictions: 242584
- Threshold: 0.5
- Model: RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42)
- Features and eligibility: identical to the existing Model A Logistic Regression evaluation
- Unknown targets: excluded before fitting and evaluation

## Pooled out-of-fold metrics

 fold held_out_participant_id         model  average_precision  roc_auc   tp     tn    fp   fn  precision   recall  specificity       f1  positive_support  negative_support
    0                  pooled random_forest           0.643901 0.938373 6702 222550 11230 2102   0.373745 0.761245     0.951963 0.501346              8804            233780

## Participant-level metrics

 fold held_out_participant_id         model  average_precision  roc_auc   tp    tn   fp  fn  precision   recall  specificity       f1  positive_support  negative_support
    1                    2301 random_forest           0.360663 0.910522  329 34522  873 260   0.273710 0.558574     0.975335 0.367393               589             35395
    2                    2303 random_forest           0.767162 0.986732  273 12581  927  12   0.227500 0.957895     0.931374 0.367677               285             13508
    3                    2304 random_forest           0.549896 0.866159  438 28906 1155 207   0.274953 0.679070     0.961578 0.391421               645             30061
    4                    2305 random_forest                NaN      NaN    0     7    0   0        NaN      NaN     1.000000      NaN                 0                 7
    5                    2306 random_forest                NaN      NaN    0     4    0   0        NaN      NaN     1.000000      NaN                 0                 4
    6                    2307 random_forest           0.430553 0.914177  112  7937  176  88   0.388889 0.560000     0.978306 0.459016               200              8113
    7                    2308 random_forest           0.601270 0.911540 1436 24121 2382 533   0.376113 0.729304     0.910123 0.496285              1969             26503
    8                    2309 random_forest           0.681641 0.958963  409 19198  790  92   0.341118 0.816367     0.960476 0.481176               501             19988
    9                    2310 random_forest           0.446861 0.931005  867 45851 2737 355   0.240566 0.709493     0.943669 0.359304              1222             48588
   10                    2313 random_forest           0.884078 0.975477 2248 27058 1060 315   0.679565 0.877097     0.962302 0.765798              2563             28118
   11                    2314 random_forest                NaN      NaN    0    59    5   0   0.000000      NaN     0.921875 0.000000                 0                64
   12                    2320 random_forest           0.572553 0.926876  530 21839 1094 213   0.326355 0.713324     0.952296 0.447824               743             22933
   13                    2401 random_forest           0.841413 0.937386   55   347   14  27   0.797101 0.670732     0.961219 0.728477                82               361
   14                    2403 random_forest                NaN      NaN    0    98   17   0   0.000000      NaN     0.852174 0.000000                 0               115
   15                    2404 random_forest                NaN      NaN    0     1    0   0        NaN      NaN     1.000000      NaN                 0                 1
   16                    2405 random_forest           1.000000 1.000000    5    21    0   0   1.000000 1.000000     1.000000 1.000000                 5                21

Metrics are reported as N/A (`None`) when class or prediction support is insufficient.
Rows from overlapping prediction windows are temporally dependent.
