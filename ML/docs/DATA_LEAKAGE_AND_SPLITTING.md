# Data Leakage and Splitting

- Never randomly split overlapping time-series rows across train and test.
- Assign every complete participant to exactly one partition.
- Keep OhioT1DM train/test files together by participant when assessing unseen-person generalization; its supplied split is not participant-independent.
- Fit preprocessing and transformations on training data only.
- Use no glucose observation after prediction time as a feature.
- Ensure the target cannot inspect glucose after `t + 30 minutes`.
- Do not duplicate the same recording period through overlapping files.
- Do not mix incompatible periods or timestamp conventions without a documented rule.
- Use a meal carbohydrate value only if it would be available at prediction time in the application workflow.
- Keep Model A and Model B partitions and eligible timestamps identical.

Overlapping prediction windows may be retained, but they create dependent examples. This must be disclosed and handled with participant/time-aware evaluation rather than row-random splitting.
