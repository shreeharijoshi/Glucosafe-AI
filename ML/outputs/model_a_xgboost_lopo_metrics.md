# Model A XGBoost LOPO Evaluation

Exploratory research results only; not clinical validation.

- Participants: 16
- Folds: 16
- Eligible out-of-fold predictions: 242584
- Participant overlap/leakage detected: no
- Threshold: 0.5
- Model: XGBClassifier(objective='binary:logistic', n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
- Features and eligibility: identical to the existing Model A evaluations
- Unknown targets: excluded before fitting and evaluation

## Pooled out-of-fold metrics

 fold held_out_participant_id   model  average_precision  roc_auc   tp     tn  fp   fn  precision   recall  specificity       f1  positive_support  negative_support
    0                  pooled xgboost           0.766317 0.959966 5076 232889 891 3728   0.850679 0.576556     0.996189 0.687293              8804            233780

## Participant-level metrics

 fold held_out_participant_id   model  average_precision  roc_auc   tp    tn  fp  fn  precision   recall  specificity       f1  positive_support  negative_support
    1                    2301 xgboost           0.584277 0.965637  240 35311  84 349   0.740741 0.407470     0.997627 0.525739               589             35395
    2                    2303 xgboost           0.478226 0.934968  113 13429  79 172   0.588542 0.396491     0.994152 0.473795               285             13508
    3                    2304 xgboost           0.490855 0.841328  238 29960 101 407   0.702065 0.368992     0.996640 0.483740               645             30061
    4                    2305 xgboost                NaN      NaN    0     7   0   0        NaN      NaN     1.000000      NaN                 0                 7
    5                    2306 xgboost                NaN      NaN    0     4   0   0        NaN      NaN     1.000000      NaN                 0                 4
    6                    2307 xgboost           0.609897 0.946410   83  8081  32 117   0.721739 0.415000     0.996056 0.526984               200              8113
    7                    2308 xgboost           0.762913 0.948909 1050 26326 177 919   0.855746 0.533266     0.993322 0.657071              1969             26503
    8                    2309 xgboost           0.822578 0.982421  330 19946  42 171   0.887097 0.658683     0.997899 0.756014               501             19988
    9                    2310 xgboost           0.680389 0.966656  625 48382 206 597   0.752106 0.511457     0.995760 0.608865              1222             48588
   10                    2313 xgboost           0.941936 0.991376 1908 28033  85 655   0.957351 0.744440     0.996977 0.837577              2563             28118
   11                    2314 xgboost                NaN      NaN    0    64   0   0        NaN      NaN     1.000000      NaN                 0                64
   12                    2320 xgboost           0.757424 0.964515  434 22858  75 309   0.852652 0.584118     0.996730 0.693291               743             22933
   13                    2401 xgboost           0.877119 0.957266   50   358   3  32   0.943396 0.609756     0.991690 0.740741                82               361
   14                    2403 xgboost                NaN      NaN    0   108   7   0   0.000000      NaN     0.939130 0.000000                 0               115
   15                    2404 xgboost                NaN      NaN    0     1   0   0        NaN      NaN     1.000000      NaN                 0                 1
   16                    2405 xgboost           1.000000 1.000000    5    21   0   0   1.000000 1.000000     1.000000 1.000000                 5                21

Metrics are reported as N/A (`None`) when class or prediction support is insufficient.
Rows from overlapping prediction windows are temporally dependent.
