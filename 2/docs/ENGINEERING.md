# Engineering Reference

## Runtime stack

| Concern | Implementation |
| --- | --- |
| CLI | Typer |
| Data loading and transformation | Pandas and NumPy |
| Runtime schema validation | Pandera `DataFrameModel` |
| Outlier detection | scikit-learn `IsolationForest` |
| Split and scaling | scikit-learn `train_test_split` and `StandardScaler` |
| Paths | `pathlib.Path` |
| Audit logging | Custom append-only JSON Lines logger |

## Main components

| Component | Responsibility |
| --- | --- |
| `InputSchema` | Coerce and strictly validate the five input columns |
| `group_median_impute` | Fill missing feature values without mutating the caller's DataFrame |
| `isolate_outliers` | Add an integer `outlier` flag |
| `split_and_scale` | Split inliers, fit on training features, and transform both folds |
| `run` | Orchestrate curation and artifact persistence |
| `generate` | Create deterministic synthetic input with missing values and outliers |

## Determinism and data leakage

Mock generation uses NumPy seed `42`. Isolation Forest and train/test splitting use `random_state=42`. Scaling occurs after splitting, and only training features are passed to `StandardScaler.fit_transform`.

## Logging behavior

Each event has a UTC timestamp, level, event name, trace ID, and logger name. Logs are opened in append mode. The current trace ID is generated per event, so it cannot correlate all events from one run.

## Change checklist

When adding or changing a feature column:

1. Update `InputSchema` and its constraints.
2. Confirm whether the column should be imputed.
3. Confirm whether the column belongs in outlier detection and scaling.
4. Add tests for nulls, invalid values, all-null groups, outliers, and leakage.
5. Update the PRD input and output contracts.
