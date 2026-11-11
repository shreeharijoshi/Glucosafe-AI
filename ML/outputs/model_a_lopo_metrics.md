# Model A LOPO Baseline Evaluation

Exploratory research results only; not clinical validation.

- Folds: 16
- Threshold: 0.5 (arbitrary fixed baseline)
- Preprocessing: StandardScaler fitted separately on training participants
- Unknown targets: excluded before fitting and evaluation

## Pooled out-of-fold metrics

 fold held_out_participant_id               model  average_precision  roc_auc   tp     tn  fp   fn  precision   recall  specificity       f1  positive_support  negative_support
    0                  pooled            logistic           0.702349 0.956123 4209 233093 687 4595   0.859681 0.478078     0.997061 0.614453              8804            233780
    0                  pooled     always_negative           0.036293 0.500000    0 233780   0 8804        NaN 0.000000     1.000000 0.000000              8804            233780
    0                  pooled training_prevalence           0.027324 0.339173    0 233780   0 8804        NaN 0.000000     1.000000 0.000000              8804            233780

## Fold metrics

 fold held_out_participant_id               model  average_precision  roc_auc   tp    tn  fp   fn  precision   recall  specificity       f1  positive_support  negative_support
    1                    2301            logistic           0.552061 0.963471  219 35309  86  370   0.718033 0.371817     0.997570 0.489933               589             35395
    1                    2301     always_negative           0.016368 0.500000    0 35395   0  589        NaN 0.000000     1.000000 0.000000               589             35395
    1                    2301 training_prevalence           0.016368 0.500000    0 35395   0  589        NaN 0.000000     1.000000 0.000000               589             35395
    2                    2303            logistic           0.415198 0.934726  105 13434  74  180   0.586592 0.368421     0.994522 0.452586               285             13508
    2                    2303     always_negative           0.020663 0.500000    0 13508   0  285        NaN 0.000000     1.000000 0.000000               285             13508
    2                    2303 training_prevalence           0.020663 0.500000    0 13508   0  285        NaN 0.000000     1.000000 0.000000               285             13508
    3                    2304            logistic           0.402612 0.841719  247 29933 128  398   0.658667 0.382946     0.995742 0.484314               645             30061
    3                    2304     always_negative           0.021006 0.500000    0 30061   0  645        NaN 0.000000     1.000000 0.000000               645             30061
    3                    2304 training_prevalence           0.021006 0.500000    0 30061   0  645        NaN 0.000000     1.000000 0.000000               645             30061
    4                    2305            logistic                NaN      NaN    0     7   0    0        NaN      NaN     1.000000      NaN                 0                 7
    4                    2305     always_negative                NaN      NaN    0     7   0    0        NaN      NaN     1.000000      NaN                 0                 7
    4                    2305 training_prevalence                NaN      NaN    0     7   0    0        NaN      NaN     1.000000      NaN                 0                 7
    5                    2306            logistic                NaN      NaN    0     4   0    0        NaN      NaN     1.000000      NaN                 0                 4
    5                    2306     always_negative                NaN      NaN    0     4   0    0        NaN      NaN     1.000000      NaN                 0                 4
    5                    2306 training_prevalence                NaN      NaN    0     4   0    0        NaN      NaN     1.000000      NaN                 0                 4
    6                    2307            logistic           0.610136 0.942922   86  8084  29  114   0.747826 0.430000     0.996425 0.546032               200              8113
    6                    2307     always_negative           0.024059 0.500000    0  8113   0  200        NaN 0.000000     1.000000 0.000000               200              8113
    6                    2307 training_prevalence           0.024059 0.500000    0  8113   0  200        NaN 0.000000     1.000000 0.000000               200              8113
    7                    2308            logistic           0.736670 0.937844  913 26412  91 1056   0.909363 0.463687     0.996566 0.614194              1969             26503
    7                    2308     always_negative           0.069156 0.500000    0 26503   0 1969        NaN 0.000000     1.000000 0.000000              1969             26503
    7                    2308 training_prevalence           0.069156 0.500000    0 26503   0 1969        NaN 0.000000     1.000000 0.000000              1969             26503
    8                    2309            logistic           0.794734 0.980275  287 19963  25  214   0.919872 0.572854     0.998749 0.706027               501             19988
    8                    2309     always_negative           0.024452 0.500000    0 19988   0  501        NaN 0.000000     1.000000 0.000000               501             19988
    8                    2309 training_prevalence           0.024452 0.500000    0 19988   0  501        NaN 0.000000     1.000000 0.000000               501             19988
    9                    2310            logistic           0.632407 0.957205  545 48438 150  677   0.784173 0.445990     0.996913 0.568597              1222             48588
    9                    2310     always_negative           0.024533 0.500000    0 48588   0 1222        NaN 0.000000     1.000000 0.000000              1222             48588
    9                    2310 training_prevalence           0.024533 0.500000    0 48588   0 1222        NaN 0.000000     1.000000 0.000000              1222             48588
   10                    2313            logistic           0.919222 0.990430 1371 28079  39 1192   0.972340 0.534920     0.998613 0.690159              2563             28118
   10                    2313     always_negative           0.083537 0.500000    0 28118   0 2563        NaN 0.000000     1.000000 0.000000              2563             28118
   10                    2313 training_prevalence           0.083537 0.500000    0 28118   0 2563        NaN 0.000000     1.000000 0.000000              2563             28118
   11                    2314            logistic                NaN      NaN    0    64   0    0        NaN      NaN     1.000000      NaN                 0                64
   11                    2314     always_negative                NaN      NaN    0    64   0    0        NaN      NaN     1.000000      NaN                 0                64
   11                    2314 training_prevalence                NaN      NaN    0    64   0    0        NaN      NaN     1.000000      NaN                 0                64
   12                    2320            logistic           0.723860 0.956306  383 22887  46  360   0.892774 0.515478     0.997994 0.653584               743             22933
   12                    2320     always_negative           0.031382 0.500000    0 22933   0  743        NaN 0.000000     1.000000 0.000000               743             22933
   12                    2320 training_prevalence           0.031382 0.500000    0 22933   0  743        NaN 0.000000     1.000000 0.000000               743             22933
   13                    2401            logistic           0.835665 0.966658   48   356   5   34   0.905660 0.585366     0.986150 0.711111                82               361
   13                    2401     always_negative           0.185102 0.500000    0   361   0   82        NaN 0.000000     1.000000 0.000000                82               361
   13                    2401 training_prevalence           0.185102 0.500000    0   361   0   82        NaN 0.000000     1.000000 0.000000                82               361
   14                    2403            logistic                NaN      NaN    0   101  14    0   0.000000      NaN     0.878261 0.000000                 0               115
   14                    2403     always_negative                NaN      NaN    0   115   0    0        NaN      NaN     1.000000      NaN                 0               115
   14                    2403 training_prevalence                NaN      NaN    0   115   0    0        NaN      NaN     1.000000      NaN                 0               115
   15                    2404            logistic                NaN      NaN    0     1   0    0        NaN      NaN     1.000000      NaN                 0                 1
   15                    2404     always_negative                NaN      NaN    0     1   0    0        NaN      NaN     1.000000      NaN                 0                 1
   15                    2404 training_prevalence                NaN      NaN    0     1   0    0        NaN      NaN     1.000000      NaN                 0                 1
   16                    2405            logistic           1.000000 1.000000    5    21   0    0   1.000000 1.000000     1.000000 1.000000                 5                21
   16                    2405     always_negative           0.192308 0.500000    0    21   0    5        NaN 0.000000     1.000000 0.000000                 5                21
   16                    2405 training_prevalence           0.192308 0.500000    0    21   0    5        NaN 0.000000     1.000000 0.000000                 5                21

Metrics are reported as N/A (`None`) when class or prediction support is insufficient.
Rows from overlapping prediction windows are temporally dependent.
