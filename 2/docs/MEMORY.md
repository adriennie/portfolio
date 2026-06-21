# Project Memory

Last reviewed: 2026-06-22

## Completed

- Implemented the Typer `generate` and `run` commands.
- Added strict Pandera validation for `amount`, `tenure`, `score`, `group`, and `target`.
- Added group-median imputation with a global-median fallback.
- Added multivariate outlier flagging with deterministic Isolation Forest settings.
- Added an inlier-only train/test split and leakage-safe standardization.
- Added CSV artifacts and structured JSON Lines logs.
- Generated and processed a deterministic 5,000-row sample on 2026-06-21.
- Consolidated project documentation and removed inherited README templates and speculative duplicate documents on 2026-06-22.

## Verified manual-run result

| Metric | Value |
| --- | ---: |
| Input rows | 5,000 |
| Outliers flagged | 805 |
| Training rows | 3,356 |
| Test rows | 839 |
| Test ratio | 0.20 |

The generated artifacts are under `mock_data/` and `output/`. This is manual-run evidence, not an automated regression test.

## Open work

- Add pinned dependency metadata and reproducible environment setup.
- Add unit and CLI integration tests.
- Define behavior for missing targets and all-null feature columns.
- Validate minimum row counts before outlier fitting and splitting.
- Add structured error events around CSV loading, transformation, and artifact writes.
- Use one run-level trace ID across related log events.
- Decide whether generated CSV and log artifacts should remain version controlled.

## Known real-world failure modes

- One row, or too few inliers after outlier filtering, causes `train_test_split` to fail.
- An entirely null feature column remains null after both median fallbacks and causes Isolation Forest to fail.
- A header-only CSV passes file-level CLI checks but fails later during processing.
- Nullable targets can produce missing values in `y_train.csv` or `y_test.csv`.
- Existing log files grow on every run because logging is append-only.
- Concurrent processes writing the same log or artifact paths can interleave logs or overwrite CSVs.
- Pandera compatibility can vary across major versions because no versions are pinned.
