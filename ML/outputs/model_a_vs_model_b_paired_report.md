# Paired Model A vs Model B LOPO Evaluation

Exploratory observational research only; not clinical validation or evidence of safety.

- Shared eligible rows: 11344
- Participants and folds: 11
- Fixed threshold: 0.5 (descriptive experimental threshold, not medically validated)
- StandardScaler and regularized logistic regression were fitted separately on training participants per fold.
- Both models used identical rows, targets, participant-held-out folds, and no imputation or threshold tuning.
- Meal timestamps are recorded-time proxies, not confirmed consumption times; participant support is uneven and prediction windows overlap.
- Results are exploratory and do not establish clinical validity or safety.

## Pooled out-of-fold metrics

 group   model  positive_support  negative_support  average_precision  roc_auc  tp    tn  fp  fn  precision   recall  specificity       f1
pooled model_a               463             10881           0.620856 0.934960 179 10839  42 284   0.809955 0.386609     0.996140 0.523392
pooled model_b               463             10881           0.617917 0.934732 178 10838  43 285   0.805430 0.384449     0.996048 0.520468

## Pooled Model B minus Model A

           metric  model_b_minus_model_a
average_precision              -0.002940
          roc_auc              -0.000228
        precision              -0.004525
           recall              -0.002160
      specificity              -0.000092
               f1              -0.002924

## Per-participant metrics

 group   model  positive_support  negative_support  average_precision  roc_auc  tp   tn  fp  fn  precision   recall  specificity       f1
  2301 model_a                12              2017           0.404994 0.953355   2 2017   0  10   1.000000 0.166667     1.000000 0.285714
  2301 model_b                12              2017           0.404863 0.953024   2 2017   0  10   1.000000 0.166667     1.000000 0.285714
  2304 model_a                38              1899           0.286671 0.761828  16 1869  30  22   0.347826 0.421053     0.984202 0.380952
  2304 model_b                38              1899           0.287920 0.761329  16 1868  31  22   0.340426 0.421053     0.983676 0.376471
  2306 model_a                 0                 1                NaN      NaN   0    1   0   0        NaN      NaN     1.000000      NaN
  2306 model_b                 0                 1                NaN      NaN   0    1   0   0        NaN      NaN     1.000000      NaN
  2307 model_a                 5               771           0.607550 0.878340   3  767   4   2   0.428571 0.600000     0.994812 0.500000
  2307 model_b                 5               771           0.607513 0.877821   3  767   4   2   0.428571 0.600000     0.994812 0.500000
  2308 model_a               138              1262           0.672696 0.893865  33 1262   0 105   1.000000 0.239130     1.000000 0.385965
  2308 model_b               138              1262           0.675579 0.894531  32 1262   0 106   1.000000 0.231884     1.000000 0.376471
  2309 model_a                29               983           0.906758 0.988056  12  983   0  17   1.000000 0.413793     1.000000 0.585366
  2309 model_b                29               983           0.908674 0.988073  12  983   0  17   1.000000 0.413793     1.000000 0.585366
  2313 model_a                48              1289           0.773039 0.979441  27 1283   6  21   0.818182 0.562500     0.995345 0.666667
  2313 model_b                48              1289           0.770389 0.979571  28 1283   6  20   0.823529 0.583333     0.995345 0.682927
  2314 model_a                 0                22                NaN      NaN   0   22   0   0        NaN      NaN     1.000000      NaN
  2314 model_b                 0                22                NaN      NaN   0   22   0   0        NaN      NaN     1.000000      NaN
  2320 model_a               162              2559           0.870769 0.974807  69 2559   0  93   1.000000 0.425926     1.000000 0.597403
  2320 model_b               162              2559           0.870962 0.974831  68 2559   0  94   1.000000 0.419753     1.000000 0.591304
  2401 model_a                31                73           0.868275 0.948741  17   71   2  14   0.894737 0.548387     0.972603 0.680000
  2401 model_b                31                73           0.866251 0.947857  17   71   2  14   0.894737 0.548387     0.972603 0.680000
  2405 model_a                 0                 5                NaN      NaN   0    5   0   0        NaN      NaN     1.000000      NaN
  2405 model_b                 0                 5                NaN      NaN   0    5   0   0        NaN      NaN     1.000000      NaN

Metrics are N/A when class support is insufficient.
