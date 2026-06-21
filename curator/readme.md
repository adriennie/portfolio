<a name="readme-top"></a>

<div align="center">

# Curator

**A deterministic Python CLI for validating tabular data, imputing missing values, flagging outliers, and producing leakage-safe train/test artifacts.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

![CLI](https://img.shields.io/badge/Interface-CLI-success?style=flat-square)
![MLOps](https://img.shields.io/badge/Workflow-MLOps-blue?style=flat-square)
![Data%20Quality](https://img.shields.io/badge/Data%20Quality-Validation%20%26%20Imputation-orange?style=flat-square)

> *Pandas • Pandera • scikit-learn • Typer*

</div>

---

## Overview

Curator is a lightweight command-line data curation pipeline for structured CSV inputs. It validates a fixed schema, repairs missing numeric features with group-aware medians, detects multivariate outliers, and writes train/test artifacts with structured JSON Lines logs.

The project is designed around:

- Strict runtime schema validation
- Leakage-safe preprocessing
- Deterministic splitting and scaling
- Append-only JSON Lines audit logging
- Simple synthetic data generation for testing

It is intentionally narrow in scope so the data contract, transformations, and outputs stay easy to reason about.

---

## Features

### Schema Validation

Validates input CSVs with Pandera before any transformation runs.

### Group-Aware Imputation

Fills missing numeric values using the median for each `group`, then falls back to the global median.

### Outlier Detection

Flags multivariate outliers across `amount`, `tenure`, and `score` using `IsolationForest`.

### Leakage-Safe Splitting

Removes flagged outliers from the modeling set, then splits inliers into train and test sets with a fixed random seed.

### Structured Audit Logging

Writes JSON Lines events for validation, imputation, outlier detection, artifact writes, and pipeline completion.

### Synthetic Data Generation

Creates mock tabular data with missing values and injected outliers for local testing.

---

## Pipeline

```text
CSV input
  -> strict Pandera validation
  -> group-median imputation
  -> IsolationForest outlier detection
  -> exclude flagged outliers from splits
  -> deterministic train/test split
  -> fit StandardScaler on training data only
  -> write CSV artifacts and JSON Lines logs
  -> generate Markdown run report
```

---

## Built With

| Technology | Purpose |
| --- | --- |
| Python 3.10+ | Core language |
| pandas | Data loading and transformation |
| numpy | Synthetic data generation and numeric work |
| pandera | Runtime schema validation |
| scikit-learn | Outlier detection, splitting, scaling |
| typer | Command-line interface |

---

## Getting Started

### Prerequisites

- Python 3.10 or newer
- Virtual environment support such as `venv`

Verify your installation:

```bash
python3 --version
```

### Installation

Run commands from the `Curator/` directory.

Create and activate a virtual environment:

```bash
python3 -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install numpy pandas pandera scikit-learn typer
```

If you want reproducible environments, pin the versions in `requirements.txt` before sharing the project.

---

## Usage

### Generate Mock Data

```bash
python pipeline.py generate --count 5000 --output-dir mock_data
```

This writes `mock_data/mock_data.csv` and appends structured events to `mock_data/generator.log.jsonl`.

### Run the Curation Pipeline

```bash
python pipeline.py run --input-file mock_data/mock_data.csv --output-dir output
```

This validates the CSV, imputes missing values, flags outliers, splits inlier rows, scales features, and writes the curated artifacts into `output/`.

### View Help

```bash
python pipeline.py --help
python pipeline.py generate --help
python pipeline.py run --help
```

---

## Outputs

The pipeline produces the following artifacts:

| File | Description |
| --- | --- |
| `curated_full.csv` | All validated rows with imputed features and an `outlier` flag |
| `X_train.csv` | Scaled training features from inlier rows |
| `X_test.csv` | Scaled test features from inlier rows |
| `y_train.csv` | Training targets |
| `y_test.csv` | Test targets |
| `pipeline.log.jsonl` | Append-only structured run log |
| `reports/latest.md` | Markdown summary of the latest successful run |

Generated mock data is stored in `mock_data/`.

---

## Input Contract

The input CSV must contain these columns. Column order does not matter.

| Column | Type after coercion | Rules |
| --- | --- | --- |
| `amount` | float | Nullable; must be at least `0` |
| `tenure` | float | Nullable; must be at least `0` |
| `score` | float | Nullable; must be between `-1,000,000` and `1,000,000` |
| `group` | string | Required; one of `alpha`, `beta`, or `gamma` |
| `target` | float | Nullable |

---

## Current Status

The core pipeline in `pipeline.py` is implemented and has been exercised end to end with generated data. The checked-in artifacts in `mock_data/` and `output/` show a successful run of the current workflow.

Automated tests and fully pinned dependency metadata have not been added yet.

---

## Limitations

- The schema and feature names are fixed in code.
- Outlier sensitivity uses `contamination="auto"`; it is not calibrated to a business threshold.
- The CLI does not yet validate that enough inlier rows remain for splitting.
- Missing targets are accepted and written to output.
- Failures outside Pandera validation may terminate without a structured error event.

---

## Roadmap

- [x] Fixed-schema CSV validation
- [x] Group-wise median imputation
- [x] IsolationForest outlier detection
- [x] Leakage-safe train/test split
- [x] Structured JSON Lines audit logging
- [x] Markdown run report generation
- [ ] Dependency pinning
- [ ] Automated tests
- [ ] Stronger error recovery for non-validation failures

---

## Related Docs

- See [PRD.md](docs/PRD.md) for the data contract and output requirements.
- See [ENGINEERING.md](docs/ENGINEERING.md) for implementation notes.
- See [MEMORY.md](docs/MEMORY.md) for status and known risks.

---

<div align="center">

**Built for reproducible data curation workflows.**

[Back to Top ↑](#readme-top)

</div>
