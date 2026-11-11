# Project Overview

## Goal

GlucoSafeAI investigates a research prototype that estimates near-term hypoglycemia risk for people with Type 1 diabetes. The initial outcome is whether any valid glucose observation below 70 mg/dL occurs in the interval `(t, t + 30 minutes]`.

## Scope

The first comparison is:

- Model A: current and recent glucose information only.
- Model B: Model A plus carbohydrates for the current meal being calculated.

The system does not accumulate meal calculations, require protein or fat, recommend insulin doses, diagnose disease, or guarantee safety.

## Expected input and output

At prediction time, the eventual pipeline may receive participant-safe recent glucose history and, for Model B, a current-meal carbohydrate estimate. It should output a research probability or binary risk estimate plus evaluation metadata. The final application contract is not yet fixed, particularly for whether the meal input is available before or after eating.

## Research versus clinical decision

Offline model output is not a medical diagnosis or treatment instruction. Small observational datasets, measurement gaps, label ambiguity, and participant differences limit generalization. Independent clinical validation and safety review would be required before any real-world use.
