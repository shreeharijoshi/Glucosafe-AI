# Open Questions

1. Which dataset or datasets will be used initially?
2. Is the meal calculator used before eating, after eating, or in both situations?
3. What exactly does the current-meal carbohydrate input represent in each candidate dataset?
4. Which participant and timestamp-alignment rules are appropriate for the selected dataset?
5. How will duplicate or conflicting glucose timestamps be handled?
6. What future-coverage policy determines whether a target is known?
7. How will recording boundaries and dataset train/test files be treated?
8. How will training, validation, and testing participants be selected?
9. Are the chosen historical glucose features consistently available?
10. Which baseline algorithm will be selected after validation?
11. Can HUPA-UCM glucose units and preprocessing provenance be confirmed?
12. Manchester participant mapping is resolved and day-first parsing is the empirically supported operational rule for `bg_ts` and `meal_ts`, but can the README conflict be confirmed authoritatively and can timestamp precision/timezone be established?
13. Can OhioT1DM support a sufficiently balanced participant-independent evaluation with only 12 distinct participants?
14. What maximum interval after a recorded meal will qualify as "recently consumed"?
15. How should multiple eligible recorded meals be handled without summing carbohydrates?
16. Does the application receive the carbohydrate estimate immediately after consumption, or can logging be delayed?
