# Product Requirements: MLOps Data Curation Pipeline

## Goal

Provide a deterministic CLI that validates a fixed CSV schema, repairs missing feature values, flags multivariate outliers, and writes leakage-safe train/test artifacts with structured audit logs.

## Supported workflows

| Workflow | Command | Result |
| --- | --- | --- |
| Generate mock data | `python pipeline.py generate --count 5000 --output-dir mock_data` | Synthetic CSV with missing feature values and extreme `amount` values |
| Curate data | `python pipeline.py run --input-file mock_data/mock_data.csv --output-dir output` | Validated, imputed, outlier-flagged, split, and scaled artifacts |

## Input contract

The input must contain exactly these columns. Column order is not significant.

| Column | Type after coercion | Rules |
| --- | --- | --- |
| `amount` | float | Nullable; value must be at least `0` |
| `tenure` | float | Nullable; value must be at least `0` |
| `score` | float | Nullable; value must be between `-1,000,000` and `1,000,000` |
| `group` | string | Required; one of `alpha`, `beta`, or `gamma` |
| `target` | float | Nullable |

## Processing requirements

1. Validate with Pandera before transformation.
2. Impute missing feature values with the median for their `group`, then the global median as fallback.
3. Detect outliers across `amount`, `tenure`, and `score` with `IsolationForest` and retain the flag in the curated dataset.
4. Exclude flagged outliers from model splits.
5. Split inliers into training and test sets with `random_state=42`.
6. Fit `StandardScaler` on training features only, then transform test features.
7. Write JSON Lines audit events and never modify the source CSV.

## Output contract

- `curated_full.csv`: all validated rows, imputed features, and `outlier` flag.
- `X_train.csv` and `X_test.csv`: scaled inlier features.
- `y_train.csv` and `y_test.csv`: corresponding targets.
- `pipeline.log.jsonl`: append-only structured events.

## Out of scope

- Streaming ingestion, databases, distributed processing, model training, and user interfaces.
- Validation/test/train three-way splits, categorical encoding, and generated Markdown reports.
- Arbitrary schemas or configurable feature columns.
